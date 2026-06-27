# WorkPulse Rubric Improvement: Solution Proposals
### Agent R — Cycle 1
#### Problem: How should WorkPulse identify above-bar prompts in Cursor conversations?

---

## Solution 1: Multi-Dimensional Rubric Scoring (MDRS)

### Core Idea
Replace the single "user-driven vs LLM-driven" binary with a weighted, multi-dimensional scoring matrix. Each prompt is evaluated across 5–7 independent dimensions, each scored 0–3, and the aggregate determines tier placement. Above-bar requires a minimum composite score *and* a minimum on the "insight" dimension specifically.

### How It Works
- **Dimensions:** (1) Originality/Novelty, (2) Specificity/Precision, (3) Correction/Pushback presence, (4) Outcome relevance, (5) Efficiency (signal-to-noise), (6) Contextual grounding, (7) Problem decomposition quality
- Each dimension scored 0–3 by an LLM judge with explicit rubric anchors
- Above-bar: composite ≥ 14/21 AND insight (dim 1+3 combined) ≥ 4
- Near-bar: composite 9–13 OR composite ≥ 14 but insight < 4
- Below-bar: composite < 9

### Strengths
1. Granularity reduces false positives — can't coast on one dimension
2. Debuggable decisions — scorecard shows exactly which dimension failed
3. Tunable without restructuring — weights adjustable per domain
4. Partial credit model — acknowledges prompting quality is continuous

### Weaknesses
1. LLM scoring drift — halo effects may pollute dimension independence
2. Rubric anchor maintenance — exemplars go stale as codebases evolve
3. Score gaming — users may optimize for surface signals
4. Computational cost — 7-dimension evaluation multiplies inference cost

### Implementation Complexity
**Medium.** Requires designing rubric anchors, structured output parser, and aggregation logic. Needs careful human calibration upfront.

### Rubric Impact
Operationalizes "genuine insight / user-originated" into measurable sub-signals. Replaces subjective holistic judgment with explicit, traceable criteria.

### Risk
Medium. Dimension independence may not hold. Risk of over-engineering.

### Verdict
**Recommended (Conditional on anchor calibration).** Best upgrade path from v1.0. Pilot with 4 dimensions first, expand later.

---

## Solution 2: Conversation Trajectory Analysis (CTA)

### Core Idea
Grade prompts not in isolation but by their *effect on conversation trajectory*. An above-bar prompt is one that causes a measurable, user-intended shift in LLM behavior — a redirect, deepening, or correction.

### How It Works
- Ingest sliding window: turns T-1, T (candidate), T+1, T+2
- LLM judge asks: "Did the conversation become more specific, correct, or better aligned after prompt T? Did the LLM change course?"
- Score: Positive Shift / Neutral / Negative Drift
- Above-bar: Positive Shift AND prompt T had non-trivial user content
- Near-bar: Positive Shift but thin prompt; or rich prompt but neutral shift
- Below-bar: Neutral or Negative trajectory

### Strengths
1. Outcome-grounded — avoids brilliant-sounding prompts that led nowhere
2. Captures correction naturally — no explicit correction detection needed
3. Resistant to gaming — can't fake a trajectory shift
4. Aligns with user value — grades on whether prompts actually worked

### Weaknesses
1. Latency — can't grade T until T+2 exists; async pipeline required
2. Attribution ambiguity — was improvement from T or accumulated context?
3. Asymmetric grading — final-turn prompts penalized (no T+1, T+2)
4. LLM grading LLM behavior — spurious shifts from temperature, not user quality

### Implementation Complexity
**Medium-High.** Requires windowed conversation store, async pipeline, attribution logic.

### Rubric Impact
Shifts from "what did user say?" to "what did user achieve?" — meaningful philosophical upgrade.

### Risk
High latency risk. Attribution errors create noisy signal.

### Verdict
**Conditional.** Excellent as supplementary signal. Pair with Solution 1 or 5 for hybrid system.

---

## Solution 3: Contrastive Baseline Benchmarking (CBB)

### Core Idea
Grade prompts by comparing to a generated "median user baseline" for the same task context. Above-bar requires surpassing the baseline by a calibrated margin.

### How It Works
- Generate 3–5 synthetic "median user" prompts for same apparent task
- LLM judge ranks actual prompt vs synthetic baselines
- Above-bar: ranked #1 AND judge articulates specific differentiating quality
- Near-bar: ranked #1–2 but no clear differentiation
- Below-bar: ranked #3+ or indistinguishable from median

