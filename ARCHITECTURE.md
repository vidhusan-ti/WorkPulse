# ARCHITECTURE.md — WorkPulse

## System Overview

```
Cursor JSONL Files
       │
       ▼
┌─────────────────┐
│  File Watcher   │  (watchdog — cross-platform)
│  transcript_    │  Detects new/modified JSONL files
│  watcher.py     │
└────────┬────────┘
         │ new turns detected
         ▼
┌─────────────────┐
│ Window Extractor│  Reads JSONL, extracts sliding
│ window_         │  windows of ~3 turns
│ extractor.py    │  Skips already-graded turns
└────────┬────────┘
         │ windows
         ▼
┌─────────────────┐
│    Grader       │  Sends window to LLM with rubric
│    grader.py    │  as system prompt
│                 │  Returns: tier + reason + coaching
└────────┬────────┘
         │ grade result
         ▼
┌─────────────────┐
│ Grade Persister │  Appends to graded_events.jsonl
│ persister.py    │  Tracks graded turn indices
└────────┬────────┘
         │ grade result
         ▼
┌─────────────────────────────────────────┐
│           Notification Router            │
│           notifier.py                   │
│                                         │
│  above_bar  → Approval Popup            │
│  near_bar   → Coaching Popup            │
│  below_bar  → (silent, ignored)         │
│                                         │
│  10-min timer → Inactivity Nudge Popup  │
└────────┬────────────────────────────────┘
         │ user approves
         ▼
┌─────────────────┐
│ Portfolio Writer│  Appends approved windows
│ portfolio.py    │  to portfolio.md
└─────────────────┘
```

## File Structure (Proposed)

```
workpulse/
├── src/
│   ├── __init__.py
│   ├── watcher.py          # File system watcher
│   ├── extractor.py        # Window extraction from JSONL
│   ├── grader.py           # LLM grader
│   ├── persister.py        # Grade storage
│   ├── notifier.py         # Notification router + 10-min timer
│   ├── popup.py            # Floating overlay UI
│   └── portfolio.py        # Portfolio.md writer
├── data/
│   ├── manual_rubric.md    # The rubric (used as system prompt)
│   ├── graded_events.jsonl # Grade history
│   └── portfolio.md        # Approved portfolio entries
├── config/
│   └── settings.json       # User config (cross-platform paths)
├── tests/
│   ├── test_extractor.py
│   ├── test_grader.py
│   └── test_notifier.py
├── requirements.txt
├── main.py                 # CLI entry point
└── README.md
```

## Data Flow Detail

### JSONL Turn Format (from Cursor)
```json
{
  "type": "user" | "assistant",
  "text": "...",
  "timestamp": 1234567890
}
```

### Window Format (internal)
```json
{
  "turns": [
    {"type": "user", "text": "...", "timestamp": ...},
    {"type": "assistant", "text": "...", "timestamp": ...},
    {"type": "user", "text": "...", "timestamp": ...}
  ],
  "transcript_path": "...",
  "start_index": 10,
  "end_index": 12
}
```

### Grade Result Format (internal)
```json
{
  "tier": "above_bar" | "near_bar" | "below_bar",
  "label": "mindblowing_portfolio" | "outstanding_portfolio" | "strong_highlight" | "mindblowing_highlight" | "below_bar",
  "score": 0-10,
  "reason": "...",
  "coaching": "...",
  "better_prompt": "...",
  "window": { ... }
}
```

## Key Design Decisions

1. **Polling vs Event-driven:** Use watchdog for file events + poll every 60s as fallback
2. **Window overlap:** Windows slide by 1 turn (overlapping) to catch cross-turn insights
3. **Deduplication:** Track graded turn indices in a state file to avoid re-grading
4. **LLM cost control:** Grade max 3 windows per cycle (configurable)
5. **Popup UI:** Single persistent overlay window, notifications queue inside it

## Pending Decisions

- LLM provider (D-008)
- Popup UI framework (D-009)
