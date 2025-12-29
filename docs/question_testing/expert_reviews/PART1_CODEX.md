OpenAI Codex v0.77.0 (research preview)
--------
workdir: /Users/nik_kosmo/Library/Mobile Documents/com~apple~CloudDocs/projects/document_polishing
model: gpt-5.2-codex
provider: openai
approval: never
sandbox: read-only
reasoning effort: medium
reasoning summaries: auto
session id: 019b6b2a-3e9c-7fb0-9d97-234aa58b489f
--------
user
# Expert Review Prompt: Question-Based Testing Framework

Please review this documentation testing framework by assuming multiple expert perspectives. Provide structured feedback on design decisions, implementation approach, and improvements.

---

## Context

**Project:** Document Polishing System - Automated ambiguity detection in technical documentation

**Current Approach:** Test documentation with multiple AI models, compare interpretations, flag disagreements as potential ambiguities

**New Feature:** Question-Based Testing Framework
- Generate comprehension questions from documentation
- Collect answers from multiple models
- Evaluate answers to detect comprehension failures
- Use disagreements/failures to identify unclear documentation

**Problem Being Solved:** Current approach finds ambiguities through open-ended interpretation, but doesn't systematically test specific aspects of documentation (e.g., requirements, procedures, constraints)

---

## Your Task

Review the framework design and implementation by assuming these expert perspectives **one at a time**:

1. **Educational Assessment Specialist** - Expert in test design, reading comprehension evaluation, item writing
2. **Technical Communication Researcher** - Expert in documentation usability, clarity metrics, user comprehension
3. **NLP/LLM Evaluation Researcher** - Expert in question-answering systems, benchmark design, LLM testing
4. **Cognitive Psychologist** - Expert in text comprehension, mental models, inference processes
5. **Software Architect** - Expert in system design, API design, maintainability

For each perspective, provide:
- ✅ **Strengths** - What's well-designed from this viewpoint
- ⚠️ **Concerns** - Potential issues or limitations
- 💡 **Recommendations** - Specific improvements or alternatives

---

## Documentation to Review

### 1. Framework Design Document

**File:** `QUESTION_BASED_TESTING_FRAMEWORK.md`

**Key sections:**
- Motivation and goals
- Question generation approach (template-based + LLM-assisted)
- Answer collection methodology
- Evaluation strategy (LLM-as-Judge)
- Integration with existing pipeline

### 2. Implementation Review Report

**File:** `PHASE_3_4_5_REVIEW_REPORT.md`

**Key findings:**
- Architecture: 5 new classes (CrossReferenceAnalyzer, ConflictDetector, AnswerCollector, AnswerEvaluator, ConsensusCalculator)
- Current status: All bugs fixed, 127/127 tests passing
- Critical issue: Template-based questions fail validation (answer leakage)
- Real-world test: 6 questions generated, 0 passed validation

### 3. Current Template Design

**File:** `scripts/templates/question_templates.json`

**Example template:**
```json
{
  "template_id": "existence_mention_01",
  "category": "factual",
  "question_pattern": "Does the documentation mention {element_text}?",
  "triggers": {
    "element_types": ["any"]
  },
  "answer_extraction": {
    "keywords": [],
    "confidence_threshold": "medium"
  }
}
```

**Problem identified:** This generates questions like:
- Q: "Does the documentation mention 'The timeout defaults to 30 seconds'?"
- A: "The timeout defaults to 30 seconds"
- Result: ❌ Fails validation - answer text appears in question

---

## Specific Questions for Each Expert

### For Educational Assessment Specialist:

1. **Question Design:**
   - Are template-based questions appropriate for testing comprehension?
   - What question types should we prioritize (factual, procedural, inferential, conditional)?
   - How do professional reading comprehension tests avoid answer leakage?

2. **Validation Rules:**
   Current rules:
   - Rule 1: Answer keywords must be present in source section
   - Rule 2: Answer text must NOT appear in question (no leakage)
   - Rule 3: Question must be grammatically correct
   - Rule 4: Question must test single concept

   Are these sufficient? What's missing?

3. **Evaluation Approach:**
   - Is LLM-as-Judge valid for scoring answers?
   - Should we use rubrics instead of binary correct/incorrect?
   - How do we handle partial understanding?

4. **Coverage Targets:**
   Current: 70% sections, 60% elements
   - Are these reasonable targets?
   - Should coverage vary by documentation type?

### For Technical Communication Researcher:

1. **Documentation-Specific Concerns:**
   - What aspects of technical docs are most critical to test (procedures, requirements, constraints, exceptions)?
   - How should questions differ for procedural vs. reference documentation?
   - Should we test different cognitive levels (recall, application, analysis)?

