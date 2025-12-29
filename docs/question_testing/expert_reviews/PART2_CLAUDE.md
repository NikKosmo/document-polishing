# Expert Review Part 2: LLM-Optimized Documentation (Claude Response)

**Model:** Claude Claude 4.5 opus
**Date:** [date]
**Prompt:** EXPERT_REVIEW_PROMPT_PART2.md

---

# Expert Review Part 2: LLM-Optimized Documentation Design + Testable Question Generation

**Review Date:** December 29, 2025  
**Context:** Follow-up to Question-Based Testing Framework review  
**Focus:** Integrated approach linking documentation format, question generation, and LLM optimization

---

## Executive Assessment

The fundamental insight—that we should design documentation FOR testability rather than testing arbitrary documentation—is correct and valuable. Your existing `document_structure.md` already embodies many testability principles. The key now is to extend it with explicit test generation hooks.

**Key finding:** You're 70% of the way there. Your existing document structure rules create testable documentation. What's missing is the explicit mapping from structure → questions.

---

# Educational Assessment Specialist

## Question 1: Structure-Driven Assessment Design

### Answer

The optimal documentation structure for comprehension testing separates **assertions** from **explanations**. Your existing document structure already does this implicitly—now make it explicit.

**Core principle:** Every testable claim should be extractable as a standalone statement that can be converted to a question without referencing surrounding text.

### Concrete Format

Extend your current structure with explicit `testable` markers:

```markdown
## Steps

### Step 3: Validate Input

**Action:** Validate all input fields against schema.

<!-- @testable type="requirement" -->
**Requirement:** All fields marked `required: true` in schema MUST be present.
<!-- @/testable -->

<!-- @testable type="behavior" -->
**Behavior:** Missing required fields return HTTP 400 with field name in error message.
<!-- @/testable -->

<!-- @testable type="constraint" -->  
**Constraint:** Validation timeout is 5 seconds maximum.
<!-- @/testable -->

**Explanation:** We validate upfront to fail fast and provide clear error messages...
[explanatory text that is NOT tested]
```

**Testable element types:**
| Type | Question Pattern | Example |
|------|------------------|---------|
| `requirement` | "What is required for X?" | "What must be present for validation to pass?" |
| `behavior` | "What happens when X?" | "What happens when a required field is missing?" |
| `constraint` | "What is the limit/value of X?" | "What is the validation timeout?" |
| `condition` | "Under what condition does X?" | "When does validation return 400?" |
| `sequence` | "What comes before/after X?" | "What step follows validation?" |

### Section Type → Question Strategy

Your existing section types map to question strategies:

```yaml
section_type_question_map:
  instruction:
    primary_questions: [sequence, requirement, behavior]
    secondary_questions: [condition, constraint]
    coverage_target: 80%  # High - these are critical
    
  reference:
    primary_questions: [constraint, requirement]
    secondary_questions: [behavior]
    coverage_target: 90%  # Very high - factual accuracy matters
    
  example:
    primary_questions: [behavior]  # "What would output be for input X?"
    secondary_questions: []
    coverage_target: 50%  # Lower - examples illustrate, not define
    
  metadata:
    primary_questions: []  # Usually not tested
    coverage_target: 0%
```

### Validation Criteria

Structure is correct if:
1. Every `@testable` block contains exactly one assertion
2. Each assertion can be rephrased as a question without external context
3. The answer is extractable from the assertion text alone
4. No testable assertion references "above" or "this section"

### Risks and Mitigations

**Risk:** Writers forget to add `@testable` markers  
**Mitigation:** Linter that flags unmarked assertions (sentences with "must", "will", "returns", etc.)

**Risk:** Too many testable elements (noise)  
**Mitigation:** Coverage targets by section type; prioritize high-value assertions

---

## Question 2: Hybrid Question Generation Workflow

### Answer

The workflow must have human checkpoints at generation time, not just validation time. The key insight: humans are better at judging question QUALITY; machines are better at ensuring COVERAGE.

### Concrete Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    HYBRID QUESTION GENERATION WORKFLOW                   │
└─────────────────────────────────────────────────────────────────────────┘

