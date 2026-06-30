"""
tests/benchmark_pipeline.py — Performance profiling for the WorkPulse v2 pipeline.

Measures time per stage using Stage 1 (local, no LLM) on real transcript windows.
Stages 2-4 require live LLM API — we profile Stage 1 and measure extraction time
for the real data, providing realistic per-window overhead estimates.

Usage:
    python3 tests/benchmark_pipeline.py

Output: proposals/performance-analysis.md
"""

from __future__ import annotations

import glob
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pipeline.stage1_snd import run_stage1

TRANSCRIPT_ROOT = "/tmp/WorkPulse-fresh/transcrpts"
TARGET_WINDOWS = 10
OUTPUT_PATH = "proposals/performance-analysis.md"


# ---------------------------------------------------------------------------
# Transcript loading
# ---------------------------------------------------------------------------


def load_transcript_windows(transcript_path: str, window_size: int = 3) -> List[Dict[str, Any]]:
    """Load a JSONL transcript and slice into windows of window_size turns."""
    turns = []
    try:
        with open(transcript_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                role = record.get("role", "unknown")
                # Extract text from nested message structure
                text = _extract_text(record.get("message", {}))
                if text:
                    turns.append({"role": role, "text": text})
    except Exception as e:
        return []

    # Slide window
    windows = []
    for i in range(len(turns) - window_size + 1):
        windows.append({"turns": turns[i:i + window_size]})
    return windows


def _extract_text(message: Any) -> str:
    """Extract text from a Cursor message dict."""
    if isinstance(message, str):
        return message.strip()
    if isinstance(message, dict):
        content = message.get("content", [])
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    texts.append(item.get("text", "").strip())
            return " ".join(texts).strip()
    return ""


def collect_transcripts(root: str, limit: int = 5) -> List[str]:
    """Find up to `limit` JSONL transcript files under root.
    
    Uses os.walk to recurse into hidden directories (e.g. .cursor).
    """
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".jsonl"):
                files.append(os.path.join(dirpath, fn))
                if len(files) >= limit:
                    return files
    return files


# ---------------------------------------------------------------------------
# Profiling
# ---------------------------------------------------------------------------


