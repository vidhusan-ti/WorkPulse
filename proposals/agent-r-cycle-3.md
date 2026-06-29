# WorkPulse Rubric Improvement Proposal
### Agent R — Cycle 3
#### Focus: Aligning the Manual Rubric with the SND→IOAS→CTA→EJAD Pipeline

---

## Background

The project owner recently replaced the previous rubric with a new, shorter version. This
proposal analyses that new rubric, identifies its gaps relative to the 4-stage pipeline that
has been built, and proposes concrete wording improvements. Cycle 1 and Cycle 2 proposals
are not repeated here — this document assumes those are known.

---

## 1. The Current Rubric (Annotated)

For reference, the full current rubric text is reproduced below with inline analysis notes:

```
[A] You are a Feedback prompt coach who will help user to improve the quality of their
    prompting by giving feedback on their...
    
    ← MISSING: No completion. Sentence is cut off mid-thought.

[B] The user's conversation with the cursor should be analysed completely and the context
    should be understood, then divide the conversation into specific windows.
    
    ← UNDER-SPECIFIED: No definition of what a "window" is, how large it is, what 
      the focal turn is, or how windows map to pipeline stages.

[C] Then categorise the windows into best conversation and average conversation.
    
    ← INCOMPLETE: Only two tiers named (best / average). "Near-miss" category is
      introduced later but not named here. Tiers don't map to pipeline output labels
      (above_bar / near_bar / below_bar).

[D] The categorization should be made based on the quality of the context and not on the
    user's prompt alone — both the user prompt as well as the system's response should be
    considered.
    
    ← GOOD — aligns with Stage 3 CTA logic. But "quality of context" is vague.
      Needs to say "trajectory effect."

[E] The best conversations are those in which...
    
    ← INCOMPLETE: Sentence fragment. Criteria list follows but this opener is broken.

[F] The conversation should be graded based on the trajectory that follows the user's prompt
    and not on the prompt alone, and it should be visible that the user brought insights,
    direction, quality and outcome.
    
    ← GOOD: Directly maps to CTA. However "quality and outcome" is circular.
      "Direction" is the key word — could be sharpened.

[G] The conversation should be user-driven and not LLM-driven.
    
    ← CORE PRINCIPLE — maps to all 4 stages. Good. But not operationalised here.

[H] The conversation should have genuine insight and content instead of the same redundant
    stuffs.
    
    ← MAPS TO SND (Stage 1). "Redundant stuffs" is informal. Should specify:
      "The user must introduce semantic novelty not already present in prior LLM turns."

[I] The key insight should be from the user and not from the LLM.
    
    ← GOOD — maps to Stage 2 IOAS (intent_clarity) and Stage 4 EJAD criterion 3.

[J] The user should not misdirect the LLM to go in the wrong direction, the steering of
    the LLM should be in the correct direction.
    
    ← MAPS TO IOAS (outcome_precision). But "correct direction" is undefined.
      For code contexts: correct = closer to a working, well-designed solution.
      For design contexts: correct = consistent with stated project constraints.

[K] The conversation should be efficient, not reaching the output by repeating the same
    prompts.
    
    ← MAPS TO EJAD criterion 5 (EFFICIENT). Good. But missing: multi-turn
      correction for the same issue should penalise the *first* attempt, not just
      flag the pattern.

[L] The user's prompt should bring in semantic novelty and not just restate or paraphrase
    what the LLM has already said. The user should contribute new information, constraints,
    insights or directions to the conversation.
    
    ← GOOD — direct SND language. But "paraphrase" isn't enough. User could
      restructure LLM content into bullets with no new content and pass SND.
      Add: "reorganising or reformatting LLM output is not semantic novelty."

[M] There should be strong alignment between the user's intent and the final outcome of the
    conversation. The user should demonstrate clear steering of the discussion and the LLM's
    response should be satisfying.
    
    ← MAPS TO IOAS. "Satisfying" is vague. Should say: "The LLM response should
      serve the user's stated intent precisely."

[N] Even if the prompts are well structured and have good content, if they don't bring any
    insights, discard those prompts.
    
    ← IMPORTANT GATE — reinforces Stage 1 SND. Good. But "insights" needs
      operationalisation (see Gap 3 below).

[O] The prompts which are just rewriting or summarising what the cursor has said, even if
    they are insightful they should not be considered.
    
    ← GOOD — mirrors EJAD criterion 6 (NOT JUST RESTRUCTURING). But applies
      beyond just rewriting — also covers "repeating with added affirmation."

[P] Having an insightful conversation after repeating something multiple times, which could
    be rectified in a single prompt, doesn't account as an insightful prompt.
    
    ← GOOD — maps to EJAD criterion 5 (EFFICIENT). But missing: how to count
      "multiple times." Needs a heuristic: >=2 prior turns on the same issue = penalty.

[Q] A near-miss conversation are those which have partial insight but fails one or more
    criteria for a best conversation. The reason for the failure and the improvement needed
    to make the conversation effective should be returned.
    
    ← GOOD: near_bar definition exists. But no guidance on what the coaching
      message should contain — the rubric doesn't tell the grader what to say.
```

