# Question-Based Testing: Phase 3, 4, 5 Implementation Plan

**Date**: 2025-12-28
**Status**: Planning
**Scope**: Document-level questions, answer collection, evaluation, and integration

---

## Executive Summary

Implement the final three phases of the Question-Based Testing Framework:
- **Phase 3**: Document-level question generation (dependencies, conflicts)
- **Phase 4**: Answer collection and LLM-as-Judge evaluation
- **Phase 5**: Integration with polish.py and comprehensive reporting

**Timeline**: Single implementation batch (Phases 3-5 together)
**Estimated LOC**: ~1,500 production + ~800 tests = ~2,300 total

---

## Phase 3: Document-Level Questions

### Objective
Generate 5-10 high-value questions about cross-section dependencies and potential conflicts.

### 3.1 Cross-Reference Analysis

**Implementation**: Add to `questioning_step.py`

```python
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

    def analyze_references(self, sections: List[Dict]) -> Dict[str, List[str]]:
        """
        Build dependency graph from cross-references.

        Note: Sections from DocumentProcessor have 'header', 'content', 'start_line', 'end_line'.
        We generate section_id by slugifying the header (e.g., "Step 1: Setup" → "step-1-setup")
        and match cross-references against both section_id and original header text.

        Returns:
            Dict mapping section_id -> [referenced_section_ids]
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

        return dependencies

    def _slugify(self, text: str) -> str:
        """Convert header to section_id (e.g., 'Step 1: Setup' → 'step-1-setup')"""
        import re
        # Remove special chars, lowercase, replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        return slug[:50]  # Limit length

    def _extract_references(self, content: str, header_to_id: Dict[str, str]) -> List[str]:
        """Extract section references from content and map to section_ids."""
        # Implementation details...
```

**Output**: `dependencies.json`
```json
{
  "dependencies": {
    "workflow-step-3": ["prerequisites", "configuration"],
    "deployment": ["workflow-step-3"]
  },
  "cycles": [],
  "orphans": ["appendix-a"]
}
```

### 3.2 Conflict Detection

**Implementation**: Add to `questioning_step.py`

```python
class ConflictDetector:
    """Detects potential conflicts between sections."""

    CONFLICT_INDICATORS = {
        'contradictory_requirements': [
            ('must', 'must not'),
            ('required', 'optional'),
            ('always', 'never')
        ],
        'overlapping_responsibilities': [
            'step', 'procedure', 'process'
        ]
    }

    def detect_conflicts(self, sections: List[Dict]) -> List[Dict]:
        """
        Identify potential conflicts.

        Returns:
            List of conflict dicts with sections and evidence
        """
```

**Output**: Conflicts added to metadata
```json
{
  "potential_conflicts": [
    {
      "section_pair": ["section_2", "section_5"],
      "conflict_type": "contradictory_requirements",
      "evidence": "Section 2 requires X, Section 5 prohibits X"
    }
  ]
}
```

### 3.3 Document-Level Question Templates

**Add to `question_templates.json`**:

```json
{
  "template_id": "document_dependency_01",
  "category": "procedural",
  "difficulty": "advanced",
  "scope": "document",
  "question_pattern": "What must be completed before {target_section} according to {source_section}?",
  "triggers": {
    "requires_dependency": true,
    "min_dependency_depth": 1
  }
},
{
  "template_id": "document_conflict_01",
  "category": "conditional",
  "difficulty": "expert",
  "scope": "document",
  "question_pattern": "How do {section_a} and {section_b} differ in their handling of {conflicting_element}?",
  "triggers": {
    "requires_conflict": true
  }
}
```

**Target**: 5-10 document-level questions per document

### 3.4 Testing

**New tests in `test_questioning_step.py`**:
- `TestCrossReferenceAnalysis` (5 tests)
  - Extract explicit references
  - Detect circular dependencies
  - Identify orphaned sections
- `TestConflictDetection` (4 tests)
  - Contradictory requirements
  - Overlapping responsibilities
- `TestDocumentLevelGeneration` (6 tests)
  - Dependency questions
  - Conflict questions
  - Coverage metrics

**Target**: ≥80% coverage for Phase 3 code

---

## Phase 4: Answer Collection & Evaluation

### Objective
Query models with generated questions, evaluate answers using LLM-as-Judge, detect comprehension issues.

