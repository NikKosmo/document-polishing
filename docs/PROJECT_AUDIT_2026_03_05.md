# Document Polishing System — Project Audit

**Date:** 2026-03-05
**Branch:** `fix/cli-prompt-guard` (2 commits ahead of `main`)
**Tests:** 132/132 passing (Python 3.12, pytest)
**Code:** 5,014 LOC production (scripts/src/) + 2,942 LOC tests

---

## 1. Code State — What Is Implemented

### 1.1 Source Modules (`scripts/src/`)

| Module | LOC | Purpose | Status |
|--------|-----|---------|--------|
| `questioning_step.py` | 2,006 | Question generation, cross-ref analysis, conflict detection, answer collection, evaluation, consensus | Phase 1-5 classes exist. Templates generate 0 valid questions (answer leakage). Not wired into polish.py. |
| `ambiguity_detector.py` | 665 | LLM-as-Judge ambiguity detection with fail-fast | Working, production-ready |
| `session_handlers.py` | 316 | CLI subprocess wrappers for claude/gemini/codex | Working. Has nohooks guard (on `fix/cli-prompt-guard` branch) |
| `detection_step.py` | 306 | Step 4: Ambiguity detection step module | Working |
| `reporting_step.py` | 303 | Step 5: Report + polished doc generation | Working |
| `session_manager.py` | 241 | Session lifecycle management | Working |
| `testing_step.py` | 241 | Step 3: Test sections with models | Working. Supports `--resume` for crash recovery |
| `model_interface.py` | 235 | ModelManager — routes queries to CLI models | Working. Has nohooks guard (on `fix/cli-prompt-guard` branch) |
| `session_init_step.py` | 220 | Step 2: Initialize model sessions with doc context | Working |
| `extraction_step.py` | 165 | Step 1: Extract sections from markdown | Working |
| `document_processor.py` | 163 | Markdown parsing with code fence handling | Working |
| `prompt_generator.py` | 150 | Interpretation prompt generation | Working |
| `__init__.py` | 3 | Package init | — |

### 1.2 CLI Scripts (`scripts/`)

| Script | Purpose | Status |
|--------|---------|--------|
| `polish.py` | Main orchestrator (Steps 1-5) | Working — does NOT include questioning step |
| `extract_sections.py` | Standalone section extraction | Working |
| `init_sessions.py` | Standalone session init | Working |
| `test_sections.py` | Standalone section testing | Working |
| `detect_ambiguities.py` | Standalone ambiguity detection | Working |
| `generate_report.py` | Standalone report generation | Working |
| `generate_questions.py` | Question generation CLI | Working (generates questions, but templates broken) |
| `test_questions.py` | Question testing CLI (generate/test/evaluate/auto) | Implemented, untested with real models (templates broken) |
| `strip_metadata.py` | Strip @meta/@assertion from bulky docs | Working (127 LOC, state machine, no regex) |

### 1.3 Test Files (`tests/`)

| Test File | Count | Coverage |
|-----------|-------|----------|
| `test_questioning_step.py` | 47 | Phase 1-2 classes only. Zero tests for Phase 3-5 (CrossReferenceAnalyzer, ConflictDetector, AnswerCollector, AnswerEvaluator, ConsensusCalculator) |
| `test_session_management.py` | 34 | Session init, context injection, lifecycle |
| `test_judge_fail_fast.py` | 12 | Judge failure handling |
| `test_document_processor_code_fences.py` | 8 | Code fence parsing |
| `test_filter_faulty_interpretations.py` | 9 | Empty/faulty interpretation filtering |
| `test_shared_ambiguity_detection.py` | 7 | Shared ambiguity (models agree but both note same concern) |
| `test_judge_prompt_content.py` | 7 | Judge prompt formatting |
| `test_intermediate_saves.py` | 5 | Partial result saving + resume |
| `test_cli_model_current_behavior.py` | 3 | CLI model subprocess behavior |
| **Total** | **132** | All passing |

### 1.4 Pipeline Architecture (as implemented in `polish.py`)

