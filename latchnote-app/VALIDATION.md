# MVP Validation Runbook

## Before testing

1. Use Python 3.12+ and install the project dependencies.
2. Copy `.env.example` to `.env` and add valid `DEEPGRAM_API_KEY` and `ANTHROPIC_API_KEY` values.
3. Start a course with mixed Indonesian/English speech.
4. Run `python -m latchnote --title "<course title>"` and choose **Start Session** from the tray.

## Per-session checklist

- [ ] Record the participant, course, and session duration.
- [ ] Confirm the tray reaches **Recording**.
- [ ] Add at least two micro-notes with `Ctrl+Space`.
- [ ] Stop the session and open the generated Markdown file in a text editor.
- [ ] Confirm timestamps, transcript, structured notes, and `📌` micro-notes appear in chronological order.
- [ ] Open the same file in Obsidian and confirm it renders normally.
- [ ] Note the longest visible transcript delay; target is 10 seconds or less.

## Recovery checks

- [ ] Stop normally: the WAV recovery file and Markdown file both remain readable.
- [ ] Disconnect the network during a recording, then stop: recovery WAV remains available and the tray reports an error.
- [ ] Restart the app after a failed transcription: the previous recovery WAV remains in `data/`.

## Feedback record

| Session | Participant | Duration | Notes worth revisiting? | Transcript issues | Hotkey friction | Next change |
|---|---|---:|---|---|---|---|
| 1 |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |

Do not add new features until the three sessions are reviewed and the observed issues are ranked.