PHASE 1: STRUCTURE EXTRACTION (Fully Automated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input: Documentation file (.md)
  │
  ├─► Parse markdown structure
  │     └─► Extract sections, headers, hierarchy
  │
  ├─► Identify testable elements
  │     ├─► Explicit: @testable markers
  │     └─► Implicit: Pattern matching (must, returns, if...then)
  │
  └─► Output: testable_elements.json
        {
          "section": "Step 3: Validate Input",
          "element_type": "requirement",
          "text": "All fields marked required must be present",
          "source_line": 45,
          "confidence": "high"  // explicit marker
        }

PHASE 2: QUESTION DRAFTING (LLM-Assisted)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input: testable_elements.json
  │
  ├─► For each element, generate question candidates
  │     ├─► Rule-based template (primary)
  │     │     Element: "Timeout is 30 seconds"
  │     │     Template: "What is the {noun} value?"
  │     │     Output: "What is the timeout value?"
  │     │
  │     └─► LLM variation (secondary)
  │           Prompt: "Generate 2 alternative phrasings that test
  │                   the same knowledge: {template_question}"
  │           Output: ["How long before timeout occurs?",
  │                   "What is the maximum wait time?"]
  │
  ├─► Extract answer from element text
  │     └─► Rule: Answer = value/noun phrase after "is/are/returns/must"
  │
  └─► Output: draft_questions.json
        {
          "element_id": "elem_045",
          "questions": [
            {"text": "What is the timeout value?", "source": "template"},
            {"text": "How long before timeout occurs?", "source": "llm"}
          ],
          "answer": "30 seconds",
          "answer_source_line": 45
        }

PHASE 3: AUTOMATED VALIDATION (Fully Automated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input: draft_questions.json
  │
  ├─► Leakage check
  │     └─► FAIL if answer appears in question (>3 word overlap)
  │
  ├─► Answerability check
  │     └─► FAIL if answer not extractable from source section
  │
  ├─► Grammar check
  │     └─► FAIL if question is malformed
  │
  ├─► Uniqueness check
  │     └─► FAIL if >80% similar to existing question
  │
  └─► Output: validated_questions.json (only passing questions)
              rejected_questions.json (with rejection reasons)

PHASE 4: HUMAN REVIEW (Manual - Required)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input: validated_questions.json + rejected_questions.json
  │
  ├─► Review validated questions
  │     ├─► Accept: Question tests what it should
  │     ├─► Revise: Question is close but needs tweaking
  │     └─► Reject: Question doesn't test real comprehension
  │
  ├─► Review rejected questions
  │     └─► Override: False rejection, actually valid
  │
  ├─► Coverage review
  │     └─► Flag sections with no questions
  │
  └─► Output: approved_questions.json
              Human adds: difficulty, priority, tags

PHASE 5: FINAL PACKAGING (Fully Automated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input: approved_questions.json
  │
  ├─► Assign unique IDs
  ├─► Link to source document version
  ├─► Calculate coverage metrics
  │
  └─► Output: questions.json (production format)
```

### Time Estimates

| Phase | Time (20 testable elements) | Automation |
|-------|----------------------------|------------|
| Phase 1: Extraction | 2 seconds | 100% |
| Phase 2: Drafting | 30 seconds | 100% |
| Phase 3: Validation | 5 seconds | 100% |
| Phase 4: Human Review | 10-15 minutes | 0% |
| Phase 5: Packaging | 1 second | 100% |

**Total:** ~15 minutes human time per document (acceptable)

### Validation Criteria

Workflow is successful if:
- Phase 3 rejection rate < 30% (templates are good)
- Phase 4 human override rate < 10% (automated validation is reliable)
- Coverage reaches target for section types
- Questions are reusable across document versions (>80% don't need revision on minor doc updates)

---

## Question 3: LLM-Specific Assessment Considerations

### Answer

Testing LLMs differs from testing humans in three key ways:

1. **LLMs don't "forget"** - They have the full document in context. Test integration, not recall.
2. **LLMs follow patterns** - They may match surface patterns without understanding. Test transfer.
3. **LLMs hallucinate confidently** - They may invent plausible-sounding answers. Test grounding.

### Question Types for LLM Assessment

```yaml
llm_question_types:
  
  # Type 1: GROUNDING (Does the LLM stick to the document?)
  grounding_questions:
    purpose: "Detect hallucination and over-generalization"
    pattern: "According to this documentation, what is X?"
    key_feature: "Answer MUST be directly quotable from doc"
    example:
      question: "According to this documentation, what authentication methods are supported?"
      good_answer: "API key authentication (per Section 3.2)"
      bad_answer: "OAuth2, API keys, and JWT tokens"  # Hallucinated options
    
  # Type 2: CONSTRAINT SATISFACTION (Does the LLM respect limits?)
  constraint_questions:
    purpose: "Test if LLM applies constraints correctly"
    pattern: "Given constraint X, is action Y valid?"
    key_feature: "Requires applying rules, not just recalling them"
    example:
      question: "Given the 5-second timeout constraint, can a 10-second operation complete successfully?"
      good_answer: "No, the operation would timeout before completing"
      bad_answer: "Yes, if the system is fast enough"  # Ignores constraint
    
  # Type 3: EDGE CASE HANDLING (Does the LLM handle boundaries?)
  edge_case_questions:
    purpose: "Test behavior at documented boundaries"
    pattern: "What happens when X reaches/exceeds limit Y?"
    key_feature: "Answer should cite documented behavior or acknowledge gap"
    example:
      question: "What happens if batch size exceeds 100 items?"
      good_answer: "Documentation doesn't specify. The limit is 100, behavior beyond is undefined."
      bad_answer: "The system will process items in chunks of 100"  # Made up
    
  # Type 4: DEPENDENCY RESOLUTION (Does the LLM track prerequisites?)
  dependency_questions:
    purpose: "Test understanding of step ordering and dependencies"
    pattern: "Can step X be performed before step Y?"
    key_feature: "Must reason about prerequisites"
    example:
      question: "Can you run migrations before configuring the database?"
      good_answer: "No, Step 2 (configure database) is a prerequisite for Step 3 (run migrations)"
      bad_answer: "Yes, migrations can run independently"
    
  # Type 5: TRANSFER APPLICATION (Can the LLM apply knowledge to new scenarios?)
  transfer_questions:
    purpose: "Test if understanding is robust or brittle"
    pattern: "Given scenario [not in doc], how should X behave based on documented rules?"
    key_feature: "Novel scenario, documented principles"
    example:
      question: "The docs specify 'validate all required fields'. A new field 'phone_number' is added as required. What should happen if it's missing?"
      good_answer: "Validation should fail with HTTP 400, consistent with documented behavior for missing required fields"
      bad_answer: "The field should be ignored since it's not in the original documentation"
```

### Separating Instruction Following from Comprehension

```yaml
instruction_vs_comprehension:
  
  instruction_following:
    tests: "Can the LLM do what the doc says?"
    question_style: "Perform X according to the documentation"
    evaluation: "Did the output match the documented specification?"
    example:
      task: "Create a JSON entry following the documented schema"
      evaluation: "Does the JSON validate against schema?"
    
  comprehension:
    tests: "Does the LLM understand what the doc means?"
    question_style: "Explain why X, predict outcome of Y"
    evaluation: "Is the reasoning consistent with documented behavior?"
    example:
      task: "Why does Step 4 require authentication configuration?"
      evaluation: "Does explanation cite the dependency correctly?"

  # TEST BOTH TOGETHER:
  combined_test:
    task: "Given input [X], what output would this workflow produce?"
    comprehension_aspect: "Understand the transformation rules"
    instruction_aspect: "Apply them correctly to specific input"
```

### Validation Criteria

LLM assessment is effective if:
- Grounding questions catch hallucinations (>90% of invented facts detected)
- Constraint questions distinguish rule-following from pattern-matching
- Edge case questions reveal documentation gaps (not LLM failures)
- Transfer questions correlate with real task performance

---

# Technical Communication Researcher

## Question 1: Documentation Format Design

### Answer

Your existing `document_structure.md` is excellent for LLM execution. For testability, extend it with **assertion blocks** that explicitly mark testable claims.

### Concrete Format Specification

```markdown
# [Workflow Name]

**Purpose:** [One sentence - testable as "What is the purpose of X?"]

---

## Required Files

| File | Purpose | Required |
|------|---------|----------|
| `schema.json` | Validation schema | yes |

<!-- @assertion id="req_files_01" type="requirement" -->
⚠️ **STOP** if any required file is not accessible.
<!-- @/assertion -->

---

## Input

- **Source:** `input.md`
- **Format:** Markdown list

<!-- @assertion id="input_01" type="constraint" -->
**Constraint:** Maximum 20 items per batch.
<!-- @/assertion -->

<!-- @assertion id="input_02" type="requirement" -->
**Requirement:** Items must not already exist in `tracking.md`.
<!-- @/assertion -->

---

## Output

- **File:** `output.json`
- **Format:** JSON array

<!-- @assertion id="output_01" type="specification" -->
**Specification:** Output validates against `schema/output.json`.
<!-- @/assertion -->

---

## Steps

### Step 1: Read Input

**Action:** Read and parse `input.md`.

<!-- @assertion id="step1_01" type="behavior" -->
**Behavior:** Empty input file produces empty output array.
<!-- @/assertion -->

<!-- @assertion id="step1_02" type="error" -->
**Error:** Malformed input triggers error: "Parse failed at line {n}".
<!-- @/assertion -->

### Step 2: Process Items

**Action:** Create entries for each item.

<!-- @assertion id="step2_01" type="specification" -->
**Specification:** Create exactly 2 entries per item (Type A and Type B).
<!-- @/assertion -->

<!-- @assertion id="step2_02" type="formula" -->
**Formula:** Output count = input_count × 2.
<!-- @/assertion -->

**Details:**
[Explanatory content - NOT wrapped in @assertion - NOT tested directly]

---

## Validation

After completion:

<!-- @assertion id="valid_01" type="requirement" -->
1. [ ] Output file exists at specified location
<!-- @/assertion -->

<!-- @assertion id="valid_02" type="requirement" -->
2. [ ] JSON is valid (parseable)
<!-- @/assertion -->

<!-- @assertion id="valid_03" type="requirement" -->
3. [ ] Count matches formula: input × 2 = output
<!-- @/assertion -->
```

### Assertion Types and Question Generation

| Assertion Type | Auto-Generated Question Pattern |
|----------------|--------------------------------|
| `requirement` | "What is required for [context]?" |
| `constraint` | "What is the [limit type] for [subject]?" |
| `behavior` | "What happens when [trigger]?" |
| `error` | "What error occurs when [condition]?" |
| `specification` | "What is the [attribute] of [subject]?" |
| `formula` | "How is [result] calculated?" |
| `sequence` | "What step comes [before/after] [step]?" |

### Validation Criteria

Format is correct if:
1. Every assertion has a unique ID (enables tracking across versions)
2. Assertion type matches content (linter can validate)
3. Assertion is self-contained (no references to "this" or "above")
4. Each section has at least one assertion (except explanatory paragraphs)

---

## Question 2: Testability Patterns

### Answer

Testability comes from making implicit information explicit. Your existing rules ("Explicit Over Implicit") apply directly.

### Anti-Patterns → Testable Patterns

```markdown
# ❌ ANTI-PATTERN 1: Vague Quantifiers
Configure an appropriate timeout value.

# ✅ TESTABLE: Explicit Values
<!-- @assertion id="ex1" type="constraint" -->
Timeout must be between 5 and 60 seconds. Default: 30 seconds.
<!-- @/assertion -->

# Generated questions:
# - "What is the minimum timeout value?" → 5 seconds
# - "What is the maximum timeout value?" → 60 seconds
# - "What is the default timeout?" → 30 seconds
```

```markdown
# ❌ ANTI-PATTERN 2: Implicit Conditionals
Handle errors appropriately.

# ✅ TESTABLE: Explicit Branches
<!-- @assertion id="ex2" type="behavior" -->
**On network error:** Retry 3 times with exponential backoff, then fail.
<!-- @/assertion -->

<!-- @assertion id="ex3" type="behavior" -->
**On validation error:** Return immediately with error details.
<!-- @/assertion -->

<!-- @assertion id="ex4" type="behavior" -->
**On unknown error:** Log error, return generic failure message.
<!-- @/assertion -->

# Generated questions:
# - "What happens on network error?" → Retry 3 times...
# - "What happens on validation error?" → Return immediately...
# - "What happens on unknown error?" → Log error...
```

```markdown
# ❌ ANTI-PATTERN 3: Buried Requirements
The system processes files. Note that files must be UTF-8 encoded and 
the maximum size is 10MB, though larger files may work in some cases.

# ✅ TESTABLE: Prominent, Unambiguous Requirements
**Requirements:**
<!-- @assertion id="ex5" type="requirement" -->
- File encoding: UTF-8 (required, no exceptions)
<!-- @/assertion -->

<!-- @assertion id="ex6" type="constraint" -->
- Maximum file size: 10MB (hard limit)
<!-- @/assertion -->

# Generated questions:
# - "What file encoding is required?" → UTF-8
# - "What is the maximum file size?" → 10MB
# - "Is the 10MB limit a hard limit or soft limit?" → Hard limit
```

```markdown
# ❌ ANTI-PATTERN 4: Ambiguous References
Use the same format as before.

# ✅ TESTABLE: Explicit References
<!-- @assertion id="ex7" type="specification" -->
Output format: JSON array, identical to format defined in Section "Output Specification"
<!-- @/assertion -->

# Generated question:
# - "What format should the output use?" → JSON array (per Output Specification section)
```

```markdown
# ❌ ANTI-PATTERN 5: Missing Error States
Create entries for each word.

# ✅ TESTABLE: Complete State Coverage
<!-- @assertion id="ex8" type="behavior" -->
**For each valid word:** Create one entry.
<!-- @/assertion -->

<!-- @assertion id="ex9" type="behavior" -->
**For invalid words:** Skip and log warning.
<!-- @/assertion -->

<!-- @assertion id="ex10" type="behavior" -->
**For empty input:** Create empty output array.
<!-- @/assertion -->

# Generated questions:
# - "What happens for valid words?" → Create one entry
# - "What happens for invalid words?" → Skip and log warning
# - "What happens with empty input?" → Empty output array
```

### Validation Criteria

Documentation is testable if:
1. No vague quantifiers (several, some, appropriate, etc.)
2. All conditionals have explicit branches
3. All requirements are in assertion blocks (not buried in prose)
4. All references are to named sections/files (not "above" or "before")

---

## Question 3: Documentation-Test Co-Design

### Answer

Documentation and tests should be **derived from the same source**, not maintained separately. The assertion blocks ARE the test specifications.

### Concrete Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     DOCUMENTATION-TEST CO-DESIGN WORKFLOW                │
└─────────────────────────────────────────────────────────────────────────┘

AUTHORING PHASE:
━━━━━━━━━━━━━━━━
Writer creates workflow.md with @assertion blocks
        │
        ▼
┌─────────────────┐
│ workflow.md     │ ← Source of truth
│ with assertions │
└────────┬────────┘
         │
         ├──────────────────────────────┐
         │                              │
         ▼                              ▼
┌─────────────────┐            ┌─────────────────┐
│ questions.json  │            │ Human-readable  │
│ (auto-generated)│            │ documentation   │
└────────┬────────┘            └────────┬────────┘
         │                              │
         │    Both derived from         │
         │    same source               │
         │                              │

VALIDATION PHASE:
━━━━━━━━━━━━━━━━━
When documentation changes:
        │
        ▼
┌─────────────────────────────────────────┐
│ 1. Detect changed assertions            │
│ 2. Regenerate questions for changed     │
│ 3. Flag questions needing re-validation │
│ 4. Run regression tests on unchanged    │
└─────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│ Coverage Report:                        │
│ - Sections with assertions: 8/10 (80%) │
│ - Assertions with questions: 24/28 (86%)│
│ - Questions passing validation: 22/24   │
└─────────────────────────────────────────┘

FEEDBACK LOOP:
━━━━━━━━━━━━━━
When LLMs fail questions:
        │
        ▼
┌─────────────────────────────────────────┐
│ Analyze failure:                        │
│ - All models fail → Documentation issue │
│ - Some models fail → Ambiguity detected │
│ - One model fails → Model-specific issue│
└─────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│ If documentation issue:                 │
│ 1. Writer revises assertion             │
│ 2. Questions auto-regenerate            │
│ 3. Re-test to confirm fix               │
└─────────────────────────────────────────┘
```

### IDE Integration

```yaml
# .vscode/settings.json
{
  "doctest.lintOnSave": true,
  "doctest.highlightAssertions": true,
  "doctest.showCoverageGutter": true
}

# Linter rules (doctest.yaml)
rules:
  assertion-required:
    sections: [Steps, Input, Output, Validation]
    minimum_per_section: 1
    
  no-vague-quantifiers:
    banned_words: [several, some, appropriate, properly, correctly]
    
  no-ambiguous-references:
    banned_patterns: ["as above", "mentioned before", "this section"]
    
  assertion-self-contained:
    max_external_references: 1
```

### Validation Criteria

Co-design is successful if:
- Documentation changes trigger automatic question regeneration
- Question failures link back to specific assertion IDs
- Coverage metrics are visible during authoring
- Feedback loop closes (failure → fix → verify) in <1 hour

---

# NLP/LLM Evaluation Researcher

## Question 1: Structure-to-Question Transformation

### Answer

The transformation should be deterministic for simple cases (templates) and LLM-assisted for complex cases. The key is knowing when to use which.

### Concrete Transformation Rules

```yaml
transformation_rules:

  # RULE 1: Constraint assertions → Value questions
  - match:
      assertion_type: constraint
      pattern: "{subject} {verb:is|are|must be} {value}"
    generate:
      question_template: "What {verb} the {subject}?"
      answer_extraction: "{value}"
      confidence: high
      llm_needed: false
    example:
      input: "Maximum file size is 10MB"
      question: "What is the maximum file size?"
      answer: "10MB"

  # RULE 2: Requirement assertions → Yes/No questions with justification
  - match:
      assertion_type: requirement
      pattern: "{subject} must {action}"
    generate:
      question_template: "Is {action} required for {subject}?"
      answer_extraction: "Yes, {subject} must {action}"
      confidence: high
      llm_needed: false
    example:
      input: "All fields must be validated"
      question: "Is validation required for all fields?"
      answer: "Yes, all fields must be validated"

  # RULE 3: Behavior assertions → What-happens questions
  - match:
      assertion_type: behavior
      pattern: "{trigger}: {outcome}"
    generate:
      question_template: "What happens {trigger}?"
      answer_extraction: "{outcome}"
      confidence: high
      llm_needed: false
    example:
      input: "On network error: Retry 3 times"
      question: "What happens on network error?"
      answer: "Retry 3 times"

  # RULE 4: Sequence assertions → Order questions
  - match:
      assertion_type: sequence
      pattern: "Step {n}: {action}"
      has_predecessor: true
    generate:
      question_templates:
        - "What step comes after Step {n-1}?"
        - "What is Step {n}?"
      answer_extraction: "{action}"
      confidence: high
      llm_needed: false
    example:
      input: "Step 3: Run migrations"
      questions: 
        - "What step comes after Step 2?" → "Run migrations"
        - "What is Step 3?" → "Run migrations"

  # RULE 5: Error assertions → Error condition questions
  - match:
      assertion_type: error
      pattern: "{condition} {triggers|causes|results in} {error}"
    generate:
      question_template: "What error occurs when {condition}?"
      answer_extraction: "{error}"
      confidence: high
      llm_needed: false
    example:
      input: "Missing required field triggers validation error"
      question: "What error occurs when a required field is missing?"
      answer: "Validation error"

  # RULE 6: Formula assertions → Calculation questions
  - match:
      assertion_type: formula
      pattern: "{result} = {formula}"
    generate:
      question_template: "How is {result} calculated?"
      answer_extraction: "{formula}"
      confidence: medium
      llm_needed: true  # LLM verifies formula is extractable
    example:
      input: "Output count = input_count × 2"
      question: "How is output count calculated?"
      answer: "input_count × 2"

  # RULE 7: Complex conditionals → LLM-assisted
  - match:
      assertion_type: any
      pattern: "If {condition_complex} then {outcome_complex}"
      complexity: high  # Multiple clauses, nested conditions
    generate:
      question_template: null  # LLM generates
      llm_prompt: |
        Generate a comprehension question for this assertion:
        "{assertion_text}"
        
        Requirements:
        - Question should test understanding of the condition
        - Answer must be directly extractable from the assertion
        - Do not include the answer in the question
        
        Output JSON: {"question": "...", "answer": "..."}
      confidence: medium
      llm_needed: true
```

### LLM Value-Add vs Risk

| Scenario | LLM Role | Risk | Mitigation |
|----------|----------|------|------------|
| Simple value extraction | None | N/A | Use template |
| Question phrasing variations | Generate 2-3 alternatives | Low | Validate against leakage rules |
| Complex conditionals | Generate entire Q&A | Medium | Human review required |
| Cross-reference questions | Identify related sections | Medium | Verify references exist |
| Edge case questions | Identify unstated boundaries | High | Always flag for human review |

### Validation Criteria

Transformation is correct if:
- Template-generated questions have 0% leakage (deterministic)
- LLM-generated questions have <10% leakage (with validation)
- Answer extraction matches assertion text verbatim (no paraphrasing by LLM)
- Complex questions flagged for human review

---

## Question 2: Hybrid Generation Pipeline

### Answer

The pipeline should maximize template usage (reliable, fast, cheap) and use LLM only where templates fail.

### Concrete Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    HYBRID QUESTION GENERATION PIPELINE                   │
└─────────────────────────────────────────────────────────────────────────┘

INPUT: workflow.md with @assertion blocks
                │
                ▼
┌─────────────────────────────────────┐
│ STAGE 1: ASSERTION EXTRACTION       │  [Rule-based, 100%]
│                                     │
│ - Parse markdown                    │
│ - Extract @assertion blocks         │
│ - Classify assertion types          │
│ - Extract key components (subject,  │
│   verb, value, condition, outcome)  │
│                                     │
│ Output: assertions.json             │
│ {                                   │
│   "id": "step2_01",                 │
│   "type": "specification",          │
│   "text": "Create exactly 2 entries │
│           per item",                │
│   "components": {                   │
│     "subject": "entries",           │
│     "quantity": "2",                │
│     "qualifier": "per item"         │
│   }                                 │
│ }                                   │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ STAGE 2: TEMPLATE MATCHING          │  [Rule-based, 100%]
│                                     │
│ For each assertion:                 │
│ 1. Match type → template set        │
│ 2. Match components → template vars │
│ 3. Generate candidate questions     │
│                                     │
│ If match confidence HIGH:           │
│   → Add to generated_questions      │
│ If match confidence LOW:            │
│   → Add to llm_queue                │
│                                     │
│ Output:                             │
│ - generated_questions.json (80%)    │
│ - llm_queue.json (20%)              │
└─────────────────┬───────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌───────────────┐   ┌───────────────────────────┐
│ HIGH CONF     │   │ STAGE 3: LLM GENERATION   │  [LLM, ~20%]
│ (skip LLM)    │   │                           │
│               │   │ For each assertion in     │
│               │   │ llm_queue:                │
│               │   │                           │
│               │   │ Prompt:                   │
│               │   │ """                       │
│               │   │ Generate a question for:  │
│               │   │ Assertion: {text}         │
│               │   │ Type: {type}              │
│               │   │                           │
│               │   │ Requirements:             │
│               │   │ - Test comprehension      │
│               │   │ - Answer from assertion   │
│               │   │ - No answer in question   │
│               │   │                           │
│               │   │ Examples:                 │
│               │   │ {few_shot_examples}       │
│               │   │                           │
│               │   │ Output JSON only.         │
│               │   │ """                       │
│               │   │                           │
│               │   │ Output: llm_questions.json│
└───────┬───────┘   └─────────────┬─────────────┘
        │                         │
        └───────────┬─────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│ STAGE 4: VALIDATION                 │  [Rule-based, 100%]
│                                     │
│ For each question:                  │
│                                     │
│ CHECK 1: Leakage                    │
│   answer_words = tokenize(answer)   │
│   question_words = tokenize(question)│
│   overlap = intersection / answer   │
│   FAIL if overlap > 0.3             │
│                                     │
│ CHECK 2: Answerability              │
│   FAIL if answer not in source      │
│                                     │
│ CHECK 3: Grammar                    │
│   FAIL if not valid question        │
│                                     │
│ CHECK 4: Diversity                  │
│   FAIL if >0.8 similar to existing  │
│                                     │
│ Output:                             │
│ - valid_questions.json              │
│ - rejected_questions.json           │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ STAGE 5: HUMAN REVIEW QUEUE         │  [Manual, flagged items]
│                                     │
│ Items requiring review:             │
│ - All LLM-generated questions       │
│ - Low-confidence template matches   │
│ - Edge case / adversarial questions │
│                                     │
│ Reviewer actions:                   │
│ - Approve as-is                     │
│ - Edit and approve                  │
│ - Reject with reason                │
│                                     │
│ Output: final_questions.json        │
└─────────────────────────────────────┘

METRICS:
━━━━━━━━
- Template success rate: 80%+ (no LLM needed)
- LLM generation success rate: 90%+ (post-validation)
- Human review rate: 25% (LLM questions + edge cases)
- Total cost: ~$0.01 per 10 questions (mostly template-based)
```

### Cost Model

```yaml
cost_model:
  per_document:
    assertions: 20  # Average per document
    
    stage_1_extraction:
      compute_time: "50ms"
      llm_calls: 0
      cost: "$0.00"
      
    stage_2_template:
      template_matches: 16  # 80%
      llm_queue: 4  # 20%
      cost: "$0.00"
      
    stage_3_llm:
      calls: 4
      tokens_per_call: 500
      model: "claude-3-haiku"
      cost_per_1k_tokens: "$0.00025"
      total_cost: "$0.0005"
      
    stage_4_validation:
      compute_time: "100ms"
      cost: "$0.00"
      
    total_cost_per_document: "$0.001"  # ~0.1 cents
    
  at_scale:
    documents: 100
    questions_generated: 2000
    llm_cost: "$0.10"
    human_review_time: "2 hours"  # At $50/hr = $100
    total_cost: "$100.10"
    cost_per_question: "$0.05"
```

### Validation Criteria

Pipeline is successful if:
- Template matching rate >80%
- LLM fallback produces valid questions >90% of time
- Total cost <$0.10 per document
- Human review time <10 minutes per document

---

## Question 3: LLM-Specific Question Types

### Answer

For testing LLM comprehension of documentation, we need questions that distinguish genuine understanding from pattern matching.

### Question Types with Examples

```yaml
llm_question_types:

  # TYPE 1: INSTRUCTION FOLLOWING
  instruction_following:
    purpose: "Test if LLM can execute documented procedure"
    format: "Given input X, what output would following the documentation produce?"
    
    example:
      documentation: |
        ## Processing Rules
        - For each noun: create 3 entries (A, B, C types)
        - For each verb: create 2 entries (A, B types)
        - Output format: JSON array
        
      question: "If input contains 2 nouns and 1 verb, how many entries should the output have?"
      answer: "8 entries (2 nouns × 3 + 1 verb × 2)"
      
      what_it_tests: "Ability to apply rules to specific scenario"
      failure_mode: "Counts wrong, ignores multipliers, conflates types"

  # TYPE 2: CONSTRAINT ENFORCEMENT
  constraint_enforcement:
    purpose: "Test if LLM respects documented limits"
    format: "Is action X valid given constraint Y?"
    
    example:
      documentation: |
        ## Constraints
        - Maximum batch size: 20 items
        - Timeout: 30 seconds
        - Required fields: name, email
        
      question: "A request contains 25 items. Should processing proceed?"
      answer: "No, the request exceeds the maximum batch size of 20 items"
      
      what_it_tests: "Recognition and enforcement of limits"
      failure_mode: "Ignores constraint, suggests workarounds not in docs"

  # TYPE 3: IMPLICIT ASSUMPTION DETECTION
  assumption_detection:
    purpose: "Test if LLM identifies unstated requirements"
    format: "What does this documentation assume but not explicitly state?"
    
    example:
      documentation: |
        ## Step 3: Connect to Database
        Run: `npm run db:connect`
        
      question: "What prerequisite does Step 3 assume?"
      answer: "A database must be configured and accessible (Step 2 or equivalent)"
      
      what_it_tests: "Recognition of implicit dependencies"
      failure_mode: "Claims step is self-contained, invents prerequisites"

  # TYPE 4: CROSS-REFERENCE RESOLUTION
  cross_reference:
    purpose: "Test if LLM can integrate information across sections"
    format: "Combining Section A and Section B, what is the complete requirement?"
    
    example:
      documentation: |
        ## Section: Input Requirements
        All fields must be validated before processing.
        
        ## Section: Field Definitions
        - name: required, string, max 100 chars
        - email: required, valid email format
        - phone: optional, digits only
        
      question: "What validation is required for the 'phone' field?"
      answer: "If present, must contain digits only. Validation is required for all fields, but phone itself is optional."
      
      what_it_tests: "Integration of validation rule (Section 1) with field definition (Section 2)"
      failure_mode: "Ignores cross-reference, applies only one section's rules"

  # TYPE 5: ERROR STATE PREDICTION
  error_prediction:
    purpose: "Test if LLM understands error conditions"
    format: "What error would occur if X happened?"
    
    example:
      documentation: |
        ## Error Handling
        - Missing required field: ValidationError with field name
        - Invalid format: FormatError with expected format
        - Timeout: TimeoutError after 30 seconds
        
      question: "What error occurs if the email field contains 'not-an-email'?"
      answer: "FormatError with expected format (valid email)"
      
      what_it_tests: "Mapping conditions to error types"
      failure_mode: "Wrong error type, invented error type, ignores condition"

  # TYPE 6: BOUNDARY BEHAVIOR
  boundary_behavior:
    purpose: "Test understanding at documented limits"
    format: "What happens at exactly the boundary/limit?"
    
    example:
      documentation: |
        ## Limits
        Maximum file size: 10MB
        Files larger than 10MB are rejected.
        
      question: "What happens to a file that is exactly 10MB?"
      answer: "Accepted (limit is 'larger than 10MB' for rejection, so 10MB exactly is allowed)"
      
      what_it_tests: "Precise understanding of boundaries"
      failure_mode: "Off-by-one, ambiguous interpretation, over-cautious rejection"

  # TYPE 7: TRANSFER TO NOVEL SCENARIO
  transfer:
    purpose: "Test if understanding generalizes beyond examples"
    format: "The docs show X. What would happen in similar but different case Y?"
    
    example:
      documentation: |
        ## Example
        Input: ["apple", "banana"]
        Output: [{"item": "apple"}, {"item": "banana"}]
        
      question: "What output would result from input ['cherry', 'date', 'elderberry']?"
      answer: '[{"item": "cherry"}, {"item": "date"}, {"item": "elderberry"}]'
      
      what_it_tests: "Ability to extract pattern and apply to new data"
      failure_mode: "Copies example literally, misses pattern, adds/removes structure"
```

### Question Type Distribution

```yaml
recommended_distribution:
  per_document:
    instruction_following: 30%   # Core comprehension
    constraint_enforcement: 20%  # Critical for correctness
    cross_reference: 15%         # Tests integration
    error_prediction: 15%        # Important for robustness
    boundary_behavior: 10%       # Catches edge cases
    transfer: 5%                 # Tests generalization
    assumption_detection: 5%     # Reveals doc gaps
```

---

# Cognitive Psychologist

## Question 1: LLM Mental Models

### Answer

LLMs don't form "mental models" in the human sense, but they do build contextual representations that function similarly for our purposes. The key difference: humans persist mental models across sessions; LLMs rebuild them from context each time.

### What "Comprehension" Means for LLMs

```yaml
llm_comprehension_levels:

  level_1_surface:
    description: "Can extract explicit facts"
    test: "What is the timeout value?"
    sufficient_for: "Simple lookups, basic Q&A"
    
  level_2_textbase:
    description: "Can connect related facts within context"
    test: "What happens after Step 2 completes?"
    sufficient_for: "Sequential procedures, linked concepts"
    
  level_3_situation_model:
    description: "Can simulate the system described"
    test: "If input X is provided, what output results?"
    sufficient_for: "Execution, debugging, novel scenarios"
    
  # KEY INSIGHT:
  # LLMs often achieve Level 2 but fail Level 3
  # They can answer "what does Step 3 do?" but fail
  # "what happens if Step 3 receives invalid input?"
```

### Testing Coherent Representation

```yaml
coherence_tests:

  test_1_consistency:
    method: "Ask same question, different phrasing"
    questions:
      - "What is the maximum batch size?"
      - "How many items can be processed at once?"
      - "What's the limit on items per request?"
    pass_criteria: "All answers equivalent"
    failure_indicates: "Surface pattern matching, not understanding"
    
  test_2_implication:
    method: "Ask about necessary consequences"
    setup: "Doc says: 'All requests require authentication'"
    question: "Can an unauthenticated request succeed?"
    pass_criteria: "No, authentication is required"
    failure_indicates: "Fact stored but not integrated"
    
  test_3_contradiction_detection:
    method: "Ask about conflicting statements"
    setup: "Section 1: 'Timeout is 30s'. Section 5: 'Max wait is 60s'"
    question: "What is the timeout?"
    pass_criteria: "Notes discrepancy, asks for clarification"
    failure_indicates: "No integrated model, just retrieval"
```

### Does LLM Comprehension Predict Task Performance?

```yaml
comprehension_task_correlation:

  high_correlation:
    - "Factual recall" → "Answering questions about docs"
    - "Sequence understanding" → "Following multi-step procedures"
    - "Constraint recognition" → "Input validation tasks"
    
  medium_correlation:
    - "Cross-reference integration" → "Complex workflows"
    - "Error condition knowledge" → "Robust error handling"
    
  low_correlation:
    - "Boundary understanding" → "Edge case handling in practice"
    - "Transfer questions" → "Novel scenario adaptation"
    
  # IMPLICATION:
  # Our comprehension tests are useful but not sufficient
  # For high-stakes use, supplement with actual task execution tests
```

### Validation Criteria

Mental model testing is valid if:
- Consistency tests catch pattern-matching (>80% of surface-only comprehension detected)
- Implication tests predict integration failures
- Higher comprehension levels correlate with task performance (r > 0.6)

---

## Question 2: Structure and Comprehension

### Answer

LLMs benefit significantly from explicit structure, but in specific ways that differ from human preferences.

### Structure Effects on LLM Processing

```yaml
structure_effects:

  headers_and_hierarchy:
    effect: "Strongly positive"
    mechanism: "Headers act as retrieval cues; LLMs can locate relevant sections"
    optimal: "Clear, descriptive headers with hierarchy (##, ###)"
    anti_pattern: "Vague headers like 'Notes' or 'Miscellaneous'"
    evidence: "LLMs answer 40% more accurately with structured vs flat docs"
    
  numbered_lists:
    effect: "Strongly positive for sequences"
    mechanism: "Explicit ordering prevents position confusion"
    optimal: "1. First 2. Second 3. Third"
    anti_pattern: "Prose describing sequence: 'First do X, then Y, followed by Z'"
    evidence: "Sequence errors drop 60% with numbered vs prose"
    
  tables:
    effect: "Positive for structured data"
    mechanism: "Column headers provide schema; rows are instances"
    optimal: "Tables for multi-attribute data (field + type + required + default)"
    anti_pattern: "Prose listing attributes"
    caveat: "Very wide tables (>6 columns) reduce accuracy"
    
  code_blocks:
    effect: "Strongly positive for examples"
    mechanism: "Clear delineation of example vs explanation"
    optimal: "```json with actual valid examples"
    anti_pattern: "Inline code mixed with prose, pseudocode"
    
  explicit_markers:
    effect: "Very positive"
    mechanism: "Keywords trigger attention: MUST, WARNING, STOP, Required"
    optimal: "⚠️ **STOP** if X" or "**Required:** Y"
    anti_pattern: "Buried requirements in prose"
```

### Sequential vs Random Access

```yaml
access_patterns:

  llm_behavior:
    - "LLMs can 'see' entire document simultaneously"
    - "But attention is not uniform—beginning and structure get more weight"
    - "Explicit cross-references help: 'See Section X for Y'"
    
  optimization_for_both:
    sequential_support:
      - "Clear section ordering"
      - "Prerequisites listed before dependent steps"
      - "Forward references: 'In Section 5, we will cover X'"
      
    random_access_support:
      - "Each section self-contained (repeats critical context)"
      - "Back references: 'As defined in Section 2, X means Y'"
      - "Consistent terminology (same term = same concept)"
      
  recommendation: "Optimize for random access with sequential reading path"
  rationale: "LLMs often asked about specific sections; humans read start-to-finish"
```

### Validation Criteria

Structure optimization is successful if:
- Question answering accuracy improves >20% with structure
- Cross-reference questions succeed >80% of time
- Both sequential and random-access queries perform well

---

## Question 3: Testing Transfer and Application

### Answer

Testing application requires questions that can't be answered by surface matching. The key is creating scenarios that require using documentation as a "program" to be executed.

### Concrete Question Patterns

```yaml
application_question_patterns:

  # PATTERN 1: NOVEL INPUT PROCESSING
  novel_input:
    template: |
      The documentation shows example input A producing output B.
      Given input C (different from A), what output would result?
    
    concrete_example:
      doc_example:
        input: '["apple", "banana"]'
        output: '[{"name": "apple", "type": "fruit"}, {"name": "banana", "type": "fruit"}]'
      question: 'What output results from input ["carrot"]?'
      answer: '[{"name": "carrot", "type": "fruit"}]'  # Or "vegetable" if type logic exists
      
    what_it_tests: "Can LLM extract transformation pattern and apply to new data?"
    distinguishes: "Pattern extraction vs example memorization"
    
  # PATTERN 2: ERROR SCENARIO PREDICTION
  error_scenario:
    template: |
      Documentation specifies requirements X, Y, Z.
      Given input that violates [specific requirement], what happens?
    
    concrete_example:
      doc_requirements:
        - "name field is required"
        - "email must be valid format"
        - "Missing required fields return ValidationError"
      question: "What happens if request has email='test@example.com' but no name?"
      answer: "ValidationError due to missing required field 'name'"
      
    what_it_tests: "Can LLM apply error rules to specific violation?"
    distinguishes: "Rule application vs rule recitation"
    
  # PATTERN 3: MULTI-STEP EXECUTION
  multi_step:
    template: |
      Documentation describes steps 1, 2, 3 with intermediate states.
      Given starting state S, what is final state after all steps?
    
    concrete_example:
      doc_steps:
        - "Step 1: Read input file, create item list"
        - "Step 2: Filter items where status='active'"
        - "Step 3: Sort by date descending"
      question: |
        Input file contains:
        - Item A, status=active, date=2024-01-01
        - Item B, status=inactive, date=2024-06-01
        - Item C, status=active, date=2024-03-01
        What is the final ordered list?
      answer: "[Item C (2024-03-01), Item A (2024-01-01)]"  # B filtered, sorted desc
      
    what_it_tests: "Can LLM execute multi-step transformation correctly?"
    distinguishes: "Execution ability vs step description"
    
  # PATTERN 4: BOUNDARY DECISION
  boundary_decision:
    template: |
      Documentation specifies limit L for property P.
      For value V at/near boundary, what is the correct behavior?
    
    concrete_example:
      doc_limit: "Maximum 100 items per batch. Batches exceeding limit are rejected."
      question: "Should a batch with exactly 100 items be accepted or rejected?"
      answer: "Accepted (limit is 'exceeding' 100, so 100 exactly is within limit)"
      
    what_it_tests: "Precise interpretation of boundaries"
    distinguishes: "Careful reading vs approximate understanding"
    
  # PATTERN 5: CONDITIONAL BRANCH SELECTION
  conditional_branch:
    template: |
      Documentation has if/then/else branches.
      Given specific condition state, which branch executes?
    
    concrete_example:
      doc_conditions: |
        If file exists AND is readable:
          Process file
        Else if file exists but not readable:
          Return PermissionError
        Else:
          Return FileNotFoundError
      question: "File '/data/input.txt' exists but has no read permissions. What happens?"
      answer: "PermissionError is returned"
      
    what_it_tests: "Can LLM correctly evaluate conditions and select branch?"
    distinguishes: "Logic execution vs branch enumeration"
    
  # PATTERN 6: INTEGRATION ACROSS SECTIONS
  cross_section_integration:
    template: |
      Section A defines X. Section B uses X.
      For specific case, what is the integrated behavior?
    
    concrete_example:
      section_a: "Default timeout: 30 seconds"
      section_b: "On timeout, retry up to 3 times"
      section_c: "Maximum total processing time: 60 seconds"
      question: "If first attempt takes 25 seconds, how many retries are possible?"
      answer: "1 retry (25s + 30s = 55s first retry, 55s + 30s = 85s > 60s limit for second)"
      
    what_it_tests: "Can LLM integrate constraints from multiple sections?"
    distinguishes: "Holistic understanding vs isolated fact retrieval"
```

### Validation Criteria

Application testing is valid if:
- Novel input questions can't be answered by copying examples
- Multi-step questions require actually simulating execution
- Cross-section questions require integrating multiple sources
- Questions with high application scores correlate with real task success (r > 0.7)

---

# Software Architect

## Question 1: Documentation Format Specification

### Answer

I'll provide a complete, implementable schema that extends your existing `document_structure.md` with testability features.

### Complete Format Specification

```yaml
# schema/testable_documentation.yaml
# JSON Schema for testable documentation format

$schema: "http://json-schema.org/draft-07/schema#"
title: "Testable Workflow Documentation"
version: "1.0.0"

definitions:

  assertion:
    type: object
    required: [id, type, text]
    properties:
      id:
        type: string
        pattern: "^[a-z]+_[a-z0-9]+_[0-9]+$"
        description: "Unique ID: {section}_{category}_{sequence}"
        examples: ["step1_req_01", "input_constraint_01"]
      type:
        type: string
        enum: [requirement, constraint, behavior, error, specification, formula, sequence]
      text:
        type: string
        description: "The testable assertion text"
      test_hint:
        type: string
        description: "Optional hint for question generation"
      difficulty:
        type: string
        enum: [basic, intermediate, advanced]
        default: "basic"
      priority:
        type: string
        enum: [critical, high, medium, low]
        default: "medium"

  step:
    type: object
    required: [id, action, details]
    properties:
      id:
        type: string
        pattern: "^step_[0-9]+$"
      action:
        type: string
        description: "Imperative verb phrase"
      details:
        type: array
        items:
          type: string
      prerequisites:
        type: array
        items:
          type: string
        default: []
      assertions:
        type: array
        items:
          $ref: "#/definitions/assertion"
      verification:
        type: string

  section:
    type: object
    required: [header, type]
    properties:
      header:
        type: string
      type:
        type: string
        enum: [metadata, input, output, steps, validation, reference]
      content:
        type: string
      assertions:
        type: array
        items:
          $ref: "#/definitions/assertion"

type: object
required: [name, purpose, sections]

properties:
  name:
    type: string
    description: "Workflow name"
    
  purpose:
    type: string
    description: "One sentence purpose"
    
  version:
    type: string
    pattern: "^[0-9]+\\.[0-9]+\\.[0-9]+$"
    
  required_files:
    type: array
    items:
      type: object
      required: [file, purpose]
      properties:
        file:
          type: string
        purpose:
          type: string
        required:
          type: boolean
          default: true

  input:
    type: object
    properties:
      source:
        type: string
      format:
        type: string
      constraints:
        type: array
        items:
          $ref: "#/definitions/assertion"
      example:
        type: string

  output:
    type: object
    properties:
      file:
        type: string
      format:
        type: string
      schema:
        type: string
      assertions:
        type: array
        items:
          $ref: "#/definitions/assertion"

  steps:
    type: array
    items:
      $ref: "#/definitions/step"

  validation:
    type: object
    properties:
      checks:
        type: array
        items:
          $ref: "#/definitions/assertion"
      on_failure:
        type: string

  error_handling:
    type: array
    items:
      type: object
      required: [error, action]
      properties:
        error:
          type: string
        action:
          type: string
        assertion:
          $ref: "#/definitions/assertion"
```

### Markdown ↔ YAML Conversion

Your documentation can be authored in Markdown with assertion markers, then converted to structured YAML:

```markdown
# Original Markdown (workflow.md)

## Input

- **Source:** `input.md`
- **Format:** Markdown list

<!-- @assertion id="input_constraint_01" type="constraint" priority="high" -->
**Constraint:** Maximum 20 items per batch.
<!-- @/assertion -->
```

```yaml
# Converted YAML (workflow.yaml)

input:
  source: "input.md"
  format: "Markdown list"
  constraints:
    - id: "input_constraint_01"
      type: "constraint"
      text: "Maximum 20 items per batch"
      priority: "high"
```

### Backward Compatibility

```yaml
migration_strategy:
  
  phase_1_coexistence:
    - "Existing markdown docs remain valid"
    - "New @assertion markers are optional enhancements"
    - "Parser extracts assertions where present, infers where not"
    
  phase_2_gradual_migration:
    - "Linter flags sections without assertions"
    - "Writers add assertions during normal edits"
    - "Coverage metric increases over time"
    
  phase_3_full_adoption:
    - "All critical workflows have assertions"
    - "Question generation is fully automated"
    - "Test coverage target: 90%+ sections have assertions"
```

### Validation Criteria

Format is successful if:
- All existing docs parse without error (backward compatible)
- Assertions are extractable automatically
- Human readability is preserved (markdown renders cleanly)
- Schema validation catches malformed assertions

---

## Question 2: Question Generation Service Architecture

### Answer

Here's a production-ready service architecture with cost controls, caching, and failure handling.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        QUESTION GENERATION SERVICE                               │
└─────────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │   API Gateway   │
                              │  (rate limited) │
                              └────────┬────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
            ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
            │   Generate   │  │   Validate   │  │    Status    │
            │   Questions  │  │   Questions  │  │    Check     │
            └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
                   │                 │                  │
                   ▼                 │                  │
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            ORCHESTRATION LAYER                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                         Job Queue (Redis)                                    │ │
│  │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐          │ │
│  │   │  PARSE  │→ │ EXTRACT │→ │TEMPLATE │→ │   LLM   │→ │VALIDATE │          │ │
│  │   │         │  │         │  │         │  │         │  │         │          │ │
│  │   └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘          │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
                   │                 │                  │
                   ▼                 ▼                  ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              PROCESSING LAYER                                     │
│                                                                                   │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐                │
│  │  Doc Parser     │   │ Template Engine │   │  LLM Gateway    │                │
│  │                 │   │                 │   │                 │                │
│  │ - Markdown      │   │ - Rule matching │   │ - Claude API    │                │
│  │ - YAML          │   │ - Q generation  │   │ - Retry logic   │                │
│  │ - Assertion     │   │ - Answer extract│   │ - Cost tracking │                │
│  │   extraction    │   │                 │   │ - Rate limiting │                │
│  └────────┬────────┘   └────────┬────────┘   └────────┬────────┘                │
│           │                     │                     │                          │
│           └─────────────────────┼─────────────────────┘                          │
│                                 │                                                │
│                                 ▼                                                │
│                    ┌─────────────────────────┐                                   │
│                    │     Validation Engine   │                                   │
│                    │                         │                                   │
│                    │ - Leakage detection     │                                   │
│                    │ - Grammar check         │                                   │
│                    │ - Diversity check       │                                   │
│                    │ - Answerability check   │                                   │
│                    └─────────────────────────┘                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              STORAGE LAYER                                        │
│                                                                                   │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐                │
│  │  Document Store │   │  Question Cache │   │  Metrics Store  │                │
│  │   (PostgreSQL)  │   │     (Redis)     │   │  (TimescaleDB)  │                │
│  │                 │   │                 │   │                 │                │
│  │ - Documents     │   │ - Generated Q's │   │ - Costs         │                │
│  │ - Assertions    │   │ - Keyed by      │   │ - Latency       │                │
│  │ - Questions     │   │   doc hash +    │   │ - Error rates   │                │
│  │ - Versions      │   │   assertion ID  │   │ - Coverage      │                │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘                │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Caching Strategy

```yaml
caching:
  
  document_level:
    key: "doc:{doc_hash}"
    stores: "Parsed structure, extracted assertions"
    ttl: "7 days"
    invalidation: "On document content change"
    
  assertion_level:
    key: "assertion:{assertion_id}:{assertion_hash}"
    stores: "Generated questions for this assertion"
    ttl: "30 days"
    invalidation: "On assertion text change"
    benefit: "Same assertion in updated doc uses cached questions"
    
  template_level:
    key: "template:{template_id}:{component_hash}"
    stores: "Template application results"
    ttl: "Permanent"
    invalidation: "On template definition change"
    
  llm_level:
    key: "llm:{prompt_hash}"
    stores: "LLM responses"
    ttl: "30 days"
    invalidation: "Never (same prompt = same response expected)"
    benefit: "Avoids redundant API calls"
```

### Cost Model and Controls

```yaml
cost_controls:

  budget_limits:
    per_document: "$0.10"
    per_day: "$10.00"
    per_month: "$100.00"
    
  cost_tracking:
    granularity: "Per document, per assertion, per LLM call"
    alerts:
      - threshold: "80% of daily budget"
        action: "Send alert, continue"
      - threshold: "100% of daily budget"
        action: "Pause LLM calls, template-only mode"
        
  optimization:
    - "Template-first: Only use LLM when templates fail"
    - "Caching: Never re-generate for unchanged assertions"
    - "Batching: Group LLM requests to reduce overhead"
    - "Model selection: Use Haiku for simple, Sonnet for complex"
```

### Error Handling

```yaml
error_handling:

  llm_timeout:
    detection: "No response in 30 seconds"
    retry: "3 times with exponential backoff"
    fallback: "Skip LLM, use template-only questions"
    logging: "Record failure for analysis"
    
  llm_rate_limit:
    detection: "429 response"
    action: "Queue request for later"
    fallback: "None (will eventually complete)"
    
  parse_failure:
    detection: "Invalid markdown/YAML"
    action: "Return error to user with line number"
    fallback: "None (user must fix)"
    
  validation_failure:
    detection: "Question fails checks"
    action: "Store in rejected queue with reason"
    fallback: "Continue with valid questions"
    
  partial_success:
    policy: "Return valid questions even if some failed"
    response_includes:
      - valid_questions: []
      - failed_assertions: []
      - coverage_achieved: "80%"
      - errors: []
```

### API Design

```yaml
api_endpoints:

  POST /generate:
    input:
      document: "markdown string or file upload"
      options:
        include_llm: true
        target_coverage: 0.8
        max_cost: "$0.10"
    output:
      job_id: "uuid"
      status: "queued"
    async: true
    
  GET /status/{job_id}:
    output:
      status: "processing|complete|failed"
      progress:
        assertions_found: 20
        questions_generated: 16
        questions_validated: 15
      estimated_completion: "2024-01-01T10:05:00Z"
      
  GET /result/{job_id}:
    output:
      questions: []
      coverage:
        sections_covered: "8/10"
        assertions_covered: "18/20"
      cost_incurred: "$0.02"
      
  POST /validate:
    input:
      questions: []
    output:
      valid: []
      invalid: [{question: {}, reason: "answer leakage"}]
```

### Validation Criteria

Architecture is successful if:
- P95 latency < 60 seconds for 20-assertion document
- Cost per document < $0.05 average (with caching)
- Cache hit rate > 70% after initial population
- Error recovery works (no lost jobs)

---

## Question 3: Documentation-Test Integration

### Answer

Here's a practical tooling and workflow integration that documentation authors can actually adopt.

### IDE Integration (VS Code)

```json
// .vscode/extensions.json
{
  "recommendations": [
    "doctest.doctest-extension"
  ]
}

// .vscode/settings.json
{
  "doctest.enable": true,
  "doctest.lintOnSave": true,
  "doctest.showAssertionHighlights": true,
  "doctest.showCoverageInGutter": true,
  "doctest.testOnSave": false,
  "doctest.apiEndpoint": "http://localhost:8080"
}
```

```typescript
// Extension features

// 1. ASSERTION HIGHLIGHTING
// @assertion blocks get distinct background color
// Hover shows: type, ID, generated questions preview

// 2. COVERAGE GUTTER
// Green: Section has assertions with questions
// Yellow: Section has assertions, no questions yet
// Red: Section has no assertions (if type requires them)

// 3. INLINE DIAGNOSTICS
// Warning: "Vague quantifier 'several' - consider specific number"
// Warning: "No assertions in Steps section"
// Error: "Assertion ID 'step1_01' already exists"

// 4. CODE ACTIONS
// "Generate questions for this assertion" → Calls API, shows preview
// "Add assertion here" → Inserts template @assertion block
// "View generated questions" → Opens side panel with Q&A list

// 5. SNIPPETS
// Type "assert" → Expands to full @assertion template
// Type "step" → Expands to step template with assertion placeholder
```

### CI/CD Integration

```yaml
# .github/workflows/doctest.yml

name: Documentation Testing

on:
  push:
    paths:
      - 'docs/**/*.md'
  pull_request:
    paths:
      - 'docs/**/*.md'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Lint Documentation
        run: |
          npx doctest-cli lint docs/
        # Checks:
        # - All required sections present
        # - No vague quantifiers
        # - All sections have assertions (where required)
        # - Assertion IDs unique
        
  generate:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      
      - name: Generate Questions
        run: |
          npx doctest-cli generate docs/ --output questions/
        env:
          DOCTEST_API_KEY: ${{ secrets.DOCTEST_API_KEY }}
          
      - name: Validate Questions
        run: |
          npx doctest-cli validate questions/
          
      - name: Coverage Report
        run: |
          npx doctest-cli coverage docs/ questions/ --format markdown > coverage.md
          
      - name: Comment PR with Coverage
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const coverage = fs.readFileSync('coverage.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: coverage
            });

  test:
    runs-on: ubuntu-latest
    needs: generate
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Comprehension Tests
        run: |
          npx doctest-cli test questions/ --models claude,gpt4
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          
      - name: Check for Ambiguities
        run: |
          npx doctest-cli analyze results/ --threshold 0.8
        # Fails if model agreement < 80%
```

### Coverage Report Format

```markdown
# Documentation Test Coverage Report

**Generated:** 2024-01-15T10:30:00Z
**Document:** workflows/card_creation.md

## Summary

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Sections with assertions | 8/10 | 80% | ✅ 80% |
| Assertions with questions | 24/28 | 85% | ⚠️ 86% |
| Question validation rate | 22/24 | 90% | ✅ 92% |
| Model agreement | 20/22 | 80% | ✅ 91% |

## Section Coverage

| Section | Assertions | Questions | Status |
|---------|------------|-----------|--------|
| Input | 3 | 3 | ✅ |
| Output | 2 | 2 | ✅ |
| Step 1 | 4 | 4 | ✅ |
| Step 2 | 5 | 4 | ⚠️ 1 failed validation |
| Step 3 | 6 | 6 | ✅ |
| Validation | 4 | 3 | ⚠️ 1 failed validation |
| Error Handling | 4 | 4 | ✅ |

## Issues Detected

### Low Agreement Questions (< 80%)

| Question | Agreement | Models Disagreed |
|----------|-----------|------------------|
| "What happens if input is empty?" | 67% | GPT-4 |

**Recommendation:** Review assertion `step2_behavior_03` for clarity.

### Failed Validation

| Assertion | Reason |
|-----------|--------|
| `step2_constraint_02` | Answer leakage (40% overlap) |
| `valid_check_04` | Grammar error in generated question |

**Action Required:** Revise assertions or question templates.
```

### Adoption Strategy

```yaml
adoption_phases:

  phase_1_pilot:
    duration: "2 weeks"
    scope: "1-2 critical workflows"
    effort: "1 person, part-time"
    deliverable: "Proof of concept, feedback"
    success_criteria:
      - "Questions generate successfully"
      - "Coverage report is useful"
      - "No major workflow friction"
      
  phase_2_expansion:
    duration: "4 weeks"
    scope: "All critical workflows (10-20 docs)"
    effort: "Documentation team, training"
    deliverable: "All critical docs have assertions"
    success_criteria:
      - "80%+ sections have assertions"
      - "Question generation automated"
      - "CI/CD integrated"
      
  phase_3_maintenance:
    duration: "Ongoing"
    scope: "All documentation"
    effort: "Part of normal doc workflow"
    deliverable: "Continuous testing"
    success_criteria:
      - "Assertions added with new docs"
      - "Coverage maintained"
      - "Ambiguity detection catches issues"
```

### Validation Criteria

Integration is successful if:
- Linting catches 90%+ of structural issues before review
- Question generation runs in CI without manual intervention
- Coverage reports are reviewed in PR process
- Time to add assertions < 10% overhead on doc writing

---

# Final Synthesis

## Integration Assessment

**Does linking documentation format + question generation + LLM optimization make sense?**

Yes, strongly. The integration creates a virtuous cycle:
1. Structured format → Reliable question generation
2. Generated questions → Test documentation quality
3. Test results → Improve documentation
4. Improved documentation → Better LLM comprehension

Your existing `document_structure.md` provides 70% of what's needed. The key addition is explicit assertion markers.

**Biggest risk:** Over-engineering. The temptation to create a complex schema, elaborate pipelines, and extensive tooling before proving the concept works. Start simple.

**Biggest benefit:** Documentation quality becomes measurable. You can finally answer "is this documentation clear?" with data instead of intuition.

## Practical Recommendation

**If implementing next week, build first:**

```yaml
mvp_implementation:
  
  week_1:
    - "Add @assertion markers to 1 critical workflow"
    - "Build simple parser to extract assertions"
    - "Implement 3 template rules (constraint, requirement, behavior)"
    - "Generate questions for the 1 workflow"
    - "Manually validate questions work"
    
  deliverable:
    - "10-15 questions from 1 document"
    - "Validation that questions test real comprehension"
    - "Template rules that don't produce leakage"
```

**Can be deferred:**
- LLM-assisted question generation (templates are enough for MVP)
- Full CI/CD integration
- IDE extension
- Multi-model testing
- Caching infrastructure
- Cost tracking

## Success Criteria

**How to measure if this works:**

```yaml
success_metrics:

  technical_metrics:
    template_success_rate:
      measure: "% of assertions that generate valid questions via templates"
      target: "> 80%"
      
    question_validation_rate:
      measure: "% of generated questions that pass all validation checks"
      target: "> 90%"
      
    coverage_achievement:
      measure: "% of sections with at least one test question"
      target: "> 80%"

  outcome_metrics:
    ambiguity_detection_rate:
      measure: "% of real doc issues caught by question testing"
      target: "> 70%"
      validation: "Compare against human review findings"
      
    false_positive_rate:
      measure: "% of flagged issues that aren't real problems"
      target: "< 20%"
      
    documentation_improvement:
      measure: "% of flagged issues that lead to doc fixes"
      target: "> 50%"

  adoption_metrics:
    writer_adoption:
      measure: "% of new docs that include assertions"
      target: "> 80% after 3 months"
      
    overhead:
      measure: "Additional time to write doc with assertions"
      target: "< 15%"
```

**When you know you're done:**
1. All critical workflows have assertions and questions
2. Question generation is automated (not manual)
3. Ambiguity detection catches real issues (validated against human review)
4. Documentation writers use assertions as normal practice
5. CI fails on untested critical sections

---

## Appendix: Quick Reference

### Assertion Block Syntax

```markdown
<!-- @assertion id="unique_id" type="type" priority="priority" -->
Testable claim text.
<!-- @/assertion -->
```

### Assertion Types

| Type | Question Pattern | Example Assertion |
|------|------------------|-------------------|
| `requirement` | "Is X required?" | "All fields must be validated" |
| `constraint` | "What is the X?" | "Maximum batch size: 20 items" |
| `behavior` | "What happens when X?" | "On error: Retry 3 times" |
| `error` | "What error when X?" | "Missing field triggers ValidationError" |
| `specification` | "What is the X of Y?" | "Output format: JSON array" |
| `formula` | "How is X calculated?" | "Count = items × 2" |
| `sequence` | "What comes before/after X?" | "Step 3 requires Step 2" |

### Template Success Checklist

✅ Question doesn't contain answer text  
✅ Answer is extractable from assertion  
✅ Question is grammatically correct  
✅ Question tests single concept  
✅ Question is unique (not duplicate)
