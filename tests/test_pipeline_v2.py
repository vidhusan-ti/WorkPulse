"""
tests/test_pipeline_v2.py — Integration tests for the WorkPulse v2 pipeline.

Covers:
  - Stage 1 (SND): Semantic Novelty Detection with known above/below-bar windows
  - Stage 1 early-exit: short prompts and confirmations should fail
  - Stage 1 novelty: novel user prompts should pass
  - Pipeline trace: correct keys are populated per stage
  - grader_v2: below-bar windows stop at stage 1 (no later stages in trace)
  - grader_v2: above-bar windows populate all 4 stages (with LLM mock)

All LLM-calling stages (2, 3, 4) are unit-tested with mocked LLM calls to
avoid requiring real API credentials. Stage 1 uses only local heuristics
(no LLM), so it is tested without mocks.
"""

from __future__ import annotations

import json
import sys
import os
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pipeline.stage1_snd import run_stage1, NOVELTY_THRESHOLD
from src.pipeline.stage2_ioas import run_stage2
from src.pipeline.stage3_cta import run_stage3
from src.pipeline.stage4_ejad import run_stage4
from src.pipeline.grader_v2 import grade_window_v2


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _window(*turns):
    return {"turns": [{"role": r, "text": t} for r, t in turns]}


WINDOW_EMPTY_USER = _window(("user", ""), ("assistant", "Sure, here you go."))

WINDOW_ONE_WORD_YES = _window(
    ("assistant", "I've refactored the function to use list comprehension. Should I proceed?"),
    ("user", "yes"),
)

WINDOW_ONE_WORD_OK = _window(
    ("assistant", "I'll update the import to use absolute paths."),
    ("user", "ok"),
)

WINDOW_VERY_SHORT = _window(
    ("assistant", "The error is caused by a missing semicolon in line 42."),
    ("user", "fix it"),
)

WINDOW_RESTATE_LLM = _window(
    ("assistant", "The solution is to refactor the database connection pool to use lazy initialisation."),
    # Near-verbatim restate that Jaccard detects as low-novelty (score ~0.18)
    ("user", "Refactor the database connection pool to use lazy initialisation."),
)

# This window has: prior assistant context, then focal user turn, then LLM response
# so Stage 2 can find both the user prompt and the LLM response.
WINDOW_NOVEL_INSIGHT = _window(
    ("user", "Actually, a singleton will cause issues in our test suite because tests share state. "
             "Use dependency injection instead — pass the cache as a constructor argument. "
             "That way each test can inject a fresh in-memory cache."),
    ("assistant", "Good point — here is the dependency injection implementation for the cache manager."),
)

WINDOW_FRESH_START = _window(
    ("user", "Rewrite the authentication module to support OAuth2 with PKCE flow. "
             "We need this because our mobile clients can't securely store client secrets."),
)

WINDOW_NOVEL_CORRECTION = _window(
    ("user", "Retries are wrong here — the downstream service charges per call. "
             "Instead, implement a circuit breaker so we fail fast when the service is degraded "
             "rather than hammering it with retries that rack up charges."),
    ("assistant", "Understood — here is the circuit breaker implementation instead of retry logic."),
)


# ===========================================================================
# Stage 1 (SND)
# ===========================================================================

