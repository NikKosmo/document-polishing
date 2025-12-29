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
            # Get or generate section_id from header
            section_id = section.get('section_id')
            if not section_id:
                header = section.get('header', '')
                # Generate section_id using same slugify logic as CrossReferenceAnalyzer
                section_id = re.sub(r'[^\w\s-]', '', header.lower())
                section_id = re.sub(r'[-\s]+', '-', section_id).strip('-')[:50]

            section_title = section.get('header', section.get('title', ''))
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

    def __init__(
        self,
        template_path: Optional[str] = None,
        enable_document_level: bool = True,
        session_manager=None,
        models_config: Optional[Dict] = None,
        session_config: Optional[Dict] = None
    ):
        """
        Initialize questioning step.

        Session management is automatic - sessions initialized with document
        context when collecting answers if not provided.

        Args:
            template_path: Path to question_templates.json (defaults to scripts/templates/)
            enable_document_level: Enable Phase 3 document-level question generation
            session_manager: Optional existing SessionManager (auto-created if needed)
            models_config: Model configuration for auto session creation
            session_config: Session configuration for auto session creation
        """
        self.generator_version = "1.0.0-phase5"
        self.enable_document_level = enable_document_level
        self.session_manager = session_manager
        self.models_config = models_config or {}
        self.session_config = session_config or {
            'enabled': True,
            'mode': 'continue-on-error',
            'max_retries': 2
        }

        # Determine template path
        if template_path is None:
            # Default to scripts/templates/question_templates.json
            current_dir = Path(__file__).parent
            template_path = current_dir.parent / 'templates' / 'question_templates.json'

        # Load templates
        loader = TemplateLoader(str(template_path))
        self.templates = loader.load()

        # Initialize Phase 2 components
        self.extractor = ElementExtractor()
        self.applicator = TemplateApplicator(self.templates)
        self.validator = QuestionValidator()

        # Initialize Phase 3 components
        if self.enable_document_level:
            self.ref_analyzer = CrossReferenceAnalyzer()
            self.conflict_detector = ConflictDetector()

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

        # Phase 3: Generate document-level questions (if enabled)
        if self.enable_document_level:
            doc_level_questions = self._generate_document_level_questions(
                sections,
                question_id_counter
            )
            selected_questions.extend(doc_level_questions)

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

    def collect_answers(
        self,
        questions: List[Question],
        models: List[str],
        document_text: str = "",
        session_manager=None
    ) -> Dict[str, Dict[str, QuestionAnswer]]:
        """
        Phase 4: Collect answers from models using sessions.

        Session management is automatic - if no session_manager provided,
        creates sessions with document context for better comprehension.

        Args:
            questions: List of Question objects
            models: List of model names to query
            document_text: Full document content for session initialization
            session_manager: Optional existing SessionManager (will create if None)

        Returns:
            Dict mapping question_id -> {model_name -> QuestionAnswer}
        """
        # Use provided session manager or create new one
        if session_manager is None:
            session_manager = self._ensure_session_manager(document_text, models)

        collector = AnswerCollector(session_manager)
        return collector.collect_answers(questions, models)

    def evaluate_answers(
        self,
        questions: List[Question],
        answers: Dict[str, Dict[str, QuestionAnswer]],
        sections: List[Dict[str, Any]],
        session_manager,
        judge_model: str = "claude"
    ) -> Dict[str, QuestionResult]:
        """
        Phase 4: Evaluate answers with LLM-as-Judge and calculate consensus.

        Args:
            questions: List of Question objects
            answers: Dict from collect_answers()
            sections: List of section dicts (for extracting context)
            session_manager: SessionManager for judge queries
            judge_model: Model to use as judge

        Returns:
            Dict mapping question_id -> QuestionResult
        """
        evaluator = AnswerEvaluator(judge_model, session_manager)
        calculator = ConsensusCalculator()

        # Build section_id -> section lookup map
        section_map = {}
        for section in sections:
            # Get section_id (either already present or generate from header)
            section_id = section.get('section_id')
            if not section_id and 'header' in section:
                # Generate section_id using same slugify logic as CrossReferenceAnalyzer
                header = section['header']
                section_id = re.sub(r'[^\w\s-]', '', header.lower())
                section_id = re.sub(r'[-\s]+', '-', section_id).strip('-')[:50]
            if section_id:
                section_map[section_id] = section

        results = {}

        for question in questions:
            question_answers = answers.get(question.question_id, {})

            # Extract context from question's target sections
            context_parts = []
            for section_id in question.target_sections:
                if section_id in section_map:
                    section = section_map[section_id]
                    # Build context with header and content
                    context_parts.append(f"## {section.get('header', section_id)}\n{section.get('content', '')}")

            context = "\n\n".join(context_parts) if context_parts else ""

            # Evaluate each model's answer
            evaluations = {}
            for model_name, answer in question_answers.items():
                evaluation = evaluator.evaluate_answer(question, answer, context)
                evaluations[model_name] = evaluation

            # Calculate consensus
            result = calculator.calculate_consensus(question, evaluations)
            result.answers = question_answers  # Add answers to result
            results[question.question_id] = result

        return results

    def detect_issues(
        self,
        results: Dict[str, QuestionResult]
    ) -> List[Dict]:
        """
        Phase 4: Convert QuestionResults to ambiguity-like issues.

        Args:
            results: Dict of question_id -> QuestionResult

        Returns:
            List of issue dicts
        """
        calculator = ConsensusCalculator()
        issues = []

        for result in results.values():
            issue = calculator.detect_issue(result)
            if issue:
                issues.append(issue)

        return issues

    def _ensure_session_manager(
        self,
        document_text: str,
        models: List[str]
    ):
        """
        Ensure session manager exists - create if needed.

        Automatically initializes sessions with document context for
        better question comprehension.

        Args:
            document_text: Full document content
            models: List of model names

        Returns:
            SessionManager with initialized sessions
        """
        if self.session_manager is not None:
            return self.session_manager

        # Import here to avoid circular dependency
        from session_init_step import SessionInitStep

        # Build minimal models_config if not provided
        if not self.models_config:
            self.models_config = {}
            for model in models:
                if model not in self.models_config:
                    self.models_config[model] = {
                        'command': model,
                        'timeout': 30
                    }

        # Initialize sessions with document context
        session_init = SessionInitStep(self.models_config, self.session_config)
        session_result = session_init.init_sessions(
            document_content=document_text,
            model_names=models,
            purpose_prompt="This document is being tested for comprehension. Please analyze questions about this documentation."
        )

        # Store for reuse
        self.session_manager = session_result.session_manager
        return self.session_manager

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

    def _generate_document_level_questions(
        self,
        sections: List[Dict[str, Any]],
        start_id: int
    ) -> List[Question]:
        """
        Generate document-level questions using Phase 3 analysis.

        Args:
            sections: List of section dicts
            start_id: Starting question ID number

        Returns:
            List of document-level Question objects
        """
        doc_questions = []
        question_id = start_id

        # Analyze cross-references and conflicts
        ref_analysis = self.ref_analyzer.analyze_references(sections)
        conflicts = self.conflict_detector.detect_conflicts(sections)

        # Get document-level templates
        doc_templates = [t for t in self.templates if t.get('scope') == 'document']

        # Generate dependency questions
        for source_id, target_ids in ref_analysis['dependencies'].items():
            for target_id in target_ids:
                # Find matching template
                dep_template = next((t for t in doc_templates if t.get('template_id') == 'document_dependency_01'), None)
                if dep_template:
                    question_text = dep_template['question_pattern'].format(
                        source_section=source_id,
                        target_section=target_id
                    )
                    expected_answer = f"Complete {source_id} before {target_id}"

                    question = Question(
                        question_id=f"q_{question_id:03d}",
                        question_text=question_text,
                        category=dep_template['category'],
                        difficulty=dep_template['difficulty'],
                        scope='document',
                        target_sections=[source_id, target_id],
                        expected_answer={
                            'text': expected_answer,
                            'confidence': 'medium'
                        },
                        generation_method='template',
                        template_id=dep_template['template_id'],
                        metadata={
                            'dependency_type': 'explicit',
                            'source': source_id,
                            'target': target_id
                        }
                    )
                    doc_questions.append(question)
                    question_id += 1

        # Generate conflict questions
        for conflict in conflicts:
            if conflict['type'] == 'contradictory_requirements':
                template = next((t for t in doc_templates if t.get('template_id') == 'document_conflict_01'), None)
                if template:
                    section_a, section_b = conflict['section_pair']
                    question_text = template['question_pattern'].format(
                        section_a=section_a,
                        section_b=section_b,
                        conflicting_element="requirements"
                    )
                    expected_answer = f"Conflict: {conflict['evidence']}"

                    question = Question(
                        question_id=f"q_{question_id:03d}",
                        question_text=question_text,
                        category=template['category'],
                        difficulty=template['difficulty'],
                        scope='document',
                        target_sections=conflict['section_pair'],
                        expected_answer={
                            'text': expected_answer,
                            'confidence': 'high'
                        },
                        generation_method='template',
                        template_id=template['template_id'],
                        metadata={
                            'conflict_type': conflict['type'],
                            'evidence': conflict['evidence']
                        }
                    )
                    doc_questions.append(question)
                    question_id += 1

            elif conflict['type'] == 'value_conflict':
                template = next((t for t in doc_templates if t.get('template_id') == 'document_conflict_02'), None)
                if template and len(conflict['conflicts']) >= 2:
                    first = conflict['conflicts'][0]
                    second = conflict['conflicts'][1]
                    question_text = template['question_pattern'].format(
                        term=conflict['term'],
                        value_a=first['value'],
                        section_a=first['section'],
                        value_b=second['value'],
                        section_b=second['section']
                    )
                    expected_answer = conflict['evidence']

                    question = Question(
                        question_id=f"q_{question_id:03d}",
                        question_text=question_text,
                        category=template['category'],
                        difficulty=template['difficulty'],
                        scope='document',
                        target_sections=[first['section'], second['section']],
                        expected_answer={
                            'text': expected_answer,
                            'confidence': 'high'
                        },
                        generation_method='template',
                        template_id=template['template_id'],
                        metadata={
                            'conflict_type': 'value_conflict',
                            'term': conflict['term']
                        }
                    )
                    doc_questions.append(question)
                    question_id += 1

        # Limit to 5-10 document-level questions
        return doc_questions[:10]


