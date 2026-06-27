"""
stage2_ioas.py — Stage 2: Intent-Outcome Alignment Scoring (IOAS)

Steering check: did the user's prompt have a clear intent, and did the LLM
actually serve that intent precisely?

Core rubric question: Did the user drive the LLM, or did the LLM drive the user?
A prompt that merely restates LLM output scores low on intent_clarity even if
syntactically well-formed — the user must bring independent steering intent.

Algorithm:
  1. Send the focal user turn + immediate LLM response to an LLM judge.
  2. Judge extracts the intent and scores:
       - intent_clarity   (0–1): how clearly the user expressed their goal
       - outcome_precision (0–1): how precisely the LLM response served it
  3. combined_score = intent_clarity × outcome_precision
  4. If combined_score < ALIGNMENT_THRESHOLD → below_bar
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

ALIGNMENT_THRESHOLD: float = 0.45
MAX_RETRIES: int = 3

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

IOAS_SYSTEM_PROMPT = """\
You are an expert conversation quality judge.

Your task: given a user prompt and the LLM's response to it, assess:
1. How clearly the user expressed their intent (intent_clarity).
2. How precisely the LLM response served that intent (outcome_precision).

Scoring guidelines:
- intent_clarity 0.0: no discernible intent, vague noise
- intent_clarity 0.5: partial intent, somewhat clear direction
- intent_clarity 1.0: crystal-clear, specific, purposeful request
- outcome_precision 0.0: LLM ignored or missed the intent entirely
- outcome_precision 0.5: LLM partially addressed it, with drift
- outcome_precision 1.0: LLM addressed the intent precisely and completely

Respond ONLY with valid JSON — no markdown, no code fences:
{
  "intent": "<one-sentence description of what the user wanted>",
  "intent_clarity": <float 0.0–1.0>,
  "outcome_precision": <float 0.0–1.0>,
  "reasoning": "<one paragraph explaining both scores>"
}
"""

IOAS_USER_TEMPLATE = """\
USER PROMPT:
{user_prompt}

LLM RESPONSE:
{llm_response}

Rate the intent clarity and outcome precision as described.
"""

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_stage2(
    window: Dict[str, Any],
    provider: str,
    model: str,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Run Intent-Outcome Alignment Scoring on a conversation window.

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
        ``{"passed": bool, "score": float, "intent": str, "reasoning": str}``
    """
    turns: List[Dict[str, Any]] = window.get("turns", [])
    user_prompt, llm_response = _extract_focal_pair(turns)

    if not user_prompt:
        return _fallback_result("No user turn found in window.")
    if not llm_response:
        return _fallback_result("No LLM response found in window.")

    user_msg = IOAS_USER_TEMPLATE.format(
        user_prompt=user_prompt,
        llm_response=llm_response,
    )

    raw = _call_llm_with_retry(
        system_prompt=IOAS_SYSTEM_PROMPT,
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
        logger.error("IOAS: parse error: %s | raw=%r", exc, raw)
        return _fallback_result(f"Parse error: {exc}")

    score = round(result["intent_clarity"] * result["outcome_precision"], 4)
    passed = score >= ALIGNMENT_THRESHOLD

    return {
        "passed": passed,
        "score": score,
        "intent": result["intent"],
        "reasoning": result["reasoning"],
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_focal_pair(
    turns: List[Dict[str, Any]],
) -> tuple[Optional[str], Optional[str]]:
    """Return (focal_user_prompt, immediate_llm_response)."""
    focal_user: Optional[str] = None
    focal_index: Optional[int] = None

    for i, turn in enumerate(turns):
        if turn.get("role") == "user" and focal_user is None:
            focal_user = turn.get("text", "").strip()
            focal_index = i
            break

    if focal_index is None or not focal_user:
        return None, None

    llm_response: Optional[str] = None
    for turn in turns[focal_index + 1 :]:
        if turn.get("role") == "assistant":
            llm_response = turn.get("text", "").strip()
            break

    return focal_user, llm_response


def _parse_and_validate(raw: str) -> Dict[str, Any]:
    """Parse LLM JSON output and validate required fields.

    Attempts to recover from:
    - Leading/trailing markdown fences
    - Partial JSON with only numeric scores (missing text fields)
    """
    # Strip any markdown fences (defensive — Anthropic sometimes adds them)
    cleaned = _strip_markdown(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Last-ditch: try the original raw
        data = json.loads(raw)

    # Provide defaults for optional text fields to avoid hard failures
    if "intent" not in data:
        data["intent"] = ""
    if "reasoning" not in data:
        data["reasoning"] = ""

    # Numeric scores are required
    for key in ("intent_clarity", "outcome_precision"):
        if key not in data:
            raise KeyError(f"Missing required key: {key}")

    # Clamp scores to [0, 1]
    data["intent_clarity"] = max(0.0, min(1.0, float(data["intent_clarity"])))
    data["outcome_precision"] = max(0.0, min(1.0, float(data["outcome_precision"])))
    return data


def _fallback_result(reason: str) -> Dict[str, Any]:
    """Return a below-bar fallback result."""
    logger.warning("IOAS fallback: %s", reason)
    return {
        "passed": False,
        "score": 0.0,
        "intent": "",
        "reasoning": reason,
    }


# ---------------------------------------------------------------------------
# LLM helpers (mirrors grader.py pattern)
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
            logger.warning("IOAS attempt %d/%d failed: %s", attempt + 1, MAX_RETRIES, exc)
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