class TestStage1SND:
    def test_empty_user_text_fails(self):
        result = run_stage1(WINDOW_EMPTY_USER)
        assert result["passed"] is False
        assert result["novelty_score"] == 0.0

    def test_empty_window_fails(self):
        result = run_stage1({"turns": []})
        assert result["passed"] is False

    def test_single_word_yes_fails(self):
        result = run_stage1(WINDOW_ONE_WORD_YES)
        assert result["passed"] is False
        assert result["novelty_score"] < NOVELTY_THRESHOLD

    def test_single_word_ok_fails(self):
        result = run_stage1(WINDOW_ONE_WORD_OK)
        assert result["passed"] is False
        assert result["novelty_score"] < NOVELTY_THRESHOLD

    def test_very_short_prompt_fails(self):
        result = run_stage1(WINDOW_VERY_SHORT)
        assert result["passed"] is False

    def test_fresh_window_no_prior_assistant_passes(self):
        result = run_stage1(WINDOW_FRESH_START)
        assert result["passed"] is True
        assert result["novelty_score"] == 1.0

    def test_novel_correction_passes(self):
        result = run_stage1(WINDOW_NOVEL_CORRECTION)
        assert result["passed"] is True
        assert result["novelty_score"] >= NOVELTY_THRESHOLD

    def test_restate_llm_output_fails(self):
        result = run_stage1(WINDOW_RESTATE_LLM)
        assert result["passed"] is False
        assert result["novelty_score"] < NOVELTY_THRESHOLD

    def test_result_keys_present(self):
        result = run_stage1(WINDOW_NOVEL_INSIGHT)
        assert "passed" in result
        assert "novelty_score" in result
        assert "reason" in result

    def test_novelty_score_is_float_in_range(self):
        result = run_stage1(WINDOW_NOVEL_INSIGHT)
        assert isinstance(result["novelty_score"], float)
        assert 0.0 <= result["novelty_score"] <= 1.0

    def test_no_turns_fails(self):
        result = run_stage1({})
        assert result["passed"] is False

    def test_only_assistant_turns_fails(self):
        window = _window(("assistant", "Here is a detailed explanation of the algorithm."))
        result = run_stage1(window)
        assert result["passed"] is False


# ===========================================================================
# Stage 2 (IOAS) — mocked LLM
# ===========================================================================

class TestStage2IOAS:
    GOOD_RESPONSE = json.dumps({
        "intent": "User wants to replace singleton with dependency injection",
        "intent_clarity": 0.9,
        "outcome_precision": 0.85,
        "reasoning": "Clear intent, well-served by LLM.",
    })

    LOW_RESPONSE = json.dumps({
        "intent": "Vague request",
        "intent_clarity": 0.3,
        "outcome_precision": 0.4,
        "reasoning": "User was vague; LLM guessed.",
    })

    def _run(self, window, mock_response):
        with patch("src.pipeline.stage2_ioas._call_llm_with_retry", return_value=mock_response):
            return run_stage2(window, provider="openai", model="gpt-4o", api_key="test")

    def test_high_scores_pass(self):
        result = self._run(WINDOW_NOVEL_INSIGHT, self.GOOD_RESPONSE)
        assert result["passed"] is True
        assert result["score"] > 0.45

    def test_low_scores_fail(self):
        result = self._run(WINDOW_NOVEL_INSIGHT, self.LOW_RESPONSE)
        assert result["passed"] is False
        assert result["score"] < 0.45

    def test_result_keys_present(self):
        result = self._run(WINDOW_NOVEL_INSIGHT, self.GOOD_RESPONSE)
        for key in ("passed", "score", "intent", "reasoning"):
            assert key in result

    def test_llm_failure_returns_fallback(self):
        with patch("src.pipeline.stage2_ioas._call_llm_with_retry", return_value=None):
            result = run_stage2(WINDOW_NOVEL_INSIGHT, provider="openai", model="gpt-4o", api_key="test")
        assert result["passed"] is False
        assert result["score"] == 0.0

    def test_malformed_json_returns_fallback(self):
        with patch("src.pipeline.stage2_ioas._call_llm_with_retry", return_value="not json at all"):
            result = run_stage2(WINDOW_NOVEL_INSIGHT, provider="openai", model="gpt-4o", api_key="test")
        assert result["passed"] is False

    def test_missing_keys_returns_fallback(self):
        partial = json.dumps({"intent": "x"})
        with patch("src.pipeline.stage2_ioas._call_llm_with_retry", return_value=partial):
            result = run_stage2(WINDOW_NOVEL_INSIGHT, provider="openai", model="gpt-4o", api_key="test")
        assert result["passed"] is False

    def test_no_user_turn_returns_fallback(self):
        window = _window(("assistant", "Here is the result."))
        with patch("src.pipeline.stage2_ioas._call_llm_with_retry", return_value=self.GOOD_RESPONSE):
            result = run_stage2(window, provider="openai", model="gpt-4o", api_key="test")
        assert result["passed"] is False

    def test_scores_clamped_to_range(self):
        response = json.dumps({
            "intent": "test",
            "intent_clarity": 1.5,
            "outcome_precision": -0.1,
            "reasoning": "clamping test",
        })
        with patch("src.pipeline.stage2_ioas._call_llm_with_retry", return_value=response):
            result = run_stage2(WINDOW_NOVEL_INSIGHT, provider="openai", model="gpt-4o", api_key="test")
        assert result["score"] == 0.0


