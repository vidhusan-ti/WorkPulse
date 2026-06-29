# v1 vs v2 Grading Comparison

| Candidate | v1 count | v2 count | Removed | Added |
|-----------|----------|----------|---------|-------|
| Abdul     | 4        | 4        | 0       | 0     |
| Arleif    | 6        | 6        | 0       | 0     |
| Bharath   | 3        | 3        | 0       | 0     |
| Vidhusan  | 1        | 1        | 0       | 0     |
| **Total** | **14**   | **14**   | **0**   | **0** |

> Note: v1 counts above reflect the already-calibrated results after prior trimming (Arleif down from 13→6, Bharath down from 6→3, Vidhusan down from 5→1). The rubric v2 re-grading confirmed that the windows surviving calibration are genuinely above bar — the new stricter tests validate the prior human-reviewed results rather than removing further windows.

## What rubric v2 confirmed about these windows

All surviving windows pass all three new gates cleanly:
- **Counterfactual test**: In every case, removing the user's prompt would have left the LLM on a worse or directionless path.
- **Decision-query gate**: None of the surviving windows are question-only prompts that let the LLM produce the insight.
- **4-part ownership test**: All pass ≥3/4 ownership checks.

## What rubric v2 filters out (previously flagged false positives)

| Window | Candidate | Failure mode | Gate that fires |
|--------|-----------|--------------|-----------------|
| W9 (psycopg2/SQLAlchemy spec) | Bharath | Well-structured spec, standard patterns | Counterfactual test |
| W3 (LiteLLM vs OpenAI) | Vidhusan | Decision query, LLM produces the analysis | Decision-query gate |
| W9 ("mindblowing prompt") | Vidhusan | Thin reactive spark, LLM develops it | Counterfactual test |

These were already filtered in prior calibration cycles — rubric v2 now provides explicit criteria that explain *why* they fail, making future grading more consistent.

## Key finding

The rubric v2 changes don't remove additional windows from the already-calibrated set — they **explain and justify** the calibration decisions with explicit, repeatable tests. This is the right outcome: the human reviewers had good instincts, and the rubric now formalises those instincts so automated grading can replicate them.