# ============================================================================
# Phase 3: Document-Level Analysis
# ============================================================================

class CrossReferenceAnalyzer:
    """Analyzes section cross-references to build dependency graph."""

    REFERENCE_PATTERNS = {
        'explicit': [
            # Match "See section X" or "Section 2.1" or "see the Setup section"
            r'(?:See|Refer to|As (?:described|shown) in)\s+(?:section\s+)?["\']?([A-Za-z0-9._\-\s]+?)["\']?\s+(?:section|for)',
            r'(?:section|Section)\s+([A-Za-z0-9._\-]+)',
        ],
        'implicit': [
            r'(?:above|previously|earlier)\s+(?:mentioned|described)',
            r'(?:following|next|subsequent)\s+section',
        ]
    }

    def _slugify(self, text: str) -> str:
        """
        Convert header to section_id (e.g., 'Step 1: Setup' → 'step-1-setup').

        Args:
            text: Header text to slugify

        Returns:
            Slugified section ID
        """
        # Remove special chars, lowercase, replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        return slug[:50]  # Limit length

    def _extract_references(self, content: str, header_to_id: Dict[str, str]) -> List[str]:
        """
        Extract section references from content and map to section_ids.

        Args:
            content: Section content to analyze
            header_to_id: Mapping of normalized headers to section IDs

        Returns:
            List of referenced section IDs
        """
        refs = set()

        # Try explicit patterns first
        for pattern in self.REFERENCE_PATTERNS['explicit']:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                ref_text = match.group(1).strip()
                # Normalize and look up in mapping
                normalized = ref_text.lower()
                if normalized in header_to_id:
                    refs.add(header_to_id[normalized])
                # Also try slugified version
                slugified = self._slugify(ref_text)
                if slugified in header_to_id:
                    refs.add(header_to_id[slugified])

        return list(refs)

    def analyze_references(self, sections: List[Dict]) -> Dict[str, Any]:
        """
        Build dependency graph from cross-references.

        Note: Sections from DocumentProcessor have 'header', 'content', 'start_line', 'end_line'.
        We generate section_id by slugifying the header (e.g., "Step 1: Setup" → "step-1-setup")
        and match cross-references against both section_id and original header text.

        Args:
            sections: List of section dicts from extraction

        Returns:
            Dict with dependencies, cycles, and orphans
        """
        # First, build section_id mapping
        section_map = {}  # section_id -> section dict
        header_to_id = {}  # normalized header -> section_id

        for i, section in enumerate(sections):
            # Generate section_id from header (fallback to index)
            header = section.get('header', f'section_{i}')
            section_id = self._slugify(header)

            # Add to section dict for downstream use
            section['section_id'] = section_id
            section_map[section_id] = section

            # Map normalized header variants for fuzzy matching
            header_to_id[header.lower()] = section_id
            header_to_id[section_id] = section_id

        # Build dependency graph
        dependencies = {}
        for section_id, section in section_map.items():
            refs = self._extract_references(section['content'], header_to_id)
            if refs:
                dependencies[section_id] = refs

        # Detect cycles (simple DFS-based detection)
        cycles = self._detect_cycles(dependencies)

        # Detect orphans (sections with no incoming or outgoing references)
        all_referenced = set()
        for refs in dependencies.values():
            all_referenced.update(refs)

        orphans = [
            sid for sid in section_map.keys()
            if sid not in dependencies and sid not in all_referenced
        ]

        return {
            'dependencies': dependencies,
            'cycles': cycles,
            'orphans': orphans,
            'section_map': section_map
        }

    def _detect_cycles(self, dependencies: Dict[str, List[str]]) -> List[List[str]]:
        """
        Detect circular dependencies using DFS.

        Args:
            dependencies: Dependency graph

        Returns:
            List of cycles (each cycle is a list of section IDs)
        """
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:])
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in dependencies.get(node, []):
                dfs(neighbor, path[:])

            rec_stack.remove(node)

        for node in dependencies:
            if node not in visited:
                dfs(node, [])

        return cycles


