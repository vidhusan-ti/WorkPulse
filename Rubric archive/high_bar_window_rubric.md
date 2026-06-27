# High-Bar Portfolio Window Rubric (Trilogy Innovations)

`rubric_version: 2.7`

Purpose: identify rare moments in AI-assisted work where the user made a real, non-obvious judgment move that brought unusually strong work out of AI. Grade the user's judgment, not the assistant's polish. The default verdict is `below_bar`.

This rubric answers two separate questions:

- `insight_quality` - how rare, original, and context-specific the user's move is.
- `portfolio_ready` - whether the transcript evidence is complete enough to save or publish as a portfolio case.

## High-Bar Standard

A portfolio-ready window must show that the person used AI as leverage for judgment, not just as a writer or executor.

The user should have made AI produce a materially better artifact, decision, workflow, or understanding than a generic user prompt would have produced. Look for:

- a sharper problem frame, success standard, or decision boundary;
- a specific rejection of a plausible but wrong assistant path;
- evidence, constraints, or domain context that changed the answer;
- a durable improvement to the artifact, process, architecture, rubric, test, or workflow;
- a move that a senior reviewer would recognize as human judgment, not prompt polish.

Do not treat fluent wording, long context, or a detailed task brief as high bar unless it contains a user-owned insight that changes what the AI does.

## Grading Unit

Grade a `window`, not the whole conversation and not a single isolated prompt.

- Read the full conversation for context.
- Return and label only the smallest contiguous window that contains one high-judgment episode.
- A typical window is 2 to 6 turns: setup, user move, and assistant response or outcome.
- A conversation can contain multiple qualifying windows. Grade each separately.
- Do not widen a window to inflate the score. Extra turns only count if they add judgment evidence.

If the full conversation is unavailable, set `mentor_review_needed = true`. Do not assign a portfolio-ready label unless the window itself proves both originality and impact.

## Labels

- `mindblowing_portfolio` - rare, first-principles, context-specific human judgment with complete portfolio evidence.
- `outstanding_portfolio` - very strong user-owned judgment with complete portfolio evidence, but less surprising than mindblowing.
- `mindblowing_highlight` - rare human judgment, but missing context, impact, or evidence needed for portfolio use.
- `strong_highlight` - useful, specific, user-owned judgment, but not rare or complete enough for portfolio use.
- `below_bar` - routine, generic, assistant-led, weakly evidenced, or no meaningful user-owned move.

Legacy alias: treat `above_bar` as portfolio eligible only when it clearly maps to `mindblowing_portfolio` or `outstanding_portfolio`.

## Evaluation Procedure

Use a hybrid judge procedure: first reason like a mentor about the best user-owned move, then map that judgment onto auditable gates and scores.

1. Read the whole conversation.
2. Find candidate windows using a short sliding scan.
3. Trim each candidate to the smallest self-contained window.
4. Holistically identify the strongest possible user-owned judgment move before scoring.
5. Run the attribution test: verify whether the user, not the assistant, introduced the key move.
6. Run the generic-LLM counterfactual: ask whether a generic LLM could plausibly generate the same key move from the same context without the user's added judgment.
7. Run the upstream-causality and recurrence audit: check whether the user caused the bad result earlier, or keeps repeating the same correction without improving the workflow.
8. Run the portfolio false-positive guards: reject windows that look impressive but do not prove user-owned judgment or durable impact.
9. Run the gates, score the dimensions, then assign one label.
10. Return a diagnosis specific to the window, including the reasoning audit that supports the label.

Do not mechanically award labels from gate keywords. The gates are an audit layer over the judge's reasoning, not a substitute for judgment.

## Hybrid Reasoning Audit

Before assigning a label, produce these audit judgments:

- `key_user_move` - the strongest candidate human judgment move, quoted or closely paraphrased from the user's words.
- `generic_llm_counterfactual` - what a generic LLM would likely have done from the same context without the user's move, and whether the user's move goes beyond that.
- `attribution_basis` - why the key move belongs to the user, the assistant, both, or neither.
- `decision_rationale` - the short reason the final label follows from the holistic move plus the gates.

If the key move cannot be attributed to the user, the window is not portfolio-ready. If the counterfactual is uncertain, set `mentor_review_needed = true`.

## Upstream Causality And Recurrence Audit

Do not automatically reward a user for fixing a problem if the transcript shows they created or repeatedly tolerated the conditions that caused it.

Before giving credit for `steering_recovery`, ask:

- Did the user's earlier vague, incomplete, or misleading prompt cause the assistant's bad result?
- Is the user correcting a recurring agent failure that they have already corrected many times?
- Would a stronger user-owned move be to change the workflow, prompt template, rule, test, memory, or guardrail so the same correction is not needed again?

If the answer is yes, downgrade portfolio readiness unless the user recognizes the recurrence and introduces a durable fix. A repeated correction can be useful evidence, but the portfolio-worthy move is preventing the repeated failure, not heroically correcting it again.

