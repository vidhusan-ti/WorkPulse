<div align="center">

# 🔱 WorkPulse

**Real-time AI prompt coach for Cursor.**  
WorkPulse watches your Cursor conversations as you work, grades your prompting quality, and gives you live coaching — so you get better every session.

</div>

---

## What it does

| Event | What happens |
|-------|-------------|
| **Above bar prompt** | A popup asks if you want to save it to your portfolio |
| **Near bar prompt** | A coaching popup explains what was missing and how to improve |
| **Below bar prompt** | Silently ignored — no noise |
| **10 min with no quality prompt** | A nudge reminder appears |

Every grade appears live on the dashboard at **http://localhost:7700**.

---

## Requirements

- Python **3.10+**
- An **Anthropic API key** ([get one here](https://console.anthropic.com/))
- **Cursor** installed and used for coding

---

## Install

```bash
pip install git+https://github.com/vidhusan-ti/WorkPulse.git
```

Or from source:

```bash
git clone https://github.com/vidhusan-ti/WorkPulse.git
cd WorkPulse
pip install -e .
```

---

## First run

```bash
workpulse-monitor
```

On first launch WorkPulse will:

1. **Ask for your Anthropic API key** — saved to `~/.workpulse/.env` (never in git)
2. **Ask whether to grade your existing Cursor history** or only new prompts from now on
3. **Start automatically** — no further setup needed

The browser opens at **http://localhost:7700** and a floating overlay widget appears in the corner of your screen.

---

## Every run after that

```bash
workpulse-monitor
```

That's it. Config is remembered. Starts straight away.

---

## What you'll see

### Floating overlay (tkinter)
A small always-on-top widget in the bottom-right corner shows:
- 🟢 Running / ⏸ Paused status + uptime
- Last graded time
- Above-bar count for today
- Pause / Resume / Close buttons

### Dashboard (browser)
Live feed of every graded result at **http://localhost:7700**:
- Prompt text, verdict (above / near / below bar), score
- Which rubric criteria passed or failed
- Coaching advice + a rewritten prompt suggestion for near-bar results
- Which Cursor project the prompt came from

---

## CLI options

```
workpulse-monitor [OPTIONS]

Options:
  --path PATH           Directory to watch for Cursor .jsonl files
                        (auto-detected if omitted — watches ALL your projects)
  --port PORT           Dashboard port (default: 7700)
  --model MODEL         Anthropic model (default: claude-sonnet-4-5)
  --grade-history       On first run: grade existing Cursor history (skip prompt)
  --no-grade-history    On first run: grade only new prompts (skip prompt)
  --dotenv PATH         Path to a custom .env file
  --verbose, -v         Enable debug logging
```

---

## Uninstall / reinstall from scratch

```bash
# 1. Uninstall
pip uninstall workpulse -y

# 2. Delete saved config and API key
#    macOS / Linux:
rm -rf ~/.workpulse
#    Windows (CMD):
rmdir /s /q %USERPROFILE%\.workpulse
#    Windows (PowerShell):
Remove-Item -Recurse -Force "$env:USERPROFILE\.workpulse"

# 3. Reinstall
pip install git+https://github.com/vidhusan-ti/WorkPulse.git
```

---

## Update to latest version

```bash
pip install --upgrade git+https://github.com/vidhusan-ti/WorkPulse.git
```

---

## Where Cursor transcripts live

WorkPulse auto-detects these — you don't need to set this manually.

| Platform | Path |
|----------|------|
| Windows | `%USERPROFILE%\.cursor\projects\` |
| macOS | `~/.cursor/projects/` |
| Linux | `~/.cursor/projects/` |

All projects under that folder are watched automatically. New projects are picked up without any config change.

---

## Config file

Persistent config lives at `~/.workpulse/config.json`. Edit it to override defaults:

```json
{
  "transcript_path": "~/.cursor/projects",
  "dashboard_port": 7700,
  "model": "claude-sonnet-4-5",
  "rubric_path": "data/manual_rubric.md",
  "window_size": 3
}
```

---

## How it works (under the hood)

```
Cursor writes .jsonl  →  watchdog detects change
       ↓
Incremental reader (only new bytes since last run)
       ↓
Stage 1 SND — Semantic Novelty Detection (local, no API call)
  └─ low novelty → drop silently
       ↓
Async grading queue (FCFS, background thread)
       ↓
4-stage pipeline:
  Stage 1  SND   — novelty pre-filter
  Stage 2  IOAS  — Intent-Outcome Alignment Scoring
  Stage 3  CTA   — Conversation Trajectory Analysis
  Stage 4  EJAD  — Ensemble + Adversarial Dissenter
       ↓
Result → dashboard SSE + overlay + OS notification (above_bar only)
       ↓
Persisted to ~/.workpulse/results.jsonl
```

---

## Project structure

```
WorkPulse/
├── src/
│   ├── pipeline/
│   │   ├── grader_v2.py        # 4-stage pipeline orchestrator
│   │   ├── stage1_snd.py       # Semantic Novelty Detection
│   │   ├── stage2_ioas.py      # Intent-Outcome Alignment Scoring
│   │   ├── stage3_cta.py       # Conversation Trajectory Analysis
│   │   └── stage4_ejad.py      # Ensemble + Adversarial Dissenter
│   ├── monitor/
│   │   ├── config.py           # Config loading + auto-detection
│   │   ├── watcher.py          # File system watcher (cross-platform)
│   │   ├── queue_worker.py     # Async grading queue
│   │   ├── dashboard.py        # Flask dashboard + SSE
│   │   ├── overlay.py          # Tkinter floating widget (Flask fallback)
│   │   ├── first_run.py        # First-run experience
│   │   ├── bookmarks.py        # Read-offset tracking per file
│   │   └── notifier.py         # OS desktop notifications
│   ├── extractor.py            # Window extraction from JSONL
│   └── cli_monitor.py          # Entry point: workpulse-monitor
├── data/
│   └── manual_rubric.md        # The grading rubric
├── tests/                      # 117 tests
├── requirements.txt
└── setup.py
```

## License

MIT
