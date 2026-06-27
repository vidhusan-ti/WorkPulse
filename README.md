# WorkPulse — AI Prompt Coach for Cursor

Monitors your Cursor conversations in real-time and gives you feedback on your prompting quality.

## What It Does

- **Watches** your Cursor transcript files as you work
- **Grades** each conversation window against the WorkPulse rubric
- **Above bar** → asks you to approve saving it to your portfolio
- **Near bar** → coaching popup explaining what was missing and how to improve
- **Average** → silently ignored (no noise)
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
│   ├── watcher.py      # File system watcher (cross-platform)
│   ├── extractor.py    # Window extraction from JSONL
│   ├── grader.py       # LLM grader
│   ├── persister.py    # Grade storage
│   ├── notifier.py     # Notification router + 10-min timer
│   ├── popup.py        # Floating overlay UI (tkinter)
│   └── portfolio.py    # portfolio.md writer
├── data/
│   ├── manual_rubric.md     # The grading rubric
│   ├── graded_events.jsonl  # Grade history
│   └── portfolio.md         # Your approved portfolio
├── config/settings.json
├── main.py
└── README.md
```