## Portfolio False-Positive Guards

These are common ways a window can look strong while failing the real bar. If any guard fails, do not assign `mindblowing_portfolio` or `outstanding_portfolio`.

- `heroic_recovery_without_prevention` - the user rescues a bad result, but does not prevent the class of failure from recurring.
- `polished_but_not_evidence_backed` - the prompt sounds mature, but lacks transcript evidence, concrete constraints, observed failures, or verified stakes.
- `verbosity_or_template_stuffing` - the prompt is long or contains goal/context/risk/tradeoff words, but those details do not change the assistant's decision path.
- `assistant_supplied_core_insight` - the assistant supplied the main diagnosis, architecture, tradeoff, or portfolio story, and the user mostly accepted or restated it.
- `local_fix_without_system_guardrail` - the user fixes one instance when a reusable rule, test, prompt pattern, memory, or workflow guardrail is the higher-leverage move.
- `wrong_problem_solved_well` - the user drives the AI effectively, but toward the wrong problem, wrong audience, or wrong success standard.
- `style_improvement_masquerading_as_judgment` - the user mainly asks for rewrite, format, tone, or crispness without changing the underlying decision.
- `no_outcome_or_artifact_delta` - the window has a good idea, but no clear effect on an artifact, standard, architecture, workflow, or decision.
- `rubric_gaming` - the prompt appears to satisfy rubric keywords but does not show authentic judgment or better AI use.

These guards should coach toward the missing higher-leverage move. For example: "Instead of correcting Langfuse drift again, add a CI rule that prevents local prompt copies from reappearing."

## Minimum Mindblowing Gates

A window can be `mindblowing` only if both gates pass:

- `human_original_move` - the user introduced the key insight, concern, reframing, standard, or decision.
- `non_obvious_insight` - the move is unlikely to be produced by a generic LLM from the same context alone.

If either gate fails, the label cannot be `mindblowing_portfolio` or `mindblowing_highlight`.

## Portfolio-Readiness Gates

These decide whether a strong or mindblowing window is portfolio-ready. If any gate fails, use a highlight label instead of a portfolio label.

- `context_verified` - surrounding conversation is available enough to explain how the move arose.
- `assistant_delta` - the user changed the direction, quality, or standard of the assistant's work.
- `not_self_inflicted` - the high-value move was not mainly a repair of a bad result caused by the user's own earlier weak prompt.
- `recurrence_addressed` - if the issue is recurring, the user improves the workflow or guardrail instead of just repeating the same correction.
- `false_positive_guards_passed` - none of the portfolio false-positive guards apply.
- `real_project_stakes` - the move is grounded in a specific product, workflow, client, system, artifact, or business decision.
- `evidence_sufficient` - the transcript or verified context supports the user's reasoning.
- `artifact_or_decision_impact` - the move changed a durable artifact, standard, architecture, plan, implementation path, or decision.
- `case_study_anatomy` - the situation, stakes, human move, evidence used, alternative rejected, artifact changed, outcome or learning, and why-not-generic-LLM explanation can all be filled honestly.

## Depth Score

Score 1 point only when the dimension is clearly demonstrated by the returned window or by context that directly verifies the window. No half credit. Do not award points for keyword presence, politeness, prompt format, or assistant-supplied insight.

1. `ownership` - the user owns the decision like an owner, not a ticket-taker.
2. `originality` - the insight is specific, non-obvious, and user-owned.
3. `reframe` - the user reframes the problem, success standard, or direction.
4. `steering_recovery` - the user redirects, corrects, or bounds the assistant; do not award if the correction merely repairs a self-inflicted or recurring failure without a durable fix.
5. `evidence` - the user provides, demands, challenges, or applies concrete facts or constraints.
6. `alternatives` - the window compares meaningful paths or rejects options with reasons.
7. `tradeoffs_second_order` - the user names costs, risks, scale, reversibility, timing, or second-order effects.
8. `leverage_at_scale` - the user uses AI, automation, deterministic workflows, or reuse to multiply output and quality.
9. `business_value` - the move connects to client value, revenue, cost, risk, or time-to-value.
10. `artifact_impact` - the move materially changes a durable artifact or decision path.

Scoring anchors:

- `0` - missing, generic, assistant-supplied, purely implied, conventional, or visible only with charity.
- `1` - specific, user-owned, grounded in the transcript, and strong enough to change how a skilled Trilogy collaborator would continue the work.

If you cannot quote or closely paraphrase the user's move for a dimension, score it `0`.

## Score To Label

- `mindblowing_portfolio` - `insight_quality = mindblowing`, `portfolio_ready = true`, all gates pass, and `score >= 8`.
- `outstanding_portfolio` - `insight_quality = outstanding`, `portfolio_ready = true`, all gates pass, and `score >= 8`.
- `mindblowing_highlight` - `insight_quality = mindblowing`, but one or more portfolio-readiness gates are missing.
- `strong_highlight` - genuine user-owned value, usually `score` 4 to 7, or `score >= 8` without enough rarity or publishable evidence.
- `below_bar` - `score <= 3`, no genuine user-owned move, assistant-supplied insight, or routine/generic work.

