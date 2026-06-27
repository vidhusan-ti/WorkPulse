"""Tests for grade persister."""
import json
import os
import tempfile
import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.persister import load_graded_indices, persist_grade


def test_persist_and_load():
    f = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    f.close()
    path = f.name

    window = {"start_index": 5, "end_index": 7, "turns": []}
    grade = {"tier": "above_bar", "label": "outstanding_portfolio", "score": 9,
             "reason": "Test", "coaching": "", "better_prompt": ""}

    persist_grade(path, "/some/transcript.jsonl", window, grade)
    indices = load_graded_indices(path)

    assert "/some/transcript.jsonl" in indices
    assert 5 in indices["/some/transcript.jsonl"]
    os.unlink(path)


def test_load_empty_file():
    f = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    f.close()
    indices = load_graded_indices(f.name)
    assert indices == {}
    os.unlink(f.name)


def test_load_nonexistent_file():
    indices = load_graded_indices("/tmp/does_not_exist_xyz.jsonl")
    assert indices == {}
