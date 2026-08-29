"""Deepgram live transcription for captured PCM audio."""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from queue import Full, Queue
from threading import Event, Thread

from .audio_capture import AudioFormat

LOGGER = logging.getLogger(__name__)
TranscriptHandler = Callable[["TranscriptSegment"], None]


class SttError(RuntimeError):
    """Raised when the live transcription connection cannot start."""


@dataclass(frozen=True)
class TranscriptSegment:
    """One final Deepgram transcript result."""

    text: str


class DeepgramSttClient:
    """Send PCM chunks to Deepgram without blocking the audio callback."""

    def __init__(
        self, api_key: str, audio_format: AudioFormat, on_final: TranscriptHandler
    ) -> None:
        self._api_key = api_key
        self._audio_format = audio_format
        self._on_final = on_final
        self._connection: object | None = None
        self._audio_queue: Queue[bytes | None] = Queue(maxsize=128)
        self._stopped = Event()
        self._worker: Thread | None = None
        self.last_error: str | None = None

    def start(self) -> None:
        """Open the live connection and begin sending queued audio."""
        if self._worker is not None:
            raise SttError("Live transcription is already running.")
        if not self._api_key:
            raise SttError("DEEPGRAM_API_KEY is not configured.")

        try:
            from deepgram import DeepgramClient
            from deepgram.core.events import EventType

            client = DeepgramClient(api_key=self._api_key)
            self._connection = client.listen.v1.connect(
                model="nova-3",
                language="multi",
                encoding="linear16",
                sample_rate=self._audio_format.rate,
                channels=self._audio_format.channels,
                interim_results=True,
                punctuate=True,
                smart_format=True,
            )
            self._connection.on(EventType.MESSAGE, self._handle_message)
            self._connection.on(EventType.ERROR, self._handle_error)
            self._connection.start_listening()
        except (ImportError, OSError, RuntimeError) as error:
            self._connection = None
            self.last_error = str(error)
            raise SttError(f"Unable to start Deepgram live transcription: {error}") from error

        self._stopped.clear()
        self._worker = Thread(target=self._send_queued_audio, name="deepgram-stt", daemon=True)
        self._worker.start()
        LOGGER.info("Deepgram live transcription started.")

    def submit_audio(self, audio: bytes) -> None:
        """Queue captured PCM audio; recovery WAV remains authoritative if queue is full."""
        if self._stopped.is_set() or self._worker is None:
            return
        try:
            self._audio_queue.put_nowait(audio)
        except Full:
            self.last_error = "Live transcription queue is full; recovery audio is retained."
            LOGGER.warning(self.last_error)

    def stop(self) -> None:
        """Stop live transcription; the local recovery WAV remains intact."""
        if self._worker is None:
            return
        self._stopped.set()
        try:
            self._audio_queue.put_nowait(None)
        except Full:
            pass
        self._worker.join(timeout=5)
        self._worker = None
        if self._connection is not None:
            self._connection.send_finalize()
            self._connection.send_close_stream()
            self._connection = None
        LOGGER.info("Deepgram live transcription stopped.")

    def retry(self) -> None:
        """Reconnect after a recoverable live-transcription failure."""
        self.stop()
        self.start()

    def _send_queued_audio(self) -> None:
        while not self._stopped.is_set():
            audio = self._audio_queue.get()
            if audio is None:
                return
            try:
                if self._connection is not None:
                    self._connection.send_media(audio)
            except (OSError, RuntimeError) as error:
                self._handle_error(error)
                return

    def _handle_message(self, message: object) -> None:
        if not getattr(message, "is_final", False):
            return
        channel = getattr(message, "channel", None)
        alternatives = getattr(channel, "alternatives", ())
        if not alternatives:
            return
        text = str(getattr(alternatives[0], "transcript", "")).strip()
        if text:
            self._on_final(TranscriptSegment(text=text))

    def _handle_error(self, error: object) -> None:
        self.last_error = str(error)
        LOGGER.error("Deepgram live transcription failed: %s", error)