### 4.1 Answer Collection

**Implementation**: Extend `questioning_step.py`

```python
class AnswerCollector:
    """Collects model answers to questions (reuses session management)."""

    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager

    def collect_answers(
        self,
        questions: List[Question],
        models: List[str]
    ) -> Dict[str, List[QuestionAnswer]]:
        """
        Query models with questions.

        Reuses existing sessions from interpretation testing.

        Returns:
            Dict mapping question_id -> [answers from all models]
        """
```

**Prompt Template**:
```
You are being tested on your comprehension of documentation.

DOCUMENT CONTEXT (from previous messages in this session):
[Already loaded via session management]

QUESTION:
{question_text}

Provide your answer in this exact JSON format:
{
  "answer": "Your answer here",
  "confidence": "high|medium|low",
  "reasoning": "Brief explanation of your answer"
}
```

**Output**: Updates `questions.json` with answers
```json
{
  "question_id": "q_001",
  "answers": {
    "claude": {
      "answer_text": "JSON format with UTF-8 encoding",
      "confidence_stated": "high",
      "response_time_ms": 1234,
      "raw_response": "{...}"
    },
    "gemini": {...},
    "codex": {...}
  }
}
```

### 4.2 LLM-as-Judge Evaluation

**Implementation**: Add to `questioning_step.py`

```python
class AnswerEvaluator:
    """Evaluates model answers using LLM-as-Judge."""

    def __init__(self, judge_model: str = "claude"):
        self.judge_model = judge_model

    def evaluate_answer(
        self,
        question: Question,
        answer: QuestionAnswer,
        context: str
    ) -> QuestionEvaluation:
        """
        Use LLM-as-Judge to evaluate answer correctness.

        Returns:
            QuestionEvaluation with score and reasoning
        """
```

**Judge Prompt Template**:
```
You are evaluating a model's answer to a documentation comprehension question.

DOCUMENTATION CONTEXT:
{section_content}

QUESTION:
{question_text}

EXPECTED ANSWER:
{expected_answer}

MODEL'S ANSWER:
{model_answer}

Evaluate the model's answer using this JSON format:
{
  "score": "correct|partially_correct|incorrect|unanswerable",
  "reasoning": "Explain why you assigned this score",
  "evidence": "Quote from documentation supporting your evaluation"
}

SCORING CRITERIA:
- correct: Answer matches expected answer in meaning
- partially_correct: Answer is incomplete or slightly off
- incorrect: Answer contradicts expected answer
- unanswerable: Question cannot be answered from provided context
```

**Scores**:
- `correct`: Full credit
- `partially_correct`: Partial credit
- `incorrect`: No credit
- `unanswerable`: Question issue (not model issue)

### 4.3 Consensus & Issue Detection

**Implementation**: Add to `questioning_step.py`

```python
class ConsensusCalculator:
    """Calculates consensus and detects comprehension issues."""

    def calculate_consensus(
        self,
        question: Question,
        evaluations: Dict[str, QuestionEvaluation]
    ) -> QuestionResult:
        """
        Determine consensus across models.

        Returns:
            QuestionResult with consensus type and issue detection
        """
```

**Consensus Types**:
- `agreement`: All models correct
- `partial_agreement`: Majority correct
- `disagreement`: No majority
- `widespread_failure`: All models incorrect (documentation issue!)

**Issue Detection**:
```python
def detect_issue(self, result: QuestionResult) -> Optional[Dict]:
    """
    Convert QuestionResult to Ambiguity-like issue.

    Returns:
        Issue dict if comprehension problem detected
    """
    if result.consensus == 'disagreement':
        return {
            'type': 'comprehension_divergence',
            'severity': 'MEDIUM',
            'question_id': result.question.question_id,
            'models_correct': [...],
            'models_incorrect': [...]
        }
    elif result.consensus == 'widespread_failure':
        return {
            'type': 'unanswerable_question',
            'severity': 'HIGH',
            'question_id': result.question.question_id,
            'reason': 'All models failed - likely documentation gap'
        }
```

### 4.4 Artifacts

