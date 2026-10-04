# Latchnote

Windows study-note prototype: system audio is transcribed locally with Whisper,
then saved as Markdown. AI formatting is optional and sends transcript text to a
user-configured OpenAI-compatible endpoint. This is a prototype, not a released
installer; long-session reliability and mixed-language quality remain unverified.

## Projects

- [`latchnote-app/`](latchnote-app/README.md) — setup, configuration, recovery, and desktop limitations.
- [`landing-page/`](landing-page/README.md) — English `/` and Indonesian `/id/` landing page; waitlist is closed until an approved receiver is tested.
- [`plans/`](plans/README.md) — implementation and validation status.
- [`latchnote-app/VALIDATION.md`](latchnote-app/VALIDATION.md) — manual real-device runbook and evidence log.

## Local checks

Desktop, from `latchnote-app/` (Python 3.12+):

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

Landing page, from `landing-page/` (Node 22.12+):

```powershell
npm ci
npm run build
npm run preview
```

Passing local checks do not establish audio capture, recovery, quality, or release readiness. See the validation runbook before making those claims.
