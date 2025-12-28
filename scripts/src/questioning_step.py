"""
Questioning Step - Generate questions from documentation sections

This module provides a clean interface for Step 5 of the document polishing pipeline.
It generates targeted questions to test model comprehension of documentation sections.

Pipeline position: After Detection (Step 4), before Reporting (Step 6)
Generates questions.json artifact for later evaluation (Phase 4).
"""

import json
import re
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime


# ============================================================================
# Phase 1: Core Dataclasses
# ============================================================================

@dataclass
class Question:
    """
    Single question with metadata.

    Represents a generated question that can be asked about a documentation section.
    Includes expected answer, metadata about generation method, and classification.
    """
    question_id: str                      # Format: q_001, q_002, etc.
    question_text: str                    # The actual question
    category: str                         # factual|procedural|conditional|quantitative|existence
    difficulty: str                       # basic|intermediate|advanced|expert
    scope: str                            # section (Phase 2), document (Phase 3+)
    target_sections: List[str]            # Section IDs this question targets
    expected_answer: Dict[str, Any]       # {text: str, source_lines: List[int], confidence: str}
    generation_method: str                # template|llm|hybrid
    template_id: Optional[str] = None     # ID of template used (if template-based)
    is_adversarial: bool = False          # Whether this is an adversarial question
    adversarial_type: Optional[str] = None  # Type if adversarial
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize question to dictionary for JSON storage.

        Returns:
            Dictionary representation of the question
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Question':
        """
        Deserialize question from dictionary.

        Args:
            data: Dictionary with question fields

        Returns:
            Question instance
        """
        return cls(**data)

    def __post_init__(self):
        """Validate question fields after initialization."""
        # Validate category
        valid_categories = ['factual', 'procedural', 'conditional', 'quantitative', 'existence']
        if self.category not in valid_categories:
            raise ValueError(f"Invalid category: {self.category}. Must be one of {valid_categories}")

        # Validate difficulty
        valid_difficulties = ['basic', 'intermediate', 'advanced', 'expert']
        if self.difficulty not in valid_difficulties:
            raise ValueError(f"Invalid difficulty: {self.difficulty}. Must be one of {valid_difficulties}")

        # Validate scope
        valid_scopes = ['section', 'document']
        if self.scope not in valid_scopes:
            raise ValueError(f"Invalid scope: {self.scope}. Must be one of {valid_scopes}")

        # Validate expected_answer is a dict
        if not isinstance(self.expected_answer, dict):
            raise TypeError("expected_answer must be a Dict, not str or other type")

        # Validate expected_answer has required fields
        if 'text' not in self.expected_answer:
            raise ValueError("expected_answer must contain 'text' field")


# ============================================================================
# Phase 4 Stubs: Answer Collection & Evaluation
# ============================================================================

@dataclass
class QuestionAnswer:
    """
    Model's answer to a question (stub for Phase 4).

    Represents a single model's response to a question.
    Will be fully implemented in Phase 4 (Answer Collection).
    """
    question_id: str
    model_name: str
    answer_text: str
    response_time_ms: int
    raw_response: str
    confidence_stated: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize answer to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestionAnswer':
        """Deserialize answer from dictionary."""
        return cls(**data)


@dataclass
class QuestionEvaluation:
    """
    Judge's evaluation of an answer (stub for Phase 4).

    Represents the LLM-as-Judge evaluation of a model's answer.
    Will be fully implemented in Phase 4 (Answer Evaluation).
    """
    question_id: str
    model_name: str
    score: str  # correct|partially_correct|incorrect|unanswerable
    reasoning: str
    evidence: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize evaluation to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestionEvaluation':
        """Deserialize evaluation from dictionary."""
        return cls(**data)