### Strengths
1. Contextual calibration — bar adapts to task type
2. Self-improving — median cluster improves as corpus grows
3. Explainable — "above baseline because X, unlike baseline Y"
4. Avoids rubric inflation — bar rises naturally as users improve

### Weaknesses
1. Baseline generation quality — synthetic prompts may not reflect real users
2. Computationally expensive — 3–5 extra generations + ranking per eval
3. Goodhart's Law risk — users imitate baseline with slight modifications
4. Cold start — no historical data means purely synthetic baseline

### Implementation Complexity
**High.** Requires baseline generation pipeline, historical data clustering, ranking judge, ongoing calibration.

### Rubric Impact
Reframes above-bar as relative standard. More robust to domain shifts but harder to explain.

### Risk
High. Baseline quality is load-bearing and hard to validate continuously.

### Verdict
**Conditional.** Valuable as rubric calibration/audit tool. Not recommended as primary live grading mechanism.

---

## Solution 4: LLM Ensemble Judge with Adversarial Dissenter (EJAD)

### Core Idea
3-model ensemble where two models evaluate normally and one is explicitly prompted to argue *against* above-bar. A prompt achieves above-bar only if it survives adversarial scrutiny.

### How It Works
- **Judge A:** Standard evaluation
- **Judge B:** Standard evaluation, different framing
- **Judge C (Dissenter):** Explicitly hunts for why prompt should NOT be above-bar
- Above-bar: A=above AND B=above AND Dissenter's strongest objection rated "weak"
- Dissenter objection always logged as structured feedback

### Strengths
1. Dramatically reduces false positives — dissenter specifically hunts failure modes
2. Structured uncertainty — disagreement creates rich near-bar feedback
3. Model diversity — cross-model agreement is strong quality signal
4. Captures edge cases — LLM-following behavior caught by adversarial judge

### Weaknesses
1. 3x inference cost
2. Dissenter can over-object — may flag genuinely excellent prompts
3. Ensemble disagreement resolution can become complex and arbitrary
4. Model correlation risk — same model with different prompts offers weak independence

### Implementation Complexity
**High.** Requires 3-call orchestration, meta-judge or voting logic, dissenter prompt engineering.

### Rubric Impact
Strongest false-positive reduction of any approach. Trades recall for precision.

### Risk
High inference cost. Dissenter calibration is critical and tricky.

### Verdict
**Conditional.** Excellent for high-stakes portfolio approval decisions. Too expensive for every window in a live monitor. Use selectively on above-bar candidates.

---

## Solution 5: Hierarchical Gate System (HGS)

### Core Idea
Replace the scoring model with a strict sequence of binary pass/fail gates. A prompt must pass ALL gates in order to be above-bar. Fail any gate → immediate tier downgrade with that gate as the coaching reason.

### How It Works
- **Gate 1 — Minimum Content:** Does the prompt contain more than task delegation? (Filters "just do X" prompts)
- **Gate 2 — User Originality:** Did the user introduce an idea, constraint, or reframe not present in prior LLM output?
- **Gate 3 — Correct Direction:** Is the user pushing toward the right goal (not misdirecting)?
- **Gate 4 — Efficiency:** Was this achievable in fewer prompts? (Penalizes repeated corrections)
- **Gate 5 — Insight Quality:** Does the move qualify as non-obvious, context-specific judgment?
- Pass all 5 → above-bar. Fail Gate 1–4 → below-bar. Pass 1–4, fail 5 → near-bar.

### Strengths
1. Explainability — users know exactly which gate they failed
2. Predictable — no scoring drift, gates are deterministic in intent
3. Fast to implement — 5 binary judgments cheaper than 7 scored dimensions
4. Easy to extend — add gates without restructuring entire system

### Weaknesses
1. Gate ordering matters enormously — a strict sequence may disqualify prompts that fail an early low-importance gate but excel on insight
2. Binary gates lose nuance — a prompt 90% of the way through Gate 5 gets the same result as one that failed completely
3. LLM binary judgment is unreliable — asking an LLM for a strict yes/no on subtle criteria produces inconsistent results
4. Gaming is straightforward — once gate criteria are known, users can craft prompts that pass each gate mechanically

### Implementation Complexity
**Low-Medium.** Simpler than scoring matrix. Requires careful gate prompt design and ordering validation.

### Rubric Impact
Makes the current v1.0 criteria explicit and sequential. Direct translation of existing above-bar criteria into operational gates.

### Risk
Low implementation risk, medium calibration risk. Gate ordering can create unexpected edge cases.

### Verdict
**Recommended.** Best starting point for v1.1 rubric. Clean, explainable, extensible. Pair with trajectory signal for stronger accuracy.

