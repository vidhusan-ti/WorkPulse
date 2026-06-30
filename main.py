#!/usr/bin/env python3
"""
WorkPulse — AI Prompt Coach for Cursor
Usage: python main.py [--config config/settings.json]
"""
import argparse
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="WorkPulse — AI Prompt Coach for Cursor")
    parser.add_argument(
        "--config", default="config/settings.json",
        help="Path to settings.json (default: config/settings.json)"
    )
    parser.add_argument(
        "--setup", action="store_true",
        help="Run interactive setup to configure transcript path and API key"
    )
    args = parser.parse_args()

    if args.setup:
        run_setup(args.config)
        return

    if not os.path.exists(args.config):
        print(f"[WorkPulse] Config not found at {args.config}")
        print("[WorkPulse] Run with --setup to configure, or copy config/settings.json and edit it.")
        sys.exit(1)

    with open(args.config) as f:
        config = json.load(f)

    # Validate required fields
    if not config.get("transcript_glob"):
        print("[WorkPulse] Error: transcript_glob is not set in config.")
        print("[WorkPulse] Run with --setup to configure.")
        sys.exit(1)

    api_key_env = config.get("llm_api_key_env", "OPENAI_API_KEY")
    if not config.get("llm_api_key") and not os.environ.get(api_key_env):
        print(f"[WorkPulse] Error: LLM API key not found. Set {api_key_env} env var or add llm_api_key to config.")
        sys.exit(1)

    from src.monitor import WorkPulseMonitor
    monitor = WorkPulseMonitor(config)
    monitor.start()


def run_setup(config_path: str):
    """Interactive setup wizard."""
    print("🔱 WorkPulse Setup\n")

    # Detect default Cursor path
    home = os.path.expanduser("~")
    if sys.platform == "win32":
        default_glob = os.path.join(home, ".cursor", "projects", "*", "agent-transcripts", "*", "*.jsonl")
    elif sys.platform == "darwin":
        default_glob = os.path.join(home, "Library", "Application Support", "Cursor", "User", "globalStorage",
                                    "cursor.agent", "agent-transcripts", "*", "*.jsonl")
    else:
        default_glob = os.path.join(home, ".config", "Cursor", "User", "globalStorage",
                                    "cursor.agent", "agent-transcripts", "*", "*.jsonl")

    print(f"Detected platform: {sys.platform}")
    print(f"Suggested transcript glob: {default_glob}")
    glob_input = input(f"Transcript glob path [press Enter to use suggested]: ").strip()
    transcript_glob = glob_input or default_glob

    provider = input("LLM provider [openai/anthropic] (default: openai): ").strip() or "openai"
    if provider == "openai":
        model = input("Model (default: gpt-4o): ").strip() or "gpt-4o"
        api_key_env = "OPENAI_API_KEY"
    else:
        model = input("Model (default: claude-3-5-sonnet-20241022): ").strip() or "claude-3-5-sonnet-20241022"
        api_key_env = "ANTHROPIC_API_KEY"

    api_key = input(f"API key (or set {api_key_env} env var, press Enter to skip): ").strip()

    config = {
        "transcript_glob": transcript_glob,
        "check_interval_seconds": 60,
        "inactive_after_minutes": 10,
        "llm_provider": provider,
        "llm_model": model,
        "llm_api_key_env": api_key_env,
        "llm_api_key": api_key or "",
        "llm_max_assistant_chars": 2000,
        "llm_max_grades_per_cycle": 3,
        "data_dir": "data",
        "portfolio_file": "data/portfolio.md",
        "graded_events_file": "data/graded_events.jsonl",
        "rubric_file": "data/manual_rubric.md",
    }

    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"\n✅ Config saved to {config_path}")
    print("Run: python main.py  to start WorkPulse")


if __name__ == "__main__":
    main()
