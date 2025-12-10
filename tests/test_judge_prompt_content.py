"""Tests for LLMJudgeStrategy._build_comparison_prompt() to verify all required parts are included."""

import sys
from pathlib import Path

# Make scripts/src importable
project_root = Path(__file__).resolve().parents[1]
scripts_src = project_root.joinpath("scripts", "src")
sys.path.insert(0, scripts_src.as_posix())

from ambiguity_detector import LLMJudgeStrategy, Interpretation


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


class TestBuildComparisonPrompt:
    """Tests for _build_comparison_prompt method."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create strategy with a dummy query function (not used in these tests)
        self.strategy = LLMJudgeStrategy(query_func=lambda x: {})

    def test_includes_interpretation(self):
        """Prompt should include the interpretation text."""
        interpretations = [
            make_interpretation("claude", "This is Claude's interpretation"),
            make_interpretation("gemini", "This is Gemini's interpretation"),
        ]

        prompt = self.strategy._build_comparison_prompt(interpretations)

        assert "This is Claude's interpretation" in prompt
        assert "This is Gemini's interpretation" in prompt

    def test_includes_steps(self):
        """Prompt should include steps when present."""
        interpretations = [
            make_interpretation("claude", "interpretation", steps=["Step 1", "Step 2"]),
            make_interpretation("gemini", "interpretation", steps=["Do A", "Do B"]),
        ]

        prompt = self.strategy._build_comparison_prompt(interpretations)

        assert "Steps:" in prompt
        assert "Step 1" in prompt
        assert "Step 2" in prompt
        assert "Do A" in prompt
        assert "Do B" in prompt

    def test_includes_assumptions(self):
        """Prompt should include assumptions when present."""
        interpretations = [
            make_interpretation("claude", "interpretation", assumptions=["Assumed X", "Assumed Y"]),
            make_interpretation("gemini", "interpretation", assumptions=["Assumed Z"]),
        ]

        prompt = self.strategy._build_comparison_prompt(interpretations)

        assert "Assumptions made:" in prompt
        assert "Assumed X" in prompt
        assert "Assumed Y" in prompt
        assert "Assumed Z" in prompt

    def test_includes_ambiguities(self):
        """Prompt should include model-noted ambiguities when present."""
        interpretations = [
            make_interpretation("claude", "interpretation", ambiguities=["What does date mean?", "Priority unclear"]),
            make_interpretation("gemini", "interpretation", ambiguities=["Date format ambiguous"]),
        ]

        prompt = self.strategy._build_comparison_prompt(interpretations)

        assert "Noted ambiguities:" in prompt
        assert "What does date mean?" in prompt
        assert "Priority unclear" in prompt
        assert "Date format ambiguous" in prompt

    def test_includes_model_names(self):
        """Prompt should include model names for each interpretation."""
        interpretations = [
            make_interpretation("claude", "interpretation 1"),
            make_interpretation("gemini", "interpretation 2"),
        ]

        prompt = self.strategy._build_comparison_prompt(interpretations)

        assert "claude" in prompt
        assert "gemini" in prompt

    def test_omits_empty_fields(self):
        """Prompt should not include section headers for empty fields."""
        interpretations = [
            make_interpretation("claude", "interpretation", steps=[], assumptions=[], ambiguities=[]),
            make_interpretation("gemini", "interpretation", steps=[], assumptions=[], ambiguities=[]),
        ]

        prompt = self.strategy._build_comparison_prompt(interpretations)

        # Should not have these headers when fields are empty
        assert "Steps:" not in prompt
        assert "Assumptions made:" not in prompt
        assert "Noted ambiguities:" not in prompt

    def test_includes_all_fields_together(self):
        """Prompt should include all fields when all are present."""
        interpretations = [
            make_interpretation(
                "claude",
                "Claude understands it this way",
                steps=["Parse input", "Process data"],
                assumptions=["Input is valid JSON"],
                ambiguities=["What format for dates?"]
            ),
            make_interpretation(
                "gemini",
                "Gemini sees it differently",
                steps=["Read file", "Extract info"],
                assumptions=["File exists"],
                ambiguities=["Which encoding to use?"]
            ),
        ]

        prompt = self.strategy._build_comparison_prompt(interpretations)

        # Check all interpretations are present
        assert "Claude understands it this way" in prompt
        assert "Gemini sees it differently" in prompt

        # Check all steps
        assert "Parse input" in prompt
        assert "Read file" in prompt

        # Check all assumptions
        assert "Input is valid JSON" in prompt
        assert "File exists" in prompt

        # Check all ambiguities
        assert "What format for dates?" in prompt
        assert "Which encoding to use?" in prompt
