# Latchnote — Execution Plan

Scope: Windows MVP in `latchnote-app/`. The first usable slice is system audio → transcript → local Markdown. UI and AI structuring come after that path works.

Updated 4 October 2026: local Whisper raw notes first (8 GB entry-level CPU target), optional provider-independent AI cleanup and user-customizable format. Automated regression passes (28 tests); checkboxes for real-session acceptance remain open. See `latchnote-app/README.md` and `latchnote-app/VALIDATION.md` for trial limits and recorded evidence.

## Milestone 0 — Decisions and Setup

- [x] Cache multilingual Whisper `base` locally; raw-only transcription requires no API keys.
- [x] Create Python project metadata and a `.gitignore` that excludes local secrets, recordings, and generated notes.
- [x] Define the local directories for temporary audio, recovery data, and final Markdown notes.
- [x] Add an `.env.example` with variable names only; never commit real keys.

**Done when:** the app starts from a clean environment and can read configuration without exposing secrets.

## Milestone 1 — Session and Local Output

- [x] Create a session model with title, start time, status, and relative timestamp helper.
- [x] Create the Markdown writer.
- [x] Generate one Markdown file per session using date and title in its filename.
- [x] Write raw transcript segments using `[HH:MM:SS]` timestamps.
- [x] Add a small automated check that validates filename and timestamp output.

**Done when:** a simulated transcript produces a correctly formatted local Markdown note without any API or UI dependency.

## Milestone 2 — WASAPI Audio Capture

- [x] Enumerate and select the default Windows output device.
- [x] Capture system audio through WASAPI loopback.
- [x] Persist audio incrementally to temporary local storage for recovery.
- [x] Implement start, stop, and safe cleanup for one session.
- [ ] Test a 30-minute capture with no crash and a playable recovery recording.

**Done when:** a user can start and stop a session and obtain a local recording of browser/course audio.

## Milestone 3 — Live Speech-to-Text

- [x] Transcribe buffered PCM locally with faster-whisper CPU INT8.
- [x] Drain complete windows and the final short window with source timestamps.
- [ ] Implement stable interim display; current trial emits delayed final segments only.
- [x] Write final transcript segments to Markdown as they arrive.
- [x] Enable multilingual language detection; actual ID/EN accuracy still requires validation.
- [x] Bound live backlog, report transcription errors/gaps, and retain recovery audio.
- [x] Show known dropped audio ranges in the journal and provide separate WAV reprocessing.
- [ ] Test with a 30-minute mixed-language course recording.

**Done when:** browser audio becomes timestamped Markdown transcript with a maximum practical delay of 10 seconds.

## Milestone 4 — Structured Notes

- [x] Accumulate only new final transcript text in 2–3 minute chunks.
- [x] Send each chunk to an optional OpenAI-compatible AI endpoint with standard factual rules.
- [x] Support a UTF-8 custom formatting file without replacing the raw transcript or standard rules.
- [x] Append structured bullets at the chunk start timestamp.
- [x] Preserve raw transcript if structuring fails; disabled AI schedules no requests.
- [x] Persist pending AI tasks in the session journal and expose explicit `--retry-pending` recovery.
- [x] Keep a stable chronological export and rebuild it from the versioned journal; show incomplete status and duration.
- [ ] Verify custom/default formats with a real provider.
- [x] Add a small check proving chunks are not sent twice.

**Done when:** one completed session produces chronological, structured Markdown notes without invented content.

## Milestone 5 — Manual Micro-Notes

- [x] Register `Ctrl+Space` as the default global hotkey.
- [x] Show a small PySide6 text input near the cursor.
- [x] Submit the note with its current relative timestamp.
- [x] Render manual notes distinctly in Markdown using `📌`.
- [x] Close the popup on submit or `Esc`.

**Done when:** a note can be captured while a browser video retains focus and it appears in the same session file.

## Milestone 6 — Minimal Tray App

- [x] Add a tray menu with Start Session, Stop Session, and Quit.
- [x] Show clear state: idle, recording, retrying, or error.
- [x] Prevent a second session from starting while one is active.
- [x] Stop safely on exit and retain recoverable data.
- [x] Add a latest-final preview, notes/recovery folder actions, and explicit pending-AI retry.

**Done when:** a non-technical user can run a full session without using the terminal.

## Milestone 7 — MVP Validation

- [ ] Run three real course sessions, including at least one 60-minute session.
- [ ] Verify no data loss during normal stop, API failure, and app restart.
- [ ] Check output in a plain text editor and Obsidian.
- [ ] Record feedback on transcript quality, note usefulness, and hotkey friction.
- [ ] Prioritize only issues observed in testing before adding new features.

**Done when:** three users complete real study sessions and say they would revisit the exported notes.

## Build Order

1. Milestone 0–1: create a testable local session and Markdown foundation.
2. Milestone 2–3: prove the core audio-to-transcript loop.
3. Milestone 4: add AI only after raw transcript is reliable.
4. Milestone 5–6: add interaction and tray controls.
5. Milestone 7: dogfood and fix observed failures.

## Explicitly Deferred

- Browser title detection
- Cloud sync and accounts
- Flashcards, quizzes, and spaced repetition
- macOS/mobile support
- Screen OCR and screen capture