---

## 2. Gap Analysis

### Gap 1 — No Window Definition
The rubric uses the word "windows" without ever defining them. The pipeline operates on
sliding 3-turn windows with a focal user turn. The rubric must specify:
- A window = a slice of consecutive turns containing a focal user prompt
- The focal turn is the single user turn being graded
- Prior LLM turns in the window are context; the following turn(s) are trajectory evidence

Without this, a human reviewer applying the rubric cannot know which turn they are scoring
or what "the conversation" refers to.

### Gap 2 — Three Tiers Not Named Consistently
The rubric introduces "best conversation," "average conversation," and "near-miss" as
separate concepts but doesn't unify them as a three-tier system:
- **above_bar** (pipeline label) = "best conversation" (rubric)
- **near_bar** (pipeline label) = "near-miss" (rubric)
- **below_bar** (pipeline label) = "average conversation" (rubric)

The mismatch between rubric vocabulary and pipeline labels means a grader reading the rubric
can't connect their judgment to what the pipeline outputs.

### Gap 3 — "Insight" Is Not Operationalised
The word "insight" appears 5 times in the rubric without a definition. The pipeline operationalises
it across 3 stages:
- **Stage 1 SND:** novelty_score (cosine distance from prior LLM turns > 0.25)
- **Stage 2 IOAS:** intent_clarity score (user had independent steering intent > 0.5)
- **Stage 4 EJAD:** criterion 2 (GENUINE INSIGHT: real thinking, not surface filler)

The rubric needs a single, concrete working definition of "insight" that anchors all three.

### Gap 4 — No Explicit Failure Modes for Each Stage
Each pipeline stage has a specific failure mode, but the rubric mentions failure modes only
loosely. There is no rubric guidance corresponding to:
- Stage 1 failure: user essentially paraphrased or echoed LLM content
- Stage 2 failure: user's request had no clear independent intent (approval/confirmation)
- Stage 3 failure: conversation trajectory didn't improve after the user prompt
- Stage 4 failure: either judge rejected it OR dissenter found a strong objection

Without per-stage failure modes, a human reviewer applying the rubric won't catch the
edge cases each stage was designed for.

### Gap 5 — No Two-Axis Distinction (Insight Quality vs. Portfolio Readiness)
Vidhusan Window 9 identified an important tension in the rubric:
> "sometimes a prompt can be mindblowing like it will be out of the box but it's not needed to
> satisfy all the 8 gates"

The current rubric applies all criteria equally, which means an exceptional, truly original
prompt can fail on efficiency grounds even though it demonstrates extraordinary insight.
The rubric should distinguish:
- **Insight quality** (intrinsic originality of the user contribution)
- **Portfolio readiness** (does the window check all criteria for inclusion?)

A prompt that scores extremely high on insight quality should have a lower portfolio threshold.

### Gap 6 — "Correct Direction" Is Undefined
The rubric says "the steering of the LLM should be in the correct direction" (criterion J)
without specifying what "correct" means. This is load-bearing — IOAS Stage 2 scores on
`outcome_precision`, which requires knowing what correct looks like. The rubric needs to say:
- In code contexts: correct = closer to a working, idiomatic, well-architected solution
- In design contexts: correct = consistent with stated project constraints and goals
- In analysis contexts: correct = toward accurate, evidence-based conclusions

### Gap 7 — Near-Bar Coaching Template Is Missing
The rubric says near-miss windows should return "the reason for the failure and the
improvement needed," but gives no template or structure for that feedback. The popup UI
shows this coaching message directly to the user. Without structure, graders produce
inconsistent, uninformative messages.

---

## 3. Proposed Improvements (Specific Wording)

### Improvement 1 — Add Window Definition (Gap 1)

**Insert after the opening sentence:**

> A **window** is a focused slice of the conversation: a sequence of turns centred on a
> single focal user prompt. The focal prompt is the one being graded. Prior LLM turns in
> the window provide context (what the user was reacting to). The turn(s) immediately
> following the focal prompt are the trajectory evidence (did the conversation improve?).

---

### Improvement 2 — Unify Tier Vocabulary (Gap 2)

**Replace the scattered tier references with a single definitions block:**

