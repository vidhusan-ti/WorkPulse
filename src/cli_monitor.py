"""
cli_monitor.py — WorkPulse Monitor entry point.

Usage:
  workpulse-monitor [--path PATH] [--port PORT] [--model MODEL]

The entry point:
  1. Loads config (CLI args > ~/.workpulse/config.json > .env > env vars > defaults)
  2. Starts Flask dashboard in a background thread (port 7700)
  3. Starts the FCFS grading queue worker in a background thread
  4. Starts the watchdog file watcher (blocks main thread)
  5. On Ctrl+C: graceful shutdown
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import threading
import time
from pathlib import Path

# Overlay widget (optional — graceful fallback if unavailable)
# Imported lazily inside main() to avoid import-time side effects

# Ensure project root is on sys.path so `src.*` imports work when run
# both as `python src/cli_monitor.py` and as `workpulse-monitor` entry point.
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Quieten noisy libs
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("watchdog").setLevel(logging.WARNING)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="workpulse-monitor",
        description="WorkPulse — real-time Cursor transcript monitor and grader.",
    )
    parser.add_argument(
        "--path", "-p",
        metavar="PATH",
        help="Path to watch for Cursor .jsonl transcript files (overrides config).",
    )
    parser.add_argument(
        "--port",
        type=int,
        metavar="PORT",
        help="Dashboard port (default: 7700).",
    )
    parser.add_argument(
        "--model", "-m",
        metavar="MODEL",
        help="Anthropic model (default: claude-sonnet-4-5).",
    )
    parser.add_argument(
        "--dotenv",
        metavar="PATH",
        default=None,
        help="Path to .env file (default: .env in cwd).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()





def _first_run_setup(cfg: dict) -> dict:
    """
    Interactive first-run wizard.
    Runs only when ANTHROPIC_API_KEY or transcript_path is missing.
    Saves API key to ~/.workpulse/.env and config to ~/.workpulse/config.json.
    """
    from pathlib import Path

    WORKPULSE_DIR = Path.home() / ".workpulse"
    WORKPULSE_DIR.mkdir(parents=True, exist_ok=True)
    env_file = WORKPULSE_DIR / ".env"

    needs_key = not cfg.get("anthropic_api_key")
    needs_path = not cfg.get("transcript_path")

    if not needs_key and not needs_path:
        return cfg  # Nothing to ask, start immediately

    print("\n\U0001f531 WorkPulse - First-time setup\n")

    # --- API key ---
    if needs_key:
        print("An Anthropic API key is needed to grade your prompts.")
        print("Get one at: https://console.anthropic.com/")
        while True:
            key = input("Enter your ANTHROPIC_API_KEY: ").strip()
            if key and len(key) > 20:
                cfg["anthropic_api_key"] = key
                os.environ["ANTHROPIC_API_KEY"] = key
                existing = env_file.read_text() if env_file.exists() else ""
                lines = [l for l in existing.splitlines() if not l.startswith("ANTHROPIC_API_KEY=")]
                lines.append(f"ANTHROPIC_API_KEY={key}")
                env_file.write_text("\n".join(lines) + "\n")
                print(f"\u2705  API key saved to {env_file}")
                break
            else:
                print("That doesn't look like a valid key. Please try again.")

    # --- Transcript path ---
    if needs_path:
        print("\nCursor transcript path not detected automatically.")
        print("Common locations:")
        print("  Windows : C:\\Users\\<name>\\.cursor\\projects")
        print("  macOS   : ~/Library/Application Support/Cursor/User/globalStorage/cursor.agent/agent-transcripts")
        print("  Linux   : ~/.config/Cursor/User/globalStorage/cursor.agent/agent-transcripts")
        path_input = input("\nEnter path (or press Enter to skip): ").strip()
        if path_input:
            cfg["transcript_path"] = path_input
        else:
            print("\u26a0  No transcript path set - file watching will be disabled.")

    from src.monitor.config import save_config, CONFIG_FILE
    try:
        save_config(cfg)
        print(f"\u2705  Config saved to {CONFIG_FILE}")
    except Exception as exc:
        print(f"Warning: could not save config: {exc}")

    print("\n\U0001f680  Starting WorkPulse...\n")
    return cfg

def main() -> None:
    args = _parse_args()
    _setup_logging(args.verbose)

    logger = logging.getLogger("workpulse")

    # ------------------------------------------------------------------ #
    # 1. Load config                                                       #
    # ------------------------------------------------------------------ #
    from src.monitor.config import load_config
    cfg = load_config(
        transcript_path=args.path,
        port=args.port,
        model=args.model,
        dotenv_path=args.dotenv,
    )

    logger.info("=== WorkPulse Monitor ===")
    logger.info("Model:      %s", cfg["model"])
    logger.info("Dashboard:  http://localhost:%d", cfg["dashboard_port"])

    # First-run setup: prompts for API key / transcript path if missing,
    # saves them, then continues automatically.
    cfg = _first_run_setup(cfg)

    if not cfg["transcript_path"]:
        logger.error(
            "No transcript path configured. "
            "Pass --path /path/to/cursor/transcripts "
            "or set transcript_path in ~/.workpulse/config.json"
        )
        sys.exit(1)

    logger.info("Watching:   %s", cfg["transcript_path"])

    # Resolve rubric path relative to project root
    rubric_path = cfg.get("rubric_path", "data/manual_rubric.md")
    if not os.path.isabs(rubric_path):
        rubric_path = os.path.join(_project_root, rubric_path)
    if not os.path.isfile(rubric_path):
        logger.warning("Rubric file not found at %s — grading will proceed without rubric context.", rubric_path)

    # ------------------------------------------------------------------ #
    # 2. Start Flask dashboard in background thread                       #
    # ------------------------------------------------------------------ #
    from src.monitor.dashboard import run_dashboard, get_result_store
    from src.monitor.dashboard import create_app as _create_dashboard

    results_file = cfg["results_file"]
    dashboard_port = cfg["dashboard_port"]

    # Pre-create the app so result_store is initialised before worker starts
    _create_dashboard(results_file=results_file, port=dashboard_port)

    def _dashboard_thread():
        from src.monitor.dashboard import create_app
        from flask import Flask
        import src.monitor.dashboard as _dash_mod
        app = _dash_mod._result_store  # already created above
        # Re-create for this thread
        _app = create_app(results_file=results_file, port=dashboard_port)
        _app.run(
            host="127.0.0.1",
            port=dashboard_port,
            threaded=True,
            use_reloader=False,
        )

    dash_thread = threading.Thread(
        target=_dashboard_thread,
        daemon=True,
        name="workpulse-dashboard",
    )
    dash_thread.start()
    logger.info("Dashboard starting at http://localhost:%d", dashboard_port)

    # ------------------------------------------------------------------ #
    # 3. Start grading queue worker                                        #
    # ------------------------------------------------------------------ #
    from src.monitor.bookmarks import BookmarkStore
    from src.monitor.notifier import notify_result
    from src.monitor.queue_worker import GradingWorker

    bookmarks = BookmarkStore(cfg["bookmarks_file"])

    def on_result(filepath: str, window: dict, result: dict) -> None:
        """Called by worker thread when a grade completes."""
        tier = result.get("tier", "")
        label = result.get("label", "")
        score = result.get("score", "?")
        prompt_preview = GradingWorker._get_prompt_preview(window)

        logger.info(
            "[%s] tier=%s label=%s score=%s | %s",
            os.path.basename(filepath),
            tier,
            label,
            score,
            prompt_preview[:80],
        )

        # Fire OS notification for above_bar
        try:
            notify_result(result, prompt_preview)
        except Exception as exc:
            logger.debug("Notification failed: %s", exc)

        # Push to dashboard SSE
        import json as _json
        from datetime import datetime, timezone
        from src.monitor.dashboard import get_result_store as _grs
        store = _grs()
        if store:
            from src.monitor.config import extract_project_id
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source_file": filepath,
                "project_id": extract_project_id(filepath),
                "tier": tier,
                "label": label,
                "score": score,
                "reason": result.get("reason", ""),
                "coaching": result.get("coaching", ""),
                "better_prompt": result.get("better_prompt", ""),
                "prompt_preview": prompt_preview,
                "pipeline_trace": result.get("pipeline_trace", {}),
                "window": window,
            }
            store.add(record)

    # ------------------------------------------------------------------ #
    # 3a. Create overlay state                                            #
    # ------------------------------------------------------------------ #
    from src.monitor.overlay import OverlayState, OverlayWidget
    overlay_state = OverlayState(start_time=time.time())

    worker = GradingWorker(
        rubric_path=rubric_path,
        provider="anthropic",
        model=cfg["model"],
        api_key=cfg["anthropic_api_key"],
        on_result=on_result,
        results_file=results_file,
        overlay_state=overlay_state,
    )
    worker.start()

    # ------------------------------------------------------------------ #
    # 4. Start watchdog file watcher (blocks main thread)                 #
    # ------------------------------------------------------------------ #
    from src.monitor.watcher import TranscriptWatcher

    def on_window(filepath: str, window: dict) -> None:
        """Called by watcher when a new window passes SND pre-filter."""
        worker.enqueue(filepath, window)

    watcher = TranscriptWatcher(
        watch_path=cfg["transcript_path"],
        on_window=on_window,
        bookmarks=bookmarks,
        window_size=cfg.get("window_size", 3),
        poll_interval=30,
    )

    # ------------------------------------------------------------------ #
    # 5. Start overlay widget                                             #
    # ------------------------------------------------------------------ #
    _shutdown_event = threading.Event()

    def _on_overlay_close():
        """Called when user clicks ✕ in the overlay."""
        logger.info("Overlay closed by user — shutting down monitor.")
        _shutdown_event.set()
        watcher.stop()  # signal watcher to stop

    overlay = OverlayWidget(overlay_state, on_close=_on_overlay_close)

    if overlay.uses_tkinter:
        # Tkinter blocks main thread — run watcher in a background thread
        logger.info("Starting watcher thread (Tkinter overlay on main thread).")
        watcher_thread = threading.Thread(
            target=watcher.run_blocking, daemon=True, name="workpulse-watcher"
        )
        watcher_thread.start()
        try:
            overlay.run()  # blocks until window closed
        except KeyboardInterrupt:
            pass
        finally:
            logger.info("Shutting down…")
            worker.stop(timeout=10.0)
            logger.info("Done. Goodbye.")
    else:
        # Flask overlay is non-blocking — watcher blocks main thread as before
        overlay.run()  # starts background Flask thread
        logger.info("Starting watcher — press Ctrl+C to stop.")
        try:
            watcher.run_blocking()
        except KeyboardInterrupt:
            pass
        finally:
            logger.info("Shutting down…")
            worker.stop(timeout=10.0)
            logger.info("Done. Goodbye.")


if __name__ == "__main__":
    main()
