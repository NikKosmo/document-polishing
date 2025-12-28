"""
Test shared ambiguity detection functionality.

This test verifies that the judge prompt asks about shared ambiguities
and that the detection logic correctly flags sections where models
agree on interpretation but all noted similar concerns.
"""

import pytest
import sys
from pathlib import Path

# Add scripts/src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts' / 'src'))

from ambiguity_detector import (
    LLMJudgeStrategy,
    AmbiguityDetector,
    Interpretation,
    Severity
)


class TestSharedAmbiguityPrompt:
    """Test that judge prompt includes shared ambiguity instructions"""

    def setup_method(self):
        """Set up test fixtures."""
        # Create strategy with a dummy query function
        self.strategy = LLMJudgeStrategy(query_func=lambda x: {})

    def test_prompt_includes_shared_ambiguity_instruction(self):
        """Verify prompt asks judge to check for shared ambiguities"""
        interpretations = [
            Interpretation(
                model_name="claude",
                raw_response="{}",
                interpretation="Set timeout appropriately",
                steps=[],
                assumptions=[],
                ambiguities=["timeout value not specified"]
            ),
            Interpretation(
                model_name="gemini",
                raw_response="{}",
                interpretation="Configure timeout setting",
                steps=[],
                assumptions=[],
                ambiguities=["what is appropriate timeout?"]
            )
        ]

        prompt = self.strategy._build_comparison_prompt(interpretations)

        # Check for shared ambiguity instruction
        assert "shared" in prompt.lower() or "similar" in prompt.lower(), \
            "Prompt should mention checking for shared/similar ambiguities"
        assert "noted ambiguities:" in prompt.lower(), \
            "Prompt should include model ambiguities"


class TestSharedAmbiguityResponse:
    """Test that response parsing handles shared ambiguity fields"""

    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = LLMJudgeStrategy(query_func=lambda x: {})

    def test_parse_response_with_shared_ambiguities(self):
        """Verify parser extracts shared_ambiguities and shared_concerns"""

        interpretations = [
            Interpretation(
                model_name="claude",
                raw_response="{}",
                interpretation="Set timeout",
                steps=[],
                assumptions=[],
                ambiguities=["timeout value unclear"]
            ),
            Interpretation(
                model_name="gemini",
                raw_response="{}",
                interpretation="Configure timeout",
                steps=[],
                assumptions=[],
                ambiguities=["timeout not specified"]
            )
        ]

        # Mock judge response with shared ambiguities
        judge_response = {
            'agree': True,
            'similarity': 0.9,
            'explanation': 'Models agree on interpretation',
            'key_differences': [],
            'shared_ambiguities': True,
            'shared_concerns': ['timeout value not specified']
        }

        result = self.strategy._parse_judge_response(judge_response, interpretations)

        assert result['shared_ambiguities'] == True
        assert result['shared_concerns'] == ['timeout value not specified']


    def test_parse_response_without_shared_ambiguities(self):
        """Verify parser handles missing shared_ambiguities gracefully"""

        interpretations = [
            Interpretation(
                model_name="claude",
                raw_response="{}",
                interpretation="Do X",
                steps=[],
                assumptions=[],
                ambiguities=[]
            ),
            Interpretation(
                model_name="gemini",
                raw_response="{}",
                interpretation="Do X",
                steps=[],
                assumptions=[],
                ambiguities=[]
            )
        ]

        # Judge response without shared ambiguities fields
        judge_response = {
            'agree': True,
            'similarity': 0.95,
            'explanation': 'Models agree',
            'key_differences': []
        }

        result = self.strategy._parse_judge_response(judge_response, interpretations)

        # Should default to False and empty list
        assert result['shared_ambiguities'] == False
        assert result['shared_concerns'] == []


