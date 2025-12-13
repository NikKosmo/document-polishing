"""Tests for Judge fail-fast behavior.

When the LLM-as-Judge fails (timeout, error, invalid response), the system
should stop immediately rather than continuing with false ambiguities.
"""

import sys
from pathlib import Path

import pytest

# Make scripts/src importable
project_root = Path(__file__).resolve().parents[1]
scripts_src = project_root.joinpath("scripts", "src")
sys.path.insert(0, scripts_src.as_posix())

from ambiguity_detector import (
    AmbiguityDetector,
    LLMJudgeStrategy,
    Interpretation,
    JudgeFailureError,
)


def make_interpretation(model_name, interpretation, steps=None, assumptions=None, ambiguities=None):
    """Helper to create Interpretation objects for testing."""
    return Interpretation(
        model_name=model_name,
        raw_response="",
        interpretation=interpretation,
        steps=steps or [],
        assumptions=assumptions or [],
        ambiguities=ambiguities or []
    )


class TestJudgeFailureError:
    """Tests for JudgeFailureError exception."""

    def test_exception_attributes(self):
        """Exception should store section_id, reason, and details."""
        error = JudgeFailureError(
            section_id="section_0",
            reason="Judge query timeout",
            details="Timeout after 300s"
        )
        
        assert error.section_id == "section_0"
        assert error.reason == "Judge query timeout"
        assert error.details == "Timeout after 300s"

    def test_exception_message_format(self):
        """Exception message should include section_id and reason."""
        error = JudgeFailureError(
            section_id="section_5",
            reason="Invalid response",
            details="Missing 'agree' field"
        )
        
        message = str(error)
        assert "section_5" in message
        assert "Invalid response" in message
        assert "Missing 'agree' field" in message

    def test_exception_without_details(self):
        """Exception should work without details."""
        error = JudgeFailureError(
            section_id="section_0",
            reason="Unknown error"
        )
        
        assert error.section_id == "section_0"
        assert error.reason == "Unknown error"
        assert error.details == ""


class TestLLMJudgeStrategyFailFast:
    """Tests for LLMJudgeStrategy fail-fast behavior."""

    def test_raises_on_judge_error_response(self):
        """Should raise JudgeFailureError when judge returns error."""
        def error_query_func(prompt):
            return {"error": True, "message": "Timeout after 300s"}
        
        strategy = LLMJudgeStrategy(query_func=error_query_func)
        strategy._current_section_id = "section_0"
        
        interpretations = [
            make_interpretation("claude", "interpretation A"),
            make_interpretation("gemini", "interpretation B"),
        ]
        
        with pytest.raises(JudgeFailureError) as exc_info:
            strategy.compare(interpretations)
        
        assert exc_info.value.section_id == "section_0"
        assert "Judge query error" in exc_info.value.reason
        assert "Timeout after 300s" in exc_info.value.details

    def test_raises_on_missing_agree_field(self):
        """Should raise JudgeFailureError when response missing 'agree' field."""
        def invalid_query_func(prompt):
            return {"similarity": 0.5, "explanation": "incomplete response"}
        
        strategy = LLMJudgeStrategy(query_func=invalid_query_func)
        strategy._current_section_id = "section_3"
        
        interpretations = [
            make_interpretation("claude", "interpretation A"),
            make_interpretation("gemini", "interpretation B"),
        ]
        
        with pytest.raises(JudgeFailureError) as exc_info:
            strategy.compare(interpretations)
        
        assert exc_info.value.section_id == "section_3"
        assert "Invalid judge response" in exc_info.value.reason
        assert "agree" in exc_info.value.details

    def test_raises_on_empty_response(self):
        """Should raise JudgeFailureError when judge returns empty response."""
        def empty_query_func(prompt):
            return {}
        
        strategy = LLMJudgeStrategy(query_func=empty_query_func)
        strategy._current_section_id = "section_1"
        
        interpretations = [
            make_interpretation("claude", "interpretation A"),
            make_interpretation("gemini", "interpretation B"),
        ]
        
        with pytest.raises(JudgeFailureError) as exc_info:
            strategy.compare(interpretations)
        
        assert exc_info.value.section_id == "section_1"

    def test_valid_response_does_not_raise(self):
        """Should NOT raise when judge returns valid response."""
        def valid_query_func(prompt):
            return {
                "agree": True,
                "similarity": 0.9,
                "explanation": "Models agree",
                "key_differences": []
            }
        
        strategy = LLMJudgeStrategy(query_func=valid_query_func)
        strategy._current_section_id = "section_0"
        
        interpretations = [
            make_interpretation("claude", "same interpretation"),
            make_interpretation("gemini", "same interpretation"),
        ]
        
        # Should not raise
        result = strategy.compare(interpretations)
        assert result["agree"] is True
        assert result["similarity"] == 0.9

    def test_valid_disagreement_does_not_raise(self):
        """Should NOT raise when judge validly reports disagreement."""
        def disagreement_query_func(prompt):
            return {
                "agree": False,
                "similarity": 0.3,
                "explanation": "Models disagree on format",
                "key_differences": ["date format", "output structure"]
            }
        
        strategy = LLMJudgeStrategy(query_func=disagreement_query_func)
        strategy._current_section_id = "section_0"
        
        interpretations = [
            make_interpretation("claude", "interpretation A"),
            make_interpretation("gemini", "interpretation B"),
        ]
        
        # Should not raise - disagreement is a valid result
        result = strategy.compare(interpretations)
        assert result["agree"] is False
        assert result["similarity"] == 0.3