> **Three tiers apply to every graded window:**
> 
> - **Above bar** ("best"): The user demonstrably drove the conversation with genuine insight,
>   correct direction, and measurable positive trajectory. Eligible for the portfolio.
> - **Near bar** ("near-miss"): The window has partial strength — passes some criteria but
>   fails one or more. Return specific coaching feedback.
> - **Below bar** ("average"): No meaningful user-driven contribution. Discard silently.

---

### Improvement 3 — Define "Insight" (Gap 3)

**Replace all unqualified uses of "insight" with this anchored definition:**

> **Insight** = the user contributes content, constraints, or direction that was not already
> present (explicitly or implicitly) in any prior LLM turn in the window. Insight can be:
> - A new architectural decision or design constraint (e.g., Abdul Window 1: quarantine-first
>   security architecture unprompted by the LLM)
> - A project-specific principle that overrides the LLM's generic recommendation (e.g.,
>   Arleif Window 3: "no logs — I want compile-time failures")
> - An original product concept introduced by the user (e.g., Vidhusan Window 1: adversarial
>   roleplay module placed in the middle of the course, not the end)
> - An accurate diagnosis of a problem the LLM missed (e.g., Vidhusan Window 8: ruling out
>   deploy causation from the 6-hour gap)
>
> **Insight is NOT:**
> - Restating the LLM's output in different words
> - Reorganising or formatting the LLM's content into bullets/headers
> - Approving, confirming, or echoing ("looks good, continue")
> - Asking the LLM to "summarise what we've discussed"

---

### Improvement 4 — Add Per-Stage Failure Modes (Gap 4)

**Add a "What disqualifies a window?" section:**

> **Automatic disqualifiers (fail immediately):**
>
> 1. **Echo/Paraphrase (Stage 1):** The user prompt is semantically equivalent to what the
>    LLM said in the immediately preceding turn(s). High cosine similarity to prior LLM
>    turns = not above bar.
>
> 2. **No independent intent (Stage 2):** The user's message has no discernible steering
>    goal — it is an approval, confirmation, generic question, or LLM-suggested action the
>    user is just rubber-stamping. If removing the user turn would not change the LLM's
>    trajectory, it has no independent intent.
>
> 3. **No trajectory improvement (Stage 3):** After the focal user prompt, the conversation
>    does not become more specific, more correct, or better aligned. A long LLM response does
>    not automatically indicate a trajectory improvement — what matters is whether the
>    *direction* improved.
>
> 4. **Failed final validation (Stage 4):** Two independent judges disagree, or an
>    adversarial review finds a specific, credible reason the prompt is not user-driven
>    (e.g., the user was following an LLM-suggested plan, not steering one).

---

### Improvement 5 — Two-Axis Exception for Exceptional Insight (Gap 5)

**Add after the disqualifiers section:**

> **Exceptional insight exception:**
> A window may qualify as above bar on insight quality alone, even if the efficiency
> criterion is not fully met, if:
> - The user's contribution introduces a genuinely novel concept that was not suggested
>   by the LLM in any form, AND
> - The insight causes a "strong" trajectory improvement (Stage 3), AND
> - Both independent judges agree it is above bar.
>
> In this case, note in the portfolio entry that the prompt qualifies on insight quality
> and flag the efficiency weakness as a coaching note alongside the above-bar verdict.

---

### Improvement 6 — Operationalise "Correct Direction" (Gap 6)

**Replace criterion J's vague phrasing with:**

> The user's steering must move the conversation toward a **correct outcome for the context**:
> - In **code contexts**: toward a working, idiomatic, well-architected solution that fits
>   the stated constraints (language, dependencies, security model)
> - In **design contexts**: consistent with the project's stated goals, constraints, and
>   prior decisions
> - In **analysis/research contexts**: toward evidence-based, accurate conclusions — not
>   circular reasoning or unsupported assumptions
>
> Prompts that introduce confident but incorrect architectural decisions, or that redirect
> the LLM away from the right answer with false premises, are NOT above bar even if they
> score high on novelty.

---

### Improvement 7 — Near-Bar Coaching Template (Gap 7)

**Add a structured coaching template for near-bar windows:**

> **Near-bar coaching message format:**
>
>     Almost above bar — here's what held this back:
>     
>     Failed: [one of: Novelty / Intent clarity / Trajectory / Validation]
>     
>     What happened: [one sentence describing the specific failure]
>     
>     To make this above bar: [one concrete, actionable change the user could have made]

---

## 4. Alignment with Pipeline Stages

