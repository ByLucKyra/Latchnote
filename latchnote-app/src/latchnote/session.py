"""Recording-session data shared by capture, transcription, and writing."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


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
