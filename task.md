# Latchnote — Execution Plan

Scope: Windows MVP in `latchnote-app/`. The first usable slice is system audio → transcript → local Markdown. UI and AI structuring come after that path works.

## Milestone 0 — Decisions and Setup

- [ ] Confirm Deepgram and Anthropic API keys are available locally.
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

- [x] Send captured audio to Deepgram streaming.
- [x] Handle interim and final transcript events.
- [ ] Write final transcript segments to Markdown as they arrive.
- [x] Support automatic language detection for Indonesian/English mixed speech.
- [x] On connection failure, retain local audio and expose a retryable error state.
- [ ] Test with a 30-minute mixed-language course recording.

**Done when:** browser audio becomes timestamped Markdown transcript with a maximum practical delay of 10 seconds.

## Milestone 4 — Structured Notes

- [ ] Accumulate only new final transcript text in 2–3 minute chunks.
- [ ] Send each chunk to Claude with a prompt that preserves facts, terms, and identifiers.
- [ ] Append structured bullets at the chunk start timestamp.
- [ ] Preserve raw transcript if structuring fails and retry later.
- [ ] Add a small check proving chunks are not sent twice.

**Done when:** one completed session produces chronological, structured Markdown notes without invented content.

## Milestone 5 — Manual Micro-Notes

- [ ] Register `Ctrl+Space` as the default global hotkey.
- [ ] Show a small PySide6 text input near the cursor.
- [ ] Submit the note with its current relative timestamp.
- [ ] Render manual notes distinctly in Markdown using `📌`.
- [ ] Close the popup on submit or `Esc`.

**Done when:** a note can be captured while a browser video retains focus and it appears in the same session file.

## Milestone 6 — Minimal Tray App

- [ ] Add a tray menu with Start Session, Stop Session, and Quit.
- [ ] Show clear state: idle, recording, retrying, or error.
- [ ] Prevent a second session from starting while one is active.
- [ ] Stop safely on exit and retain recoverable data.

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
