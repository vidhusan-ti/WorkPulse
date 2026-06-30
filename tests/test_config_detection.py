"""
tests/test_config_detection.py

Tests for _detect_cursor_transcript_path() and _has_agent_transcripts().
All tests use a fake tmp home — no hardcoded usernames or drive letters.
"""
import importlib
import os
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reload_config(monkeypatch, fake_home: Path):
    """Reload src.monitor.config with Path.home() patched to fake_home."""
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    # Force re-import so module-level Path.home() calls use the patch
    if "src.monitor.config" in sys.modules:
        del sys.modules["src.monitor.config"]
    import src.monitor.config as cfg_mod
    return cfg_mod


# ---------------------------------------------------------------------------
# _has_agent_transcripts
# ---------------------------------------------------------------------------

class TestHasAgentTranscripts:
    def test_returns_true_when_jsonl_exists(self, tmp_path):
        from src.monitor.config import _has_agent_transcripts
        proj = tmp_path / "proj-abc" / "agent-transcripts"
        proj.mkdir(parents=True)
        (proj / "chat.jsonl").write_text("{}")
        assert _has_agent_transcripts(tmp_path) is True

    def test_returns_false_when_no_jsonl(self, tmp_path):
        from src.monitor.config import _has_agent_transcripts
        (tmp_path / "agent-transcripts").mkdir()
        assert _has_agent_transcripts(tmp_path) is False

    def test_returns_false_for_empty_dir(self, tmp_path):
        from src.monitor.config import _has_agent_transcripts
        assert _has_agent_transcripts(tmp_path) is False

    def test_does_not_raise_on_missing_dir(self, tmp_path):
        from src.monitor.config import _has_agent_transcripts
        missing = tmp_path / "does_not_exist"
        # Should return False, not raise
        assert _has_agent_transcripts(missing) is False


# ---------------------------------------------------------------------------
# _detect_cursor_transcript_path — primary path
# ---------------------------------------------------------------------------

class TestDetectPrimaryPath:
    def test_detects_primary_with_transcripts(self, tmp_path, monkeypatch):
        """~/.cursor/projects with transcripts → returns that path."""
        projects = tmp_path / ".cursor" / "projects"
        at_dir = projects / "proj-123" / "agent-transcripts"
        at_dir.mkdir(parents=True)
        (at_dir / "session.jsonl").write_text("{}")

        cfg = _reload_config(monkeypatch, tmp_path)
        result = cfg._detect_cursor_transcript_path()
        assert result == str(projects)

    def test_detects_primary_dir_even_without_transcripts(self, tmp_path, monkeypatch):
        """~/.cursor/projects exists but empty → still return it (new machine)."""
        projects = tmp_path / ".cursor" / "projects"
        projects.mkdir(parents=True)

        cfg = _reload_config(monkeypatch, tmp_path)
        result = cfg._detect_cursor_transcript_path()
        assert result == str(projects)

    def test_returns_none_when_cursor_dir_missing(self, tmp_path, monkeypatch):
        """No ~/.cursor at all → return None (no fallbacks present either)."""
        cfg = _reload_config(monkeypatch, tmp_path)
        result = cfg._detect_cursor_transcript_path()
        assert result is None

    def test_nested_project_detected(self, tmp_path, monkeypatch):
        """Transcripts nested several levels deep are found."""
        at_dir = (
            tmp_path / ".cursor" / "projects"
            / "ws-xyz" / "agent-transcripts"
        )
        at_dir.mkdir(parents=True)
        (at_dir / "a.jsonl").write_text("{}")

        cfg = _reload_config(monkeypatch, tmp_path)
        result = cfg._detect_cursor_transcript_path()
        assert result is not None
        assert ".cursor" in result
        assert "projects" in result


# ---------------------------------------------------------------------------
# No hardcoded paths
# ---------------------------------------------------------------------------

class TestNoHardcodedPaths:
    def test_no_hardcoded_username_in_source(self):
        """The source file must not contain any hardcoded absolute paths."""
        src_path = Path(__file__).resolve().parent.parent / "src" / "monitor" / "config.py"
        source = src_path.read_text()
        # Should never contain /home/<specific-user> or C:\Users\<name>
        import re
        # Check for /home/<word>/<word> patterns (hardcoded unix home)
        assert not re.search(r"/home/[a-zA-Z0-9_]+/[a-zA-Z0-9_]", source), \
            "Hardcoded Unix home path found in config.py"
        # Check for Windows-style C:\Users\<name>
        assert not re.search(r"[A-Z]:\\\\Users\\\\[a-zA-Z0-9_]+", source), \
            "Hardcoded Windows user path found in config.py"

    def test_result_uses_actual_home(self, tmp_path, monkeypatch):
        """Returned path must be relative to the (patched) home, not hardcoded."""
        projects = tmp_path / ".cursor" / "projects"
        projects.mkdir(parents=True)

        cfg = _reload_config(monkeypatch, tmp_path)
        result = cfg._detect_cursor_transcript_path()
        assert result is not None
        assert str(tmp_path) in result, \
            f"Result {result!r} does not contain fake home {tmp_path}"