**answers.json** (extends questions.json):
```json
{
  "question_id": "q_001",
  "question_text": "What format should the output use?",
  "answers": {
    "claude": {"answer_text": "JSON", "confidence": "high"},
    "gemini": {"answer_text": "JSON format", "confidence": "high"},
    "codex": {"answer_text": "JSON", "confidence": "medium"}
  },
  "evaluations": {
    "claude": {"score": "correct", "reasoning": "..."},
    "gemini": {"score": "correct", "reasoning": "..."},
    "codex": {"score": "partially_correct", "reasoning": "Missing details"}
  },
  "consensus": "partial_agreement",
  "issue_detected": true,
  "issue_type": "comprehension_divergence",
  "severity": "LOW"
}
```

**question_results.json** (summary):
```json
{
  "total_questions": 35,
  "section_level": 30,
  "document_level": 5,
  "consensus_breakdown": {
    "agreement": 28,
    "partial_agreement": 5,
    "disagreement": 2,
    "widespread_failure": 0
  },
  "issues_detected": 2,
  "coverage": {
    "section_coverage_pct": 75.0,
    "element_coverage_pct": 62.0
  }
}
```

### 4.5 Testing

**New tests**:
- `TestAnswerCollection` (5 tests)
  - Reuse sessions correctly
  - Handle model timeouts
  - Parse answer JSON
- `TestAnswerEvaluation` (6 tests)
  - Judge prompt formatting
  - Score parsing (all 4 types)
  - Evidence extraction
- `TestConsensusCalculation` (5 tests)
  - All consensus types
  - Issue detection logic
- `TestEndToEnd` (3 tests)
  - Full question → answer → evaluate pipeline
  - Integration with session management

**Target**: ≥85% coverage for Phase 4 code

---

## Phase 5: Integration & Reporting

### Objective
Integrate question testing into polish.py, add CLI commands, enhance reporting.

### 5.1 QuestioningStep Integration

**Update `questioning_step.py`**: Combine Phase 2-4 into unified step

```python
class QuestioningStep:
    """
    Step 5: Generate and test questions.

    Combines:
    - Question generation (Phase 2)
    - Answer collection (Phase 4)
    - Evaluation (Phase 4)
    """

    def __init__(self, session_manager):
        """
        Initialize questioning step.

        Args:
            session_manager: SessionManager for answer collection (required for Phase 4)
        """
        self.session_manager = session_manager

    def generate_questions(self, sections, document_text):
        """Phase 2: Generate questions from sections"""

    def collect_answers(self, questions, models):
        """
        Phase 4: Collect answers from models using existing sessions.

        Args:
            questions: List of Question objects
            models: List of model names to query

        Returns:
            AnswerResult with collected answers
        """

    def evaluate_answers(self, questions, answers):
        """Phase 4: Evaluate answers with LLM-as-Judge"""

    def detect_issues(self, results):
        """Phase 4: Convert results to ambiguity-like issues"""
```

### 5.2 CLI Script

**Create `scripts/test_questions.py`**:

```python
#!/usr/bin/env python3
"""
Test Questions CLI - Question-based testing workflow

Commands:
    generate  - Generate questions from sections
    test      - Collect answers from models
    evaluate  - Evaluate answers with judge
    auto      - Run full pipeline (generate → test → evaluate)
"""

def cmd_generate(args):
    """Generate questions (Phase 2)"""

def cmd_test(args):
    """Collect answers (Phase 4)"""

def cmd_evaluate(args):
    """Evaluate answers (Phase 4)"""

def cmd_auto(args):
    """Run full pipeline"""
```

**Usage**:
```bash
# Full pipeline
python scripts/test_questions.py auto workspace/sections.json document.md

# Or step-by-step
python scripts/test_questions.py generate workspace/sections.json document.md
python scripts/test_questions.py test workspace/questions.json --session workspace/session_metadata.json
python scripts/test_questions.py evaluate workspace/answers.json
```

### 5.3 Polish.py Integration

**Add to `polish.py`** after detection step:

