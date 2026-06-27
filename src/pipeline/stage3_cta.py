"""
stage3_cta.py — Stage 3: Conversation Trajectory Analysis (CTA)

Impact check: did the conversation improve in direction, quality, or
specificity as a result of this user prompt?

Core rubric question: Did the user drive the LLM, or did the LLM drive the user?
A strong trajectory delta requires the user prompt to have genuinely advanced
the conversation in a user-driven way — not just triggered a long LLM output.

We ask an LLM judge to assess the *trajectory delta* — how much the
conversation's heading changed for the better after the focal user turn.

A strong or moderate improvement suggests the user prompt drove meaningful
progress; weak or no improvement suggests the conversation drifted or stalled.

Trajectory delta values:
  - "strong"   → clear, substantive improvement; above_bar_candidate
  - "moderate" → noticeable improvement; above_bar_candidate
  - "weak"     → minor or surface-level change; near_bar
  - "none"     → no improvement or negative drift; near_bar
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

MAX_RETRIES: int = 3

# Trajectory delta values that qualify a window as an above-bar candidate.
ABOVE_BAR_DELTAS = {"strong", "moderate"}

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

CTA_SYSTEM_PROMPT = """\
You are an expert conversation quality judge specialising in trajectory analysis.

Your task: analyse how the conversation changed in direction, quality, and
specificity *after* the focal user prompt. Assess the trajectory delta.

Trajectory delta definitions:
- "strong"   : The user prompt clearly advanced the conversation — introduced
               a concrete direction, made a significant clarifying distinction,
               unlocked a new line of reasoning, or substantially improved
               the quality or specificity of the dialogue.
- "moderate" : The user prompt noticeably improved the conversation — added
               useful context, refined scope, or redirected away from a
               dead-end with clear intent.
- "weak"     : The user prompt caused only minor or surface-level change —
               small clarifications that didn't meaningfully advance things,
               or improvement that the LLM would have reached anyway.
- "none"     : The user prompt caused no improvement, or the conversation
               drifted, stalled, or degraded after it.

Consider:
1. Was the next LLM response better (more specific, accurate, useful) because
   of this user prompt?
2. Did the following user turn (if present) show deeper engagement, suggesting
   the prior exchange was productive?
3. Would removing this user turn have materially changed the conversation's
   trajectory?

Respond ONLY with valid JSON — no markdown, no code fences:
{
  "trajectory_delta": "<strong|moderate|weak|none>",
  "reasoning": "<one paragraph explaining your assessment>"
}
"""

CTA_USER_TEMPLATE = """\
CONVERSATION WINDOW:

{conversation_text}

FOCAL USER PROMPT (the turn being graded):
{focal_user_prompt}

