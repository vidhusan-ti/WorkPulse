"""
stage4_ejad.py — Stage 4: Ensemble + Adversarial Dissenter (EJAD)

Final validation gate, only reached by above_bar_candidates from Stage 3.

Core rubric question: Did the user drive the LLM, or did the LLM drive the user?
This stage uses two standard judges and one adversarial dissenter to ensure
that only genuinely user-driven, non-trivial prompts reach above-bar.

Architecture (cost-efficient dual-role design):
  1. STANDARD JUDGE call: one LLM call instructed to play *two* standard
     judges and return both verdicts in a single JSON response.
  2. DISSENTER call: a separate adversarial LLM call that actively searches
     for every reason this should NOT be above-bar.
  3. META-CHECK: inline logic (no extra LLM call) rates whether the
     dissenter's objection is "weak" or "strong" based on the dissenter's
     own confidence score.

Above-bar requires:
  - Both standard judges agree it is above-bar.
  - Dissenter's objection is rated "weak" (confidence ≤ 0.4).

If either condition fails → near_bar (not below_bar; Stage 3 already
established it's at least near_bar quality).
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

MAX_RETRIES: int = 3

# Dissenter confidence threshold: at or below this → objection is "weak".
DISSENTER_WEAK_THRESHOLD: float = 0.4

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

STANDARD_JUDGE_SYSTEM = """\
You are TWO independent expert conversation quality judges (Judge A and Judge B).
Each judge independently evaluates whether the focal user prompt is genuinely
above-bar according to the rubric below.

RUBRIC — Above-bar requires ALL of the following:
1. USER-DRIVEN: The user steered the conversation, not the LLM.
2. GENUINE INSIGHT: The prompt introduces real thinking, not surface filler.
3. USER-ORIGINATED: The content is the user's own — not restating LLM output.
4. NOT MISDIRECTED: The prompt moves toward the correct goal.
5. EFFICIENT: No repeated corrections for the same problem.
6. NOT JUST RESTRUCTURING: Not merely reformatting or reorganising LLM output.

Each judge returns an independent verdict with reasoning.

Respond ONLY with valid JSON — no markdown, no code fences:
{
  "judge_a": {
    "verdict": "<above_bar|not_above_bar>",
    "confidence": <float 0.0–1.0>,
    "reasoning": "<one sentence>"
  },
  "judge_b": {
    "verdict": "<above_bar|not_above_bar>",
    "confidence": <float 0.0–1.0>,
    "reasoning": "<one sentence>"
  }
}
"""

STANDARD_JUDGE_USER_TEMPLATE = """\
CONVERSATION WINDOW:

{conversation_text}

FOCAL USER PROMPT (the turn being graded):
{focal_user_prompt}

Judge A and Judge B: independently evaluate whether this focal prompt is
above-bar per the rubric.
"""

DISSENTER_SYSTEM = """\
You are an adversarial dissenter. Your job is to find EVERY reason why the
focal user prompt should NOT be rated above-bar.

Core question: Was the LLM driving the user, or the user driving the LLM?

Be ruthless. Look specifically for these WorkPulse anti-patterns:

TIER 1 — DEFINITIVE BELOW-BAR (any of these alone disqualifies):
1. User restating what LLM just said — near-verbatim or paraphrase of prior assistant turn
2. User just approving LLM suggestion — "looks good", "yes that works", "go ahead"
3. User asking operational/debugging questions — "can you add a test?", "why is this failing?"
4. Good prompt STRUCTURE but LLM supplied the core insight — user just packaged LLM content
5. Repeated correction of same issue without fixing root cause — user is stuck, not driving

TIER 2 — STRONG OBJECTIONS (require further scrutiny):
6. User being led by LLM (LLM-driven pattern) — user's direction came from LLM suggestion
7. Misdirection: user pursuing wrong goal or wrong approach
8. Padding: filler words, unnecessary elaboration adding no value
9. False insight: something that looks like insight but is obvious or trivial
10. Pure restructuring: just reorganising what the LLM already said

Rate your confidence that this prompt is NOT above-bar (0.0=definitely above-bar, 1.0=definitely NOT).

