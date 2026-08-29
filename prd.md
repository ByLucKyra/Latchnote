# Product Requirements Document (PRD)

## Latchnote

**Real-time note companion for solo online learners**

| | |
|---|---|
| **Status** | Draft — MVP |
| **Owner** | Lucky Ramadhan |
| **Last updated** | July 24, 2026 |
| **Version** | 0.1 |

---

## 1. Summary

Latchnote is a Windows desktop companion app that listens to system audio while the user watches an online course, transcribes it in real time, and organizes it into structured Markdown notes — without requiring the user to pause or manually type through the whole session. A global hotkey lets the user drop short, personal keyword notes at any moment, preserving the small amount of manual/motor engagement known to aid retention, without demanding full note-taking.

## 2. Problem

The founder (and many fellow students) learn primarily through listening, not writing. Watching an online course while trying to take notes forces a trade-off: either pause constantly to write and lose flow, or stay focused and lose the material because nothing was written down to review later. Existing tools don't fit this specific gap:

- **Post-hoc tools** (NoteGPT, VidNotes, Heuristica) require uploading or linking a video *after* watching — they don't help *during* the session, and don't work for live or already-consumed content without a re-upload step.
- **Real-time overlay tools** (Cluely and similar) are architecturally close, but were built for interview/meeting assistance, carry "invisible/undetectable" framing that has no relevance to solo learning, and are priced/positioned for that market.
- **Fully automated notetakers** remove the user from the process entirely. But some manual, physical engagement — even just typing a keyword — reinforces memory (the generation effect). None of the existing tools preserve room for that.

## 3. Research Findings (Market & Cognitive Basis)

### 3.1 The problem is measurable, not just anecdotal

- Students report spending significant weekly time (industry estimates cite 5-8 hours/week) organizing notes on top of 15-20 hours of lecture/course content.
- Divided attention between note-taking and fast-paced video content is a documented cause of missed information — the mismatch between speaking pace and writing/typing pace is a recurring finding across studies on video-based learning.

### 3.2 Manual writing has stronger retention evidence than expected — this reframes the hotkey feature

Cognitive science findings that directly affect Latchnote's design:

- Multiple studies (Peper & Mayer; a 2021 replication) found handwritten note-takers outperformed both photo-takers and non-note-takers on memory tests — even when their notes contained *less* information.
- The "generation effect": actively producing information yields better retention and comprehension than passively receiving it.
- Karpicke & Roediger (2008): active recall produced 80% retention after one week vs. 36% for passive re-reading.

**Implication:** the assumption that "a small manual touch is enough" is directionally supported, but the evidence suggests the *amount* and *nature* of active engagement matters more than previously assumed. A 1-3 word micro-note may be a weaker retention aid than a design that occasionally prompts the user to actively recall or write a short summary before the AI fills in the rest. This is a design question to revisit post-Week 4 dogfooding — see Open Questions.

### 3.3 Market size and demand signals

- Global AI note-taking market: ~$740M in 2026, projected to reach ~$3.48B by 2035 (CAGR ~18.75%).
- Education is the largest application segment (30%+ share); students are the largest end-user segment (40%+ share).
- Demand signal: a comparable AI note-taking competitor grew from 1M to 5.7M users in six months (~20,000 new users/day), reaching eight-figure ARR — evidence this category can scale quickly once product-market fit is found.

### 3.4 Competitive landscape update: LectureScribe

A close competitor identified during market research, not previously scoped:

- Full AI study platform: real-time transcription plus auto-generated flashcards, quizzes, study guides, video summaries, and visual infographics from lecture content.
- Already at 25,000+ users, with active campus-by-campus marketing (UCSD, Purdue, UPenn, WUSTL, etc.) and claimed 97%+ transcription accuracy, including technical/medical terminology.
- Exports to Notion, Obsidian, PDF, and Anki.

**How Latchnote differs:**
- LectureScribe's value proposition centers on the *output* (rich study materials generated after the fact); it shows no evidence of a live micro-interaction mechanism during viewing.
- No evidence of optimization for Indonesian/English code-switched speech — a real gap for the target user base.
- LectureScribe competes on breadth of AI-generated study materials (flashcards, quizzes, video); Latchnote's differentiation must stay anchored to the *in-the-moment* experience — staying present while watching — rather than trying to match LectureScribe's feature breadth.

## 4. Goals

- Let the user watch a course start to finish with full attention, and end the session with usable, structured notes.
- Preserve a small, deliberate space for manual engagement (not full automation) to support retention.
- Support mixed Indonesian/English speech, since local technical courses commonly code-switch.
- Validate the concept cheaply: author + a handful of classmates, Windows-only, no monetization yet.

## 5. Non-Goals (MVP)

- No screen OCR or on-screen content capture.
- No "invisible" or screen-share-undetectable overlay behavior.
- No macOS or mobile support.
- No cloud sync or multi-device accounts.
- No flashcards, quizzes, or spaced repetition.
- No pricing or subscription logic.

## 6. Target User

- Diploma/degree student taking technical online courses (YouTube, Udemy, Dicoding, recorded lectures) alongside formal study.
- Self-identifies as an auditory learner; retains material better by listening than reading.
- Finds continuous note-taking disruptive to focus, but values the retention boost from some manual writing.
- Comfortable with mixed Indonesian/English technical vocabulary.
- Uses Windows as primary device.

## 7. Positioning

> For a solo, auditory-learning online course watcher who cannot keep up with manual note-taking while focusing on the material, **Latchnote** is a desktop companion app that quietly captures course audio in real time and organizes it into structured notes — while preserving a small, deliberate space for the user to "touch" the notes themselves, supporting retention through light active engagement rather than full passive automation.

