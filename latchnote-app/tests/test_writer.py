from datetime import datetime, timedelta
from threading import Event, Lock

import pytest

from latchnote.session import Session, SessionOrchestrator
from latchnote.writer import JournalError, MarkdownWriter, read_journal


def test_writer_formats_session_and_timestamp(tmp_path) -> None:
    session = Session("Python: Lists", started_at=datetime(2026, 8, 29, 9, 0))
    writer = MarkdownWriter(tmp_path, session)
    writer.append_transcript("Lists preserve order.", session.timestamp(session.started_at + timedelta(seconds=65)))
    writer.append_manual_note("review append", "00:02:00")

    assert writer.path.name == "2026-08-29_Python- Lists.md"
    assert writer.path.read_text(encoding="utf-8") == (
        "# Session: Python: Lists\n"
        "**Date:** 2026-08-29 09:00\n**Status:** In progress\n\n"
        "---\n\n"
        "## [00:01:05]\n\n"
        "Lists preserve order.\n\n"
        "## [00:02:00]\n\n"
        "📌 **review append**\n"
    )


def test_rebuild_is_chronological_and_ignores_only_truncated_tail(tmp_path) -> None:
    session = Session("Course", started_at=datetime(2026, 10, 2, 9))
    writer = MarkdownWriter(tmp_path, session)
    writer.append_manual_note("later", "00:00:03")
    writer.append_transcript("pertama / first 講義", "00:00:01")
    writer.add_pending_task("chunk-1", "source", "00:00:02")
    writer.complete_task("chunk-1", "- structured", "00:00:02")
    with writer.journal_path.open("ab") as journal:
        journal.write(b'{"version":')

    before = writer.path.read_text(encoding="utf-8")
    rebuilt = MarkdownWriter.rebuild(writer.journal_path)
    content = rebuilt.read_text(encoding="utf-8")
    assert content == before
    assert content.index("pertama / first 講義") < content.index("structured") < content.index("later")
    assert len([event for event in read_journal(writer.journal_path) if event["type"] == "structured"]) == 1


def test_journal_middle_corruption_fails_closed(tmp_path) -> None:
    writer = MarkdownWriter(tmp_path, Session("Course", started_at=datetime(2026, 10, 2, 9)))
    writer.append_transcript("keep", "00:00:01")
    lines = writer.journal_path.read_bytes().splitlines()
    writer.journal_path.write_bytes(lines[0] + b"\nnot-json\n" + lines[1] + b"\n")
    with pytest.raises(JournalError, match="line 2"):
        MarkdownWriter.rebuild(writer.journal_path)


def test_recovery_gap_is_durable_and_visible_in_export(tmp_path) -> None:
    writer = MarkdownWriter(tmp_path, Session("Course", started_at=datetime(2026, 10, 2, 9)))
    writer.append_recovery_gap(12, 17, "Whisper queue was full")
    content = writer.path.read_text(encoding="utf-8")
    assert "Transcript gap to [00:00:17]" in content
    assert "Reprocess the retained WAV separately" in content


def test_failed_windows_replace_keeps_previous_export(tmp_path, monkeypatch) -> None:
    writer = MarkdownWriter(tmp_path, Session("Course", started_at=datetime(2026, 10, 2, 9)))
    writer.append_transcript("keep old export", "00:00:01")
    before = writer.path.read_bytes()

    def fail_replace(self, target):
        raise PermissionError("destination open")

    monkeypatch.setattr(type(writer.path), "replace", fail_replace)
    with pytest.raises(JournalError, match="Unable to rebuild"):
        MarkdownWriter.rebuild(writer.journal_path)
    assert writer.path.read_bytes() == before
    assert not list(tmp_path.glob(writer.path.name + ".*.tmp"))


def test_reserved_windows_filename_and_collision_share_identity(tmp_path) -> None:
    session = Session("CON", started_at=datetime(2026, 10, 2, 9))
    first = MarkdownWriter(tmp_path, session)
    second = MarkdownWriter(tmp_path, session)
    assert first.path.name == "2026-10-02__CON.md"
    assert second.path.stem == f"{first.session_id}_1"
    assert second.journal_path.with_suffix(".md") == second.path


def test_pending_task_retries_after_resume_without_duplicate_export(tmp_path) -> None:
    session = Session("Course", started_at=datetime(2026, 10, 2, 9))
    writer = MarkdownWriter(tmp_path, session)
    writer.append_transcript("source", "00:00:02")
    writer.add_pending_task("task-1", "source", "00:00:02")
    resumed = MarkdownWriter.resume(writer.journal_path)
    orchestrator = SessionOrchestrator(resumed.session, resumed, lambda _: "- recovered", 1)
    orchestrator.retry_pending()
    orchestrator.finish(timeout=2)
    resumed.complete_task("task-1", "- duplicate", "00:00:02")
    assert resumed.pending_tasks() == []
    assert resumed.path.read_text(encoding="utf-8").count("### Structured notes") == 1


def test_structuring_uses_one_worker_for_all_chunks(tmp_path) -> None:
    active = maximum = calls = 0
    lock = Lock()
    entered, release = Event(), Event()

    def structure(text: str) -> str:
        nonlocal active, maximum, calls
        with lock:
            active += 1
            calls += 1
            maximum = max(maximum, active)
        entered.set()
        assert release.wait(2)
        with lock:
            active -= 1
        return f"- {text}"

    session = Session("Course", started_at=datetime(2026, 10, 2, 9))
    writer = MarkdownWriter(tmp_path, session)
    orchestrator = SessionOrchestrator(session, writer, structure, 1)
    try:
        orchestrator.add_final_transcript("1", session.started_at + timedelta(seconds=1))
        assert entered.wait(2)
        for second in (2, 3):
            orchestrator.add_final_transcript(str(second), session.started_at + timedelta(seconds=second))
    finally:
        release.set()
        orchestrator.finish(timeout=2)
    assert calls == 3 and maximum == 1


def test_shutdown_deadline_leaves_pending_task_marked(tmp_path) -> None:
    entered, release = Event(), Event()

    def structure(text: str) -> str:
        entered.set()
        assert release.wait(2)
        return f"- {text}"

    session = Session("Course", started_at=datetime(2026, 10, 2, 9))
    writer = MarkdownWriter(tmp_path, session)
    orchestrator = SessionOrchestrator(session, writer, structure, 1)
    orchestrator.add_final_transcript("pending source", session.started_at + timedelta(seconds=1))
    assert entered.wait(2)
    try:
        assert orchestrator.finish(timeout=0.01) is False
        assert len(writer.pending_tasks()) == 1
        assert "**Status:** Incomplete" in writer.path.read_text(encoding="utf-8")
        duration = next(event["duration_seconds"] for event in read_journal(writer.journal_path) if event["type"] == "session_end")
    finally:
        release.set()
        orchestrator._worker.join(timeout=2)
    content = writer.path.read_text(encoding="utf-8")
    assert "**Status:** Complete" in content
    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)
    assert f"**Duration:** {hours:02}:{minutes:02}:{seconds:02}" in content
