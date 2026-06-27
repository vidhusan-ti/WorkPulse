# PROJECT_STATE.md — WorkPulse

**Last Updated:** 2026-06-27
**Status:** Planning → Architecture Phase

## What Is WorkPulse

A cross-platform Cursor conversation monitor that:
1. Watches Cursor JSONL transcript files in real-time
2. Grades user prompt windows against the manual rubric
3. Shows floating overlay popups:
   - **Above bar** → ask user to approve saving to `portfolio.md`
   - **Near bar** → coaching popup with improvement suggestion
   - **Average** → silently ignored
4. Nudges user with a floating alert if no above/near-bar prompts in 10 minutes

## Current State

- Repo has rubric files, graded data (68 events), config template — NO source code
- Existing grader was Windows-only (hardcoded paths in config/settings.json)
- Rubric to use: `data/manual_rubric.md` (Vidhu's decision)
- Grading engine: TBD (LLM-backed, model configurable)

## Components To Build

- [ ] Transcript watcher (cross-platform file monitor)
- [ ] Window extractor (sliding 3-turn windows from JSONL)
- [ ] Grader (LLM call with manual_rubric as system prompt)
- [ ] Grade persister (append to graded_events.jsonl)
- [ ] Popup UI (floating overlay, cross-platform)
- [ ] Portfolio writer (approved_insights.md / portfolio.md)
- [ ] 10-min inactivity monitor + nudge

## Tech Stack (Proposed)

- Python 3.10+
- `watchdog` — cross-platform file watching
- `tkinter` or `PyQt6` — floating overlay UI
- LLM: configurable (OpenAI / Anthropic / Cursor API)
- `pytest` — testing

## Architecture Decision Pending

- LLM provider choice
- Popup framework choice (tkinter vs PyQt6)
