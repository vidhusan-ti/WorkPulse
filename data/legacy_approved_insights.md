# Legacy / Archived Approved Insights

These entries are preserved for history but are not active above-bar examples under the current 7/7 high-bar rubric. Some were approved under the older 5/7 rubric; others describe an older architecture that no longer matches the project.

---

## Legacy Approved Insight

**Score:** 5

**Prompt:**

> “Before connecting Google Docs API, help me define the exact local output format that would make manual review easy and later automation simple.

**Why it was previously above the bar:**

- Gives enough detail to evaluate intent.
- Mentions purpose or reasoning.
- Provides or references context.
- Pushes toward action or a concrete direction.
- Constrains the expected output.

---

## Legacy Approved Insight

**Score:** 5

**Prompt:**

> My goal is to prove the MVP works without building UI. Given we can read Cursor transcripts, what is the simplest pipeline to extract 50 prompt-response pairs, grade them, and show evidence to reviewers?

**Why it was previously above the bar:**

- Gives enough detail to evaluate intent.
- Mentions purpose or reasoning.
- Provides or references context.
- Pushes toward action or a concrete direction.
- Constrains the expected output.

---

## Legacy Approved Insight

**Score:** 5

**Prompt:**

> I'm choosing between LiteLLM and a direct OpenAI client for structured JSON grading. Constraints: single classify call, must fallback to heuristics, minimal dependencies. Recommend one approach and explain the tradeoff in one paragraph.

**Why it was previously above the bar:**

- context: Names hard constraints (single call, heuristic fallback, minimal deps).
- clarity: Specific deliverable - one recommendation plus one-paragraph tradeoff.
- action: Bounded ask that drives a decision, not open-ended exploration.

---

## Archived Approved Insight

**Score:** 7

**Prompt:**

> We need to grade prompts in real time but have no paid API and no local GPU. My proposal: heuristic monitor for instant nudges plus a Cursor skill for authoritative grading. What are the risks of this split, and what would you change?

**Why it was previously above the bar:**

- insight: Proposes a two-tier design with distinct roles (fast nudge vs authoritative grade).
- context: States hard constraints - real-time, no API, no GPU.
- risk: Explicitly asks for failure modes of the split.
- recommendation: Comes with a concrete proposal, not a blank "thoughts?"
- action: Asks what to change, not just whether the idea is good.

