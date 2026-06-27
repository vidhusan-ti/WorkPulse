"""
portfolio.py — Writes approved above-bar windows to portfolio.md.
"""
import os
from datetime import datetime
from typing import Dict, Any

from src.extractor import get_window_text


def append_to_portfolio(portfolio_file: str, window: Dict[str, Any], grade: Dict[str, Any]) -> None:
    """Append an approved portfolio entry to portfolio.md."""
    os.makedirs(os.path.dirname(portfolio_file), exist_ok=True)

    # Create file with header if it doesn't exist
    if not os.path.exists(portfolio_file):
        with open(portfolio_file, "w", encoding="utf-8") as f:
            f.write("# Portfolio — WorkPulse\n\nApproved above-bar conversation windows.\n\n")

    window_text = get_window_text(window)
    entry = f"""
---

## {grade.get('label', 'above_bar').replace('_', ' ').title()} | Score: {grade.get('score', '?')}/10
**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

**Why it passed:**
{grade.get('reason', '')}

**Conversation:**

{window_text}

"""
    with open(portfolio_file, "a", encoding="utf-8") as f:
        f.write(entry)
