# MEMORY.md — Rudra's Long-Term Memory

_Curated memory across all sessions. Updated as conversations happen._

---

## About Vidhu

- Full name: Vidhu (likely Vidhusan based on transcript data in workspace)
- Timezone: IST (UTC+5:30), India
- Named me Rudra 🔱
- Prefers direct, concise answers — no fluff

## WorkPulse Project

- **What it is:** AI prompt coach for Cursor — monitors transcript JSONL files, grades prompts, shows floating overlay popups
- **Stack:** Python, watchdog, Anthropic API, Flask dashboard (port 7700), tkinter overlay
- **Status:** Phase 5 complete. 89/89 tests passing. Pip-installable.
- **Entry point:** `workpulse-monitor` CLI command
- **Grading pipeline:** 4-stage SND→IOAS→CTA→EJAD
- **Repo:** https://github.com/vidhusan-ti/WorkPulse.git
- **Install:** `pip install git+https://github.com/vidhusan-ti/WorkPulse.git`

## Recent Changes (2026-06-30)

- Added `_first_run_setup()` to `src/cli_monitor.py`
  - On first run: prompts for ANTHROPIC_API_KEY + transcript path
  - Saves key to `~/.workpulse/.env`, config to `~/.workpulse/config.json`
  - Every subsequent run starts automatically with no prompts
- Dashboard at `http://localhost:7700`

## Conversation Patterns

- Vidhu types fast, informal style (typos are normal — just understand and respond)
- Asks practical "how do I" questions about WorkPulse
- Wants things to just work, minimal steps for end users

---

_Last updated: 2026-06-30_
