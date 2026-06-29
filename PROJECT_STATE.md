# PROJECT_STATE.md — WorkPulse

**Last Updated:** 2026-06-29
**Status:** Phase 5 Active — Pipeline v2 complete, 73 tests passing, monitor wired

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
**Phase 4 (Monitor Loop):** ✅ Done (now uses pipeline v2 by default)
**Phase 5 (Pipeline v2):** ✅ Done — 4-stage SND→IOAS→CTA→EJAD, 73 tests
**Phase 6 (Polish):** 🔄 In progress

## Components Status

- [x] Transcript watcher (watchdog + os.walk polling, handles hidden .cursor dirs)
- [x] Window extractor (sliding 3-turn windows)
- [x] Grader v1 (OpenAI / Anthropic, legacy)
- [x] Grader v2 — 4-stage pipeline (SND→IOAS→CTA→EJAD)
- [x] Stage 1 (SND) — Jaccard/embedding novelty detection
- [x] Stage 2 (IOAS) — Intent-outcome alignment scoring
- [x] Stage 3 (CTA) — Conversation trajectory analysis
- [x] Stage 4 (EJAD) — Ensemble + adversarial dissenter
- [x] Grade persister (graded_events.jsonl + focal_prompt_hash + trace summary)
- [x] SWOD deduplication (Proposal 12 — no duplicate above-bar counts)
- [x] Popup UI (tkinter floating overlay)
- [x] Portfolio writer (portfolio.md with pipeline trace summary)
- [x] 10-min inactivity monitor + nudge
- [x] CLI entry point (main.py with --setup wizard)
- [x] README with platform-specific transcript paths
- [x] 73 tests (pipeline stages, extractor, persister)

## QA History

- **2026-06-29** — QA Agent Cycle 1 ran. 89/89 tests pass. 3 bugs fixed (persist_grade makedirs crash, grader_v2 format-spec crash, SentenceTransformer model caching). 1 bug deferred (has_follow_up_turns positional match). 10 gaps documented. Full report: proposals/agent-qa-cycle-1.md
- **2026-06-29** — QA Agent Cycle 2 ran. End-to-end T -> PR -> R loop validated. Rubric v2 internally consistent; all 3 false positives (Bharath W9, Vidhusan W3, Vidhusan W9) correctly filtered to near_bar. GAP-1 CLOSED: rubric now wired into Stage 2/3/4 via rubric_context injection. 89/89 tests still pass. Full report: proposals/agent-qa-cycle-2.md

## Next Steps

1. **Integration test** — test with a real Cursor transcript JSONL file
2. **Rubric review** — verify grader output quality with sample windows
3. **Edge cases** — handle malformed JSONL, empty files, missing API keys gracefully
4. **Package** — pip-installable package for easy distribution

## Agent T History
- **Cycle 1** (2026-06-27) — Evaluated 5 grading approaches against 6 real transcript windows; identified best combination pipeline (SND→IOAS→CTA→EJAD). See proposals/agent-t-cycle-1-comparison.md.
- **Cycle 2** (2026-06-29) — Calibration review of v1 grading results for all 4 candidates (Abdul 7, Arleif 13, Bharath 9, Vidhusan 9 windows). Flagged Bharath W9 as false positive candidate, Vidhusan W3/W6/W9 as near-bar, Arleif W6/W12 as borderline. Identified 4 rubric gaps and 4 process clarifications. See proposals/agent-t-cycle-2.md.

## Agent PR History
- **Cycle 1** (2026-06-29) — Rubric failure analysis: identified 5 concrete failure modes with test cases from actual grading results. Top 3 priority fixes: (1) define "insight" with counterfactual test, (2) decision-query gate, (3) domain-independent "correct direction" proxy signals. Primary false positives analysed: Bharath W9, Vidhusan W3, Vidhusan W9. See proposals/agent-pr-cycle-1.md.

## Agent R History

- **Cycle 1** — Initial rubric design proposals (solutions 1–11), multi-dimensional scoring, CTA concept, contrastive baseline
- **Cycle 2** — Edge cases, SWOD deduplication (Proposal 12), Stage 1 calibration (Proposal 13), context-aware window sizing (Proposal 14)
- **Cycle 3** (2026-06-29) — Rubric alignment analysis: 7 gaps identified in new manual rubric, 7 concrete improvement proposals covering window definition, tier vocabulary unification, insight operationalisation, per-stage failure modes, two-axis insight exception, "correct direction" definition, and near-bar coaching template. Proposals cross-referenced with all 4 candidate result sets.
- **Cycle 4** (2026-06-29) — Rewrote `data/manual_rubric.md` to v2 applying all 5 failure mode fixes from Agent PR Cycle 1. Key changes: window definition added, tier vocabulary unified (`above_bar`/`near_bar`/`below_bar`), "insight" defined with counterfactual test, decision-query gate added, 4-part ownership test, domain-independent proxy signals for "correct direction", near-bar coaching template, quick reference checklist. Changelog: `data/rubric-changelog.md`.
