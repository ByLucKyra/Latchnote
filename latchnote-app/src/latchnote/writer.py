"""Plain-Markdown output for Latchnote sessions."""

import re
from pathlib import Path

from .session import Session


def _safe_filename(title: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", title).strip(" .-")
    return cleaned or "untitled-session"


class MarkdownWriter:
    """Append transcript and manual notes to one session file."""

    def __init__(self, notes_dir: Path, session: Session) -> None:
        self._session = session
        notes_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{session.started_at:%Y-%m-%d}_{_safe_filename(session.title)}.md"
        self.path = notes_dir / filename
        self.path.write_text(
            f"# Session: {session.title}\n"
            f"**Date:** {session.started_at:%Y-%m-%d %H:%M}\n\n"
            "---\n",
            encoding="utf-8",
        )

    def append_transcript(self, text: str, timestamp: str) -> None:
        """Append one final transcript segment."""
        self._append(f"\n## [{timestamp}]\n\n{text.strip()}\n")

    def append_manual_note(self, text: str, timestamp: str) -> None:
        """Append a visually distinct user micro-note."""
        self._append(f"\n## [{timestamp}]\n\n📌 **{text.strip()}**\n")

    def _append(self, text: str) -> None:
        with self.path.open("a", encoding="utf-8") as notes_file:
            notes_file.write(text)
