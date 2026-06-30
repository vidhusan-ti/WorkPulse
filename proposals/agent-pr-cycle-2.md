# Agent PR — Cycle 2: Stress-Test of Rubric v2 Remaining Gaps

## Ownership Test Validation (Failure Mode 4)

### Abdul W2 (ITD meta-critique) — 4/4 ✅
- **New constraint**: The judgment about *inadequate evidence standards* was not in any prior LLM turn. ✅
- **User-initiated**: Abdul spontaneously challenges the quality of the LLM's own output. ✅
- **LLM extended**: LLM then did the CLM market analysis to strengthen the evidence trail. ✅
- **Removal test**: If replaced with "what do you think of this ITD?", LLM would have defended its document or made incremental improvements — not triggered a full evidence-standard critique. ✅
- **Verdict**: 4/4 — above bar confirmed.
- **Ambiguity flagged**: A skeptical grader might argue Check 1 fails because "the LLM, being self-aware, implicitly knew the ITD's weaknesses." This reasoning is shaky but possible. **Proposed fix**: Rubric should clarify that the "new constraint" check applies to *what appeared in the conversation*, not what the LLM theoretically could have known.

### Arleif W4 (concierge routing nightmare) — 2/4 ❌
- **New constraint**: The LLM had already produced the multi-agent architecture and implicitly knew routing was complex. ⚠️ Ambiguous.
- **User-initiated**: Arleif raised this. ✅
- **LLM extended**: The LLM produced the architectural redesign — that's *originated*, not *extended*. ❌
- **Removal test**: If Arleif had asked "what do you recommend for my multi-agent routing?", LLM might have suggested similar redesign. ❌
- **Verdict**: 2/4 — near_bar. Prior removal was correct.
- **Ambiguity flagged**: Check 1 ("new constraint") is genuinely ambiguous when the user's contribution is a *diagnosis of failure* rather than a *new constraint*. The rubric conflates these two types of user contribution. **Proposed fix**: Split Check 1 into (a) new information/constraint OR (b) diagnosis of failure the LLM had not surfaced. Either counts.

### Bharath W2 (multi-tenant pivot) — 3-4/4, borderline on Check 4
- **New constraint**: LLM was building single-tenant — multi-tenant pivot not in prior output. ✅
- **User-initiated**: Bharath raises this independently. ✅
- **LLM extended**: LLM validates and extends the model. ✅
- **Removal test**: Multi-tenancy is a standard pattern the LLM knows. If the conversation continued without this prompt, would LLM eventually suggest it? Only if asked about scale — without this prompt, it was building single-tenant. **Borderline.**
- **Verdict**: 3-4/4 — above bar, but this is the genuine borderline case for the counterfactual threshold.
- **Proposed fix for rubric**: The removal test should specify a time horizon — "Would the LLM have reached this *in this conversation*, not in some hypothetical future conversation." That closes the "LLM knows this pattern" escape hatch.

---

## Correct Direction Proxy Validation (Failure Mode 5)

### Hard-to-apply window: Arleif W5 (kill dynamic prompts, switch to Anthropic)
The 3 proxies are: (a) LLM accepts without pushback, (b) trajectory resolves toward goal, (c) no later rejection by user.

**Problem**: In W5, Arleif makes a decisive call to switch providers *and* kill dynamic prompts. Both are correct architectural decisions, but:
- Proxy (a) "LLM accepts without pushback" — the LLM accepts because it's instructed to, not because it independently validated the decision. An LLM would rarely push back on a user's firm decision regardless of correctness.
- Proxy (b) "trajectory resolves toward goal" — impossible to verify without seeing the subsequent sessions where the switch actually happened.
- Proxy (c) "no later rejection" — not applicable in a single-session transcript.

**Root problem**: The proxies work well for *technical correctness* (architecture, code) but fail for *strategic decisions* where the LLM is deferential by nature and the outcome is multi-session.

**Better signal**: For strategic/architectural decisions, replace (a) with: *"The LLM's response treats the user's direction as the correct path and does not suggest alternatives or caveats that indicate the user may be wrong."* This distinguishes genuine agreement from deference.

---

## Counterfactual Calibration

### Clearly above bar (counterfactual = NO)
**Abdul W1** (quarantine-then-scan S3 pipeline):
- Without this prompt: LLM would have proposed a simple upload-and-parse pipeline.
- The specific threat model (parser exploits, malware in PDFs), the quarantine-first pattern, and the background job design are all user-originated.
- Counterfactual answer: Clearly NO — the LLM would not have produced this architecture.

### Clearly near bar (counterfactual = YES)
**Vidhusan W3** (LiteLLM vs direct OpenAI):
- Without this prompt: If user had asked "what are my options for LLM integration?", LLM would have produced the same comparative analysis.
- The user's contribution is the *question*, not any constraint, data, or direction that changes what the correct answer is.
- Counterfactual answer: Clearly YES — the LLM produces the insight, not the user.

### Borderline case
**Bharath W2** (multi-tenant pivot):
- Without this prompt: LLM *might* have suggested multi-tenancy if later asked about scaling. But it wasn't going there on its own.
- Resolution: Apply time-horizon constraint — "in *this* conversation, without this prompt, the LLM was building single-tenant." That makes the counterfactual answer NO.
- **Graders should apply the in-conversation time horizon, not a hypothetical "eventually the LLM would know this" standard.**

### Recommended threshold wording
> "Would the LLM have reached this output *within this conversation* without the user's specific input? If yes, the user's contribution is near_bar at best, even if the question was sharp or the framing was good."

---

## Proposed Calibration Examples for Rubric

### Example A — above_bar (embed in rubric)
**Prompt**: *"i'd like to store my pdf first in a quarantined s3 directory or bucket first, and then run a background job to get that file, run security scan for malware, parser exploits etc. and then extract metadata, store it in db record, and then put it into respective s3 bucket."*

**Why above_bar**: The quarantine-first security model with parser exploit threat modelling was not in any prior LLM output. The LLM validates and refines — it does not originate. Counterfactual: LLM would have proposed a simple upload-and-parse pipeline. Ownership: 4/4.

### Example B — near_bar (embed in rubric)
**Prompt**: *"Should I use LiteLLM or call the OpenAI API directly for this?"*

**Why near_bar**: This is a decision query — the user asks a sharp, well-framed question, but the comparative analysis (trade-offs, recommendation) is produced entirely by the LLM. The user contributed the question, not the insight. Ownership: 2/4. Decision-query gate fires.

---

## Summary: 3 fixes for rubric v3

1. **Clarify Check 1 of ownership test** — "new constraint OR failure diagnosis the LLM had not surfaced." Closes the Abdul W2 ambiguity.
2. **Add time-horizon to removal test** — "within *this* conversation, not hypothetically." Closes the Bharath W2 borderline ambiguity.
3. **Replace Proxy (a) for strategic decisions** — distinguish genuine LLM agreement from deference. Closes the Arleif W5 domain gap.
4. **Embed calibration examples A and B directly in rubric** — one above_bar, one near_bar, self-contained.