---

## Solution 6: Semantic Novelty Detection (SND)

### Core Idea
Grade prompts by measuring semantic distance between the user's contribution and the prior LLM output. Above-bar prompts must introduce semantically novel content — ideas, constraints, or framings not already present in the conversation.

### How It Works
- Embed the user's prompt and the prior 2 LLM turns
- Compute cosine similarity between user prompt embedding and LLM output embeddings
- Low similarity (high novelty) → user introduced something genuinely new
- High similarity → user is echoing, restating, or approving LLM content
- Combine novelty score with a quality floor (prompt must also be coherent and task-relevant)
- Thresholds calibrated from labeled dataset

### Strengths
1. Fast and cheap — embedding + cosine similarity is computationally trivial vs LLM judge
2. Objective — not subject to LLM judge drift or prompt sensitivity
3. Scales to real-time — can run on every prompt with negligible latency
4. Catches restating patterns reliably — the most common false positive in current rubric

### Weaknesses
1. Novelty ≠ quality — a user can introduce semantically novel but wrong or irrelevant content; high novelty score would still grade it above-bar
2. Embedding models miss semantic equivalence — paraphrases of LLM output may have low similarity despite being functionally identical
3. Domain-specific embeddings required — generic embeddings poorly represent code-specific concepts and Cursor-specific workflows
4. No insight quality signal — can detect that something new was introduced but not whether it's good

### Implementation Complexity
**Low.** Embedding pipeline is straightforward. Threshold calibration requires labeled data.

### Rubric Impact
Excellent at catching the "user restating LLM output" false positive. Weak at identifying genuine above-bar quality. Best as a fast pre-filter.

### Risk
Low technical risk. High false-negative risk for paraphrased LLM content. Misses quality entirely.

### Verdict
**Conditional.** Excellent as a fast first-pass filter to eliminate obvious below-bar prompts cheaply before expensive LLM evaluation. Not a standalone grader.

---

## Solution 7: Human-Calibrated Spot Check Loop (HCSL)

### Core Idea
The rubric is never fully automated. Instead, a small percentage of LLM-graded prompts are routed to human review on a rolling basis. Human decisions correct the LLM grader and continuously retrain its calibration.

### How It Works
- LLM grader runs on all prompts as normal
- 5–10% of above-bar and near-bar decisions are flagged for human spot-check (sampled, not random — prioritize boundary cases)
- Human reviewer confirms, corrects, or escalates
- Corrections feed back into a calibration dataset
- Monthly rubric review meeting uses accumulated corrections to update rubric language and LLM judge prompt
- Over time, LLM grader improves; spot-check rate can decrease

### Strengths
1. Ground truth — human judgment is the ultimate calibration source; no automated system can match it for edge cases
2. Drift detection — human spot checks catch rubric drift before it compounds
3. Trust building — users trust a system where they know humans are involved in calibration
4. Rubric evolution — corrections naturally surface which criteria need clarification

### Weaknesses
1. Requires human time — not fully autonomous; needs ongoing reviewer commitment
2. Doesn't scale without tooling — without a proper review interface, spot-checking becomes burdensome
3. Reviewer bias — a single reviewer introduces their own biases; need reviewer calibration too
4. Latency in corrections — rubric improvements happen on monthly cycle, not continuously

### Implementation Complexity
**Medium.** Requires building a spot-check queue, review interface (even a simple one), and calibration data pipeline.

### Rubric Impact
Meta-improvement rather than direct rubric change. Ensures all other solutions stay calibrated over time.

### Risk
Low. The main risk is reviewer fatigue causing spot-check quality to degrade.

### Verdict
**Recommended.** Not a standalone solution but a mandatory component of any production rubric system. Every other solution here is better with this layer on top.

---

## Solution 8: Intent-Outcome Alignment Scoring (IOAS)

### Core Idea
Grade prompts by evaluating the alignment between the user's *apparent intent* and the *actual outcome* of the LLM's response. Above-bar prompts are those where the user articulated a clear intent and the LLM's response precisely served that intent — evidence that the user was steering, not following.

### How It Works
- Extract user intent from prompt: "What is this user trying to achieve?"
- Evaluate LLM response: "Did the response directly serve that intent?"
- Compute intent-outcome alignment: High / Partial / Misaligned
- Evaluate whether intent was user-originated or LLM-suggested
- Above-bar: High alignment + user-originated intent + intent is non-trivial
- Near-bar: High alignment but intent was LLM-suggested, OR partial alignment with user-originated intent
- Below-bar: Misaligned, or trivial intent

