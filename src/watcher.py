"""
watcher.py — Cross-platform file watcher using watchdog.
Monitors Cursor JSONL transcript directories for new/modified files.
"""
import os
import glob
import time
import threading
from typing import Callable, Set

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


class TranscriptHandler(FileSystemEventHandler if WATCHDOG_AVAILABLE else object):
    def __init__(self, on_transcript_changed: Callable[[str], None]):
        if WATCHDOG_AVAILABLE:
            super().__init__()
        self.on_transcript_changed = on_transcript_changed
        self._seen: Set[str] = set()

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".jsonl"):
            self.on_transcript_changed(event.src_path)

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".jsonl"):
            self.on_transcript_changed(event.src_path)


class TranscriptWatcher:
    """
    Watches Cursor transcript directories for changes.
    Falls back to polling if watchdog is unavailable.
    """
    def __init__(
        self,
        transcript_glob: str,
        on_transcript_changed: Callable[[str], None],
        poll_interval: int = 60,
    ):
        self.transcript_glob = transcript_glob
        self.on_transcript_changed = on_transcript_changed
        self.poll_interval = poll_interval
        self._observer = None
        self._poll_thread = None
        self._running = False
        self._known_files: dict = {}  # path -> mtime

    def start(self):
        self._running = True
        if WATCHDOG_AVAILABLE:
            self._start_watchdog()
        # Always run polling as fallback/supplement
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def stop(self):
        self._running = False
        if self._observer:
            self._observer.stop()
            self._observer.join()

    def _start_watchdog(self):
        """Start watchdog observers on all unique directories in the glob."""
        dirs = self._get_watch_dirs()
        if not dirs:
            return
        self._observer = Observer()
        handler = TranscriptHandler(self.on_transcript_changed)
        for d in dirs:
            if os.path.isdir(d):
                self._observer.schedule(handler, d, recursive=True)
        self._observer.start()

    def _get_watch_dirs(self) -> Set[str]:
        """Derive watch directories from the glob pattern."""
        # Take the non-glob prefix of the pattern as the watch root
        parts = self.transcript_glob.replace("\\", "/").split("/")
        watch_parts = []
        for p in parts:
            if any(c in p for c in ("*", "?", "[")):
                break
            watch_parts.append(p)
        if not watch_parts:
            return set()
        watch_root = "/".join(watch_parts) or "/"
        # On Windows, restore drive letter
        if len(watch_root) == 1 and self.transcript_glob[1:3] == ":/":
            watch_root = watch_root + ":/"
        return {watch_root} if os.path.exists(watch_root) else set()

    def _poll_loop(self):
        """Polling fallback — checks all glob files every poll_interval seconds.
        
        Uses os.walk instead of glob.glob so that hidden directories (like
        ~/.cursor) are traversed correctly on all platforms.  glob.glob on
        Python < 3.11 skips hidden dirs on some systems.
        """
        while self._running:
            try:
                files = self._find_transcript_files()
                for path in files:
                    try:
                        mtime = os.path.getmtime(path)
                        if self._known_files.get(path) != mtime:
                            self._known_files[path] = mtime
                            self.on_transcript_changed(path)
                    except OSError:
                        continue
            except Exception:
                pass
            time.sleep(self.poll_interval)

    def _find_transcript_files(self):
        """Find all .jsonl files under the watch root using os.walk.
        
        Handles hidden directories (e.g. ~/.cursor/) that glob.glob may miss.
        Falls back to glob if watch root cannot be determined.
        """
        watch_dirs = self._get_watch_dirs()
        if not watch_dirs:
            # fallback to glob
            return glob.glob(self.transcript_glob, recursive=True)
        
        found = []
        for root_dir in watch_dirs:
            for dirpath, _dirnames, filenames in os.walk(root_dir):
                for fname in filenames:
                    if fname.endswith(".jsonl"):
                        found.append(os.path.join(dirpath, fname))
        return found
