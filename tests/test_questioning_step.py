"""Tests for whole-document questioning (Step 5)."""

import json
import sys
from pathlib import Path

import pytest
import yaml

# Add scripts and scripts/src to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "src"))

import polish  # noqa: E402
import test_questions  # noqa: E402
from questioning_step import (  # noqa: E402
    QuestionSetValidationError,
    assign_verdict,
    calculate_document_score,
    calculate_question_score,
    load_question_set,
    map_issue_to_severity,
)


class TestYamlLoading:
    """Validate question-set YAML loading and schema checks."""

    def test_load_valid_question_set(self, tmp_path):
        question_set_path = tmp_path / "questions.yaml"
        payload = {
            "version": "1.0",
            "document": "doc.md",
            "bulky_source": "bulky.md",
            "created": "2026-03-05",
            "author": "nik",
            "description": "test",
            "questions": [
                {
                    "id": "q1",
                    "question": "What should happen?",
                    "category": "authorization",
                    "difficulty": "standard",
                    "assertions": ["a1"],
                    "expected": {
                        "key_points": ["Only user can merge"],
                        "anti_points": ["Yes merge now"],
                        "notes": "Coverage rationale",
                    },
                }
            ],
            "metadata": {"question_count": 1},
        }
        question_set_path.write_text(yaml.safe_dump(payload), encoding="utf-8")

        question_set = load_question_set(str(question_set_path))

        assert question_set.version == "1.0"
        assert question_set.document == "doc.md"
        assert question_set.bulky_source == "bulky.md"
        assert question_set.created == "2026-03-05"
        assert question_set.author == "nik"
        assert question_set.description == "test"
        assert len(question_set.questions) == 1
        assert question_set.questions[0].id == "q1"
        assert question_set.questions[0].expected.key_points == ["Only user can merge"]

    @pytest.mark.parametrize("missing_field", ["version", "document", "questions"])
    def test_missing_required_top_level_field_raises(self, tmp_path, missing_field):
        payload = {"version": "1.0", "document": "doc.md", "questions": []}
        payload.pop(missing_field)
        path = tmp_path / "questions.yaml"
        path.write_text(yaml.safe_dump(payload), encoding="utf-8")

        with pytest.raises(QuestionSetValidationError, match=f"Missing required field: {missing_field}"):
            load_question_set(str(path))

    @pytest.mark.parametrize(
        "question_payload,error_match",
        [
            ({"question": "Q", "expected": {"key_points": ["x"]}}, "questions\\[0\\]\\.id"),
            ({"id": "q1", "question": "Q", "expected": {}}, "expected.key_points"),
        ],
    )
    def test_malformed_question_raises(self, tmp_path, question_payload, error_match):
        payload = {"version": "1.0", "document": "doc.md", "questions": [question_payload]}
        path = tmp_path / "questions.yaml"
        path.write_text(yaml.safe_dump(payload), encoding="utf-8")

        with pytest.raises(QuestionSetValidationError, match=error_match):
            load_question_set(str(path))


class TestVerdicts:
    """Validate four verdict assignment paths."""

    def test_verdict_correct(self):
        assert assign_verdict(3, 3, has_anti_points=False, is_evasive=False) == "correct"

    def test_verdict_partial(self):
        assert assign_verdict(1, 2, has_anti_points=False, is_evasive=False) == "partial"

    def test_verdict_incorrect(self):
        assert assign_verdict(1, 3, has_anti_points=False, is_evasive=False) == "incorrect"
        assert assign_verdict(3, 3, has_anti_points=True, is_evasive=False) == "incorrect"

    def test_verdict_evasive(self):
        assert assign_verdict(0, 3, has_anti_points=False, is_evasive=True) == "evasive"


class TestScoring:
    """Validate Step 5 scoring formula."""

    def test_score_matched_div_total(self):
        assert calculate_question_score(2, 4, has_anti_points=False) == 0.5

    def test_score_anti_point_penalty_zeroes(self):
        assert calculate_question_score(4, 4, has_anti_points=True) == 0.0

    def test_score_floor_max_zero(self):
        assert calculate_question_score(1, 4, has_anti_points=True) == 0.0

    def test_document_score_is_mean(self):
        scores = {"q1": 1.0, "q2": 0.5, "q3": 0.0}
        assert calculate_document_score(scores) == pytest.approx(0.5)


class TestIssueSeverityMapping:
    """Validate issue type to ambiguity severity mapping."""

    @pytest.mark.parametrize(
        "issue_type,expected",
        [
            ("conflict not detected", "critical"),
            ("false premise accepted", "high"),
            ("incorrect answer", "high"),
            ("partially correct", "medium"),
            ("adversarial failure", "medium"),
        ],
    )
    def test_issue_mapping(self, issue_type, expected):
        assert map_issue_to_severity(issue_type).value == expected


class TestQuestionCliParsing:
    """Validate new test_questions.py CLI contract."""

    def test_questions_flag_is_required(self):
        parser = test_questions.build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_document_flag_is_required(self):
        parser = test_questions.build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--questions", "q.yaml"])

    def test_models_and_judge_optional_with_defaults(self):
        parser = test_questions.build_parser()
        args = parser.parse_args(["--questions", "q.yaml", "--document", "doc.md"])

        assert args.questions == "q.yaml"
        assert args.document == "doc.md"
        assert args.models is None
        assert args.judge == "claude"