class ConflictDetector:
    """Detects potential conflicts between sections."""

    CONFLICT_INDICATORS = {
        'contradictory_requirements': [
            ('must', 'must not'),
            ('required', 'optional'),
            ('always', 'never'),
            ('should', 'should not'),
        ],
        'value_conflicts': [
            # Pattern to detect same term with different values
            r'(\w+)\s+(?:is|=|:)\s+([^\s]+)',
        ]
    }

    def detect_conflicts(self, sections: List[Dict]) -> List[Dict]:
        """
        Identify potential conflicts between sections.

        Args:
            sections: List of section dicts (with section_id)

        Returns:
            List of conflict dicts with sections and evidence
        """
        conflicts = []

        # Check for contradictory requirements
        for i, section_a in enumerate(sections):
            for section_b in sections[i+1:]:
                conflict = self._check_contradiction(section_a, section_b)
                if conflict:
                    conflicts.append(conflict)

        # Check for value conflicts (same term, different values)
        value_conflicts = self._detect_value_conflicts(sections)
        conflicts.extend(value_conflicts)

        return conflicts

    def _check_contradiction(self, section_a: Dict, section_b: Dict) -> Optional[Dict]:
        """
        Check if two sections have contradictory requirements.

        Args:
            section_a: First section
            section_b: Second section

        Returns:
            Conflict dict if found, None otherwise
        """
        content_a = section_a['content'].lower()
        content_b = section_b['content'].lower()

        # Get section IDs with safe fallback chain
        section_id_a = section_a.get('section_id') or section_a.get('header') or section_a.get('title', 'unknown')
        section_id_b = section_b.get('section_id') or section_b.get('header') or section_b.get('title', 'unknown')

        for positive, negative in self.CONFLICT_INDICATORS['contradictory_requirements']:
            if positive in content_a and negative in content_b:
                return {
                    'type': 'contradictory_requirements',
                    'section_pair': [section_id_a, section_id_b],
                    'evidence': f"Section {section_id_a} contains '{positive}', Section {section_id_b} contains '{negative}'"
                }
            elif negative in content_a and positive in content_b:
                return {
                    'type': 'contradictory_requirements',
                    'section_pair': [section_id_a, section_id_b],
                    'evidence': f"Section {section_id_a} contains '{negative}', Section {section_id_b} contains '{positive}'"
                }

        return None

    def _detect_value_conflicts(self, sections: List[Dict]) -> List[Dict]:
        """
        Detect cases where same term has different values across sections.

        Args:
            sections: List of section dicts

        Returns:
            List of value conflict dicts
        """
        conflicts = []
        term_values = {}  # term -> [(section_id, value)]

        # Extract term-value pairs from all sections
        for section in sections:
            # Get section ID with safe fallback chain
            section_id = section.get('section_id') or section.get('header') or section.get('title', 'unknown')
            content = section['content']

            for pattern in self.CONFLICT_INDICATORS['value_conflicts']:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    term = match.group(1).lower()
                    value = match.group(2).strip()

                    if term not in term_values:
                        term_values[term] = []
                    term_values[term].append((section_id, value))

        # Find terms with conflicting values
        for term, values in term_values.items():
            if len(values) > 1:
                unique_values = set(v[1] for v in values)
                if len(unique_values) > 1:
                    # Conflict: same term, different values
                    conflicts.append({
                        'type': 'value_conflict',
                        'term': term,
                        'conflicts': [
                            {'section': sid, 'value': val}
                            for sid, val in values
                        ],
                        'evidence': f"Term '{term}' has conflicting values: {', '.join(unique_values)}"
                    })

        return conflicts


