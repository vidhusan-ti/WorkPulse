# TODO.md — WorkPulse

## Current Priority

### Phase 1 — Architecture & Rubric Finalisation (NOW)
- [x] Analyse repo
- [x] Write PROJECT_STATE.md, TODO.md, DECISIONS.md
- [ ] Finalise rubric wording (manual_rubric.md → clean version)
- [ ] Decide LLM provider
- [ ] Design system architecture diagram (in DECISIONS.md)

### Phase 2 — Core Pipeline
- [ ] Implement transcript JSONL reader/parser
- [ ] Implement sliding window extractor (3-turn windows)
- [ ] Implement LLM grader with rubric as system prompt
- [ ] Implement grade persistence (graded_events.jsonl)
- [ ] Write unit tests for all above

### Phase 3 — Popup UI
- [ ] Implement floating overlay (cross-platform)
- [ ] Above-bar popup: show window summary + approve/reject
- [ ] Near-bar popup: show coaching note + improvement suggestion
- [ ] 10-minute inactivity nudge popup

### Phase 4 — Monitor Loop
- [ ] Implement file watcher (cross-platform with watchdog)
- [ ] Implement monitor loop (watch → extract → grade → notify)
- [ ] Implement portfolio.md writer on approval

### Phase 5 — Polish
- [ ] Config file (cross-platform paths)
- [ ] CLI entry point
- [ ] README
- [ ] End-to-end testing with real transcripts

## Blocked

Nothing blocked yet.
