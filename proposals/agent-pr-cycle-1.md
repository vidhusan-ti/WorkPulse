# Agent PR — Cycle 1: Rubric Failure Analysis

*Generated: 2026-06-29*
*Inputs: manual_rubric.md, results/grading-notes-cycle-3.md, results/{abdul,arleif,bharath,vidhusan}/v1.md, proposals/agent-t-cycle-2.md, proposals/agent-r-cycle-3.md*

---

## Failure Mode 1: Well-Structured Task Descriptions Accepted as Above-Bar

**Rubric gap:**
The rubric says "even if prompts are well structured and have good content, if they don't bring any insights, discard those prompts" — but it never defines what makes content constitute insight vs. well-structured specification. The word "insight" appears five times in the rubric without a working definition. This leaves graders relying on *impression* (long, technical, detailed = must be above-bar) rather than a testable criterion.

**How it manifests:**
Graders accept specification prompts where the user delivers a technically impressive, well-organised design, but the spec uses standard patterns that the LLM could have proposed unprompted. The grader rewards the *quality of the document*, not the *novelty of the user's contribution*.

**Test case — Bharath W9:**
> "Phase A: Set up psycopg2 connection pool with env-var config (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD). Phase B: SQLAlchemy models mirroring the existing schema... Phase C: CRUD operations... Phase D: Alembic migration..."

The four-phase decomposition (connection pool → ORM models → CRUD operations → migration) is the canonical incremental approach any LLM would propose for a DB integration task. The technology choices (psycopg2, SQLAlchemy, Alembic) are the Python standard stack. Agent T flagged this: "If the LLM had proposed this architecture, the user would likely have accepted it." This window was graded above-bar despite being a standard specification delivered clearly.

Contrast with **Abdul W1** (quarantine S3 + security scan pipeline), which is also a technical specification but introduces a threat-model-driven architecture the LLM had not proposed — the quarantine-before-processing principle was user-originated.

