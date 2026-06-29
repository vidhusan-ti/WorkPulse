"""
watcher.py — Watchdog-based file watcher + incremental JSONL reader.

Watches a directory tree recursively for new/modified .jsonl files.
For each change, reads only the new bytes since the last bookmark offset,
parses new JSONL lines, extracts conversation windows, and submits them
to the grading queue after the SND fast-path pre-filter.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.extractor import extract_windows, _normalise_turn
from src.monitor.bookmarks import BookmarkStore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Attempt to import watchdog; fall back to polling if unavailable
# ---------------------------------------------------------------------------

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logger.warning("watchdog not installed; falling back to polling watcher.")


# ---------------------------------------------------------------------------
# Incremental JSONL reader
# ---------------------------------------------------------------------------

class IncrementalJSONLReader:
    """Reads only new lines from a JSONL file since the last byte offset."""

    def __init__(self, bookmarks: BookmarkStore):
        self._bookmarks = bookmarks

    def read_new_turns(self, filepath: str) -> List[Dict[str, Any]]:
        """Return new normalised turns from *filepath* since last bookmark.

        Updates the bookmark after a successful read.
        Returns an empty list if no new content or file is unreadable.
        """
        abs_path = os.path.abspath(filepath)
        offset = self._bookmarks.get(abs_path)

        try:
            file_size = os.path.getsize(abs_path)
        except OSError:
            return []

        if file_size <= offset:
            # File may have been truncated/rotated — reset bookmark
            if file_size < offset:
                logger.debug("File shrank (%s); resetting bookmark.", abs_path)
                self._bookmarks.set(abs_path, 0)
                offset = 0
            else:
                return []  # Nothing new

        new_turns: List[Dict[str, Any]] = []
        try:
            with open(abs_path, "rb") as f:
                f.seek(offset)
                raw_bytes = f.read()
                new_offset = offset + len(raw_bytes)
        except OSError as exc:
            logger.warning("Could not read %s: %s", abs_path, exc)
            return []

        # Parse new lines
        text = raw_bytes.decode("utf-8", errors="replace")
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
                turn = _normalise_turn(raw)
                if turn["role"] in ("user", "assistant") and turn["text"]:
                    new_turns.append(turn)
            except json.JSONDecodeError:
                continue

        # Update bookmark
        self._bookmarks.set(abs_path, new_offset)
        logger.debug("Read %d new turns from %s (offset %d→%d)",
                     len(new_turns), abs_path, offset, new_offset)
        return new_turns


# ---------------------------------------------------------------------------
# SND fast-path pre-filter (local, no API)
# ---------------------------------------------------------------------------

def _snd_passes(window: Dict[str, Any]) -> bool:
    """Run Stage 1 SND locally. Returns True if window passes."""
    try:
        from src.pipeline.stage1_snd import run_stage1
        result = run_stage1(window)
        passed = result.get("passed", False)
        if not passed:
            logger.debug("SND pre-filter: below_bar — %s", result.get("reason", ""))
        return passed
    except Exception as exc:
        logger.warning("SND pre-filter crashed (%s); letting window through.", exc)
        return True  # Conservative: don't silently drop on error


# ---------------------------------------------------------------------------
# Watchdog event handler
# ---------------------------------------------------------------------------

if WATCHDOG_AVAILABLE:
    class _TranscriptHandler(FileSystemEventHandler):
        def __init__(self, on_file_changed: Callable[[str], None]):
            super().__init__()
            self._on_file_changed = on_file_changed
            self._debounce: Dict[str, threading.Timer] = {}
            self._lock = threading.Lock()

        def _handle(self, path: str) -> None:
            if not path.endswith(".jsonl"):
                return
            # Debounce: coalesce rapid events for the same file (100 ms)
            with self._lock:
                existing = self._debounce.pop(path, None)
                if existing:
                    existing.cancel()
                timer = threading.Timer(0.1, self._on_file_changed, args=(path,))
                self._debounce[path] = timer
                timer.start()

        def on_modified(self, event):
            if not event.is_directory:
                self._handle(event.src_path)

        def on_created(self, event):
            if not event.is_directory:
                self._handle(event.src_path)


# ---------------------------------------------------------------------------
# Main watcher class
# ---------------------------------------------------------------------------

class TranscriptWatcher:
    """
    Watches a directory for .jsonl changes and submits new windows to queue.

    Parameters
    ----------
    watch_path:
        Directory to watch recursively.
    on_window:
        Callback called with (filepath, window) for each new window that
        passes the SND pre-filter. Called from a background thread.
    bookmarks:
        BookmarkStore instance for tracking read offsets.
    window_size:
        Number of turns per grading window.
    poll_interval:
        Polling interval in seconds (used when watchdog is unavailable or
        as a safety net alongside watchdog).
    """

    def __init__(
        self,
        watch_path: str,
        on_window: Callable[[str, Dict[str, Any]], None],
        bookmarks: BookmarkStore,
        window_size: int = 3,
        poll_interval: int = 30,
    ):
        self._watch_path = watch_path
        self._on_window = on_window
        self._bookmarks = bookmarks
        self._reader = IncrementalJSONLReader(bookmarks)
        self._window_size = window_size
        self._poll_interval = poll_interval
        self._observer: Optional[Any] = None
        self._poll_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        # Per-file turn buffer: accumulates turns across multiple reads
        self._turn_buffers: Dict[str, List[Dict[str, Any]]] = {}
        self._buffer_lock = threading.Lock()

    def start(self) -> None:
        """Start watching. Returns immediately (watcher runs in background thread)."""
        watch_path = self._watch_path
        if not os.path.isdir(watch_path):
            logger.warning("Watch path does not exist: %s — waiting for it to appear", watch_path)

        if WATCHDOG_AVAILABLE:
            self._start_watchdog()
        else:
            logger.info("Using polling watcher (interval: %ds)", self._poll_interval)

        # Always run a periodic poll as safety net
        self._poll_thread = threading.Thread(
            target=self._poll_loop, daemon=True, name="workpulse-poll"
        )
        self._poll_thread.start()
        logger.info("TranscriptWatcher started on: %s", watch_path)

    def stop(self) -> None:
        """Signal watcher to stop."""
        self._stop_event.set()
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)

    def run_blocking(self) -> None:
        """Start and block until KeyboardInterrupt or stop() is called."""
        self.start()
        try:
            self._stop_event.wait()
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received.")
        finally:
            self.stop()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _start_watchdog(self) -> None:
        handler = _TranscriptHandler(self._on_file_changed)
        self._observer = Observer()
        watch_path = self._watch_path
        if os.path.isdir(watch_path):
            self._observer.schedule(handler, watch_path, recursive=True)
        else:
            # Watch parent or home dir until path appears
            parent = str(Path(watch_path).parent)
            if not os.path.isdir(parent):
                parent = str(Path.home())
            self._observer.schedule(handler, parent, recursive=True)
        self._observer.start()
        logger.debug("watchdog Observer started.")

    def _poll_loop(self) -> None:
        """Periodic poll: scan all .jsonl files in the watch path."""
        while not self._stop_event.is_set():
            self._stop_event.wait(timeout=self._poll_interval)
            if self._stop_event.is_set():
                break
            self._scan_directory()

    def _scan_directory(self) -> None:
        """Walk the watch directory and process any .jsonl files with new content."""
        watch_path = self._watch_path
        if not os.path.isdir(watch_path):
            return
        for root, _dirs, files in os.walk(watch_path):
            for fname in files:
                if fname.endswith(".jsonl"):
                    self._on_file_changed(os.path.join(root, fname))

    def _on_file_changed(self, filepath: str) -> None:
        """Called when a .jsonl file is created or modified."""
        abs_path = os.path.abspath(filepath)
        new_turns = self._reader.read_new_turns(abs_path)
        if not new_turns:
            return

        with self._buffer_lock:
            buf = self._turn_buffers.setdefault(abs_path, [])
            buf.extend(new_turns)
            # Extract windows from the accumulated buffer
            windows = extract_windows(buf, window_size=self._window_size)
            # Keep only the last (window_size - 1) turns in buffer for next overlap
            if len(buf) > self._window_size:
                self._turn_buffers[abs_path] = buf[-(self._window_size - 1):]

        for window in windows:
            if _snd_passes(window):
                try:
                    self._on_window(abs_path, window)
                except Exception as exc:
                    logger.error("on_window callback failed: %s", exc)