**Differentiation:**

| | Latchnote | Cluely-style overlays | Post-hoc tools (NoteGPT, etc.) |
|---|---|---|---|
| When it works | Live, while watching | Live, but built for interviews/meetings | After the video, via upload/link |
| User involvement | Light — hotkey micro-notes | None (fully passive) or focused on hiding usage | None (fully passive) |
| Output | Local Markdown | Varies, often cloud-based | Varies, often cloud-based |
| Framing | Learning companion | "Cheat on everything" — meeting/interview aid | Study summarizer |

## 8. User Stories

- As a learner, I want the app to quietly transcribe and organize what I'm hearing, so that I don't have to choose between focusing and note-taking.
- As a learner, I want to press one hotkey and jot a 2-3 word note when something feels important, without switching windows or losing my place in the video.
- As a learner, I want my notes saved as a plain Markdown file, so I can open them in any editor or note app I already use.
- As a learner, I want to tell my own manual notes apart from the AI-generated ones, so I know what I personally flagged as important.
- As a learner, I want a session to survive a full 60-minute course without crashing or losing what was already captured.

## 9. Functional Requirements

### 9.1 Audio Capture
- Capture system audio output (WASAPI loopback) on Windows — no mic, no virtual cable required.
- Support continuous capture for at least 60 minutes without failure.
- Simple start/stop control (tray icon).

### 9.2 Speech-to-Text
- Stream captured audio to a speech-to-text service in real time or near-real-time.
- Handle mixed Indonesian/English speech without requiring the user to pre-select a language.
- Attach a timestamp (relative to session start) to each transcript segment.

### 9.3 Note Structuring
- Every ~2-3 minutes of speech, send the accumulated raw transcript to an LLM for restructuring into bullet-point notes.
- Preserve technical terms, proper nouns, and code identifiers exactly.
- Strip filler words and false starts.
- Never introduce information not present in the source transcript.

### 9.4 Manual Micro-Notes
- Global hotkey (default `Ctrl+Space`) works regardless of which window has focus.
- On press, show a small floating input box near the cursor.
- On submit, save the note text with the current session timestamp.
- Mark manual notes visually distinct from AI-generated notes in the output (e.g. 📌 prefix).
- Popup auto-dismisses on submit or `Esc`, with minimal disruption to the video.

### 9.5 Output & Storage
- Write notes to a local `.md` file per session.
- File name includes date + session title.
- AI-structured notes and manual micro-notes appear interleaved in chronological order.
- Output is plain Markdown, readable in Obsidian, Notion, or any text editor without conversion.

## 10. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Performance | Structuring for a chunk completes within ~5-10 seconds of the chunk boundary |
| Usability | Micro-note interaction takes a few seconds at most |
| Reliability | No crash or data loss during a continuous 60-minute session |
| Portability | Output is plain Markdown, no proprietary formatting |
| Privacy | Notes stored locally, not in third-party cloud, for MVP |
| Cost control | Chunking avoids redundant API calls to STT/LLM providers |

## 11. Architecture Overview

```
Audio Capture (WASAPI loopback)
        ↓
STT Client (Deepgram streaming)
        ↓
Session Orchestrator ──→ Note Structurer (Claude API) ──→ Markdown Writer
        ↑
Hotkey Listener (global hotkey + popup) ──────────────────↗
```

**Stack:** Python, PyAudioWPatch, Deepgram streaming API, Anthropic Claude API, `keyboard` + PySide6, `pystray`, local Markdown storage.

## 12. Success Metrics (MVP validation)

Since this is a pre-revenue, dogfooding-stage MVP, success is qualitative first:

- At least 3 people (including the founder) complete a full real study session using Latchnote.
- Each of those sessions produces a notes file the user says they would actually revisit.
- No session-ending crash across those test sessions.
- At least one specific piece of feedback per tester on what to change before the next iteration.

## 13. Risks

| Risk | Mitigation |
|---|---|
| STT accuracy on mixed Indonesian/English is poor | Test early (Week 1) with real course audio before building downstream features on top |
| API cost scales unpredictably with session length | Chunk-based calls only; monitor usage during dogfooding |
| Hotkey/popup feels disruptive rather than helpful | Keep popup minimal; get direct feedback in Week 4 dogfooding |
| WASAPI loopback setup differs across Windows versions/audio drivers | Test on multiple machines during Week 4, not just the founder's own laptop |

## 14. Timeline

| Week | Focus | Exit Criteria |
|---|---|---|
| 1 | Audio capture + STT pipeline | 30-minute session produces accurate raw transcript, no crashes |
| 2 | Chunking + LLM structuring + Markdown output | A completed session produces a readable, reusable `.md` file |
| 3 | Hotkey micro-notes + minimal tray UI | Full session runs start-to-finish without touching code |
| 4 | Dogfooding with real courses + peers | 3+ users complete a real session, feedback collected |

## 15. Open Questions

- Should micro-notes support any formatting beyond plain text (e.g. tags)?
- Should the app auto-detect course/video title (e.g. from browser tab) to pre-fill the session name, or stay manual for MVP?
- Post-MVP: is the next priority cloud sync, flashcard generation, or multi-language UI — pending dogfooding feedback?
- Given the retention research in Section 3.2, should the micro-note interaction evolve beyond 1-3 keywords — e.g. occasionally prompting a short recall summary — to better match evidence on active engagement and retention? To be evaluated after Week 4 dogfooding.
