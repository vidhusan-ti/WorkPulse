"""WorkPulse grading pipeline v2.

Public API:
    from src.pipeline import grade_window_v2

    result = grade_window_v2(
        window={"turns": [{"role": "user", "text": "..."}, ...]},
        rubric_path="data/manual_rubric.md",
        provider="openai",  # or "anthropic"
        model="gpt-4o",
        api_key=None,  # falls back to env var
    )
    # result: {"tier": "above_bar"|"near_bar"|"below_bar",
    #          "label": str, "score": int,
    #          "reason": str, "coaching": str, "better_prompt": str,
    #          "pipeline_trace": {...}}

Pipeline stages:
    Stage 1 (SND)  — Semantic Novelty Detection         [local heuristic]
    Stage 2 (IOAS) — Intent-Outcome Alignment Scoring   [single LLM call]
    Stage 3 (CTA)  — Conversation Trajectory Analysis   [single LLM call]
    Stage 4 (EJAD) — Ensemble + Adversarial Dissenter   [two LLM calls]
"""

from src.pipeline.grader_v2 import grade_window_v2
from src.pipeline.stage1_snd import run_stage1
from src.pipeline.stage2_ioas import run_stage2
from src.pipeline.stage3_cta import run_stage3
from src.pipeline.stage4_ejad import run_stage4

__all__ = [
    "grade_window_v2",
    "run_stage1",
    "run_stage2",
    "run_stage3",
    "run_stage4",
]
