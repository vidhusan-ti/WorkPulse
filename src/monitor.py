"""
monitor.py — Main monitor loop. Wires all components together.
"""
import os
import json
import time
import threading
from typing import Dict, Any

from src.watcher import TranscriptWatcher
from src.extractor import get_new_windows
from src.grader import grade_window
from src.pipeline import grade_window_v2
from src.persister import load_graded_indices, persist_grade
from src.notifier import Notifier


class WorkPulseMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_dir = config.get("data_dir", "data")
        self.graded_events_file = config.get("graded_events_file", "data/graded_events.jsonl")
        self.portfolio_file = config.get("portfolio_file", "data/portfolio.md")
        self.rubric_file = config.get("rubric_file", "data/manual_rubric.md")
        self.transcript_glob = config.get("transcript_glob", "")
        self.check_interval = config.get("check_interval_seconds", 60)
        self.inactive_minutes = config.get("inactive_after_minutes", 10)
        self.max_grades_per_cycle = config.get("llm_max_grades_per_cycle", 3)

        self.llm_provider = config.get("llm_provider", "openai")
        self.llm_model = config.get("llm_model", "gpt-4o")
        self.llm_api_key = config.get("llm_api_key") or os.environ.get(
            config.get("llm_api_key_env", "OPENAI_API_KEY")
        )
        # Feature flag: use 4-stage pipeline v2 (default: True)
        self.use_pipeline_v2 = config.get("use_pipeline_v2", True)

        self.notifier = Notifier(self.portfolio_file, self.inactive_minutes)
        self._graded_indices: Dict[str, set] = {}
        self._lock = threading.Lock()
        self._pending_paths = set()

    def start(self):
        print("[WorkPulse] Starting monitor...")

        # Load existing graded indices
        self._graded_indices = load_graded_indices(self.graded_events_file)

        # Start inactivity timer
        self.notifier.start_inactivity_timer()

        # Start file watcher
        self._watcher = TranscriptWatcher(
            transcript_glob=self.transcript_glob,
            on_transcript_changed=self._on_transcript_changed,
            poll_interval=self.check_interval,
        )
        self._watcher.start()

        print(f"[WorkPulse] Watching: {self.transcript_glob}")
        print(f"[WorkPulse] Inactivity nudge after: {self.inactive_minutes} minutes")
        print("[WorkPulse] Running. Press Ctrl+C to stop.")

        try:
            while True:
                self._process_pending()
                time.sleep(5)
        except KeyboardInterrupt:
            print("[WorkPulse] Stopping...")
            self._watcher.stop()
            self.notifier.stop()

    def _on_transcript_changed(self, path: str):
        with self._lock:
            self._pending_paths.add(path)

    def _process_pending(self):
        with self._lock:
            paths = list(self._pending_paths)
            self._pending_paths.clear()

        for path in paths:
            self._process_transcript(path)

    def _process_transcript(self, path: str):
        graded = self._graded_indices.get(path, set())
        try:
            windows = get_new_windows(path, graded, window_size=3)
        except Exception as e:
            print(f"[WorkPulse] Error reading {path}: {e}")
            return

        if not windows:
            return

        # Limit grades per cycle to control LLM costs
        windows = windows[:self.max_grades_per_cycle]

        for window in windows:
            try:
                print(f"[WorkPulse] Grading window at index {window['start_index']} in {os.path.basename(path)}")
                if self.use_pipeline_v2:
                    grade = grade_window_v2(
                        window,
                        rubric_path=self.rubric_file,
                        provider=self.llm_provider,
                        model=self.llm_model,
                        api_key=self.llm_api_key,
                    )
                else:
                    grade = grade_window(
                        window,
                        rubric_path=self.rubric_file,
                        provider=self.llm_provider,
                        model=self.llm_model,
                        api_key=self.llm_api_key,
                    )

                persist_grade(self.graded_events_file, path, window, grade)
                self._graded_indices.setdefault(path, set()).add(window["start_index"])

                tier = grade.get("tier", "below_bar")
                print(f"[WorkPulse] → {tier} (score: {grade.get('score', '?')})")

                self.notifier.handle_grade(window, grade)

            except Exception as e:
                print(f"[WorkPulse] Error grading window: {e}")


def load_config(config_path: str = "config/settings.json") -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)
