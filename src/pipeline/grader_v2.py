"""
grader_v2.py — WorkPulse Grading Pipeline v2 Orchestrator

Runs the 4-stage pipeline in sequence, stopping early when a stage
definitively rules a window below-bar.

Pipeline:
    Stage 1 (SND)  — Semantic Novelty Detection         [cheap pre-filter]
    Stage 2 (IOAS) — Intent-Outcome Alignment Scoring   [steering check]
    Stage 3 (CTA)  — Conversation Trajectory Analysis   [impact check]
    Stage 4 (EJAD) — Ensemble + Adversarial Dissenter   [final gate]

Decision logic:
    Stage 1 fail → BELOW_BAR  (stop)
    Stage 2 fail → BELOW_BAR  (stop)
    Stage 3 weak → NEAR_BAR   (stop)
    Stage 4 fail → NEAR_BAR
    Stage 4 pass → ABOVE_BAR
"""

from __future__ import annotations

import logging
import traceback
from typing import Any, Dict, Optional

from src.pipeline.stage1_snd import run_stage1
from src.pipeline.stage2_ioas import run_stage2
from src.pipeline.stage3_cta import run_stage3
from src.pipeline.stage4_ejad import run_stage4

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Label / score mappings per tier
# ---------------------------------------------------------------------------

TIER_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "above_bar": {
        "label": "outstanding_portfolio",
        "score": 8,
    },
    "near_bar": {
        "label": "strong_highlight",
        "score": 5,
    },
    "below_bar": {
        "label": "below_bar",
        "score": 1,
    },
}

# ---------------------------------------------------------------------------
# Coaching / better_prompt generation prompt (reuses grader LLM infra)
# ---------------------------------------------------------------------------

COACHING_SYSTEM = """You are a prompt-quality coach for AI-assisted development.

CORE QUESTION: Did the user drive the LLM, or did the LLM drive the user?
Your coaching must help the user become a better driver.

Given a near-bar conversation window and the specific pipeline stage that
caused it to fall short, provide:
1. coaching: one paragraph of actionable, specific advice. Reference exactly
   which stage the window failed (Stage 2: intent clarity, Stage 3: trajectory
   impact, or Stage 4: dissenter objection) and what the user needs to change.
   Avoid generic advice — be concrete about THIS window.
2. better_prompt: a concrete rewritten version of the focal user prompt that
   addresses the specific failure. The rewrite should make the user's intent
   clearer, bring genuine user-originated insight, and steer the LLM more
   effectively.

Common coaching patterns for near-bar outcomes:
- Stage 2 failed (low intent_clarity): User needs to express their own goal
  more specifically — what to do, why, and what constraints apply.
- Stage 2 failed (low outcome_precision): Prompt was too vague; rewrite with
  tighter scope so the LLM addresses the intent precisely.
- Stage 3 failed (weak/no trajectory): Prompt did not move conversation forward;
  rewrite to introduce a new direction or concrete constraint.
- Stage 4 failed (dissenter objection): Identify the anti-pattern (e.g. user
  restating LLM output, user just approving) and rewrite showing user judgment.

Respond ONLY with valid JSON — no markdown, no code fences:
{
  "coaching": "<specific actionable paragraph referencing the failing stage>",
  "better_prompt": "<rewritten prompt addressing the specific failure>"
}
"""

