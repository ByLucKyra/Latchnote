"""Durable event journal and chronological Markdown export for sessions."""

import json
import logging
import math
import re
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session import Session

LOGGER = logging.getLogger(__name__)
_RESERVED = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$", re.IGNORECASE)


class JournalError(RuntimeError):
    """Raised when a session journal is corrupt or cannot be written."""


def _safe_filename(title: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", title).strip(" .-") or "untitled-session"
    return f"_{cleaned}" if _RESERVED.fullmatch(cleaned) else cleaned


def read_journal(path: Path) -> list[dict[str, object]]:
    """Read versioned events; ignore only a malformed final partial line."""
    try:
        data = path.read_bytes()
        lines = data.splitlines()
        events = []
        session_id = None
        sequence = 0
        for index, line in enumerate(lines):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                if (
                    not isinstance(event, dict)
                    or event.get("version") != 1
                    or not isinstance(event.get("sequence"), int)
                    or event.get("sequence", 0) < 1
                    or not all(isinstance(event.get(key), str) for key in ("session_id", "event_id", "type", "timestamp", "text"))
                    or _parse_seconds(event.get("timestamp", "")) < 0
                    or event.get("type") not in {"session", "session_metadata", "session_end", "transcript", "manual", "recovery_gap", "structured", "task_pending", "task_success"}
                ):
                    raise ValueError("unsupported journal event")
                kind = event["type"]
                if kind == "session" and not all(isinstance(event.get(key), str) for key in ("title", "date")):
                    raise ValueError("invalid session metadata")
                if kind == "session_metadata" and not isinstance(event.get("started_at"), str):
                    raise ValueError("invalid session start")
                if kind in {"task_pending", "task_success", "structured"} and not isinstance(event.get("task_id"), str):
                    raise ValueError("invalid task event")
                if kind == "session_end" and (not isinstance(event.get("complete"), bool) or not isinstance(event.get("duration_seconds"), int)):
                    raise ValueError("invalid session end")
                if kind == "recovery_gap" and (
                    not isinstance(event.get("end_seconds"), (int, float))
                    or not math.isfinite(event["end_seconds"])
                    or event["end_seconds"] < _parse_seconds(event["timestamp"])
                ):
                    raise ValueError("invalid recovery gap")
                if session_id is not None and event["session_id"] != session_id:
                    raise ValueError("multiple sessions in journal")
                if int(event["sequence"]) <= sequence:
                    raise ValueError("unordered event sequence")
            except (ValueError, AttributeError, TypeError) as error:
                if index == len(lines) - 1 and not data.endswith(b"\n"):
                    LOGGER.warning("Ignoring incomplete final journal line in %s", path)
                    break
                raise JournalError(f"Corrupt session journal at line {index + 1}.") from error
            events.append(event)
            session_id = event["session_id"]
            sequence = int(event["sequence"])
        return events
    except OSError as error:
        raise JournalError("Unable to read session journal.") from error


def _render(events: list[dict[str, object]]) -> str:
    session = next((event for event in events if event["type"] == "session"), None)
    if session is None:
        raise JournalError("Session journal has no session metadata.")
    title = str(session["title"])
    endings = [event for event in events if event["type"] == "session_end"]
    if endings:
        ending = max(endings, key=lambda event: int(event["sequence"]))
        duration = max(0, int(ending.get("duration_seconds", 0)))
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        status = "Complete" if ending.get("complete") else "Incomplete"
        details = f"**Date:** {session['date']}\n**Status:** {status}\n**Duration:** {hours:02}:{minutes:02}:{seconds:02}\n\n"
    else:
        details = f"**Date:** {session['date']}\n**Status:** In progress\n\n"
    output = [f"# Session: {title}\n", details, "---\n"]
    successful = {event.get("task_id") for event in events if event["type"] == "task_success"}
    latest_structured = {
        event.get("task_id"): event for event in events
        if event["type"] == "structured" and event.get("task_id") in successful
    }
    rendered = [event for event in events if event["type"] in {"transcript", "manual", "recovery_gap"}]
    rendered.extend(latest_structured.values())
    for event in sorted(rendered, key=lambda item: (str(item["timestamp"]), int(item["sequence"]))):
        timestamp, text = event["timestamp"], str(event["text"]).strip()
        if event["type"] == "transcript":
            body = text
        elif event["type"] == "manual":
            body = f"📌 **{text}**"
        elif event["type"] == "recovery_gap":
            end_time = _format_seconds(float(event["end_seconds"]))
            body = f"> Transcript gap to [{end_time}]: {text}. Reprocess the retained WAV separately; recovered text is not merged automatically."
        else:
            body = f"### Structured notes\n\n{text}"
        output.append(f"\n## [{timestamp}]\n\n{body}\n")
    return "".join(output)


class MarkdownWriter:
    """Append session events durably and maintain a rebuildable Markdown view."""

    def __init__(self, notes_dir: Path, session: "Session") -> None:
        self.session = session
        self._lock = RLock()
        notes_dir.mkdir(parents=True, exist_ok=True)
        stem = f"{session.started_at:%Y-%m-%d}_{_safe_filename(session.title)}"
        suffix = 0
        while True:
            self.path = notes_dir / f"{stem}{f'_{suffix}' if suffix else ''}.md"
            self.journal_path = self.path.with_suffix(".jsonl")
            if self.journal_path.exists():
                suffix += 1
                continue
            try:
                with self.path.open("x", encoding="utf-8"):
                    pass
                try:
                    self.journal_path.open("x", encoding="utf-8").close()
                except FileExistsError:
                    self.path.unlink()
                    suffix += 1
                    continue
                except OSError:
                    self.path.unlink(missing_ok=True)
                    raise
                break
            except FileExistsError:
                suffix += 1
        self.session_id = self.path.stem
        self._sequence = 0
        self._record("session", "00:00:00", "", title=session.title, date=f"{session.started_at:%Y-%m-%d %H:%M}")
        self._record("session_metadata", "00:00:00", "", started_at=session.started_at.isoformat())
        self._write_export()

    @classmethod
    def resume(cls, journal_path: Path) -> "MarkdownWriter":
        """Reopen an existing journal for an explicit pending-task retry."""
        from .session import Session

        events = read_journal(journal_path)
        metadata = next((event for event in events if event["type"] == "session"), None)
        if metadata is None:
            raise JournalError("Session journal has no session metadata.")
        writer = cls.__new__(cls)
        started = next((event.get("started_at") for event in events if event["type"] == "session_metadata"), None)
        writer.session = Session(str(metadata["title"]), datetime.fromisoformat(str(started)) if started else datetime.strptime(str(metadata["date"]), "%Y-%m-%d %H:%M"))
        writer._lock = RLock()
        writer.journal_path = journal_path
        writer.path = journal_path.with_suffix(".md")
        writer.session_id = str(events[0]["session_id"])
        writer._sequence = max(int(event["sequence"]) for event in events)
        return writer

    def append_transcript(self, text: str, timestamp: str) -> None:
        """Persist one final transcript segment."""
        self._record("transcript", timestamp, text)
        self._write_export()

    def append_manual_note(self, text: str, timestamp: str) -> None:
        """Persist one personal micro-note."""
        self._record("manual", timestamp, text)
        self._write_export()

    def append_recovery_gap(self, start_seconds: float, end_seconds: float, reason: str) -> None:
        """Journal a known source range that Whisper could not transcribe."""
        self._record("recovery_gap", _format_seconds(start_seconds), reason, end_seconds=end_seconds)
        self._write_export()

    def add_pending_task(self, task_id: str, text: str, timestamp: str) -> None:
        """Persist provider work before sending the request."""
        with self._lock:
            if task_id in {event.get("task_id") for event in read_journal(self.journal_path)}:
                return
            self._record("task_pending", timestamp, text, task_id=task_id)

    def complete_task(self, task_id: str, bullets: str, timestamp: str) -> None:
        """Persist successful provider output once, then rebuild the export."""
        with self._lock:
            events = read_journal(self.journal_path)
            if task_id in {event.get("task_id") for event in events if event["type"] == "task_success"}:
                return
            self._record("structured", timestamp, bullets, task_id=task_id)
            self._record("task_success", timestamp, "", task_id=task_id)
            events = read_journal(self.journal_path)
            endings = [event for event in events if event["type"] == "session_end"]
            if endings and not endings[-1].get("complete") and not self.pending_tasks():
                self._record(
                    "session_end", str(endings[-1]["timestamp"]), "", complete=True,
                    duration_seconds=int(endings[-1].get("duration_seconds", 0)),
                )
                events = read_journal(self.journal_path)
            self._write_export_locked(events)

    def finish_session(self, duration_seconds: int, complete: bool) -> None:
        """Persist final status and duration without losing the original on retry."""
        with self._lock:
            endings = [event for event in read_journal(self.journal_path) if event["type"] == "session_end"]
            if endings:
                duration_seconds = int(endings[-1].get("duration_seconds", duration_seconds))
            complete = complete and not self.pending_tasks()
            self._record(
                "session_end", "00:00:00", "", complete=complete,
                duration_seconds=max(0, duration_seconds),
            )
            self._write_export_locked(read_journal(self.journal_path))

    def pending_tasks(self) -> list[dict[str, object]]:
        """Return unfinished provider tasks for an explicit recovery action."""
        events = read_journal(self.journal_path)
        complete = {event.get("task_id") for event in events if event["type"] == "task_success"}
        latest = {event.get("task_id"): event for event in events if event["type"] == "task_pending"}
        return [event for task_id, event in latest.items() if task_id not in complete]

    def _record(self, event_type: str, timestamp: str, text: str, **extra: object) -> None:
        with self._lock:
            self._sequence += 1
            event = {
                "version": 1, "session_id": self.session_id, "event_id": uuid.uuid4().hex,
                "sequence": self._sequence, "type": event_type, "timestamp": timestamp,
                "text": text.strip(), **extra,
            }
            try:
                with self.journal_path.open("a", encoding="utf-8", newline="\n") as journal:
                    journal.write(json.dumps(event, ensure_ascii=False) + "\n")
                    journal.flush()
            except OSError as error:
                self._sequence -= 1
                raise JournalError("Unable to persist session event; Markdown was not updated.") from error

    def _write_export(self) -> None:
        with self._lock:
            self._write_export_locked(read_journal(self.journal_path))

    def _write_export_locked(self, events: list[dict[str, object]]) -> None:
        content = _render(events)
        try:
            self.path.write_text(content, encoding="utf-8")
        except OSError as error:
            LOGGER.error("Markdown export failed; journal retained at %s", self.journal_path)
            raise JournalError("Session journal saved, but Markdown export failed.") from error

    @staticmethod
    def rebuild(journal_path: Path) -> Path:
        """Rebuild a Markdown export atomically from its journal."""
        events = read_journal(journal_path)
        content = _render(events)
        output = journal_path.with_suffix(".md")
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="\n", dir=output.parent,
                prefix=output.name + ".", suffix=".tmp", delete=False,
            ) as file:
                temporary = Path(file.name)
                file.write(content)
            temporary.replace(output)
        except OSError as error:
            if temporary:
                temporary.unlink(missing_ok=True)
            raise JournalError("Unable to rebuild Markdown export; journal retained.") from error
        return output


def _format_seconds(seconds: float) -> str:
    hours, remainder = divmod(max(0, int(seconds)), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def _parse_seconds(timestamp: str) -> int:
    parts = timestamp.split(":")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError("invalid source timestamp")
    hours, minutes, seconds = (int(part) for part in parts)
    if minutes > 59 or seconds > 59:
        raise ValueError("invalid source timestamp")
    return hours * 3600 + minutes * 60 + seconds
