"""WASAPI loopback capture with a local WAV recovery recording."""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from wave import Wave_write, open as open_wave

try:
    import pyaudiowpatch as pyaudio
except ModuleNotFoundError:  # Allows configuration and Markdown work without audio installed.
    pyaudio = None

LOGGER = logging.getLogger(__name__)
AudioChunkHandler = Callable[[bytes], None]


class AudioCaptureError(RuntimeError):
    """Raised when Windows loopback capture cannot start."""


@dataclass(frozen=True)
class AudioFormat:
    """The native format exposed by the selected loopback device."""

    channels: int
    rate: int
    sample_width: int


class WasapiLoopbackCapture:
    """Capture default Windows speaker output into a recoverable WAV file."""

    def __init__(self, data_dir: Path, on_chunk: AudioChunkHandler | None = None) -> None:
        self._data_dir = data_dir
        self._on_chunk = on_chunk
        self._audio: object | None = None
        self._stream: object | None = None
        self._wave_file: Wave_write | None = None
        self._lock = Lock()
        self.format: AudioFormat | None = None
        self.path: Path | None = None

    def start(self, session_slug: str) -> Path:
        """Start capture and return the local WAV recovery path."""
        if self._stream is not None:
            raise AudioCaptureError("Audio capture is already running.")
        if pyaudio is None:
            raise AudioCaptureError("PyAudioWPatch is not installed.")

        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._audio = pyaudio.PyAudio()
        try:
            device = self._audio.get_default_wasapi_loopback()
            self.format = AudioFormat(
                channels=int(device["maxInputChannels"]),
                rate=int(device["defaultSampleRate"]),
                sample_width=self._audio.get_sample_size(pyaudio.paInt16),
            )
            self.path = self._data_dir / f"{session_slug}.wav"
            self._wave_file = open_wave(str(self.path), "wb")
            self._wave_file.setnchannels(self.format.channels)
            self._wave_file.setsampwidth(self.format.sample_width)
            self._wave_file.setframerate(self.format.rate)
            self._stream = self._audio.open(
                format=pyaudio.paInt16,
                channels=self.format.channels,
                rate=self.format.rate,
                input=True,
                input_device_index=device["index"],
                frames_per_buffer=1024,
                stream_callback=self._record_chunk,
            )
        except (OSError, LookupError) as error:
            self.stop()
            raise AudioCaptureError(f"Unable to start WASAPI loopback: {error}") from error

        LOGGER.info("Capturing default Windows audio to %s", self.path)
        return self.path

    def set_chunk_handler(self, on_chunk: AudioChunkHandler) -> None:
        """Set the live-audio consumer after the native format is known."""
        with self._lock:
            self._on_chunk = on_chunk

    def stop(self) -> None:
        """Stop capture and close the WAV file without discarding it."""
        with self._lock:
            if self._stream is not None:
                self._stream.stop_stream()
                self._stream.close()
                self._stream = None
            if self._wave_file is not None:
                self._wave_file.close()
                self._wave_file = None
            if self._audio is not None:
                self._audio.terminate()
                self._audio = None
        LOGGER.info("Audio capture stopped.")

    def _record_chunk(
        self, in_data: bytes, frame_count: int, time_info: dict[str, float], status: int
    ) -> tuple[bytes, int]:
        with self._lock:
            if self._wave_file is not None:
                self._wave_file.writeframes(in_data)
        if self._on_chunk is not None:
            self._on_chunk(in_data)
        return in_data, pyaudio.paContinue