```
Step 1: Extract sections (extraction_step.py)
Step 2: Initialize sessions with full doc context (session_init_step.py) [optional]
Step 3: Test sections — each section sent to N models for interpretation (testing_step.py)
Step 4: Detect ambiguities — LLM-as-Judge compares interpretations (detection_step.py)
Step 5: Generate report + polished doc (reporting_step.py)

NOT integrated: questioning_step.py, strip_metadata.py
```

---

## 2. Branch State

### Current Branch: `fix/cli-prompt-guard`

**Local `main` is 1 commit behind `origin/main`** — needs `git pull` to pick up `25c6d66`.

After pulling, `fix/cli-prompt-guard` has 1 commit not on main:
- `5d074cc` — Use `~/.config/nohooks` dir for all LLM CLI subprocesses

(Commit `25c6d66` "Add CLI prompt guard" is already on `origin/main` — likely pushed directly.)

Files changed vs origin/main: `model_interface.py`, `session_handlers.py` (nohooks cwd pattern)

**This branch has real unmerged work.** The nohooks pattern prevents PAI Algorithm format from being injected into LLM CLI subprocess calls. This is a cross-project pattern also used in loom, german, and english projects.

### Other Branches: All Squash-Merged (Stale)

All other local branches were squash-merged into `main`. They show as "NOT merged" because git doesn't recognize squash-merge as an ancestor relationship, but their content is fully present on `main`:

| Branch | Main Commit | Status |
|--------|-------------|--------|
| `feature/intermediate-result-saving` | `ee7dd7e` | Content on main |
| `refactor/step-numbering` | `aa974ce` | Content on main |
| `hygiene/audit-fixes-and-linting` | `0a109c8` | Content on main |
| `docs/agents-md-parent-requirement` | `c4f3618` | Content on main |
| `feature/bulky-clean-week1` | `81cd979` | Content on main |
| `feature/bulky-clean-architecture` | `5e14a26` | Content on main |
| `feature/question-based-testing-phase1-2` | `be08b9b` | Content on main |
| `feat/question-based-testing-phase2` | `2acbc0a` | Content on main |
| `feat/shared-ambiguity-detection` | `ff8621b` | Content on main |
| `docs/question-based-testing-framework` | `9f0f9e4` | Content on main |
| + 13 more older branches | — | All content on main |

**These branches can be safely deleted.** They serve no purpose since their changes are already in `main` via squash-merge.

### Remote Branches

Only 3 remote branches exist:
- `origin/main` — primary
- `origin/fix/cli-prompt-guard` — current work
- `origin/feature/add-gitignore-check` — stale (content on main)
- `origin/feature/bulky-clean-architecture` — stale (content on main)

---

## 3. What Was Done — The Two Approaches

### 3.1 Core Pipeline: Multi-Model Perception (Working)

**Status:** Fully implemented and working.

The interpretation-based approach sends each section to multiple LLMs, collects their interpretations, and uses LLM-as-Judge to find disagreements. This is the `polish.py` pipeline (Steps 1-5).

Key capabilities:
- Session management maintains full doc context across queries (67% ambiguity reduction demonstrated)
- Shared ambiguity detection (models agree but both note the same concern)
- Fail-fast on judge errors
- Intermediate result saving with `--resume`
- Modular architecture — each step runs standalone via CLI

### 3.2 Question-Based Testing Framework (Implemented but Templates Broken)

**Status:** Code exists for all 5 phases. Templates generate 0 valid questions.

**Phase 1-2 (Section-Level Questions):** Implemented and tested (47 tests).
- `ElementExtractor` — 8 regex patterns to find testable elements in sections
- `TemplateApplicator` — 14 section-level templates + 4 document-level templates
- `QuestionValidator` — 4 validation rules (leakage, length, answerability, uniqueness)
- **Problem:** Templates put answer text in questions → 100% answer leakage → validator rejects all questions

**Phase 3 (Document-Level Questions):** Implemented, zero tests.
- `CrossReferenceAnalyzer` — builds dependency graph from section cross-references
- `ConflictDetector` — finds contradictory requirements between sections

