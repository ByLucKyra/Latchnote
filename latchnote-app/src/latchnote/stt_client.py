"""Local CPU Whisper transcription of small windows of captured PCM audio."""

import logging
from math import isclose
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from queue import Empty, Full, Queue
from threading import Event, Lock, Thread
from time import monotonic
from typing import TYPE_CHECKING
from wave import open as open_wave

from .audio_capture import AudioFormat

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

LOGGER = logging.getLogger(__name__)


class SttError(RuntimeError):
    """Raised when local transcription cannot start or finish safely."""


@dataclass(frozen=True)
class TranscriptSegment:
    """One final transcript with its position in the source audio."""

    text: str
    start_seconds: float


def load_whisper_model(
    model: str, cache_dir: Path, threads: int = 2, download: bool = False
) -> "WhisperModel":
    """Load CPU INT8 Whisper; network downloads require an explicit opt-in."""
    try:
        from faster_whisper import WhisperModel

        return WhisperModel(
            model, device="cpu", compute_type="int8", cpu_threads=threads, num_workers=1,
            download_root=str(cache_dir), local_files_only=not download,
        )
    except (ImportError, OSError, RuntimeError, ValueError) as error:
        raise SttError("Unable to load local Whisper. Run --download-model first, or check the model path.") from error


def transcribe_audio(
    model: "WhisperModel", source: str | BytesIO, language: str | None = None, offset: float = 0
) -> Iterator[TranscriptSegment]:
    """Yield timestamped text using the same decoder for live and saved audio."""
    segments, _ = model.transcribe(
        source, language=language, beam_size=1, vad_filter=True, condition_on_previous_text=False
    )
    for segment in segments:
        text = segment.text.strip()
        if text:
            yield TranscriptSegment(text, offset + segment.start)


class LocalWhisperSttClient:
    """Decode on one worker while capture writes the authoritative recovery WAV."""

    def __init__(
        self, model: "WhisperModel", audio_format: AudioFormat,
        on_final: Callable[[TranscriptSegment], None], window_seconds: int = 5,
        language: str | None = None,
    ) -> None:
        if window_seconds < 1 or audio_format.sample_width != 2 or audio_format.channels < 1 or audio_format.rate < 1:
            raise SttError("Whisper requires positive windows and 16-bit PCM audio.")
        self._model = model
        self._format = audio_format
        self._on_final = on_final
        self._language = language
        self._bytes_per_second = audio_format.rate * audio_format.channels * audio_format.sample_width
        self._window_bytes = self._bytes_per_second * window_seconds
        # ponytail: bounded 30-second backlog; recover saved WAV if CPU cannot keep up.
        self._queue: Queue[tuple[float, bytes]] = Queue(maxsize=max(1, 30 // window_seconds))
        self._buffer = bytearray()
        self._received_bytes = 0
        self._stopping = Event()
        self._gap_lock = Lock()
        self._gaps: list[tuple[float, float]] = []
        self._worker: Thread | None = None
        self.last_error: str | None = None

    def start(self) -> None:
        """Start decoding without loading a second model or blocking audio capture."""
        if self._worker is not None:
            raise SttError("Local transcription is already running.")
        self._worker = Thread(target=self._run, name="whisper-stt", daemon=True)
        self._worker.start()

    def submit_audio(self, audio: bytes) -> None:
        """Accept native PCM from the single capture callback without waiting for inference."""
        if self._stopping.is_set() or self._worker is None or not self._worker.is_alive():
            return
        self._buffer.extend(audio)
        while len(self._buffer) >= self._window_bytes:
            self._enqueue(bytes(self._buffer[:self._window_bytes]))
            del self._buffer[:self._window_bytes]

    def _enqueue(self, audio: bytes) -> None:
        offset = self._received_bytes / self._bytes_per_second
        self._received_bytes += len(audio)
        try:
            self._queue.put_nowait((offset, audio))
        except Full:
            self.last_error = "Whisper cannot keep up; live text has gaps. Use --transcribe-file on the saved WAV."
            end = offset + len(audio) / self._bytes_per_second
            with self._gap_lock:
                if self._gaps and isclose(self._gaps[-1][1], offset, abs_tol=1e-9):
                    self._gaps[-1] = (self._gaps[-1][0], end)
                else:
                    self._gaps.append((offset, end))
            LOGGER.warning(self.last_error)

    def pending_gaps(self) -> list[tuple[float, float]]:
        """Return source-audio ranges dropped by the bounded queue."""
        with self._gap_lock:
            return self._gaps.copy()

    def acknowledge_gap(self, gap: tuple[float, float]) -> None:
        """Remove a gap only after its journal event has been written."""
        with self._gap_lock:
            if gap in self._gaps:
                self._gaps.remove(gap)

    def stop(self, timeout: float = 60) -> None:
        """After capture stops, flush the tail and drain queued windows before returning."""
        if self._worker is None:
            return
        if self._buffer:
            self._enqueue(bytes(self._buffer))
            self._buffer.clear()
        self._stopping.set()
        self._worker.join(timeout=timeout)
        if self._worker.is_alive():
            raise SttError("Whisper is still draining audio; wait and choose Stop again. Recovery WAV is retained.")
        self._worker = None

    def _run(self) -> None:
        try:
            while True:
                try:
                    offset, audio = self._queue.get(timeout=0.1)
                except Empty:
                    if self._stopping.is_set():
                        return
                    continue
                source = BytesIO()
                with open_wave(source, "wb") as wave_file:
                    wave_file.setnchannels(self._format.channels)
                    wave_file.setsampwidth(self._format.sample_width)
                    wave_file.setframerate(self._format.rate)
                    wave_file.writeframes(audio)
                source.seek(0)
                started = monotonic()
                # ponytail: non-overlapping windows may split words; add overlap after ID/EN benchmarks.
                for segment in transcribe_audio(self._model, source, self._language, offset):
                    self._on_final(segment)
                LOGGER.info("Whisper: %.2fs audio processed in %.2fs", len(audio) / self._bytes_per_second, monotonic() - started)
        except (OSError, RuntimeError, ValueError) as error:
            self.last_error = f"Local transcription failed ({type(error).__name__}); recovery WAV is retained."
            LOGGER.error(self.last_error)
