"""
stage1_snd.py — Stage 1: Semantic Novelty Detection (SND)

Cheap pre-filter that checks whether the user's prompt introduces genuinely
new semantic content relative to prior LLM (assistant) turns in the window.

The core question: did the user bring something new to the conversation, or
are they just echoing / slightly rephrasing what the LLM already said?

Algorithm:
  1. Embed the user prompt.
  2. Embed each prior assistant turn.
  3. Compute cosine similarity between the user prompt and every prior
     assistant turn.
  4. novelty_score = 1 - max_cosine_similarity
  5. If novelty_score < NOVELTY_THRESHOLD → below_bar

Falls back to Jaccard-distance-based overlap if sentence-transformers is not
available.
"""

from __future__ import annotations

import logging
import math
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Minimum novelty score required to pass Stage 1.
NOVELTY_THRESHOLD: float = 0.25
# Sentence-transformers model used for embedding.
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_stage1(window: Dict[str, Any]) -> Dict[str, Any]:
    """Run Semantic Novelty Detection on a conversation window.

    Parameters
    ----------
    window:
        A conversation window dict with a ``turns`` key containing a list of
        ``{"role": str, "text": str}`` dicts.

    Returns
    -------
    dict
        ``{"passed": bool, "novelty_score": float, "reason": str}``
    """
    turns: List[Dict[str, Any]] = window.get("turns", [])

    # ---- Identify the focal user turn and prior assistant turns ----
    user_prompt, prior_assistant_texts = _split_turns(turns)

    if not user_prompt:
        return {
            "passed": False,
            "novelty_score": 0.0,
            "reason": "No user turn found in window.",
        }

    if not prior_assistant_texts:
        # No prior assistant context → trivially novel.
        return {
            "passed": True,
            "novelty_score": 1.0,
            "reason": "No prior assistant turns to compare against; treating as novel.",
        }

    # ---- Short prompt penalty (handles "yes", "ok", single-word confirmations) ----
    _penalty = _short_prompt_penalty(user_prompt)
    if _penalty is not None:
        passed = _penalty >= NOVELTY_THRESHOLD
        reason = f"Short prompt penalty applied (score={_penalty:.3f}); likely a confirmation or single-word response."
        return {"passed": passed, "novelty_score": _penalty, "reason": reason}

    # ---- Attempt embedding-based novelty ----
    try:
        novelty_score = _embedding_novelty(user_prompt, prior_assistant_texts)
        method = "embedding"
    except Exception as exc:
        logger.warning("sentence-transformers unavailable (%s); falling back to Jaccard.", exc)
        novelty_score = _jaccard_novelty(user_prompt, prior_assistant_texts)
        method = "jaccard"

    passed = novelty_score >= NOVELTY_THRESHOLD
    if passed:
        reason = (
            f"User prompt is semantically novel (score={novelty_score:.3f}, "
            f"threshold={NOVELTY_THRESHOLD}, method={method})."
        )
    else:
        reason = (
            f"User prompt lacks novelty (score={novelty_score:.3f} < "
            f"threshold={NOVELTY_THRESHOLD}, method={method}). "
            "The prompt appears to restate or echo prior LLM output."
        )

    return {
        "passed": passed,
        "novelty_score": round(novelty_score, 4),
        "reason": reason,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _split_turns(
    turns: List[Dict[str, Any]],
) -> tuple[Optional[str], List[str]]:
    """Return (focal_user_prompt, prior_assistant_texts).

    The focal user turn is the first user turn in the window (index 0 is
    typically user in a 3-turn sliding window).  Prior assistant turns are
    all assistant turns that appear *before* the focal user turn.
    """
    focal_user: Optional[str] = None
    prior_assistant: List[str] = []

    # The window typically looks like:
    #   [user_turn_N, assistant_turn_N, user_turn_N+1]
    # We want:
    #   focal = turns[0] (user)
    #   prior = any assistant turns before it (none in a fresh window, but
    #           could exist in longer windows)
    # For safety, collect the *first* user turn and all assistant turns
    # strictly before it.

    focal_index = None
    for i, turn in enumerate(turns):
        if turn.get("role") == "user" and focal_user is None:
            focal_user = turn.get("text", "").strip()
            focal_index = i
            break

    if focal_index is None or not focal_user:
        return None, []

    for turn in turns[:focal_index]:
        if turn.get("role") == "assistant":
            text = turn.get("text", "").strip()
            if text:
                prior_assistant.append(text)

    # Also include any assistant turns that come *after* the focal user turn
    # (i.e. the immediate LLM response in the same window) because novelty
    # relative to the LLM's own output in this window is equally important.
    for turn in turns[focal_index + 1 :]:
        if turn.get("role") == "assistant":
            text = turn.get("text", "").strip()
            if text:
                prior_assistant.append(text)
            # Only take the first assistant response after the focal turn.
            break

    return focal_user, prior_assistant


# ---- Embedding-based novelty ----


def _embedding_novelty(user_prompt: str, prior_texts: List[str]) -> float:
    """Compute novelty score using sentence-transformer embeddings.

    novelty_score = 1 - max(cosine_similarity(user_prompt, prior_text))
    """
    from sentence_transformers import SentenceTransformer  # type: ignore

    model = SentenceTransformer(EMBEDDING_MODEL)
    all_texts = [user_prompt] + prior_texts
    embeddings = model.encode(all_texts, convert_to_numpy=True)

    user_vec = embeddings[0]
    prior_vecs = embeddings[1:]

    max_sim = max(_cosine_similarity(user_vec, pv) for pv in prior_vecs)
    return float(1.0 - max_sim)


def _cosine_similarity(a: "np.ndarray", b: "np.ndarray") -> float:  # noqa: F821
    """Cosine similarity between two numpy vectors."""
    import numpy as np  # type: ignore

    dot = float(np.dot(a, b))
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


# ---- Jaccard-based fallback ----


def _tokenize(text: str) -> set:
    """Lowercase word tokenizer for Jaccard overlap."""
    return set(re.findall(r"\b[a-z0-9]+\b", text.lower()))


def _jaccard_distance(set_a: set, set_b: set) -> float:
    """Jaccard distance = 1 - (|A ∩ B| / |A ∪ B|)."""
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return 1.0 - (intersection / union) if union else 0.0


def _jaccard_novelty(user_prompt: str, prior_texts: List[str]) -> float:
    """Compute novelty score using Jaccard distance as fallback.

    novelty_score = min(jaccard_distance(user_tokens, prior_tokens))
    We take the *min* distance (= least novel comparison) to be conservative.
    """
    user_tokens = _tokenize(user_prompt)
    distances = [_jaccard_distance(user_tokens, _tokenize(pt)) for pt in prior_texts]
    return float(min(distances)) if distances else 1.0


def _short_prompt_penalty(user_prompt: str) -> float:
    """Short prompts (< 5 words) get a novelty penalty — likely confirmations."""
    words = user_prompt.strip().split()
    if len(words) <= 2:
        return 0.05   # "yes", "ok", "sure" → near-zero novelty
    if len(words) <= 4:
        return 0.15   # very short, likely operational
    return None       # no penalty, use normal computation