COACHING_USER_TEMPLATE = """CONVERSATION WINDOW:

{conversation_text}

FOCAL USER PROMPT:
{focal_user_prompt}

PIPELINE FAILURE REASON:
{pipeline_reason}

Provide specific coaching that addresses the exact failure reason above.
Tell the user which stage failed, why it failed, and what specifically they
should do differently. Then provide a concrete better_prompt rewrite.
"""

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def grade_window_v2(
    window: Dict[str, Any],
    rubric_path: str,
    provider: str,
    model: str,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Grade a conversation window using the 4-stage pipeline.

    Parameters
    ----------
    window:
        A conversation window dict with a ``turns`` list of
        ``{"role": str, "text": str}`` dicts.
    rubric_path:
        Path to the rubric markdown file (used for context; not directly
        injected into pipeline prompts but available for future extensions).
    provider:
        LLM provider: ``"anthropic"`` or ``"openai"``.
    model:
        Model identifier string (e.g. ``"claude-sonnet-4-5"``).
    api_key:
        Optional API key; falls back to environment variable if omitted.

    Returns
    -------
    dict
        ``{
            "tier":          "above_bar"|"near_bar"|"below_bar",
            "label":         str,
            "score":         int,
            "reason":        str,
            "coaching":      str,
            "better_prompt": str,
            "pipeline_trace": {stage_name: result_dict, ...}
        }``
    """
    pipeline_trace: Dict[str, Any] = {}

    # ------------------------------------------------------------------ #
    # Stage 1: Semantic Novelty Detection                                  #
    # ------------------------------------------------------------------ #
    try:
        s1 = run_stage1(window)
    except Exception:
        logger.error("Stage 1 (SND) crashed:\n%s", traceback.format_exc())
        s1 = {
            "passed": False,
            "novelty_score": 0.0,
            "reason": "Stage 1 crashed; treating as below_bar.",
        }

    pipeline_trace["stage1_snd"] = s1

    if not s1.get("passed", False):
        return _build_result(
            tier="below_bar",
            reason=f"Stage 1 (SND) failed: {s1.get('reason', 'low novelty')}",
            coaching="",
            better_prompt="",
            pipeline_trace=pipeline_trace,
        )

    # ------------------------------------------------------------------ #
    # Stage 2: Intent-Outcome Alignment Scoring                            #
    # ------------------------------------------------------------------ #
    try:
        s2 = run_stage2(window, provider=provider, model=model, api_key=api_key)
    except Exception:
        logger.error("Stage 2 (IOAS) crashed:\n%s", traceback.format_exc())
        s2 = {
            "passed": False,
            "score": 0.0,
            "intent": "",
            "reasoning": "Stage 2 crashed; treating as below_bar.",
        }

    pipeline_trace["stage2_ioas"] = s2

    if not s2.get("passed", False):
        return _build_result(
            tier="below_bar",
            reason=(
                f"Stage 2 (IOAS) failed: intent-outcome alignment score "
                f"{s2.get('score', 0.0):.3f} below threshold. "
                f"{s2.get('reasoning', '')}"
            ),
            coaching="",
            better_prompt="",
            pipeline_trace=pipeline_trace,
        )

    # ------------------------------------------------------------------ #
    # Stage 3: Conversation Trajectory Analysis                            #
    # ------------------------------------------------------------------ #
    try:
        s3 = run_stage3(window, provider=provider, model=model, api_key=api_key)
    except Exception:
        logger.error("Stage 3 (CTA) crashed:\n%s", traceback.format_exc())
        s3 = {
            "tier": "near_bar",
            "trajectory_delta": "none",
            "reasoning": "Stage 3 crashed; treating as near_bar.",
        }

    pipeline_trace["stage3_cta"] = s3

    if s3.get("tier") != "above_bar_candidate":
        # Weak or no trajectory → near_bar; generate coaching.
        reason = (
            f"Stage 3 (CTA): trajectory delta is "
            f"'{s3.get('trajectory_delta', 'unknown')}' — not strong enough "
            f"for above-bar. {s3.get('reasoning', '')}"
        )
        coaching, better_prompt = _get_coaching(
            window=window,
            pipeline_reason=reason,
            provider=provider,
            model=model,
            api_key=api_key,
        )
        return _build_result(
            tier="near_bar",
            reason=reason,
            coaching=coaching,
            better_prompt=better_prompt,
            pipeline_trace=pipeline_trace,
        )

    # ------------------------------------------------------------------ #
    # Stage 4: Ensemble + Adversarial Dissenter                            #
    # ------------------------------------------------------------------ #
    try:
        s4 = run_stage4(window, provider=provider, model=model, api_key=api_key)
    except Exception:
        logger.error("Stage 4 (EJAD) crashed:\n%s", traceback.format_exc())
        s4 = {
            "passed": False,
            "standard_verdict": "",
            "dissenter_objection": "",
            "final_reasoning": "Stage 4 crashed; treating as near_bar.",
        }

    pipeline_trace["stage4_ejad"] = s4

    if not s4.get("passed", False):
        reason = (
            f"Stage 4 (EJAD) did not confirm above-bar. "
            f"{s4.get('final_reasoning', '')}"
        )
        coaching, better_prompt = _get_coaching(
            window=window,
            pipeline_reason=reason,
            provider=provider,
            model=model,
            api_key=api_key,
        )
        return _build_result(
            tier="near_bar",
            reason=reason,
            coaching=coaching,
            better_prompt=better_prompt,
            pipeline_trace=pipeline_trace,
        )

    # ------------------------------------------------------------------ #
    # All stages passed → ABOVE_BAR                                        #
    # ------------------------------------------------------------------ #
    reason = (
        f"All 4 pipeline stages passed. "
        f"Novelty: {s1.get('novelty_score', 'n/a')}. "
        f"Intent alignment: {s2.get('score', 'n/a'):.3f}. "
        f"Trajectory: {s3.get('trajectory_delta', 'n/a')}. "
        f"Ensemble: {s4.get('final_reasoning', '')}"
    )
    return _build_result(
        tier="above_bar",
        reason=reason,
        coaching="",
        better_prompt="",
        pipeline_trace=pipeline_trace,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_result(
    tier: str,
    reason: str,
    coaching: str,
    better_prompt: str,
    pipeline_trace: Dict[str, Any],
) -> Dict[str, Any]:
    """Assemble the final graded result dict."""
    defaults = TIER_DEFAULTS.get(tier, TIER_DEFAULTS["below_bar"])
    return {
        "tier": tier,
        "label": defaults["label"],
        "score": defaults["score"],
        "reason": reason,
        "coaching": coaching,
        "better_prompt": better_prompt,
        "pipeline_trace": pipeline_trace,
    }


def _get_focal_user_prompt(window: Dict[str, Any]) -> str:
    """Return the focal user prompt text from a window, or empty string."""
    for turn in window.get("turns", []):
        if turn.get("role") == "user":
            text = turn.get("text", "").strip()
            if text:
                return text
    return ""


def _format_conversation(window: Dict[str, Any]) -> str:
    """Format all turns as a readable transcript."""
    lines = []
    for turn in window.get("turns", []):
        role = turn.get("role", "unknown").upper()
        text = turn.get("text", "").strip()
        if text:
            lines.append(f"[{role}]\n{text}")
    return "\n\n".join(lines)


def _get_coaching(
    window: Dict[str, Any],
    pipeline_reason: str,
    provider: str,
    model: str,
    api_key: Optional[str],
) -> tuple[str, str]:
    """Generate coaching and better_prompt for near-bar windows.

    Returns (coaching, better_prompt). Falls back to empty strings on error.
    """
    import json
    import time

    focal = _get_focal_user_prompt(window)
    if not focal:
        return "", ""

    conv_text = _format_conversation(window)
    user_msg = COACHING_USER_TEMPLATE.format(
        conversation_text=conv_text,
        focal_user_prompt=focal,
        pipeline_reason=pipeline_reason,
    )

    for attempt in range(3):
        try:
            if provider == "openai":
                raw = _call_openai_raw(COACHING_SYSTEM, user_msg, model, api_key)
            elif provider == "anthropic":
                raw = _call_anthropic_raw(COACHING_SYSTEM, user_msg, model, api_key)
            else:
                return "", ""

            data = json.loads(raw)
            return (
                str(data.get("coaching", "")),
                str(data.get("better_prompt", "")),
            )
        except Exception as exc:
            logger.warning("Coaching call attempt %d/3 failed: %s", attempt + 1, exc)
            if attempt < 2:
                time.sleep(2 ** attempt)

    return "", ""


def _call_openai_raw(
    system_prompt: str,
    user_message: str,
    model: str,
    api_key: Optional[str],
) -> str:
    """Minimal OpenAI call returning raw text."""
    import os

    from openai import OpenAI  # type: ignore

    client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    if not raw or not raw.strip():
        raise ValueError("Empty response from OpenAI")
    return raw


def _call_anthropic_raw(
    system_prompt: str,
    user_message: str,
    model: str,
    api_key: Optional[str],
) -> str:
    """Minimal Anthropic call returning raw text."""
    import os

    import anthropic  # type: ignore

    client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    raw = response.content[0].text if response.content else ""
    if not raw or not raw.strip():
        raise ValueError("Empty response from Anthropic")
    # Strip markdown fences
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()
