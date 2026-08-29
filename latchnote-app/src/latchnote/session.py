"""Recording-session data and transcript chunk orchestration."""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Lock, Thread

from .structurer import StructuringError
from .writer import MarkdownWriter

LOGGER = logging.getLogger(__name__)
StructureChunk = Callable[[str], str]


class SessionStatus(str, Enum):
    """A session's current lifecycle state."""

    IDLE = "idle"
    RECORDING = "recording"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class Session:
    """Metadata for one local Latchnote session."""

    title: str
    started_at: datetime = field(default_factory=datetime.now)
    status: SessionStatus = SessionStatus.IDLE

    def timestamp(self, at: datetime | None = None) -> str:
        """Return elapsed time in ``HH:MM:SS`` format."""
        elapsed = max(0, int(((at or datetime.now()) - self.started_at).total_seconds()))
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"


@dataclass(frozen=True)
class TranscriptChunk:
    """New final transcript text accumulated for one structuring request."""

    start_seconds: int
    text: str


class TranscriptChunker:
    """Accumulate final transcript text into non-overlapping chunks."""

    def __init__(self, chunk_seconds: int = 120) -> None:
        self._chunk_seconds = chunk_seconds
        self._chunk_started_at = 0
        self._parts: list[str] = []

    def add(self, text: str, elapsed_seconds: int) -> TranscriptChunk | None:
        """Add text and return a completed chunk once its interval has elapsed."""
        self._parts.append(text)
        # ponytail: chunks close on the next final segment; add a timer only if exact boundaries matter.
        if elapsed_seconds - self._chunk_started_at < self._chunk_seconds:
            return None
        return self._take(elapsed_seconds)

    def flush(self, elapsed_seconds: int) -> TranscriptChunk | None:
        """Return the remaining new transcript at session end."""
        if not self._parts:
            return None
        return self._take(elapsed_seconds)

    def _take(self, next_start: int) -> TranscriptChunk:
        chunk = TranscriptChunk(self._chunk_started_at, " ".join(self._parts))
        self._parts = []
        self._chunk_started_at = next_start
        return chunk


class SessionOrchestrator:
    """Write final transcript and structure each new chunk in the background."""

    def __init__(
        self,
        session: Session,
        writer: MarkdownWriter,
        structure_chunk: StructureChunk,
        chunk_seconds: int = 120,
    ) -> None:
        self._session = session
        self._writer = writer
        self._structure_chunk = structure_chunk
        self._chunker = TranscriptChunker(chunk_seconds)
        self._failed_chunks: list[TranscriptChunk] = []
        self._threads: list[Thread] = []
        self._lock = Lock()

    def add_final_transcript(self, text: str, at: datetime | None = None) -> None:
        """Persist a final transcript segment and schedule its completed chunk."""
        recorded_at = at or datetime.now()
        elapsed_seconds = max(0, int((recorded_at - self._session.started_at).total_seconds()))
        self._writer.append_transcript(text, self._session.timestamp(recorded_at))
        chunk = self._chunker.add(text, elapsed_seconds)
        if chunk is not None:
            self._schedule(chunk)

    def add_manual_note(self, text: str, at: datetime | None = None) -> None:
        """Persist a user micro-note at its current session timestamp."""
        recorded_at = at or datetime.now()
        self._writer.append_manual_note(text, self._session.timestamp(recorded_at))

    def finish(self, at: datetime | None = None) -> None:
        """Schedule the final partial chunk and wait briefly for active requests."""
        recorded_at = at or datetime.now()
        elapsed_seconds = max(0, int((recorded_at - self._session.started_at).total_seconds()))
        chunk = self._chunker.flush(elapsed_seconds)
        if chunk is not None:
            self._schedule(chunk)
        self.wait_for_structuring()

    def retry_failed(self) -> None:
        """Retry chunks whose raw transcript was preserved after a Claude failure."""
        with self._lock:
            failed_chunks, self._failed_chunks = self._failed_chunks, []
        for chunk in failed_chunks:
            self._schedule(chunk)

    def wait_for_structuring(self, timeout: float = 10) -> None:
        """Wait up to ``timeout`` seconds for outstanding structuring requests."""
        with self._lock:
            threads, self._threads = self._threads, []
        for thread in threads:
            thread.join(timeout=timeout)

    def _schedule(self, chunk: TranscriptChunk) -> None:
        thread = Thread(target=self._structure, args=(chunk,), daemon=True)
        with self._lock:
            self._threads.append(thread)
        thread.start()

    def _structure(self, chunk: TranscriptChunk) -> None:
        try:
            bullets = self._structure_chunk(chunk.text)
        except StructuringError as error:
            with self._lock:
                self._failed_chunks.append(chunk)
            LOGGER.warning("Structured notes deferred: %s", error)
            return
        self._writer.append_structured_notes(
            bullets, self._format_seconds(chunk.start_seconds)
        )

    @staticmethod
    def _format_seconds(elapsed_seconds: int) -> str:
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
