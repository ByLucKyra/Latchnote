# Latchnote — Project Rules

Rules for AI-assisted development on this codebase. These are always active.

---

## Identity

Latchnote is a **Windows desktop companion app** for solo online learners. It captures system audio via WASAPI loopback, transcribes it in real time with Deepgram, structures notes with Claude API, and lets the user drop manual micro-notes via a global hotkey — all outputting to local Markdown files.

## Stack (locked for MVP)

- **Language:** Python 3.12+
- **Audio capture:** PyAudioWPatch (WASAPI loopback)
- **Speech-to-text:** Deepgram streaming API
- **Note structuring:** Anthropic Claude API
- **UI / hotkey popup:** PySide6 + `keyboard` (global hotkey)
- **System tray:** `pystray`
- **Output:** Local `.md` files, plain Markdown

Do not introduce new frameworks, UI toolkits, or runtime dependencies without explicit user approval. Prefer stdlib and what's already installed.

## Architecture

```
audio_capture.py  →  stt_client.py  →  session.py  →  structurer.py  →  writer.py
                                            ↑
                                     hotkey_listener.py
```

- **`audio_capture.py`** — WASAPI loopback audio stream
- **`stt_client.py`** — Deepgram streaming client, emits timestamped transcript segments
- **`session.py`** — Orchestrates a recording session: accumulates transcript chunks, triggers structuring every ~2-3 min, interleaves micro-notes
- **`structurer.py`** — Sends raw transcript chunks to Claude API, returns bullet-point Markdown
- **`writer.py`** — Appends structured notes + micro-notes to the session `.md` file chronologically
- **`hotkey_listener.py`** — Global hotkey (`Ctrl+Space`), floating input popup (PySide6), emits timestamped micro-notes back to session
- **`main.py`** — Entry point, wires everything together, starts system tray icon

Keep modules focused. One responsibility per file. No god-objects.

## Coding Conventions

- All code in a single top-level `src/latchnote/` package. No nested sub-packages unless genuinely needed.
- Type hints on all function signatures. No `Any` unless unavoidable.
- Docstrings on public functions and classes — one-liner is fine, skip for trivial helpers.
- Use `logging` (stdlib) for all diagnostic output. No `print()` in committed code.
- Config values (API keys, hotkey binding, chunk interval) go in a single `config.py` or `.env` file. Never hardcoded in logic modules.
- Error handling: catch specific exceptions. Never bare `except:`. API calls and audio streams must have retry/graceful-failure paths — a crash during a 60-minute session is unacceptable.
- Async: use `asyncio` where the library demands it (Deepgram SDK). Keep sync code sync. Don't mix paradigms in one module without reason.

## Markdown Output Format

Session files follow this structure:

```markdown
# Session: <title>
**Date:** YYYY-MM-DD HH:MM
**Duration:** X minutes

---

## [00:00 – 02:30]

- Bullet point from AI structuring
- Another point

## [02:30 – 05:00]

- 📌 **user typed keyword here** ← micro-note, always with 📌 prefix
- AI-structured bullet from this chunk
```

- Micro-notes are prefixed with `📌` and bold text — visually distinct from AI bullets.
- Chunks are grouped by time range headers.
- No HTML, no proprietary formatting. Must render cleanly in Obsidian, Notion, and any plaintext editor.

## LLM Structuring Rules

When prompting Claude to structure transcript chunks:

- **Preserve** technical terms, proper nouns, code identifiers, and library/framework names exactly as spoken.
- **Strip** filler words ("uh", "um", "you know"), false starts, and repetitions.
- **Never hallucinate** — do not add information not present in the source transcript.
- **Output** concise bullet points. No paragraph prose. No headers within a chunk (the time-range header is added by the writer).
- **Bilingual awareness** — Indonesian/English code-switching is expected. Keep both languages as-is; do not translate.

## Testing

- Core logic (chunking, markdown formatting, timestamp math) should have unit tests in `tests/`.
- Use `pytest`. No fixtures or mocking frameworks unless the test genuinely needs them.
- Audio capture and API integrations: manual testing during dogfooding. Don't mock WASAPI or Deepgram in unit tests — it adds complexity for no real coverage.

## What NOT to Build (MVP)

These are explicitly out of scope per the PRD. Do not implement or scaffold for:

- Screen OCR / on-screen content capture
- macOS or mobile support
- Cloud sync or user accounts
- Flashcards, quizzes, or spaced repetition
- Pricing or subscription logic
- "Invisible" or "undetectable" overlay behavior

## File Naming

- Session output: `YYYY-MM-DD_<session-title>.md` in a `notes/` directory (user-configurable).
- Source code: `snake_case.py`, no abbreviations.
- Test files: `test_<module>.py` mirroring the source module.

## Git

- Commit messages: imperative mood, concise (`Add audio capture module`, `Fix chunk boundary timing`).
- `.env` and API keys: never committed. Use `.env.example` as template.
- Keep `.gitignore` current for Python (`__pycache__/`, `.env`, `*.pyc`, `dist/`, etc.).
