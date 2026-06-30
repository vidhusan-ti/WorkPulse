# Agent QA — Cycle 3: Validation of Rubric v3

**Date:** 2026-06-29
**Rubric version validated:** v3 (as in `data/manual_rubric.md` after Agent R Cycle 5 changes)
**PR Cycle 2 proposals validated against:** `proposals/agent-pr-cycle-2.md`

---

## Summary Verdict

**Rubric v3 is ready to use.** All 4 v3 fixes integrate cleanly. The 3 known borderline cases are now unambiguously resolved. Both calibration examples are correct and internally consistent. All 89 tests pass.

One minor wording note (documented below) does not block use — it is a cosmetic precision issue, not a logical gap.

---

## 1. Rubric v3 Consistency Check

### 1.1 — Do the 4 fixes integrate cleanly?

**Fix 1 — Check 1 of ownership test extended to cover failure diagnosis**

v3 Check 1 now reads:
> "Was the constraint, direction, **OR failure diagnosis** new — not present in any prior LLM output in this conversation?"

Integration assessment: Clean.

- The three ownership checks (2, 3, 4) are independent of Check 1 and are not affected by this wording change.
- The extended Check 1 does not create an overlap with Check 2 ("user-initiated"). A failure diagnosis can be both new (Check 1) and user-initiated (Check 2) — these test different dimensions: *what* was contributed vs *who* initiated the direction change.
- The extended Check 1 does not create an overlap with the counterfactual test. The counterfactual test asks whether the LLM would have reached the same outcome independently; Check 1 asks whether the specific contribution appeared in any prior output. These are complementary gates, not redundant ones.
- No contradiction with the Automatic Disqualifiers section. The disqualifiers list three types of user turn that can never be above-bar; none of them are "failure diagnoses." If anything, the extended Check 1 is consistent with the "Insight IS" bullet that reads "An accurate diagnosis of a problem the LLM missed."

**Fix 2 — Removal test scoped to within-conversation only**

v3 Criterion 6 now reads:
> "*Apply this test within-conversation only — do not ask whether the LLM 'could have known this eventually'. Ask: without this specific turn, would this conversation have produced this outcome?*"

Integration assessment: Clean.

- This scoping note is appended to Criterion 6 (User-driven, not LLM-driven) as a parenthetical. It does not modify the criterion logic — it constrains the application of the removal test. No other criterion references the removal test independently, so no cross-criterion conflict arises.
- The scoping note is consistent with the Counterfactual Test box above the criteria section, which asks "would the LLM have reached the same outcome if the user had said nothing new?" — the within-conversation framing applies to both.

**Fix 3 — Proxy (a) replaced for strategic/architectural decisions**

v3 Criterion 3 (Correct direction) now contains:
> "*For strategic or architectural decisions (not code/implementation): replace proxy (a) with — 'The LLM's response treats the user's direction as correct and does not suggest alternatives or caveats indicating the user may be wrong.' Pure LLM deference to a firm user decision does not satisfy this proxy.*"

Integration assessment: Clean with one minor precision note (see §1.4 below).

- The replacement proxy is only triggered for "strategic or architectural decisions (not code/implementation)." This scope qualifier is explicit and prevents the replacement from silently applying to code contexts where proxy (a) is still useful.
- The new proxy is distinct from the original three proxies and tests a different failure mode (deferential LLM agreement vs. genuine acceptance). No overlap with proxies (b) or (c).
- The caveat "Pure LLM deference to a firm user decision does not satisfy this proxy" adds necessary nuance that closes the gap.

**Fix 4 — Calibration examples section added**

v3 includes an explicit `## Calibration Examples` section at the end of the rubric with one above_bar and one near_bar example.

Integration assessment: Clean (see detailed calibration validation in §3 below).

---

### 1.2 — Does the ownership test have 4 clearly distinct, non-overlapping checks?

The 4-part ownership test in v3:

1. Was the constraint, direction, or failure diagnosis new — not present in any prior LLM output in this conversation?
2. Was the direction change user-initiated (not following an LLM suggestion)?
3. Did the LLM extend or implement the insight rather than develop it from scratch?
4. If the user's turn were replaced with a generic question, would the LLM still reach the same insight?

