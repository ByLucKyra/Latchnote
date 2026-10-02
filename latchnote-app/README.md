# Latchnote: local Whisper trial

Windows system audio → local Whisper raw transcript → optional AI-formatted Markdown.
Current trial uses **faster-whisper 1.2.1**, multilingual `base`, CPU INT8,
two inference threads, and five-second audio windows. No STT API key or dedicated
GPU is required. This is a prototype, not a validated Windows `.exe` release.

## Setup and first run

Run these commands from `latchnote-app/` with Python 3.12+:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m latchnote --download-model
.\.venv\Scripts\python.exe -m latchnote --title "My course" --raw-only
```

The explicit download step requires internet and caches the model in `data/models/`.
Subsequent transcription uses cached files only, without uploading audio. Keep that
directory when running offline. First model load can take a few seconds; it is
reused across tray sessions. PyAV is constrained below 19 because version 19 removed
an argument still used by faster-whisper 1.2.1. No separate FFmpeg installation is needed.

Choose **Start Session** in the tray, play your course in any application routed
through the default Windows output device, and press `Ctrl+Space` for a personal
note. Choose **Stop Session** to flush the final short audio window. Wait for Stop
to finish before Quit. If Stop reports that Whisper is still draining, wait and
choose Stop again; capture has already stopped and its WAV is retained.

Notes go to `notes/YYYY-MM-DD_<title>.md`; repeated titles receive a suffix rather
than overwriting earlier notes. The same unique session ID names the Markdown,
JSONL recovery journal, and WAV in `data/`. The journal is the source of truth;
Markdown events sort by source timestamp and stable sequence. It records incomplete
AI work and the measured session duration. This captures system output, not your
microphone. Other sounds on that device can also be captured. Files are retained
until you remove them yourself.

## Configuration

Use `.env.example` as a reference; create/edit `.env` locally without replacing an
existing secret file. Run from `latchnote-app/` because config/paths are relative
to the working directory. Restart the process after changing settings.

```dotenv
LATCHNOTE_WHISPER_MODEL=base
LATCHNOTE_WHISPER_LANGUAGE=
LATCHNOTE_WHISPER_THREADS=2
LATCHNOTE_WHISPER_WINDOW_SECONDS=5
```

Blank language enables detection; `id` is an optional Indonesian hint to test.
Use multilingual `tiny`, `base`, or `small`, not `.en` models, for ID/EN.
Changing model requires rerunning `--download-model`. Threads accept 1–16;
windows accept 1–30 seconds. Smaller windows do not guarantee lower latency:
repeated decoding and language detection also cost CPU.

## Optional AI cleanup and custom formatting

Raw transcription always works without a provider. To enable cleanup, configure
an **OpenAI-compatible chat-completions endpoint**, model and, if required, key:

```dotenv
NOTES_AI_BASE_URL=https://console-provider.example/api/v1
NOTES_AI_API_KEY=
NOTES_AI_MODEL=
LATCHNOTE_NOTES_FORMAT=
```

The example URL is a placeholder, not a working provider. For Groq, the API base is
`https://api.groq.com/openai/v1` ([provider documentation](https://console.groq.com/docs/openai)); choose a model available to your account.
Start without `--raw-only` to use configured cleanup. That flag overrides AI config
and guarantees Latchnote does not make notes-provider requests. Empty provider/model
configuration means raw-only. Invalid optional settings fall back to raw-only with
a warning instead of preventing capture. Native vendor APIs with different request
formats, including Anthropic Messages, are **not** handled by this adapter.

The adapter sends **transcript text**, not recordings, about every 120 seconds of
transcribed source audio and for the final remaining chunk. Provider usage may cost
money or consume a free quota. Endpoint must use HTTPS; HTTP is permitted only for
loopback local services. Keys stay in local configuration and are not logged.

Latchnote owns session metadata, `[HH:MM:SS]` timestamps, `### Structured notes`,
and `📌` personal notes. The default AI body uses `#### Key ideas`,
`#### Technical details`, and `#### Examples` when relevant. Its fixed prompt
requires source-grounded facts, preserved identifiers, no invented examples, and
original ID/EN wording. This is a model instruction, not a factual guarantee.

For a custom style, copy/edit `notes-format.example.md` and set:

```dotenv
LATCHNOTE_NOTES_FORMAT=my-notes-format.md
```

The UTF-8 file can change headings, verbosity and bullet/table presentation.
It is added to the standard factual rules, rather than replacing them. It must
contain 1–16000 characters. Customization is file-based for this trial; a settings
editor is not implemented yet. AI never replaces the independently saved raw text.
If the provider times out or rejects a request, raw notes remain available.

## Saved audio and recovery trial

```powershell
.\.venv\Scripts\python.exe -m latchnote --transcribe-file "data/session.wav" --title "Recovered course" --raw-only
```

This creates a **new** Markdown note from the complete saved audio; it does not
merge into or overwrite an existing session. It can also process a user-supplied
audio file supported by PyAV. Remove `--raw-only` to request configured cleanup.
Do not treat repeated AI attempts as free: requests may be billed again.

Rebuild a damaged or missing Markdown export from its journal:

```powershell
.\.venv\Scripts\python.exe -m latchnote --rebuild-notes "notes/2026-10-02_My course.jsonl"
```

Retry durable AI tasks only when you explicitly choose to make provider requests:

```powershell
.\.venv\Scripts\python.exe -m latchnote --retry-pending "notes/2026-10-02_My course.jsonl"
```

These commands do not need network access for rebuild; retry requires valid
`NOTES_AI_*` settings. A crash between a provider response and its journaled
success can cause that chunk to be requested again. The journal flushes each event,
but does not promise survival of sudden power loss or failing storage hardware.

## Checks and limits

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

On 2 October 2026, an offline English sample from
[whisper.cpp](https://github.com/ggml-org/whisper.cpp/blob/master/samples/jfk.wav)
was transcribed with CPU INT8 and two threads on **AMD Ryzen 5 5600H**:

- Whole-file CLI: 11 seconds of audio, 8.33 seconds total including load.
- Windowed worker: 11 seconds of audio, 9.09 seconds processing/drain (RTF 0.83),
  three output segments. The final one-second tail alone took about 2.80 seconds.
- Regression suite: 16 tests passed at this checkpoint. Subsequent changes can add tests.

These are short smoke checks, not benchmarks proving entry-level/8 GB suitability.
Intel/AMD entry-level CPUs, ID/EN code-switching, browser/Zoom contention, RAM usage,
60-minute thermal behavior, hotkey focus, and tray capture still need real validation.
Five-second windows give delayed final segments, **not word-by-word interim captions**.

The worker has a bounded roughly 30-second backlog. If the CPU cannot keep up,
the tray reports gaps and the full WAV is retained for `--transcribe-file` recovery.
Non-overlapping windows may split words at boundaries; overlap/stable partial decoding
is deferred until quality tests justify it. Pending AI tasks remain in the session
journal after the total shutdown deadline and can be retried explicitly. Real-device
Windows open-file behavior and long-session durability still need manual validation.