### Strengths
1. Captures goal-directedness — a key quality of above-bar prompting that other methods miss
2. Rewards precision — prompts that are vague produce partial alignment even if the LLM does something useful
3. Detects misdirection — if the user's intent is wrong (misdiagnosed problem), alignment is high but intent quality catches it
4. Natural near-bar signal — partial alignment produces specific coaching: "your intent was right but the prompt didn't communicate X"

### Weaknesses
1. Intent extraction is lossy — LLM-inferred intent from a short prompt may not reflect true user goals
2. Outcome evaluation requires LLM judge on both input and output — doubles evaluation surface area
3. Intent can be trivial and still align perfectly — "make this function longer" has perfect alignment but is clearly below-bar
4. Confounds prompt quality with LLM capability — a great prompt may produce misaligned output because the LLM failed, not the user

### Implementation Complexity
**Medium.** Two-stage LLM evaluation (intent extraction + alignment scoring). Requires intent quality filter to avoid trivial intent trap.

### Rubric Impact
Adds goal-directedness signal currently missing from v1.0. Enriches near-bar feedback with specific intent-gap coaching.

### Risk
Medium. Intent extraction quality is variable. Confounding with LLM failure modes needs careful handling.

### Verdict
**Conditional.** Good supplementary signal, especially for near-bar coaching quality. Not sufficient as standalone.

---

## Solution 9: Behavioral Pattern Library Matching (BPLM)

### Core Idea
Build a library of named above-bar and below-bar behavioral patterns. Grade prompts by matching them to the closest pattern(s). Above-bar patterns are explicitly defined, curated, and versioned. The rubric becomes a pattern taxonomy, not a scoring function.

### How It Works
- Define above-bar patterns: "Correction after LLM error", "Constraint injection", "Problem reframe", "Scope narrowing", "Evidence demand", "Assumption challenge", "Direction recovery"
- Define below-bar anti-patterns: "Task delegation", "LLM approval", "Restatement", "Prompt padding", "Ambiguous request"
- LLM judge matches prompt to nearest pattern(s) from library
- Above-bar: matches ≥1 above-bar pattern AND no disqualifying anti-pattern
- Near-bar: partially matches above-bar pattern OR matches anti-pattern that blocks full credit
- Below-bar: only anti-patterns or no match

### Strengths
1. Highly explainable — "your prompt matched the 'LLM approval' anti-pattern" is concrete and actionable
2. Easy to extend — new patterns added without restructuring; library grows incrementally
3. Encodes institutional knowledge — patterns capture what experienced prompt engineers know about quality
4. Consistent — same pattern produces same grade regardless of topic domain

### Weaknesses
1. Library completeness — uncatalogued patterns get misclassified; novel above-bar behavior may not match any defined pattern
2. Pattern ambiguity — prompts often match multiple patterns simultaneously; resolution logic needed
3. Maintenance burden — patterns need regular review as prompting norms evolve
4. LLM pattern matching is imprecise — fuzzy matching to named patterns introduces its own inconsistency

### Implementation Complexity
**Medium.** Pattern library design requires significant domain expertise upfront. Matching logic is straightforward. Ongoing library maintenance is the main cost.

### Rubric Impact
Makes the rubric a living, curated taxonomy rather than a static scoring function. Most interpretable system for users and reviewers.

### Risk
Medium. Library incompleteness is the primary failure mode. Requires active curation team.

### Verdict
**Recommended.** Excellent for user-facing feedback quality. Best combined with a scoring system (Solution 1) to handle unmatched cases.

---

## Solution 10: Adaptive Threshold Personalization (ATP)

### Core Idea
Instead of a universal above-bar threshold, calibrate thresholds per user based on their historical prompting baseline. What counts as above-bar for a beginner differs from what counts for an experienced engineer. The rubric adapts to the individual.

### How It Works
- Track each user's prompt quality distribution over rolling 30-day window
- Compute user's personal baseline: median score, 75th percentile, 90th percentile
- Above-bar threshold = user's 85th percentile (top 15% of their own output)
- Near-bar = 65th–85th percentile
- Below-bar = below 65th percentile
- Absolute floor: even at above-bar threshold, minimum quality requirements must be met (prevents drift to the mean)
- New users use population-level thresholds until 50 prompts are graded

### Strengths
1. Motivationally sound — users are measured against their own growth, not an external standard
2. Anti-plateau — as users improve, the bar rises; they can't coast on old above-bar habits
3. Reduces beginner frustration — new users aren't immediately compared to expert-level criteria
4. Captures relative improvement — a below-average user who dramatically improves gets recognized