Assess the trajectory delta caused by this focal user prompt.
"""

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_stage3(
    window: Dict[str, Any],
    provider: str,
    model: str,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Run Conversation Trajectory Analysis on a conversation window.

    Parameters
    ----------
    window:
        Conversation window dict with a ``turns`` list.
    provider:
        LLM provider: ``"anthropic"`` or ``"openai"``.
    model:
        Model identifier string.
    api_key:
        Optional API key; falls back to environment variable if omitted.

    Returns
    -------
    dict
        ``{"tier": "above_bar_candidate"|"near_bar",
           "trajectory_delta": str, "reasoning": str}``
    """
    turns: List[Dict[str, Any]] = window.get("turns", [])
    focal_user_prompt = _get_focal_user_prompt(turns)

    if not focal_user_prompt:
        return _fallback_result("No user turn found in window.")

    conversation_text = _format_conversation(turns)

    has_follow_up = _has_follow_up_turns(turns, focal_user_prompt)
    user_msg = CTA_USER_TEMPLATE.format(
        conversation_text=conversation_text,
        focal_user_prompt=focal_user_prompt,
        has_follow_up="yes" if has_follow_up else "no — this may be the end of the transcript",
    )

    raw = _call_llm_with_retry(
        system_prompt=CTA_SYSTEM_PROMPT,
        user_message=user_msg,
        provider=provider,
        model=model,
        api_key=api_key,
    )

    if raw is None:
        return _fallback_result("LLM call failed after retries.")

    try:
        result = _parse_and_validate(raw)
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.error("CTA: parse error: %s | raw=%r", exc, raw)
        return _fallback_result(f"Parse error: {exc}")

    delta = result["trajectory_delta"]
    tier = "above_bar_candidate" if delta in ABOVE_BAR_DELTAS else "near_bar"

    return {
        "tier": tier,
        "trajectory_delta": delta,
        "reasoning": result["reasoning"],
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_focal_user_prompt(turns: List[Dict[str, Any]]) -> Optional[str]:
    """Return the text of the first user turn in the window."""
    for turn in turns:
        if turn.get("role") == "user":
            text = turn.get("text", "").strip()
            if text:
                return text
    return None




def _has_follow_up_turns(turns: List[Dict[str, Any]], focal_user_prompt: str) -> bool:
    """Return True if there are any turns after the focal user turn."""
    found_focal = False
    for turn in turns:
        if found_focal:
            # There is at least one turn after the focal user turn
            if turn.get("text", "").strip():
                return True
        if turn.get("role") == "user" and turn.get("text", "").strip() == focal_user_prompt:
            found_focal = True
    return False

def _format_conversation(turns: List[Dict[str, Any]]) -> str:
    """Format turns as a readable conversation transcript."""
    lines: List[str] = []
    for turn in turns:
        role = turn.get("role", "unknown").upper()
        text = turn.get("text", "").strip()
        if text:
            lines.append(f"[{role}]\n{text}")
    return "\n\n".join(lines)


def _parse_and_validate(raw: str) -> Dict[str, Any]:
    """Parse LLM JSON output and validate required fields.

    Handles optional no_follow_up_turns field and strips markdown fences.
    """
    cleaned = _strip_markdown(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        data = json.loads(raw)

    if "trajectory_delta" not in data:
        raise KeyError("Missing key: trajectory_delta")

    delta = str(data["trajectory_delta"]).lower().strip()
    if delta not in ("strong", "moderate", "weak", "none"):
        raise ValueError(f"Invalid trajectory_delta: {delta!r}")
    data["trajectory_delta"] = delta

    # Provide reasoning default
    if "reasoning" not in data:
        data["reasoning"] = ""

    return data


def _fallback_result(reason: str) -> Dict[str, Any]:
    """Return a near-bar fallback result on error."""
    logger.warning("CTA fallback: %s", reason)
    return {
        "tier": "near_bar",
        "trajectory_delta": "none",
        "reasoning": reason,
    }


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------


def _call_llm_with_retry(
    system_prompt: str,
    user_message: str,
    provider: str,
    model: str,
    api_key: Optional[str],
) -> Optional[str]:
    """Call the LLM with exponential-backoff retry. Returns raw text or None."""
    for attempt in range(MAX_RETRIES):
        try:
            if provider == "openai":
                return _call_openai(system_prompt, user_message, model, api_key)
            elif provider == "anthropic":
                return _call_anthropic(system_prompt, user_message, model, api_key)
            else:
                raise ValueError(f"Unknown provider: {provider}")
        except Exception as exc:
            logger.warning("CTA attempt %d/%d failed: %s", attempt + 1, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
    return None


def _call_openai(
    system_prompt: str,
    user_message: str,
    model: str,
    api_key: Optional[str],
) -> str:
    """Call OpenAI chat completions and return raw text."""
    try:
        from openai import OpenAI  # type: ignore
    except ImportError as exc:
        raise ImportError("openai package not installed. Run: pip install openai") from exc

    client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    if not raw or not raw.strip():
        raise ValueError("Empty response from OpenAI")
    return raw


def _call_anthropic(
    system_prompt: str,
    user_message: str,
    model: str,
    api_key: Optional[str],
) -> str:
    """Call Anthropic messages API and return raw text."""
    try:
        import anthropic  # type: ignore
    except ImportError as exc:
        raise ImportError("anthropic package not installed. Run: pip install anthropic") from exc

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
    return _strip_markdown(raw)


def _strip_markdown(text: str) -> str:
    """Strip markdown code fences from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]
    return text.strip()