```python
# Step 5: Question-based testing (optional)
if self.config.get('enable_question_testing', False):
    print("Step 5: Generating and testing questions...")
    self._log("Step 5: Generating and testing questions...")

    from src.questioning_step import QuestioningStep

    # Initialize with session manager for answer collection
    questioning = QuestioningStep(
        session_manager=self.model_manager.session_manager
    )

    # Generate questions
    question_result = questioning.generate_questions(
        sections=extraction_result.sections,
        document_text=self.document_text
    )
    question_result.save(str(self.workspace))

    # Collect answers (reuse sessions)
    answer_result = questioning.collect_answers(
        questions=question_result.questions,
        models=models
    )

    # Evaluate answers
    eval_result = questioning.evaluate_answers(
        questions=question_result.questions,
        answers=answer_result.answers
    )

    # Detect issues
    question_issues = questioning.detect_issues(eval_result.results)

    # Save question results as artifact
    question_results_file = self.workspace / "question_results.json"
    with open(question_results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_questions': len(question_result.questions),
            'issues_detected': len(question_issues),
            'consensus_breakdown': eval_result.consensus_breakdown,
            'coverage': question_result.statistics.get('coverage', {}),
            'issues': question_issues  # Full issue details
        }, f, indent=2, ensure_ascii=False)

    print(f"  Generated {len(question_result.questions)} questions")
    print(f"  Detected {len(question_issues)} comprehension issues")
    self._log(f"Generated {len(question_result.questions)} questions")
    self._log(f"Detected {len(question_issues)} comprehension issues")

    # Merge question issues with ambiguity results for reporting
    # Question issues use same format as ambiguity issues
    all_issues = ambiguities + question_issues
else:
    question_issues = []
    all_issues = ambiguities

# Step 6: Generate report (use all_issues instead of just ambiguities)
print("Step 6: Generating report...")
self._log("Step 6: Generating report...")

reporting_step = ReportingStep()
report_result = reporting_step.generate_report(
    sections=sections,
    ambiguities=all_issues,  # Include both ambiguities and question issues
    test_results=test_results,
    document_name=self.document_path.name
)
```

**Config option** in `scripts/config.yaml`:
```yaml
# Question-based testing (experimental)
enable_question_testing: false  # Set to true to enable
question_testing:
  coverage_targets:
    section_pct: 70.0
    element_pct: 60.0
  include_document_level: true
  max_questions: 50
```

### 5.4 Reporting Integration

**Add to `report.md`** (after ambiguities section):

```markdown
## Question-Based Testing Results

**Coverage:**
- Section coverage: 75.0% (22/29 sections)
- Element coverage: 62.0% (45/73 elements)
- Total questions: 35 (30 section-level, 5 document-level)

**Consensus:**
- Agreement: 28 questions (80.0%)
- Partial agreement: 5 questions (14.3%)
- Disagreement: 2 questions (5.7%)
- Widespread failure: 0 questions (0.0%)

**Issues Detected:** 2

### Issue 1: Comprehension Divergence (MEDIUM)
**Question:** What must be completed before Step 3?
**Section:** section_5 (Workflow)
**Models correct:** claude, gemini
**Models incorrect:** codex
**Codex answer:** "Step 1" (Expected: "Step 1 and Step 2")

**Recommendation:** Clarify dependency chain in section_5

---

### Issue 2: Comprehension Divergence (LOW)
**Question:** What is the default timeout value?
**Section:** section_8 (Configuration)
**Models correct:** claude, codex
**Models incorrect:** gemini
**Gemini answer:** "60 seconds" (Expected: "30 seconds")

**Recommendation:** Make default value more prominent in section_8

---

**Full results:** See `workspace/question_results.json`
```

**Add to summary**:
```markdown
## Summary

**Question Testing:**
- 35 questions generated (70% section coverage, 62% element coverage)
- 2 comprehension issues detected
- Recommendation: Review section_5 and section_8 for clarity improvements
```

### 5.5 Testing

**New tests**:
- `TestPolishIntegration` (4 tests)
  - Question testing enabled
  - Question testing disabled
  - Session reuse works
  - Report includes results
- `TestCLI` (5 tests)
  - All 4 commands work
  - Error handling
  - Artifact compatibility

**Target**: ≥85% coverage for Phase 5 code

---

## Implementation Sequence

### Batch 1: Phase 3 (Document-Level Questions)
1. Implement `CrossReferenceAnalyzer`
2. Implement `ConflictDetector`
3. Add document-level templates
4. Update `generate_questions()` to include document-level
5. Write tests (15 tests)
6. Update coverage calculation

**Deliverable**: Document-level questions working standalone

