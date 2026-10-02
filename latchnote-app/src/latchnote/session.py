"""Recording-session data and transcript chunk orchestration."""

import logging
import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from queue import Queue
from threading import Lock, Thread
from time import monotonic

from .structurer import StructuringError
from .writer import JournalError, MarkdownWriter

LOGGER = logging.getLogger(__name__)
StructureChunk = Callable[[str], str]


class SessionStatus(str, Enum):
    """A session's current lifecycle state."""

    IDLE = "idle"
    RECORDING = "recording"
    RETRYING = "retrying"
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
        structure_chunk: StructureChunk | None = None,
        chunk_seconds: int = 120,
    ) -> None:
        self._session = session
        self._writer = writer
        self._structure_chunk = structure_chunk
        self._chunker = TranscriptChunker(chunk_seconds)
        self._failed_chunks: list[TranscriptChunk] = []
        self._lock = Lock()
        self._chunk_lock = Lock()
        self._queue: Queue[tuple[str, TranscriptChunk] | None] = Queue()
        self._queued: set[str] = set()
        self._worker = Thread(target=self._run_worker, name="notes-structurer", daemon=True) if structure_chunk else None
        if self._worker:
            self._worker.start()

    def add_final_transcript(self, text: str, at: datetime | None = None) -> None:
        """Persist a final transcript segment and schedule its completed chunk."""
        recorded_at = at or datetime.now()
        elapsed_seconds = max(0, int((recorded_at - self._session.started_at).total_seconds()))
        self._writer.append_transcript(text, self._session.timestamp(recorded_at))
        with self._chunk_lock:
            chunk = self._chunker.add(text, elapsed_seconds) if self._structure_chunk else None
        if chunk is not None:
            self._schedule(chunk)

    def add_manual_note(self, text: str, at: datetime | None = None) -> None:
        """Persist a user micro-note at its current session timestamp."""
        recorded_at = at or datetime.now()
        self._writer.append_manual_note(text, self._session.timestamp(recorded_at))

    def add_recovery_gap(self, start_seconds: float, end_seconds: float, reason: str) -> None:
        """Persist a missing source-audio range without merging guessed recovery text."""
        self._writer.append_recovery_gap(start_seconds, end_seconds, reason)

    def finish(self, at: datetime | None = None, timeout: float = 10, source_success: bool = True) -> bool:
        """Drain provider work by a total deadline and report unfinished tasks."""
        deadline = monotonic() + timeout
        recorded_at = at or datetime.now()
        elapsed_seconds = max(0, int((recorded_at - self._session.started_at).total_seconds()))
        with self._chunk_lock:
            chunk = self._chunker.flush(elapsed_seconds)
        if chunk is not None:
            self._schedule(chunk)
        self.wait_for_structuring(max(0, deadline - monotonic()))
        if self._worker and self._worker.is_alive():
            self._queue.put(None)
            self._worker.join(timeout=max(0, deadline - monotonic()))
        complete = source_success and not self._writer.pending_tasks()
        duration = max(0, int((recorded_at - self._session.started_at).total_seconds()))
        self._writer.finish_session(duration, complete)
        return complete

    def retry_failed(self) -> None:
        """Retry provider tasks that remain pending in the session journal."""
        self.retry_pending()

    def retry_pending(self) -> None:
        """Requeue durable provider tasks without duplicating completed output."""
        if not self._worker or not self._worker.is_alive():
            return
        for task in self._writer.pending_tasks():
            chunk = TranscriptChunk(self._parse_timestamp(str(task["timestamp"])), str(task["text"]))
            task_id = str(task["task_id"])
            with self._lock:
                if task_id in self._queued:
                    continue
                self._queued.add(task_id)
            self._queue.put((task_id, chunk))

    def wait_for_structuring(self, timeout: float = 10) -> None:
        """Wait up to ``timeout`` seconds for outstanding structuring requests."""
        deadline = monotonic() + timeout
        with self._queue.all_tasks_done:
            while self._queue.unfinished_tasks:
                remaining = deadline - monotonic()
                if remaining <= 0:
                    return
                self._queue.all_tasks_done.wait(remaining)

    def _schedule(self, chunk: TranscriptChunk) -> None:
        task_id = hashlib.sha256(f"{self._writer.session_id}\0{chunk.start_seconds}\0{chunk.text}".encode()).hexdigest()
        timestamp = self._format_seconds(chunk.start_seconds)
        self._writer.add_pending_task(task_id, chunk.text, timestamp)
        if self._worker:
            with self._lock:
                if task_id in self._queued:
                    return
                self._queued.add(task_id)
            self._queue.put((task_id, chunk))

    def _run_worker(self) -> None:
        while True:
            task = self._queue.get()
            try:
                if task is None:
                    return
                task_id, chunk = task
                try:
                    bullets = self._structure_chunk(chunk.text)
                except StructuringError as error:
                    with self._lock:
                        self._failed_chunks.append(chunk)
                    LOGGER.warning("Structured notes deferred: %s", error)
                    continue
                self._writer.complete_task(task_id, bullets, self._format_seconds(chunk.start_seconds))
            except (JournalError, OSError) as error:
                LOGGER.error("Structured notes remain pending: %s", error)
            finally:
                if task is not None:
                    with self._lock:
                        self._queued.discard(task[0])
                self._queue.task_done()

    @staticmethod
    def _parse_timestamp(timestamp: str) -> int:
        hours, minutes, seconds = (int(part) for part in timestamp.split(":"))
        return hours * 3600 + minutes * 60 + seconds

    @staticmethod
    def _format_seconds(elapsed_seconds: int) -> str:
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
