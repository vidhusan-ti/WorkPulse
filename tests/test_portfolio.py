"""Tests for portfolio.py — entry formatting with trace summary and focal hash."""
import os
import tempfile
import pytest
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.portfolio import append_to_portfolio, _stage_summary_line


def make_window(user_text="Test prompt", has_assistant=True):
    turns = [{"role": "user", "text": user_text}]
    if has_assistant:
        turns.append({"role": "assistant", "text": "Here is the answer."})
    return {"start_index": 0, "end_index": 1, "turns": turns}


def make_grade(tier="above_bar", trace=None):
    return {
        "tier": tier,
        "label": "outstanding_portfolio",
        "score": 8,
        "reason": "User specified concrete requirement.",
        "coaching": "",
        "better_prompt": "",
        "pipeline_trace": trace or {},
    }


class TestStageSummaryLine:
    def test_empty_trace(self):
        line = _stage_summary_line({})
        assert "unavailable" in line.lower()

    def test_full_trace_summary(self):
        summary = {
            "s1_novelty": 0.75,
            "s2_score": 0.82,
            "s3_delta": "strong",
            "s4_passed": True,
        }
        line = _stage_summary_line(summary)
        assert "0.75" in line
        assert "0.82" in line
        assert "strong" in line
        assert "True" in line

    def test_partial_trace(self):
        summary = {"s1_novelty": 0.5}
        line = _stage_summary_line(summary)
        assert "0.50" in line
        assert "|" not in line  # Only one field, no separator

    def test_s1_s2_separator(self):
        summary = {"s1_novelty": 0.5, "s2_score": 0.6}
        line = _stage_summary_line(summary)
        assert " | " in line


class TestAppendToPortfolio:
    def test_creates_file_with_header(self):
        f = tempfile.NamedTemporaryFile(suffix=".md", delete=False)
        f.close()
        os.unlink(f.name)  # Delete so append_to_portfolio creates it fresh

        append_to_portfolio(f.name, make_window(), make_grade())
        with open(f.name) as rf:
            content = rf.read()
        assert "Portfolio" in content
        os.unlink(f.name)

    def test_entry_includes_tier_label(self):
        f = tempfile.NamedTemporaryFile(suffix=".md", delete=False)
        f.close()
        append_to_portfolio(f.name, make_window(), make_grade())
        with open(f.name) as rf:
            content = rf.read()
        assert "Outstanding Portfolio" in content
        assert "8/10" in content
        os.unlink(f.name)

    def test_entry_includes_focal_hash(self):
        f = tempfile.NamedTemporaryFile(suffix=".md", delete=False)
        f.close()
        append_to_portfolio(f.name, make_window("Unique prompt for hash test"), make_grade())
        with open(f.name) as rf:
            content = rf.read()
        assert "**Hash:**" in content
        os.unlink(f.name)

    def test_entry_includes_pipeline_trace(self):
        trace = {
            "stage1_snd": {"passed": True, "novelty_score": 0.7},
            "stage2_ioas": {"passed": True, "score": 0.85},
            "stage3_cta": {"tier": "above_bar_candidate", "trajectory_delta": "strong"},
            "stage4_ejad": {"passed": True},
        }
        f = tempfile.NamedTemporaryFile(suffix=".md", delete=False)
        f.close()
        append_to_portfolio(f.name, make_window(), make_grade(trace=trace))
        with open(f.name) as rf:
            content = rf.read()
        assert "**Pipeline:**" in content
        assert "strong" in content
        os.unlink(f.name)

    def test_appends_multiple_entries(self):
        f = tempfile.NamedTemporaryFile(suffix=".md", delete=False)
        f.close()
        os.unlink(f.name)
        append_to_portfolio(f.name, make_window("First prompt"), make_grade())
        append_to_portfolio(f.name, make_window("Second prompt"), make_grade())
        with open(f.name) as rf:
            content = rf.read()
        assert content.count("---") >= 2
        os.unlink(f.name)

    def test_includes_user_prompt_text(self):
        user_text = "Implement exponential backoff with jitter for all retry calls."
        f = tempfile.NamedTemporaryFile(suffix=".md", delete=False)
        f.close()
        append_to_portfolio(f.name, make_window(user_text), make_grade())
        with open(f.name) as rf:
            content = rf.read()
        assert user_text in content
        os.unlink(f.name)