| Rubric Criterion | Pipeline Stage | Current Rubric Clarity | Proposed Fix |
|---|---|---|---|
| Semantic novelty — user brings new content | Stage 1 SND | Partial (criterion L good, H vague) | Improvement 3 (insight definition) + Improvement 4 (Stage 1 disqualifier) |
| Independent steering intent | Stage 2 IOAS | Poor ("key insight from user" is vague) | Improvement 3 (intent examples) + Improvement 4 (Stage 2 disqualifier) |
| Trajectory improvement after focal prompt | Stage 3 CTA | Partial (criteria F/D good) | Improvement 4 (Stage 3 disqualifier) + Improvement 1 (window definition with trajectory evidence) |
| Final validation — both judges + dissenter | Stage 4 EJAD | Not mentioned in rubric at all | Improvement 4 (Stage 4 disqualifier) |
| Three-tier output (above/near/below) | All stages | Fragmented — three names, no definitions | Improvement 2 (unified tier block) |
| Near-bar coaching output | Stage 4 EJAD output | Mentioned but no structure | Improvement 7 (coaching template) |
| Exceptional insight override | Stage 4 EJAD | Not mentioned | Improvement 5 (two-axis exception) |

---

## 5. Examples from Candidate Results

These above-bar windows illustrate why the proposed improvements matter:

### Why "insight" needs a definition (Improvement 3)

**Abdul Window 1** (quarantine S3 bucket architecture): The user introduced a threat-model-driven
security design the LLM had not proposed. Under the current rubric, "insight" is undefined —
a grader might reject this as "just a technical requirement" rather than recognising it as a
user-originated architectural decision.

**Arleif Window 3** ("I want compile-time failures or worst the operation to fail"):
The user applied a project philosophy as a hard constraint. This is insight by the proposed
definition (new constraint not in any prior LLM turn). Without the definition, a grader might
score this low because the user turn is short.

### Why "correct direction" needs operationalisation (Improvement 6)

**Vidhusan Window 2** (contradicting the buy-Sirion recommendation): The user supplied
real constraints (self-build with Cursor/Claude, 40 users, cost model) that changed the
correct answer. An operationalised "correct direction" criterion recognises this as above bar
because the user moved the conversation toward a more accurate recommendation. A vague rubric
might penalise this for contradicting the LLM.

### Why the two-axis exception matters (Improvement 5)

**Vidhusan Window 9** ("sometimes a prompt can be mindblowing but doesn't satisfy all the gates"):
This very window is the user identifying the tension. Bharath Window 4 (full chaos-target
design spec with 4 distinct failure classes) is an example of a prompt that could fail the
"efficiency" criterion (it is very long and detailed) but is clearly above bar on insight
quality. The exception rule preserves these correctly.

### Why near-bar coaching needs structure (Improvement 7)

**Vidhusan Window 5** (multi-turn frustration: "if you are still evaluating single messages
then you can stop involving me in this project") represents a near-miss pattern: the user
had a valid architectural insight but expressed it through emotional escalation and repetition.
The current rubric says return "the reason for the failure and the improvement needed" but
gives no template. A structured coaching message here would say:
*"Failed: Efficiency. What happened: the valid architectural insight (whole-conversation as
focal unit) required multiple frustrated escalations to land. To make this above bar: state
the principle and the constraint in a single turn early."*

### Why window definition matters (Improvement 1)

**Arleif Window 4** (PR meta-reasoning: "look at this PR, it is terrible — was it the DoD,
or the prompts?"): This only reads as above-bar if you know the focal turn is the user's
meta-question, and that the prior LLM turns were a review of the PR. Without a window
definition, a human grader might treat the LLM's PR feedback as the focal content and
downgrade the user turn as "just a follow-up question."

---

## 6. Summary — Prioritised Changes

| Priority | Improvement | Effort | Impact |
|---|---|---|---|
| P1 | Improvement 2: Unify tier vocabulary | Trivial | Eliminates ambiguity for all graders |
| P1 | Improvement 3: Define "insight" with examples | Low | Reduces false positives/negatives most |
| P1 | Improvement 4: Per-stage failure modes | Low | Connects rubric to pipeline logic |
| P2 | Improvement 1: Window definition | Trivial | Required for consistent human evaluation |
| P2 | Improvement 6: Operationalise "correct direction" | Low | Prevents incorrect accepts |
| P2 | Improvement 7: Near-bar coaching template | Low | Consistency for user-facing feedback |
| P3 | Improvement 5: Two-axis exception | Medium | Handles exceptional outliers correctly |

---

## 7. What NOT to Change

The current rubric's core principle is sound and should be preserved verbatim:
> *"The conversation should be user-driven and not LLM-driven."*

This single sentence is the north star that all 4 pipeline stages operationalise. Every
improvement in this proposal is an elaboration of this principle — not a revision to it.

---

*Agent R — Cycle 3 — 2026-06-29*
