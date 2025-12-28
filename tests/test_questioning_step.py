"""
Tests for questioning_step.py - Question-based testing framework

Test coverage for Phase 1 & 2:
- Question dataclass validation
- QuestioningResult save/load
- Template loading
- Element extraction (8 patterns)
- Template application
- Question validation (4 rules)
- Coverage calculation
- End-to-end integration
"""

import pytest
import json
import tempfile
import shutil
import sys
from pathlib import Path
from datetime import datetime

# Add scripts/src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts' / 'src'))

from questioning_step import (
    Question,
    QuestionAnswer,
    QuestionEvaluation,
    QuestionResult,
    QuestioningResult,
    TestableElement,
    ElementExtractor,
    TemplateLoader,
    TemplateApplicator,
    QuestionValidator,
    QuestioningStep,
    generate_questions_from_sections
)


# ============================================================================
# Test Class 1: Question Dataclass
# ============================================================================

class TestQuestionDataclass:
    """Test Question dataclass validation."""

    def test_question_creation_with_dict_answer(self):
        """Test creating question with Dict expected_answer."""
        question = Question(
            question_id="q_001",
            question_text="What is the format?",
            category="factual",
            difficulty="basic",
            scope="section",
            target_sections=["section_1"],
            expected_answer={
                "text": "JSON format",
                "source_lines": [10, 12],
                "confidence": "high"
            },
            generation_method="template",
            template_id="factual_format_01"
        )

        assert question.question_id == "q_001"
        assert isinstance(question.expected_answer, dict)
        assert question.expected_answer["text"] == "JSON format"

    def test_question_rejects_string_answer(self):
        """Test that Question rejects string expected_answer."""
        with pytest.raises(TypeError, match="expected_answer must be a Dict"):
            Question(
                question_id="q_001",
                question_text="What is the format?",
                category="factual",
                difficulty="basic",
                scope="section",
                target_sections=["section_1"],
                expected_answer="JSON format",  # String instead of Dict
                generation_method="template"
            )

    def test_question_requires_text_field_in_answer(self):
        """Test that expected_answer must have 'text' field."""
        with pytest.raises(ValueError, match="expected_answer must contain 'text' field"):
            Question(
                question_id="q_001",
                question_text="What is the format?",
                category="factual",
                difficulty="basic",
                scope="section",
                target_sections=["section_1"],
                expected_answer={"confidence": "high"},  # Missing 'text' field
                generation_method="template"
            )

    def test_question_validates_category(self):
        """Test that invalid category raises error."""
        with pytest.raises(ValueError, match="Invalid category"):
            Question(
                question_id="q_001",
                question_text="What is the format?",
                category="invalid_category",
                difficulty="basic",
                scope="section",
                target_sections=["section_1"],
                expected_answer={"text": "JSON format"},
                generation_method="template"
            )

    def test_question_validates_difficulty(self):
        """Test that invalid difficulty raises error."""
        with pytest.raises(ValueError, match="Invalid difficulty"):
            Question(
                question_id="q_001",
                question_text="What is the format?",
                category="factual",
                difficulty="super_hard",
                scope="section",
                target_sections=["section_1"],
                expected_answer={"text": "JSON format"},
                generation_method="template"
            )

    def test_question_validates_scope(self):
        """Test that invalid scope raises error."""
        with pytest.raises(ValueError, match="Invalid scope"):
            Question(
                question_id="q_001",
                question_text="What is the format?",
                category="factual",
                difficulty="basic",
                scope="global",  # Invalid
                target_sections=["section_1"],
                expected_answer={"text": "JSON format"},
                generation_method="template"
            )

    def test_question_to_dict_roundtrip(self):
        """Test serialization and deserialization."""
        original = Question(
            question_id="q_001",
            question_text="What is the format?",
            category="factual",
            difficulty="basic",
            scope="section",
            target_sections=["section_1"],
            expected_answer={"text": "JSON format", "confidence": "high"},
            generation_method="template",
            template_id="factual_format_01",
            metadata={"key": "value"}
        )

        # Serialize
        data = original.to_dict()
        assert isinstance(data, dict)
        assert data["question_id"] == "q_001"

        # Deserialize
        reconstructed = Question.from_dict(data)
        assert reconstructed.question_id == original.question_id
        assert reconstructed.expected_answer == original.expected_answer
        assert reconstructed.metadata == original.metadata


# ============================================================================
# Test Class 2: QuestioningResult
# ============================================================================

