# DECISIONS.md — WorkPulse

## D-001 — Rubric to Use
**Decision:** Use `data/manual_rubric.md` as the grading rubric (not the high_bar_window_rubric.md)
**Reason:** Vidhu's explicit decision. Simpler, more actionable, better suited for MVP.
**Date:** 2026-06-27

---

## D-002 — Three-Tier Grading System
**Decision:** Simplify to 3 tiers only
| Tier | Action |
|------|--------|
| Above bar (`mindblowing_portfolio` / `outstanding_portfolio`) | Popup → user approves → saved to portfolio.md |
| Near bar (`mindblowing_highlight` / `strong_highlight`) | Coaching popup with improvement suggestion |
| Average (`below_bar`) | Silently ignored |
**Reason:** Vidhu's explicit decision. Cleaner UX, less noise.
**Date:** 2026-06-27

---

## D-003 — Notification Method
**Decision:** Floating overlay (always-on-top window popup)
**Reason:** Non-blocking, cross-platform, visible while Cursor is open.
**Date:** 2026-06-27

---

## D-004 — Platform
**Decision:** Cross-platform (Windows, Mac, Linux)
**Reason:** Vidhu's explicit decision.
**Date:** 2026-06-27

---

## D-005 — Portfolio Approval
**Decision:** User must approve before anything is saved to portfolio.md
**Reason:** Quality control — only conscious saves, no auto-adds.
**Date:** 2026-06-27

---

## D-006 — 10-Minute Inactivity Nudge
**Decision:** If no above-bar or near-bar prompt in 10 minutes → floating overlay nudge
**Reset trigger:** Any above-bar or near-bar prompt resets the timer.
**Date:** 2026-06-27

---

## D-007 — Grading Unit
**Decision:** Windows of ~3 turns (not single prompts, not full conversations)
**Reason:** Single prompts lack context; full conversations are too large to grade cheaply.
**Date:** 2026-06-27

---

## D-008 — LLM Provider
**Decision:** PENDING — need Vidhu's input
**Options:** OpenAI GPT-4o / Anthropic Claude / Cursor API
**Date:** 2026-06-27

---

## D-009 — Popup UI Framework
**Decision:** PENDING — evaluating tkinter vs PyQt6
**Criteria:** Cross-platform support, minimal dependencies, good overlay support
**Date:** 2026-06-27

---

## D-008 UPDATE — LLM Provider (Finalised)
**Decision:** Anthropic Claude (claude-sonnet-4-5 as default)
**Reason:** Better nuanced judgment, longer context, more reliable JSON, superior attribution reasoning — all critical for the rubric's core question.
**Date:** 2026-06-27
