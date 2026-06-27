---
name: prompt-coach
description: Grades Cursor chat windows using the workflow.md rubric. Separates insight quality from portfolio readiness, writes grades to data/graded_events.jsonl, and can save portfolio-ready insights to data/approved_insights.md. Use when the user asks to grade prompts, run prompt coach, check whether a prompt is mindblowing or portfolio-ready, or review latest Cursor transcripts.
disable-model-invocation: true
---

# Prompt Coach (Cursor LLM Grader)

Grade user windows from Cursor agent transcripts using `workflow.md` and the canonical rubric in `data/high_bar_window_rubric.md`. The monitor uses the Cursor SDK by default; manual skill grading uses your judgment inside Cursor chat.

## When to run

Use when the user asks to:
- grade their latest prompt (or new prompts since last run)
- check insight quality or portfolio readiness
- run prompt coach / prompt-coach skill
- review ungraded transcript pairs

## Pipeline (run every step, in order)

Copy this checklist and track progress:

```
- [ ] 1. Export: run the grade queue script
- [ ] 2. Read: queue file, workflow rubric, and approved examples
- [ ] 3. Grade: apply rubric to each queued prompt-response window
- [ ] 4. Confirm: ask before saving portfolio-ready insights
- [ ] 5. Persist: write results JSON and run apply script
- [ ] 6. Report: summarize labels, scores, and coaching
```

### 1. Export ungraded prompts

Read `config/settings.json` for paths. From the project root, run:

```powershell
python -m src.export_grade_queue --latest 1
```

For all new prompts since last grading:

```powershell
python -m src.export_grade_queue --all-new
```

Then read `data/cursor_grade_queue.json`. If `pairs` is empty, report that everything is already graded and stop.

### 2. Read rubric and examples

Read these files before grading:
- `workflow.md` - rubric dimensions
- `data/high_bar_window_rubric.md` - canonical labels and gates
- `data/approved_insights.md` - examples of portfolio-ready windows (if present)

### 3. Grade each queued pair

For each item in `pairs`, treat the user prompt plus assistant reply as a small candidate window. Use the assistant reply as context only; do not credit the user for insights the assistant supplied.

Grade on two axes:
- `insight_quality`: `mindblowing`, `outstanding`, `strong`, or `routine`
- `portfolio_ready`: true only when the transcript evidence is complete enough for approved portfolio use

Minimum mindblowing gates:
- `human_original_move`: the user introduced the key insight, concern, reframing, standard, or decision.
- `non_obvious_insight`: a generic LLM would be unlikely to produce the same move from the docs alone.

Portfolio-readiness gates:
- context verified
- assistant-delta proven
- real project stakes
- evidence sufficient
- artifact or decision impact
- case-study anatomy complete

Labels:
- `mindblowing_portfolio`: rare first-principles move plus complete portfolio evidence
- `outstanding_portfolio`: very strong complete portfolio case
- `mindblowing_highlight`: rare move but missing portfolio evidence, context, impact, or anatomy
- `strong_highlight`: genuine user-owned value but not rare or complete enough for portfolio
- `below_bar`: routine, generic, assistant-led, or ordinary execution

Do not let checklist completion create a portfolio label. Do not let missing portfolio evidence erase a genuinely mindblowing human move.

**Scoring anchors**:
- `0`: missing, generic, copied from the assistant, purely implied, or present only as a keyword
- `1`: self-directed, specific, user-owned, grounded in the prompt, and strong enough to change what a skilled collaborator would do
- No half credit. If you cannot quote or paraphrase the user's move for a dimension, score `0`.

**Mentor review**:
Set `mentor_review_needed` to `true` when originality, assistant-delta, domain context, portfolio readiness, or evidence completeness is debatable.

**Insight diagnosis**:
- `insight_type`: one of `course_correction`, `problem_framing`, `evidence_validation`, `tradeoff_judgment`, `architecture_process_design`, `principled_pushback`, `artifact_leverage`, or `none`
- `why_it_matters`: what better decision, risk reduction, or execution improvement the prompt enables
- `strongest_move`: the best thinking move the user made in their actual words
- `missing_move`: the highest-leverage addition that would improve the next prompt
- `decision_quality`: short notes for `frame`, `alternatives`, `information`, `tradeoffs`, `reasoning`, and `commitment_to_action`
- `mentor_review_needed`: boolean
- `mentor_alignment_risk`: what a human mentor might disagree with
- `confidence`: `high`, `medium`, or `low`