2. **Real-World Validity:**
   - Do model comprehension failures predict real user comprehension issues?
   - What documentation problems might this approach miss?
   - How should we validate that fixed "ambiguities" actually improve user comprehension?

3. **Practical Utility:**
   - Is this more useful than traditional documentation review methods?
   - What's the right balance between automated and manual review?
   - How should we present results to documentation writers?

### For NLP/LLM Evaluation Researcher:

1. **Question Generation:**
   - Should we use LLM-assisted generation instead of templates?
   - What existing QA datasets (SQuAD, RACE) can inform our approach?
   - How do we ensure question diversity?

2. **Multi-Model Evaluation:**
   - Is comparing multiple models' answers a valid ambiguity signal?
   - What consensus mechanisms work best?
   - How do we account for model-specific biases?

3. **LLM-as-Judge:**
   - What are the failure modes of using LLMs to evaluate answers?
   - Should we use specialized prompts per question type?
   - How do we validate judge consistency?

4. **Benchmark Design:**
   - Should we create a gold standard test set?
   - How do we measure framework effectiveness?
   - What metrics matter (precision, recall, coverage)?

### For Cognitive Psychologist:

1. **Comprehension Modeling:**
   - What levels of comprehension should we test (surface, textbase, situation model)?
   - How do we distinguish memorization from understanding?
   - Should we test inference-making separately from fact recall?

2. **Question Types:**
   - What question types reveal different comprehension processes?
   - How should we test implicit vs. explicit information?
   - Should we include "trick questions" to test careful reading?

3. **Mental Models:**
   - Can we test if models build accurate mental models of systems described in docs?
   - How do we detect misconceptions vs. missing information?
   - Should we test transfer (applying doc knowledge to new scenarios)?

### For Software Architect:

1. **Architecture:**
   - Is the 5-class design appropriate?
   - Should template application be separated from question generation?
   - How should we handle different documentation formats (API docs, tutorials, reference)?

2. **Extensibility:**
   - How easy is it to add new question types?
   - Should we support custom validators per domain?
   - How should we handle different output formats?

3. **Performance:**
   - What's the scalability for large documentation sets?
   - Should question generation be cached?
   - How do we handle session management efficiently?

4. **Integration:**
   - Does this fit well with the existing pipeline?
   - Should question testing be optional or mandatory?
   - How do we version questions/answers for tracking changes?

---

## Implementation Context

### Current Architecture

```
DocumentProcessor → SectionExtractor → [NEW] QuestioningStep → Testing → Detection → Reporting
                                              ↓
                                    1. Generate Questions (template-based)
                                    2. Collect Answers (multi-model, with sessions)
                                    3. Evaluate Answers (LLM-as-Judge)
                                    4. Calculate Consensus
                                    5. Detect Issues
```

### Key Design Decisions

1. **Template-based generation** (not pure LLM generation)
   - Rationale: Control, reproducibility, cost
   - Trade-off: Less flexible, requires good templates

2. **Section-level + Document-level questions**
   - Section: Test understanding of individual parts
   - Document: Test cross-references, conflicts, dependencies

3. **Session-based answer collection**
   - Models see full document before answering
   - Rationale: Better context for comprehension

4. **LLM-as-Judge evaluation**
   - Use one model to evaluate others' answers
   - Rationale: Scalable, no human annotation needed
   - Trade-off: Judge quality affects results

5. **Coverage-based selection**
   - Don't ask every possible question
   - Target: 70% sections, 60% elements
   - Rationale: Balance thoroughness with cost/time

### Known Limitations

1. **Template design is broken** - Current templates cause answer leakage
2. **No validation of approach** - Haven't tested if this finds real doc issues
3. **No gold standard** - No ground truth for "correct" answers
4. **Cost** - Multiple LLM calls per question (collection + evaluation)
5. **Bias** - All models might share same misunderstandings

---

## Output Format

For each expert perspective, structure your response as:

```markdown
## [Expert Role]

### ✅ Strengths
- [Specific strength with reasoning]
- [Another strength]
...

### ⚠️ Concerns
- [Specific concern with explanation]
- [Another concern]
...

### 💡 Recommendations
1. [Specific, actionable recommendation]
   - Why: [Rationale]
   - How: [Implementation approach]
   - Priority: [High/Medium/Low]

2. [Another recommendation]
   ...
```

---

## Final Synthesis

After reviewing from all perspectives, provide:

1. **Overall Assessment:**
   - Is this approach fundamentally sound?
   - What are the biggest risks?
   - What are the highest-value improvements?