### Weaknesses
1. Portfolio incomparability — above-bar for user A may be below-bar for user B; portfolio entries aren't comparable across users
2. Ceiling problem — expert users may find it harder to hit above-bar than beginners, creating perverse incentives
3. Gaming via sandbagging — users could deliberately submit low-quality prompts to lower their baseline, making it easier to hit above-bar later
4. Cold start — 50-prompt threshold means weeks of population-level grading before personalization kicks in

### Implementation Complexity
**Medium-High.** Requires per-user historical data store, rolling window computation, and dual threshold system (personal + absolute floor).

### Rubric Impact
Reframes above-bar from absolute quality to relative personal achievement. Fundamentally changes what the portfolio means.

### Risk
Medium. Sandbagging risk. Portfolio comparability problem may matter if WorkPulse ever supports team/cohort views.

### Verdict
**Conditional.** Excellent for individual coaching and motivation. Problematic if WorkPulse needs to compare users (hiring, team calibration). Decide which use case is primary first.

---

## Solution 11: Retrieval-Augmented Grade Calibration (RAGC)

### Core Idea
At grading time, retrieve the 3–5 most similar previously-graded prompts from a vector database. The LLM judge sees these examples alongside the current prompt. Grade decisions are anchored to real historical examples, not abstract criteria.

### How It Works
- Maintain a vector DB of all graded prompts with their grades and reasoning
- At evaluation time: embed candidate prompt, retrieve top-k similar graded examples
- Inject retrieved examples into judge prompt: "Here are similar past prompts and how they were graded: [examples]. Now grade this prompt consistently."
- Above-bar: judge rates above-bar AND retrieved examples confirm it's at least as strong as the weakest retrieved above-bar example
- Disagreement between judge and retrieved examples triggers near-bar + human review flag

### Strengths
1. Consistency — grades anchor to real decisions, not abstract criteria; calibration drifts less over time
2. Few-shot improvement — similar examples dramatically improve LLM judge accuracy on edge cases
3. Institutional memory — good and bad grading decisions are preserved and influence future grades
4. Automatic calibration improvement — as corpus grows, retrieval quality improves, judge improves

### Weaknesses
1. Vector DB infrastructure required — adds operational complexity
2. Retrieval quality bottleneck — if similar prompts aren't in the DB, retrieval adds noise not signal
3. Historical bias — if early grades were miscalibrated, retrieval propagates those errors
4. Privacy concerns — storing all graded prompts raises data retention questions

### Implementation Complexity
**High.** Requires vector DB (Pinecone, Chroma, Weaviate, or local), embedding pipeline, retrieval logic, and judge prompt redesign. Significant infrastructure.

### Rubric Impact
Makes grading self-improving and historically consistent. The rubric becomes a living calibration document backed by real examples.

### Risk
Medium-High. Infrastructure complexity. Historical miscalibration propagation risk.

### Verdict
**Recommended (Long-term).** The best investment for a production rubric at scale. Implement after Solutions 1 or 5 are stable. Phase 2 or Phase 3 priority.

---

## Summary Comparison

| # | Solution | Complexity | Rubric Accuracy | False Positive Risk | Verdict |
|---|----------|------------|-----------------|--------------------:|---------|
| 1 | Multi-Dimensional Rubric Scoring | Medium | High | Low-Medium | ✅ Recommended |
| 2 | Conversation Trajectory Analysis | Medium-High | High | Low | ⚡ Conditional |
| 3 | Contrastive Baseline Benchmarking | High | Medium | Medium | ⚡ Conditional |
| 4 | Ensemble Judge + Adversarial Dissenter | High | Very High | Very Low | ⚡ Conditional (high-stakes) |
| 5 | Hierarchical Gate System | Low-Medium | Medium-High | Medium | ✅ Recommended |
| 6 | Semantic Novelty Detection | Low | Low-Medium | High | ⚡ Pre-filter only |
| 7 | Human-Calibrated Spot Check Loop | Medium | Very High | Very Low | ✅ Mandatory layer |
| 8 | Intent-Outcome Alignment Scoring | Medium | Medium | Medium | ⚡ Conditional |
| 9 | Behavioral Pattern Library Matching | Medium | High | Low | ✅ Recommended |
| 10 | Adaptive Threshold Personalization | Medium-High | Medium | Low | ⚡ Conditional |
| 11 | Retrieval-Augmented Grade Calibration | High | Very High | Very Low | ✅ Long-term |

---

*Generated by Agent R — Cycle 1 | 2026-06-27*