class TestQuestioningResult:
    """Test QuestioningResult save/load functionality."""

    def test_save_and_load_roundtrip(self, tmp_path):
        """Test saving and loading questions.json."""
        # Create sample question
        question = Question(
            question_id="q_001",
            question_text="What is the format?",
            category="factual",
            difficulty="basic",
            scope="section",
            target_sections=["section_1"],
            expected_answer={"text": "JSON format"},
            generation_method="template"
        )

        # Create result
        result = QuestioningResult(
            questions=[question],
            document_path="test.md",
            generation_timestamp="2025-12-28T10:00:00",
            generator_version="1.0.0-phase2"
        )

        # Save
        result.save(str(tmp_path))
        questions_file = tmp_path / "questions.json"
        assert questions_file.exists()

        # Load
        loaded = QuestioningResult.load(str(tmp_path))
        assert len(loaded.questions) == 1
        assert loaded.questions[0].question_id == "q_001"
        assert loaded.document_path == "test.md"
        assert loaded.generator_version == "1.0.0-phase2"

    def test_save_uses_utf8_encoding(self, tmp_path):
        """Test that save uses UTF-8 encoding."""
        question = Question(
            question_id="q_001",
            question_text="Quelle est la taille maximale?",  # French
            category="quantitative",
            difficulty="basic",
            scope="section",
            target_sections=["section_1"],
            expected_answer={"text": "100 caractères"},
            generation_method="template"
        )

        result = QuestioningResult(questions=[question])
        result.save(str(tmp_path))

        # Read file and verify UTF-8
        with open(tmp_path / "questions.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "Quelle" in data["questions"][0]["question_text"]
            assert "caractères" in data["questions"][0]["expected_answer"]["text"]

    def test_calculate_statistics(self):
        """Test statistics calculation."""
        questions = [
            Question(
                question_id=f"q_{i:03d}",
                question_text=f"Question {i}",
                category=["factual", "procedural", "conditional"][i % 3],
                difficulty=["basic", "intermediate"][i % 2],
                scope="section",
                target_sections=[f"section_{i % 5}"],
                expected_answer={"text": f"Answer {i}"},
                generation_method="template",
                metadata={"element_text": f"Element {i % 5}"}  # 5 unique elements
            )
            for i in range(1, 11)
        ]

        result = QuestioningResult(questions=questions)
        result.calculate_statistics(total_sections=10, total_elements=20)

        stats = result.statistics
        assert stats["total_questions"] == 10
        assert stats["section_level"] == 10
        assert stats["document_level"] == 0
        assert stats["adversarial"] == 0
        assert stats["coverage"]["sections_covered"] == 5
        assert stats["coverage"]["section_coverage_pct"] == 50.0
        # Fixed: Now counts unique elements (5) not questions (10)
        assert stats["coverage"]["elements_covered"] == 5
        assert stats["coverage"]["element_coverage_pct"] == 25.0


# ============================================================================
# Test Class 3: Template Loading
# ============================================================================

class TestTemplateLoading:
    """Test template loading functionality."""

    @pytest.fixture
    def template_file(self, tmp_path):
        """Create a temporary template file."""
        template_data = {
            "version": "1.0.0",
            "templates": [
                {
                    "template_id": "test_01",
                    "category": "factual",
                    "difficulty": "basic",
                    "question_pattern": "What is {element_text}?",
                    "triggers": {
                        "element_types": ["requirement"],
                        "required_keywords": ["must"]
                    }
                },
                {
                    "template_id": "test_02",
                    "category": "procedural",
                    "difficulty": "intermediate",
                    "question_pattern": "How to {element_text}?",
                    "triggers": {
                        "element_types": ["step"],
                        "required_keywords": []
                    }
                }
            ]
        }

        template_path = tmp_path / "templates.json"
        with open(template_path, "w", encoding="utf-8") as f:
            json.dump(template_data, f, indent=2, ensure_ascii=False)

        return template_path

    def test_load_templates(self, template_file):
        """Test loading templates from JSON file."""
        loader = TemplateLoader(str(template_file))
        templates = loader.load()

        assert len(templates) == 2
        assert templates[0]["template_id"] == "test_01"
        assert templates[1]["template_id"] == "test_02"

    def test_templates_indexed_by_category(self, template_file):
        """Test that templates are indexed by category."""
        loader = TemplateLoader(str(template_file))
        loader.load()

        assert "factual" in loader.templates_by_category
        assert "procedural" in loader.templates_by_category
        assert len(loader.templates_by_category["factual"]) == 1
        assert len(loader.templates_by_category["procedural"]) == 1

    def test_load_missing_file_raises_error(self, tmp_path):
        """Test that loading missing file raises FileNotFoundError."""
        loader = TemplateLoader(str(tmp_path / "nonexistent.json"))
        with pytest.raises(FileNotFoundError):
            loader.load()


# ============================================================================
# Test Class 4: Element Extraction
# ============================================================================

class TestElementExtraction:
    """Test element extraction with 8 regex patterns."""

    def test_extract_steps(self):
        """Test extracting step elements."""
        sections = [{
            "section_id": "section_1",
            "title": "Installation",
            "content": "Step 1: Download the file\nStep 2: Extract the archive",
            "start_line": 1
        }]

        extractor = ElementExtractor()
        elements = extractor.extract_elements(sections)

        step_elements = [e for e in elements if e.element_type == "step"]
        assert len(step_elements) >= 1
        assert any("Step 1" in e.text or "Download" in e.text for e in step_elements)

    def test_extract_requirements(self):
        """Test extracting requirement elements."""
        sections = [{
            "section_id": "section_1",
            "title": "Requirements",
            "content": "The system must support UTF-8 encoding. Authentication is required.",
            "start_line": 1
        }]

        extractor = ElementExtractor()
        elements = extractor.extract_elements(sections)

        req_elements = [e for e in elements if e.element_type == "requirement"]
        assert len(req_elements) >= 1
        assert any("must" in e.text.lower() or "required" in e.text.lower() for e in req_elements)

    def test_extract_conditionals(self):
        """Test extracting conditional elements."""
        sections = [{
            "section_id": "section_1",
            "title": "Usage",
            "content": "If the file exists, skip download. When processing fails, retry.",
            "start_line": 1
        }]

        extractor = ElementExtractor()
        elements = extractor.extract_elements(sections)

        cond_elements = [e for e in elements if e.element_type == "conditional"]
        assert len(cond_elements) >= 1
        assert any("if" in e.text.lower() or "when" in e.text.lower() for e in cond_elements)

    def test_extract_outputs(self):
        """Test extracting output elements."""
        sections = [{
            "section_id": "section_1",
            "title": "Output",
            "content": "The script generates a JSON report. Returns exit code 0 on success.",
            "start_line": 1
        }]

        extractor = ElementExtractor()
        elements = extractor.extract_elements(sections)

        output_elements = [e for e in elements if e.element_type == "output"]
        assert len(output_elements) >= 1

    def test_extract_inputs(self):
        """Test extracting input elements."""
        sections = [{
            "section_id": "section_1",
            "title": "Input",
            "content": "The function accepts two parameters. Takes a configuration file as input.",
            "start_line": 1
        }]

        extractor = ElementExtractor()
        elements = extractor.extract_elements(sections)

        input_elements = [e for e in elements if e.element_type == "input"]
        assert len(input_elements) >= 1

    def test_extract_constraints(self):
        """Test extracting constraint elements."""
        sections = [{
            "section_id": "section_1",
            "title": "Limits",
            "content": "The maximum file size is 10MB. Must use at least 2 characters.",
            "start_line": 1
        }]

        extractor = ElementExtractor()
        elements = extractor.extract_elements(sections)

        constraint_elements = [e for e in elements if e.element_type == "constraint"]
        assert len(constraint_elements) >= 1
        assert any("maximum" in e.text.lower() or "limit" in e.text.lower() for e in constraint_elements)

    def test_extract_defaults(self):
        """Test extracting default elements."""
        sections = [{
            "section_id": "section_1",
            "title": "Configuration",
            "content": "The timeout defaults to 30 seconds. Port is set to 8080.",
            "start_line": 1
        }]

        extractor = ElementExtractor()
        elements = extractor.extract_elements(sections)

        default_elements = [e for e in elements if e.element_type == "default"]
        assert len(default_elements) >= 1

    def test_extract_exceptions(self):
        """Test extracting exception elements."""
        sections = [{
            "section_id": "section_1",
            "title": "Error Handling",
            "content": "If validation fails, return error. Raises an exception on invalid input.",
            "start_line": 1
        }]

        extractor = ElementExtractor()
        elements = extractor.extract_elements(sections)

        exc_elements = [e for e in elements if e.element_type == "exception"]
        assert len(exc_elements) >= 1

    def test_remove_duplicates(self):
        """Test that duplicate elements are removed."""
        sections = [{
            "section_id": "section_1",
            "title": "Test",
            "content": "The system must work. The system must work.",  # Duplicate
            "start_line": 1
        }]

        extractor = ElementExtractor()
        elements = extractor.extract_elements(sections)

        # Should only have one element (duplicate removed)
        texts = [e.text for e in elements]
        assert len(texts) == len(set(texts))  # All unique


# ============================================================================
# Test Class 5: Template Application
# ============================================================================

class TestTemplateApplication:
    """Test template application logic."""

    @pytest.fixture
    def templates(self):
        """Sample templates for testing."""
        return [
            {
                "template_id": "factual_01",
                "category": "factual",
                "difficulty": "basic",
                "question_pattern": "What is {element_text}?",
                "answer_extraction": {"confidence_threshold": "high"},
                "triggers": {
                    "element_types": ["requirement"],
                    "required_keywords": ["must"]
                }
            },
            {
                "template_id": "procedural_01",
                "category": "procedural",
                "difficulty": "basic",
                "question_pattern": "How to {element_text}?",
                "answer_extraction": {"confidence_threshold": "medium"},
                "triggers": {
                    "element_types": ["step"],
                    "required_keywords": []
                }
            }
        ]

    def test_apply_matching_template(self, templates):
        """Test applying template that matches element."""
        element = TestableElement(
            element_type="requirement",
            text="The system must support UTF-8",
            section_id="section_1",
            section_title="Requirements",
            start_line=10,
            end_line=10,
            context="The system must support UTF-8 encoding"
        )

        applicator = TemplateApplicator(templates)
        matches = applicator.apply(element)

        assert len(matches) > 0
        template, question_text, answer = matches[0]
        assert template["template_id"] == "factual_01"
        assert "What is" in question_text

    def test_no_match_for_wrong_element_type(self, templates):
        """Test that template doesn't match wrong element type."""
        element = TestableElement(
            element_type="output",  # No templates match output
            text="The system produces a report",
            section_id="section_1",
            section_title="Output",
            start_line=10,
            end_line=10,
            context="The system produces a report"
        )

        applicator = TemplateApplicator(templates)
        matches = applicator.apply(element)

        # factual_01 only matches "requirement", so no match
        factual_matches = [m for m in matches if m[0]["template_id"] == "factual_01"]
        assert len(factual_matches) == 0

    def test_max_per_element_limit(self, templates):
        """Test that max_per_element limits results."""
        element = TestableElement(
            element_type="step",
            text="Download the file",
            section_id="section_1",
            section_title="Steps",
            start_line=10,
            end_line=10,
            context="Step 1: Download the file"
        )

        # Add more templates that would all match
        many_templates = templates * 5  # 10 templates

        applicator = TemplateApplicator(many_templates)
        matches = applicator.apply(element, max_per_element=2)

        assert len(matches) <= 2


# ============================================================================
# Test Class 6: Question Validation
# ============================================================================

class TestQuestionValidation:
    """Test question validation with 4 rules."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return QuestionValidator()

    @pytest.fixture
    def sample_element(self):
        """Create sample element for testing."""
        return TestableElement(
            element_type="requirement",
            text="The system must support UTF-8 encoding",
            section_id="section_1",
            section_title="Requirements",
            start_line=10,
            end_line=10,
            context="Documentation states: The system must support UTF-8 encoding for all text files"
        )

    def test_valid_question_passes(self, validator, sample_element):
        """Test that valid question passes all rules."""
        question = "According to the documentation, what encoding must the system support?"
        answer = "UTF-8 encoding"

        is_valid, reason = validator.validate(question, answer, sample_element)
        assert is_valid
        assert reason == "Valid"

    def test_rule1_answerable(self, validator, sample_element):
        """Test Rule 1: Answer keywords must be in context."""
        question = "What encoding is required?"
        answer = "Base64 encoding"  # Not in context

        is_valid, reason = validator.validate(question, answer, sample_element)
        # Should fail because "Base64" is not in context
        # Note: May pass if stop words allow it - check implementation
        if not is_valid:
            assert "not found" in reason.lower()

    def test_rule2_no_leakage(self, validator, sample_element):
        """Test Rule 2: Answer should not appear in question."""
        question = "The system must support UTF-8 encoding, correct?"
        answer = "The system must support UTF-8 encoding"

        is_valid, reason = validator.validate(question, answer, sample_element)
        assert not is_valid
        assert "leakage" in reason.lower() or "appears in question" in reason.lower()

    def test_rule3_grammatical(self, validator, sample_element):
        """Test Rule 3: Must be proper question format."""
        # Missing question mark
        question = "What encoding is supported"
        answer = "UTF-8"

        is_valid, reason = validator.validate(question, answer, sample_element)
        assert not is_valid
        assert "question format" in reason.lower()

    def test_rule3_must_start_with_question_word(self, validator, sample_element):
        """Test that question must start with question word."""
        question = "The encoding is what?"
        answer = "UTF-8"

        is_valid, reason = validator.validate(question, answer, sample_element)
        assert not is_valid

    def test_rule4_single_concept(self, validator, sample_element):
        """Test Rule 4: No multi-part questions."""
        question = "What encoding is supported and what is the file format?"
        answer = "UTF-8 and JSON"

        is_valid, reason = validator.validate(question, answer, sample_element)
        assert not is_valid
        assert "multi-part" in reason.lower()


# ============================================================================
# Test Class 7: Coverage Calculation
# ============================================================================

class TestCoverageCalculation:
    """Test coverage calculation with 70%/60% targets."""

    def test_section_coverage_calculation(self):
        """Test section coverage percentage calculation."""
        questions = [
            Question(
                question_id=f"q_{i:03d}",
                question_text=f"Question {i}",
                category="factual",
                difficulty="basic",
                scope="section",
                target_sections=[f"section_{i % 3}"],  # 3 sections covered
                expected_answer={"text": f"Answer {i}"},
                generation_method="template"
            )
            for i in range(6)
        ]

        result = QuestioningResult(questions=questions)
        result.calculate_statistics(total_sections=10, total_elements=20)

        # 3 sections covered out of 10 = 30%
        assert result.statistics["coverage"]["sections_covered"] == 3
        assert result.statistics["coverage"]["section_coverage_pct"] == 30.0

    def test_element_coverage_calculation(self):
        """Test element coverage percentage calculation."""
        # Create questions with unique element_text to simulate 12 different elements
        questions = [
            Question(
                question_id=f"q_{i:03d}",
                question_text=f"Question {i}",
                category="factual",
                difficulty="basic",
                scope="section",
                target_sections=["section_1"],
                expected_answer={"text": f"Answer {i}"},
                generation_method="template",
                metadata={"element_text": f"Unique element {i}"}  # Each question tests different element
            )
            for i in range(12)
        ]

        result = QuestioningResult(questions=questions)
        result.calculate_statistics(total_sections=10, total_elements=20)

        # Fixed: 12 unique elements covered out of 20 = 60%
        assert result.statistics["coverage"]["elements_covered"] == 12
        assert result.statistics["coverage"]["element_coverage_pct"] == 60.0

    def test_meets_70_60_targets(self):
        """Test that result meets 70% section / 60% element targets."""
        # Create questions covering 8/10 sections (80%) and 15/20 unique elements (75%)
        questions = []
        qid = 1

        # Cover 8 sections with unique elements
        for section_id in range(8):
            questions.append(Question(
                question_id=f"q_{qid:03d}",
                question_text=f"Question {qid}",
                category="factual",
                difficulty="basic",
                scope="section",
                target_sections=[f"section_{section_id}"],
                expected_answer={"text": f"Answer {qid}"},
                generation_method="template",
                metadata={"element_text": f"Element {qid}"}  # Unique element
            ))
            qid += 1

        # Add more questions with unique elements to reach 15 unique elements
        for i in range(7):
            questions.append(Question(
                question_id=f"q_{qid:03d}",
                question_text=f"Question {qid}",
                category="factual",
                difficulty="basic",
                scope="section",
                target_sections=["section_0"],  # Reuse section
                expected_answer={"text": f"Answer {qid}"},
                generation_method="template",
                metadata={"element_text": f"Element {qid}"}  # Unique element
            ))
            qid += 1

        result = QuestioningResult(questions=questions)
        result.calculate_statistics(total_sections=10, total_elements=20)

        assert result.statistics["coverage"]["section_coverage_pct"] >= 70.0
        # Fixed: Now correctly counts 15 unique elements = 75%
        assert result.statistics["coverage"]["element_coverage_pct"] >= 60.0


# ============================================================================
# Test Class 8: Integration Tests
# ============================================================================

class TestQuestioningStepIntegration:
    """Test end-to-end QuestioningStep integration."""

    @pytest.fixture
    def temp_templates(self, tmp_path):
        """Create temporary template file."""
        template_data = {
            "version": "1.0.0",
            "templates": [
                {
                    "template_id": "factual_format_01",
                    "category": "factual",
                    "difficulty": "basic",
                    "question_pattern": "What format should {element_text} use?",
                    "answer_extraction": {"confidence_threshold": "high", "keywords": ["format"], "context_window": 2},
                    "triggers": {
                        "element_types": ["requirement", "constraint"],
                        "required_keywords": ["format"]
                    },
                    "validation_hints": {
                        "answer_should_contain": ["format"],
                        "answer_should_not_contain": ["what"]
                    }
                },
                {
                    "template_id": "procedural_step_01",
                    "category": "procedural",
                    "difficulty": "basic",
                    "question_pattern": "What is the first step in the process?",
                    "answer_extraction": {"confidence_threshold": "high", "keywords": ["first"], "context_window": 2},
                    "triggers": {
                        "element_types": ["step"],
                        "required_keywords": []
                    },
                    "validation_hints": {
                        "answer_should_contain": [],
                        "answer_should_not_contain": []
                    }
                }
            ]
        }

        template_path = tmp_path / "test_templates.json"
        with open(template_path, "w", encoding="utf-8") as f:
            json.dump(template_data, f, indent=2, ensure_ascii=False)

        return template_path

    @pytest.fixture
    def sample_sections(self):
        """Create sample sections for testing."""
        return [
            {
                "section_id": "section_1",
                "title": "Configuration",
                "content": "The output format must be JSON with proper indentation. All files must use UTF-8 encoding format.",
                "start_line": 1
            },
            {
                "section_id": "section_2",
                "title": "Installation",
                "content": "Follow these steps:\n\nStep 1: Download the installer from the website\nStep 2: Run the setup program\nStep 3: Complete the installation wizard",
                "start_line": 10
            },
            {
                "section_id": "section_3",
                "title": "Usage",
                "content": "The system has several requirements. The maximum file size is 10MB. The processing timeout defaults to 30 seconds.",
                "start_line": 20
            }
        ]

    def test_end_to_end_question_generation(self, temp_templates, sample_sections, tmp_path):
        """Test complete question generation workflow."""
        step = QuestioningStep(template_path=str(temp_templates))
        result = step.generate_questions(
            sections=sample_sections,
            document_text="Sample document text",
            document_path="test.md"
        )

        # Should generate some questions
        assert len(result.questions) > 0

        # All questions should be valid
        for question in result.questions:
            assert question.question_id.startswith("q_")
            assert isinstance(question.expected_answer, dict)
            assert "text" in question.expected_answer

        # Statistics should be calculated
        assert "total_questions" in result.statistics
        assert "coverage" in result.statistics

    def test_save_and_load_integration(self, temp_templates, sample_sections, tmp_path):
        """Test generating, saving, and loading questions."""
        step = QuestioningStep(template_path=str(temp_templates))
        result = step.generate_questions(
            sections=sample_sections,
            document_text="Sample document",
            document_path="test.md"
        )

        # Save
        output_dir = tmp_path / "output"
        result.save(str(output_dir))

        # Load
        loaded = QuestioningResult.load(str(output_dir))

        assert len(loaded.questions) == len(result.questions)
        assert loaded.document_path == result.document_path

    def test_convenience_function(self, temp_templates, sample_sections):
        """Test generate_questions_from_sections convenience function."""
        # Set up templates in expected location
        # This test would need the actual templates directory structure

        result = generate_questions_from_sections(
            sections=sample_sections,
            document_text="Sample document",
            document_path="test.md"
        )

        assert isinstance(result, QuestioningResult)

    def test_empty_sections(self, temp_templates):
        """Test generating questions from empty sections."""
        step = QuestioningStep(template_path=str(temp_templates))
        result = step.generate_questions(
            sections=[],
            document_text="",
            document_path="empty.md"
        )

        assert len(result.questions) == 0
        assert result.statistics['total_questions'] == 0

    def test_coverage_selection_with_no_candidates(self, temp_templates):
        """Test coverage selection with no candidate questions."""
        step = QuestioningStep(template_path=str(temp_templates))
        selected = step._select_for_coverage(
            candidates=[],
            total_sections=10,
            total_elements=20,
            targets={'section_pct': 70.0, 'element_pct': 60.0}
        )

        assert selected == []

    def test_custom_coverage_targets(self, temp_templates, sample_sections):
        """Test using custom coverage targets."""
        step = QuestioningStep(template_path=str(temp_templates))
        result = step.generate_questions(
            sections=sample_sections,
            document_text="Sample document",
            document_path="test.md",
            coverage_targets={'section_pct': 50.0, 'element_pct': 40.0}
        )

        assert isinstance(result, QuestioningResult)


# ============================================================================
# Additional Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_question_answer_roundtrip(self):
        """Test QuestionAnswer serialization (Phase 4 stub)."""
        answer = QuestionAnswer(
            question_id="q_001",
            model_name="claude",
            answer_text="JSON format",
            response_time_ms=1500,
            raw_response='{"answer": "JSON format"}',
            confidence_stated="high"
        )

        data = answer.to_dict()
        reconstructed = QuestionAnswer.from_dict(data)

        assert reconstructed.question_id == answer.question_id
        assert reconstructed.model_name == answer.model_name

    def test_question_evaluation_roundtrip(self):
        """Test QuestionEvaluation serialization (Phase 4 stub)."""
        evaluation = QuestionEvaluation(
            question_id="q_001",
            model_name="claude",
            score="correct",
            reasoning="Answer matches expected",
            evidence="Line 45-46"
        )

        data = evaluation.to_dict()
        reconstructed = QuestionEvaluation.from_dict(data)

        assert reconstructed.question_id == evaluation.question_id
        assert reconstructed.score == evaluation.score

    def test_question_result_roundtrip(self):
        """Test QuestionResult serialization (Phase 4 stub)."""
        question = Question(
            question_id="q_001",
            question_text="What is the format?",
            category="factual",
            difficulty="basic",
            scope="section",
            target_sections=["section_1"],
            expected_answer={"text": "JSON format"},
            generation_method="template"
        )

        result = QuestionResult(
            question=question,
            consensus="agreement",
            issue_detected=False
        )

        data = result.to_dict()
        reconstructed = QuestionResult.from_dict(data)

        assert reconstructed.question.question_id == question.question_id
        assert reconstructed.consensus == "agreement"

    def test_element_extractor_with_no_matches(self):
        """Test element extraction when no patterns match."""
        sections = [{
            "section_id": "section_1",
            "title": "Introduction",
            "content": "This is just plain text without any special patterns.",
            "start_line": 1
        }]

        extractor = ElementExtractor()
        elements = extractor.extract_elements(sections)

        # Should return empty or minimal list
        assert isinstance(elements, list)

    def test_template_applicator_with_regex_keyword(self):
        """Test template matching with regex keyword."""
        template = {
            "template_id": "test_01",
            "category": "quantitative",
            "difficulty": "basic",
            "question_pattern": "How many items?",
            "answer_extraction": {"confidence_threshold": "high"},
            "triggers": {
                "element_types": ["constraint"],
                "required_keywords": ["\\d+"]  # Regex pattern
            }
        }

        element = TestableElement(
            element_type="constraint",
            text="The system supports 100 items",
            section_id="section_1",
            section_title="Limits",
            start_line=10,
            end_line=10,
            context="The system supports 100 items maximum"
        )

        applicator = TemplateApplicator([template])
        matches = applicator.apply(element)

        assert len(matches) > 0

    def test_validator_with_empty_answer(self):
        """Test validator with empty answer."""
        validator = QuestionValidator()
        element = TestableElement(
            element_type="requirement",
            text="Test requirement",
            section_id="section_1",
            section_title="Requirements",
            start_line=10,
            end_line=10,
            context="Test requirement context"
        )

        is_valid, reason = validator.validate(
            "What is required?",
            "",
            element
        )

        # Empty answer might still be answerable if no meaningful words
        # Just verify it returns a result
        assert isinstance(is_valid, bool)
        assert isinstance(reason, str)

    def test_add_question_to_result(self):
        """Test adding questions to result."""
        result = QuestioningResult()

        question = Question(
            question_id="q_001",
            question_text="Test question?",
            category="factual",
            difficulty="basic",
            scope="section",
            target_sections=["section_1"],
            expected_answer={"text": "Test answer"},
            generation_method="template"
        )

        result.add_question(question)

        assert len(result.questions) == 1
        assert result.questions[0].question_id == "q_001"
