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


from src.persister import _focal_prompt_hash, _summarise_trace, deduplicate_session_grades


def test_focal_prompt_hash_same_for_same_prompt():
    window = {"turns": [{"role": "user", "text": "Implement OAuth2 PKCE"}]}
    h1 = _focal_prompt_hash(window)
    h2 = _focal_prompt_hash(window)
    assert h1 == h2
    assert len(h1) == 16


def test_focal_prompt_hash_different_for_different_prompts():
    w1 = {"turns": [{"role": "user", "text": "Implement OAuth2 PKCE"}]}
    w2 = {"turns": [{"role": "user", "text": "Refactor the database layer"}]}
    assert _focal_prompt_hash(w1) != _focal_prompt_hash(w2)


def test_focal_prompt_hash_first_user_turn_only():
    window = {
        "turns": [
            {"role": "assistant", "text": "Here is the suggestion"},
            {"role": "user", "text": "Implement OAuth2 PKCE"},
            {"role": "user", "text": "Second user turn"},
        ]
    }
    # Should hash first user turn only
    w_single = {"turns": [{"role": "user", "text": "Implement OAuth2 PKCE"}]}
    assert _focal_prompt_hash(window) == _focal_prompt_hash(w_single)


def test_summarise_trace_stage1_only():
    trace = {"stage1_snd": {"passed": False, "novelty_score": 0.1}}
    summary = _summarise_trace(trace)
    assert summary["s1_passed"] is False
    assert summary["s1_novelty"] == 0.1
    assert "s2_passed" not in summary


def test_summarise_trace_full():
    trace = {
        "stage1_snd": {"passed": True, "novelty_score": 0.7},
        "stage2_ioas": {"passed": True, "score": 0.8},
        "stage3_cta": {"tier": "above_bar_candidate", "trajectory_delta": "strong"},
        "stage4_ejad": {"passed": True},
    }
    summary = _summarise_trace(trace)
    assert summary["s1_passed"] is True
    assert summary["s2_score"] == 0.8
    assert summary["s3_delta"] == "strong"
    assert summary["s4_passed"] is True


def test_deduplicate_keeps_highest_score():
    grades = [
        {"focal_prompt_hash": "abc123", "score": 5, "tier": "near_bar"},
        {"focal_prompt_hash": "abc123", "score": 8, "tier": "above_bar"},
        {"focal_prompt_hash": "abc123", "score": 3, "tier": "below_bar"},
    ]
    deduped = deduplicate_session_grades(grades)
    assert len(deduped) == 1
    assert deduped[0]["score"] == 8
    assert deduped[0]["tier"] == "above_bar"


def test_deduplicate_preserves_unique_prompts():
    grades = [
        {"focal_prompt_hash": "aaa", "score": 8, "tier": "above_bar"},
        {"focal_prompt_hash": "bbb", "score": 5, "tier": "near_bar"},
        {"focal_prompt_hash": "ccc", "score": 1, "tier": "below_bar"},
    ]
    deduped = deduplicate_session_grades(grades)
    assert len(deduped) == 3


def test_persist_grade_includes_focal_hash():
    import tempfile
    f = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    f.close()
    path = f.name

    window = {
        "start_index": 5, "end_index": 7,
        "turns": [{"role": "user", "text": "Implement OAuth2"}]
    }
    grade = {
        "tier": "above_bar", "label": "outstanding_portfolio", "score": 8,
        "reason": "Test", "coaching": "", "better_prompt": "",
        "pipeline_trace": {"stage1_snd": {"passed": True, "novelty_score": 0.8}},
    }

    persist_grade(path, "/test.jsonl", window, grade)

    with open(path) as f:
        event = json.loads(f.read().strip())

    assert "focal_prompt_hash" in event
    assert len(event["focal_prompt_hash"]) == 16
    assert "pipeline_trace_summary" in event
    assert event["pipeline_trace_summary"]["s1_passed"] is True
    import os; os.unlink(path)