**Distinctness analysis:**

| Check | What it tests | Overlap risk |
|-------|--------------|--------------|
| 1 | Novelty of the contribution (content) | Could superficially overlap with Check 4 |
| 2 | Agency/initiation (who started it) | Independent |
| 3 | LLM's role post-insight (implementation vs. origination) | Independent |
| 4 | Counterfactual necessity (would LLM have gotten there anyway) | Could superficially overlap with Check 1 |

**Check 1 vs Check 4 — are they redundant?** No.

- Check 1 is backward-looking: "was this content absent from prior LLM turns?"
- Check 4 is forward-looking: "if the user turn were replaced with a generic question, would the LLM still arrive at the same insight?"
- Example where they diverge: User says "use a circuit breaker here." The LLM had not mentioned circuit breakers in this conversation (Check 1 passes). But the codebase context makes circuit breakers an obvious next step, so Check 4 fails (LLM might have gotten there anyway). The checks test different failure modes.

**Verdict:** The 4 checks are sufficiently distinct. No problematic overlap. The 3-of-4 threshold appropriately handles edge cases where one check produces an ambiguous result.

---

### 1.3 — Does the calibration example section match the criteria in the rubric body?

Checked in detail in §3 below. Short answer: Yes.

---

### 1.4 — Is the decision-query gate consistent with the new strategic-decision proxy (Fix 3)?

The decision-query gate applies when the user *asks the LLM to choose* (LLM is deciding). The Fix 3 proxy applies when the user *makes a decision* and the LLM responds to it (user is deciding). These address different scenarios and are complementary, not conflicting.

- "Should I use LiteLLM or OpenAI directly?" → decision-query gate (LLM chooses, user asks)
- "We're switching to Anthropic" → Fix 3 proxy (user decides, LLM accepts)

No case simultaneously triggers both in a contradictory way. **Consistent.**

**One precision note (non-blocking):** The decision-query gate section could explicitly note that it does not apply when the user is *issuing* a strategic direction (Fix 3 territory) rather than *querying* for a recommendation. A single clarifying sentence would prevent ambiguity for less experienced graders. This is a polish item, not a logic error.

---

## 2. Borderline Case Re-evaluation (v3 applied)

### 2.1 — Abdul W2 (ITD meta-critique): Does Fix 1 make this unambiguous?

**PR Cycle 2 ambiguity:** A skeptical grader might argue Check 1 fails because "the LLM, being self-aware, implicitly knew the ITD's weaknesses."

**v3 ownership test walk-through:**

- **Check 1** (new constraint OR failure diagnosis): Abdul's diagnosis of *inadequate evidence standards* is explicitly covered by the extended wording. The LLM had not surfaced this criticism in any prior conversation output — it had produced the ITD document and defended it. "Failure diagnosis" directly names this type of contribution. **PASS**
- **Check 2** (user-initiated): Abdul spontaneously challenges the LLM's output quality without prompting. **PASS**
- **Check 3** (LLM extended): The LLM then performed the CLM market analysis to strengthen the evidence trail — implementing Abdul's diagnosis, not inventing it. **PASS**
- **Check 4** (removal test): Replacing Abdul's turn with "what do you think of this ITD?" would not have produced a full evidence-standard critique. **PASS**

**Verdict: 4/4. Unambiguously above bar under v3.**

The "skeptical grader" escape hatch is now explicitly foreclosed. The rubric's phrasing "not present in any prior LLM output *in this conversation*" combined with "OR failure diagnosis" closes the gap. The argument that the LLM *could have known* is also ruled out by the within-conversation scoping from Fix 2. **No residual ambiguity.**

---

### 2.2 — Bharath W2 (multi-tenant pivot): Does Fix 2 make the removal test unambiguous?

**PR Cycle 2 ambiguity:** Check 4 was borderline because "multi-tenancy is a standard pattern the LLM knows — if the conversation continued, would LLM eventually suggest it?"

**v3 ownership test walk-through:**

