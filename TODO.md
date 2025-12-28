# Document Polishing TODO

**Documentation ambiguity detection system tasks**

---

## Active

### Increment 2 - Ambiguity Detection (Polish)
- [P3] [ ] Review shared ambiguity severity calculation: should it use total participating models or only models that noted ambiguities? (Currently uses total participating models) `2025-12-28` #improvement #edge-case

### Other Active Tasks
- [P2] [ ] Test remaining context dependency documents (abbreviations, prerequisites, constraints, comprehensive) `2025-12-12` #testing #session-management

## Backlog

### Question-Based Testing Implementation (Incremental)
**Design:** docs/QUESTION_BASED_TESTING_FRAMEWORK.md | **Approach:** Sequential pipeline (Step 5), template-only generation, positive scenario first, 70%/60% coverage targets, JSON format

#### Phase 1: Core Infrastructure
- [P2] [ ] Create Question/Answer/Evaluation dataclasses in questioning_step.py module `2025-12-27` #question-testing #phase1
- [P2] [ ] Implement questions.json artifact format with save/load methods `2025-12-27` #question-testing #phase1 #artifacts
- [P2] [ ] Implement answers.json artifact format `2025-12-27` #question-testing #phase1 #artifacts
- [P2] [ ] Implement question_results.json artifact format `2025-12-27` #question-testing #phase1 #artifacts

#### Phase 2: Template Library & Section-Level Generation
- [P2] [ ] Create JSON template library (10-15 templates: factual, procedural, conditional) `2025-12-27` #question-testing #phase2
- [P2] [ ] Implement testable element extraction (requirements, steps, conditionals, constraints) `2025-12-27` #question-testing #phase2
- [P2] [ ] Implement template application logic for section-level questions `2025-12-27` #question-testing #phase2
- [P2] [ ] Implement question validation (answerable, grammatical, single concept) `2025-12-27` #question-testing #phase2
- [P2] [ ] Add section coverage metrics (target: 70%) `2025-12-27` #question-testing #phase2 #metrics

#### Phase 3: Document-Level Questions
- [P2] [ ] Build dependency graph from section cross-references `2025-12-27` #question-testing #phase3
- [P2] [ ] Identify potential conflict pairs between sections `2025-12-27` #question-testing #phase3
- [P2] [ ] Generate document-level questions (5-10 key questions: dependencies, conflicts, workflow) `2025-12-27` #question-testing #phase3
- [P2] [ ] Add element coverage metrics (target: 60%) `2025-12-27` #question-testing #phase3 #metrics

#### Phase 4: Answer Collection & Evaluation
- [P2] [ ] Implement model querying for questions (reuse session management) `2025-12-27` #question-testing #phase4
- [P2] [ ] Create LLM-as-Judge evaluation prompts `2025-12-27` #question-testing #phase4
- [P2] [ ] Implement judge response parsing (correct/partially_correct/incorrect/unanswerable) `2025-12-27` #question-testing #phase4
- [P2] [ ] Implement consensus calculation and issue detection `2025-12-27` #question-testing #phase4
- [P2] [ ] Convert QuestionResults to Ambiguity objects with severity mapping `2025-12-27` #question-testing #phase4

#### Phase 5: Integration & CLI
- [P2] [ ] Create questioning_step.py module (QuestioningStep class with generate/collect/evaluate) `2025-12-27` #question-testing #phase5 #modular
- [P2] [ ] Create CLI script: test_questions.py (generate, test, evaluate, auto commands) `2025-12-27` #question-testing #phase5 #cli
- [P2] [ ] Integrate questioning step into polish.py (after detection step) `2025-12-27` #question-testing #phase5 #integration
- [P2] [ ] Add question testing results to report.md (summary, issues, coverage) `2025-12-27` #question-testing #phase5 #reporting
- [P2] [ ] Add enable_question_testing config option `2025-12-27` #question-testing #phase5 #config

#### Phase 6: Adversarial Testing (Later - Separate Increment)
- [P2] [ ] Add adversarial templates (trick questions, edge cases, false premises) `#question-testing #adversarial #future
- [P2] [ ] Implement adversarial generation patterns `#question-testing #adversarial #future
- [P2] [ ] Implement adversarial evaluation criteria (passed/failed, failure modes) `#question-testing #adversarial #future
- [P2] [ ] Add adversarial pass rate metrics `#question-testing #adversarial #future

### Increment 2 - Other Polish Tasks
- [P2] [ ] Add adversarial/red-team prompt variant for interpretation testing `2025-12-01` #improvement #gemini-feedback