Score alone never creates a portfolio label. On portfolio-readiness doubt, choose a highlight. On insight-quality doubt, choose the lower quality.

## Insight Types

Choose exactly one:

- `course_correction` - recognizes an unproductive loop and changes the working method.
- `problem_framing` - moves from a vague task to the real decision, audience, or review standard.
- `evidence_validation` - checks claims, asks for proof, or searches for missing facts before committing.
- `tradeoff_judgment` - compares options by friction, risk, scope, maintainability, user impact, or timing.
- `architecture_process_design` - shapes systems, workflows, ownership boundaries, observability, or feedback loops.
- `principled_pushback` - rejects a plausible model suggestion when it violates intent, constraints, or standards.
- `artifact_leverage` - turns discussion into a cleaner doc, implementation path, demo, prompt, test, or reusable standard.
- `none` - no meaningful insight pattern is present.

## Automatic Fail Patterns

A window is normally not portfolio-ready if the user is mainly:

- Asking the assistant to write, rewrite, summarize, format, or polish.
- Using a prompt template without adding real judgment.
- Asking for options without naming a hypothesis, constraint, rejection, or decision.
- Accepting the assistant's recommendation without validation or pushback.
- Triggering a bad result through an unclear earlier prompt, then asking to fix the result without acknowledging or correcting the upstream cause.
- Repeating the same correction across conversations instead of creating a rule, test, prompt pattern, memory, or workflow change that prevents recurrence.
- Performing heroic recovery without creating prevention.
- Writing a long, polished, rubric-shaped prompt with no genuine decision move.
- Solving the wrong problem well.
- Asking a generic product, architecture, or research question that could apply to many projects.
- Relying on assistant research where the insight belongs to the assistant, not the user.
- Telling a portfolio story that requires invented context outside the transcript.
- Repeating strong-sounding words like "risk", "tradeoff", "architecture", or "evidence" without a real move.
- Adding manual or unreliable LLM-in-the-loop steps where a deterministic or automated workflow is the higher-leverage move.
- Producing technically sound work with no line to business value, client outcome, cost, risk, or scale impact.

These patterns can still become `mindblowing_highlight` only when the user introduces a genuinely rare move but the portfolio record is incomplete.

## Required Output Fields

Each grade must be a single JSON object with these fields:

- `score` - integer 0 to 10.
- `label` - one of the five labels above.
- `insight_quality` - `mindblowing`, `outstanding`, `strong`, or `routine`.
- `portfolio_ready` - true only for `mindblowing_portfolio` or `outstanding_portfolio`.
- `strengths` - specific evidence for the score.
- `gaps` - failed gates, weak dimensions, or missing evidence.
- `coaching` - 2 to 4 concrete bullets for improving the next move.
- `better_prompt` - a rewritten prompt that preserves intent and adds the missing judgment.
- `insight_type` - one insight type from this rubric.
- `why_it_matters` - the decision, risk reduction, or execution improvement enabled by the move.
- `strongest_move` - the best user-owned thinking move, quoted or closely paraphrased.
- `missing_move` - the highest-leverage addition that would improve the window.
- `key_user_move` - the strongest candidate user-owned move, quoted or closely paraphrased.
- `generic_llm_counterfactual` - whether a generic LLM could likely produce the same move from the same context alone.
- `attribution_basis` - evidence that the move came from the user rather than the assistant.
- `decision_rationale` - concise justification for the final label after the audit and gates.
- `minimum_mindblowing_gates_failed` - failed minimum gates, or an empty list.
- `portfolio_readiness_gates_failed` - failed readiness gates, or an empty list.
- `case_study_anatomy_failed` - missing case-study anatomy fields, or an empty list.
- `mentor_review_needed` - true when originality, context, or domain meaning is uncertain.
- `mentor_alignment_risk` - what a human reviewer might disagree with.
- `confidence` - `high`, `medium`, or `low`.
- `decision_quality` - short notes for `frame`, `alternatives`, `information`, `tradeoffs`, `reasoning`, and `commitment_to_action`.

## Coaching Rules

For `below_bar`, `strong_highlight`, and `mindblowing_highlight`, coach toward a stronger thinking move, not just a prettier prompt.

- Name the failed gates or weak dimensions.
- Explain whether the weakness is context, ownership, assistant-supplied insight, evidence, impact, outcome, originality, upstream cause, or recurrence.
- Tie the diagnosis to the user's actual words.
- Suggest a stronger next move: validation question, edge-case test, POC criterion, decision log, artifact revision, second-order-effect check, evidence demand, workflow guardrail, or reusable rule.

Do not turn a weak window into a polished fake portfolio entry. If the transcript does not prove the insight, say so.
