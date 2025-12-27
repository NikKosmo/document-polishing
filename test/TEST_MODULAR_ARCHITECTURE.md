# Testing Modular Architecture

**Version:** 1.0
**Date:** 2025-12-27
**Purpose:** Test specification for modular document polishing architecture

---

## Overview

This document describes the testing approach for the modular architecture implementation. The system has been refactored to separate concerns into step modules, CLI scripts, and a refactored orchestrator.

**Goal:** Verify that modularization works correctly while maintaining 100% backward compatibility with the existing polish.py workflow.

---

## Test Approach

### 1. Unit Testing Phase

Test each step module independently to verify core functionality.

**Modules to test:**
- `scripts/src/extraction_step.py`
- `scripts/src/session_init_step.py`
- `scripts/src/testing_step.py`
- `scripts/src/detection_step.py`
- `scripts/src/reporting_step.py`

**Test focus:**
- Core functionality (extract, init, test, detect, generate)
- Save/load methods for Result dataclasses
- Error handling (FileNotFoundError, invalid input, etc.)
- Edge cases (empty documents, no ambiguities, judge failures)

**Test fixtures:**
Use existing test documents from `docs/test/`:
- `test_context_terms_definitions.md`
- `test_context_abbreviations_acronyms.md`

Create sample artifacts:
- `fixtures/sample_sections.json` (from extraction)
- `fixtures/sample_test_results.json` (from testing)
- `fixtures/sample_ambiguities.json` (from detection)

**Success criteria:**
- All unit tests pass
- 80%+ code coverage for step modules
- Save/load roundtrip works for all Result types

---

### 2. Integration Testing Phase

Test CLI scripts end-to-end to verify they work independently.

**Scripts to test:**
- `scripts/extract_sections.py`
- `scripts/init_sessions.py`
- `scripts/test_sections.py`
- `scripts/detect_ambiguities.py`
- `scripts/generate_report.py`

**Test scenarios:**

#### Scenario 1: Full pipeline using CLI scripts
```bash
# Extract
python extract_sections.py doc.md --workspace workspace/test --output sections.json

# Test (without sessions)
python test_sections.py workspace/test/sections.json --models claude --no-sessions --workspace workspace/test

# Detect
python detect_ambiguities.py workspace/test/test_results.json --workspace workspace/test

# Report
python generate_report.py workspace/test/test_results.json workspace/test/ambiguities.json \
    --document doc.md --workspace workspace/test
```

**Verify:**
- All artifacts created (sections.json, test_results.json, ambiguities.json, report.md)
- Exit codes: 0 for success, 1 for errors
- Error messages clear and helpful

#### Scenario 2: Partial pipeline (debug workflow)
```bash
# Re-run detection on existing test_results.json
python detect_ambiguities.py existing/test_results.json --workspace retry

# Re-generate report
python generate_report.py existing/test_results.json retry/ambiguities.json \
    --document doc.md --workspace retry
```

**Verify:**
- Can use existing artifacts
- No need to re-query models
- Output goes to new workspace

#### Scenario 3: CLI argument handling
```bash
# Missing required args → helpful error message
python extract_sections.py  # Should show usage

# Invalid file paths → clear error
python extract_sections.py nonexistent.md  # FileNotFoundError

# --workspace flag → creates directory, outputs to workspace
python extract_sections.py doc.md --workspace /tmp/test1
```

**Success criteria:**
- All integration tests pass
- CLI scripts chain correctly
- Error handling is robust
- --workspace parameter works

---

### 3. Regression Testing Phase

Test that refactored polish.py produces identical outputs to the original.

**Test approach:**

#### Baseline Comparison
```python
# Use existing workspace outputs as baseline
baseline_workspace = "workspace/polish_session_log_20251212_210941"

# Run refactored polish.py on same document
new_run = polish.py("../common_rules/session_log.md")

# Compare outputs:
assert new_workspace / "test_results.json" ≈ baseline / "test_results.json"
assert new_workspace / "ambiguities.json" == baseline / "ambiguities.json"
assert new_workspace / "report.md" ≈ baseline / "report.md"
```

**New artifacts to verify:**
- `sections.json` - Should contain extracted sections
- `session_metadata.json` - Should contain session IDs (if sessions enabled)

**Existing artifacts - must match:**
- `test_results.json` - Exact match (same models, same prompts)
- `ambiguities.json` - Exact match (same detection logic)
- `report.md` - Content match (formatting may differ slightly)
- `{doc}_polished.md` - Content match

**Test cases:**

1. **No ambiguities found**
   - Document: Use a clear, unambiguous document
   - Verify: ambiguities.json = [], no polished document created

2. **Multiple ambiguities found**
   - Document: Use `common_rules/document_structure.md` (known to have ambiguities)
   - Verify: All ambiguities detected, polished document created

3. **Judge failure handling**
   - Simulate judge timeout/error
   - Verify: Fail-fast behavior, clean error message, sessions cleaned up

4. **Session management**
   - With sessions enabled: Verify session_metadata.json created
   - With sessions disabled: Verify stateless mode works

