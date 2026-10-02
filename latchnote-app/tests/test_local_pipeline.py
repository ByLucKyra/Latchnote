from datetime import datetime, timedelta
from threading import Event
from types import SimpleNamespace
from wave import open as open_wave

import httpx
import pytest

from latchnote import structurer
from latchnote.config import load_settings
from latchnote.session import Session, SessionOrchestrator
from latchnote.stt_client import LocalWhisperSttClient, SttError
from latchnote.audio_capture import AudioFormat
from latchnote.structurer import NotesStructurer, StructuringError
from latchnote.writer import MarkdownWriter


def test_local_worker_drains_windows_and_tail_with_source_timestamps() -> None:
    lengths = []
    results = []

    class Decoder:
        def transcribe(self, source, **options):
            assert options["beam_size"] == 1 and options["vad_filter"]
            with open_wave(source, "rb") as audio:
                lengths.append(audio.getnframes())
                assert audio.getnchannels() == 1 and audio.getsampwidth() == 2
            return iter([SimpleNamespace(text=" hello ", start=0.25)]), None

    client = LocalWhisperSttClient(Decoder(), AudioFormat(1, 8, 2), results.append, 2)
    client.start()
    client.submit_audio(b"\0\0" * 36)  # two 2-second windows, then a half-second tail
    client.stop(timeout=2)
    client.stop(timeout=2)
    assert lengths == [16, 16, 4]
    assert [segment.start_seconds for segment in results] == [0.25, 2.25, 4.25]
    assert [segment.text for segment in results] == ["hello"] * 3
    assert client.last_error is None


def test_slow_decoder_timeout_keeps_worker_until_drain_completes() -> None:
    entered, release = Event(), Event()

    class Decoder:
        def transcribe(self, source, **options):
            entered.set()
            assert release.wait(3)
            return iter([]), None

    client = LocalWhisperSttClient(Decoder(), AudioFormat(1, 8, 2), lambda _: None, 1)
    client.start()
    client.submit_audio(b"\0\0" * 8)
    assert entered.wait(2)
    try:
        with pytest.raises(SttError, match="still draining"):
            client.stop(timeout=0.01)
        assert client._worker.is_alive()
    finally:
        release.set()
        client.stop(timeout=2)


def test_queue_overflow_reports_gap_and_preserves_audio_offsets() -> None:
    client = LocalWhisperSttClient(object(), AudioFormat(1, 8, 2), lambda _: None, 30)
    client._enqueue(b"\0\0" * 8)
    client._enqueue(b"\0\0" * 8)  # dropped window still occupies one second of source time
    assert "gaps" in client.last_error
    assert client._queue.get()[0] == 0
    client._enqueue(b"\0\0" * 8)
    assert client._queue.get()[0] == 2


def test_raw_only_has_no_structuring_requests_and_files_do_not_overwrite(tmp_path) -> None:
    session = Session("Same title", started_at=datetime(2026, 10, 2, 9))
    first = MarkdownWriter(tmp_path, session)
    orchestrator = SessionOrchestrator(session, first)
    orchestrator.add_final_transcript("raw text", session.started_at + timedelta(seconds=130))
    orchestrator.finish()
    original = first.path.read_bytes()
    second = MarkdownWriter(tmp_path, session)
    assert second.path != first.path and first.path.read_bytes() == original
    assert "raw text" in original.decode() and "Structured notes" not in original.decode()
    assert orchestrator._worker is None


def test_custom_format_keeps_standard_rules_and_provider_payload(tmp_path, monkeypatch) -> None:
    template = tmp_path / "format.md"
    template.write_text("Use #### Konsep and a concise Markdown table.", encoding="utf-8")

    def post(url, **kwargs):
        assert url == "https://provider.example/v1/chat/completions"
        assert kwargs["headers"]["Authorization"] == "Bearer test-placeholder"
        assert kwargs["timeout"] == 30 and kwargs["follow_redirects"] is False
        messages = kwargs["json"]["messages"]
        assert structurer.STANDARD_RULES in messages[0]["content"]
        assert "#### Konsep" in messages[0]["content"]
        assert messages[1] == {"role": "user", "content": "source only"}
        return httpx.Response(200, json={"choices": [{"message": {"content": "#### Konsep\n- source only"}}]})

    monkeypatch.setattr(structurer.httpx, "post", post)
    client = NotesStructurer("https://provider.example/v1/", "test-placeholder", "test-model", template)
    assert client.structure("source only") == "#### Konsep\n- source only"


