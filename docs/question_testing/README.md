# Question-Based Testing Framework - Documentation

This directory contains all documentation related to the Question-Based Testing Framework for LLM documentation comprehension.

## Overview

The Question-Based Testing Framework tests LLM comprehension of documentation by:
1. Generating questions from documentation sections
2. Collecting answers from multiple LLM models
3. Evaluating answers using LLM-as-Judge
4. Detecting ambiguities through model disagreement

## Documentation Structure

### Core Documents

- **[FRAMEWORK.md](./FRAMEWORK.md)** - Complete framework design specification
  - Motivation and goals
  - Question taxonomy (7 types)
  - Answer evaluation methodology
  - Integration with polishing pipeline
  - Implementation phases (1-5)

- **[IMPLEMENTATION_REVIEW.md](./IMPLEMENTATION_REVIEW.md)** - Phase 3-5 implementation review
  - Architecture analysis (5 new classes)
  - Bug report (all bugs fixed as of 2025-12-29)
  - Code quality assessment
  - Test coverage analysis
  - Real-world testing results

- **[BUG_FIXES.md](./BUG_FIXES.md)** - Summary of bug fixes (2025-12-29)
  - Bug #1: KeyError in ConflictDetector (FIXED)
  - Bug #2: CLI --document-level flag (FIXED)
  - Bug #3: CLI --session parameter (FIXED)
  - Automatic session management integration

- **[INITIAL_DESIGN_PROMPT.md](./INITIAL_DESIGN_PROMPT.md)** - Original design prompt (2025-12-27)
  - Expert design task specification
  - Research areas and industry standards
  - Two-level testing strategy (section + document)
  - Adversarial testing requirements
  - This prompt led to the creation of FRAMEWORK.md

- **[REGEX_LIMITATIONS.md](./REGEX_LIMITATIONS.md)** - Regex pattern analysis (2025-12-28)
  - What works well vs. what doesn't
  - 8 regex patterns with examples
  - Common false positives
  - Recommendations for document_structure.md
  - Coverage metrics and implementation notes

### Expert Reviews

Two rounds of expert panel reviews from multiple AI models (Codex, Gemini, Claude):

#### Part 1: Framework Review
**Location:** `expert_reviews/PART1_*.md`

Reviews of initial implementation focusing on:
- Educational assessment principles
- Technical communication best practices
- NLP/LLM evaluation methodologies
- Cognitive psychology insights
- Software architecture

**Files:**
- `PART1_PROMPT.md` - Review prompt sent to experts
- `PART1_CODEX.md` - OpenAI Codex response (917 lines)
- `PART1_GEMINI.md` - Google Gemini response
- `PART1_CLAUDE.md` - Anthropic Claude response

#### Part 2: LLM-Optimized Documentation Design
**Location:** `expert_reviews/PART2_*.md`

Reviews of integrated approach linking:
- Documentation format design
- Structure-based question generation
- Testability-first documentation

**Files:**
- `PART2_PROMPT.md` - Review prompt for integrated approach
- `PART2_CODEX.md` - OpenAI Codex response (1,411 lines)
- `PART2_GEMINI.md` - Google Gemini response (186 lines)
- `PART2_CLAUDE.md` - Anthropic Claude response (2,307 lines)

**Key Insights from Part 2:**
- Use `@assertion` markers in markdown for testable claims
- Hybrid generation: templates (80%) + LLM (20%)
- Test-Driven Documentation (TDD) for LLMs
- Integration with existing `document_structure.md`

### Implementation Plans

**Location:** `plans/` (if any phase plans exist)

Original implementation plans for Phases 1-5.

## Current Status

**Date:** 2025-12-29

### Completed

✅ **Phases 1-2:** Question generation (template-based)
- Question dataclass, validation rules
- Element extraction (8 patterns)
- Template application
- Coverage calculation
- 47 tests, all passing