**Phase 4 (Answer Collection & Evaluation):** Implemented, zero tests.
- `AnswerCollector` — queries models with questions, reuses sessions
- `AnswerEvaluator` — LLM-as-Judge scores answers (correct/partially_correct/incorrect/unanswerable)
- `ConsensusCalculator` — determines consensus type (agreement/partial/disagreement/widespread_failure)

**Phase 5 (CLI):** Implemented.
- `test_questions.py` — 4 commands (generate/test/evaluate/auto)
- **NOT wired into polish.py** — question testing and interpretation testing are separate workflows

**The idea behind questioning:**
The interpretation testing (current pipeline) catches HOW models understand text, but not WHETHER they can correctly USE that understanding. Questions test:
1. Specific comprehension (section-level): "What is the default timeout value?"
2. Holistic understanding (document-level): "What must be completed before Step 3?"
3. Conflict detection: "How do Section A and Section B differ on X?"

**Expert reviews** (3 rounds × 3 models = 9 reviews in `docs/question_testing/expert_reviews/`) recommended:
- Use `@assertion` markers to define testable claims in source docs
- Hybrid approach: templates (80%) + LLM generation (20%)
- Question patterns that test comprehension, not mere mention

### 3.3 Bulky-Clean Document Architecture (Implemented, Not Integrated)

**Status:** Strip script works. Week 1 exercises completed. Not wired into polish.py.

**Concept:** Source/build system for documentation:
- **Bulky docs** (`docs/bulky/`): Source of truth with `@meta` blocks and `@assertion` markers
- **Clean docs** (`docs/clean/`): Stripped versions for LLM consumption
- **Transform:** `strip_metadata.py` — deterministic line-by-line state machine, no regex

**What exists:**
- `scripts/strip_metadata.py` (127 LOC) — working, tested
- `docs/bulky/git_workflow.md` — v1 with @meta + 7 assertions
- `docs/bulky/git_workflow_v2.md` — v2 with 8 assertions (corrected based on agentic research)
- `docs/bulky/BULKY_FORMAT_GUIDE.md` — comprehensive authoring guide (800+ lines)
- `docs/clean/git_workflow.md` — stripped v1
- `docs/clean/git_workflow_v2.md` — stripped v2
- `docs/clean/git_workflow_v3.md` — a third version (281 lines)
- `docs/clean/git_workflow_v3.1.md` — a 3.1 version (281 lines)

**Week 1 exercises completed (from TODO.md):**
1. ✓ Create bulky version of git_workflow.md
2. ✓ Build strip_metadata.py
3. ✓ Manual question writing — pivoted to full research approach, 24 tests run, validated bulky-clean works (cold: 13%, old doc: 13%, new doc: 88% correct)
4. ✓ Authoring guide (BULKY_FORMAT_GUIDE.md)

**Not done:**
- Week 2: Question template implementation from @assertion markers
- Week 3: Integration into polish.py
- The bridge between bulky-clean and questioning_step.py doesn't exist yet

---

## 4. Documentation State

### 4.1 Documents Aligned With Current Code

| Document | Location | Why Aligned |
|----------|----------|-------------|
| `AGENTS.md` (v0.3.0) | Root | Matches current modular architecture, CLI commands, project structure |
| `TODO.md` | Root | Accurate task tracking, completed items match code state |
| `AMBIGUITY_DETECTION_CLARIFICATIONS.md` | `docs/` | Design decisions for Increment 2 — still relevant |
| `CONTEXT_INJECTION_OPTIONS.md` | `docs/` | Documents session management approach — still relevant |
| `BULKY_FORMAT_GUIDE.md` | `docs/bulky/` | Matches strip_metadata.py behavior exactly |
| `BULKY_CLEAN_ARCHITECTURE_PLAN.md` | `docs/question_testing/plans/` | Active plan, Week 1 completed, Weeks 2-3 pending |
| `IMPLEMENTATION_REVIEW.md` | `docs/question_testing/` | Accurate Phase 3-5 review, bug status matches code |
| `BUG_FIXES.md` | `docs/question_testing/` | All 3 bugs fixed as documented |
| `REGEX_LIMITATIONS.md` | `docs/question_testing/` | Analysis of 8 regex patterns in ElementExtractor — still valid |
| Expert reviews (Part 1-3) | `docs/question_testing/expert_reviews/` | Reference material, recommendations still applicable |
| Test docs | `docs/test/` | Active test fixtures and procedures |

