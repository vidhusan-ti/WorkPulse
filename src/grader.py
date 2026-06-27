"""
grader.py — LLM-backed grader using manual_rubric.md as system prompt.
Returns tier (above_bar / near_bar / below_bar), reason, and coaching.
"""
import json
import os
from typing import Dict, Any

from src.extractor import get_window_text

RUBRIC_CACHE = {}


def load_rubric(rubric_path: str) -> str:
    if rubric_path not in RUBRIC_CACHE:
        with open(rubric_path, "r", encoding="utf-8") as f:
            RUBRIC_CACHE[rubric_path] = f.read()
    return RUBRIC_CACHE[rubric_path]


SYSTEM_PROMPT_TEMPLATE = """{rubric}

---

You are grading a window of a Cursor conversation.

Respond ONLY with valid JSON in this exact format:
{{
  "tier": "above_bar" | "near_bar" | "below_bar",
  "label": "mindblowing_portfolio" | "outstanding_portfolio" | "strong_highlight" | "mindblowing_highlight" | "below_bar",
  "score": <integer 0-10>,
  "reason": "<one paragraph explaining the grade>",
  "coaching": "<specific coaching note for the user — what was missing and why>",
  "better_prompt": "<a concrete example of a stronger version of the user's last prompt, or empty string if above_bar>"
}}

Tier mapping:
- above_bar: mindblowing_portfolio or outstanding_portfolio
- near_bar: strong_highlight or mindblowing_highlight  
- below_bar: below_bar

Do not include any text outside the JSON object.
"""


def grade_window(
    window: Dict[str, Any],
    rubric_path: str,
    provider: str = "openai",
    model: str = "gpt-4o",
    api_key: str = None,
) -> Dict[str, Any]:
    """
    Grade a conversation window using the LLM.
    Returns grade dict with tier, label, score, reason, coaching, better_prompt.
    """
    rubric = load_rubric(rubric_path)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(rubric=rubric)
    window_text = get_window_text(window)

    user_message = f"Grade this conversation window:\n\n{window_text}"

    if provider == "openai":
        return _grade_openai(system_prompt, user_message, model, api_key)
    elif provider == "anthropic":
        return _grade_anthropic(system_prompt, user_message, model, api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def _grade_openai(system_prompt: str, user_message: str, model: str, api_key: str) -> Dict[str, Any]:
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("openai package not installed. Run: pip install openai")

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
    return json.loads(raw)


def _grade_anthropic(system_prompt: str, user_message: str, model: str, api_key: str) -> Dict[str, Any]:
    try:
        import anthropic
    except ImportError:
        raise ImportError("anthropic package not installed. Run: pip install anthropic")

    client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    raw = response.content[0].text
    # Strip any markdown code fences if present
    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    return json.loads(raw)
