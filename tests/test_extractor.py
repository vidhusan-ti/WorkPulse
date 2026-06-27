"""Tests for the window extractor."""
import json
import os
import tempfile
import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.extractor import load_transcript, extract_windows, get_window_text


def make_jsonl(turns):
    """Create a temp JSONL file with given turns."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8")
    for turn in turns:
        f.write(json.dumps(turn) + "\n")
    f.close()
    return f.name


def test_load_transcript_basic():
    turns = [
        {"type": "user", "text": "Hello"},
        {"type": "assistant", "text": "Hi there"},
    ]
    path = make_jsonl(turns)
    loaded = load_transcript(path)
    assert len(loaded) == 2
    assert loaded[0]["text"] == "Hello"
    os.unlink(path)


def test_extract_windows_basic():
    # extract_windows expects normalised turns (role/text format, as returned by load_transcript)
    turns = [
        {"role": "user", "text": "Q1"},
        {"role": "assistant", "text": "A1"},
        {"role": "user", "text": "Q2"},
        {"role": "assistant", "text": "A2"},
        {"role": "user", "text": "Q3"},
        {"role": "assistant", "text": "A3"},
    ]
    windows = extract_windows(turns, window_size=3)
    # Should produce windows starting at user turns
    assert len(windows) >= 1
    for w in windows:
        assert w["turns"][0]["role"] == "user"


def test_window_text_format():
    # get_window_text expects normalised turns (role/text format)
    window = {
        "turns": [
            {"role": "user", "text": "What is X?"},
            {"role": "assistant", "text": "X is Y."},
        ],
        "start_index": 0,
        "end_index": 1,
    }
    text = get_window_text(window)
    assert "[USER]" in text
    assert "[ASSISTANT]" in text
    assert "What is X?" in text


def test_extract_windows_skips_assistant_start():
    # extract_windows expects normalised turns
    turns = [
        {"role": "assistant", "text": "Welcome"},
        {"role": "user", "text": "Q1"},
        {"role": "assistant", "text": "A1"},
    ]
    windows = extract_windows(turns)
    assert all(w["turns"][0]["role"] == "user" for w in windows)


def test_load_transcript_skips_bad_lines():
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8")
    f.write('{"type": "user", "text": "valid"}\n')
    f.write('not valid json\n')
    f.write('{"type": "assistant", "text": "also valid"}\n')
    f.close()
    turns = load_transcript(f.name)
    assert len(turns) == 2
    os.unlink(f.name)