@dataclass
class QuestionResult:
    """
    Complete result for a question across all models (stub for Phase 4).

    Aggregates answers and evaluations for a single question.
    Will be fully implemented in Phase 4.
    """
    question: Question
    answers: Dict[str, QuestionAnswer] = field(default_factory=dict)
    evaluations: Dict[str, QuestionEvaluation] = field(default_factory=dict)
    consensus: str = ""
    issue_detected: bool = False
    issue_type: Optional[str] = None
    severity: Optional[str] = None
    recommendation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize result to dictionary."""
        data = asdict(self)
        # Convert nested objects
        data['question'] = self.question.to_dict()
        data['answers'] = {k: v.to_dict() for k, v in self.answers.items()}
        data['evaluations'] = {k: v.to_dict() for k, v in self.evaluations.items()}
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestionResult':
        """Deserialize result from dictionary."""
        # Reconstruct nested objects
        question = Question.from_dict(data['question'])
        answers = {k: QuestionAnswer.from_dict(v) for k, v in data.get('answers', {}).items()}
        evaluations = {k: QuestionEvaluation.from_dict(v) for k, v in data.get('evaluations', {}).items()}

        return cls(
            question=question,
            answers=answers,
            evaluations=evaluations,
            consensus=data.get('consensus', ''),
            issue_detected=data.get('issue_detected', False),
            issue_type=data.get('issue_type'),
            severity=data.get('severity'),
            recommendation=data.get('recommendation')
        )


# ============================================================================
# Phase 2: Question Generation Result
# ============================================================================

@dataclass
class QuestioningResult:
    """
    Result of question generation.

    Contains all generated questions, statistics, and metadata.
    Can be saved to/loaded from questions.json.
    """
    questions: List[Question] = field(default_factory=list)
    results: List[QuestionResult] = field(default_factory=list)  # Empty in Phase 2, used in Phase 4
    statistics: Dict[str, Any] = field(default_factory=dict)
    document_path: str = ""
    generation_timestamp: str = ""
    generator_version: str = "1.0.0-phase2"

    def save(self, output_dir: str):
        """
        Save questioning result to JSON file.

        Creates questions.json in the output directory with UTF-8 encoding,
        2-space indentation, and ensure_ascii=False for international characters.

        Args:
            output_dir: Directory to save questions.json
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        questions_file = output_path / 'questions.json'

        # Build data structure
        data = {
            'document_path': self.document_path,
            'generation_timestamp': self.generation_timestamp,
            'generator_version': self.generator_version,
            'statistics': self.statistics,
            'questions': [q.to_dict() for q in self.questions]
        }

        # Write with UTF-8, 2-space indent, ensure_ascii=False
        with open(questions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, input_dir: str) -> 'QuestioningResult':
        """
        Load questioning result from JSON file.

        Args:
            input_dir: Directory containing questions.json

        Returns:
            QuestioningResult instance

        Raises:
            FileNotFoundError: If questions.json doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        questions_file = Path(input_dir) / 'questions.json'

        if not questions_file.exists():
            raise FileNotFoundError(f"Questions file not found: {questions_file}")

        with open(questions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Reconstruct questions from dicts
        questions = [Question.from_dict(q) for q in data.get('questions', [])]

        return cls(
            questions=questions,
            results=[],  # Empty in Phase 2
            statistics=data.get('statistics', {}),
            document_path=data.get('document_path', ''),
            generation_timestamp=data.get('generation_timestamp', ''),
            generator_version=data.get('generator_version', '1.0.0-phase2')
        )

    def add_question(self, question: Question):
        """
        Add a question to the result.

        Args:
            question: Question to add
        """
        self.questions.append(question)

    def calculate_statistics(self, total_sections: int = 0, total_elements: int = 0):
        """
        Calculate and update statistics for the generated questions.

        Args:
            total_sections: Total number of sections in document
            total_elements: Total number of testable elements extracted
        """
        # Count by category
        by_category = {}
        for question in self.questions:
            by_category[question.category] = by_category.get(question.category, 0) + 1

        # Count by difficulty
        by_difficulty = {}
        for question in self.questions:
            by_difficulty[question.difficulty] = by_difficulty.get(question.difficulty, 0) + 1

        # Count by scope
        section_level = sum(1 for q in self.questions if q.scope == 'section')
        document_level = sum(1 for q in self.questions if q.scope == 'document')

        # Count adversarial
        adversarial_count = sum(1 for q in self.questions if q.is_adversarial)

        # Calculate coverage
        sections_covered = len(set(
            section_id
            for q in self.questions
            for section_id in q.target_sections
        ))

        # Count unique elements covered (not just questions)
        # Use metadata to track which elements were tested
        unique_elements_covered = len(set(
            (q.target_sections[0] if q.target_sections else '',
             q.metadata.get('element_text', '')[:50])  # Use element text as identifier
            for q in self.questions
        ))

        section_coverage_pct = (sections_covered / total_sections * 100) if total_sections > 0 else 0
        element_coverage_pct = (unique_elements_covered / total_elements * 100) if total_elements > 0 else 0

        self.statistics = {
            'total_questions': len(self.questions),
            'section_level': section_level,
            'document_level': document_level,
            'adversarial': adversarial_count,
            'by_category': by_category,
            'by_difficulty': by_difficulty,
            'coverage': {
                'sections_covered': sections_covered,
                'total_sections': total_sections,
                'section_coverage_pct': round(section_coverage_pct, 1),
                'elements_covered': unique_elements_covered,  # Fixed: count unique elements
                'total_elements': total_elements,
                'element_coverage_pct': round(element_coverage_pct, 1)
            }
        }

        # Update generation timestamp
        self.generation_timestamp = datetime.now().isoformat()


# ============================================================================
# Phase 2: Testable Element Dataclass
# ============================================================================

@dataclass
class TestableElement:
    """
    Extracted testable element from documentation.

    Represents a specific part of documentation that can generate a question.
    """
    element_type: str  # step|requirement|conditional|output|input|constraint|default|exception
    text: str  # The extracted text
    section_id: str  # Section this element belongs to
    section_title: str  # Human-readable section title
    start_line: int  # Starting line number
    end_line: int  # Ending line number
    context: str = ""  # Surrounding context for answer extraction


# ============================================================================
# Phase 2: Element Extraction
# ============================================================================

class ElementExtractor:
    """
    Extracts testable elements from documentation sections using regex patterns.

    Uses 8 regex patterns to identify:
    1. Steps - Numbered procedures
    2. Requirements - Must/required statements
    3. Conditionals - If/when/unless clauses
    4. Outputs - Expected results
    5. Inputs - Required inputs
    6. Constraints - Limits and restrictions
    7. Defaults - Default values
    8. Exceptions - Error cases
    """

    # 8 Regex Patterns for Element Extraction
    PATTERNS = {
        'step': [
            r'(?:^|\n)(Step\s+\d+[:.]\s+.+?)(?=\n(?:Step\s+\d+|#{1,6}\s|\n|$))',
            r'(?:^|\n)(\d+\.\s+.+?)(?=\n(?:\d+\.|#{1,6}\s|\n|$))',
            r'(?:^|\n)(First,?\s+.+?)(?=\n(?:Second|Next|Then|#{1,6}\s|\n|$))',
        ],
        'requirement': [
            r'(?:^|\n)(.+?\s+(?:must|required|shall)\s+.+?)(?=[.!?\n])',
            r'(?:^|\n)(.+?\s+is\s+required.+?)(?=[.!?\n])',
        ],
        'conditional': [
            r'(?:^|\n)((?:If|When|Unless)\s+.+?,\s+.+?)(?=[.!?\n])',
            r'(?:^|\n)(.+?\s+if\s+.+?)(?=[.!?\n])',
        ],
        'output': [
            r'(?:^|\n)(.+?\s+(?:outputs?|produces?|generates?|returns?)\s+.+?)(?=[.!?\n])',
            r'(?:^|\n)(The\s+(?:output|result)\s+.+?)(?=[.!?\n])',
        ],
        'input': [
            r'(?:^|\n)(.+?\s+(?:inputs?|accepts?|takes?|receives?)\s+.+?)(?=[.!?\n])',
            r'(?:^|\n)(The\s+input\s+.+?)(?=[.!?\n])',
        ],
        'constraint': [
            r'(?:^|\n)(.+?\s+(?:maximum|minimum|max|min|limit)\s+.+?)(?=[.!?\n])',
            r'(?:^|\n)(.+?\s+(?:at\s+most|at\s+least|no\s+more\s+than)\s+.+?)(?=[.!?\n])',
        ],
        'default': [
            r'(?:^|\n)(.+?\s+(?:defaults?\s+to|default\s+value)\s+.+?)(?=[.!?\n])',
            r'(?:^|\n)(.+?\s+is\s+set\s+to\s+.+?)(?=[.!?\n])',
        ],
        'exception': [
            r'(?:^|\n)(.+?\s+(?:error|exception|fail|invalid)\s+.+?)(?=[.!?\n])',
            r'(?:^|\n)(If\s+.+?\s+(?:fails|errors).+?)(?=[.!?\n])',
        ]
    }

    def extract_elements(self, sections: List[Dict[str, Any]]) -> List[TestableElement]:
        """
        Extract testable elements from all sections.

        Args:
            sections: List of section dicts from extraction step

        Returns:
            List of TestableElement instances
        """
        elements = []

        for section in sections:
            section_id = section.get('section_id', '')
            section_title = section.get('title', '')
            content = section.get('content', '')
            start_line = section.get('start_line', 0)

            # Try each pattern type
            for element_type, patterns in self.PATTERNS.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
                    for match in matches:
                        # Calculate line numbers (approximate)
                        text_before_match = content[:match.start()]
                        lines_before = text_before_match.count('\n')
                        match_text = match.group(1).strip()
                        match_lines = match_text.count('\n')

                        # Extract context (surrounding text)
                        context_start = max(0, match.start() - 200)
                        context_end = min(len(content), match.end() + 200)
                        context = content[context_start:context_end]

                        element = TestableElement(
                            element_type=element_type,
                            text=match_text,
                            section_id=section_id,
                            section_title=section_title,
                            start_line=start_line + lines_before,
                            end_line=start_line + lines_before + match_lines,
                            context=context
                        )
                        elements.append(element)

        # Remove duplicates (same text in same section)
        seen = set()
        unique_elements = []
        for elem in elements:
            key = (elem.section_id, elem.element_type, elem.text[:50])
            if key not in seen:
                seen.add(key)
                unique_elements.append(elem)

        return unique_elements


# ============================================================================
# Phase 2: Template Loading & Application
# ============================================================================

class TemplateLoader:
    """Loads question templates from JSON file."""

    def __init__(self, template_path: str):
        """
        Initialize template loader.

        Args:
            template_path: Path to question_templates.json
        """
        self.template_path = Path(template_path)
        self.templates = []
        self.templates_by_category = {}

    def load(self) -> List[Dict[str, Any]]:
        """
        Load templates from JSON file.

        Returns:
            List of template dicts

        Raises:
            FileNotFoundError: If template file doesn't exist
            json.JSONDecodeError: If template file is invalid JSON
        """
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template file not found: {self.template_path}")

        with open(self.template_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.templates = data.get('templates', [])

        # Index by category
        for template in self.templates:
            category = template.get('category', '')
            if category not in self.templates_by_category:
                self.templates_by_category[category] = []
            self.templates_by_category[category].append(template)

        return self.templates


class TemplateApplicator:
    """Applies templates to elements to generate questions."""

    def __init__(self, templates: List[Dict[str, Any]]):
        """
        Initialize template applicator.

        Args:
            templates: List of template dicts from loader
        """
        self.templates = templates

    def apply(self, element: TestableElement, max_per_element: int = 2) -> List[Tuple[Dict, str, str]]:
        """
        Apply templates to an element to generate questions.

        Args:
            element: TestableElement to generate questions from
            max_per_element: Maximum questions per element (default 2)

        Returns:
            List of (template, question_text, expected_answer) tuples
        """
        matches = []

        for template in self.templates:
            # Check if template triggers match element
            if self._matches_triggers(template, element):
                # Generate question and answer
                question_text = self._fill_question_pattern(template, element)
                expected_answer = self._extract_answer(template, element)

                if question_text and expected_answer:
                    matches.append((template, question_text, expected_answer))

        # Limit to max_per_element, prioritizing diversity
        if len(matches) > max_per_element:
            # Group by category, take one from each
            by_category = {}
            for match in matches:
                cat = match[0].get('category', '')
                if cat not in by_category:
                    by_category[cat] = match
            matches = list(by_category.values())[:max_per_element]

        return matches

    def _matches_triggers(self, template: Dict[str, Any], element: TestableElement) -> bool:
        """Check if template triggers match element type."""
        triggers = template.get('triggers', {})
        element_types = triggers.get('element_types', [])
        required_keywords = triggers.get('required_keywords', [])

        # Check element type match
        if 'any' not in element_types and element.element_type not in element_types:
            return False

        # Check required keywords
        element_text_lower = element.text.lower()
        for keyword in required_keywords:
            # Support regex keywords
            if keyword.startswith('\\'):
                if not re.search(keyword, element.text):
                    return False
            else:
                if keyword.lower() not in element_text_lower:
                    return False

        return True

    def _fill_question_pattern(self, template: Dict[str, Any], element: TestableElement) -> str:
        """Fill template pattern with element data."""
        pattern = template.get('question_pattern', '')

        # Extract element_text (truncate if too long)
        element_text = element.text
        if len(element_text) > 100:
            element_text = element_text[:100] + "..."

        # Simple replacement (can be enhanced)
        question = pattern.replace('{section_title}', element.section_title)
        question = question.replace('{element_text}', element_text)

        # Extract attribute if present (e.g., "default value" -> "value")
        attribute = self._extract_attribute(element.text)
        question = question.replace('{attribute}', attribute)

        return question

    def _extract_attribute(self, text: str) -> str:
        """Extract attribute name from element text."""
        # Simple heuristic: look for "format", "value", "path", etc.
        text_lower = text.lower()
        if 'format' in text_lower:
            return 'format'
        if 'value' in text_lower:
            return 'value'
        if 'path' in text_lower or 'location' in text_lower:
            return 'location'
        return 'value'

    def _extract_answer(self, template: Dict[str, Any], element: TestableElement) -> str:
        """Extract expected answer from element context."""
        extraction = template.get('answer_extraction', {})
        keywords = extraction.get('keywords', [])
        context_window = extraction.get('context_window', 2)

        # Use element text as answer (simplified)
        # In a full implementation, this would be more sophisticated
        answer = element.text

        # Truncate to reasonable length
        if len(answer) > 200:
            answer = answer[:200] + "..."

        return answer


# ============================================================================
# Phase 2: Question Validation
# ============================================================================

class QuestionValidator:
    """
    Validates generated questions using 4 rules:
    1. Answerable - Answer keywords present in section
    2. No leakage - Answer not in question
    3. Grammatical - Proper question structure
    4. Single concept - No multi-part questions
    """

    def validate(self, question_text: str, expected_answer: str, element: TestableElement) -> Tuple[bool, str]:
        """
        Validate a question.

        Args:
            question_text: The generated question
            expected_answer: The expected answer text
            element: The source element

        Returns:
            (is_valid, reason) tuple
        """
        # Rule 1: Answerable - answer keywords in section
        if not self._is_answerable(expected_answer, element):
            return False, "Answer keywords not found in section context"

        # Rule 2: No leakage - answer not in question
        if self._has_leakage(question_text, expected_answer):
            return False, "Answer text appears in question"

        # Rule 3: Grammatical - proper question structure
        if not self._is_grammatical(question_text):
            return False, "Not a proper question format"

        # Rule 4: Single concept - no multi-part questions
        if self._is_multipart(question_text):
            return False, "Multi-part question detected"

        return True, "Valid"

    def _is_answerable(self, answer: str, element: TestableElement) -> bool:
        """Check if answer can be found in element context."""
        # Extract key words from answer
        answer_words = set(re.findall(r'\w+', answer.lower()))
        context_words = set(re.findall(r'\w+', element.context.lower()))

        # Common words to ignore
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        answer_words -= stop_words

        if not answer_words:
            return True  # No meaningful words to check

        # At least 30% of answer words should be in context
        overlap = answer_words & context_words
        return len(overlap) / len(answer_words) >= 0.3

    def _has_leakage(self, question: str, answer: str) -> bool:
        """Check if answer appears in question."""
        question_lower = question.lower()
        answer_lower = answer.lower()

        # For short answers (≤20 chars), check for exact match of significant words
        if len(answer) <= 20:
            # Extract significant words from answer (remove stop words)
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'are'}
            answer_words = set(re.findall(r'\w+', answer_lower))
            answer_words -= stop_words

            # If answer has significant words, check if they all appear in question
            if answer_words:
                question_words = set(re.findall(r'\w+', question_lower))
                # Leakage if all answer words appear in question
                if answer_words.issubset(question_words):
                    # Additional check: answer text appears as substring
                    if answer_lower in question_lower:
                        return True

            return False

        # For long answers (>20 chars), check for significant substring overlap
        # Check if answer substring appears in question
        for i in range(len(answer) - 20):
            substring = answer_lower[i:i+20]
            if substring in question_lower:
                return True

        return False

    def _is_grammatical(self, question: str) -> bool:
        """Check if question has proper structure."""
        # Must end with question mark
        if not question.strip().endswith('?'):
            return False

        # Must start with question word or be inverted
        question_words = ['what', 'where', 'when', 'why', 'how', 'which', 'who', 'is', 'are', 'does', 'do', 'can', 'should', 'according']
        first_word = question.strip().split()[0].lower()
        if first_word not in question_words:
            return False

        # Must be reasonable length
        if len(question) < 20 or len(question) > 500:
            return False

        return True

    def _is_multipart(self, question: str) -> bool:
        """Check if question asks multiple things."""
        # Check for "and" connecting two question clauses
        and_count = question.lower().count(' and ')
        or_count = question.lower().count(' or ')

        # Multiple question marks
        question_marks = question.count('?')
        if question_marks > 1:
            return True

        # "and" + question word suggests multi-part
        if and_count > 0:
            question_words = ['what', 'where', 'when', 'why', 'how', 'which']
            for word in question_words:
                if and_count > 0 and question.lower().count(f'and {word}') > 0:
                    return True

        return False


# ============================================================================
# Phase 2: Question Generation Step
# ============================================================================

class QuestioningStep:
    """
    Step 5: Generate questions from documentation sections.

    Pipeline position: After Detection (Step 4), before Reporting (Step 6)

    This step generates targeted questions to test model comprehension.
    In Phase 2, only question generation is implemented. Answer collection
    and evaluation are deferred to Phase 4.

    Usage:
        step = QuestioningStep()
        result = step.generate_questions(sections, document_text)
        result.save('workspace/')
    """

    def __init__(self, template_path: Optional[str] = None):
        """
        Initialize questioning step.

        Args:
            template_path: Path to question_templates.json (defaults to scripts/templates/)
        """
        self.generator_version = "1.0.0-phase2"

        # Determine template path
        if template_path is None:
            # Default to scripts/templates/question_templates.json
            current_dir = Path(__file__).parent
            template_path = current_dir.parent / 'templates' / 'question_templates.json'

        # Load templates
        loader = TemplateLoader(str(template_path))
        self.templates = loader.load()

        # Initialize components
        self.extractor = ElementExtractor()
        self.applicator = TemplateApplicator(self.templates)
        self.validator = QuestionValidator()

    def generate_questions(
        self,
        sections: List[Dict[str, Any]],
        document_text: str,
        document_path: str = "",
        coverage_targets: Dict[str, float] = None
    ) -> QuestioningResult:
        """
        Generate questions from sections.

        Args:
            sections: List of section dicts from extraction step
            document_text: Full document content
            document_path: Path to source document
            coverage_targets: Optional dict with 'section_pct' and 'element_pct' targets

        Returns:
            QuestioningResult with generated questions
        """
        if coverage_targets is None:
            coverage_targets = {'section_pct': 70.0, 'element_pct': 60.0}

        # Phase 2.1: Extract testable elements
        elements = self.extractor.extract_elements(sections)

        # Phase 2.2: Apply templates to generate candidate questions
        candidate_questions = []
        question_id_counter = 1

        for element in elements:
            # Apply templates to this element
            matches = self.applicator.apply(element, max_per_element=2)

            for template, question_text, expected_answer in matches:
                # Validate question
                is_valid, reason = self.validator.validate(question_text, expected_answer, element)

                if is_valid:
                    # Create Question object
                    question = Question(
                        question_id=f"q_{question_id_counter:03d}",
                        question_text=question_text,
                        category=template.get('category', 'factual'),
                        difficulty=template.get('difficulty', 'basic'),
                        scope='section',  # Phase 2 only does section-level
                        target_sections=[element.section_id],
                        expected_answer={
                            'text': expected_answer,
                            'source_lines': [element.start_line, element.end_line],
                            'confidence': template.get('answer_extraction', {}).get('confidence_threshold', 'medium')
                        },
                        generation_method='template',
                        template_id=template.get('template_id'),
                        is_adversarial=False,
                        metadata={
                            'testable_element': element.element_type,
                            'element_text': element.text[:100]
                        }
                    )
                    candidate_questions.append(question)
                    question_id_counter += 1

        # Phase 2.3: Select questions to meet coverage targets
        selected_questions = self._select_for_coverage(
            candidate_questions,
            len(sections),
            len(elements),
            coverage_targets
        )

        # Create result
        result = QuestioningResult(
            questions=selected_questions,
            results=[],
            statistics={},
            document_path=document_path,
            generation_timestamp=datetime.now().isoformat(),
            generator_version=self.generator_version
        )

        # Calculate statistics
        result.calculate_statistics(total_sections=len(sections), total_elements=len(elements))

        return result

    def _select_for_coverage(
        self,
        candidates: List[Question],
        total_sections: int,
        total_elements: int,
        targets: Dict[str, float]
    ) -> List[Question]:
        """
        Select questions to meet coverage targets.

        Prioritizes diverse coverage across sections and categories.

        Args:
            candidates: All candidate questions
            total_sections: Total sections in document
            total_elements: Total testable elements
            targets: Coverage targets (section_pct, element_pct)

        Returns:
            Selected questions
        """
        if not candidates:
            return []

        # Calculate target counts
        target_section_count = int(total_sections * targets['section_pct'] / 100)
        target_element_count = int(total_elements * targets['element_pct'] / 100)

        # Group by section
        by_section = {}
        for q in candidates:
            for section_id in q.target_sections:
                if section_id not in by_section:
                    by_section[section_id] = []
                by_section[section_id].append(q)

        # Select questions: prioritize section coverage first
        selected = []
        sections_covered = set()
        elements_covered = 0

        # Round 1: Take best question from each section
        for section_id in sorted(by_section.keys()):
            if by_section[section_id]:
                # Take first question (they're already validated)
                selected.append(by_section[section_id][0])
                sections_covered.add(section_id)
                elements_covered += 1
                by_section[section_id].pop(0)

        # Round 2: Add more questions until coverage targets met
        while elements_covered < target_element_count:
            # Find section with most remaining questions
            best_section = max(by_section.items(), key=lambda x: len(x[1]), default=(None, []))
            if not best_section[1]:
                break  # No more candidates

            selected.append(best_section[1][0])
            elements_covered += 1
            best_section[1].pop(0)

        return selected


# Convenience function for simple usage
def generate_questions_from_sections(
    sections: List[Dict[str, Any]],
    document_text: str,
    document_path: str = ""
) -> QuestioningResult:
    """
    Generate questions from sections (convenience function).

    Args:
        sections: List of section dicts
        document_text: Full document content
        document_path: Path to source document

    Returns:
        QuestioningResult with generated questions
    """
    step = QuestioningStep()
    return step.generate_questions(sections, document_text, document_path)


# For testing the module directly
if __name__ == '__main__':
    import sys

    print("Question-Based Testing Module")
    print("=" * 50)
    print(f"Version: 1.0.0-phase2")
    print(f"Status: Phase 1 - Core Infrastructure")
    print()
    print("Phase 1: Core dataclasses implemented")
    print("  ✓ Question dataclass")
    print("  ✓ QuestionAnswer dataclass (stub)")
    print("  ✓ QuestionEvaluation dataclass (stub)")
    print("  ✓ QuestionResult dataclass (stub)")
    print("  ✓ QuestioningResult dataclass")
    print("  ✓ save()/load() methods with UTF-8 support")
    print()
    print("Phase 2: To be implemented")
    print("  - Template library (14 templates)")
    print("  - Element extraction (8 regex patterns)")
    print("  - Template application logic")
    print("  - Question validation")
    print("  - Coverage metrics")
    print()

    # Demo: Create a sample question and serialize it
    print("Demo: Creating and serializing a sample question")
    print("-" * 50)

    sample_question = Question(
        question_id="q_001",
        question_text="According to the Configuration section, what format should the output use?",
        category="factual",
        difficulty="basic",
        scope="section",
        target_sections=["section_3"],
        expected_answer={
            "text": "JSON format with UTF-8 encoding",
            "source_lines": [45, 46],
            "confidence": "high"
        },
        generation_method="template",
        template_id="factual_format_01",
        is_adversarial=False,
        metadata={"testable_element": "requirement"}
    )

    print(f"Question ID: {sample_question.question_id}")
    print(f"Category: {sample_question.category}")
    print(f"Difficulty: {sample_question.difficulty}")
    print(f"Question: {sample_question.question_text}")
    print(f"Expected Answer: {sample_question.expected_answer['text']}")
    print()

    # Test serialization
    question_dict = sample_question.to_dict()
    print("✓ Serialized to dict")

    reconstructed = Question.from_dict(question_dict)
    print("✓ Deserialized from dict")
    print(f"✓ Round-trip successful: {reconstructed.question_id == sample_question.question_id}")
    print()

    # Test QuestioningResult
    result = QuestioningResult(
        questions=[sample_question],
        document_path="test_document.md",
        generation_timestamp=datetime.now().isoformat(),
        generator_version="1.0.0-phase2"
    )

    result.calculate_statistics(total_sections=10, total_elements=25)

    print("QuestioningResult statistics:")
    print(f"  Total questions: {result.statistics['total_questions']}")
    print(f"  Section coverage: {result.statistics['coverage']['section_coverage_pct']}%")
    print(f"  Element coverage: {result.statistics['coverage']['element_coverage_pct']}%")
    print()

    # Test save/load if output path provided
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
        print(f"Saving to: {output_dir}")
        result.save(output_dir)
        print("✓ Saved questions.json")

        loaded = QuestioningResult.load(output_dir)
        print("✓ Loaded questions.json")
        print(f"✓ Round-trip successful: {len(loaded.questions)} question(s) loaded")
    else:
        print("Usage: python questioning_step.py [output_dir]")
        print("  (optional: specify output directory to test save/load)")