2. **Priority Recommendations:**
   - Top 3 changes to make before using in production
   - Top 3 research questions to answer

3. **Alternative Approaches:**
   - Are there simpler ways to achieve the same goal?
   - What hybrid approaches might work better?

---

## Additional Notes

- You have access to the full codebase if you need to review implementation details
- Focus on design and approach, not code quality (that's been reviewed)
- Be specific - generic advice like "add more tests" isn't helpful
- Consider trade-offs - every recommendation has costs
- Think about practical use - will documentation writers actually use this?

---

**Begin your review now. Take your time with each perspective.**
mcp startup: no servers

thinking
**Preparing to read files**
exec
/bin/zsh -lc ls in /Users/nik_kosmo/Library/Mobile Documents/com~apple~CloudDocs/projects/document_polishing succeeded in 289ms:
AGENTS.md
CLAUDE.md
LICENSE
README.md
SESSION_LOG.md
TODO.md
docs
requirements.txt
scripts
temp
test
tests
workspace

thinking
**Deciding on file reading method**
exec
/bin/zsh -lc "sed -n '1,220p' QUESTION_BASED_TESTING_FRAMEWORK.md" in /Users/nik_kosmo/Library/Mobile Documents/com~apple~CloudDocs/projects/document_polishing exited 1 in 239ms:
sed: QUESTION_BASED_TESTING_FRAMEWORK.md: No such file or directory
exec
/bin/zsh -lc "sed -n '1,220p' PHASE_3_4_5_REVIEW_REPORT.md" in /Users/nik_kosmo/Library/Mobile Documents/com~apple~CloudDocs/projects/document_polishing exited 1 in 219ms:
sed: PHASE_3_4_5_REVIEW_REPORT.md: No such file or directory
exec
/bin/zsh -lc "sed -n '1,220p' scripts/templates/question_templates.json" in /Users/nik_kosmo/Library/Mobile Documents/com~apple~CloudDocs/projects/document_polishing succeeded in 207ms:
{
  "version": "1.0.0",
  "description": "Template library for question-based testing framework",
  "templates": [
    {
      "template_id": "factual_format_01",
      "category": "factual",
      "difficulty": "basic",
      "question_pattern": "According to the {section_title} section, what format should the {element_text} use?",
      "answer_extraction": {
        "keywords": ["format", "formatted", "formatting"],
        "context_window": 2,
        "confidence_threshold": "high"
      },
      "triggers": {
        "element_types": ["requirement", "constraint", "output"],
        "required_keywords": ["format", "formatted as", "must be formatted"]
      },
      "validation_hints": {
        "answer_should_contain": ["format"],
exec
/bin/zsh -lc "sed -n '220,520p' scripts/templates/question_templates.json" in /Users/nik_kosmo/Library/Mobile Documents/com~apple~CloudDocs/projects/document_polishing succeeded in 252ms:
        "keywords": ["maximum", "minimum", "max", "min", "limit", "at most", "at least"],
        "context_window": 2,
        "confidence_threshold": "high"
      },
      "triggers": {
        "element_types": ["constraint", "requirement"],
        "required_keywords": ["maximum", "minimum", "max", "min", "limit", "at most", "at least"]
      },
      "validation_hints": {
        "answer_should_contain": ["\\d+", "maximum", "minimum"],
        "answer_should_not_contain": ["what is"]
      }
    },
    {
      "template_id": "existence_mention_01",
      "category": "existence",
      "difficulty": "basic",
      "question_pattern": "Does the documentation mention {element_text}?",
      "answer_extraction": {
        "keywords": [],

thinking
**Searching for missing files with ripgrep**
exec
/bin/zsh -lc "rg --files -g 'QUESTION_BASED_TESTING_FRAMEWORK.md' -g 'PHASE_3_4_5_REVIEW_REPORT.md'" in /Users/nik_kosmo/Library/Mobile Documents/com~apple~CloudDocs/projects/document_polishing succeeded in 275ms:
docs/QUESTION_BASED_TESTING_FRAMEWORK.md

thinking
**Searching for report file**
exec
/bin/zsh -lc "rg --files -g 'PHASE_3_4_5_REVIEW_REPORT.md'" in /Users/nik_kosmo/Library/Mobile Documents/com~apple~CloudDocs/projects/document_polishing exited 1 in 211ms:


thinking
**Searching for review report files**
exec
/bin/zsh -lc "rg --files -g '*REVIEW*REPORT*.md'" in /Users/nik_kosmo/Library/Mobile Documents/com~apple~CloudDocs/projects/document_polishing exited 1 in 180ms:


thinking
**Noting missing report file**
exec
/bin/zsh -lc "sed -n '1,260p' docs/QUESTION_BASED_TESTING_FRAMEWORK.md" in /Users/nik_kosmo/Library/Mobile Documents/com~apple~CloudDocs/projects/document_polishing succeeded in 186ms:
# Question-Based Testing Framework for LLM Documentation Evaluation

**Version:** 1.0  
**Date:** December 2025  
**Author:** Document Polishing System Design Team  
**Purpose:** Comprehensive design specification for question-based testing to complement interpretation-based ambiguity detection

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Research Findings](#2-research-findings)
3. [Question-Based Testing Design](#3-question-based-testing-design)
4. [Adversarial Testing Design](#4-adversarial-testing-design)
5. [Multi-Level Testing Strategy](#5-multi-level-testing-strategy)
6. [Integration Architecture](#6-integration-architecture)
7. [Implementation Specification](#7-implementation-specification)
8. [Success Metrics & Validation](#8-success-metrics--validation)

exec
/bin/zsh -lc "sed -n '260,520p' docs/QUESTION_BASED_TESTING_FRAMEWORK.md" in /Users/nik_kosmo/Library/Mobile Documents/com~apple~CloudDocs/projects/document_polishing succeeded in 183ms:
Template: "What happens when [condition] in [section]?"
Example: "What happens when the input file is empty in the Processing section?"

Template: "Under what circumstances does [action] occur?"
Example: "Under what circumstances does the system retry the connection?"
```

**Quantitative Questions:**
```
Template: "How many [items] does [section] require?"
Example: "How many validation passes does Step 2 require?"

Template: "What is the [maximum/minimum] [measurement] specified?"
Example: "What is the maximum file size specified for uploads?"
```

**Existence Questions:**
```
Template: "Does [section] mention [concept]?"
Example: "Does the Error Handling section mention timeout exceptions?"
exec
/bin/zsh -lc "sed -n '520,1040p' docs/QUESTION_BASED_TESTING_FRAMEWORK.md" in /Users/nik_kosmo/Library/Mobile Documents/com~apple~CloudDocs/projects/document_polishing succeeded in 186ms:

**Generation Patterns:**

| Pattern | Example |
|---------|---------|
| Zero/empty input | "What if the input list is empty?" |
| Maximum limits | "What if there are 1 million entries?" |
| Null/missing values | "What if required field is null?" |
| Type edge cases | "What if ID is negative?" |
| Concurrent operations | "What if two users run this simultaneously?" |

**Template:**
```
Edge Case Type: Empty Input
Document states: "Process all items in the list."
Edge Question: "What happens if the list contains zero items?"
Expected Behavior: Model acknowledges edge case is not specified OR provides reasonable inference.
Pass Criteria: Model does not hallucinate a specific behavior not in document.
```

exec
/bin/zsh -lc "sed -n '1040,1560p' docs/QUESTION_BASED_TESTING_FRAMEWORK.md" in /Users/nik_kosmo/Library/Mobile Documents/com~apple~CloudDocs/projects/document_polishing succeeded in 176ms:
          "raw_response": "...",
          "confidence_stated": null
        },
        "gpt4": {
          "answer_text": "According to the documentation, outputs must be JSON-formatted and use UTF-8 encoding.",
          "response_time_ms": 1456,
          "raw_response": "...",
          "confidence_stated": null
        }
      }
    }
  ]
}
```

#### 6.2.3 Question Results Artifact

**File:** `question_results.json`

```json
exec
/bin/zsh -lc "sed -n '1560,2080p' docs/QUESTION_BASED_TESTING_FRAMEWORK.md" in /Users/nik_kosmo/Library/Mobile Documents/com~apple~CloudDocs/projects/document_polishing succeeded in 185ms:
    # Any incorrect answer is an issue
    IF any(e.score == "incorrect" for e in evaluations.values()):
        RETURN Issue(
            detected=True,
            type="incorrect_answer",
            severity=map_severity(question),
            recommendation=generate_recommendation(question, evaluations)
        )
    
    # Disagreement is an issue
    IF consensus == "disagreement":
        RETURN Issue(
            detected=True,
            type="comprehension_disagreement",
            severity="medium",
            recommendation="Clarify section to ensure consistent interpretation"
        )
    
    # Adversarial failure is an issue
    IF question.is_adversarial AND adversarial_failed(question, evaluations):
exec
/bin/zsh -lc "sed -n '2080,2600p' docs/QUESTION_BASED_TESTING_FRAMEWORK.md" in /Users/nik_kosmo/Library/Mobile Documents/com~apple~CloudDocs/projects/document_polishing succeeded in 176ms:
  "reasoning": "<analysis of how model handled the adversarial element>",
  "failure_mode": "<if failed, what went wrong>"
}
```

---

## Appendix D: Implementation Checklist

### D.1 Phase 1: Core Infrastructure
- [ ] Question data structures (Question, Answer, Evaluation)
- [ ] Template library (factual, procedural, conditional)
- [ ] Question generation algorithm
- [ ] questions.json artifact format

### D.2 Phase 2: Question Generation
- [ ] Section-level question generator
- [ ] Document-level question generator
- [ ] Template application logic
- [ ] LLM-based question generation

thinking
**Drafting structured review with detailed recommendations**

I'll prepare a thorough review following the user's requested format using Markdown headings, noting the missing PHASE_3_4_5_REVIEW_REPORT.md file, highlighting strengths, concerns, and recommendations across five expert sections, and providing a final synthesis. I’ll address template leakage issues, coverage target inconsistencies, LLM evaluation biases, and suggest improvements including unanswerable questions and rubric scoring. The response will balance ASCII formatting with emojis since the user explicitly requested them, and I’ll include thoughtful citations to relevant docs while prioritizing clarity and conciseness.
codex
Note: `PHASE_3_4_5_REVIEW_REPORT.md` is not present in the workspace, so I relied on your summary plus `docs/QUESTION_BASED_TESTING_FRAMEWORK.md` and `scripts/templates/question_templates.json`.

## Educational Assessment Specialist

### ✅ Strengths
- Clear taxonomy and difficulty tiers in `docs/QUESTION_BASED_TESTING_FRAMEWORK.md` give a solid blueprint for item writing and balanced test forms.
- Inclusion of unanswerable, adversarial, and inference questions aligns with modern comprehension assessment practices.
- Section-level vs document-level separation mirrors standard practice of testing local vs global comprehension.

### ⚠️ Concerns
- Template-based items currently leak answers when `element_text` is a verbatim clause, which undermines validity.
- Validation rules are mostly surface-level; they do not address distractor quality, inference demand, or construct-irrelevant variance.
- Binary scoring plus LLM-as-judge without rubrics risks conflating partial understanding with full failure.
- Coverage targets are inconsistent (70/60 in your prompt vs 95/80 in `docs/QUESTION_BASED_TESTING_FRAMEWORK.md`), making measurement expectations unclear.

### 💡 Recommendations
1. Split item stems from evidence spans
   - Why: Prevents answer leakage and improves construct validity.
   - How: Use span IDs or abstracted labels instead of raw `element_text` in `scripts/templates/question_templates.json`.
   - Priority: High

2. Add rubric-based scoring for partial credit
   - Why: Comprehension often degrades in degrees; binary scoring hides actionable nuance.
   - How: Include rubric slots per template (key concepts, optional details, disqualifiers) and have the judge score each.
   - Priority: High

3. Expand validation to include cognitive demand checks
   - Why: Many templates are still pure recall; higher-level comprehension is under-tested.
   - How: Add validation for inference requirement and absence of direct sentence overlap.
   - Priority: Medium

4. Make coverage targets conditional on doc genre
   - Why: Procedures need denser procedural/inference testing than reference docs.
   - How: Use a doc-type classifier to adjust targets per category.
   - Priority: Medium

## Technical Communication Researcher

### ✅ Strengths
- Conflict detection and cross-reference questions target real documentation failure modes.
- Adversarial categories map well to common usability pitfalls (missing context, false premises).
- Integration plan aligns with existing pipeline and should surface actionable issues.

### ⚠️ Concerns
- Model comprehension failure does not necessarily predict user comprehension; false positives are likely without human validation.
- Template categories still focus heavily on recall; practical usability hinges on procedural success and edge-case clarity.
- No explicit plan for presenting issues to writers in a way that supports revision decisions.

### 💡 Recommendations
1. Add user-task aligned question sets
   - Why: Usability issues emerge in task execution, not just recall.
   - How: For procedural sections, generate scenario-based questions tied to end-user goals.
   - Priority: High

2. Validate with small-scale human review
   - Why: Establish whether flagged issues correspond to actual user confusion.
   - How: Sample 10-20 questions per doc for writer review and track disagreement.
   - Priority: Medium

3. Improve report framing for writers
   - Why: Writers need actionable guidance, not just model disagreement.
   - How: Add “writing fix type” tags (missing prerequisite, ambiguous term, conflicting constraint).
   - Priority: Medium

## NLP/LLM Evaluation Researcher

### ✅ Strengths
- Hybrid generation approach (template + LLM) is aligned with best practice for controllability and diversity.
- LLM-as-judge prompt includes evidence citation, which supports auditability.
- Includes metamorphic and adversarial testing ideas that help probe brittleness.

### ⚠️ Concerns
- LLM-as-judge is known to be inconsistent and susceptible to prompt framing; no calibration plan is specified.
- Consensus is based on model answers, which may be correlated and not independent.
- Several templates are yes/no or require minimal reasoning; they may not surface subtle ambiguity.

### 💡 Recommendations
1. Calibrate the judge with small gold sets
   - Why: Judge drift will affect reliability and issue rates.
   - How: Create a 50-100 item benchmark per doc type; use it to calibrate judge prompts and scoring.
   - Priority: High

2. Add diversity constraints in question generation
   - Why: Similar templates can overfit and miss novel ambiguity types.
   - How: Enforce per-section max template repeats and use paraphrase/negative templates.
   - Priority: Medium

3. Use paired evaluation prompts by question type
   - Why: Different question types require different scoring criteria.
   - How: Provide prompt variants for factual vs procedural vs adversarial questions.
   - Priority: Medium

4. Add model-specific bias checks
   - Why: Shared biases can make disagreement an unreliable ambiguity signal.
   - How: Include a baseline non-LLM heuristic evaluator for factual numeric questions.
   - Priority: Medium

## Cognitive Psychologist

### ✅ Strengths
- Explicit distinction between local (section) and global (document) comprehension aligns with textbase vs situation model.
- Adversarial questions that test false premises and contradictions align with inference monitoring concepts.
- Edge case probes can reveal missing situation model constraints.

### ⚠️ Concerns
- Many templates still test surface recall, not mental model construction.
- Lack of explicit separation between inference, integration, and application questions.
- No method to distinguish memorization from genuine understanding.

### 💡 Recommendations
1. Add inference-only question types
   - Why: Situation model construction is key for comprehension, especially in procedures.
   - How: Ask “what would happen if X changes” with no direct sentence answer.
   - Priority: High

2. Include transfer questions
   - Why: Applying doc knowledge to a novel scenario indicates deeper understanding.
   - How: Add “apply to new input” prompts using constrained variations.
   - Priority: Medium

3. Add confidence calibration prompts
   - Why: Overconfidence in ambiguous areas is a key signal.
   - How: Require model to state uncertainty level, and flag high-confidence wrong answers.
   - Priority: Medium

## Software Architect

### ✅ Strengths
- The 5-class design provides separation of concerns and aligns with pipeline step modularity.
- Artifacts (`questions.json`, `answers.json`, `question_results.json`) are well specified and integrate with existing ambiguity format.
- Optional pipeline integration preserves backward compatibility.

### ⚠️ Concerns
- Question generation and template application are tightly coupled; leakage bugs show that abstraction needs refinement.
- Document-level templates embed candidate values in the question (e.g., `document_conflict_02`), which is both leakage and biased.
- Scalability risk: LLM calls scale as questions × models × judge, with no caching strategy.

### 💡 Recommendations
1. Separate template rendering from element selection
   - Why: Prevents element content from leaking into question stem.
   - How: Use a two-stage process: (a) select element IDs, (b) render questions with abstracted labels.
   - Priority: High

2. Add caching for question generation and evaluation
   - Why: Large docs will be cost-heavy; caching stabilizes iterative runs.
   - How: Cache by `(doc_hash, template_id, element_id)` and by `(question_id, model_id)` for answers.
   - Priority: Medium

3. Add versioning for questions/answers
   - Why: Needed for tracking regressions across doc revisions.
   - How: Include doc hash and template version in artifacts.
   - Priority: Medium

4. Support pluggable validators
   - Why: Domain-specific checks are common in technical docs.
   - How: Allow per-template validators registered by category or doc type.
   - Priority: Medium

---

## Final Synthesis

### Overall Assessment
- Fundamentally sound: the dual-level question strategy is a meaningful complement to interpretation testing.
- Biggest risks: answer leakage in templates, judge inconsistency, and lack of ground-truth validation.
- Highest-value improvements: fix generation/validation to stop leakage, calibrate evaluation, and align question types with task-oriented comprehension.

### Priority Recommendations
Top 3 changes before production:
1. Replace `element_text` slotting with abstracted IDs to eliminate leakage in `scripts/templates/question_templates.json`.
2. Introduce rubric-based scoring and judge calibration with a small gold set.
3. Add task-oriented procedural questions and reduce reliance on pure recall.

Top 3 research questions:
1. Do question-based failures correlate with human user confusion?
2. How stable is LLM-as-judge across doc domains and question types?
3. What mix of template vs LLM-generated questions yields the best precision/recall for ambiguities?

### Alternative Approaches
- Simpler: Use deterministic checks on extracted requirements and constraints (conflict detection without QA).
- Hybrid: Combine heuristic conflict detectors with a smaller set of QA items focused on high-risk sections.
- Task simulation: Generate scenario-based tasks and ask models to execute them step-by-step, then score with a rubric.

If you want, I can also review the question generation/validation logic in code and propose a concrete leakage-proof template schema.
tokens used
33,449
Note: `PHASE_3_4_5_REVIEW_REPORT.md` is not present in the workspace, so I relied on your summary plus `docs/QUESTION_BASED_TESTING_FRAMEWORK.md` and `scripts/templates/question_templates.json`.

## Educational Assessment Specialist

### ✅ Strengths
- Clear taxonomy and difficulty tiers in `docs/QUESTION_BASED_TESTING_FRAMEWORK.md` give a solid blueprint for item writing and balanced test forms.
- Inclusion of unanswerable, adversarial, and inference questions aligns with modern comprehension assessment practices.
- Section-level vs document-level separation mirrors standard practice of testing local vs global comprehension.

### ⚠️ Concerns
- Template-based items currently leak answers when `element_text` is a verbatim clause, which undermines validity.
- Validation rules are mostly surface-level; they do not address distractor quality, inference demand, or construct-irrelevant variance.
- Binary scoring plus LLM-as-judge without rubrics risks conflating partial understanding with full failure.
- Coverage targets are inconsistent (70/60 in your prompt vs 95/80 in `docs/QUESTION_BASED_TESTING_FRAMEWORK.md`), making measurement expectations unclear.

### 💡 Recommendations
1. Split item stems from evidence spans
   - Why: Prevents answer leakage and improves construct validity.
   - How: Use span IDs or abstracted labels instead of raw `element_text` in `scripts/templates/question_templates.json`.
   - Priority: High

2. Add rubric-based scoring for partial credit
   - Why: Comprehension often degrades in degrees; binary scoring hides actionable nuance.
   - How: Include rubric slots per template (key concepts, optional details, disqualifiers) and have the judge score each.
   - Priority: High

3. Expand validation to include cognitive demand checks
   - Why: Many templates are still pure recall; higher-level comprehension is under-tested.
   - How: Add validation for inference requirement and absence of direct sentence overlap.
   - Priority: Medium

4. Make coverage targets conditional on doc genre
   - Why: Procedures need denser procedural/inference testing than reference docs.
   - How: Use a doc-type classifier to adjust targets per category.
   - Priority: Medium

## Technical Communication Researcher

### ✅ Strengths
- Conflict detection and cross-reference questions target real documentation failure modes.
- Adversarial categories map well to common usability pitfalls (missing context, false premises).
- Integration plan aligns with existing pipeline and should surface actionable issues.

### ⚠️ Concerns
- Model comprehension failure does not necessarily predict user comprehension; false positives are likely without human validation.
- Template categories still focus heavily on recall; practical usability hinges on procedural success and edge-case clarity.
- No explicit plan for presenting issues to writers in a way that supports revision decisions.

### 💡 Recommendations
1. Add user-task aligned question sets
   - Why: Usability issues emerge in task execution, not just recall.
   - How: For procedural sections, generate scenario-based questions tied to end-user goals.
   - Priority: High

2. Validate with small-scale human review
   - Why: Establish whether flagged issues correspond to actual user confusion.
   - How: Sample 10-20 questions per doc for writer review and track disagreement.
   - Priority: Medium

3. Improve report framing for writers
   - Why: Writers need actionable guidance, not just model disagreement.
   - How: Add “writing fix type” tags (missing prerequisite, ambiguous term, conflicting constraint).
   - Priority: Medium

## NLP/LLM Evaluation Researcher

### ✅ Strengths
- Hybrid generation approach (template + LLM) is aligned with best practice for controllability and diversity.
- LLM-as-judge prompt includes evidence citation, which supports auditability.
- Includes metamorphic and adversarial testing ideas that help probe brittleness.

### ⚠️ Concerns
- LLM-as-judge is known to be inconsistent and susceptible to prompt framing; no calibration plan is specified.
- Consensus is based on model answers, which may be correlated and not independent.
- Several templates are yes/no or require minimal reasoning; they may not surface subtle ambiguity.

### 💡 Recommendations
1. Calibrate the judge with small gold sets
   - Why: Judge drift will affect reliability and issue rates.
   - How: Create a 50-100 item benchmark per doc type; use it to calibrate judge prompts and scoring.
   - Priority: High

2. Add diversity constraints in question generation
   - Why: Similar templates can overfit and miss novel ambiguity types.
   - How: Enforce per-section max template repeats and use paraphrase/negative templates.
   - Priority: Medium

3. Use paired evaluation prompts by question type
   - Why: Different question types require different scoring criteria.
   - How: Provide prompt variants for factual vs procedural vs adversarial questions.
   - Priority: Medium

4. Add model-specific bias checks
   - Why: Shared biases can make disagreement an unreliable ambiguity signal.
   - How: Include a baseline non-LLM heuristic evaluator for factual numeric questions.
   - Priority: Medium

## Cognitive Psychologist

### ✅ Strengths
- Explicit distinction between local (section) and global (document) comprehension aligns with textbase vs situation model.
- Adversarial questions that test false premises and contradictions align with inference monitoring concepts.
- Edge case probes can reveal missing situation model constraints.

### ⚠️ Concerns
- Many templates still test surface recall, not mental model construction.
- Lack of explicit separation between inference, integration, and application questions.
- No method to distinguish memorization from genuine understanding.

### 💡 Recommendations
1. Add inference-only question types
   - Why: Situation model construction is key for comprehension, especially in procedures.
   - How: Ask “what would happen if X changes” with no direct sentence answer.
   - Priority: High

2. Include transfer questions
   - Why: Applying doc knowledge to a novel scenario indicates deeper understanding.
   - How: Add “apply to new input” prompts using constrained variations.
   - Priority: Medium

3. Add confidence calibration prompts
   - Why: Overconfidence in ambiguous areas is a key signal.
   - How: Require model to state uncertainty level, and flag high-confidence wrong answers.
   - Priority: Medium

## Software Architect

### ✅ Strengths
- The 5-class design provides separation of concerns and aligns with pipeline step modularity.
- Artifacts (`questions.json`, `answers.json`, `question_results.json`) are well specified and integrate with existing ambiguity format.
- Optional pipeline integration preserves backward compatibility.

### ⚠️ Concerns
- Question generation and template application are tightly coupled; leakage bugs show that abstraction needs refinement.
- Document-level templates embed candidate values in the question (e.g., `document_conflict_02`), which is both leakage and biased.
- Scalability risk: LLM calls scale as questions × models × judge, with no caching strategy.

### 💡 Recommendations
1. Separate template rendering from element selection
   - Why: Prevents element content from leaking into question stem.
   - How: Use a two-stage process: (a) select element IDs, (b) render questions with abstracted labels.
   - Priority: High

2. Add caching for question generation and evaluation
   - Why: Large docs will be cost-heavy; caching stabilizes iterative runs.
   - How: Cache by `(doc_hash, template_id, element_id)` and by `(question_id, model_id)` for answers.
   - Priority: Medium

3. Add versioning for questions/answers
   - Why: Needed for tracking regressions across doc revisions.
   - How: Include doc hash and template version in artifacts.
   - Priority: Medium

4. Support pluggable validators
   - Why: Domain-specific checks are common in technical docs.
   - How: Allow per-template validators registered by category or doc type.
   - Priority: Medium

---

## Final Synthesis

### Overall Assessment
- Fundamentally sound: the dual-level question strategy is a meaningful complement to interpretation testing.
- Biggest risks: answer leakage in templates, judge inconsistency, and lack of ground-truth validation.
- Highest-value improvements: fix generation/validation to stop leakage, calibrate evaluation, and align question types with task-oriented comprehension.

### Priority Recommendations
Top 3 changes before production:
1. Replace `element_text` slotting with abstracted IDs to eliminate leakage in `scripts/templates/question_templates.json`.
2. Introduce rubric-based scoring and judge calibration with a small gold set.
3. Add task-oriented procedural questions and reduce reliance on pure recall.

Top 3 research questions:
1. Do question-based failures correlate with human user confusion?
2. How stable is LLM-as-judge across doc domains and question types?
3. What mix of template vs LLM-generated questions yields the best precision/recall for ambiguities?

### Alternative Approaches
- Simpler: Use deterministic checks on extracted requirements and constraints (conflict detection without QA).
- Hybrid: Combine heuristic conflict detectors with a smaller set of QA items focused on high-risk sections.
- Task simulation: Generate scenario-based tasks and ask models to execute them step-by-step, then score with a rubric.

If you want, I can also review the question generation/validation logic in code and propose a concrete leakage-proof template schema.
