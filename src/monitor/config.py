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

def _detect_cursor_transcript_path() -> Optional[str]:
    """Try to find Cursor's default transcript directory on the current OS."""
    system = platform.system()
    home = Path.home()

    candidates = []
    if system == "Darwin":  # macOS
        candidates = [
            home / "Library" / "Application Support" / "Cursor" / "User" / "workspaceStorage",
            home / "Library" / "Application Support" / "Cursor" / "logs",
        ]
    elif system == "Linux":
        candidates = [
            home / ".config" / "Cursor" / "User" / "workspaceStorage",
            home / ".config" / "cursor" / "User" / "workspaceStorage",
        ]
    elif system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            candidates = [
                Path(appdata) / "Cursor" / "User" / "workspaceStorage",
            ]

    for path in candidates:
        if path.exists():
            return str(path)

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
