from datetime import datetime, timedelta

from latchnote.session import Session, SessionOrchestrator, TranscriptChunker
from latchnote.writer import MarkdownWriter


def test_chunker_emits_new_text_once() -> None:
    chunker = TranscriptChunker(chunk_seconds=120)

    assert chunker.add("first segment", 0) is None
    first_chunk = chunker.add("second segment", 121)
    final_chunk = chunker.flush(130)

    assert first_chunk is not None
    assert first_chunk.text == "first segment second segment"
    assert final_chunk is None


def test_orchestrator_writes_transcript_and_structured_notes(tmp_path) -> None:
    started_at = datetime(2026, 8, 30, 9, 0)
    session = Session("Chunk test", started_at=started_at)
    writer = MarkdownWriter(tmp_path, session)
    orchestrator = SessionOrchestrator(session, writer, lambda text: f"- {text}", 120)

    orchestrator.add_final_transcript("Only this text.", started_at + timedelta(seconds=121))
    orchestrator.wait_for_structuring()

    content = writer.path.read_text(encoding="utf-8")
    assert "## [00:02:01]" in content
    assert "Only this text." in content
    assert "### Structured notes\n\n- Only this text." in content


def test_orchestrator_writes_manual_note(tmp_path) -> None:
    started_at = datetime(2026, 8, 30, 9, 0)
    session = Session("Manual note", started_at=started_at)
    writer = MarkdownWriter(tmp_path, session)
    orchestrator = SessionOrchestrator(session, writer, lambda text: text)

    orchestrator.add_manual_note("review append", started_at + timedelta(seconds=42))

    assert "## [00:00:42]" in writer.path.read_text(encoding="utf-8")
    assert "📌 **review append**" in writer.path.read_text(encoding="utf-8")