class TestSharedAmbiguityDetection:
    """Test that detector flags sections with shared ambiguities"""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = AmbiguityDetector(strategy="simple")

    def test_flags_section_with_shared_ambiguities(self, monkeypatch):
        """Verify detector creates ambiguity for shared concerns"""
        # Mock comparison result with shared ambiguities
        def mock_compare(interpretations):
            return {
                'agree': True,
                'similarity': 0.9,
                'details': 'Models agree',
                'groups': [['claude', 'gemini']],
                'key_differences': [],
                'shared_ambiguities': True,
                'shared_concerns': ['timeout value unclear']
            }

        monkeypatch.setattr(self.detector.strategy, 'compare', mock_compare)

        test_results = {
            'section_1': {
                'section': {
                    'header': 'Configuration',
                    'content': 'Set timeout appropriately.'
                },
                'results': {
                    'claude': {
                        'interpretation': 'Configure timeout',
                        'steps': [],
                        'assumptions': [],
                        'ambiguities': ['timeout value not specified']
                    },
                    'gemini': {
                        'interpretation': 'Set timeout setting',
                        'steps': [],
                        'assumptions': [],
                        'ambiguities': ['what is appropriate timeout?']
                    }
                }
            }
        }

        ambiguities = self.detector.detect(test_results)

        assert len(ambiguities) == 1
        assert ambiguities[0].comparison_details['reason'] == 'Models agreed but all noted similar concerns'
        assert ambiguities[0].comparison_details['shared_concerns'] == ['timeout value unclear']


    def test_severity_medium_for_three_models(self, monkeypatch):
        """Verify MEDIUM severity when 3 models share concern"""
        def mock_compare(interpretations):
            return {
                'agree': True,
                'similarity': 0.85,
                'details': 'Models agree',
                'groups': [['claude', 'gemini', 'codex']],
                'key_differences': [],
                'shared_ambiguities': True,
                'shared_concerns': ['timeout value unclear']
            }

        monkeypatch.setattr(self.detector.strategy, 'compare', mock_compare)

        test_results = {
            'section_1': {
                'section': {
                    'header': 'Configuration',
                    'content': 'Set timeout appropriately.'
                },
                'results': {
                    'claude': {
                        'interpretation': 'Configure timeout',
                        'steps': [],
                        'assumptions': [],
                        'ambiguities': ['timeout value not specified']
                    },
                    'gemini': {
                        'interpretation': 'Set timeout setting',
                        'steps': [],
                        'assumptions': [],
                        'ambiguities': ['what is appropriate timeout?']
                    },
                    'codex': {
                        'interpretation': 'Set timeout',
                        'steps': [],
                        'assumptions': [],
                        'ambiguities': ['timeout value unclear']
                    }
                }
            }
        }

        ambiguities = self.detector.detect(test_results)

        assert len(ambiguities) == 1
        assert ambiguities[0].severity == Severity.MEDIUM


    def test_severity_low_for_two_models(self, monkeypatch):
        """Verify LOW severity when only 2 models share concern"""
        def mock_compare(interpretations):
            return {
                'agree': True,
                'similarity': 0.85,
                'details': 'Models agree',
                'groups': [['claude', 'gemini']],
                'key_differences': [],
                'shared_ambiguities': True,
                'shared_concerns': ['timeout value unclear']
            }

        monkeypatch.setattr(self.detector.strategy, 'compare', mock_compare)

        test_results = {
            'section_1': {
                'section': {
                    'header': 'Configuration',
                    'content': 'Set timeout appropriately.'
                },
                'results': {
                    'claude': {
                        'interpretation': 'Configure timeout',
                        'steps': [],
                        'assumptions': [],
                        'ambiguities': ['timeout value not specified']
                    },
                    'gemini': {
                        'interpretation': 'Set timeout setting',
                        'steps': [],
                        'assumptions': [],
                        'ambiguities': ['what is appropriate timeout?']
                    }
                }
            }
        }

        ambiguities = self.detector.detect(test_results)

        assert len(ambiguities) == 1
        assert ambiguities[0].severity == Severity.LOW


    def test_no_flag_without_shared_ambiguities(self, monkeypatch):
        """Verify no ambiguity flagged when shared_ambiguities is False"""
        def mock_compare(interpretations):
            return {
                'agree': True,
                'similarity': 0.95,
                'details': 'Models agree completely',
                'groups': [['claude', 'gemini']],
                'key_differences': [],
                'shared_ambiguities': False,
                'shared_concerns': []
            }

        monkeypatch.setattr(self.detector.strategy, 'compare', mock_compare)

        test_results = {
            'section_1': {
                'section': {
                    'header': 'Simple Section',
                    'content': 'Clear instruction.'
                },
                'results': {
                    'claude': {
                        'interpretation': 'Do clear thing',
                        'steps': [],
                        'assumptions': [],
                        'ambiguities': []
                    },
                    'gemini': {
                        'interpretation': 'Do clear thing',
                        'steps': [],
                        'assumptions': [],
                        'ambiguities': []
                    }
                }
            }
        }

        ambiguities = self.detector.detect(test_results)

        assert len(ambiguities) == 0