# ===========================================================================
# Stage 3 (CTA) — mocked LLM
# ===========================================================================

class TestStage3CTA:
    STRONG_RESPONSE = json.dumps({"trajectory_delta": "strong", "reasoning": "Conversation advanced."})
    MODERATE_RESPONSE = json.dumps({"trajectory_delta": "moderate", "reasoning": "Noticeable improvement."})
    WEAK_RESPONSE = json.dumps({"trajectory_delta": "weak", "reasoning": "Minor change."})
    NONE_RESPONSE = json.dumps({"trajectory_delta": "none", "reasoning": "No improvement."})

    def _run(self, window, mock_response):
        with patch("src.pipeline.stage3_cta._call_llm_with_retry", return_value=mock_response):
            return run_stage3(window, provider="openai", model="gpt-4o", api_key="test")

    def test_strong_delta_above_bar_candidate(self):
        result = self._run(WINDOW_NOVEL_INSIGHT, self.STRONG_RESPONSE)
        assert result["tier"] == "above_bar_candidate"
        assert result["trajectory_delta"] == "strong"

    def test_moderate_delta_above_bar_candidate(self):
        result = self._run(WINDOW_NOVEL_INSIGHT, self.MODERATE_RESPONSE)
        assert result["tier"] == "above_bar_candidate"

    def test_weak_delta_near_bar(self):
        result = self._run(WINDOW_NOVEL_INSIGHT, self.WEAK_RESPONSE)
        assert result["tier"] == "near_bar"

    def test_none_delta_near_bar(self):
        result = self._run(WINDOW_NOVEL_INSIGHT, self.NONE_RESPONSE)
        assert result["tier"] == "near_bar"

    def test_result_keys_present(self):
        result = self._run(WINDOW_NOVEL_INSIGHT, self.STRONG_RESPONSE)
        for key in ("tier", "trajectory_delta", "reasoning"):
            assert key in result

    def test_llm_failure_defaults_near_bar(self):
        with patch("src.pipeline.stage3_cta._call_llm_with_retry", return_value=None):
            result = run_stage3(WINDOW_NOVEL_INSIGHT, provider="openai", model="gpt-4o", api_key="test")
        assert result["tier"] == "near_bar"

    def test_invalid_delta_fallback(self):
        bad = json.dumps({"trajectory_delta": "excellent", "reasoning": "x"})
        with patch("src.pipeline.stage3_cta._call_llm_with_retry", return_value=bad):
            result = run_stage3(WINDOW_NOVEL_INSIGHT, provider="openai", model="gpt-4o", api_key="test")
        assert result["tier"] == "near_bar"

    def test_no_follow_up_turns(self):
        """End of transcript — user turn with no follow-up — should still work."""
        window = _window(
            ("user", "Can you explain dependency injection with a real example?"),
        )
        with patch("src.pipeline.stage3_cta._call_llm_with_retry", return_value=self.MODERATE_RESPONSE):
            result = run_stage3(window, provider="openai", model="gpt-4o", api_key="test")
        assert result["tier"] == "above_bar_candidate"

    def test_end_of_transcript_user_plus_assistant(self):
        window = _window(
            ("user", "Rewrite the cache to support TTL expiry with lazy eviction."),
            ("assistant", "Here is the updated cache implementation with TTL eviction..."),
        )
        with patch("src.pipeline.stage3_cta._call_llm_with_retry", return_value=self.STRONG_RESPONSE):
            result = run_stage3(window, provider="openai", model="gpt-4o", api_key="test")
        assert result["tier"] == "above_bar_candidate"


# ===========================================================================
# Stage 4 (EJAD) — mocked LLM
# ===========================================================================

