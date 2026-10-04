# MVP Validation Runbook

## Execution record — 4 October 2026

Baseline commit: `badf1f5`. Python 3.12.10, Node 24.11.0.

| Check | Result | Scope |
|---|---|---|
| `python -m pytest -q` | PASS — 28 passed | Automated regression only; no hardware/audio quality claim |
| `python -m pip check` | PASS — no broken requirements | Installed environment only; not a fresh-machine install |
| `npm run build` | PASS — `/` and `/id/` generated | Static build only; no visual/browser interaction check |
| 5–10 minute real-audio smoke / same-title collision | NOT RUN | Needs Windows playback session and manual artifact inspection |
| Failure/recovery matrix | NOT RUN | No deliberate fault injection performed |
| Three participants, 30/60-minute sessions, terms/latency/cost | NOT RUN | Needs participant consent, target hardware, and optional provider budget |
| Second machine, Obsidian, fresh setup | NOT RUN | No second-device or editor verification performed |

Release verdict: **NO-GO for early access**. Only automated local checks passed.
Next owner/action: product owner schedules consenting participants and target
Windows devices, sets a spend cap before any paid-provider test, then fills the
tables below with anonymized evidence. Do not enter emails, API keys, or raw
private lecture transcripts here.

## Before testing

1. Use Python 3.12+ and install the project dependencies.
2. Use `.env.example` as a reference without overwriting local keys. Run `python -m latchnote --download-model` once; local raw transcription needs no API key.
3. Start a course with mixed Indonesian/English speech.
4. Run `python -m latchnote --title "<course title>" --raw-only` and choose **Start Session** from the tray. Test optional `NOTES_AI_*` cleanup separately without `--raw-only`.

## Per-session checklist

- [ ] Record the participant, course, and session duration.
- [ ] Confirm the tray reaches **Recording**.
- [ ] Add at least two micro-notes with `Ctrl+Space`.
- [ ] Stop the session and open the generated Markdown file in a text editor.
- [ ] Confirm timestamps, transcript, structured notes, and `📌` micro-notes appear in chronological order.
- [ ] Open the same file in Obsidian and confirm it renders normally.
- [ ] Note the longest visible transcript delay; target is 10 seconds or less.
- [ ] Measure CPU, peak RAM, backlog, and video smoothness on an actual 8 GB entry-level Intel/AMD machine; cached-model offline mode must work.
- [ ] Test standard and custom AI formatting independently; verify every generated fact against raw transcript.

## Recovery checks

- [ ] Stop normally: the WAV recovery file and Markdown file both remain readable.
- [ ] Disconnect the network during raw-only recording: local STT must continue. Test optional provider failure separately: raw notes and recovery WAV remain available.
- [ ] Restart the app after a failed transcription: the previous recovery WAV remains in `data/`.
- [ ] Run `python -m latchnote --transcribe-file "data/<saved-session>.wav" --raw-only`; a new note is created without overwriting old output.

## Feedback record

| Session | Participant | Duration | Notes worth revisiting? | Transcript issues | Hotkey friction | Next change |
|---|---|---:|---|---|---|---|
| 1 |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |

Do not add new features until the three sessions are reviewed and the observed issues are ranked.