### 4.2 Documents Conflicting With Current Code

| Document | Location | Conflict |
|----------|----------|----------|
| `README.md` | Root | **Outdated.** References old commands, doesn't reflect modular architecture. AGENTS.md is authoritative. |
| `docs/question_testing/README.md` | `docs/question_testing/` | Says "127/127 tests passing" — now 132/132. Says "templates fundamentally broken" — still true, but minor version discrepancy. |
| `PROJECT_STATUS_ANALYSIS.md` | `docs/` | Dated 2025-12-27. Says "73 tests passing" — now 132. Roadmap dates in Q1/Q2 2025 are clearly wrong (should be 2026). Status of some items outdated (modular architecture marked "in progress" but completed). |

### 4.3 Outdated Document Versions

| File | Location | Issue |
|------|----------|-------|
| `git_workflow.md` | `docs/clean/` | v1 — original with known errors. `git_workflow_v2.md` is the corrected version. Both kept as test artifacts but can confuse. |
| `git_workflow_v3.md` | `docs/clean/` | No corresponding bulky version exists. Origin unclear — possibly manually created. |
| `git_workflow_v3.1.md` | `docs/clean/` | No corresponding bulky version exists. Origin unclear. |
| `QUESTION_TESTING_PHASE1_PHASE2_PLAN.md` | `docs/question_testing/plans/archived/` | Correctly archived — Phase 1-2 completed. |
| `QUESTION_TESTING_PHASE3_4_5_PLAN.md` | `docs/question_testing/plans/archived/` | **Improperly archived.** Phase 3-5 code exists but has zero tests and broken templates. This plan is still the reference for completing the work. Should NOT be in `archived/`. |

### 4.4 Archived Documents Assessment

**`docs/archive/early-design/`** — 7 files:

| File | Assessment |
|------|------------|
| `DOCUMENTATION_POLISHING_WORKFLOW.md` | Correctly archived — describes theoretical 9-step process, actual implementation is 5-step |
| `DOCUMENTATION_POLISHING_IMPLEMENTATION.md` | Correctly archived — pre-implementation pseudo-code |
| `DOCUMENTATION_POLISHING_QUICK_REFERENCE.md` | Correctly archived — references commands that don't exist |
| `README.md` | Correctly archived — old README for early design docs |
| `prompt.md` | Correctly archived — task description for external model |
| `gemini_feedback.md` | Correctly archived — historical early feedback |
| `gemini_sentence_embeddings_research.md` | Correctly archived — early research on embeddings approach |

**Verdict:** Archive is mostly correct. One exception noted above: `QUESTION_TESTING_PHASE3_4_5_PLAN.md` is in `plans/archived/` but shouldn't be.

### 4.5 Documents That Are Artifacts (Prompts, Reviews)

The `docs/question_testing/` directory contains a mix of design docs and artifacts:

**Design docs (reference):**
- `FRAMEWORK.md` (69K) — comprehensive framework spec, still the vision document
- `INITIAL_DESIGN_PROMPT.md` — the prompt that generated FRAMEWORK.md
- `BULKY_CLEAN_ARCHITECTURE_PLAN.md` — active plan

**Implementation artifacts:**
- `IMPLEMENTATION_REVIEW.md` — code review findings
- `BUG_FIXES.md` — bug fix log
- `REGEX_LIMITATIONS.md` — regex pattern analysis

