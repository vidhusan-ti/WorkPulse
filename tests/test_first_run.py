"""
tests/test_first_run.py

Tests for the first-run grading-history flow (src/monitor/first_run.py).
All tests use a fake tmp ~/.workpulse via monkeypatched module attributes —
no GUI is ever opened (forced_choice / console paths only).
"""
from pathlib import Path

import pytest

from src.monitor.bookmarks import BookmarkStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _patch_state(monkeypatch, tmp_path):
    """Point first_run's state file at a temp .workpulse dir."""
    import src.monitor.first_run as fr
    wp = tmp_path / ".workpulse"
    wp.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(fr, "WORKPULSE_DIR", wp)
    monkeypatch.setattr(fr, "STATE_FILE", wp / "state.json")
    return fr


def _make_transcripts(root: Path, n_files: int = 2):
    paths = []
    for i in range(n_files):
        d = root / f"proj-{i}" / "agent-transcripts" / f"uuid-{i}"
        d.mkdir(parents=True)
        f = d / f"chat-{i}.jsonl"
        f.write_text('{"role": "user", "text": "hello"}\n')
        paths.append(f)
    return paths


# ---------------------------------------------------------------------------
# is_first_run / mark_initialized
# ---------------------------------------------------------------------------

class TestIsFirstRun:
    def test_true_when_no_state(self, monkeypatch, tmp_path):
        fr = _patch_state(monkeypatch, tmp_path)
        assert fr.is_first_run() is True

    def test_false_after_mark(self, monkeypatch, tmp_path):
        fr = _patch_state(monkeypatch, tmp_path)
        fr.mark_initialized(grade_history=True)
        assert fr.is_first_run() is False

    def test_not_retriggered_when_bookmarks_cleared(self, monkeypatch, tmp_path):
        """Clearing bookmarks/results must NOT re-show the first-run prompt."""
        fr = _patch_state(monkeypatch, tmp_path)
        fr.mark_initialized(grade_history=False)
        # state.json depends only on itself, not on bookmarks.json
        assert fr.is_first_run() is False


# ---------------------------------------------------------------------------
# seed_bookmarks_to_eof
# ---------------------------------------------------------------------------

class TestSeeding:
    def test_seed_sets_offsets_to_file_size(self, monkeypatch, tmp_path):
        fr = _patch_state(monkeypatch, tmp_path)
        proj_root = tmp_path / "projects"
        proj_root.mkdir()
        files = _make_transcripts(proj_root, 3)
        bm = BookmarkStore(str(tmp_path / "bookmarks.json"))

        count = fr.seed_bookmarks_to_eof(str(proj_root), bm)

        assert count == 3
        for f in files:
            assert bm.get(str(f)) == f.stat().st_size

    def test_seed_missing_dir_returns_zero(self, monkeypatch, tmp_path):
        fr = _patch_state(monkeypatch, tmp_path)
        bm = BookmarkStore(str(tmp_path / "bookmarks.json"))
        assert fr.seed_bookmarks_to_eof(str(tmp_path / "nope"), bm) == 0


# ---------------------------------------------------------------------------
# handle_first_run
# ---------------------------------------------------------------------------

class TestHandleFirstRun:
    def test_only_new_seeds_and_marks(self, monkeypatch, tmp_path):
        fr = _patch_state(monkeypatch, tmp_path)
        proj_root = tmp_path / "projects"
        proj_root.mkdir()
        files = _make_transcripts(proj_root, 2)
        bm = BookmarkStore(str(tmp_path / "bookmarks.json"))
        cfg = {"transcript_path": str(proj_root)}

        fr.handle_first_run(cfg, bm, forced_choice=False)

        for f in files:
            assert bm.get(str(f)) == f.stat().st_size
        assert fr.is_first_run() is False
        assert fr._load_state()["grade_history"] is False

    def test_grade_history_does_not_seed(self, monkeypatch, tmp_path):
        fr = _patch_state(monkeypatch, tmp_path)
        proj_root = tmp_path / "projects"
        proj_root.mkdir()
        files = _make_transcripts(proj_root, 2)
        bm = BookmarkStore(str(tmp_path / "bookmarks.json"))
        cfg = {"transcript_path": str(proj_root)}

        fr.handle_first_run(cfg, bm, forced_choice=True)

        for f in files:
            assert bm.get(str(f)) == 0  # untouched -> full backlog graded
        assert fr._load_state()["grade_history"] is True

    def test_second_run_is_noop(self, monkeypatch, tmp_path):
        fr = _patch_state(monkeypatch, tmp_path)
        proj_root = tmp_path / "projects"
        proj_root.mkdir()
        files = _make_transcripts(proj_root, 1)
        bm = BookmarkStore(str(tmp_path / "bookmarks.json"))
        cfg = {"transcript_path": str(proj_root)}

        # First run (only-new) marks initialized + seeds.
        fr.handle_first_run(cfg, bm, forced_choice=False)
        # Pretend the watcher advanced this file's offset.
        f = files[0]
        bm.set(str(f), 5)

        # A subsequent run must be a no-op (no reseeding, no clobbering).
        fr.handle_first_run(cfg, bm, forced_choice=False)
        assert bm.get(str(f)) == 5


# ---------------------------------------------------------------------------
# Console fallback (no GUI)
# ---------------------------------------------------------------------------

class TestConsoleFallback:
    def test_non_interactive_defaults_to_only_new(self, monkeypatch, tmp_path):
        fr = _patch_state(monkeypatch, tmp_path)

        class _NoTTY:
            def isatty(self):
                return False

        monkeypatch.setattr("sys.stdin", _NoTTY())
        assert fr._ask_via_console() is False

    def test_yes_when_user_types_y(self, monkeypatch, tmp_path):
        fr = _patch_state(monkeypatch, tmp_path)

        class _TTY:
            def isatty(self):
                return True

        monkeypatch.setattr("sys.stdin", _TTY())
        monkeypatch.setattr("builtins.input", lambda *_a, **_k: "y")
        assert fr._ask_via_console() is True
