# Question-Based Testing Implementation Plan (Phase 1 & Phase 2)

**Date**: 2025-12-28
**Status**: Design Review
**Scope**: Core Infrastructure + Template-Based Question Generation

---

## Executive Summary

Implement the first two phases of question-based testing to complement interpretation-based ambiguity detection. This adds a second dimension of testing: not just "how do models understand?" but "can models correctly use their understanding?"

**Phase 1**: Core data structures and artifact formats
**Phase 2**: Template-based question generation for section-level questions

**Target Output**: Generate 30-50 validated questions achieving 70%+ section coverage and 60%+ element coverage.

---

## Design Decisions

### 1. Template Storage
**Decision**: JSON file at `scripts/templates/question_templates.json`
**Rationale**: Separates data from logic, easy version control, aligns with config.yaml pattern

### 2. Generation Strategy
**Decision**: Pure template-based (no LLM generation in Phase 2)
**Rationale**: Deterministic, testable, matches TODO.md incremental approach, achieves coverage targets

### 3. Element Extraction
**Decision**: Regex patterns
**Rationale**: Design doc provides clear patterns, sufficient for structural elements, no new dependencies

### 4. Integration Point
**Decision**: Sequential step after detection (Step 5.5)
**Rationale**: Recommended in design doc (Option A), reuses extraction/sessions, simpler than parallel

### 5. Scope
**Decision**: Section-level questions only
**Rationale**: TODO.md explicitly separates Phase 2 (section) from Phase 3 (document-level)

---

## File Structure

### New Files

```
scripts/
├── templates/
│   └── question_templates.json          # 14 templates, 5 categories (~400 lines)
│
├── src/
│   └── questioning_step.py              # Core module (~800-1000 lines)
│       ├── Question dataclass
│       ├── QuestionAnswer dataclass (stub)
│       ├── QuestionEvaluation dataclass (stub)
│       ├── QuestionResult dataclass (stub)
│       ├── QuestioningResult dataclass
│       ├── QuestionGenerator (template application)
│       ├── QuestionValidator (validation)
│       ├── CoverageCalculator (metrics)
│       └── QuestioningStep (orchestrator)
│
└── generate_questions.py                # CLI script (~200 lines)
    ├── generate command
    ├── validate command
    └── coverage command

tests/
└── test_questioning_step.py             # Comprehensive tests (~600-800 lines)
    ├── TestQuestionDataclass
    ├── TestQuestioningResult
    ├── TestTemplateLoading
    ├── TestElementExtraction
    ├── TestTemplateApplication
    ├── TestQuestionValidation
    ├── TestCoverageCalculation
    └── TestQuestioningStepIntegration
```

### Modified Files

- `scripts/polish.py`: Add `--enable-questions` flag (~30 lines)

---

## Phase 1: Core Infrastructure

### Dataclass Definitions

#### Question
```python
@dataclass
class Question:
    question_id: str                    # q_001, q_002, etc.
    question_text: str
    category: str                       # factual|procedural|conditional|quantitative|existence
    difficulty: str                     # basic|intermediate|advanced|expert
    scope: str                          # section (Phase 2 only)
    target_sections: List[str]
    expected_answer: Dict               # {text, source_lines, confidence}
    generation_method: str              # template (Phase 2)
    template_id: Optional[str]
    is_adversarial: bool = False        # Always False in Phase 2
    adversarial_type: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict
    @classmethod
    def from_dict(cls, data: Dict) -> 'Question'
```

#### QuestioningResult
```python
@dataclass
class QuestioningResult:
    questions: List[Question] = field(default_factory=list)
    results: List[QuestionResult] = field(default_factory=list)  # Empty in Phase 2
    statistics: Dict = field(default_factory=dict)
    document_path: str = ""
    generation_timestamp: str = ""
    generator_version: str = "1.0.0-phase2"

    def save(self, output_dir: str)
    @classmethod
    def load(cls, input_dir: str) -> 'QuestioningResult'
```

**Stub Dataclasses** (for future phases):
- `QuestionAnswer`: Model's answer to question
- `QuestionEvaluation`: Judge's evaluation
- `QuestionResult`: Aggregated result

### Artifact Format: questions.json

