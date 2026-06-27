# LLM Agent Workflow

This file captures the agreed prompt-coach workflow for future analysis.

## Purpose

The system monitors local Cursor transcript files, grades user windows against the high-bar rubric, gives coaching for weak or incomplete windows, and asks the user before adding portfolio-ready windows to the approved portfolio.

## Flow

1. Read Cursor transcript JSONL files.
2. Extract prompt-response pairs or short windows with surrounding context.
3. Skip prompts that were already graded.
4. Send each new pair to the LLM grader.
5. Validate the grader output against the expected grade structure.
6. Persist the grade to `data/graded_events.jsonl`.
7. If the window is `below_bar`, show a coaching popup with the missing moves and a better next prompt.
8. If the window is `strong_highlight` or `mindblowing_highlight`, show coaching that preserves the insight but names the missing evidence, impact, or case-study anatomy.
9. If the window is `mindblowing_portfolio` or `outstanding_portfolio`, show an approval popup asking whether it can be added to the portfolio.
10. If the user approves, append it to `data/approved_insights.md`.
11. If the user rejects, do not add it to the approved portfolio.

## Human Review Decision

There is no separate review queue. The popup approval is the human review step for portfolio inclusion.

The automated grader decides the window's `insight_quality` and `portfolio_ready` status. The user decides whether a portfolio-ready window should be saved into the approved insights portfolio.

## Current MVP Shape

```text
transcript -> prompt-response extraction -> grader -> grade persistence
  -> below_bar -> coaching popup
  -> strong_highlight / mindblowing_highlight -> evidence or next-move coaching popup
  -> mindblowing_portfolio / outstanding_portfolio -> approval popup -> approved_insights.md if approved
```

## Notes For Future Analysis

- The approved portfolio should only contain windows that are portfolio-ready under `data/high_bar_window_rubric.md`.
- Borderline or uncertain portfolio cases should default to a highlight label, not an approved portfolio label.
- A genuinely rare move can be `mindblowing_highlight` even when it fails portfolio-readiness gates.
- The popup approval is enough for the current single-user workflow.
- A separate review queue may only be useful later if batch calibration, rejection analytics, or multi-user review becomes necessary.
