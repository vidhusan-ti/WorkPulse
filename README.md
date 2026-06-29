# WorkPulse — AI Prompt Coach for Cursor

Monitors your Cursor conversations in real-time and gives you feedback on your prompting quality.

## What It Does

- **Watches** your Cursor transcript files as you work
- **Grades** each conversation window against the WorkPulse rubric
- **Above bar** → asks you to approve saving it to your portfolio
- **Near bar** → coaching popup explaining what was missing and how to improve
- **Below bar** → silently ignored (no noise)
- **10-minute nudge** → if you haven't had a quality prompt in 10 minutes, a floating reminder appears

## Quick Start

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Setup
```bash
python main.py --setup
```
This will ask for your Cursor transcript path and LLM API key.

### 3. Run
```bash
python main.py
```

### Environment Variables
Instead of storing your API key in config, set it as an env var:
```bash
export OPENAI_API_KEY=sk-...   # for OpenAI
export ANTHROPIC_API_KEY=...   # for Anthropic
```

## Configuration

Edit `config/settings.json`:

| Key | Description | Default |
|-----|-------------|---------|
| `transcript_glob` | Glob path to Cursor JSONL files | *(set in setup)* |
| `check_interval_seconds` | How often to poll for changes | 60 |
| `inactive_after_minutes` | Minutes before inactivity nudge | 10 |
| `llm_provider` | `openai` or `anthropic` | `openai` |
| `llm_model` | Model name | `gpt-4o` |
| `llm_max_grades_per_cycle` | Max windows graded per check | 3 |
| `use_pipeline_v2` | Use 4-stage pipeline v2 (recommended) | `true` |

## Cursor Transcript Location

| Platform | Path |
|----------|------|
| Windows | `C:\Users\<name>\.cursor\projects\*\agent-transcripts\*\*.jsonl` |
| macOS | `~/Library/Application Support/Cursor/User/globalStorage/cursor.agent/agent-transcripts/*/*.jsonl` |
| Linux | `~/.config/Cursor/User/globalStorage/cursor.agent/agent-transcripts/*/*.jsonl` |

## Running Tests
```bash
pytest tests/
```

## Project Structure
```
workpulse/
├── src/
│   ├── pipeline/              # 4-stage grading pipeline v2
│   │   ├── __init__.py        # Public API: grade_window_v2
│   │   ├── grader_v2.py       # Pipeline orchestrator
│   │   ├── stage1_snd.py      # Semantic Novelty Detection
│   │   ├── stage2_ioas.py     # Intent-Outcome Alignment Scoring
│   │   ├── stage3_cta.py      # Conversation Trajectory Analysis
│   │   └── stage4_ejad.py     # Ensemble + Adversarial Dissenter
│   ├── watcher.py             # File system watcher (cross-platform)
│   ├── extractor.py           # Window extraction from JSONL
│   ├── grader.py              # LLM grader v1 (legacy)
│   ├── monitor.py             # Main loop — wires all components
│   ├── persister.py           # Grade storage + SWOD deduplication
│   ├── notifier.py            # Notification router + 10-min timer
│   ├── popup.py               # Floating overlay UI (tkinter)
│   └── portfolio.py           # portfolio.md writer
├── data/
│   ├── manual_rubric.md     # The grading rubric
│   ├── graded_events.jsonl  # Grade history
│   └── portfolio.md         # Your approved portfolio
├── config/settings.json
├── main.py
└── README.md
```

---

## WorkPulse Monitor

Real-time Cursor transcript watcher with automatic grading, OS notifications, and a live web dashboard.

### Install

```bash
pip install git+https://github.com/vidhusan-ti/WorkPulse.git
```

Or from source:

```bash
git clone https://github.com/vidhusan-ti/WorkPulse.git
cd WorkPulse
pip install -e .
```

### Setup

Create a `.env` file in your project root:

```
ANTHROPIC_API_KEY=your_key_here
```

Or export it directly:

```bash
export ANTHROPIC_API_KEY=your_key_here
```

### Run

```bash
workpulse-monitor --path /path/to/cursor/transcripts
```

Options:

```
--path PATH    Directory to watch for Cursor .jsonl files (auto-detected if omitted)
--port PORT    Dashboard port (default: 7700)
--model MODEL  Anthropic model (default: claude-sonnet-4-5)
--verbose      Enable debug logging
```

### Dashboard

Open [http://localhost:7700](http://localhost:7700) in your browser.

The dashboard shows:
- Live running status + uptime
- Real-time feed of `above_bar` and `near_bar` results via Server-Sent Events
- Full prompt text, verdict, score, and which rubric criteria passed/failed
- Coaching advice and rewritten prompt suggestions for near-bar results

### Config file

Persistent config at `~/.workpulse/config.json`:

```json
{
  "transcript_path": "/path/to/cursor/transcripts",
  "dashboard_port": 7700,
  "model": "claude-sonnet-4-5",
  "rubric_path": "data/manual_rubric.md"
}
```

### How it works

1. **File watching** — `watchdog` watches the transcript directory recursively for new/modified `.jsonl` files
2. **Incremental reading** — Only new bytes are read since the last run (bookmarked per file in `~/.workpulse/bookmarks.json`)
3. **SND pre-filter** — Stage 1 Semantic Novelty Detection runs locally (no API call) to discard low-novelty turns
4. **Async grading** — Windows that pass SND are queued and graded in the background (FCFS order) without blocking the watcher
5. **Notifications** — `above_bar` results trigger a native OS desktop notification
6. **Dashboard** — Results streamed live to the browser via SSE; persisted to `~/.workpulse/results.jsonl`
