# WorkPulse Manual Grading Rubric — v3.1

**Core principle:** *The conversation should be user-driven and not LLM-driven.*

Graders should be able to apply this rubric in under 2 minutes per window.

---

## What Is a Window?

A **window** is a focal user turn plus the surrounding context turns. The **focal turn** is the single user prompt being graded. The LLM turns immediately before it are context (what the user was reacting to). The turn(s) immediately after it are trajectory evidence (did the conversation improve?).

---

## Three Tiers

| Label | Meaning |
|---|---|
| `above_bar` | User demonstrably drove the conversation with genuine insight, correct direction, and positive trajectory. Eligible for the portfolio. |
| `near_bar` | Partial strength — passes some criteria but fails one or more. Return specific coaching feedback (see template below). |
| `below_bar` | No meaningful user-driven contribution. Discard silently. |

> **Do not use** "best", "average", or "near-miss" — use the labels above consistently.

---

## What Is "Insight"?

**Insight** = the user contributes content, constraints, or direction that was **not already present** (explicitly or implicitly) in any prior LLM turn in the window.

**Insight IS:**
- A new architectural decision or constraint the LLM had not proposed (e.g., a quarantine-first security design)
- A project-specific principle that overrides a generic LLM recommendation (e.g., "no logs — I want compile-time failures")
- An original concept or idea introduced by the user (not derived from any prior LLM turn)
- An accurate diagnosis of a problem the LLM missed

**Insight is NOT:**
- Restating the LLM's output in different words
- Reorganising or reformatting LLM content into bullets or headers
- Approving, confirming, or echoing ("looks good, continue")
- Asking the LLM to summarise what was discussed

### Counterfactual Test (apply before grading `above_bar`)

> *"Would the LLM have reached the same outcome if the user had said nothing new — e.g., if the user had simply asked 'how should I implement this?' or 'what do you think?'"*

If yes → the insight is LLM-driven → grade `near_bar` or `below_bar` regardless of how polished the user's prompt looks.

---

## Decision-Query Gate

A prompt that asks the LLM to choose between options or recommend an approach is **NOT** `above_bar` unless the user's supplied constraints change what the correct recommendation would be.