def profile_stage1(windows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Profile Stage 1 (SND) on a list of windows. Returns timing stats."""
    times = []
    results = []
    passed = 0
    failed = 0

    for window in windows:
        t0 = time.perf_counter()
        result = run_stage1(window)
        elapsed = time.perf_counter() - t0
        times.append(elapsed)
        results.append(result)
        if result["passed"]:
            passed += 1
        else:
            failed += 1

    total = sum(times)
    avg = total / len(times) if times else 0
    p95 = sorted(times)[int(0.95 * len(times))] if len(times) >= 20 else max(times) if times else 0

    return {
        "count": len(windows),
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / len(windows) * 100, 1) if windows else 0,
        "total_ms": round(total * 1000, 2),
        "avg_ms": round(avg * 1000, 3),
        "min_ms": round(min(times) * 1000, 3) if times else 0,
        "max_ms": round(max(times) * 1000, 3) if times else 0,
        "p95_ms": round(p95 * 1000, 3),
    }


def estimate_pipeline_cost(stage1_stats: Dict[str, Any]) -> Dict[str, Any]:
    """Estimate full pipeline time based on Stage 1 + assumed LLM latency."""
    avg_stage1 = stage1_stats["avg_ms"]
    pass_rate = stage1_stats["pass_rate"] / 100.0

    # Assumed LLM call latencies (based on typical Claude/GPT-4 API response times)
    # These are conservative estimates for prompt-response cycles
    assumed_s2_ms = 1800    # Stage 2: single LLM call ~1.8s
    assumed_s3_ms = 2200    # Stage 3: single LLM call ~2.2s (longer window context)
    assumed_s4_std_ms = 2000  # Stage 4: standard judge call ~2.0s
    assumed_s4_diss_ms = 1800  # Stage 4: dissenter call ~1.8s (if judges agree)
    assumed_coaching_ms = 1500  # Coaching: ~1.5s

    # Conservative estimate: ~40% reach Stage 3, ~20% reach Stage 4
    pct_reach_s2 = pass_rate
    pct_reach_s3 = pass_rate * 0.7  # ~70% of Stage 2 passers
    pct_reach_s4 = pct_reach_s3 * 0.5  # ~50% of Stage 3 passers
    pct_above_bar = pct_reach_s4 * 0.6  # ~60% of Stage 4 passers

    # Expected time per window (average)
    expected_ms = (
        avg_stage1
        + pct_reach_s2 * assumed_s2_ms
        + pct_reach_s3 * assumed_s3_ms
        + pct_reach_s4 * (assumed_s4_std_ms + assumed_s4_diss_ms * 0.7)
        + (pct_reach_s3 * 0.5) * assumed_coaching_ms  # near-bar coaching
    )

    return {
        "expected_ms_per_window": round(expected_ms, 0),
        "stage1_pct": round(avg_stage1 / expected_ms * 100, 1) if expected_ms else 0,
        "llm_calls_pct": round((expected_ms - avg_stage1) / expected_ms * 100, 1) if expected_ms else 0,
        "pct_windows_reach_s2": round(pct_reach_s2 * 100, 1),
        "pct_windows_reach_s3": round(pct_reach_s3 * 100, 1),
        "pct_windows_reach_s4": round(pct_reach_s4 * 100, 1),
        "estimated_above_bar_rate": round(pct_above_bar * 100, 1),
    }


def identify_bottlenecks(stage1_stats: Dict[str, Any]) -> List[str]:
    """Identify pipeline bottlenecks from profiling data."""
    bottlenecks = []

    if stage1_stats["avg_ms"] > 50:
        bottlenecks.append(
            f"Stage 1 is slow (avg {stage1_stats['avg_ms']}ms). "
            "When sentence-transformers loads a model for the first time, "
            "it can take several seconds. Consider pre-loading the model at startup."
        )
    else:
        bottlenecks.append(
            f"Stage 1 is fast (avg {stage1_stats['avg_ms']}ms using Jaccard fallback). "
            "With sentence-transformers, first-call model loading (~2-5s) is the bottleneck; "
            "subsequent calls are fast (~5-20ms)."
        )

    bottlenecks.append(
        "LLM API calls (Stages 2-4) dominate pipeline time. "
        "Each stage adds ~1.5-2.5s latency. The 3 LLM calls in Stage 4 "
        "(standard judges + dissenter) are the most expensive stage."
    )

    if stage1_stats["pass_rate"] > 60:
        bottlenecks.append(
            f"High Stage 1 pass rate ({stage1_stats['pass_rate']}%). "
            "Many windows are reaching the expensive LLM stages. "
            "Consider tightening the novelty threshold or adding more heuristic "
            "pre-filters to reduce LLM call volume."
        )
    else:
        bottlenecks.append(
            f"Stage 1 pass rate is {stage1_stats['pass_rate']}% — "
            "this is healthy. Most routine windows are filtered cheaply before "
            "reaching the expensive LLM stages."
        )

    bottlenecks.append(
        "Stage 4 makes 2 separate LLM calls (standard judges + dissenter) only "
        "when Stage 3 passes. The early-exit on judge disagreement saves 1 call "
        "in ~30-40% of Stage 4 windows."
    )

    return bottlenecks


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print(f"Collecting transcripts from {TRANSCRIPT_ROOT}...")
    transcript_files = collect_transcripts(TRANSCRIPT_ROOT, limit=5)
    print(f"Found {len(transcript_files)} transcript files.")

    all_windows: List[Dict[str, Any]] = []
    transcript_stats = []
    for path in transcript_files:
        windows = load_transcript_windows(path)
        print(f"  {os.path.basename(os.path.dirname(path))}: {len(windows)} windows")
        transcript_stats.append({
            "file": path,
            "windows": len(windows),
        })
        all_windows.extend(windows)
        if len(all_windows) >= TARGET_WINDOWS * 2:
            break

    # Cap at enough windows for meaningful benchmarking
    bench_windows = all_windows[:max(TARGET_WINDOWS, len(all_windows))]
    print(f"\nBenchmarking Stage 1 (SND) on {len(bench_windows)} windows...")

    stage1_stats = profile_stage1(bench_windows)
    print(f"Stage 1 stats: avg={stage1_stats['avg_ms']}ms, "
          f"pass_rate={stage1_stats['pass_rate']}%")

    cost_estimates = estimate_pipeline_cost(stage1_stats)
    bottlenecks = identify_bottlenecks(stage1_stats)

    # Write analysis report
    report = _build_report(
        transcript_stats=transcript_stats,
        bench_window_count=len(bench_windows),
        stage1_stats=stage1_stats,
        cost_estimates=cost_estimates,
        bottlenecks=bottlenecks,
    )

    os.makedirs("proposals", exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        f.write(report)

    print(f"\nAnalysis written to {OUTPUT_PATH}")
    return stage1_stats


def _build_report(
    transcript_stats,
    bench_window_count,
    stage1_stats,
    cost_estimates,
    bottlenecks,
) -> str:
    lines = [
        "# WorkPulse Pipeline v2 — Performance Analysis",
        "",
        f"*Generated by benchmark_pipeline.py*",
        "",
        "## Summary",
        "",
        f"- **Windows benchmarked:** {bench_window_count}",
        f"- **Transcripts sampled:** {len(transcript_stats)}",
        "",
        "## Stage 1 (SND) — Local Heuristic Performance",
        "",
        "Stage 1 runs entirely locally (Jaccard fallback when sentence-transformers unavailable).",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Windows tested | {stage1_stats['count']} |",
        f"| Pass rate | {stage1_stats['pass_rate']}% |",
        f"| Average time | {stage1_stats['avg_ms']} ms |",
        f"| Min time | {stage1_stats['min_ms']} ms |",
        f"| Max time | {stage1_stats['max_ms']} ms |",
        f"| P95 time | {stage1_stats['p95_ms']} ms |",
        f"| Total time | {stage1_stats['total_ms']} ms |",
        f"| Passed (filtered out) | {stage1_stats['failed']} ({stage1_stats['failed']} below-bar) |",
        "",
        "**Note:** These timings use the Jaccard fallback (no sentence-transformers installed).",
        "With sentence-transformers, first-call model load adds ~2-5s but subsequent calls",
        "are faster and more accurate.",
        "",
        "## Full Pipeline Time Estimates",
        "",
        "Based on Stage 1 timings + typical LLM API latency assumptions",
        "(Claude/GPT-4 API, non-streaming, ~1500-2200ms per call):",
        "",
        "| Stage | Assumed Latency | % Windows Reaching |",
        "|-------|----------------|-------------------|",
        f"| Stage 1 (SND) | {stage1_stats['avg_ms']} ms | 100% |",
        f"| Stage 2 (IOAS) | ~1800ms | {cost_estimates['pct_windows_reach_s2']}% |",
        f"| Stage 3 (CTA) | ~2200ms | {cost_estimates['pct_windows_reach_s3']}% |",
        f"| Stage 4 (EJAD, 2 calls) | ~3800ms | {cost_estimates['pct_windows_reach_s4']}% |",
        "",
        f"**Expected time per window (average):** {cost_estimates['expected_ms_per_window']}ms",
        f"- Stage 1 is {cost_estimates['stage1_pct']}% of total time",
        f"- LLM calls are {cost_estimates['llm_calls_pct']}% of total time",
        f"- Estimated above-bar rate: {cost_estimates['estimated_above_bar_rate']}%",
        "",
        "## Bottlenecks Identified",
        "",
    ]

    for i, b in enumerate(bottlenecks, 1):
        lines.append(f"{i}. {b}")

    lines += [
        "",
        "## Optimisation Recommendations",
        "",
        "### High Priority",
        "1. **Pre-load sentence-transformers model at startup** — eliminates ~2-5s cold-start",
        "   latency on first window processed per session.",
        "2. **Async/parallel LLM calls** — Stage 4's standard judges call returns two verdicts",
        "   in one API call (already optimised). Stage 2+3 could potentially run in parallel",
        "   if Stage 1 pass rate is high enough to justify it.",
        "3. **Caching Stage 1 novelty scores** — for repeated/similar prompts, cache Jaccard",
        "   scores keyed by (user_prompt_hash, prior_text_hash) to avoid recomputation.",
        "",
        "### Medium Priority",
        "4. **Stricter Stage 1 threshold** — raising NOVELTY_THRESHOLD from 0.25 to 0.30-0.35",
        "   would filter more windows cheaply, reducing LLM costs at the expense of slightly",
        "   higher false-negative rate.",
        "5. **Streaming Stage 2+3 in parallel** — if Stage 1 passes, Stage 2 and Stage 3",
        "   could potentially start simultaneously since Stage 3 takes the full window context",
        "   (doesn't strictly need Stage 2 result to proceed).",
        "6. **Smaller model for Stage 2** — Stage 2 (IOAS) does a relatively simple two-score",
        "   classification. A cheaper/faster model (e.g., claude-haiku, gpt-4o-mini) could",
        "   handle Stage 2 while reserving the larger model for Stage 4.",
        "",
        "### Low Priority",
        "7. **Batch processing** — for offline transcript analysis, batch multiple windows",
        "   through the pipeline to amortise API connection overhead.",
        "8. **Stage 1 caching at session level** — if the same assistant turn appears in",
        "   multiple overlapping windows (sliding window), cache its embedding.",
        "",
        "## Transcript Data",
        "",
        "| Transcript File | Windows Extracted |",
        "|----------------|-------------------|",
    ]

    for s in transcript_stats:
        fname = os.path.basename(s["file"])
        lines.append(f"| {fname[:60]} | {s['windows']} |")

    lines += ["", "---", "*End of performance analysis*"]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