**Root cause:**
The rubric has no test for "would the LLM have proposed this unprompted?" Graders have no mechanism to distinguish *novel specification* (user brings architecture the LLM didn't have) from *standard specification* (user delivers a clean implementation of a pattern the LLM already knows). Both look identical on surface quality. The rubric's gate ("if they don't bring any insights, discard") is present but the word "insights" does the entire filtering work without any definition.

**Proposed fix:**
Add a mandatory counterfactual test immediately after the quality assessment:

> "Before grading a specification prompt above bar, apply the counterfactual test: would the LLM have proposed a materially similar architecture if the user had simply asked 'how should I implement this?' If yes, grade as near-bar or below-bar regardless of specification quality. A standard specification delivered with good structure is below-bar. A specification that introduces a constraint, pattern, or design decision the LLM could not have derived from the stated requirements alone is above-bar."

---

## Failure Mode 2: Decision Queries That Trigger Strong LLM Responses Accepted as Above-Bar

**Rubric gap:**
The rubric's criterion on user-driven conversations (criterion G: "The conversation should be user-driven and not LLM-driven") applies to the *output* of the conversation, not to the *ownership* of the steering. A well-framed question can produce an entirely LLM-driven answer and still feel user-driven because the user asked well. There is no rubric criterion that explicitly says "a recommendation request is not above-bar unless the user's constraints change what the recommendation would be."

**How it manifests:**
Graders see: structured question → high-quality LLM response → good trajectory. They conclude the prompt was above-bar because the *outcome* was good. But the insight in the outcome is entirely the LLM's — the user contributed structure and framing, not substance.

**Test case — Vidhusan W3:**
> "I'm choosing between LiteLLM and a direct OpenAI client for structured JSON grading. Constraints: single classify call, must fallback to heuristics, minimal dependencies. Recommend one approach and explain the tradeoff in one paragraph."

This is a very clean decision query with real constraints. However:
- The constraints (single call, fallback to heuristics, minimal dependencies) are standard criteria any engineer would apply to this problem — not domain-specific knowledge the LLM lacks.
- The user is asking for a recommendation, not providing one.
- If the user had sent "which is better, LiteLLM or direct OpenAI client for a simple grading task?", they would have received a similar answer.

Agent T correctly flagged this as near-bar: "The constraints are real, but the LLM would have given a reasonable answer with minimal framing." Yet the grading agent marked it above-bar.

Contrast with **Vidhusan W2** where the user *contradicts* the LLM's buy-Sirion recommendation with concrete constraints (self-build with Cursor/Claude, ~40 users, specific cost model). Here the user's constraints *change the correct answer* — that is what makes it above-bar.

**Root cause:**
The rubric conflates "user contributed to good framing" with "user contributed the key insight." A well-structured question is good prompting but is not user-driven insight. The rubric has no criterion for this distinction. Grading agents fall into the trap of rewarding good outcomes, which is explicitly warned against in grading-notes-cycle-3 ("the insight is the LLM's, not the user's") but that warning exists only in the notes, not in the rubric itself.

**Proposed fix:**
Add an explicit criterion addressing decision queries:

> "A prompt that asks the LLM to choose between options or recommend an approach is above-bar ONLY if the user's supplied constraints, context, or framing change what the correct recommendation would be — i.e., the answer to the user's query would be materially different without the user's specific input. A well-structured question using general engineering criteria (performance, simplicity, dependencies) is near-bar at best. The test is: does removing the user's constraints reduce the quality of the LLM's answer? If the LLM would have arrived at the same recommendation without the user's framing, grade as near-bar."

---

## Failure Mode 3: Thin Reactive Sparks That the LLM Develops Accepted as Above-Bar

**Rubric gap:**
The rubric says "The key insight should be from the user and not from the LLM" but it does not define what "key insight" means or how to attribute insight ownership when the user provides a brief observation and the LLM develops it substantially. This gap creates a judgment problem: a one-sentence user prompt that the LLM turns into a detailed design feels like a successful conversation — so graders reward the *conversation quality*, not the *user's contribution quality*.

**How it manifests:**
A user writes 1–2 sentences that are non-obvious but brief. The LLM expands these into a detailed, valuable response. The grader sees a short user turn followed by a high-quality LLM response and faces a calibration question: was the user's spark itself the insight, or did the LLM do 90% of the insight work?

**Test case — Vidhusan W9:**
> "hey wait sometime a prompt can be mindblowing like it will be out of the box but its not needed to satisfy all the 8 gates right"

This is a genuine observation — the user has identified a real tension in rubric design. But:
- The observation is expressed as a tentative question, not a principled statement.
- The LLM's response does all the work of resolving the tension: it develops the two-axis scoring framework (insight quality vs. portfolio readiness), names the axes, and produces the concrete rule.
- The user's contribution is the trigger, not the insight. The insight lives in the LLM's response.

Agent T's verdict: "Near-bar per rubric: 'key insight should be from the user and not from the LLM.'" Yet this was graded above-bar.

Contrast with **Arleif W3**: "so you saying there is no type safety pretty much in that area? I don't want logs, logs are just a different way to hide. I want compile time failures or worst the operation to fail so someone fixes the issue." This is also short, but the key insight — "logs are a different way to hide, not a fix" — is entirely in the user's turn. The LLM implements, not develops.

**Root cause:**
The rubric does not specify where the threshold is between "thin spark" and "owned insight." The phrasing "key insight should be from the user" requires graders to make an attribution judgment that is inherently subjective. Without a test — e.g., "if you remove the user's turn and replace it with a blank, does the LLM still arrive at the insight?" — graders default to rewarding conversations where the LLM's response was impressive.

**Proposed fix:**
Replace the vague "key insight from user" criterion with a removal test:

> "The user's contribution must carry the key insight independently. Apply the removal test: if the user's prompt were replaced with a generic 'what do you think?' — would the LLM still produce the same substantive insight? If yes, the insight is LLM-driven and the window is near-bar at best, regardless of how well the user's prompt frames the topic. The user must contribute the substance of the insight, not just trigger the LLM to find it."

---

## Failure Mode 4: "Key Insight from User vs. LLM" Applied Inconsistently Across Similar Window Patterns

**Rubric gap:**
This is the rubric's hardest criterion to apply and it appears without any operationalisation. The rubric simply states "The key insight should be from the user and not from the LLM" (one sentence). There is no definition of what makes an insight "key", no method for attributing ownership when insight is co-developed, no examples, and no guidance for the "sharp question forcing LLM to produce insight" edge case.

**How it manifests:**
The same window pattern — sharp user question → high-quality LLM response — receives different verdicts because no consistent test exists. The grading notes explicitly name this as the hardest criterion: "When the user asks a sharp question that forces the LLM to produce insight, who owns the insight?"

This inconsistency is visible across candidates:

- **Arleif W10** (catching LLM hedging on foundational assumption — "You can't be saying 'if' on a fundamental fact like that"): User asks a sharp corrective question. LLM then verifies the fact. Graded above-bar. ✅ Correctly above-bar — the user's *correction* ("you cannot design around an unverified architectural fact") is the insight, stated explicitly in the user turn.

- **Vidhusan W3** (LiteLLM vs. direct OpenAI decision query): User asks a well-framed question. LLM gives a good answer. Graded above-bar. ❌ Should be near-bar — the LLM's recommendation is the insight; the user contributed only framing.

- **Arleif W12** ("why is there an IF, can't we go 1 way or another"): User objects to a conditional fallback. LLM simplifies. Graded above-bar, flagged borderline by Agent T. The design principle ("clean architecture, no conditional fallbacks") is in the user turn — borderline above-bar.

All three follow the same surface pattern but the attribution of insight is different in each case. Without a consistent test, graders make different calls.

**Root cause:**
The criterion "key insight from user" is a conclusion, not a test. Graders need a method to evaluate it, not a principle to agree with. Without a method, each grader substitutes their own threshold. The rubric provides no examples of what "user-owned insight" looks like vs. "LLM-developed insight following a user spark."

**Proposed fix:**
Add a four-part insight ownership test:

> "To determine whether the key insight belongs to the user or the LLM, apply all four checks. The insight is user-owned if it passes at least three:
> 1. The insight is explicitly stated in the user's turn (not just implied or asked about)
> 2. The insight was not present (explicitly or implicitly) in any prior LLM turn in the window
> 3. The LLM's subsequent response implements, validates, or extends the insight rather than developing it from scratch
> 4. If the user's turn were replaced with a question ('how should we handle this?'), the LLM could not have reached the same insight without the user's specific information or principle
>
> If only two of four checks pass, the insight is co-developed — grade as near-bar."

---

## Failure Mode 5: "Correct Direction" Is Undefined, Making Correctness Grading Domain-Dependent

**Rubric gap:**
The rubric states "The user should not misdirect the LLM to go in the wrong direction, the steering of the LLM should be in the correct direction." This criterion exists to prevent graders from rewarding confident-but-wrong steering, but "correct direction" is entirely undefined. Graders reviewing code, design, and analysis contexts have no rubric guidance on what "correct" means for each. The grading notes explicitly flag this: "Requires knowing the domain. Reviewers may not recognise wrong directions in unfamiliar codebases."

**How it manifests:**
Graders who understand the domain apply this correctly. Graders who don't know the codebase cannot verify whether the user's architectural decision was sound. This creates a systematic bias: technically complex transcripts (where the grader lacks domain context) are graded more leniently than simple ones (where correctness is obvious). In the extreme case, a confident-but-wrong architectural decision by the user gets graded above-bar because "the user seemed sure and the LLM followed along."

**Test case — Bharath W4 (above-bar correctly, but illustrates the domain-knowledge dependency):**
> "Build a Node.js Express application... must break in predictable, classifiable ways when specific endpoints are hit. [Four failure routes: TypeError, ECONNREFUSED, CPU busy-loop, process.exit on missing env var]"

A grader who understands incident-response agent design recognises these four failure classes (logic error, dependency failure, saturation, config panic) as semantically well-chosen for exercising a classifier. A grader without that context sees "a detailed spec" and grades on completeness, not on whether the failure taxonomy was actually well-designed for the stated purpose.

The risk: if a user had specified *badly designed* failure classes (e.g., only variations on TypeError), a domain-naive grader would still give full credit because the spec looks complete and the LLM implemented it.

**Root cause:**
The correctness gate requires domain knowledge that graders may not have. Unlike the other criteria (novelty, trajectory, efficiency — all of which can be assessed from the conversation text alone), correctness requires knowing what the *right* answer is. Without a domain-independent proxy test, graders skip this criterion in ambiguous cases or default to "the user seemed confident, so probably correct."

**Proposed fix:**
Add domain-independent proxy signals that work without domain expertise:

> "To assess whether the user is steering in the correct direction without requiring domain expertise, check all three signals:
> 1. Consistency: Is the user's direction consistent with constraints they have previously stated? (A user who said 'no edge functions' in an earlier turn and now proposes an architecture using edge functions is steering incorrectly — this is detectable without domain knowledge.)
> 2. LLM acceptance: Does the LLM implement the direction without flagging contradictions or errors? (LLMs reliably surface obvious contradictions. Implementation without concern is a weak but useful signal.)
> 3. Trajectory resolution: Does the conversation become more resolved after the user's prompt, not more confused or circular?
>
> For graders with domain expertise: verify technical correctness directly.
> For graders without domain expertise: require all three proxy signals before grading above-bar on direction.
>
> Context-specific definitions:
> - Code contexts: correct = closer to a working, idiomatic, well-architected solution fitting the stated constraints
> - Design contexts: correct = consistent with the project's stated goals, constraints, and prior decisions
> - Analysis contexts: correct = toward accurate, evidence-based conclusions, not circular reasoning"

---

## Summary: Top 3 Highest-Priority Fixes

### Priority 1 — Define "insight" with a counterfactual test
**Addresses:** Failure Modes 1, 3, 4
**Why highest priority:** The word "insight" is undefined and appears five times in the rubric. Every grading decision passes through this concept. Adding the counterfactual test ("would the LLM have proposed this without the user's specific input?") eliminates the most common false-positive pattern across all candidates.

**Exact wording to add (after the existing "key insight" criterion):**
> "Insight test: The user's contribution is an insight if and only if it introduces information, constraints, or direction that was not already present (explicitly or implicitly) in any prior LLM turn. To verify, apply the counterfactual: could the LLM have reached this point without the user's specific input? If yes, it is not an insight — grade as near-bar or below-bar. Reorganising, reformatting, or restating LLM content with different words is explicitly not an insight even if the result looks polished."

---

### Priority 2 — Add a decision-query gate
**Addresses:** Failure Mode 2
**Why second priority:** Decision queries are a common, high-quality prompting pattern that systematically passes as above-bar when it should be near-bar. Vidhusan W3 is the clearest false positive in the entire dataset. Without an explicit gate, every technically skilled user who frames good questions will inflate their above-bar count.

**Exact wording to add (new criterion):**
> "Decision queries — asking the LLM to recommend between options — are NOT above-bar unless the user's stated constraints change what the correct recommendation would be. Test: would the LLM have given materially the same recommendation without the user's specific framing? If yes, near-bar. If the user's constraints reverse or substantially narrow the LLM's answer, above-bar."

---

### Priority 3 — Operationalise "correct direction" with domain-independent proxy signals
**Addresses:** Failure Mode 5
**Why third priority:** This is currently being silently skipped by graders in unfamiliar domains, which means technically complex transcripts — the ones that are hardest to evaluate and most likely to contain sophisticated-sounding but wrong steering — are systematically graded more leniently. The proxy-signal approach allows any grader to apply the criterion reliably.

**Exact wording to add (replace the vague "correct direction" phrase):**
> "Correct direction — domain-independent check: Verify (a) the direction is consistent with the user's own prior constraints, (b) the LLM implements without flagging errors or contradictions, and (c) the conversation becomes more resolved, not more circular, after the prompt. Graders without domain expertise must require all three signals. Graders with domain expertise should verify correctness directly."

---

*Agent PR — Cycle 1 — 2026-06-29*
