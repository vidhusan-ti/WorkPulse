"""
grader.py — LLM-backed grader using manual_rubric.md as system prompt.
Returns tier (above_bar / near_bar / below_bar), reason, and coaching.
"""
import json
import os
import time
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

Respond ONLY with valid JSON in this exact format (no markdown, no code fences, just raw JSON):
{{
  "tier": "above_bar",
  "label": "outstanding_portfolio",
  "score": 8,
  "reason": "one paragraph explaining the grade",
  "coaching": "",
  "better_prompt": ""
}}

Tier must be exactly one of: above_bar, near_bar, below_bar
Label must be exactly one of: mindblowing_portfolio, outstanding_portfolio, strong_highlight, mindblowing_highlight, below_bar

Tier mapping:
- above_bar: use mindblowing_portfolio (9-10) or outstanding_portfolio (7-8)
- near_bar: use mindblowing_highlight (5-6) or strong_highlight (4-5)
- below_bar: use below_bar (0-3)

coaching and better_prompt: fill only for near_bar, leave empty string for others.
"""


def _fallback_grade() -> Dict[str, Any]:
    return {
        "tier": "below_bar",
        "label": "below_bar",
        "score": 0,
        "reason": "Grader returned empty response.",
        "coaching": "",
        "better_prompt": "",
    }


def grade_window(
    window: Dict[str, Any],
    rubric_path: str,
    provider: str = "anthropic",
    model: str = "claude-sonnet-4-5",
    api_key: str = None,
    max_retries: int = 3,
) -> Dict[str, Any]:
    rubric = load_rubric(rubric_path)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(rubric=rubric)
    window_text = get_window_text(window)
    user_message = f"Grade this conversation window:\n\n{window_text}"

    for attempt in range(max_retries):
        try:
            if provider == "openai":
                result = _grade_openai(system_prompt, user_message, model, api_key)
            elif provider == "anthropic":
                result = _grade_anthropic(system_prompt, user_message, model, api_key)
            else:
                raise ValueError(f"Unknown provider: {provider}")

            # Validate required fields
            if "tier" not in result:
                raise ValueError("Missing 'tier' in grade response")
            if result["tier"] not in ("above_bar", "near_bar", "below_bar"):
                raise ValueError(f"Invalid tier: {result['tier']}")

            return result

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            print(f"[grader] Warning: parse error after {max_retries} attempts: {e}")
            return _fallback_grade()
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            print(f"[grader] Error: {e}")
            return _fallback_grade()

    return _fallback_grade()


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
    if not raw or not raw.strip():
        raise ValueError("Empty response from OpenAI")
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
    raw = response.content[0].text if response.content else ""
    if not raw or not raw.strip():
        raise ValueError("Empty response from Anthropic")

    # Strip markdown code fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)
