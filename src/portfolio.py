"""
portfolio.py — Writes approved above-bar windows to portfolio.md.
"""
import os
from datetime import datetime, timezone
from typing import Dict, Any

from src.extractor import get_window_text
from src.persister import _focal_prompt_hash, _summarise_trace


def _stage_summary_line(trace_summary: Dict[str, Any]) -> str:
    """Format pipeline trace summary as a compact one-line string."""
    parts = []
    if "s1_novelty" in trace_summary:
        parts.append(f"S1 novelty={trace_summary['s1_novelty']:.2f}")
    if "s2_score" in trace_summary:
        parts.append(f"S2 score={trace_summary['s2_score']:.2f}")
    if "s3_delta" in trace_summary:
        parts.append(f"S3 Δ={trace_summary['s3_delta']}")
    if "s4_passed" in trace_summary:
        parts.append(f"S4 pass={trace_summary['s4_passed']}")
    return " | ".join(parts) if parts else "pipeline trace unavailable"


def append_to_portfolio(portfolio_file: str, window: Dict[str, Any], grade: Dict[str, Any]) -> None:
    """Append an approved portfolio entry to portfolio.md."""
    os.makedirs(os.path.dirname(portfolio_file), exist_ok=True)

    # Create file with header if it doesn't exist
    if not os.path.exists(portfolio_file):
        with open(portfolio_file, "w", encoding="utf-8") as f:
            f.write("# Portfolio — WorkPulse\n\nApproved above-bar conversation windows.\n\n")

    window_text = get_window_text(window)
    focal_hash = _focal_prompt_hash(window)
    trace = grade.get("pipeline_trace", {})
    trace_summary = _summarise_trace(trace) if trace else {}
    stage_line = _stage_summary_line(trace_summary)
    date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    entry = f"""
---

## {grade.get("label", "above_bar").replace("_", " ").title()} | Score: {grade.get("score", "?")}/10
**Date:** {date_str}
**Hash:** `{focal_hash}`
**Pipeline:** {stage_line}

**Why it passed:**
{grade.get("reason", "")}

**Conversation:**

{window_text}

"""
    with open(portfolio_file, "a", encoding="utf-8") as f:
        f.write(entry)