@pytest.mark.parametrize("response", [httpx.Response(401, text="sensitive provider body"), httpx.Response(200, json={})])
def test_provider_errors_do_not_expose_bodies_or_erase_raw(tmp_path, monkeypatch, response) -> None:
    monkeypatch.setattr(structurer.httpx, "post", lambda *a, **k: response)
    client = NotesStructurer("https://provider.example/v1", "test-placeholder", "test-model")
    with pytest.raises(StructuringError) as error:
        client.structure("source")
    assert "sensitive" not in str(error.value) and "test-placeholder" not in str(error.value)
    session = Session("Provider failure", started_at=datetime(2026, 10, 2))
    writer = MarkdownWriter(tmp_path, session)
    orchestrator = SessionOrchestrator(session, writer, client.structure, 1)
    orchestrator.add_final_transcript("retain me", session.started_at + timedelta(seconds=2))
    orchestrator.finish()
    assert "retain me" in writer.path.read_text(encoding="utf-8")
    assert len(orchestrator._failed_chunks) == 1


def test_endpoint_validation_and_cpu_setting_boundaries(tmp_path, monkeypatch) -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        NotesStructurer("http://remote.example/v1", "", "model")
    NotesStructurer("http://127.0.0.1:8000/v1", "", "model")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LATCHNOTE_WHISPER_THREADS", "0")
    with pytest.raises(ValueError, match="LATCHNOTE_WHISPER_THREADS"):
        load_settings()


def test_provider_timeout_is_retryable_without_logging_key(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise httpx.ReadTimeout("sensitive-request-details")

    monkeypatch.setattr(structurer.httpx, "post", fail)
    client = NotesStructurer("https://provider.example/v1", "test-placeholder", "test-model")
    with pytest.raises(StructuringError, match="timed out") as error:
        client.structure("keep this source")
    assert "sensitive" not in str(error.value)


def test_audio_stop_never_holds_callback_lock(tmp_path) -> None:
    from latchnote.audio_capture import WasapiLoopbackCapture

    capture = WasapiLoopbackCapture(tmp_path)

    class Stream:
        def stop_stream(self):
            assert capture._lock.acquire(blocking=False)
            capture._lock.release()

        def close(self):
            pass

    capture._stream = Stream()
    capture.stop()
    capture.stop()


def test_raw_only_and_invalid_ai_configuration_do_not_create_provider_client(tmp_path) -> None:
    from latchnote.__main__ import _notes_structurer
    from latchnote.config import Settings

    configured = Settings(tmp_path, tmp_path, notes_ai_base_url="https://provider.example/v1", notes_ai_model="model")
    assert _notes_structurer(configured, True) is None
    invalid = Settings(tmp_path, tmp_path, notes_ai_base_url="http://remote.example/v1")
    assert _notes_structurer(invalid, False) is None


def test_controller_stops_capture_before_decoder_and_keeps_timeout_retryable(tmp_path) -> None:
    from latchnote.__main__ import SessionController
    from latchnote.config import Settings
    from latchnote.session import SessionStatus

    events = []
    controller = SessionController(Settings(tmp_path, tmp_path), "Stop order", raw_only=True)
    controller._capture = SimpleNamespace(stop=lambda: events.append("capture"))

    def timeout():
        events.append("decoder")
        raise SttError("still draining")

    controller._stt = SimpleNamespace(stop=timeout, last_error=None)
    controller._orchestrator = SimpleNamespace(finish=lambda **kwargs: events.append("notes") or True)
    controller.stop_session()
    assert events == ["capture", "decoder"]
    assert controller.can_stop and not controller.can_start
    assert controller.status is SessionStatus.ERROR
    controller._stt.stop = lambda: events.append("decoder drained")
    controller.stop_session()
    assert events[-3:] == ["capture", "decoder drained", "notes"]
    assert not controller.can_stop and controller.status is SessionStatus.STOPPED