**Expert review artifacts (prompts + responses):**
- `expert_reviews/PART1_PROMPT.md` + `PART1_CLAUDE.md` + `PART1_CODEX.md` + `PART1_GEMINI.md`
- `expert_reviews/PART2_PROMPT.md` + `PART2_CLAUDE.md` + `PART2_CODEX.md` + `PART2_GEMINI.md`
- `expert_reviews/PART3_PROMPT.md` + `PART3_CLAUDE.md` + `PART3_CODEX.md` + `PART3_GEMINI.md`
- `EXPERT_REVIEW_PART2_COMPARATIVE_ANALYSIS.md` (88K)
- `EXPERT_REVIEW_PART3_COMPARATIVE_ANALYSIS.md` (56K)

These are valuable reference material but inflate the docs directory. They document the thinking behind the @assertion approach and template redesign recommendations.

### 4.6 Temp Files

`temp/` contains work products from bulky-clean Week 1 exercises:
- `agentic_git_research.md` — git best practices research
- `generated_questions_based_on_workflow.md` — manually crafted questions
- `full_test_analysis.md` — comprehensive 400-line test results analysis
- `test_results/` (24 files) — raw model responses from exercise 3
- `run_question_tests.sh` — test runner script
- Session state files from Junie tasks

These are correctly in `temp/` — work artifacts, not reference docs.

---

## 5. The Options for Questioning — What Was Considered

### Option A: Template-Based Questions from Sections (Current, Broken)

The `questioning_step.py` approach: extract testable elements from sections using regex, apply templates to generate questions, validate questions. **Problem:** Template design causes answer leakage. Fixing templates is the main blocker.

**What would fix it:** Redesign templates per expert Part 2 recommendations — question patterns that test comprehension, not mention. Example: instead of "Does it mention {answer}?" → "Given scenario X, what should happen?" The infrastructure (Question dataclass, validator, CLI) all works — just the templates need redesign.

### Option B: Questions from @assertion Markers (Bulky-Clean Bridge)

The Week 2-3 plan: extract `@assertion` markers from bulky docs, generate questions from assertion content. The assertion already states the testable claim, so question generation is more reliable than regex element extraction.

**What exists:** `strip_metadata.py` can parse assertions. Bulky docs have assertions. But no template engine maps assertions → questions yet.

### Option C: Full-Document Questions (What Nik Discussed)

Send the full document to models and ask targeted questions about the entire document, rather than section-by-section interpretation testing. This would be an **additional step** alongside the existing pipeline:

1. Steps 1-5 (existing pipeline): section-by-section interpretation → ambiguity detection
2. **New step:** Full-document questioning → comprehension verification

The `AnswerCollector` in Phase 4 of `questioning_step.py` already supports this pattern — it uses sessions (full doc context) to ask questions. The infrastructure exists; the question source is the missing piece.

### Option D: Hybrid (Expert Recommended)

Templates handle 80% of questions (from @assertion markers or section elements). LLM generates the remaining 20% for complex cross-reference and inference questions. This is the expert consensus from all 3 review rounds.

---

## 6. Summary

### What Works Now
- Multi-model interpretation testing pipeline (polish.py) — production-ready
- 132 tests, modular architecture, session management, crash recovery
- Strip metadata script for bulky → clean transform

### What's Implemented But Not Working
- Question templates (100% answer leakage, 0 valid questions generated)

### What's Implemented But Not Integrated
- Question-based testing (Phases 1-5 exist in code, not wired into polish.py)
- Bulky-clean strip pipeline (exists, not wired into polish.py)
- `fix/cli-prompt-guard` branch (nohooks pattern, not merged to main)

### What's Planned But Not Started
- Template redesign (from @assertion markers or improved patterns)
- Week 2-3 of bulky-clean plan (assertion→question bridge)
- Phase 3-5 tests (0 tests for 5 classes totaling ~750 LOC)
- Full-document questioning as additional pipeline step
- Increment 3 (fix generation)
- Increment 4 (packaging)

### Key Decisions Pending
1. **Template fix strategy:** Redesign existing templates vs generate from @assertion markers vs LLM-generated questions
2. **Integration approach:** Add questioning as Step 6 in polish.py vs keep as separate workflow
3. **Branch cleanup:** Merge `fix/cli-prompt-guard`, delete stale branches
4. **Doc cleanup:** Move `PHASE3_4_5_PLAN.md` out of archived, decide on orphan clean versions