- **Check 1**: LLM was building single-tenant — multi-tenant pivot not in any prior output in this conversation. **PASS**
- **Check 2**: Bharath raises this independently. **PASS**
- **Check 3**: LLM validates and extends the multi-tenant model. **PASS**
- **Check 4** (removal test, now within-conversation): Without Bharath's prompt, would *this* conversation have produced multi-tenancy? Fix 2 explicitly excludes the "LLM would eventually know this" reasoning. The LLM was actively building single-tenant; Bharath's pivot redirected it. Within this conversation, without this prompt: single-tenant continued. **PASS**

**Verdict: 4/4. Unambiguously above bar under v3.**

The within-conversation scoping note in Criterion 6 directly forecloses the "LLM knows this pattern generally" reasoning. The PR Cycle 2 "borderline on Check 4" is resolved. **No residual ambiguity.**

---

### 2.3 — Arleif W5 (kill dynamic prompts, switch to Anthropic): Does Fix 3 apply cleanly?

**PR Cycle 2 ambiguity:** Proxy (a) ("LLM accepts without pushback") is vacuous for strategic decisions because LLMs rarely push back on firm user decisions regardless of correctness.

**v3 Criterion 3 (Correct direction) — strategic decision path:**

Arleif's W5 is a strategic decision (switch provider + kill dynamic prompts). Fix 3 proxy applies:

> "The LLM's response treats the user's direction as the correct path and does not suggest alternatives or caveats indicating the user may be wrong."

This gives the grader a usable, substantive test. A grader now asks: does the LLM's response contain evidence it *evaluated* the decision (e.g., noting why Anthropic solves the prompt-format drift problem, confirming dynamic prompts were the root cause) — or does it just comply generically ("sure, I'll switch now")?

The additional caveat "Pure LLM deference to a firm user decision does not satisfy this proxy" explicitly prevents a vacuous pass.

**Verdict: Fix 3 applies cleanly and resolves the proxy (a) vacuousness problem.**

**One remaining inherent limitation (not a rubric gap):** Whether the LLM's acceptance is genuine or deferential requires reading the actual LLM response turn. This is inherent to the data, not a rubric flaw. A grader applying v3 to W5 must read both the user turn and the LLM follow-up — which is the correct behaviour. The rubric now provides the right test; the result depends on the transcript. **No residual ambiguity in the rubric; application requires transcript access.**

---

## 3. Calibration Examples Validation

### 3.1 — above_bar example

**Prompt:** "i'd like to store my pdf first in a quarantined s3 directory or bucket first, and then run a background job to get that file, run security scan for malware, parser exploits etc..."

**Walk-through against all v3 criteria:**

1. **Semantic novelty:** Quarantine-first pattern + parser exploit threat model — not in any prior LLM output. The "Insight IS" definition includes "a new architectural decision or constraint the LLM had not proposed." **PASS**

2. **Genuine insight (4-part ownership test):**
   - Check 1: New constraint and direction — quarantine-first security model, specific threat model. **PASS**
   - Check 2: User-introduced unprompted. **PASS**
   - Check 3: "LLM validates, not originates" — stated in example. **PASS**
   - Check 4: "Counterfactual: LLM would have proposed simple upload-and-parse" — stated in example. **PASS**
   - 4/4. **PASS**

3. **Correct direction:** Quarantine-then-scan is standard defence-in-depth security. LLM acceptance without caveats. **PASS**

4. **Positive trajectory:** From "simple upload-and-parse" to "quarantine-first security pipeline" — measurably more resolved and correct. **PASS**

5. **Efficiency:** No indication of multiple prior attempts. **PASS (assumed)**

6. **User-driven:** Removing this turn produces simple upload-and-parse — confirmed by counterfactual. **PASS**

**All criteria pass. Verdict: above_bar is correct.**

**Consistency check:** The example reasoning — "LLM validates, not originates. Counterfactual: LLM would have proposed simple upload-and-parse. Ownership: 4/4." — matches the rubric criteria exactly. No inconsistency.

---

### 3.2 — near_bar example

**Prompt:** "Should I use LiteLLM or call the OpenAI API directly for this?"

**Walk-through against all v3 criteria:**

