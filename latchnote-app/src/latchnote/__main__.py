"""Run Latchnote as a Windows system-tray application."""

import argparse
import logging
from dataclasses import dataclass

import pystray
from PIL import Image, ImageDraw
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from .audio_capture import AudioCaptureError, WasapiLoopbackCapture
from .config import Settings, load_settings
from .hotkey_listener import GlobalHotkeyListener, HotkeyError, MicroNoteController
from .session import Session, SessionOrchestrator, SessionStatus
from .structurer import ClaudeStructurer
from .stt_client import DeepgramSttClient, SttError
from .writer import MarkdownWriter

LOGGER = logging.getLogger(__name__)


@dataclass
class SessionController:
    """Own the single active recording session."""

    settings: Settings
    title: str
    status: SessionStatus = SessionStatus.IDLE
    last_error: str | None = None

    def __post_init__(self) -> None:
        self._capture: WasapiLoopbackCapture | None = None
        self._stt: DeepgramSttClient | None = None
        self._orchestrator: SessionOrchestrator | None = None

    @property
    def can_start(self) -> bool:
        """Return whether a new recording may begin."""
        return self.status is not SessionStatus.RECORDING

    @property
    def can_stop(self) -> bool:
        """Return whether an active recording may stop."""
        return self.status is SessionStatus.RECORDING

    def start_session(self) -> None:
        """Start audio capture, live transcription, and local note writing."""
        if not self.can_start:
            return
        if self.status is SessionStatus.ERROR:
            self.status = SessionStatus.RETRYING
            self.last_error = None
        if not self.settings.deepgram_api_key:
            self._set_error("Add DEEPGRAM_API_KEY to .env, then choose Start Session again.")
            return

        session = Session(title=self.title, status=SessionStatus.RECORDING)
        writer = MarkdownWriter(self.settings.notes_dir, session)
        structurer = ClaudeStructurer(
            self.settings.anthropic_api_key or "", self.settings.anthropic_model
        )
        orchestrator = SessionOrchestrator(session, writer, structurer.structure)
        capture = WasapiLoopbackCapture(self.settings.data_dir)
        try:
            capture.start(f"{session.started_at:%Y%m%d-%H%M%S}")
            if capture.format is None:
                raise AudioCaptureError("WASAPI did not provide an audio format.")
            stt = DeepgramSttClient(
                self.settings.deepgram_api_key,
                capture.format,
                lambda segment: orchestrator.add_final_transcript(segment.text),
            )
            capture.set_chunk_handler(stt.submit_audio)
            stt.start()
        except (AudioCaptureError, SttError) as error:
            capture.stop()
            self._set_error(str(error))
            return

        self._capture = capture
        self._stt = stt
        self._orchestrator = orchestrator
        self.status = SessionStatus.RECORDING
        self.last_error = None
        LOGGER.info("Session started: %s", writer.path)

    def stop_session(self) -> None:
        """Stop one session without discarding recovery audio or raw notes."""
        if not self.can_stop:
            return
        try:
            if self._stt is not None:
                self._stt.stop()
            if self._capture is not None:
                self._capture.stop()
            if self._orchestrator is not None:
                self._orchestrator.finish()
        finally:
            self._capture = None
            self._stt = None
            self._orchestrator = None
            self.status = SessionStatus.STOPPED
        LOGGER.info("Session stopped.")

    def add_micro_note(self, text: str) -> None:
        """Add a micro-note only while a session is active."""
        if self._orchestrator is not None:
            self._orchestrator.add_manual_note(text)

    def _set_error(self, message: str) -> None:
        self.status = SessionStatus.ERROR
        self.last_error = message
        LOGGER.error(message)


class TrayApplication(QObject):
    """Expose Start, Stop, and Quit through a compact system-tray menu."""

    quit_requested = Signal()

    def __init__(self, controller: SessionController) -> None:
        super().__init__()
        self._controller = controller
        self._icon = pystray.Icon(
            "latchnote",
            _tray_image(),
            "Latchnote — Idle",
            pystray.Menu(
                pystray.MenuItem(lambda _: self._status_text(), None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Start Session", self._start, enabled=lambda _: controller.can_start),
                pystray.MenuItem("Stop Session", self._stop, enabled=lambda _: controller.can_stop),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", self._quit),
            ),
        )

    def run(self) -> None:
        """Start the tray icon alongside Qt's event loop."""
        self._icon.run_detached()

    def stop(self) -> None:
        """Remove the tray icon."""
        self._icon.stop()

    def _start(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self._controller.start_session()
        self._refresh(icon)

    def _stop(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self._controller.stop_session()
        self._refresh(icon)

    def _quit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self._controller.stop_session()
        icon.stop()
        self.quit_requested.emit()

    def _refresh(self, icon: pystray.Icon) -> None:
        icon.title = f"Latchnote — {self._status_text()}"
        if self._controller.last_error:
            icon.notify(self._controller.last_error, "Latchnote error")
        icon.update_menu()

    def _status_text(self) -> str:
        return self._controller.status.value.replace("_", " ").title()


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
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    app = QApplication([])
    controller = SessionController(load_settings(), args.title)
    micro_notes = MicroNoteController(controller.add_micro_note)
    hotkey = GlobalHotkeyListener(micro_notes.request_show)
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


if __name__ == "__main__":
    raise SystemExit(main())