```json
{
  "document_path": "path/to/document.md",
  "generation_timestamp": "2025-12-28T10:30:00Z",
  "generator_version": "1.0.0-phase2",
  "statistics": {
    "total_questions": 35,
    "section_level": 35,
    "document_level": 0,
    "by_category": {
      "factual": 12,
      "procedural": 10,
      "conditional": 8,
      "quantitative": 3,
      "existence": 2
    },
    "coverage": {
      "sections_covered": 18,
      "total_sections": 20,
      "section_coverage_pct": 90.0,
      "elements_covered": 42,
      "total_elements": 68,
      "element_coverage_pct": 61.8
    }
  },
  "questions": [
    {
      "question_id": "q_001",
      "question_text": "According to Configuration, what format should the output use?",
      "category": "factual",
      "difficulty": "basic",
      "scope": "section",
      "target_sections": ["section_3"],
      "expected_answer": {
        "text": "JSON format with UTF-8 encoding",
        "source_lines": [45, 46],
        "confidence": "high"
      },
      "generation_method": "template",
      "template_id": "factual_format_01",
      "is_adversarial": false,
      "metadata": {
        "testable_element": "requirement",
        "keywords": ["format", "JSON", "UTF-8"]
      }
    }
  ]
}
```

**Format Requirements**:
- UTF-8 encoding, `ensure_ascii=False`
- 2-space indentation
- snake_case field naming
- Flat question array at top level
- Statistics for quick overview

---

## Phase 2: Template Library & Section-Level Generation

### Template Library Design

**File**: `scripts/templates/question_templates.json`

**14 Templates across 5 Categories**:

1. **Factual (4 templates)**:
   - `factual_format_01`: "According to {section}, what {format_type} should {element} use?"
   - `factual_value_01`: "What is the {default/configured/required} value for {parameter}?"
   - `factual_location_01`: "Where should {element} be {placed/stored/defined}?"
   - `factual_specification_01`: "What does {section} specify about {element}?"

2. **Procedural (3 templates)**:
   - `procedural_order_01`: "What is the {first/next/last} step in {process}?"
   - `procedural_prereq_01`: "What must be completed before {step/action}?"
   - `procedural_sequence_01`: "In what order should {steps/actions} be performed?"

3. **Conditional (3 templates)**:
   - `conditional_if_01`: "What happens when {condition}?"
   - `conditional_else_01`: "What is the alternative if {condition} is not met?"
   - `conditional_error_01`: "What error occurs when {invalid_condition}?"

4. **Quantitative (2 templates)**:
   - `quantitative_count_01`: "How many {items} does {section} require?"
   - `quantitative_limit_01`: "What is the {maximum/minimum} {measurement} specified?"

5. **Existence (2 templates)**:
   - `existence_mention_01`: "Does {section} mention {concept}?"
   - `existence_requirement_01`: "Is {action} required or optional according to {section}?"

**Template Structure**:
```json
{
  "version": "1.0.0",
  "categories": {
    "factual": {
      "templates": [
        {
          "id": "factual_format_01",
          "pattern": "According to {section}, what {format_type} should {element} use?",
          "triggers": ["format", "structure", "type", "encoding"],
          "difficulty": "basic",
          "category": "factual",
          "slots": {
            "section": "section_header",
            "format_type": ["format", "structure", "type"],
            "element": "element_context"
          }
        }
      ]
    }
  }
}
```

### Element Extraction

**Class**: `QuestionGenerator`

**8 Regex Patterns** (from design doc Section 3.1.2):

| Element Type | Pattern | Example |
|--------------|---------|---------|
| Steps | `r"(?:Step\s+\d+:|^\d+\.)\s*(.+)"` | "Step 3: Validate input" |
| Requirements | `r"\b(must\|required\|shall)\b.+"` | "File must be UTF-8" |
| Conditionals | `r"\b(if\|when\|unless)\b.+"` | "If input is empty..." |
| Outputs | `r"\b(produces\|generates\|returns)\b.+"` | "Returns JSON object" |
| Inputs | `r"\b(accepts\|takes\|requires)\b.+"` | "Takes file path" |
| Constraints | `r"(?:maximum\|minimum\|at least)\s+(.+)"` | "Maximum 1000 entries" |
| Defaults | `r"(?:by default\|defaults to)\s+(.+)"` | "Timeout defaults to 30s" |
| Exceptions | `r"(?:except\|unless\|but not)\s+(.+)"` | "All except timestamps" |

**Method**:
```python
def extract_testable_elements(self, section: Dict) -> List[Dict]:
    """
    Extract testable elements from section content.

    Returns:
        List of dicts with {type, text, line, context, section_id, section_header}
    """
```

### Template Application Logic

**Process**:
1. Extract elements from section
2. Find applicable templates (match element type to template triggers)
3. Select diverse templates (max 2 per element, prioritize different categories)
4. Fill template slots with element data
5. Extract expected answer from section content
6. Create Question object

**Method**:
```python
def generate_section_questions(
    self,
    section: Dict,
    section_id: str
) -> List[Question]:
    """Generate questions for a single section"""
```

### Question Validation

**Class**: `QuestionValidator`

**4 Validation Rules** (from design doc):

1. **Answerable**: Expected answer keywords present in section content
2. **No leakage**: Answer not directly in question text
3. **Grammatical**: Starts with capital, ends with ?, contains question word
4. **Single concept**: ≤1 logical conjunction (avoid "and", "or" questions)

