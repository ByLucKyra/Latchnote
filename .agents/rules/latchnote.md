# Latchnote — Project Rules

Rules for AI-assisted development on this codebase. These are always active.

---

## Identity

Latchnote is a **Windows desktop companion app** for solo online learners. It captures system audio via WASAPI loopback, transcribes locally with Whisper, optionally structures notes through a user-configured AI API, and lets the user drop manual micro-notes via a global hotkey — all outputting to local Markdown files. The October 2, 2026 user decision replaces Deepgram/Anthropic with local raw transcription for entry-level 8 GB machines and customizable AI formatting.

## Stack (locked for MVP)

- **Language:** Python 3.12+
- **Audio capture:** PyAudioWPatch (WASAPI loopback)
- **Speech-to-text:** faster-whisper, CPU INT8; default multilingual `base`, two threads
- **Note structuring:** Optional OpenAI-compatible chat endpoint via HTTPX
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
- **`stt_client.py`** — Local Whisper worker, emits source-timestamped final transcript windows
- **`session.py`** — Orchestrates a recording session: accumulates transcript chunks, triggers structuring every ~2-3 min, interleaves micro-notes
- **`structurer.py`** — Sends text chunks to optional provider with standard factual rules plus custom presentation instructions
- **`writer.py`** — Journals session events durably and maintains a chronological `.md` export
- **`hotkey_listener.py`** — Global hotkey (`Ctrl+Space`), floating input popup (PySide6), emits timestamped micro-notes back to session
- **`__main__.py`** — Entry point, tray app, explicit model download and saved-audio CLI

Keep modules focused. One responsibility per file. No god-objects.

## Coding Conventions

- All code in a single top-level `src/latchnote/` package. No nested sub-packages unless genuinely needed.
- Type hints on all function signatures. No `Any` unless unavoidable.
- Docstrings on public functions and classes — one-liner is fine, skip for trivial helpers.
- Use `logging` (stdlib) for all diagnostic output. No `print()` in committed code.
- Config values (API keys, hotkey binding, chunk interval) go in a single `config.py` or `.env` file. Never hardcoded in logic modules.
- Error handling: catch specific exceptions. Never bare `except:`. API calls and audio streams must have retry/graceful-failure paths — a crash during a 60-minute session is unacceptable.
- Keep synchronous code synchronous. Decode on a worker, not in the audio callback; load the model once and bound the backlog. Do not enable GPU acceleration by default without testing target hardware.

## Markdown Output Format

Session files follow this structure:

```markdown
# Session: <title>
**Date:** YYYY-MM-DD HH:MM

---

## [00:00:00]

Raw transcript text as spoken.

## [00:00:00]

### Structured notes

#### Key ideas
- Source-grounded AI bullet, optional and presentation-customizable.

## [00:02:30]

📌 **user typed keyword here**
```

- Micro-notes are prefixed with `📌` and bold text — visually distinct from AI bullets.
- Event headers use `[HH:MM:SS]`; AI uses chunk start time and manual notes use submit time. A same-ID JSONL journal is authoritative; rebuild sorts by `(timestamp, sequence)`. Incomplete sessions show status and duration, and unfinished AI tasks remain retryable.
- No HTML, no proprietary formatting. Must render cleanly in Obsidian, Notion, and any plaintext editor.

## LLM Structuring Rules

When prompting a configured provider to structure transcript chunks:

- **Preserve** technical terms, proper nouns, code identifiers, and library/framework names exactly as spoken.
- **Strip** filler words ("uh", "um", "you know"), false starts, and repetitions.
- **Never hallucinate** — do not add information not present in the source transcript.
- **Output** Markdown note bodies, using the standard section format by default. Users may customize presentation via a UTF-8 file; preserve Latchnote metadata and factual rules. Do not let provider failure erase raw text.
- **Bilingual awareness** — Indonesian/English code-switching is expected. Keep both languages as-is; do not translate.

## Testing

- Core logic (chunking, markdown formatting, timestamp math) should have unit tests in `tests/`.
- Use `pytest`. No fixtures or mocking frameworks unless the test genuinely needs them.
- Hardware and model quality require manual/real-audio tests. Small fake decoders/transports may check lifecycle, timestamp, timeout, and failure handling; do not treat them as hardware or accuracy validation.

## What NOT to Build (MVP)

These are explicitly out of scope per the PRD. Do not implement or scaffold for:

- Screen OCR / on-screen content capture
- macOS or mobile support
- Cloud sync or user accounts
- Flashcards, quizzes, or spaced repetition
- Pricing or subscription logic
- "Invisible" or "undetectable" overlay behavior

## File Naming

- Session output: `YYYY-MM-DD_<session-title>[suffix].md` plus same-ID `.jsonl`; the WAV uses that ID too. Collisions use exclusive creation and a suffix.
- Source code: `snake_case.py`, no abbreviations.
- Test files: `test_<module>.py` mirroring the source module.

## Git

- Commit messages: imperative mood, concise (`Add audio capture module`, `Fix chunk boundary timing`).
- `.env` and API keys: never committed. Use `.env.example` as template.
- Keep `.gitignore` current for Python (`__pycache__/`, `.env`, `*.pyc`, `dist/`, etc.).
