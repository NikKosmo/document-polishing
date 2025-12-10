"""Tests for filtering out faulty/empty interpretations before sending to judge."""

import sys
from pathlib import Path

# Make scripts/src importable
project_root = Path(__file__).resolve().parents[1]
scripts_src = project_root.joinpath("scripts", "src")
sys.path.insert(0, scripts_src.as_posix())

from ambiguity_detector import AmbiguityDetector, Interpretation


class TestInterpretationFromResponse:
    """Tests for Interpretation.from_response() method."""

    def test_error_response_sets_error_field(self):
        """Error responses should have error field set."""
        response = {"error": True, "message": "Timeout after 180s"}
        interp = Interpretation.from_response("gemini", response)

        assert interp.error == "Timeout after 180s"
        assert interp.interpretation == ""

    def test_raw_response_without_interpretation(self):
        """Raw response (failed JSON parse) creates interpretation with empty string."""
        response = {"error": False, "raw_response": "```js\n{invalid json}\n```"}
        interp = Interpretation.from_response("gemini", response)

        assert interp.error is None
        assert interp.interpretation == ""

    def test_valid_response_has_interpretation(self):
        """Valid parsed response has interpretation field populated."""
        response = {
            "interpretation": "This is a valid interpretation",
            "steps": ["Step 1"],
            "assumptions": [],
            "ambiguities": []
        }
        interp = Interpretation.from_response("claude", response)

        assert interp.error is None
        assert interp.interpretation == "This is a valid interpretation"


class TestFilterFaultyInterpretations:
    """Tests for filtering faulty/empty interpretations in AmbiguityDetector.detect()."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = AmbiguityDetector(strategy="simple")

    def test_filters_out_error_responses(self):
        """Interpretations with error should be filtered out."""
        test_results = {
            "section_0": {
                "section": {"header": "Test", "content": "Test content"},
                "results": {
                    "claude": {
                        "interpretation": "Valid interpretation",
                        "steps": [],
                        "assumptions": [],
                        "ambiguities": []
                    },
                    "gemini": {
                        "error": True,
                        "message": "Timeout after 180s"
                    },
                    "codex": {
                        "interpretation": "Another valid interpretation",
                        "steps": [],
                        "assumptions": [],
                        "ambiguities": []
                    }
                }
            }
        }

        # Should not raise and should compare only claude and codex
        ambiguities = self.detector.detect(test_results)
        # If detected, check only valid models are in interpretations
        for amb in ambiguities:
            assert "gemini" not in amb.interpretations

    def test_filters_out_empty_interpretations(self):
        """Interpretations with empty string should be filtered out."""
        test_results = {
            "section_0": {
                "section": {"header": "Test", "content": "Test content"},
                "results": {
                    "claude": {
                        "interpretation": "Valid interpretation",
                        "steps": [],
                        "assumptions": [],
                        "ambiguities": []
                    },
                    "gemini": {
                        "error": False,
                        "raw_response": "```js\n{some invalid json}\n```"
                    },
                    "codex": {
                        "interpretation": "Another valid interpretation",
                        "steps": [],
                        "assumptions": [],
                        "ambiguities": []
                    }
                }
            }
        }

        ambiguities = self.detector.detect(test_results)
        for amb in ambiguities:
            assert "gemini" not in amb.interpretations

    def test_filters_out_whitespace_only_interpretations(self):
        """Interpretations with only whitespace should be filtered out."""
        test_results = {
            "section_0": {
                "section": {"header": "Test", "content": "Test content"},
                "results": {
                    "claude": {
                        "interpretation": "Valid interpretation",
                        "steps": [],
                        "assumptions": [],
                        "ambiguities": []
                    },
                    "gemini": {
                        "interpretation": "   \n\t  ",
                        "steps": [],
                        "assumptions": [],
                        "ambiguities": []
                    },
                    "codex": {
                        "interpretation": "Another valid interpretation",
                        "steps": [],
                        "assumptions": [],
                        "ambiguities": []
                    }
                }
            }
        }

        ambiguities = self.detector.detect(test_results)
        for amb in ambiguities:
            assert "gemini" not in amb.interpretations

    def test_skips_section_with_less_than_two_valid_interpretations(self):
        """Sections with fewer than 2 valid interpretations should be skipped."""
        test_results = {
            "section_0": {
                "section": {"header": "Test", "content": "Test content"},
                "results": {
                    "claude": {
                        "interpretation": "Only valid interpretation",
                        "steps": [],
                        "assumptions": [],
                        "ambiguities": []
                    },
                    "gemini": {
                        "error": True,
                        "message": "Timeout"
                    },
                    "codex": {
                        "error": False,
                        "raw_response": "unparseable response"
                    }
                }
            }
        }

        ambiguities = self.detector.detect(test_results)
        # Section should be skipped entirely since only 1 valid interpretation
        assert len(ambiguities) == 0

    def test_processes_section_with_two_valid_interpretations(self):
        """Sections with exactly 2 valid interpretations should be processed."""
        test_results = {
            "section_0": {
                "section": {"header": "Test", "content": "Test content"},
                "results": {
                    "claude": {
                        "interpretation": "Interpretation A with specific details",
                        "steps": ["Do X", "Do Y"],
                        "assumptions": ["Assume Z"],
                        "ambiguities": []
                    },
                    "gemini": {
                        "error": True,
                        "message": "Timeout"
                    },
                    "codex": {
                        "interpretation": "Interpretation B with different approach",
                        "steps": ["Do P", "Do Q"],
                        "assumptions": [],
                        "ambiguities": []
                    }
                }
            }
        }

        # Should process with claude and codex only
        ambiguities = self.detector.detect(test_results)
        # Check that if any ambiguity is found, it only contains claude and codex
        for amb in ambiguities:
            assert set(amb.interpretations.keys()) == {"claude", "codex"}

    def test_real_world_scenario_gemini_raw_response(self):
        """Test real-world scenario where Gemini returns raw_response instead of parsed JSON."""
        test_results = {
            "section_7": {
                "section": {
                    "header": "Cross-Project TODOs",
                    "content": "**Root `TODO.md`** should track cross-project items"
                },
                "results": {
                    "claude": {
                        "interpretation": "The root TODO.md file should be used exclusively for tasks that span multiple projects",
                        "steps": ["Create or maintain a TODO.md file at the root level"],
                        "assumptions": ["Priority levels follow standard convention"],
                        "ambiguities": ["What exactly constitutes a cross-project dependency?"]
                    },
                    "gemini": {
                        "error": False,
                        "raw_response": "```js\n{\"interpretation\": \"some text\"}\n```"
                    },
                    "codex": {
                        "interpretation": "The root TODO.md must maintain a consolidated list of cross-project efforts",
                        "steps": ["Open the root TODO.md file"],
                        "assumptions": ["Cross-project scope means initiatives that impact more than one project"],
                        "ambiguities": ["Not specified how often TODO.md should be updated"]
                    }
                }
            }
        }

        ambiguities = self.detector.detect(test_results)
        # Gemini should be filtered out, only claude and codex compared
        for amb in ambiguities:
            assert "gemini" not in amb.interpretations
            assert "claude" in amb.interpretations
            assert "codex" in amb.interpretations