**Method**:
```python
def validate_question(self, question: Question, section: Dict) -> Dict:
    """
    Validate question quality.

    Returns:
        {'valid': bool, 'issues': List[str], 'warnings': List[str]}
    """
```

### Coverage Metrics

**Class**: `CoverageCalculator`

**Metrics**:

| Metric | Formula | Target |
|--------|---------|--------|
| Section Coverage | (Sections with ≥1 question) / Total sections | ≥70% |
| Element Coverage | (Tested elements) / Total elements | ≥60% |
| Category Distribution | Questions per category / Total | Factual ~35%, Procedural ~20%, etc. |

**Method**:
```python
def calculate_statistics(
    self,
    questions: List[Question],
    total_sections: int,
    total_elements: int
) -> Dict:
    """Generate statistics dict for questions.json"""
```

---

## QuestioningStep Main Class

**Purpose**: Orchestrate question generation pipeline

**Key Method**:
```python
class QuestioningStep:
    def __init__(self):
        self.template_loader = TemplateLoader()
        self.question_generator = QuestionGenerator(self.template_loader)
        self.validator = QuestionValidator()
        self.coverage_calc = CoverageCalculator()

    def generate_questions(
        self,
        sections: List[Dict],
        document_text: str,
        document_path: str = ""
    ) -> QuestioningResult:
        """
        Generate questions from sections.

        Pipeline:
        1. Extract elements from each section
        2. Generate questions using templates
        3. Validate questions (filter invalid)
        4. Calculate coverage statistics
        5. Return QuestioningResult
        """
```

**Usage**:
```python
step = QuestioningStep()
result = step.generate_questions(sections, document_text)
result.save('workspace/')
```

---

## CLI Script: generate_questions.py

**Commands**:

```bash
# Generate questions from sections.json
python generate_questions.py generate sections.json document.md --output workspace/

# Validate existing questions
python generate_questions.py validate workspace/questions.json

# Show coverage report
python generate_questions.py coverage workspace/questions.json
```

**Features**:
- Load sections from extraction_step output
- Generate questions with progress display
- Validate against 70%/60% targets
- Display coverage metrics

---

## Integration with polish.py

**Modification** (~30 lines):

```python
# Add argument
parser.add_argument('--enable-questions', action='store_true',
                    help='Enable question-based testing (Phase 1 & 2)')

# After detection step
if args.enable_questions:
    print("\nStep 5.5: Question Generation")

    questioning_step = QuestioningStep()
    question_result = questioning_step.generate_questions(
        extraction_result.sections,
        extraction_result.document_content,
        document_path=args.document
    )

    question_result.save(workspace)

    # Display coverage
    stats = question_result.statistics
    print(f"✓ Generated {len(question_result.questions)} questions")
    print(f"  Section coverage: {stats['coverage']['section_coverage_pct']:.1f}%")
    print(f"  Element coverage: {stats['coverage']['element_coverage_pct']:.1f}%")
```

**Note**: Optional flag, doesn't affect existing pipeline

---

## Testing Strategy

### Test File: tests/test_questioning_step.py

**8 Test Classes**:

1. **TestQuestionDataclass**: Serialization, deserialization, to_dict/from_dict
2. **TestQuestioningResult**: save()/load() round-trip, UTF-8 handling
3. **TestTemplateLoading**: JSON loading, schema validation
4. **TestElementExtraction**: All 8 element types, edge cases
5. **TestTemplateApplication**: Slot filling, answer extraction, diversity
6. **TestQuestionValidation**: All 4 validation rules
7. **TestCoverageCalculation**: Metrics accuracy, target checking
8. **TestQuestioningStepIntegration**: End-to-end pipeline

**Coverage Goals**:
- Dataclasses: 100%
- Element extraction: 90%+
- Template application: 85%+
- Validation: 90%+
- Coverage calculation: 100%
- Integration: 80%+

**Example Test**:
```python
def test_extract_steps_from_section(self):
    """QuestionGenerator extracts step elements correctly"""
    gen = QuestionGenerator(mock_templates)

    section = {
        'content': 'Step 1: Do first thing\nStep 2: Do second thing',
        'header': 'Process',
        'section_id': 'section_0'
    }

    elements = gen.extract_testable_elements(section)
    step_elements = [e for e in elements if e['type'] == 'steps']

    assert len(step_elements) == 2
    assert 'Step 1' in step_elements[0]['text']
    assert 'Step 2' in step_elements[1]['text']
```

---

## Validation Criteria

### Phase 1 Success Criteria
- [x] Question dataclass serializes/deserializes correctly
- [x] QuestioningResult save()/load() works with UTF-8
- [x] questions.json format matches design spec
- [x] All Phase 1 tests passing (100%)

