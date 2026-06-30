"""
bookmarks.py — Byte-offset bookmark persistence for incremental JSONL reading.

Bookmarks are stored in ~/.workpulse/bookmarks.json as:
  { "/absolute/path/to/file.jsonl": <byte_offset>, ... }

On restart, reading resumes from the stored offset so already-seen content
is never re-graded.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


class BookmarkStore:
    """Thread-safe persistent store for per-file byte offsets."""

    def __init__(self, bookmarks_file: str | None = None):
        if bookmarks_file is None:
            bookmarks_file = str(Path.home() / ".workpulse" / "bookmarks.json")
        self._path = Path(bookmarks_file)
        self._lock = threading.Lock()
        self._data: Dict[str, int] = {}
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, filepath: str) -> int:
        """Return the stored byte offset for *filepath*, or 0 if unseen."""
        abs_path = os.path.abspath(filepath)
        with self._lock:
            return self._data.get(abs_path, 0)

    def set(self, filepath: str, offset: int) -> None:
        """Update the byte offset for *filepath* and flush to disk."""
        abs_path = os.path.abspath(filepath)
        with self._lock:
            self._data[abs_path] = offset
            self._flush()

    def all(self) -> Dict[str, int]:
        """Return a copy of all bookmarks."""
        with self._lock:
            return dict(self._data)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load bookmarks from disk; silently start fresh on any error."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.is_file():
            self._data = {}
            return
        try:
            with open(self._path) as f:
                raw = json.load(f)
            # Validate structure: must be {str: int}
            self._data = {
                k: int(v)
                for k, v in raw.items()
                if isinstance(k, str) and isinstance(v, (int, float))
            }
            logger.debug("Loaded %d bookmarks from %s", len(self._data), self._path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            logger.warning("Could not load bookmarks from %s: %s. Starting fresh.", self._path, exc)
            self._data = {}

    def _flush(self) -> None:
        """Write current bookmarks to disk (must be called under self._lock)."""
        try:
            # Atomic write via temp file
            tmp = self._path.with_suffix(".tmp")
            with open(tmp, "w") as f:
                json.dump(self._data, f, indent=2)
            tmp.replace(self._path)
        except OSError as exc:
            logger.error("Failed to persist bookmarks to %s: %s", self._path, exc)