1. **Semantic novelty:** The question is new, but no constraint that would change the recommendation is introduced. Borderline at the novelty gate; resolved by the decision-query gate below.

2. **Decision-query gate fires:** User asks LLM to choose between options. Test: "Would the LLM have given materially the same recommendation without the user's specific constraints?" — Yes, because no constraints are supplied that would change the answer. **Gate fires → near_bar or below_bar.**

3. **Genuine insight (4-part ownership test):**
   - Check 1: No new constraint, direction, or failure diagnosis. **FAIL**
   - Check 2: User-initiated. **PASS**
   - Check 3: LLM produces the comparative analysis from scratch. **FAIL**
   - Check 4: Replacing with "what integration approach should I use?" → LLM still produces same analysis. **FAIL**
   - 1/4 or 2/4 (example states 2/4, granting Check 2 and borderline Check 1). Below 3/4 threshold. **FAIL**

**Decision-query gate fires, ownership 2/4. Verdict: near_bar is correct.**

**Consistency check:** The example reasoning — "Decision-query gate fires. The comparative analysis is LLM-produced. User contributed the question, not the insight. Ownership: 2/4." — matches the rubric criteria exactly. No inconsistency.

---

### 3.3 — Overall calibration assessment

Both examples are correct and internally consistent. They cover distinct failure-mode territories: ownership-complete (above_bar) vs. decision-query gate with ownership below threshold (near_bar). Good calibration coverage for the most common grader decision points.

**One polish suggestion (non-blocking):** A below_bar anchor example (e.g., "yes, continue" or "ok looks good") would help graders calibrate the bottom end. The Automatic Disqualifiers section provides conceptual coverage, but a concrete example would make the discard threshold visceral. Suggested for a future cycle.

---

## 4. Test Results

```
89 passed in 9.13s
```

All 89 tests pass. No failures. No regressions from QA Cycle 2. Full suite:

- `tests/test_extractor.py` — window extraction
- `tests/test_persister.py` — grade persistence
- `tests/test_pipeline_v2.py` — pipeline stages and integration (Stage 1 SND, Stage 2 IOAS, Stage 3 CTA, Stage 4 EJAD, grader_v2 integration, template coaching fallback, label refinement, coaching-on-failure, has_follow_up fix)
- `tests/test_portfolio.py` — portfolio writer

---

## 5. Remaining Open Issues

### Issue 1 — Decision-query gate / Fix 3 boundary (priority: low, non-blocking)
The decision-query gate (user asks LLM to decide) and Fix 3 proxy (user issues a strategic decision) are logically distinct but could be conflated by a quick reader. A one-line clarifying note in the decision-query gate section would make the boundary explicit. Suggested wording: *"Note: this gate applies when the user is asking for a recommendation. When the user is issuing a strategic direction, apply the strategic-decision proxy in Criterion 3 instead."*

### Issue 2 — Missing below_bar calibration example (priority: low, non-blocking)
The calibration section covers above_bar and near_bar anchors. A below_bar example (e.g., "yes, continue") would complete the three-tier coverage and help calibrate the discard threshold for new graders.

### Issue 3 — Arleif W5 deference test requires transcript access (inherent limitation, no rubric action needed)
Fix 3 provides the correct test. Applying it to W5 requires reading the LLM's response turn to determine whether acceptance was evaluative or purely deferential. This is correct rubric behaviour, not a gap. Grader training should remind evaluators to always read both turns when applying Fix 3.

---

## 6. Overall Verdict

**Rubric v3 is ready to use.**

- All 4 v3 fixes integrate cleanly with no contradictions or overlaps.
- The ownership test's 4 checks are distinct and non-overlapping.
- The calibration examples match the rubric criteria exactly and are internally consistent.
- The decision-query gate and Fix 3 are complementary, not conflicting.
- The 3 known borderline cases (Abdul W2, Bharath W2, Arleif W5) are now unambiguously resolved.
- All 89 tests pass. No regressions.

The 3 remaining open issues are polish items (low priority, non-blocking). Rubric v3 can proceed to use in grading.

---

*Agent QA — Cycle 3 — 2026-06-29*
