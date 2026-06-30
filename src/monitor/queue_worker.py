"""
queue_worker.py — FCFS grading queue with a single background worker thread.

Windows are submitted via enqueue() and processed sequentially in arrival order.
The main watcher loop never blocks — all API calls happen in the worker thread.
"""

from __future__ import annotations

import json
import logging
import os
import queue
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

if TYPE_CHECKING:
    from src.monitor.overlay import OverlayState

logger = logging.getLogger(__name__)

# Sentinel to signal worker shutdown
_STOP = object()


class GradingWorker:
    """
    Single-threaded FCFS grading worker.

    Parameters
    ----------
    rubric_path:
        Path to the rubric markdown file.
    provider:
        LLM provider (default: ``"anthropic"``).
    model:
        Model name (default: ``"claude-sonnet-4-5"``).
    api_key:
        Anthropic API key (falls back to ANTHROPIC_API_KEY env var).
    on_result:
        Callback invoked with (filepath, window, grade_result) after each grade.
    results_file:
        Path to persist results as JSONL.
    """

    def __init__(
        self,
        rubric_path: str,
        provider: str = "anthropic",
        model: str = "claude-sonnet-4-5",
        api_key: Optional[str] = None,
        on_result: Optional[Callable[[str, Dict[str, Any], Dict[str, Any]], None]] = None,
        results_file: Optional[str] = None,
        overlay_state: "Optional[OverlayState]" = None,
    ):
        self._rubric_path = rubric_path
        self._provider = provider
        self._model = model
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._on_result = on_result
        self._overlay_state = overlay_state
        self._results_file = results_file or str(Path.home() / ".workpulse" / "results.jsonl")
        self._queue: queue.Queue = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._started = False

        # Ensure results dir exists
        Path(self._results_file).parent.mkdir(parents=True, exist_ok=True)

    def start(self) -> None:
        """Start the background worker thread."""
        if self._started:
            return
        self._started = True
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="workpulse-grader"
        )
        self._thread.start()
        logger.info("GradingWorker started.")

    def stop(self, timeout: float = 10.0) -> None:
        """Signal the worker to stop and wait for it to finish."""
        if not self._started:
            return
        self._queue.put(_STOP)
        if self._thread:
            self._thread.join(timeout=timeout)
        logger.info("GradingWorker stopped.")

    def enqueue(self, filepath: str, window: Dict[str, Any]) -> None:
        """Add a window to the grading queue (non-blocking)."""
        self._queue.put((filepath, window))
        logger.debug("Enqueued window from %s (queue size: %d)", filepath, self._queue.qsize())

    # ------------------------------------------------------------------
    # Worker loop
    # ------------------------------------------------------------------

    def _run(self) -> None:
        logger.info("GradingWorker thread running.")
        while True:
            try:
                item = self._queue.get(block=True, timeout=1.0)
            except queue.Empty:
                continue

            if item is _STOP:
                logger.info("GradingWorker received stop signal.")
                break

            filepath, window = item
            try:
                self._grade_one(filepath, window)
            except Exception as exc:
                logger.error("Unhandled error grading window from %s: %s", filepath, exc, exc_info=True)
            finally:
                self._queue.task_done()

    def _grade_one(self, filepath: str, window: Dict[str, Any]) -> None:
        """Grade a single window and dispatch the result."""
        from src.pipeline.grader_v2 import grade_window_v2

        logger.info("Grading window from %s …", os.path.basename(filepath))
        t0 = time.monotonic()

        try:
            result = grade_window_v2(
                window=window,
                rubric_path=self._rubric_path,
                provider=self._provider,
                model=self._model,
                api_key=self._api_key,
            )
        except Exception as exc:
            logger.error("grade_window_v2 failed: %s", exc, exc_info=True)
            return

        elapsed = time.monotonic() - t0
        tier = result.get("tier", "unknown")
        label = result.get("label", "")
        logger.info("Graded in %.1fs → tier=%s label=%s", elapsed, tier, label)

        # Persist result
        self._persist(filepath, window, result)

        # Update overlay state
        if self._overlay_state is not None:
            try:
                self._overlay_state.set_last_graded()
                if result.get("tier") == "above_bar":
                    self._overlay_state.increment_above_bar()
            except Exception as exc:
                logger.debug("overlay_state update failed: %s", exc)

        # Dispatch callback
        if self._on_result:
            try:
                self._on_result(filepath, window, result)
            except Exception as exc:
                logger.error("on_result callback failed: %s", exc)

    def _persist(
        self,
        filepath: str,
        window: Dict[str, Any],
        result: Dict[str, Any],
    ) -> None:
        """Append result to the JSONL results file."""
        from src.monitor.config import extract_project_id
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_file": filepath,
            "project_id": extract_project_id(filepath),
            "tier": result.get("tier"),
            "label": result.get("label"),
            "score": result.get("score"),
            "reason": result.get("reason", ""),
            "coaching": result.get("coaching", ""),
            "better_prompt": result.get("better_prompt", ""),
            "prompt_preview": self._get_prompt_preview(window),
            "pipeline_trace": result.get("pipeline_trace", {}),
            "window": window,
        }
        try:
            with open(self._results_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except OSError as exc:
            logger.error("Failed to persist result: %s", exc)

    @staticmethod
    def _get_prompt_preview(window: Dict[str, Any], max_chars: int = 200) -> str:
        """Return the first user turn text, truncated."""
        for turn in window.get("turns", []):
            if turn.get("role") == "user":
                text = turn.get("text", "").strip()
                if text:
                    return text[:max_chars] + ("…" if len(text) > max_chars else "")
        return ""