class TestAmbiguityDetectorFailFast:
    """Tests for AmbiguityDetector fail-fast with LLM judge."""

    def test_detect_raises_on_judge_failure(self):
        """AmbiguityDetector.detect() should propagate JudgeFailureError."""
        def error_query_func(prompt):
            return {"error": True, "message": "Connection refused"}
        
        detector = AmbiguityDetector(
            strategy="llm_judge",
            llm_query_func=error_query_func
        )
        
        test_results = {
            "section_0": {
                "section": {"header": "Test Section", "content": "Some content"},
                "results": {
                    "claude": {"interpretation": "interpretation A", "steps": [], "assumptions": [], "ambiguities": []},
                    "gemini": {"interpretation": "interpretation B", "steps": [], "assumptions": [], "ambiguities": []},
                }
            }
        }
        
        with pytest.raises(JudgeFailureError) as exc_info:
            detector.detect(test_results)
        
        assert exc_info.value.section_id == "section_0"

    def test_detect_stops_at_first_judge_failure(self):
        """Detection should stop at first judge failure, not continue to next section."""
        call_count = {"value": 0}
        
        def failing_query_func(prompt):
            call_count["value"] += 1
            if call_count["value"] == 1:
                return {"error": True, "message": "Timeout"}
            return {"agree": True, "similarity": 1.0, "explanation": "OK", "key_differences": []}
        
        detector = AmbiguityDetector(
            strategy="llm_judge",
            llm_query_func=failing_query_func
        )
        
        test_results = {
            "section_0": {
                "section": {"header": "Section 0", "content": "Content 0"},
                "results": {
                    "claude": {"interpretation": "A", "steps": [], "assumptions": [], "ambiguities": []},
                    "gemini": {"interpretation": "B", "steps": [], "assumptions": [], "ambiguities": []},
                }
            },
            "section_1": {
                "section": {"header": "Section 1", "content": "Content 1"},
                "results": {
                    "claude": {"interpretation": "C", "steps": [], "assumptions": [], "ambiguities": []},
                    "gemini": {"interpretation": "D", "steps": [], "assumptions": [], "ambiguities": []},
                }
            }
        }
        
        with pytest.raises(JudgeFailureError):
            detector.detect(test_results)
        
        # Should have only called judge once (failed on first section)
        assert call_count["value"] == 1

    def test_no_false_ambiguities_on_judge_failure(self):
        """When judge fails, should raise error, NOT return false ambiguities."""
        def error_query_func(prompt):
            return {"error": True, "message": "Service unavailable"}
        
        detector = AmbiguityDetector(
            strategy="llm_judge",
            llm_query_func=error_query_func
        )
        
        test_results = {
            "section_0": {
                "section": {"header": "Test", "content": "Content"},
                "results": {
                    "claude": {"interpretation": "X", "steps": [], "assumptions": [], "ambiguities": []},
                    "gemini": {"interpretation": "Y", "steps": [], "assumptions": [], "ambiguities": []},
                }
            }
        }
        
        # Should raise, not return a list with false ambiguities
        with pytest.raises(JudgeFailureError):
            detector.detect(test_results)


class TestSimpleStrategyUnaffected:
    """Verify simple strategy is NOT affected by fail-fast changes."""

    def test_simple_strategy_works_normally(self):
        """Simple strategy should work without raising JudgeFailureError."""
        detector = AmbiguityDetector(strategy="simple", similarity_threshold=0.7)
        
        test_results = {
            "section_0": {
                "section": {"header": "Test", "content": "Content"},
                "results": {
                    "claude": {"interpretation": "same thing", "steps": [], "assumptions": [], "ambiguities": []},
                    "gemini": {"interpretation": "same thing", "steps": [], "assumptions": [], "ambiguities": []},
                }
            }
        }
        
        # Should not raise
        ambiguities = detector.detect(test_results)
        assert isinstance(ambiguities, list)