✅ **Phases 3-5:** Document-level analysis + Answer evaluation + CLI
- CrossReferenceAnalyzer, ConflictDetector
- AnswerCollector, AnswerEvaluator, ConsensusCalculator
- CLI with 4 commands (generate, test, evaluate, auto)
- All bugs fixed, 127/127 tests passing

✅ **Automatic session management** integrated

### Issues

⚠️ **Templates fundamentally broken**
- Current templates generate 0 valid questions (100% answer leakage)
- Root cause: Templates put answer text in questions
- Example: Q: "Does it mention '{answer}'?" A: "{answer}"
- **Action:** Template redesign needed (see expert reviews Part 2)

❌ **Missing tests for Phase 3-5**
- 0 tests for CrossReferenceAnalyzer, ConflictDetector
- 0 tests for AnswerCollector, AnswerEvaluator, ConsensusCalculator
- Plan called for 43 additional tests

### Next Steps (Based on Expert Reviews)

1. **Redesign templates** using expert recommendations:
   - Use `@assertion` markers (Part 2 reviews)
   - Hybrid approach: templates + LLM generation
   - Question patterns that test comprehension, not mention

2. **Extend document structure** for testability:
   - Add assertion types (requirement, constraint, behavior, etc.)
   - Make testable elements explicit
   - Integrate with existing `common_rules/document_structure.md`

3. **Add Phase 3-5 tests** (minimum 25 tests)

4. **Validate with real documents**

5. **Integrate with polish.py pipeline**

## Key Files for Implementation

### Current Implementation
- `scripts/src/questioning_step.py` (2,009 lines)
- `scripts/test_questions.py` (363 lines)
- `scripts/templates/question_templates.json` (376 lines)
- `tests/test_questioning_step.py` (47 tests)

### Related Documentation
- `common_rules/document_structure.md` - Current doc structure standard
- `docs/PROJECT_STATUS_ANALYSIS.md` - Overall project status

## Expert Panel Recommendations Summary

### From Part 1 (Framework Review)

**Educational Assessment:**
- Fix template answer leakage (critical)
- Add item response theory validation
- Use rubrics instead of binary scoring

**Technical Communication:**
- Add human validation benchmark
- Implement task-based validation questions
- Connect to established readability metrics

**NLP/LLM Evaluation:**
- Implement hybrid question generation (templates + LLM)
- Add judge calibration and cross-validation
- Create gold-standard validation corpus

**Cognitive Psychology:**
- Add paraphrase/transfer questions for deep comprehension
- Implement inference chain questions
- Test situation model through scenario application

**Software Architecture:**
- Split 2,000+ line file into modules
- Define explicit section schema with validation
- Add comprehensive Phase 3-5 tests (critical blocker)

### From Part 2 (LLM-Optimized Documentation)

**Core Recommendation:** Extend existing `document_structure.md` with `@assertion` markers

**Documentation Format:**
```markdown
<!-- @assertion id="req_01" type="requirement" -->
All fields must be validated before processing.
<!-- @/assertion -->
```

**Question Generation Workflow:**
1. Extract assertions (100% automated)
2. Template matching (80% coverage)
3. LLM generation for complex cases (20%)
4. Automated validation
5. Human review (10-15 min per doc)

**MVP Implementation (Week 1):**
- Add @assertion markers to 1 critical workflow
- Build parser to extract assertions
- Implement 3 template rules
- Generate and manually validate questions

**Success Metrics:**
- Template success rate > 80%
- Question validation rate > 90%
- Coverage > 80% of sections
- Overhead < 15% on doc writing time

## References

### External Standards
- SQuAD 2.0 (reading comprehension dataset)
- Bloom's Taxonomy (comprehension levels)
- DITA (information typing)

### Related Research
- Automatic Question Generation (NLP)
- LLM-as-Judge evaluation
- Reading comprehension assessment
- Technical documentation testing

---

**Last Updated:** 2025-12-29
**Status:** Implementation complete, templates need redesign
