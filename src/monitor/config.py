"""
config.py — Config loading for WorkPulse Monitor.

Priority order:
  1. CLI args (passed in at runtime)
  2. ~/.workpulse/config.json
  3. .env file (ANTHROPIC_API_KEY etc.)
  4. Environment variables
  5. Hardcoded defaults
"""

from __future__ import annotations

import json
import logging
import os
import platform
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

WORKPULSE_DIR = Path.home() / ".workpulse"
CONFIG_FILE = WORKPULSE_DIR / "config.json"
BOOKMARKS_FILE = WORKPULSE_DIR / "bookmarks.json"
RESULTS_FILE = WORKPULSE_DIR / "results.jsonl"

# ---------------------------------------------------------------------------
# Cursor transcript path auto-detection
# ---------------------------------------------------------------------------

def _has_agent_transcripts(base: Path) -> bool:
    """Return True if *base* contains at least one .jsonl under any agent-transcripts/ subdir.

    Short-circuits on first match for speed. Never raises.
    """
    try:
        for jsonl in base.rglob("agent-transcripts/*.jsonl"):
            if jsonl.is_file():
                return True
    except (OSError, PermissionError):
        pass
    return False


def extract_project_id(filepath: str) -> str:
    """Extract the Cursor project-id from a transcript filepath.

    Cursor stores transcripts at:
        ~/.cursor/projects/<project-id>/agent-transcripts/<uuid>/<uuid>.jsonl

    Returns the <project-id> segment if found, otherwise the parent
    directory name, and finally "unknown" as a last resort. Never raises.
    """
    try:
        parts = Path(filepath).parts
        for i, part in enumerate(parts):
            if part == "agent-transcripts" and i > 0:
                return parts[i - 1]   # the project-id folder
        # Fallback: second-to-last directory
        p = Path(filepath)
        if p.parent.name:
            return p.parent.name
    except Exception:
        pass
    return "unknown"


def _detect_cursor_transcript_path() -> Optional[str]:
    """Auto-detect the Cursor agent-transcript directory — cross-platform, no hardcoded paths.

    Change summary: returns ~/.cursor/projects as primary target so ALL repos are watched;
    per-repo attribution via extract_project_id(); fallbacks kept for legacy installs.

    Priority:
      1. PRIMARY  — ~/.cursor/projects  (contains agent-transcripts/ across all OSes)
      2. FALLBACK — OS-specific Cursor app-data dirs (workspaceStorage / logs)

    Returns the first existing path that contains at least one .jsonl transcript,
    or None if nothing is found. Never raises.
    """
    home = Path.home()

    # ------------------------------------------------------------------
    # 1. PRIMARY: ~/.cursor/projects  (OS-independent)
    # ------------------------------------------------------------------
    primary = home / ".cursor" / "projects"
    try:
        if primary.is_dir() and _has_agent_transcripts(primary):
            logger.info("Auto-detected Cursor transcript path (primary): %s", primary)
            return str(primary)
        elif primary.is_dir():
            # Dir exists but no transcripts yet — still prefer it so new
            # projects are picked up automatically once Cursor writes them.
            logger.info(
                "Auto-detected Cursor projects dir (primary, no transcripts yet): %s", primary
            )
            return str(primary)
    except (OSError, PermissionError) as exc:
        logger.debug("Primary detection failed: %s", exc)

    # ------------------------------------------------------------------
    # 2. FALLBACK: OS-specific Cursor app-data dirs
    # ------------------------------------------------------------------
    system = platform.system()
    fallbacks: list[Path] = []

    if system == "Darwin":
        fallbacks = [
            home / "Library" / "Application Support" / "Cursor" / "User" / "workspaceStorage",
            home / "Library" / "Application Support" / "Cursor" / "logs",
        ]
    elif system == "Linux":
        fallbacks = [
            home / ".config" / "Cursor" / "User" / "workspaceStorage",
            home / ".config" / "cursor" / "User" / "workspaceStorage",
        ]
    elif system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            fallbacks = [Path(appdata) / "Cursor" / "User" / "workspaceStorage"]

    for candidate in fallbacks:
        try:
            if candidate.is_dir():
                logger.info("Auto-detected Cursor transcript path (fallback): %s", candidate)
                return str(candidate)
        except (OSError, PermissionError) as exc:
            logger.debug("Fallback candidate %s inaccessible: %s", candidate, exc)

    logger.debug("Could not auto-detect Cursor transcript path.")
    return None