### Batch 2: Phase 4 (Answer Collection & Evaluation)
1. Implement `AnswerCollector` (reuse sessions)
2. Implement `AnswerEvaluator` (LLM-as-Judge)
3. Implement `ConsensusCalculator`
4. Update dataclasses (QuestionAnswer, QuestionEvaluation, QuestionResult)
5. Write tests (19 tests)
6. Create `question_results.json` format

**Deliverable**: Full question → answer → evaluate pipeline

### Batch 3: Phase 5 (Integration)
1. Create `test_questions.py` CLI
2. Integrate into `polish.py`
3. Add config options
4. Update reporting (report.md)
5. Write integration tests (9 tests)
6. Update TODO.md

**Deliverable**: Complete question-based testing feature

---

## Success Criteria

### Phase 3
- [ ] Cross-reference analysis extracts dependencies
- [ ] Conflict detection identifies contradictions
- [ ] Document-level questions generated (5-10 per document)
- [ ] Tests achieve ≥80% coverage
- [ ] Can generate document-level questions standalone

### Phase 4
- [ ] Answer collection reuses existing sessions
- [ ] LLM-as-Judge evaluates all 4 score types
- [ ] Consensus calculation detects issues
- [ ] Tests achieve ≥85% coverage
- [ ] Full pipeline works end-to-end

### Phase 5
- [ ] CLI commands work (generate, test, evaluate, auto)
- [ ] Polish.py integration optional via config
- [ ] Report includes question testing results
- [ ] Tests achieve ≥85% coverage
- [ ] All 127+ tests passing

---

## Risk Mitigation

### Risk 1: LLM-as-Judge reliability
**Mitigation**:
- Use Claude (most reliable) as default judge
- Log all judge responses for debugging
- Add manual review option for disputed scores

### Risk 2: Session reuse complexity
**Mitigation**:
- Reuse existing session_manager code (battle-tested)
- Add session validation before querying
- Fall back to new sessions if needed

### Risk 3: Report bloat
**Mitigation**:
- Summarize in report.md (top issues only)
- Full details in question_results.json
- Make question testing optional (config flag)

### Risk 4: Performance
**Mitigation**:
- Limit max questions to 50 by default
- Parallel model queries (already implemented)
- Cache judge responses

---

## Estimated Effort

**Phase 3**: ~500 LOC production + ~300 LOC tests = ~800 LOC
**Phase 4**: ~700 LOC production + ~400 LOC tests = ~1,100 LOC
**Phase 5**: ~300 LOC production + ~100 LOC tests = ~400 LOC

**Total**: ~1,500 LOC production + ~800 LOC tests = ~2,300 LOC

**Timeline**: 1 implementation session (all 3 phases together)

---

## Open Questions

1. **Judge model choice**: Always use Claude, or make configurable?
   - **Recommendation**: Default to Claude, allow config override

2. **Question limit**: 50 max or unlimited?
   - **Recommendation**: 50 max with config override

3. **Integration timing**: Before or after detection step?
   - **Recommendation**: After detection (Step 5)

4. **Reporting depth**: Summary only or detailed per-question?
   - **Recommendation**: Summary in report.md, details in JSON

---

## Next Steps

1. Review this plan with user
2. Implement Phase 3 (document-level questions)
3. Implement Phase 4 (answer collection & evaluation)
4. Implement Phase 5 (integration & reporting)
5. Run codex review on final implementation
6. Create PR with all three phases
7. Update documentation

---

## Appendix: File Structure

```
scripts/
├── src/
│   └── questioning_step.py          # Updated with Phase 3-4 code
├── templates/
│   └── question_templates.json      # Add document-level templates
├── generate_questions.py            # Existing (Phase 2)
└── test_questions.py                # New (Phase 5)

tests/
└── test_questioning_step.py         # Add Phase 3-5 tests

docs/
└── QUESTION_BASED_TESTING_FRAMEWORK.md  # Reference

temp/
└── QUESTION_TESTING_PHASE3_4_5_PLAN.md  # This file

workspace/
├── questions.json                   # Phase 2 output
├── answers.json                     # Phase 4 output (merged with questions)
└── question_results.json            # Phase 4 summary
```

---

**Status**: Ready for implementation
**Priority**: P2 (after Phase 1 & 2 complete)
**Dependencies**: Phase 1 & 2 must be complete and merged
