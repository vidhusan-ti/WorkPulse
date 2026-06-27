# Mentor Calibration Protocol

Use this protocol to align the LLM grader with mentor judgment. The rubric is only considered production-grade after it is tested against mentor-labeled windows.

## Dataset Shape

Create `data/mentor_calibration_set.jsonl` with one JSON object per window:

```json
{
  "prompt": "User prompt text",
  "assistant_context": "Relevant assistant reply or prior context",
  "mentor_label": "mindblowing_portfolio | outstanding_portfolio | mindblowing_highlight | strong_highlight | below_bar",
  "mentor_insight_quality": "mindblowing | outstanding | strong | routine",
  "mentor_portfolio_ready": false,
  "mentor_score": 0,
  "mentor_reason": "Why the mentor labeled it this way",
  "mentor_key_user_move": "Strongest user-owned move, quoted or closely paraphrased",
  "mentor_generic_llm_counterfactual": "What a generic LLM likely would have done from the same context",
  "mentor_attribution_basis": "Why the key move belongs to the user, assistant, both, or neither",
  "mentor_decision_rationale": "Why the final label follows from the holistic move plus the gates",
  "minimum_mindblowing_gates_failed": [],
  "portfolio_readiness_gates_failed": [],
  "case_study_anatomy_failed": [],
  "expected_insight_type": "course_correction | problem_framing | evidence_validation | tradeoff_judgment | architecture_process_design | principled_pushback | artifact_leverage | none",
  "rubric_version": "2.5"
}
```

## Required Mix

Collect at least 50 real windows:

- 20 obvious `below_bar` windows
- 10 `strong_highlight` windows
- 8 `mindblowing_highlight` windows with incomplete evidence
- 7 borderline portfolio-readiness cases
- 5 true portfolio-ready windows

## Acceptance Target

The grader is mentor-aligned only when:

- No known false positives are saved as approved insights.
- Portfolio-ready agreement with the mentor is above 90%.
- Insight-quality agreement is tracked separately from portfolio-readiness agreement.
- Every disagreement is categorized by attribution, generic-LLM counterfactual, minimum mindblowing gate, portfolio-readiness gate, anatomy field, or ambiguous dimension.
- The judge consistently marks borderline windows with `mentor_review_needed = true`.
- False positives must show where the audit failed: wrong key user move, assistant-owned synthesis credited to the user, overconfident counterfactual, or unsupported decision rationale.

## Review Loop

1. Mentor labels the dataset.
2. Run the Cursor grader on the same prompts.
3. Compare label, insight quality, portfolio-ready status, score, insight type, failed gates, and hybrid audit fields.
4. Audit false positives first.
5. Update the holistic judge instructions, counterfactual test, attribution rules, gates, anchor tests, or examples.
6. Repeat after changing the rubric, judge model, or prompt examples.

## Hybrid Audit Checks

For every disagreement, review these questions before changing the rubric:

- Did the judge select the same `key_user_move` as the mentor?
- Did it correctly separate user-owned thinking from assistant-supplied synthesis?
- Did the `generic_llm_counterfactual` explain why the move is or is not non-obvious from the same context alone?
- Did `decision_rationale` connect the holistic judgment to the final gates and label?
- Did uncertainty in attribution or counterfactual reasoning trigger `mentor_review_needed = true`?
