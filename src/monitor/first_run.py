"""
first_run.py — First-run experience for WorkPulse.

On the very first launch on a machine, ask the user whether to grade their
existing Cursor conversation history (the backlog) or only new prompts from
now on. The choice is persisted in ~/.workpulse/state.json so the prompt is
shown exactly once.

Design notes:
  * First-run detection uses a dedicated state file (state.json) — NOT
    bookmarks.json — so clearing results/bookmarks never re-triggers the
    prompt.
  * "Only new" is implemented by seeding each existing transcript's bookmark
    to its current byte size, so the watcher starts reading only new bytes.
  * The popup uses tkinter (consistent with the overlay); it falls back to a
    console y/N prompt, and to a safe "only new" default when running
    non-interactively (avoids surprise API spend on a large backlog).
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

WORKPULSE_DIR = Path.home() / ".workpulse"
STATE_FILE = WORKPULSE_DIR / "state.json"


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------

def _load_state() -> dict:
    """Read state.json; return {} on any error (never raises)."""
    try:
        if STATE_FILE.is_file():
            with open(STATE_FILE) as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not read state file %s: %s", STATE_FILE, exc)
    return {}


def is_first_run() -> bool:
    """True if WorkPulse has never completed first-run setup.

    Intentionally independent of bookmarks.json / results.jsonl so that
    clearing those files does not show the first-run prompt again.
    """
    return not _load_state().get("initialized", False)


def mark_initialized(grade_history: bool) -> None:
    """Persist that first-run is done and which choice was made."""
    try:
        WORKPULSE_DIR.mkdir(parents=True, exist_ok=True)
        state = _load_state()
        state.update(
            {
                "initialized": True,
                "grade_history": bool(grade_history),
                "first_run_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        tmp = STATE_FILE.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(state, f, indent=2)
        tmp.replace(STATE_FILE)
        logger.debug("Wrote first-run state to %s", STATE_FILE)
    except OSError as exc:
        logger.error("Failed to persist state to %s: %s", STATE_FILE, exc)


# ---------------------------------------------------------------------------
# Asking the user
# ---------------------------------------------------------------------------

_DIALOG_TITLE = "WorkPulse — First Run"
_DIALOG_BODY = (
    "Grade your existing Cursor conversation history too?\n\n"
    "Yes  =  grade past prompts now (uses more API credits)\n"
    "No   =  only grade new prompts from now on"
)


def _ask_via_tkinter() -> Optional[bool]:
    """Show a GUI yes/no dialog. Returns the answer, or None if GUI unavailable."""
    try:
        import tkinter as tk
        from tkinter import messagebox
    except Exception:
        return None

    try:
        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        answer = messagebox.askyesno(_DIALOG_TITLE, _DIALOG_BODY, parent=root)
        root.destroy()
        return bool(answer)
    except Exception as exc:
        logger.debug("tkinter first-run dialog unavailable: %s", exc)
        return None


def _ask_via_console() -> bool:
    """Console fallback. Defaults to False (only-new) when non-interactive."""
    try:
        if not sys.stdin or not sys.stdin.isatty():
            logger.info(
                "Non-interactive session — defaulting to grade only NEW prompts."
            )
            return False
        resp = input(
            "\nGrade your EXISTING Cursor history too? "
            "[y = grade past, N = only new]: "
        ).strip().lower()
        return resp in ("y", "yes")
    except (EOFError, OSError):
        return False


def ask_grade_history() -> bool:
    """Ask the user whether to grade existing history. GUI first, console fallback."""
    result = _ask_via_tkinter()
    if result is None:
        result = _ask_via_console()
    return result


# ---------------------------------------------------------------------------
# Seeding bookmarks (the "only new" behavior)
# ---------------------------------------------------------------------------

def seed_bookmarks_to_eof(watch_path: str, bookmarks) -> int:
    """Mark every existing *.jsonl under *watch_path* as already read.

    Sets each file's bookmark to its current byte size so the watcher only
    grades content written afterwards. Returns the number of files seeded.
    Only stat()s files (never reads contents) so it stays fast with hundreds
    of projects and large transcripts. Never raises.
    """
    count = 0
    try:
        base = Path(watch_path)
    except TypeError:
        return 0
    if not base.is_dir():
        return 0

    try:
        for jsonl in base.rglob("*.jsonl"):
            try:
                size = jsonl.stat().st_size
                bookmarks.set(str(jsonl), size)
                count += 1
            except (OSError, PermissionError):
                continue
    except (OSError, PermissionError) as exc:
        logger.debug("seed_bookmarks_to_eof walk failed: %s", exc)

    logger.info("Marked %d existing transcript(s) as already-read.", count)
    return count


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def handle_first_run(cfg: dict, bookmarks, forced_choice: Optional[bool] = None) -> None:
    """Run the first-run grading-history flow if this is the first launch.

    Parameters
    ----------
    cfg:
        Loaded config dict (must contain "transcript_path").
    bookmarks:
        A BookmarkStore instance (has a ``set(path, offset)`` method).
    forced_choice:
        True  -> grade existing history (skip prompt)
        False -> only new prompts (skip prompt)
        None  -> ask the user interactively
    """
    if not is_first_run():
        return

    if forced_choice is not None:
        grade_history = bool(forced_choice)
        logger.info("First-run choice via flag: grade_history=%s", grade_history)
    else:
        grade_history = ask_grade_history()

    if grade_history:
        logger.info("First run: grading existing Cursor history (backlog).")
    else:
        watch_path = cfg.get("transcript_path")
        if watch_path:
            seed_bookmarks_to_eof(watch_path, bookmarks)
        logger.info("First run: grading only NEW prompts from now on.")

    mark_initialized(grade_history)