### Edge Cases (Return if issues recur)
- [P3] [ ] Handle models asking for clarification instead of following prompt format (e.g., section_20 in document_structure test - Claude responded with "I need to clarify the context here" instead of JSON) `2025-12-26` #edge-case #prompt-compliance
- [P3] [ ] Fix Gemini JSON parsing failure (section_7 in todo.md test - looks like valid JSON but failed to parse) `2025-12-26` #edge-case #gemini #parsing
- [P3] [ ] Investigate Gemini timeout issues (increase timeout or simplify prompts) `2025-12-26` #edge-case #gemini

### Increment 3 - Fix Generation
- [P2] [ ] Implement `fix_generator.py` with real fix strategies `2025-12-01` #increment3
- [P2] [ ] Implement `fix_applier.py` to modify documents `2025-12-01` #increment3
- [P2] [ ] Add iteration support (re-test after fixes) `2025-12-01` #increment3
- [P2] [ ] Implement agreement scoring (% of models that agree) `2025-12-01` #increment3
- [P2] [ ] Use model-reported ambiguities as input to fix generator `2025-12-06` #increment3 #leverage-data

### Increment 4 - Polish & Package
- [P3] [ ] Add FastEmbed strategy as optional optimization `2025-12-01` #optimization #optional
- [P3] [ ] Implement hybrid strategy (embeddings filter → LLM verify) `2025-12-01` #optimization
- [P3] [ ] Add readability scoring to prevent robotic writing `2025-12-01` #quality #gemini-feedback
- [P3] [ ] Create setup.py / pyproject.toml `2025-12-01` #packaging
- [P3] [ ] Create proper README.md with usage instructions `2025-12-01` #docs
- [P3] [ ] Add .env.example for API keys `2025-12-01` #packaging

## Completed

- [P2] [✓] Flag sections where models agree but both noted same ambiguity - Implemented shared ambiguity detection using LLM judge semantic understanding (not keyword matching) - Updated judge prompt to ask about shared concerns, added shared_ambiguities/shared_concerns fields to response, added third detection condition - Severity: MEDIUM for ≥3 models, LOW otherwise - Created 7 comprehensive tests - All 80 tests passing (73 original + 7 new) - 41 lines added to production code - Codex review: Approved with minor suggestions - PR #TBD `2025-12-28` #improvement #edge-case #llm-judge
- [P2] [✓] Modular Architecture Implementation - Created 5 step modules (extraction_step.py, session_init_step.py, testing_step.py, detection_step.py, reporting_step.py ~1,200 LOC), 5 CLI scripts (extract_sections.py, test_sections.py, detect_ambiguities.py, generate_report.py, init_sessions.py), refactored polish.py to use modules (~200 lines moved), created TEST_MODULAR_ARCHITECTURE.md - Enables debug workflows (re-run detection without model queries), iterative development (modify prompts, re-test), prepares for Increment 3 - All 73 tests passing, full backward compatibility maintained - New artifacts: sections.json, session_metadata.json - PR #22 `2025-12-27` #architecture #modularity #refactoring
- [P0] [✓] Fix critical gitignore failures discovered during PR #20 - **Root cause: Inline comments in .gitignore treated as literal pattern** - Pattern `SESSION_LOG.md      # comment` matched file "SESSION_LOG.md      # comment" (with spaces+comment), not actual file "SESSION_LOG.md" - In .gitignore, `#` only starts comment at line beginning, mid-line `#` is literal - **Fix: Moved all inline comments to separate lines** - All 4 issues traced to same root cause: (1) SESSION_LOG.md pattern had trailing spaces+comment, (2) workspace/** pattern had trailing spaces+comment, (3) CI was actually working correctly (patterns genuinely broken), (4) PyCharm correctly showed as non-ignored - **Investigation: Dual analysis (Claude Explore agent + Codex CLI)** independently confirmed same root cause - **Verification: All patterns now work** - git check-ignore returns exit 0, patterns match correctly, files properly ignored - PR #21 `2025-12-26` #critical #gitignore #investigation
- [P1] [✓] Include original document in workspace - Added shutil.copy2() to copy original document to workspace as `original_{filename}` for easy reference - Added logging and display in summary output - All 73 tests passing `2025-12-26` #ux #workspace
- [P2] [✓] Remove "Detailed Test Results" section from report.md - Removed expandable details section with raw model responses - Replaced with simple note pointing to test_results.json - Reduces context waste (reports mainly read by AI models), removes duplication - All 73 tests passing `2025-12-26` #optimization #context-efficiency
- [P3] [✓] Simplify test matrix to Python 3.11 only - Removed multi-version testing (3.8-3.11) for 4x faster CI - This is a personal tool, no need for broad version compatibility - PR #14 `2025-12-13` #ci #optimization
- [P2] [✓] Fix gitignore patterns for workspace/temp/output - Changed patterns from workspace/ to **/workspace/ to match directories anywhere in tree - Fixed issue where scripts/workspace/ was not being ignored - PR #15 `2025-12-13` #bug #gitignore
- [P2] [✓] Add mandatory git workflow check to CLAUDE.md - Added requirement to read common_rules/git_workflow.md before any git command - Added critical note to git_workflow.md header - Prevents future git mistakes `2025-12-13` #process #git
- [P0] [✓] Add GitHub Actions check to prevent gitignore violations - Created .github/workflows/check-gitignore.yml with two-stage validation (gitignore patterns + sensitive files) - Checks files with --diff-filter=ACMRT, uses git check-ignore for validation - Fails CI if gitignored files detected, warns on sensitive patterns - Will prevent future violations like PR #11 `2025-12-13` #critical #ci #github-actions #prevention
- [P0] [✓] Fix fail-fast violation when judge fails - Implemented JudgeFailureError exception, stops immediately on judge failure instead of continuing with false ambiguities - Added comprehensive error handling in polish.py and ambiguity_detector.py - Created 12 new tests (all 73 tests passing) - System now exits cleanly with clear error message when judge times out or returns invalid response `2025-12-13` #bug #critical #fail-fast #judge
- [P1] [✓] Fix Gemini session creation to use "latest" instead of parsing session list `2025-12-12` #bug #gemini #session-management
- [P0] [✓] Implement and test session management for document context `2025-12-12` #feature #session-management #context
- [P1] [✓] Fix chunking logic to handle markdown code fences correctly `2025-12-11` #bug #chunking #data-quality
- [P1] [✓] Filter out faulty/empty interpretations before sending to judge `2025-12-10` #bug #judge #data-quality
- [P1] [✓] Include model-reported ambiguities in judge prompt `2025-12-10` #improvement #judge #data-quality
- [P1] [✓] Add GitHub Actions CI workflow for automated testing `2025-12-10` #devops #ci #testing
- [P1] [✓] Fix LLM-as-Judge response parsing (handle already-parsed JSON format) `2025-12-06` #bug #increment2 #parsing
- [P1] [✓] Test Increment 2 with real documentation (common_rules/todo.md - found 0 ambiguities) `2025-12-06` #testing #increment2
- [P1] [✓] Fix JSON parsing for Claude/Gemini markdown-wrapped responses `2025-12-06` #bug #parsing
- [P1] [✓] Remove default config fallback (fail fast if config not found) `2025-12-06` #refactor #explicit-config
- [P1] [✓] Add progress logging to workspace directory `2025-12-06` #ux #logging
- [P1] [✓] Increment 1 - Core system working `2025-11-30` #increment1
- [P1] [✓] Cleanup temp files and remove outdated/unused files `2025-11-30` #cleanup
- [P1] [✓] Reorganize project structure `2025-11-30` #refactor
- [P1] [✓] Test Increment 1 with real CLI tools `2025-12-01` #testing #increment1
- [P1] [✓] Create `ambiguity_detector.py` module with pluggable strategies `2025-12-01` #increment2
- [P1] [✓] Research sentence embeddings options (Gemini) `2025-12-01` #research
- [P1] [✓] Integrate `ambiguity_detector.py` into `polish.py` `2025-12-01` #increment2 #integration
- [P1] [✓] Wire up LLM-as-Judge strategy (claude as judge) `2025-12-01` #increment2 #core
- [P1] [✓] Add document name to output folder `2025-12-01` #ux #quick-win

