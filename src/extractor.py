"""
extractor.py — Reads Cursor JSONL transcripts and extracts sliding 3-turn windows.
"""
import json
import os
from typing import List, Dict, Any


def load_transcript(path: str) -> List[Dict[str, Any]]:
    """Load all turns from a Cursor JSONL transcript file."""
    turns = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                turns.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return turns


def extract_windows(turns: List[Dict[str, Any]], window_size: int = 3) -> List[Dict[str, Any]]:
    """
    Extract sliding windows of ~window_size turns.
    Each window starts on a user turn.
    Returns list of window dicts with turns + metadata.
    """
    windows = []
    i = 0
    while i < len(turns):
        # Start each window on a user turn
        if turns[i].get("type") != "user" and turns[i].get("role") != "user":
            i += 1
            continue

        window_turns = []
        j = i
        while j < len(turns) and len(window_turns) < window_size:
            window_turns.append(turns[j])
            j += 1

        if len(window_turns) >= 2:  # Need at least user + assistant
            windows.append({
                "turns": window_turns,
                "start_index": i,
                "end_index": j - 1,
            })

        i += 1  # Slide by 1 for overlap

    return windows


def get_new_windows(
    path: str,
    graded_indices: set,
    window_size: int = 3
) -> List[Dict[str, Any]]:
    """
    Load transcript, extract windows, filter out already-graded ones.
    A window is considered graded if its start_index is in graded_indices.
    """
    turns = load_transcript(path)
    all_windows = extract_windows(turns, window_size)
    new_windows = [
        w for w in all_windows
        if w["start_index"] not in graded_indices
    ]
    return new_windows


def get_window_text(window: Dict[str, Any]) -> str:
    """Format a window as readable text for the LLM grader."""
    lines = []
    for turn in window["turns"]:
        role = turn.get("type") or turn.get("role", "unknown")
        text = turn.get("text") or turn.get("content", "")
        # Truncate very long assistant responses
        if role in ("assistant", "ai") and len(text) > 2000:
            text = text[:2000] + "\n[... truncated ...]"
        lines.append(f"[{role.upper()}]\n{text}")
    return "\n\n".join(lines)
