Use Cursor local agent transcript JSONL files as the MVP input source to extract real prompt-response conversations for grading.

Canonical high-bar rubric (window-based): `data/high_bar_window_rubric.md`.

Two-axis grading:
- Insight quality: judge whether the user's move is `mindblowing`, `outstanding`, `strong`, or `routine`.
- Portfolio readiness: judge whether the transcript proves enough context, assistant-delta, evidence, stakes, artifact or decision impact, and case-study anatomy to publish the window.

Minimum mindblowing gates:
- Human-original move: the user introduced the key insight, concern, reframing, standard, or decision.
- Non-obvious insight: the move is unlikely to be produced by a generic LLM from the docs alone.

Portfolio-ready labels:
- `mindblowing_portfolio`: rare, first-principles move plus full evidence and case-study anatomy.
- `outstanding_portfolio`: very strong complete portfolio case, even if less surprising than mindblowing.

Highlight labels:
- `mindblowing_highlight`: rare move, but missing portfolio evidence, context, impact, or anatomy.
- `strong_highlight`: genuine user-owned value, but not rare or complete enough for portfolio.
- `below_bar`: routine, generic, assistant-led, or ordinary execution.

Bar: insanely high for approved portfolio entries. Do not let checklist completion create a portfolio label, and do not let missing portfolio evidence erase a genuinely mindblowing human move.

Scoring anchors:
- 0 = missing, generic, copied, implied, or keyword-only.
- 1 = self-directed, specific, user-owned, grounded, and strong enough to change what a skilled collaborator would do.

Mentor calibration:
- Borderline cases must be flagged for mentor review.
- The grader is production-grade only after testing against at least 50 mentor-labeled real prompts.