# ============================================================================
# Phase 4: Answer Collection & Evaluation
# ============================================================================

class AnswerCollector:
    """Collects model answers to questions (reuses session management)."""

    def __init__(self, session_manager):
        """
        Initialize answer collector.

        Args:
            session_manager: SessionManager instance for model queries
        """
        self.session_manager = session_manager

    def collect_answers(
        self,
        questions: List[Question],
        models: List[str]
    ) -> Dict[str, Dict[str, QuestionAnswer]]:
        """
        Query models with questions using existing sessions.

        Args:
            questions: List of Question objects
            models: List of model names to query

        Returns:
            Dict mapping question_id -> {model_name -> QuestionAnswer}
        """
        import time
        answers = {}

        for question in questions:
            answers[question.question_id] = {}

            # Build prompt
            prompt = self._build_prompt(question)

            for model in models:
                try:
                    start_time = time.time()

                    # Query model using session
                    response_dict = self.session_manager.query_in_session(
                        model_name=model,
                        prompt=prompt
                    )

                    elapsed_ms = int((time.time() - start_time) * 1000)

                    # Extract response string for parsing
                    # query_in_session returns either parsed JSON or {"raw_response": "..."}
                    if 'raw_response' in response_dict:
                        response_str = response_dict['raw_response']
                    else:
                        # Already parsed JSON, serialize it for our parser
                        response_str = json.dumps(response_dict)

                    # Parse response
                    answer_data = self._parse_response(response_str)

                    # Create QuestionAnswer
                    answer = QuestionAnswer(
                        question_id=question.question_id,
                        model_name=model,
                        answer_text=answer_data.get('answer', ''),
                        response_time_ms=elapsed_ms,
                        raw_response=response_str,
                        confidence_stated=answer_data.get('confidence')
                    )

                    answers[question.question_id][model] = answer

                except Exception as e:
                    # Log error, create failed answer
                    print(f"Error collecting answer from {model} for {question.question_id}: {e}")
                    answers[question.question_id][model] = QuestionAnswer(
                        question_id=question.question_id,
                        model_name=model,
                        answer_text=f"ERROR: {str(e)}",
                        response_time_ms=0,
                        raw_response="",
                        confidence_stated="none"
                    )

        return answers

    def _build_prompt(self, question: Question) -> str:
        """
        Build prompt for answering a question.

        Args:
            question: Question object

        Returns:
            Formatted prompt string
        """
        return f"""You are being tested on your comprehension of documentation.

DOCUMENT CONTEXT (from previous messages in this session):
[Already loaded via session management]

QUESTION:
{question.question_text}

Provide your answer in this exact JSON format:
{{
  "answer": "Your answer here",
  "confidence": "high|medium|low",
  "reasoning": "Brief explanation of your answer"
}}"""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse model response to extract answer.

        Args:
            response: Raw model response

        Returns:
            Dict with 'answer', 'confidence', 'reasoning'
        """
        import json

        # Try to parse as JSON
        try:
            # Handle markdown-wrapped JSON
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                json_str = response[start:end].strip()
            elif '```' in response:
                start = response.find('```') + 3
                end = response.find('```', start)
                json_str = response[start:end].strip()
            else:
                json_str = response.strip()

            data = json.loads(json_str)
            return data

        except (json.JSONDecodeError, ValueError):
            # Fallback: treat entire response as answer
            return {
                'answer': response.strip(),
                'confidence': 'low',
                'reasoning': 'Failed to parse JSON response'
            }


class AnswerEvaluator:
    """Evaluates model answers using LLM-as-Judge."""

    def __init__(self, judge_model: str = "claude", session_manager=None):
        """
        Initialize answer evaluator.

        Args:
            judge_model: Model to use as judge (default: claude)
            session_manager: SessionManager for judge queries
        """
        self.judge_model = judge_model
        self.session_manager = session_manager

    def evaluate_answer(
        self,
        question: Question,
        answer: QuestionAnswer,
        context: str
    ) -> QuestionEvaluation:
        """
        Use LLM-as-Judge to evaluate answer correctness.

        Args:
            question: Question object
            answer: QuestionAnswer object
            context: Section content for reference

        Returns:
            QuestionEvaluation with score and reasoning
        """
        # Build judge prompt
        prompt = self._build_judge_prompt(question, answer, context)

        try:
            # Query judge model
            response_dict = self.session_manager.query_in_session(
                model_name=self.judge_model,
                prompt=prompt
            )

            # Extract response string for parsing
            if 'raw_response' in response_dict:
                response_str = response_dict['raw_response']
            else:
                response_str = json.dumps(response_dict)

            # Parse judge response
            eval_data = self._parse_judge_response(response_str)

            return QuestionEvaluation(
                question_id=question.question_id,
                model_name=answer.model_name,
                score=eval_data.get('score', 'incorrect'),
                reasoning=eval_data.get('reasoning', ''),
                evidence=eval_data.get('evidence', '')
            )

        except Exception as e:
            print(f"Error evaluating answer from {answer.model_name}: {e}")
            return QuestionEvaluation(
                question_id=question.question_id,
                model_name=answer.model_name,
                score='incorrect',
                reasoning=f'Judge error: {str(e)}',
                evidence=''
            )

    def _build_judge_prompt(self, question: Question, answer: QuestionAnswer, context: str) -> str:
        """Build LLM-as-Judge prompt."""
        return f"""You are evaluating a model's answer to a documentation comprehension question.