# ---------------------------------------------------------------------------
# Load .env file manually (avoid requiring python-dotenv as hard dep)
# ---------------------------------------------------------------------------

def _load_dotenv(dotenv_path: Optional[str] = None) -> None:
    """Parse a simple .env file and set env vars (does not override existing)."""
    paths_to_try = []
    if dotenv_path:
        paths_to_try.append(Path(dotenv_path))
    # Look in cwd and one level up
    paths_to_try += [Path(".env"), Path("../.env")]

    for path in paths_to_try:
        if path.is_file():
            try:
                with open(path) as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, _, val = line.partition("=")
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        if key and key not in os.environ:
                            os.environ[key] = val
                logger.debug("Loaded .env from %s", path)
                return
            except OSError:
                continue


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_config(
    transcript_path: Optional[str] = None,
    port: Optional[int] = None,
    model: Optional[str] = None,
    dotenv_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Load and merge config from all sources. Returns a unified config dict."""

    # Load .env first so env vars are populated
    _load_dotenv(dotenv_path)

    # Also try python-dotenv if available
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(dotenv_path or ".env", override=False)
    except ImportError:
        pass

    # Ensure workpulse dir exists
    WORKPULSE_DIR.mkdir(parents=True, exist_ok=True)

    # Base defaults
    cfg: Dict[str, Any] = {
        "transcript_path": None,
        "anthropic_api_key": None,
        "dashboard_port": 7700,
        "model": "claude-sonnet-4-5",
        "rubric_path": "data/manual_rubric.md",
        "window_size": 3,
        "bookmarks_file": str(BOOKMARKS_FILE),
        "results_file": str(RESULTS_FILE),
    }

    # Load from ~/.workpulse/config.json
    if CONFIG_FILE.is_file():
        try:
            with open(CONFIG_FILE) as f:
                file_cfg = json.load(f)
            cfg.update(file_cfg)
            logger.debug("Loaded config from %s", CONFIG_FILE)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read %s: %s", CONFIG_FILE, exc)

    # Apply environment variables
    env_key = os.environ.get("ANTHROPIC_API_KEY")
    if env_key:
        cfg["anthropic_api_key"] = env_key

    env_model = os.environ.get("WORKPULSE_MODEL")
    if env_model:
        cfg["model"] = env_model

    env_port = os.environ.get("WORKPULSE_PORT")
    if env_port:
        try:
            cfg["dashboard_port"] = int(env_port)
        except ValueError:
            pass

    # Apply CLI overrides (highest priority)
    if transcript_path:
        cfg["transcript_path"] = transcript_path
    if port is not None:
        cfg["dashboard_port"] = port
    if model:
        cfg["model"] = model

    # Auto-detect Cursor path if not set
    if not cfg["transcript_path"]:
        detected = _detect_cursor_transcript_path()
        if detected:
            cfg["transcript_path"] = detected
            logger.info("Auto-detected Cursor transcript path: %s", detected)

    return cfg


def save_config(cfg: Dict[str, Any]) -> None:
    """Persist config to ~/.workpulse/config.json (excludes sensitive keys)."""
    WORKPULSE_DIR.mkdir(parents=True, exist_ok=True)
    safe = {k: v for k, v in cfg.items() if k != "anthropic_api_key"}
    with open(CONFIG_FILE, "w") as f:
        json.dump(safe, f, indent=2)
