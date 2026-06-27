"""
persister.py — Persists grade results to graded_events.jsonl and tracks graded indices.
"""
import json
import os
from typing import Dict, Any, Set
from datetime import datetime, timezone


def load_graded_indices(graded_events_file: str) -> Dict[str, Set[int]]:
    """
    Returns a dict mapping transcript_path -> set of graded start_indices.
    """
    indices: Dict[str, Set[int]] = {}
    if not os.path.exists(graded_events_file):
        return indices
    with open(graded_events_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                path = event.get("transcript_path", "")
                idx = event.get("start_index")
                if path and idx is not None:
                    indices.setdefault(path, set()).add(idx)
            except json.JSONDecodeError:
                continue
    return indices


def persist_grade(
    graded_events_file: str,
    transcript_path: str,
    window: Dict[str, Any],
    grade: Dict[str, Any],
) -> None:
    """Append a grade result to graded_events.jsonl."""
    event = {
        "timestamp": datetime.now(tz=__import__("datetime").timezone.utc).isoformat(),
        "transcript_path": transcript_path,
        "start_index": window["start_index"],
        "end_index": window["end_index"],
        "tier": grade.get("tier"),
        "label": grade.get("label"),
        "score": grade.get("score"),
        "reason": grade.get("reason"),
        "coaching": grade.get("coaching"),
        "better_prompt": grade.get("better_prompt", ""),
        "window_turns": len(window.get("turns", [])),
    }
    os.makedirs(os.path.dirname(graded_events_file), exist_ok=True)
    with open(graded_events_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