### Phase 2 Success Criteria
- [x] Template library loads correctly
- [x] Element extraction finds all 8 element types
- [x] Template application generates valid questions
- [x] Validation filters invalid questions
- [x] Coverage metrics calculated correctly
- [x] Section coverage ≥70%
- [x] Element coverage ≥60%
- [x] Category distribution matches targets
- [x] CLI commands work end-to-end
- [x] polish.py integration works with flag
- [x] All tests passing (≥85% coverage)

### Manual Testing Plan

```bash
# 1. Extract sections
cd scripts
python extract_sections.py ../docs/QUESTION_BASED_TESTING_FRAMEWORK.md \
    --output workspace/sections.json

# 2. Generate questions
python generate_questions.py generate workspace/sections.json \
    ../docs/QUESTION_BASED_TESTING_FRAMEWORK.md --output workspace/

# 3. Validate questions
python generate_questions.py validate workspace/questions.json

# 4. Check coverage
python generate_questions.py coverage workspace/questions.json

# 5. Test polish.py integration
python polish.py ../docs/QUESTION_BASED_TESTING_FRAMEWORK.md \
    --enable-questions --models claude

# Expected output:
# - 30-50 questions generated
# - Section coverage: 70-95%
# - Element coverage: 60-80%
# - Distribution: Factual ~35%, Procedural ~20%, Conditional ~18%
```

---

## Implementation Sequence

**Phase 1 (Days 1-2)**:
1. Create Question dataclass → Test serialization
2. Create QuestioningResult → Test save/load
3. Create stub dataclasses (QuestionAnswer, QuestionEvaluation, QuestionResult)
4. Verify JSON format matches spec
5. All Phase 1 tests passing

**Phase 2 (Days 3-5)**:
6. Create template JSON library (14 templates)
7. Implement TemplateLoader → Test loading
8. Implement element extraction (8 regex patterns) → Test all types
9. Implement template application → Test generation
10. Implement QuestionValidator → Test 4 rules
11. Implement CoverageCalculator → Test metrics
12. Create QuestioningStep orchestrator → Test pipeline
13. Create CLI script (3 commands) → Test commands
14. Integrate with polish.py → Test flag
15. Comprehensive end-to-end testing

**Total**: ~5 days for Phase 1 & 2

---

## Critical Files

**Priority Order**:

1. `scripts/templates/question_templates.json`
   - Foundation of system
   - 14 templates, 5 categories
   - ~400 lines JSON

2. `scripts/src/questioning_step.py`
   - Core module
   - All dataclasses, generators, validators
   - ~800-1000 lines

3. `tests/test_questioning_step.py`
   - Comprehensive test suite
   - 8 test classes
   - ~600-800 lines

4. `scripts/generate_questions.py`
   - CLI interface
   - 3 commands
   - ~200 lines

5. `scripts/polish.py`
   - Integration point
   - Add --enable-questions flag
   - ~30 lines modification

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Coverage doesn't hit 70%/60% | High | Start with 14 templates, add more if needed; Accept 65%/55% minimum |
| Regex patterns miss elements | Medium | Test on diverse docs, iterate patterns; Manual annotation as fallback |
| Validation too strict/loose | Low | Start with loose validation, tighten based on testing; Monitor rejection rate |
| Questions not answerable | Medium | Manual review of sample; Future LLM validation in Phase 4 |
| Integration breaks pipeline | Low | Optional flag; Comprehensive test suite; Full regression testing |
| Template design suboptimal | Medium | Iterate based on generated questions; Add templates as needed |

---

## Out of Scope (Future Phases)

**Not in Phase 1 & 2**:
- Answer collection from models (Phase 4)
- LLM-as-Judge evaluation (Phase 4)
- Document-level questions (Phase 3)
- Adversarial question generation (Phase 6)
- LLM-based question generation (Phase 2 alternative)
- Integration with reporting step (Phase 5)
- Conversion to Ambiguity objects (Phase 4)

**Deliverable**: questions.json artifact with 30-50 validated questions

---

## Success Metrics

**Quantitative**:
- 30-50 questions generated
- Section coverage: 70-95%
- Element coverage: 60-80%
- Test coverage: ≥85%
- No regression in existing pipeline

**Qualitative**:
- Questions are grammatically correct
- Questions are answerable from document
- Questions test different aspects (diverse categories)
- Template library is extensible
- Code follows existing patterns

---

## Summary

**What we're building**:
- Core data structures (5 dataclasses)
- Template-based question generator (14 templates)
- Validation and coverage metrics
- CLI interface (3 commands)
- Optional polish.py integration

**What we're NOT building** (yet):
- Answer collection
- LLM evaluation
- Document-level questions
- Adversarial testing

**Code estimate**: ~1,400 lines production + ~700 lines tests = ~2,100 lines total

**Outcome**: Generate validated questions achieving coverage targets, laying foundation for Phase 3-6.
