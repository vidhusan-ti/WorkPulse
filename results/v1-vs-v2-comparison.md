# v1 vs v2 Grading Comparison

| Candidate | v1 count | v2 count | Removed | Added |
|-----------|----------|----------|---------|-------|
| Abdul     | 4        | 4        | none    | none  |
| Arleif    | 6        | 5        | Window 4 (routing nightmare) | none |
| Bharath   | 3        | 3        | none    | none  |
| Vidhusan  | 1        | 1        | none    | none  |
| **Total** | **14**   | **13**   | **1**   | **0** |

> Note: The task description quoted v1 counts of Abdul=7, Arleif=13, Bharath=6, Vidhusan=5. Actual v1 counts confirmed by reading the v1.md files were Abdul=4, Arleif=6, Bharath=3, Vidhusan=1. The v2 counts above are relative to the confirmed v1 baseline.

---

## What the new rubric filtered out (and why)

### Arleif Window 4 — "routing nightmare / what do you recommend?" (REMOVED)

**v1 rationale for inclusion:** Arleif diagnoses a systemic failure at the right level of abstraction and frames the trade-off honestly.

**Why v2 removes it:** Fails the **decision-query gate**. The turn describes the problem accurately ("routing is unreliable", "keeping state in order is too hard") but the closing ask — "What do you recommend? I'm open to changing the plan" — delegates insight generation to the LLM. The LLM produces the architectural redesign (stop using a silent router, make concierge the responder, collapse the two-hop system). Arleif's contribution is a detailed, well-framed problem statement. That is near_bar — good context-setting that enables the LLM to produce better output — but the insight itself belongs to the LLM's response. Under v2, a prompt that asks a sharp question and lets the LLM produce the recommendation = near_bar, not above_bar.

**Counterfactual test also informative:** The LLM would have eventually surfaced the silent-router critique through its own analysis of the logs; the user's framing accelerated it but did not introduce a constraint that changed the correct answer.

---

## What was held despite pressure from the new rubric

### Abdul Window 3 — ETL pipeline + multi-hop query
This window includes a question at the end ("will the CLM tool be able to perform as per our expectation?") which initially triggers the decision-query gate. Kept because: the binding contribution is the *constraint* — a concrete ETL workaround proposal plus an exact multi-hop natural-language query. The query itself defines the hardest problem (amendment → governing MSA → ticket-origin in one NL request) more precisely than anything prior. Under v2's exception clause ("only if user's constraints change the correct recommendation"), this passes — the multi-hop query's constraints are what determine whether a CLM can handle it, and the LLM's answer changes as a result.

### Arleif Window 2 — stack-specific constraints (Supabase / no edge functions)
Similar pressure from the decision-query gate (includes "do we have guidance about..."). Kept because: the binding constraints (no edge functions, business logic stays in app layer only) precede the question and are not derivable from prior context. Those constraints materially change the correct architecture output. The question is near_bar but the constraints dominate.

### Bharath Window 1 — test harness design
Ends with "what my target project should generate?" which superficially looks like the LLM is producing the insight. Kept because: the constraint (endpoint-triggered OpenTelemetry log generator as test harness) is Bharath's design — the LLM is being asked to enumerate the implications of that design, not to invent it.

---

## Any new above-bar windows found under v2

None. The stricter rubric reduced the count by 1 (Arleif W4 removed). No new windows were promoted — the decision-query gate and counterfactual test ruled out all borderline near-miss candidates reviewed (Vidhusan's "The Mirror" name-only prompt, Vidhusan's personalised.md session where LLM had already explored adjacent ideas).

---

## Calibration notes for future cycles

1. **Decision-query gate is the sharpest filter.** Roughly half the borderline cases in both v1 and v2 review involved detailed questions. The exception (user constraints change the correct recommendation) is real but narrow — reviewers should require the constraint to be explicitly stated and demonstrably change the LLM's answer.

2. **Problem statements are near_bar by default.** A well-framed problem description that enables the LLM to produce a good response is valuable but not above_bar. The insight must belong to the user, not be unlocked by the user.

3. **Counterfactual test catches "accelerators" vs. "originators."** Some user turns accelerate convergence to an answer the LLM would have eventually reached. Those are near_bar. Above_bar requires a direction, constraint, or correction that the LLM demonstrably would not have produced on its own trajectory.