DOCUMENTATION CONTEXT:
{context}

QUESTION:
{question.question_text}

EXPECTED ANSWER:
{question.expected_answer['text']}

MODEL'S ANSWER:
{answer.answer_text}

Evaluate the model's answer using this JSON format:
{{
  "score": "correct|partially_correct|incorrect|unanswerable",
  "reasoning": "Explain why you assigned this score",
  "evidence": "Quote from documentation supporting your evaluation"
}}

SCORING CRITERIA:
- correct: Answer matches expected answer in meaning
- partially_correct: Answer is incomplete or slightly off
- incorrect: Answer contradicts expected answer
- unanswerable: Question cannot be answered from provided context"""

    def _parse_judge_response(self, response: str) -> Dict[str, Any]:
        """Parse judge response."""
        import json

        try:
            # Handle markdown-wrapped JSON
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                json_str = response[start:end].strip()
            elif '```' in response:
                start = response.find('```') + 3
                end = response.find('```', start)
                json_str = response[start:end].strip()
            else:
                json_str = response.strip()

            return json.loads(json_str)

        except (json.JSONDecodeError, ValueError):
            return {
                'score': 'incorrect',
                'reasoning': 'Failed to parse judge response',
                'evidence': ''
            }


class ConsensusCalculator:
    """Calculates consensus and detects comprehension issues."""

    def calculate_consensus(
        self,
        question: Question,
        evaluations: Dict[str, QuestionEvaluation]
    ) -> QuestionResult:
        """
        Determine consensus across models.

        Args:
            question: Question object
            evaluations: Dict of {model_name -> QuestionEvaluation}

        Returns:
            QuestionResult with consensus type and issue detection
        """
        if not evaluations:
            return QuestionResult(
                question=question,
                consensus='no_data',
                issue_detected=False
            )

        # Count scores
        scores = [e.score for e in evaluations.values()]
        correct_count = scores.count('correct')
        incorrect_count = scores.count('incorrect')
        partial_count = scores.count('partially_correct')
        unanswerable_count = scores.count('unanswerable')
        total = len(scores)

        # Determine consensus type
        if correct_count == total:
            consensus = 'agreement'
        elif correct_count >= total * 0.7:
            consensus = 'partial_agreement'
        elif incorrect_count == total or unanswerable_count == total:
            consensus = 'widespread_failure'
        else:
            consensus = 'disagreement'

        # Detect issues
        issue_detected = False
        issue_type = None
        severity = None
        recommendation = None

        if consensus == 'disagreement':
            issue_detected = True
            issue_type = 'comprehension_divergence'
            severity = 'MEDIUM'
            correct_models = [m for m, e in evaluations.items() if e.score == 'correct']
            incorrect_models = [m for m, e in evaluations.items() if e.score != 'correct']
            recommendation = f"Models disagree: {len(correct_models)} correct, {len(incorrect_models)} incorrect. Review question clarity."

        elif consensus == 'widespread_failure':
            issue_detected = True
            issue_type = 'unanswerable_question'
            severity = 'HIGH'
            recommendation = "All models failed - likely documentation gap or question issue."

        return QuestionResult(
            question=question,
            evaluations=evaluations,
            consensus=consensus,
            issue_detected=issue_detected,
            issue_type=issue_type,
            severity=severity,
            recommendation=recommendation
        )

    def detect_issue(self, result: QuestionResult) -> Optional[Dict]:
        """
        Convert QuestionResult to Ambiguity-like issue format.

        Args:
            result: QuestionResult

        Returns:
            Issue dict if comprehension problem detected, None otherwise
        """
        if not result.issue_detected:
            return None

        models_correct = [m for m, e in result.evaluations.items() if e.score == 'correct']
        models_incorrect = [m for m, e in result.evaluations.items() if e.score != 'correct']

        return {
            'type': result.issue_type,
            'severity': result.severity,
            'question_id': result.question.question_id,
            'question_text': result.question.question_text,
            'target_sections': result.question.target_sections,
            'models_correct': models_correct,
            'models_incorrect': models_incorrect,
            'consensus': result.consensus,
            'recommendation': result.recommendation
        }


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
