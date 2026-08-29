from datetime import datetime, timedelta

from latchnote.session import Session
from latchnote.writer import MarkdownWriter


def test_writer_formats_session_and_timestamp(tmp_path) -> None:
    session = Session("Python: Lists", started_at=datetime(2026, 8, 29, 9, 0))
    writer = MarkdownWriter(tmp_path, session)
    writer.append_transcript("Lists preserve order.", session.timestamp(session.started_at + timedelta(seconds=65)))
    writer.append_manual_note("review append", "00:02:00")

    assert writer.path.name == "2026-08-29_Python- Lists.md"
    assert writer.path.read_text(encoding="utf-8") == (
        "# Session: Python: Lists\n"
        "**Date:** 2026-08-29 09:00\n\n"
        "---\n\n"
        "## [00:01:05]\n\n"
        "Lists preserve order.\n\n"
        "## [00:02:00]\n\n"
        "📌 **review append**\n"
    )
