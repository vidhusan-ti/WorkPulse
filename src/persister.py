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


def _focal_prompt_hash(window: Dict[str, Any]) -> str:
    """Return a short hash of the focal user prompt for deduplication.
    
    The focal prompt is the first user turn in the window.
    Used by SWOD (Proposal 12) to deduplicate overlapping windows
    that share the same focal user turn.
    """
    import hashlib
    focal_text = ""
    for turn in window.get("turns", []):
        if turn.get("role") == "user":
            focal_text = turn.get("text", "").strip().lower()
            break
    return hashlib.sha256(focal_text.encode()).hexdigest()[:16]


def _summarise_trace(pipeline_trace: Dict[str, Any]) -> Dict[str, Any]:
    """Produce a compact summary of the pipeline trace for storage."""
    summary = {}
    s1 = pipeline_trace.get("stage1_snd", {})
    if s1:
        summary["s1_passed"] = s1.get("passed")
        summary["s1_novelty"] = s1.get("novelty_score")
    s2 = pipeline_trace.get("stage2_ioas", {})
    if s2:
        summary["s2_passed"] = s2.get("passed")
        summary["s2_score"] = s2.get("score")
    s3 = pipeline_trace.get("stage3_cta", {})
    if s3:
        summary["s3_tier"] = s3.get("tier")
        summary["s3_delta"] = s3.get("trajectory_delta")
    s4 = pipeline_trace.get("stage4_ejad", {})
    if s4:
        summary["s4_passed"] = s4.get("passed")
    return summary


def persist_grade(
    graded_events_file: str,
    transcript_path: str,
    window: Dict[str, Any],
    grade: Dict[str, Any],
) -> None:
    """Append a grade result to graded_events.jsonl.
    
    Includes focal_prompt_hash for SWOD deduplication (Proposal 12).
    Includes pipeline_trace_summary for compact storage.
    """
    event = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "transcript_path": transcript_path,
        "start_index": window.get("start_index"),
        "end_index": window.get("end_index"),
        "focal_prompt_hash": _focal_prompt_hash(window),
        "tier": grade.get("tier"),
        "label": grade.get("label"),
        "score": grade.get("score"),
        "reason": grade.get("reason"),
        "coaching": grade.get("coaching"),
        "better_prompt": grade.get("better_prompt", ""),
        "window_turns": len(window.get("turns", [])),
        "pipeline_trace_summary": _summarise_trace(grade.get("pipeline_trace", {})),
    }
    _dir = os.path.dirname(graded_events_file)
    if _dir:
        os.makedirs(_dir, exist_ok=True)
    with open(graded_events_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def deduplicate_session_grades(grades: list) -> list:
    """Deduplicate graded windows sharing the same focal user prompt.
    
    Implements SWOD (Proposal 12): when multiple overlapping windows share
    the same focal user turn, keep only the highest-scoring grade.
    
    Parameters
    ----------
    grades:
        List of grade result dicts with "focal_prompt_hash" and "score".
    
    Returns
    -------
    list
        Deduplicated, keeping highest score per unique focal prompt.
    """
    seen: Dict[str, Dict[str, Any]] = {}
    for grade in grades:
        hash_key = grade.get("focal_prompt_hash", "")
        if not hash_key:
            continue
        if hash_key not in seen or grade.get("score", 0) > seen[hash_key].get("score", 0):
            seen[hash_key] = grade
    return list(seen.values())