**Test:** Would the LLM have given materially the same recommendation without the user's specific constraints?
- If yes → `near_bar` (good framing, but the insight is LLM's)
- If the user's constraints reverse or substantially narrow the answer → may be `above_bar`

A well-structured question using general engineering criteria (performance, simplicity, dependencies) is `near_bar` at best — even if the question is sharp and the LLM's answer is excellent.

> **Note:** This gate applies to prompts that *ask* a question. It does **not** apply to prompts where the user is *issuing* a decision or architectural direction (e.g. "kill dynamic prompts, we're switching to Anthropic"). Decisive user directives are evaluated under the ownership test and strategic-decision proxy instead.

---

## Criteria for `above_bar`

A window must pass **all** of these:

1. **Semantic novelty** — The user contributes new information, constraints, or direction. Reorganising or paraphrasing LLM content — even elegantly — does not count.

2. **Genuine insight from the user (not the LLM)** — Apply the 4-part ownership test:
   - Was the constraint, direction, **OR failure diagnosis** new — not present in any prior LLM output in this conversation?
   - Was the direction change **user-initiated** (not following an LLM suggestion)?
   - Did the LLM **extend or implement** the insight rather than develop it from scratch?
   - If the user's turn were replaced with a generic question, would the LLM still reach the same insight?
   
   The insight is user-owned if it passes at least 3 of 4. If only 2 pass → co-developed → `near_bar`.

3. **Correct direction** — The user steers toward a better outcome, not away from it.

   *Domain-independent proxy signals (use when you lack domain expertise — require all three):*
   - **Consistency:** Is the direction consistent with constraints the user stated earlier in the conversation?
   - **LLM acceptance:** Does the LLM implement the direction without flagging contradictions or errors?
   - **Trajectory resolution:** Does the conversation become more resolved after the prompt — not more circular or confused?

   > **For strategic or architectural decisions (not code/implementation):** replace proxy (a) with — "The LLM's response treats the user's direction as correct and does not suggest alternatives or caveats indicating the user may be wrong." Pure LLM deference to a firm user decision does not satisfy this proxy.
   >
   > **Important — read the LLM response turn:** To apply this proxy you must look at the LLM's response, not just the user prompt. In a JSONL transcript, the LLM response immediately follows the focal user turn and has `"role": "assistant"`. Read that turn to judge whether the LLM genuinely accepted the direction, pushed back, or merely deferred.

   *If you have domain expertise:* verify correctness directly.
   - Code: toward a working, idiomatic, well-architected solution fitting stated constraints
   - Design: consistent with stated project goals, constraints, and prior decisions
   - Analysis: toward accurate, evidence-based conclusions (not circular reasoning)

4. **Positive trajectory** — The conversation measurably improves after the focal turn: more specific, more correct, or better aligned with the user's goal. A long LLM response is not itself evidence of improvement — the *direction* must improve.

5. **Efficiency** — The user does not arrive at the insight only after repeating the same prompt multiple times. If the same correction needed ≥2 prior turns to land, the first attempt is penalised.

6. **User-driven, not LLM-driven** — The user is steering, not rubber-stamping an LLM-suggested plan. If removing the user's turn would not change the LLM's trajectory, the turn has no independent steering value.

   *Apply this test within-conversation only — do not ask whether the LLM "could have known this eventually". Ask: without this specific turn, would this conversation have produced this outcome?*

---

## Automatic Disqualifiers

Fail immediately — do not grade `above_bar`:

- **Echo/paraphrase:** The user prompt is semantically equivalent to what the LLM said in the immediately preceding turn(s).
- **No independent intent:** The user message is an approval, confirmation, generic question, or the user is executing an LLM-suggested action with no new input.
- **No trajectory improvement:** The conversation does not become more specific, correct, or aligned after the focal turn.
- **Insight is LLM's:** Counterfactual test or decision-query gate fires — the LLM would have reached the same outcome unprompted.

---

## Near-Bar Coaching Template

When a window grades `near_bar`, return this structure:

```
Almost above bar — here's what held this back:

Failed: [one of: Novelty / Insight ownership / Correct direction / Trajectory / Efficiency]

What happened: [one sentence describing the specific failure]

To make this above bar: [one concrete, actionable change the user could have made]
```

---

## Quick Reference Checklist

```
[ ] Is the user's contribution new — not already in any prior LLM turn?
[ ] Counterfactual test: LLM could NOT have reached this without the user's specific input?
[ ] Decision-query gate: if asking for a recommendation, do the user's constraints change the answer?
[ ] 4-part ownership test: passes ≥3 of 4?
[ ] Direction consistent + LLM accepts + conversation resolves?
[ ] Positive trajectory after the focal turn?
[ ] Insight reached efficiently (not after ≥2 failed attempts)?
[ ] User is steering — not rubber-stamping?
```

All 8 checks pass → `above_bar`
Partial pass (fails 1–2) → `near_bar` + coaching message
Fails insight/novelty gates → `below_bar`

---

## Calibration Examples

### above_bar example
**Prompt:** "i'd like to store my pdf first in a quarantined s3 directory or bucket first, and then run a background job to get that file, run security scan for malware, parser exploits etc..."
**Verdict:** above_bar
**Why:** The quarantine-first security model and parser exploit threat model were not in any prior LLM output. LLM validates, not originates. Counterfactual: LLM would have proposed simple upload-and-parse. Ownership: 4/4.

### near_bar example
**Prompt:** "Should I use LiteLLM or call the OpenAI API directly for this?"
**Verdict:** near_bar
**Why:** Decision-query gate fires. The comparative analysis is LLM-produced. User contributed the question, not the insight. Ownership: 2/4.
