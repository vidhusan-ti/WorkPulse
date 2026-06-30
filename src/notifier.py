"""
notifier.py — Routes grade results to the right popup and manages the 10-min inactivity timer.
"""
import time
import threading
from typing import Dict, Any, Callable

from src.popup import show_above_bar_popup, show_near_bar_popup, show_inactivity_nudge
from src.extractor import get_window_text
from src.portfolio import append_to_portfolio


class Notifier:
    def __init__(self, portfolio_file: str, inactive_after_minutes: int = 10):
        self.portfolio_file = portfolio_file
        self.inactive_threshold = inactive_after_minutes * 60  # seconds
        self._last_signal_time = time.time()
        self._timer_thread: threading.Thread = None
        self._running = False

    def start_inactivity_timer(self):
        """Start background thread that nudges user after inactivity threshold."""
        self._running = True
        self._timer_thread = threading.Thread(target=self._inactivity_loop, daemon=True)
        self._timer_thread.start()

    def stop(self):
        self._running = False

    def _inactivity_loop(self):
        while self._running:
            time.sleep(30)  # Check every 30 seconds
            elapsed = time.time() - self._last_signal_time
            if elapsed >= self.inactive_threshold:
                show_inactivity_nudge()
                self._last_signal_time = time.time()  # Reset after nudge

    def _reset_timer(self):
        """Call this when an above-bar or near-bar window is found."""
        self._last_signal_time = time.time()

    def handle_grade(self, window: Dict[str, Any], grade: Dict[str, Any]) -> None:
        """Route grade result to appropriate popup."""
        tier = grade.get("tier", "below_bar")

        if tier == "above_bar":
            self._reset_timer()
            window_text = get_window_text(window)

            def on_approve():
                append_to_portfolio(self.portfolio_file, window, grade)

            def on_reject():
                pass  # User declined — do nothing

            show_above_bar_popup(grade, window_text, on_approve, on_reject)

        elif tier == "near_bar":
            self._reset_timer()
            show_near_bar_popup(grade)

        # below_bar: silently ignored
