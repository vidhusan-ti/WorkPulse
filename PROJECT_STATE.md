# PROJECT_STATE.md — WorkPulse

**Last Updated:** 2026-06-27
**Status:** Phase 2 Complete — Core pipeline built and tested

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

**Phase 1 (Planning):** ✅ Done
**Phase 2 (Core Pipeline):** ✅ Done — all 6 tests passing
**Phase 3 (Popup UI):** ✅ Done (tkinter-based floating overlay)
**Phase 4 (Monitor Loop):** ✅ Done
**Phase 5 (Polish):** 🔄 In progress

## Components Status

- [x] Transcript watcher (watchdog + polling fallback)
- [x] Window extractor (sliding 3-turn windows)
- [x] Grader (OpenAI / Anthropic, configurable)
- [x] Grade persister (graded_events.jsonl)
- [x] Popup UI (tkinter floating overlay)
- [x] Portfolio writer (portfolio.md)
- [x] 10-min inactivity monitor + nudge
- [x] CLI entry point (main.py with --setup wizard)
- [x] README with platform-specific transcript paths

## Next Steps

1. **Integration test** — test with a real Cursor transcript JSONL file
2. **Rubric review** — verify grader output quality with sample windows
3. **Edge cases** — handle malformed JSONL, empty files, missing API keys gracefully
4. **Package** — pip-installable package for easy distribution
