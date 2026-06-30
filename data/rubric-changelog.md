# Rubric Changelog

## v3 — 2026-06-29 (Agent R Cycle 5)

**Source:** Applied 4 fixes from Agent PR Cycle 2 stress-test of rubric v2.

### What Changed

**1. Ownership test Check 1 wording (Fix 1)**
Check 1 previously read: "Was the constraint or direction **new** (not present in any prior LLM turn)?"
Updated to: "Was the constraint, direction, **OR failure diagnosis** new — not present in any prior LLM output in this conversation?"
*Why:* Agent PR Cycle 2 found that Check 1 was ambiguous when the user's contribution was a *diagnosis of failure* rather than a new constraint (e.g., Abdul W2 meta-critique). The old wording conflated two distinct types of user contribution. Now either counts.

**2. Removal test time-horizon (Fix 2)**
Added explicit scope note to criterion 6 (User-driven, not LLM-driven):
"Apply this test within-conversation only — do not ask whether the LLM 'could have known this eventually'. Ask: without this specific turn, would this conversation have produced this outcome?"
*Why:* Agent PR Cycle 2 identified the Bharath W2 borderline case — where graders might reason "the LLM knows multi-tenancy patterns, so it would have suggested it eventually." That escape hatch invalidates the removal test. The fix constrains the test to the actual conversation.

**3. Correct direction proxy (a) for strategic decisions (Fix 3)**
Added a callout block under the domain-independent proxy signals:
"For strategic or architectural decisions (not code/implementation): replace proxy (a) with — 'The LLM's response treats the user's direction as correct and does not suggest alternatives or caveats indicating the user may be wrong.' Pure LLM deference to a firm user decision does not satisfy this proxy."
*Why:* Agent PR Cycle 2 found that for strategic decisions (e.g., Arleif W5 provider switch), proxy (a) "LLM accepts without pushback" is vacuous — LLMs rarely push back on firm user decisions regardless of correctness. The replacement proxy distinguishes genuine validation from deference.

**4. Embedded calibration examples (Fix 4)**
Added a new "Calibration Examples" section at the end of the rubric with two anchor cases:
- **above_bar:** Abdul W1 quarantine-first S3 pipeline (ownership 4/4, counterfactual clearly NO)
- **near_bar:** Vidhusan W3 LiteLLM vs OpenAI decision query (decision-query gate fires, ownership 2/4)
*Why:* Rubric rules alone are insufficient for consistent calibration. Graders need concrete examples that anchor both ends of the boundary. These two cases were identified by Agent PR Cycle 2 as the clearest representatives of each side.

### What Did NOT Change

The core principle, tier definitions, insight definition, counterfactual test, decision-query gate, automatic disqualifiers, near-bar coaching template, and quick reference checklist are all preserved from v2.


## v2 — 2026-06-29 (Agent R Cycle 4)

**Source:** Applied all 5 failure modes identified in Agent PR Cycle 1.

### What Changed

**1. Added window definition**
The rubric previously used "window" without defining it. Now: a window = focal user turn + surrounding context turns (prior LLM turns = context; following turns = trajectory evidence). Required for consistent human evaluation.

**2. Fixed tier vocabulary**
Replaced inconsistent "best" / "average" / "near-miss" with consistent `above_bar` / `near_bar` / `below_bar` throughout. These now match pipeline output labels exactly.

**3. Defined "insight" with examples and a counterfactual test** *(Priority 1)*
"Insight" appeared 5 times in v1 with no definition. v2 adds:
- A positive definition of what insight IS (new constraints, user-originated principles, missed-problem diagnosis)
- A negative definition of what insight is NOT (restatement, reformatting, echo/approval)
- A mandatory counterfactual test: "Would the LLM have reached the same outcome if the user had said nothing new?" If yes → not insight.

**4. Added decision-query gate** *(Priority 2)*
A prompt asking the LLM to recommend between options is NOT `above_bar` unless the user's constraints change what the correct recommendation would be. Addresses the Vidhusan W3 false-positive pattern (well-framed decision query with general engineering criteria graded `above_bar`).

**5. Replaced "correct direction" with domain-independent proxy signals** *(Priority 3)*
"Steering in the correct direction" was undefined in v1. v2 adds three domain-independent proxy signals any grader can apply without domain expertise: (a) consistency with the user's prior stated constraints, (b) LLM accepts without flagging errors, (c) conversation resolves rather than becoming more circular. Domain-expert path still available for direct correctness verification.

**6. Added 4-part insight ownership test**
Replaces the vague "key insight should be from the user" with a 4-part test. Insight is user-owned if ≥3 of 4 pass; otherwise co-developed → `near_bar`. Directly addresses Failure Modes 3 and 4 from Agent PR Cycle 1.

**7. Added automatic disqualifiers section**
Explicit list of conditions that immediately prevent `above_bar` grading, replacing scattered implicit disqualifiers throughout v1.

**8. Added near-bar coaching template**
v1 said "return the reason for failure and improvement needed" with no structure. v2 adds a 3-field template: Failed (category) / What happened (one sentence) / To make this above bar (one concrete action).

**9. Added quick reference checklist**
8-item checklist for graders. Enables consistent application in under 2 minutes.

### What Did NOT Change

The core principle is preserved verbatim: *"The conversation should be user-driven and not LLM-driven."*
The fundamental evaluation approach (grade the trajectory, not the prompt alone) is preserved.

### Why These Changes

Agent PR Cycle 1 identified that the top 3 false positives across all candidates (Bharath W9, Vidhusan W3, Vidhusan W9) all stemmed from the same root cause: graders rewarded the quality of the user's output (polished spec, sharp question, clever observation) rather than testing whether the user's contribution was genuinely novel or causally responsible for the outcome. All v2 changes are targeted at making these tests explicit and mechanical enough that graders without domain expertise can apply them consistently.