Be honest. Strengths and gaps must name specific rubric dimensions.

### 4. Confirm portfolio saves

For each `mindblowing_portfolio` or `outstanding_portfolio` result, ask the user:

> This window is portfolio-ready. Save it to your portfolio (`data/approved_insights.md`)?

Set `save_to_portfolio` to `true` only if they approve. Default `false`.

### 5. Persist results

Write `data/cursor_grade_results.json` using this schema:

```json
{
  "grades": [
    {
      "event_id": "transcript_path:turn_index",
      "pair": {
        "transcript_path": "...",
        "user_text": "...",
        "assistant_text": "...",
        "turn_index": 0,
        "file_mtime": 0.0
      },
      "grade": {
        "score": 8,
        "label": "outstanding_portfolio",
        "insight_quality": "outstanding",
        "portfolio_ready": true,
        "strengths": ["frame: ...", "tradeoffs: ..."],
        "gaps": ["depth: ..."],
        "coaching": "2-4 bullets tied to this prompt's gaps, not a generic paragraph.",
        "better_prompt": "Full rewritten prompt with goal, context, constraints, and proposed direction.",
        "insight_type": "tradeoff_judgment",
        "why_it_matters": "Explains how this prompt changes a decision or reduces execution risk.",
        "strongest_move": "The strongest thinking move in the user's actual prompt.",
        "missing_move": "The highest-leverage addition for next time.",
        "minimum_mindblowing_gates_failed": [],
        "portfolio_readiness_gates_failed": [],
        "case_study_anatomy_failed": [],
        "decision_quality": {
          "frame": "...",
          "alternatives": "...",
          "information": "...",
          "tradeoffs": "...",
          "reasoning": "...",
          "commitment_to_action": "..."
        },
        "mentor_review_needed": false,
        "mentor_alignment_risk": "What a human mentor might disagree with.",
        "confidence": "medium"
      },
      "save_to_portfolio": false
    }
  ]
}
```

Then run:

```powershell
python -m src.apply_cursor_grades
```

### 6. Report to the user

For each graded prompt, show:
- **Label** and **score**
- The user prompt (short excerpt if long)
- Top strengths and gaps
- Insight type, strongest move, missing move, and why it matters
- Confidence and mentor-review flag
- Coaching and better_prompt

End with counts by label and whether any were saved to the portfolio.

## Rules

- Grade user prompts only; never grade assistant reply quality.
- Do not invent transcript content; use only what is in the queue file.
- Do not skip the apply script; it prevents duplicate event_ids in `data/graded_events.jsonl`.
- Do not append to `data/approved_insights.md` without user approval, and only save `mindblowing_portfolio` or `outstanding_portfolio` entries.
- For manual skill runs, do not call external LLM APIs; your judgment as Cursor agent is the grader.
- Keep coaching specific and actionable, not generic praise.

## Automation (monitor)

When `monitor_auto_coach` is `true` (default), `python -m src.monitor` grades prompts automatically via the **Cursor SDK** using `CURSOR_API_KEY`. It shows popups for portfolio-ready, highlight, and below-bar labels (live session only unless `monitor_notify_backlog` is true).

Set `"grader": "anthropic"` to use the Anthropic backend. Otherwise keep `"grader": "cursor"` for Cursor SDK grading.

Restart the monitor after changing settings.

## Automation (optional Cursor cron)

For periodic grading without opening chat each time, create a Cursor Automation (hourly cron) with:

```
Run the prompt-coach skill: export new ungraded prompts with
`python -m src.export_grade_queue --all-new`, grade them per the skill,
write data/cursor_grade_results.json, run `python -m src.apply_cursor_grades`,
and report counts. Do not save portfolio-ready prompts to the portfolio without
explicit approval; set save_to_portfolio false for automated runs.
```