class TestPolishIntegration:
    """Validate polish.py integration for Step 5 invocation/skip."""

    @pytest.fixture
    def base_setup(self, tmp_path):
        doc = tmp_path / "doc.md"
        doc.write_text("# Test\n\ncontent", encoding="utf-8")

        workspace_dir = tmp_path / "workspace"
        config = {
            "models": {
                "claude": {"type": "cli", "command": "claude", "args": ["-p"], "enabled": True},
                "gemini": {"type": "cli", "command": "gemini", "args": [], "enabled": True},
            },
            "profiles": {
                "standard": {"models": ["claude", "gemini"], "iterations": 1},
            },
            "settings": {
                "default_profile": "standard",
                "workspace_dir": str(workspace_dir),
                "output_dir": str(tmp_path / "output"),
            },
            "session_management": {"enabled": False},
        }
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

        return {"doc": doc, "config": config_path, "workspace": workspace_dir, "tmp": tmp_path}

    def _patch_pipeline(self, monkeypatch):
        class StubExtractionResult:
            def __init__(self):
                self.sections = [{"header": "H", "content": "C"}]
                self.summary = []
                self.document_content = "doc content"

            def save(self, output_path):
                Path(output_path).write_text(json.dumps({"sections": self.sections}), encoding="utf-8")

        class StubExtractionStep:
            def __init__(self, _document_path):
                pass

            def extract(self):
                return StubExtractionResult()

        class StubTestingResult:
            def __init__(self):
                self.test_results = {"section_0": {"section": {}, "results": {"claude": {"raw_response": "ok"}}}}

            def save(self, output_path):
                Path(output_path).write_text(json.dumps(self.test_results), encoding="utf-8")

        class StubTestingStep:
            def __init__(self, *_args, **_kwargs):
                pass

            def test_sections(self, *_args, **_kwargs):
                return StubTestingResult()

        class StubDetectionResult:
            def __init__(self):
                self.ambiguities = []
                self.severity_counts = {}

            def save(self, output_path):
                Path(output_path).write_text("[]", encoding="utf-8")

        class StubDetectionStep:
            def __init__(self, *_args, **_kwargs):
                pass

            def detect(self, _test_results):
                return StubDetectionResult()

        class StubReportingStep:
            def __init__(self, *_args, **_kwargs):
                self.question_result_seen = None

            def generate_report(self, _test_results, _ambiguities, _models, question_result=None):
                self.question_result_seen = question_result
                return "# report"

            def generate_polished_document(self, document_content, _ambiguities):
                return document_content

        monkeypatch.setattr(polish, "ExtractionStep", StubExtractionStep)
        monkeypatch.setattr(polish, "TestingStep", StubTestingStep)
        monkeypatch.setattr(polish, "DetectionStep", StubDetectionStep)
        monkeypatch.setattr(polish, "ReportingStep", StubReportingStep)

    def test_with_questions_invokes_step5(self, base_setup, monkeypatch):
        self._patch_pipeline(monkeypatch)

        called = {"run": False}

        class StubQuestionResult:
            def __init__(self):
                self.question_set = type("QS", (), {"questions": []})
                self.model_names = ["claude"]
                self.evaluations = {}
                self.document_score = 0.0
                self.issues = []

            def save(self, workspace_path):
                wp = Path(workspace_path)
                wp.mkdir(parents=True, exist_ok=True)
                (wp / "question_responses.json").write_text("{}", encoding="utf-8")
                (wp / "question_evaluations.json").write_text("{}", encoding="utf-8")

        class StubQuestioningStep:
            def __init__(self, *_args, **_kwargs):
                pass

            def run(self, *args, **kwargs):
                called["run"] = True
                return StubQuestionResult()

        monkeypatch.setattr(polish, "QuestioningStep", StubQuestioningStep)

        question_yaml = base_setup["tmp"] / "questions.yaml"
        question_yaml.write_text(
            yaml.safe_dump(
                {
                    "version": "1.0",
                    "document": base_setup["doc"].name,
                    "questions": [
                        {
                            "id": "q1",
                            "question": "Q?",
                            "category": "general",
                            "difficulty": "standard",
                            "expected": {"key_points": ["k1"], "anti_points": []},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        polisher = polish.DocumentPolisher(str(base_setup["doc"]), str(base_setup["config"]))
        polisher.polish(models=["claude"], questions_path=str(question_yaml))

        assert called["run"] is True

    def test_without_questions_skips_step5_and_logs(self, base_setup, monkeypatch, capsys):
        self._patch_pipeline(monkeypatch)

        class FailingQuestioningStep:
            def __init__(self, *_args, **_kwargs):
                pass

            def run(self, *args, **kwargs):
                raise AssertionError("Questioning step should not run")

        monkeypatch.setattr(polish, "QuestioningStep", FailingQuestioningStep)

        polisher = polish.DocumentPolisher(str(base_setup["doc"]), str(base_setup["config"]))
        polisher.polish(models=["claude"], questions_path=None)

        captured = capsys.readouterr()
        assert "Step 5: Question testing -- skipped" in captured.out
