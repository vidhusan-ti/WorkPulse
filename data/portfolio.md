# Approved Insights

Only windows that are portfolio-ready under the current high-bar rubric belong here:

- label is `mindblowing_portfolio` or `outstanding_portfolio`
- portfolio-readiness gates pass
- case-study anatomy is complete
- the user shows moment-specific product, engineering, or decision judgment

Rare but under-evidenced moves belong in coaching or raw review as `mindblowing_highlight`, not in approved insights.

Legacy entries were moved to `data/legacy_approved_insights.md`.

## Calibration Examples

These are synthetic examples of windows that should pass the current high-bar rubric as portfolio-ready. They are not transcript-derived approved insights.

---

## Example Portfolio-Ready Window: PR Review Blocker

**Label:** `outstanding_portfolio`

**Score:** 8/10

**Prompt:**

> I am reviewing a course-content PR and I do not think we should flat accept it yet. Two issues look like merge blockers, not style comments:
>
> 1. The new MCQ reflection prompts say "the option directly above/below yours," but our course rule requires option shuffling. My recommendation is to keep shuffling and rewrite those prompts to reference answer content instead of position.
> 2. Module 3 and Module 4 refer back to earlier module answers, but this course can run modules as separate sessions. My recommendation is to remove hidden cross-session memory assumptions unless the module explicitly carries forward a recap artifact.
>
> Please challenge this review stance. Map each blocker to the problem/fix that introduced it, compare the cost of my preferred fix against the alternative, and produce a reviewer comment that is firm enough to block merge but specific enough for the author to act on.

**Why it passes:**

- `drive`: The user initiates a review decision instead of asking whether the PR is good.
- `frame`: The problem is framed as merge-blocking conflicts, not generic feedback.
- `evidence`: The prompt cites concrete conflicting behaviors.
- `alternatives`: It compares keeping shuffle vs rewriting prompts, and removing hidden memory vs carrying recap state.
- `tradeoffs`: It asks for cost comparison and merge impact.
- `model_use`: It uses the model to challenge, map, compare, and draft.
- `leverage`: The answer directly improves review quality and prevents regressions before merge.

---

## Example Portfolio-Ready Window: MVP Scope Decision

**Label:** `outstanding_portfolio`

**Score:** 8/10

**Prompt:**

> I am deciding the MVP scope for a Contract Intelligence Platform. Current evidence from legal tickets shows repeated duplicate submissions, missing parent agreements for amendments, and lost negotiation context across Zammad, Jira, and email. My recommendation is to launch v1 with structured contract storage, full-text search, counterparty history, ticket-of-origin linkage, and two-tier RBAC. I would defer clause-level diffing and renewal alerts.
>
> The risk is that a partial ingestion path may make the index untrusted, but waiting for complete ETL from every source may delay the pilot too much. Please stress-test my MVP cut. Compare "partial ETL plus manual upload for pilot" against "full ETL before launch" using legal-team trust, implementation time, duplicate-request reduction, and rollback risk. End with the questions I must answer before asking leadership for approval.

**Why it passes:**

- `drive`: The user owns a concrete MVP recommendation.
- `frame`: The decision is scoped to launch readiness and pilot trust.
- `evidence`: It cites ticket-derived pain and source systems.
- `alternatives`: It compares partial ETL vs full ETL.
- `tradeoffs`: It names trust, time, duplicate reduction, and rollback risk.
- `model_use`: It asks the model to stress-test and refine the decision.
- `leverage`: The result changes what gets built and what leadership must approve.

---

## Example Portfolio-Ready Window: Monitoring Design

**Label:** `outstanding_portfolio`

**Score:** 8/10

**Prompt:**

> I want to run our prompt-monitoring project on existing Cursor transcripts before investing in live monitoring changes. My hypothesis is that transcript-first validation is safer because it lets us calibrate false positives against real prompts without interrupting active work. The tradeoff is that old transcripts may lack workspace context, so the grader might over-penalize prompts that were actually clear in-session.
>
> Please compare two paths: (A) build a transcript replay pipeline first, with prompt-response pairs plus nearby context, or (B) improve the live monitor first and collect new events going forward. Use these constraints: no saving weak prompts to approved insights, approved portfolio entries must be `mindblowing_portfolio` or `outstanding_portfolio`, and the first useful output should be a small file of only clearly portfolio-ready examples. Recommend one path, list the failure modes, and define a validation checklist for the first 20 graded prompts.

**Why it passes:**

- `drive`: The user proposes transcript-first validation as a hypothesis.
- `frame`: The decision is about validation order, not just running a script.
- `evidence`: It names the available data source and missing context risk.
- `alternatives`: It compares replay-first vs live-monitor-first.
- `tradeoffs`: It weighs calibration safety against context loss.
- `model_use`: It asks for comparison, recommendation, failure modes, and checklist.
- `leverage`: The answer creates a safer validation path for the monitoring project.