## Blocked

(No blockers)

## Someday/Maybe

- [P3] [ ] Parallel model queues (process all chunks per model independently to avoid blocking on slow models) `#optimization #performance`
- [P3] [ ] "Realistic reading" test mode - feed whole document, test what model actually follows vs skips `#research #future-tool`
- [P3] [ ] Document real-world use cases and examples `#docs`
- [P3] [ ] Create demo video/walkthrough `#docs #marketing`
- [P3] [ ] Add "When NOT to use this tool" section to docs `#docs #gemini-feedback`
- [P3] [ ] API model support (OpenAI, Anthropic direct) `#feature`
- [P3] [ ] Web UI for reports `#feature`

---

## Research Findings (Reference)

### Embedding Options (from Gemini research 2025-12-01)
| Option | Install Size | Speed (CPU) | Best For |
|--------|--------------|-------------|----------|
| FastEmbed | ~150MB | ~20ms/pair | Production use |
| sentence-transformers | ~600MB+ | ~30ms/pair | If PyTorch already installed |
| OpenAI API | <10MB | ~300ms | Zero local setup |
| LLM-as-Judge | <10MB | ~1-2s | Highest accuracy, low volume |

**Decision:** Start with LLM-as-Judge (no new deps, catches semantic contradictions). Add FastEmbed later as optimization if needed.

### Hybrid Strategy (Future)
```
If similarity > 0.95 → Agree (skip LLM)
If similarity < 0.6  → Disagree (skip LLM)
If 0.6 - 0.95        → Ask LLM to verify
```

---

**See `../common_rules/todo.md` for format guidelines**
