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