Respond ONLY with valid JSON — no markdown, no code fences:
{
  "objections": ["<objection 1>", "<objection 2>", ...],
  "confidence_not_above_bar": <float 0.0-1.0>,
  "summary": "<one paragraph summarising the strongest objection>"
}
"""

DISSENTER_USER_TEMPLATE = """\
CONVERSATION WINDOW:

{conversation_text}

FOCAL USER PROMPT (the turn being graded):
{focal_user_prompt}

Find every reason this should NOT be above-bar.
"""

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_stage4(
    window: Dict[str, Any],
    provider: str,
    model: str,
    api_key: Optional[str] = None,
    rubric_context: Optional[str] = None,
) -> Dict[str, Any]:
    """Run Ensemble + Adversarial Dissenter validation.

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
    rubric_context:
        Optional rubric text to prepend to the system prompts.

    Returns
    -------
    dict
        ``{"passed": bool, "standard_verdict": str,
           "dissenter_objection": str, "final_reasoning": str}``
    """
    turns: List[Dict[str, Any]] = window.get("turns", [])
    focal_user_prompt = _get_focal_user_prompt(turns)

    if not focal_user_prompt:
        return _fallback_result("No user turn found in window.")

    conversation_text = _format_conversation(turns)

    # ---- Standard judges (dual-role, single call) ----
    _standard_system = STANDARD_JUDGE_SYSTEM
    _dissenter_system = DISSENTER_SYSTEM
    if rubric_context:
        _rubric_prefix = (
            "MANUAL GRADING RUBRIC (authoritative reference — apply these criteria):\n"
            + rubric_context
            + "\n\n---\n\n"
        )
        _standard_system = _rubric_prefix + STANDARD_JUDGE_SYSTEM
        _dissenter_system = _rubric_prefix + DISSENTER_SYSTEM

    standard_raw = _call_llm_with_retry(
        system_prompt=_standard_system,
        user_message=STANDARD_JUDGE_USER_TEMPLATE.format(
            conversation_text=conversation_text,
            focal_user_prompt=focal_user_prompt,
        ),
        provider=provider,
        model=model,
        api_key=api_key,
    )

    if standard_raw is None:
        return _fallback_result("Standard judge LLM call failed after retries.")

    try:
        standard_result = _parse_standard_judges(standard_raw)
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.error("EJAD standard judge parse error: %s | raw=%r", exc, standard_raw)
        return _fallback_result(f"Standard judge parse error: {exc}")

    judges_agree = (
        standard_result["judge_a"]["verdict"] == "above_bar"
        and standard_result["judge_b"]["verdict"] == "above_bar"
    )

    standard_verdict = _summarise_standard_verdict(standard_result)

    # If both judges already disagree, we can skip the dissenter to save cost.
    if not judges_agree:
        return {
            "passed": False,
            "failure_mode": "judge_disagreement",
            "standard_verdict": standard_verdict,
            "dissenter_objection": "Skipped (judges did not agree).",
            "final_reasoning": (
                "Both standard judges did not agree this is above-bar. "
                f"Judge A: {standard_result['judge_a']['verdict']} "
                f"({standard_result['judge_a']['reasoning']}). "
                f"Judge B: {standard_result['judge_b']['verdict']} "
                f"({standard_result['judge_b']['reasoning']})."
            ),
        }

    # ---- Dissenter (separate adversarial call) ----
    dissenter_raw = _call_llm_with_retry(
        system_prompt=_dissenter_system,
        user_message=DISSENTER_USER_TEMPLATE.format(
            conversation_text=conversation_text,
            focal_user_prompt=focal_user_prompt,
        ),
        provider=provider,
        model=model,
        api_key=api_key,
    )

    if dissenter_raw is None:
        # If dissenter fails, be conservative: don't promote to above-bar.
        return _fallback_result("Dissenter LLM call failed after retries.")

    try:
        dissenter_result = _parse_dissenter(dissenter_raw)
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.error("EJAD dissenter parse error: %s | raw=%r", exc, dissenter_raw)
        return _fallback_result(f"Dissenter parse error: {exc}")

    dissenter_confidence = dissenter_result["confidence_not_above_bar"]
    dissenter_objection_weak = dissenter_confidence <= DISSENTER_WEAK_THRESHOLD

    passed = judges_agree and dissenter_objection_weak

    dissenter_objection = dissenter_result["summary"]
    if dissenter_result.get("objections"):
        top_objections = "; ".join(dissenter_result["objections"][:3])
        dissenter_objection = f"{dissenter_objection} [Top objections: {top_objections}]"

    if passed:
        final_reasoning = (
            f"Both standard judges agreed (above-bar) and dissenter objection "
            f"was weak (confidence={dissenter_confidence:.2f} ≤ {DISSENTER_WEAK_THRESHOLD}). "
            f"Standard verdict: {standard_verdict}."
        )
        failure_mode = None
    else:
        if not dissenter_objection_weak:
            final_reasoning = (
                f"Dissenter raised strong objections "
                f"(confidence={dissenter_confidence:.2f} > {DISSENTER_WEAK_THRESHOLD}): "
                f"{dissenter_result['summary']}"
            )
            failure_mode = "strong_dissenter"
        else:
            final_reasoning = (
                f"Standard judges did not unanimously agree. {standard_verdict}"
            )
            failure_mode = "judge_disagreement"

    result = {
        "passed": passed,
        "standard_verdict": standard_verdict,
        "dissenter_objection": dissenter_objection,
        "final_reasoning": final_reasoning,
    }
    if failure_mode is not None:
        result["failure_mode"] = failure_mode
    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_focal_user_prompt(turns: List[Dict[str, Any]]) -> Optional[str]:
    """Return the text of the first user turn."""
    for turn in turns:
        if turn.get("role") == "user":
            text = turn.get("text", "").strip()
            if text:
                return text
    return None


def _format_conversation(turns: List[Dict[str, Any]]) -> str:
    """Format turns as a readable conversation transcript."""
    lines: List[str] = []
    for turn in turns:
        role = turn.get("role", "unknown").upper()
        text = turn.get("text", "").strip()
        if text:
            lines.append(f"[{role}]\n{text}")
    return "\n\n".join(lines)


def _parse_standard_judges(raw: str) -> Dict[str, Any]:
    """Parse and validate standard judges JSON response."""
    cleaned = _strip_markdown(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        data = json.loads(raw)
    for judge_key in ("judge_a", "judge_b"):
        if judge_key not in data:
            raise KeyError(f"Missing key: {judge_key}")
        judge = data[judge_key]
        for field in ("verdict", "confidence", "reasoning"):
            if field not in judge:
                raise KeyError(f"Missing {judge_key}.{field}")
        if judge["verdict"] not in ("above_bar", "not_above_bar"):
            raise ValueError(f"Invalid verdict in {judge_key}: {judge['verdict']!r}")
        judge["confidence"] = max(0.0, min(1.0, float(judge["confidence"])))
    return data


def _parse_dissenter(raw: str) -> Dict[str, Any]:
    """Parse and validate dissenter JSON response."""
    cleaned = _strip_markdown(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        data = json.loads(raw)
    for field in ("objections", "confidence_not_above_bar", "summary"):
        if field not in data:
            raise KeyError(f"Missing key: {field}")
    data["confidence_not_above_bar"] = max(
        0.0, min(1.0, float(data["confidence_not_above_bar"]))
    )
    if not isinstance(data["objections"], list):
        data["objections"] = [str(data["objections"])]
    return data


def _summarise_standard_verdict(result: Dict[str, Any]) -> str:
    """Produce a human-readable summary of the standard judges' verdicts."""
    a = result["judge_a"]
    b = result["judge_b"]
    return (
        f"Judge A: {a['verdict']} (conf={a['confidence']:.2f}; {a['reasoning']}). "
        f"Judge B: {b['verdict']} (conf={b['confidence']:.2f}; {b['reasoning']})."
    )


def _fallback_result(reason: str) -> Dict[str, Any]:
    """Return a failed (near-bar) fallback result on error."""
    logger.warning("EJAD fallback: %s", reason)
    return {
        "passed": False,
        "standard_verdict": "",
        "dissenter_objection": "",
        "final_reasoning": reason,
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
            logger.warning("EJAD attempt %d/%d failed: %s", attempt + 1, MAX_RETRIES, exc)
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