**Success criteria:**
- All 73 existing tests still pass
- polish.py outputs match baseline (within acceptable variance)
- New artifacts (sections.json, session_metadata.json) created
- No regressions in functionality

---

### 4. Workflow Testing Phase

Test real-world usage patterns for the modular system.

#### Workflow 1: Debug failed run
```bash
# Initial run with judge failure
python polish.py doc.md  # Judge fails on section_3

# Debug: Re-run just detection with different judge
python detect_ambiguities.py workspace/run1/test_results.json --judge gemini --workspace workspace/debug

# Generate report from debug run
python generate_report.py workspace/run1/test_results.json workspace/debug/ambiguities.json \
    --document doc.md --workspace workspace/debug
```

**Verify:** Can debug without re-querying models (saves time/cost)

#### Workflow 2: Iterative prompt development
```bash
# Initial extraction
python extract_sections.py doc.md --workspace workspace/iter1

# Test with prompt v1
python test_sections.py workspace/iter1/sections.json --models claude --workspace workspace/iter1

# Edit prompt_generator.py to improve prompts

# Re-test with prompt v2 (reuses sections.json)
python test_sections.py workspace/iter1/sections.json --models claude --workspace workspace/iter2

# Compare results
diff workspace/iter1/test_results.json workspace/iter2/test_results.json
```

**Verify:** Can iterate on prompts efficiently

#### Workflow 3: Full polish workflow (baseline)
```bash
# Standard usage - should work exactly as before
python polish.py ../common_rules/todo.md --models claude,gemini

# Verify:
# - All 5 steps run
# - All artifacts created (including new sections.json, session_metadata.json)
# - Sessions work (if enabled)
# - Final output identical to before refactoring
```

**Success criteria:**
- All workflows execute successfully
- Debug workflow saves time (no model re-queries)
- Iterative workflow enables fast iteration
- Full workflow maintains backward compatibility

---

## Test File Structure

```
tests/
├── unit/
│   ├── test_extraction_step.py
│   ├── test_session_init_step.py
│   ├── test_testing_step.py
│   ├── test_detection_step.py
│   └── test_reporting_step.py
├── integration/
│   ├── test_cli_extract_sections.py
│   ├── test_cli_init_sessions.py
│   ├── test_cli_test_sections.py
│   ├── test_cli_detect_ambiguities.py
│   ├── test_cli_generate_report.py
│   └── test_cli_full_workflow.py
├── regression/
│   ├── test_polish_backward_compat.py
│   ├── test_polish_outputs.py
│   └── test_polish_edge_cases.py
├── workflow/
│   ├── test_debug_workflow.py
│   ├── test_iterative_workflow.py
│   └── test_modular_pipeline.py
└── fixtures/
    ├── sample_document.md
    ├── sample_sections.json
    ├── sample_test_results.json
    └── sample_ambiguities.json
```

---

## Implementation Guidelines

**For test authors:**

1. **Use pytest framework** - Standard Python testing tool
2. **Mock external dependencies** - Don't actually query models in unit tests
3. **Use fixtures** - Share test data across test files
4. **Test one thing at a time** - Unit tests should be focused
5. **Clear test names** - `test_extraction_step_handles_empty_document()`
6. **Assert expected behavior** - Not just "no exceptions"

**Testing philosophy:**
- **Unit tests:** Fast, isolated, mock dependencies
- **Integration tests:** Slower, use real CLI commands, verify file I/O
- **Regression tests:** Compare to baseline, verify no breaking changes
- **Workflow tests:** End-to-end scenarios, verify real-world usage

**Coverage goals:**
- Unit tests: 80%+ for step modules
- Integration tests: All CLI argument combinations
- Regression tests: 100% backward compatibility
- Workflow tests: All documented use cases

---

## Success Criteria Summary

✅ **All unit tests pass** (80%+ coverage for step modules)
✅ **All integration tests pass** (CLI scripts work standalone)
✅ **All 73 existing tests still pass** (no regressions)
✅ **polish.py outputs identical to baseline** (backward compatible)
✅ **CLI scripts successfully chain together** (full pipeline works)
✅ **Standalone detection works** (debug workflow functional)
✅ **New artifacts created** (sections.json, session_metadata.json)

---

## Running the Tests

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run with coverage
pytest --cov=src --cov-report=html tests/

# Run specific test file
pytest tests/unit/test_extraction_step.py

# Run specific test
pytest tests/unit/test_extraction_step.py::test_extract_from_document
```

---

## Notes for Implementation

- **Start with unit tests** - Easiest to write, fastest feedback
- **Use existing workspaces** - For baseline comparisons
- **Mock model queries** - Don't want tests to actually call models
- **Fixture management** - Create reusable test data
- **Parallel execution** - Use pytest-xdist for faster runs

**Key test data locations:**
- Existing workspaces: `scripts/workspace/polish_*`
- Test documents: `docs/test/*.md`
- Config: `scripts/config.yaml`

---

**Version History:**
- v1.0 (2025-12-27): Initial test specification
