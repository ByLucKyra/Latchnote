"""Run Latchnote as a Windows system-tray application."""

import argparse
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread
from time import monotonic

import pystray
from PIL import Image, ImageDraw
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QVBoxLayout

from .audio_capture import AudioCaptureError, WasapiLoopbackCapture
from .config import Settings, load_settings
from .hotkey_listener import GlobalHotkeyListener, HotkeyError, MicroNoteController
from .session import Session, SessionOrchestrator, SessionStatus
from .structurer import NotesStructurer
from .stt_client import LocalWhisperSttClient, SttError, load_whisper_model, transcribe_audio
from .writer import JournalError, MarkdownWriter

LOGGER = logging.getLogger(__name__)


@dataclass
class SessionController:
    """Own the single active recording session."""

    settings: Settings
    title: str
    raw_only: bool = False
    status: SessionStatus = SessionStatus.IDLE
    last_error: str | None = None
    config_path: Path | None = None

    def __post_init__(self) -> None:
        self._capture: WasapiLoopbackCapture | None = None
        self._stt: LocalWhisperSttClient | None = None
        self._orchestrator: SessionOrchestrator | None = None
        self._whisper_model = None
        self.on_transcript: Callable[[str, str], None] | None = None
        self.mode_message = "Transcript only"
        self._retry_thread: Thread | None = None

    @property
    def can_start(self) -> bool:
        """Return whether a new recording may begin."""
        return self._capture is None and not (self._retry_thread and self._retry_thread.is_alive())

    @property
    def can_stop(self) -> bool:
        """Return whether an active recording may stop."""
        return self._capture is not None

    @property
    def can_retry(self) -> bool:
        """Return whether explicit pending-task recovery may start."""
        return self._capture is None and not (self._retry_thread and self._retry_thread.is_alive())

    def start_session(self) -> None:
        """Start audio capture, live transcription, and local note writing."""
        if not self.can_start:
            return
        if self.config_path is not None:
            try:
                refreshed = load_settings(self.config_path)
            except (OSError, ValueError) as error:
                self._set_error(f"Unable to reload settings: {error}. Check {self.config_path}.")
                return
            if (refreshed.whisper_model, refreshed.whisper_threads) != (self.settings.whisper_model, self.settings.whisper_threads):
                self._whisper_model = None
            self.settings = refreshed
        if self.status is SessionStatus.ERROR:
            self.status = SessionStatus.RETRYING
            self.last_error = None
        try:
            if self._whisper_model is None:
                self._whisper_model = load_whisper_model(
                    self.settings.whisper_model, self.settings.data_dir / "models", self.settings.whisper_threads
                )
        except SttError as error:
            self._set_error(str(error))
            return

        session = Session(title=self.title, status=SessionStatus.RECORDING)
        structurer = _notes_structurer(self.settings, self.raw_only)
        self.mode_message = "Transcript only" if structurer is None else "AI notes enabled"
        capture = WasapiLoopbackCapture(self.settings.data_dir)
        stt = None
        try:
            writer = MarkdownWriter(self.settings.notes_dir, session)
            orchestrator = SessionOrchestrator(session, writer, structurer.structure if structurer else None)
            capture.start(writer.session_id, paused=True)
            self._capture = capture
            self._orchestrator = orchestrator
            if capture.format is None:
                raise AudioCaptureError("WASAPI did not provide an audio format.")
            stt = LocalWhisperSttClient(
                self._whisper_model,
                capture.format,
                lambda segment: self._handle_final(
                    orchestrator,
                    session.started_at + timedelta(seconds=segment.start_seconds),
                    session.timestamp(session.started_at + timedelta(seconds=segment.start_seconds)),
                    segment.text,
                ),
                self.settings.whisper_window_seconds,
                self.settings.whisper_language,
            )
            stt.start()
            capture.set_chunk_handler(stt.submit_audio)
        except (AudioCaptureError, SttError, JournalError, OSError) as error:
            capture.stop()
            if stt is not None:
                stt.stop()
            self._capture = None
            self._orchestrator = None
            self._set_error(str(error))
            return

        self._stt = stt
        self.status = SessionStatus.RECORDING
        self.last_error = None
        LOGGER.info("Session started: %s", writer.path)

    def _handle_final(self, orchestrator: SessionOrchestrator, at: datetime, timestamp: str, text: str) -> None:
        orchestrator.add_final_transcript(text, at)
        if self.on_transcript:
            self.on_transcript(timestamp, text)

    def _persist_gaps(self) -> str | None:
        if self._stt is None or self._orchestrator is None:
            return None
        try:
            for start, end in self._stt.pending_gaps():
                self._orchestrator.add_recovery_gap(start, end, "Whisper queue was full")
                self._stt.acknowledge_gap((start, end))
        except JournalError as error:
            return str(error)
        return None

    def retry_pending_tasks(self) -> None:
        """Retry session journal tasks only after an explicit tray action."""
        if not self.can_retry:
            return
        try:
            settings = load_settings(self.config_path) if self.config_path else self.settings
            journals = [
                path for path in settings.notes_dir.glob("*.jsonl")
                if MarkdownWriter.resume(path).pending_tasks()
            ]
            self.settings = settings
            if not journals:
                self.mode_message = "No pending AI tasks"
                self.status = SessionStatus.IDLE
                return
            structurer = _notes_structurer(settings, self.raw_only)
            if structurer is None:
                raise ValueError("Pending AI retry needs valid NOTES_AI_* settings; transcript-only mode is active.")
        except (OSError, ValueError) as error:
            self._set_error(str(error))
            return
        self.status = SessionStatus.RETRYING
        self.last_error = None
        self._retry_thread = Thread(
            target=self._retry_pending_worker, args=(structurer.structure, journals), name="notes-recovery", daemon=True
        )
        self._retry_thread.start()

    def _retry_pending_worker(self, structure: Callable[[str], str], journals: list[Path]) -> None:
        try:
            for journal in journals:
                writer = MarkdownWriter.resume(journal)
                orchestrator = SessionOrchestrator(writer.session, writer, structure)
                orchestrator.retry_pending()
                if not orchestrator.finish():
                    raise RuntimeError("Some AI tasks remain pending; their journals are available in the notes folder.")
            self.status = SessionStatus.STOPPED
            self.last_error = None
        except (JournalError, OSError, RuntimeError, ValueError) as error:
            self._set_error(str(error))

    def stop_session(self) -> None:
        """Stop one session without discarding recovery audio or raw notes."""
        if not self.can_stop:
            return
        gap_error = None
        try:
            if self._capture is not None:
                self._capture.stop()
            if self._stt is not None:
                try:
                    self._stt.stop()
                finally:
                    gap_error = self._persist_gaps()
            stt_error = self._stt.last_error if self._stt else None
            notes_complete = True
            if self._orchestrator is not None:
                notes_complete = self._orchestrator.finish(source_success=not stt_error and not gap_error)
        except (AudioCaptureError, SttError, JournalError, OSError) as error:
            self._set_error(str(error))
            return
        error = stt_error or gap_error
        if not error and not notes_complete:
            error = "AI notes remain pending; use --retry-pending with the session journal to retry them."
        self._capture = None
        self._stt = None
        self._orchestrator = None
        self.status = SessionStatus.ERROR if error else SessionStatus.STOPPED
        self.last_error = error
        LOGGER.info("Session stopped.")

    def add_micro_note(self, text: str) -> None:
        """Add a micro-note only while a session is active."""
        if self._orchestrator is not None:
            self._orchestrator.add_manual_note(text)

    def _set_error(self, message: str) -> None:
        self.status = SessionStatus.ERROR
        self.last_error = message
        LOGGER.error(message)


