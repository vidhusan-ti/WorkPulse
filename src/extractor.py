"""
extractor.py — Reads Cursor JSONL transcripts and extracts sliding 3-turn windows.
Handles both Cursor JSONL formats:
  - Format A: {"type": "user", "text": "..."}
  - Format B: {"role": "user", "message": {"content": [{"type": "text", "text": "..."}]}}
"""
import json
import os
from typing import List, Dict, Any


def _normalise_turn(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise any Cursor turn format into {role, text}."""
    # Format B: {"role": ..., "message": {"content": [...]}}
    if "role" in raw and "message" in raw:
        role = raw["role"]
        content = raw["message"].get("content", [])
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        return {"role": role, "text": "\n".join(text_parts).strip()}

    # Format A: {"type": "user"/"assistant", "text": "..."}
    if "type" in raw:
        role = raw["type"]
        text = raw.get("text", raw.get("content", ""))
        return {"role": role, "text": text}

    # Fallback
    return {"role": raw.get("role", "unknown"), "text": str(raw)}


def load_transcript(path: str) -> List[Dict[str, Any]]:
    """Load and normalise all turns from a Cursor JSONL transcript file."""
    turns = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
                turn = _normalise_turn(raw)
                # Only keep user/assistant turns with text content
                if turn["role"] in ("user", "assistant") and turn["text"]:
                    turns.append(turn)
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
        if turns[i].get("role") != "user":
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
        role = turn.get("role", "unknown").upper()
        text = _clean_text(turn.get("text", ""))
        # Truncate very long assistant responses
        if role == "ASSISTANT" and len(text) > 2000:
            text = text[:2000] + "\n[... truncated ...]"
        lines.append(f"[{role}]\n{text}")
    return "\n\n".join(lines)


def _clean_text(text: str) -> str:
    """Strip Cursor metadata tags from user text for cleaner grading."""
    import re
    # Remove <timestamp>...</timestamp>
    text = re.sub(r'<timestamp>.*?</timestamp>', '', text, flags=re.DOTALL)
    # Remove <user_query> tags but keep content
    text = re.sub(r'<user_query>\s*', '', text)
    text = re.sub(r'\s*</user_query>', '', text)
    return text.strip()