class TestStage4EJAD:
    BOTH_ABOVE_BAR = json.dumps({
        "judge_a": {"verdict": "above_bar", "confidence": 0.9, "reasoning": "Strong user insight."},
        "judge_b": {"verdict": "above_bar", "confidence": 0.85, "reasoning": "Clear user ownership."},
    })

    JUDGE_A_DISAGREES = json.dumps({
        "judge_a": {"verdict": "not_above_bar", "confidence": 0.7, "reasoning": "User echoed LLM."},
        "judge_b": {"verdict": "above_bar", "confidence": 0.6, "reasoning": "Some novelty."},
    })

    WEAK_DISSENTER = json.dumps({
        "objections": ["Minor paraphrasing"],
        "confidence_not_above_bar": 0.2,
        "summary": "Objections are weak; prompt is user-driven.",
    })

    STRONG_DISSENTER = json.dumps({
        "objections": ["User restating LLM output", "No original insight", "LLM supplied the core idea"],
        "confidence_not_above_bar": 0.85,
        "summary": "User clearly echoed LLM output — not above-bar.",
    })

    def _run_sequence(self, window, *responses):
        call_count = [0]
        def mock_call(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            return responses[idx] if idx < len(responses) else None
        with patch("src.pipeline.stage4_ejad._call_llm_with_retry", side_effect=mock_call):
            result = run_stage4(window, provider="openai", model="gpt-4o", api_key="test")
        return result, call_count[0]

    def test_both_agree_weak_dissenter_passes(self):
        result, _ = self._run_sequence(WINDOW_NOVEL_INSIGHT, self.BOTH_ABOVE_BAR, self.WEAK_DISSENTER)
        assert result["passed"] is True

    def test_both_agree_strong_dissenter_fails(self):
        result, _ = self._run_sequence(WINDOW_NOVEL_INSIGHT, self.BOTH_ABOVE_BAR, self.STRONG_DISSENTER)
        assert result["passed"] is False

    def test_judges_disagree_skips_dissenter(self):
        result, calls = self._run_sequence(WINDOW_NOVEL_INSIGHT, self.JUDGE_A_DISAGREES)
        assert result["passed"] is False
        assert calls == 1  # Only standard judges call; no dissenter

    def test_result_keys_present(self):
        result, _ = self._run_sequence(WINDOW_NOVEL_INSIGHT, self.BOTH_ABOVE_BAR, self.WEAK_DISSENTER)
        for key in ("passed", "standard_verdict", "dissenter_objection", "final_reasoning"):
            assert key in result

    def test_standard_judge_failure_fallback(self):
        with patch("src.pipeline.stage4_ejad._call_llm_with_retry", return_value=None):
            result = run_stage4(WINDOW_NOVEL_INSIGHT, provider="openai", model="gpt-4o", api_key="test")
        assert result["passed"] is False


# ===========================================================================
# grader_v2 integration
# ===========================================================================

class TestGraderV2:
    RUBRIC_PATH = "data/manual_rubric.md"

    S2_PASS = json.dumps({
        "intent": "Refactor for DI",
        "intent_clarity": 0.9,
        "outcome_precision": 0.88,
        "reasoning": "Clear and well-served.",
    })

    S3_STRONG = json.dumps({"trajectory_delta": "strong", "reasoning": "Significant advance."})

    S4_JUDGES = json.dumps({
        "judge_a": {"verdict": "above_bar", "confidence": 0.9, "reasoning": "Strong."},
        "judge_b": {"verdict": "above_bar", "confidence": 0.88, "reasoning": "Clear."},
    })

    S4_DISSENTER_WEAK = json.dumps({
        "objections": [],
        "confidence_not_above_bar": 0.15,
        "summary": "No significant objections.",
    })

    def test_below_bar_stops_at_stage1(self):
        result = grade_window_v2(
            WINDOW_ONE_WORD_YES, rubric_path=self.RUBRIC_PATH,
            provider="openai", model="gpt-4o", api_key="test",
        )
        assert result["tier"] == "below_bar"
        trace = result["pipeline_trace"]
        assert "stage1_snd" in trace
        assert "stage2_ioas" not in trace
        assert "stage3_cta" not in trace
        assert "stage4_ejad" not in trace

    def test_empty_user_below_bar_stage1(self):
        result = grade_window_v2(
            WINDOW_EMPTY_USER, rubric_path=self.RUBRIC_PATH,
            provider="openai", model="gpt-4o", api_key="test",
        )
        assert result["tier"] == "below_bar"
        assert "stage2_ioas" not in result["pipeline_trace"]

    def test_below_bar_at_stage2_trace(self):
        s2_fail = json.dumps({
            "intent": "vague",
            "intent_clarity": 0.2,
            "outcome_precision": 0.3,
            "reasoning": "User was vague.",
        })
        with patch("src.pipeline.stage2_ioas._call_llm_with_retry", return_value=s2_fail):
            result = grade_window_v2(
                WINDOW_NOVEL_INSIGHT, rubric_path=self.RUBRIC_PATH,
                provider="openai", model="gpt-4o", api_key="test",
            )
        assert result["tier"] == "below_bar"
        trace = result["pipeline_trace"]
        assert "stage1_snd" in trace
        assert "stage2_ioas" in trace
        assert "stage3_cta" not in trace

    def test_near_bar_at_stage3_trace(self):
        s3_weak = json.dumps({"trajectory_delta": "weak", "reasoning": "Minor change."})
        coaching_mock = json.dumps({"coaching": "Try harder.", "better_prompt": "Do X specifically."})
        with patch("src.pipeline.stage2_ioas._call_llm_with_retry", return_value=self.S2_PASS):
            with patch("src.pipeline.stage3_cta._call_llm_with_retry", return_value=s3_weak):
                with patch("src.pipeline.grader_v2._call_openai_raw", return_value=coaching_mock):
                    result = grade_window_v2(
                        WINDOW_NOVEL_INSIGHT, rubric_path=self.RUBRIC_PATH,
                        provider="openai", model="gpt-4o", api_key="test",
                    )
        assert result["tier"] == "near_bar"
        trace = result["pipeline_trace"]
        assert "stage1_snd" in trace
        assert "stage2_ioas" in trace
        assert "stage3_cta" in trace
        assert "stage4_ejad" not in trace

    def test_above_bar_all_4_stages(self):
        s4_responses = [self.S4_JUDGES, self.S4_DISSENTER_WEAK]
        s4_idx = [0]
        def mock_s4(*args, **kwargs):
            idx = s4_idx[0]; s4_idx[0] += 1
            return s4_responses[idx] if idx < len(s4_responses) else None

        with patch("src.pipeline.stage2_ioas._call_llm_with_retry", return_value=self.S2_PASS):
            with patch("src.pipeline.stage3_cta._call_llm_with_retry", return_value=self.S3_STRONG):
                with patch("src.pipeline.stage4_ejad._call_llm_with_retry", side_effect=mock_s4):
                    result = grade_window_v2(
                        WINDOW_NOVEL_INSIGHT, rubric_path=self.RUBRIC_PATH,
                        provider="openai", model="gpt-4o", api_key="test",
                    )
        assert result["tier"] == "above_bar"
        for stage in ("stage1_snd", "stage2_ioas", "stage3_cta", "stage4_ejad"):
            assert stage in result["pipeline_trace"], f"Missing {stage}"

    def test_result_always_has_required_keys(self):
        result = grade_window_v2(
            WINDOW_ONE_WORD_YES, rubric_path=self.RUBRIC_PATH,
            provider="openai", model="gpt-4o", api_key="test",
        )
        for key in ("tier", "label", "score", "reason", "coaching", "better_prompt", "pipeline_trace"):
            assert key in result

    def test_below_bar_score_is_low(self):
        result = grade_window_v2(
            WINDOW_ONE_WORD_YES, rubric_path=self.RUBRIC_PATH,
            provider="openai", model="gpt-4o", api_key="test",
        )
        assert result["score"] <= 3

    def test_stage1_passed_is_bool(self):
        result = grade_window_v2(
            WINDOW_ONE_WORD_YES, rubric_path=self.RUBRIC_PATH,
            provider="openai", model="gpt-4o", api_key="test",
        )
        assert isinstance(result["pipeline_trace"]["stage1_snd"]["passed"], bool)

    def test_restate_window_below_bar(self):
        result = grade_window_v2(
            WINDOW_RESTATE_LLM, rubric_path=self.RUBRIC_PATH,
            provider="openai", model="gpt-4o", api_key="test",
        )
        assert result["tier"] == "below_bar"


# ===========================================================================
# Template Coaching Fallback Tests
# ===========================================================================

class TestTemplateCoachinFallback:
    """Tests for the template_coaching fallback in grader_v2."""

    def test_stage2_intent_failure_message(self):
        from src.pipeline.grader_v2 import _template_coaching
        result = _template_coaching("Stage 2 (IOAS) failed: intent-outcome alignment score 0.120 below threshold.")
        assert "Stage 2" in result
        assert len(result) > 50

    def test_stage3_trajectory_failure_message(self):
        from src.pipeline.grader_v2 import _template_coaching
        result = _template_coaching("Stage 3 (CTA): trajectory delta is 'weak'.")
        assert "Stage 3" in result or "trajectory" in result.lower()

    def test_stage4_ejad_failure_message(self):
        from src.pipeline.grader_v2 import _template_coaching
        result = _template_coaching("Stage 4 (EJAD) did not confirm above-bar. Dissenter raised strong objections.")
        assert "Stage 4" in result or "dissenter" in result.lower()

    def test_generic_fallback_message(self):
        from src.pipeline.grader_v2 import _template_coaching
        result = _template_coaching("Some unknown pipeline reason.")
        assert len(result) > 50
        assert "above-bar" in result or "LLM" in result

    def test_near_bar_coaching_not_empty_on_llm_failure(self):
        """When coaching LLM call fails, grader_v2 should return template coaching, not empty."""
        from src.pipeline.grader_v2 import grade_window_v2
        s2_pass = '{"intent": "x", "intent_clarity": 0.9, "outcome_precision": 0.9, "reasoning": "ok"}'
        s3_weak = '{"trajectory_delta": "weak", "reasoning": "minor"}'
        window = {
            "turns": [
                {"role": "user", "text": "Refactor the auth module to use OAuth2 PKCE."},
                {"role": "assistant", "text": "Here is the OAuth2 PKCE implementation."},
            ]
        }
        with patch("src.pipeline.stage2_ioas._call_llm_with_retry", return_value=s2_pass):
            with patch("src.pipeline.stage3_cta._call_llm_with_retry", return_value=s3_weak):
                # Make coaching LLM call fail
                with patch("src.pipeline.grader_v2._call_openai_raw", side_effect=Exception("timeout")):
                    result = grade_window_v2(
                        window, rubric_path="data/manual_rubric.md",
                        provider="openai", model="gpt-4o", api_key="test",
                    )
        assert result["tier"] == "near_bar"
        # Coaching should not be empty — template fallback should kick in
        assert result["coaching"] != ""
        assert len(result["coaching"]) > 20


# ===========================================================================
# Label Refinement Tests
# ===========================================================================

class TestLabelRefinement:
    """Tests for _refine_above_bar_label and _refine_near_bar_label."""

    def test_above_bar_default_label_outstanding(self):
        from src.pipeline.grader_v2 import _refine_above_bar_label
        trace = {"stage4_ejad": {"final_reasoning": "Both judges agreed. confidence=0.25"}}
        label, score = _refine_above_bar_label(trace)
        assert label == "outstanding_portfolio"
        assert score == 8

    def test_above_bar_very_weak_dissenter_mindblowing(self):
        from src.pipeline.grader_v2 import _refine_above_bar_label
        trace = {"stage4_ejad": {"final_reasoning": "All passed. confidence=0.10 is low."}}
        label, score = _refine_above_bar_label(trace)
        assert label == "mindblowing_portfolio"
        assert score == 9

    def test_above_bar_no_s4_trace_defaults_outstanding(self):
        from src.pipeline.grader_v2 import _refine_above_bar_label
        label, score = _refine_above_bar_label({})
        assert label == "outstanding_portfolio"
        assert score == 8

    def test_near_bar_high_ioas_moderate_trajectory_mindblowing(self):
        from src.pipeline.grader_v2 import _refine_near_bar_label
        trace = {
            "stage2_ioas": {"score": 0.72},
            "stage3_cta": {"trajectory_delta": "moderate"},
        }
        label, score = _refine_near_bar_label(trace)
        assert label == "mindblowing_highlight"
        assert score == 6

    def test_near_bar_medium_ioas_strong_highlight(self):
        from src.pipeline.grader_v2 import _refine_near_bar_label
        trace = {
            "stage2_ioas": {"score": 0.52},
            "stage3_cta": {"trajectory_delta": "weak"},
        }
        label, score = _refine_near_bar_label(trace)
        assert label == "strong_highlight"

    def test_near_bar_low_scores_strong_highlight(self):
        from src.pipeline.grader_v2 import _refine_near_bar_label
        trace = {
            "stage2_ioas": {"score": 0.20},
            "stage3_cta": {"trajectory_delta": "none"},
        }
        label, score = _refine_near_bar_label(trace)
        assert label == "strong_highlight"
        assert score == 4

    def test_grader_near_bar_uses_refinement(self):
        """near_bar result uses refined label, not hardcoded string."""
        from src.pipeline.grader_v2 import grade_window_v2
        import json
        s2_high = json.dumps({
            "intent": "x", "intent_clarity": 0.9, "outcome_precision": 0.85, "reasoning": "ok"
        })
        s3_moderate = json.dumps({"trajectory_delta": "moderate", "reasoning": "noticeable"})
        coaching_mock = json.dumps({"coaching": "Try this.", "better_prompt": "Do X."})
        window = {
            "turns": [
                {"role": "user", "text": "Refactor to use dependency injection for testability."},
                {"role": "assistant", "text": "Here is the DI implementation."},
            ]
        }
        with patch("src.pipeline.stage2_ioas._call_llm_with_retry", return_value=s2_high):
            with patch("src.pipeline.stage3_cta._call_llm_with_retry", return_value=s3_moderate):
                with patch("src.pipeline.grader_v2._call_openai_raw", return_value=coaching_mock):
                    result = grade_window_v2(
                        window, rubric_path="data/manual_rubric.md",
                        provider="openai", model="gpt-4o", api_key="test",
                    )
        assert result["tier"] == "near_bar"
        # With high S2 score (0.765) and moderate trajectory → mindblowing_highlight
        assert result["label"] in ("mindblowing_highlight", "strong_highlight")
        assert result["score"] >= 4


class TestStage2CoachingOnFailure:
    """Stage 2 failures should now generate coaching, not empty strings."""

    def test_stage2_below_bar_gets_coaching(self):
        """When Stage 2 fails, below_bar result should have non-empty coaching."""
        from src.pipeline.grader_v2 import grade_window_v2
        import json

        s1_pass_window = {
            "turns": [
                {"role": "user", "text": "Implement dependency injection for all service classes."},
                {"role": "assistant", "text": "The strategy pattern would work better here."},
            ]
        }
        # Mock Stage 1 to pass, Stage 2 to fail (low score)
        s1_pass = {"passed": True, "novelty_score": 0.85, "reason": "Novel", "method": "jaccard"}
        s2_fail = json.dumps({
            "intent": "code refactor", "intent_clarity": 0.1, "outcome_precision": 0.05,
            "reasoning": "User gave no constraints, LLM did all thinking."
        })
        coaching_mock = json.dumps({
            "coaching": "Add specific requirements to your prompt.",
            "better_prompt": "Refactor X to use Y pattern because Z."
        })

        with patch("src.pipeline.grader_v2.run_stage1", return_value=s1_pass):
            with patch("src.pipeline.stage2_ioas._call_llm_with_retry", return_value=s2_fail):
                with patch("src.pipeline.grader_v2._call_openai_raw", return_value=coaching_mock):
                    result = grade_window_v2(
                        s1_pass_window,
                        rubric_path="data/manual_rubric.md",
                        provider="openai", model="gpt-4o", api_key="test",
                    )

        assert result["tier"] == "below_bar"
        # The key assertion: below_bar from Stage 2 now gets coaching
        assert result["coaching"] != ""
        assert len(result["coaching"]) > 10

    def test_stage1_below_bar_no_coaching(self):
        """Stage 1 failures (low novelty) should NOT generate coaching — it's just spam."""
        from src.pipeline.grader_v2 import grade_window_v2
        import json

        restate_window = {
            "turns": [
                {"role": "user", "text": "Use lazy initialisation for the connection pool."},
                {"role": "assistant", "text": "Use lazy initialisation for the connection pool."},
            ]
        }

        with patch("src.pipeline.stage1_snd._jaccard_novelty", return_value=0.0):
            result = grade_window_v2(
                restate_window,
                rubric_path="data/manual_rubric.md",
                provider="openai", model="gpt-4o", api_key="test",
            )

        assert result["tier"] == "below_bar"
        # Stage 1 failures: no coaching (too noisy, low-quality signal)
        assert result["coaching"] == ""