def _request_micro_note_if_active(controller: SessionController, request_show: Callable[[], None]) -> None:
    """Ignore the global hotkey while no note can be saved."""
    if controller.can_stop:
        request_show()


class TrayApplication(QObject):
    """Expose Start, Stop, and Quit through a compact system-tray menu."""

    quit_requested = Signal()

    def __init__(self, controller: SessionController) -> None:
        super().__init__()
        self._controller = controller
        self._preview = TranscriptPreview()
        self._controller.on_transcript = self._preview.publish_final
        self._last_status = controller.status
        self._last_error = controller.last_error
        self._icon = pystray.Icon(
            "latchnote",
            _tray_image(),
            "Latchnote — Idle",
            pystray.Menu(
                pystray.MenuItem(lambda _: self._status_text(), None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Start Session", self._start, enabled=lambda _: controller.can_start),
                pystray.MenuItem("Stop Session", self._stop, enabled=lambda _: controller.can_stop),
                pystray.MenuItem("Live Transcript", self._show_transcript),
                pystray.MenuItem("Open Notes Folder", self._open_notes),
                pystray.MenuItem("Open Recovery Folder", self._open_recovery),
                pystray.MenuItem("Retry Pending AI", self._retry_pending, enabled=lambda _: controller.can_retry),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", self._quit),
            ),
        )
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_error)
        self._timer.start(1000)

    def run(self) -> None:
        """Start the tray icon alongside Qt's event loop."""
        self._icon.run_detached()

    def stop(self) -> None:
        """Remove the tray icon."""
        self._timer.stop()
        self._icon.stop()

    def _check_error(self) -> None:
        gap_error = self._controller._persist_gaps()
        if gap_error:
            self._controller._set_error(gap_error)
            self._refresh(self._icon)
            return
        stt = self._controller._stt
        if stt and stt.last_error and stt.last_error != self._controller.last_error:
            message = stt.last_error
            if self._controller._capture and self._controller._capture.path:
                path = self._controller._capture.path
                config = f' --config "{self._controller.config_path}"' if self._controller.config_path else ""
                message += f' WAV retained at {path}. Reprocess separately with python -m latchnote{config} --transcribe-file "{path}" --title "Recovered audio" --raw-only.'
            self._controller._set_error(message)
            self._refresh(self._icon)
        elif (self._controller.status, self._controller.last_error) != (self._last_status, self._last_error):
            self._refresh(self._icon)

    def _start(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self._controller.start_session()
        self._refresh(icon)

    def _stop(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self._controller.stop_session()
        self._refresh(icon)

    def _show_transcript(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self._preview.open_requested.emit()

    def _open_notes(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self._open_directory(self._controller.settings.notes_dir)

    def _open_recovery(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self._open_directory(self._controller.settings.data_dir)

    def _retry_pending(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self._controller.retry_pending_tasks()
        self._refresh(icon)

    def _open_directory(self, path: Path) -> None:
        try:
            path.mkdir(parents=True, exist_ok=True)
            os.startfile(str(path))
        except OSError as error:
            self._controller._set_error(f"Unable to open folder ({type(error).__name__}): {path}")
            self._refresh(self._icon)

    def _quit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self._controller.stop_session()
        if self._controller.can_stop:
            self._refresh(icon)
            return
        icon.stop()
        self.quit_requested.emit()

    def _refresh(self, icon: pystray.Icon) -> None:
        self._preview.state_updated.emit(self._status_text())
        self._last_status = self._controller.status
        self._last_error = self._controller.last_error
        icon.title = f"Latchnote — {self._status_text()}"
        if self._controller.last_error:
            icon.notify(self._controller.last_error, "Latchnote error")
        icon.update_menu()

    def _status_text(self) -> str:
        if self._controller.can_stop and self._controller.status is SessionStatus.ERROR:
            return "Recording (transcription issue; WAV is being saved)"
        if self._controller.status is SessionStatus.RECORDING:
            return f"Recording ({self._controller.mode_message})"
        return self._controller.status.value.replace("_", " ").title()


class TranscriptPreview(QDialog):
    """Show the latest final local Whisper text when the user opens the window."""

    text_updated = Signal(str, str)
    state_updated = Signal(str)
    open_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Latchnote transcript")
        self._state = QLabel("Idle")
        self._time = QLabel("Latest final segment")
        self._text = QLabel("Whisper updates after each audio window; interim captions are unavailable.")
        self._text.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self._state)
        layout.addWidget(self._time)
        layout.addWidget(self._text)
        self.resize(480, 160)
        self.text_updated.connect(self._set_text)
        self.state_updated.connect(self._state.setText)
        self.open_requested.connect(self.show)

    def publish_final(self, timestamp: str, text: str) -> None:
        """Send worker output to the Qt thread without opening or focusing the window."""
        self.text_updated.emit(timestamp, text)

    def _set_text(self, timestamp: str, text: str) -> None:
        self._time.setText(f"Latest final segment [{timestamp}]")
        self._text.setText(text)


def _tray_image() -> Image.Image:
    image = Image.new("RGBA", (64, 64), "#1E293B")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((12, 12, 52, 52), radius=12, fill="#38BDF8")
    draw.rectangle((25, 22, 31, 42), fill="#0F172A")
    draw.rectangle((31, 36, 42, 42), fill="#0F172A")
    return image


def main() -> int:
    """Launch the tray application."""
    parser = argparse.ArgumentParser(description="Run Latchnote in the system tray.")
    parser.add_argument("--title", default="Study session", help="Default title for a session")
    parser.add_argument("--config", type=Path, default=Path(".env"), help="Settings file (default: .env in current directory)")
    parser.add_argument("--download-model", action="store_true", help="Download/cache the configured local Whisper model")
    parser.add_argument("--transcribe-file", type=Path, help="Transcribe saved audio locally, without recording")
    recovery = parser.add_mutually_exclusive_group()
    recovery.add_argument("--rebuild-notes", type=Path, help="Rebuild Markdown from a session .jsonl journal")
    recovery.add_argument("--retry-pending", type=Path, help="Retry pending AI tasks from a session .jsonl journal")
    parser.add_argument("--raw-only", action="store_true", help="Disable all AI provider requests")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        settings = load_settings(args.config)
        if args.rebuild_notes:
            LOGGER.info("Rebuilt %s", MarkdownWriter.rebuild(args.rebuild_notes))
            return 0
        if args.retry_pending:
            writer = MarkdownWriter.resume(args.retry_pending)
            structurer = _notes_structurer(settings, args.raw_only)
            if structurer is None:
                raise RuntimeError("Pending AI retry requires valid NOTES_AI_* configuration and must not use --raw-only.")
            orchestrator = SessionOrchestrator(writer.session, writer, structurer.structure)
            orchestrator.retry_pending()
            orchestrator.finish()
            pending = writer.pending_tasks()
            if pending:
                LOGGER.error("%d AI task(s) remain pending; journal and raw transcript are retained.", len(pending))
                return 1
            LOGGER.info("Pending AI tasks completed and notes rebuilt: %s", writer.path)
            return 0
        if args.download_model or args.transcribe_file:
            started = monotonic()
            model = load_whisper_model(
                settings.whisper_model, settings.data_dir / "models", settings.whisper_threads, args.download_model
            )
            if args.transcribe_file:
                if not args.transcribe_file.is_file():
                    raise FileNotFoundError("Audio input file does not exist.")
                session = Session(args.title)
                writer = MarkdownWriter(settings.notes_dir, session)
                structurer = _notes_structurer(settings, args.raw_only)
                orchestrator = SessionOrchestrator(session, writer, structurer.structure if structurer else None)
                count = 0
                for segment in transcribe_audio(model, str(args.transcribe_file), settings.whisper_language):
                    orchestrator.add_final_transcript(
                        segment.text, session.started_at + timedelta(seconds=segment.start_seconds)
                    )
                    count += 1
                orchestrator.finish()
                LOGGER.info("Saved %s (%d segments), elapsed %.2fs", writer.path, count, monotonic() - started)
            else:
                LOGGER.info("Local Whisper model ready; subsequent runs can work offline.")
            return 0
    except (SttError, OSError, RuntimeError, ValueError) as error:
        LOGGER.error("Local transcription/configuration failed (%s). Check model cache, audio path, and settings.", type(error).__name__)
        return 1
    app = QApplication([])
    controller = SessionController(settings, args.title, args.raw_only, config_path=args.config)
    micro_notes = MicroNoteController(controller.add_micro_note)
    hotkey = GlobalHotkeyListener(lambda: _request_micro_note_if_active(controller, micro_notes.request_show))
    tray = TrayApplication(controller)
    tray.quit_requested.connect(app.quit)
    try:
        hotkey.start()
        tray.run()
        return app.exec()
    except HotkeyError as error:
        controller._set_error(str(error))
        tray.run()
        return app.exec()
    finally:
        hotkey.stop()
        tray.stop()
        controller.stop_session()


def _notes_structurer(settings: Settings, raw_only: bool) -> NotesStructurer | None:
    if raw_only or not (settings.notes_ai_base_url or settings.notes_ai_model):
        LOGGER.info("Raw-only mode: audio and transcript stay local; no AI provider requests.")
        return None
    if not settings.notes_ai_base_url:
        LOGGER.warning("NOTES_AI_BASE_URL is missing; continuing in transcript-only mode.")
        return None
    if not settings.notes_ai_model:
        LOGGER.warning("NOTES_AI_MODEL is missing; continuing in transcript-only mode.")
        return None
    try:
        return NotesStructurer(
            settings.notes_ai_base_url, settings.notes_ai_api_key,
            settings.notes_ai_model, settings.notes_format_path,
        )
    except (OSError, ValueError):
        LOGGER.warning("AI settings/format are invalid; continuing with raw-only notes. Check NOTES_AI_* settings.")
        return None


if __name__ == "__main__":
    raise SystemExit(main())
