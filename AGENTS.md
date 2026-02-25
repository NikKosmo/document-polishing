
# Document Polishing System - Technical Guide

**Version:** 0.3.0 (Active Development - Modular Architecture Complete)

**Multi-project workspace:** This project is part of a larger workspace. If `../AGENTS.md` exists, **you MUST read it before proceeding** — it contains cross-project standards and shared rules (`common_rules/`).

## Purpose

Automated tool that detects ambiguities in documentation by testing it with multiple AI models and identifying where interpretations differ.

## Core Concept

Test documentation → Compare model interpretations → Detect disagreements → Generate fixes → Validate consistency

## Quick Commands

### Full Polish Workflow (Primary)
```bash
# Polish a document
cd scripts && python3 polish.py ../test/test_simple.md

# Use specific models/profile
cd scripts && python3 polish.py document.md --models claude,gemini --profile thorough

# List models and version
cd scripts && python3 polish.py --list-models
cd scripts && python3 polish.py --version
```

### Modular Workflow (Advanced)
```bash
# Extract sections
cd scripts && python3 extract_sections.py doc.md --workspace ws/run1

# Test sections
cd scripts && python3 test_sections.py ws/run1/sections.json --models claude,gemini --workspace ws/run1

# Detect ambiguities
cd scripts && python3 detect_ambiguities.py ws/run1/test_results.json --workspace ws/run1

# Generate report
cd scripts && python3 generate_report.py ws/run1/test_results.json ws/run1/ambiguities.json \
    --document doc.md --workspace ws/run1
```

### Debug Workflow
```bash
# Re-run detection without re-querying models
cd scripts && python3 detect_ambiguities.py ws/failed/test_results.json \
    --judge gemini --workspace ws/retry
```

### Quality Checks (run before committing)
```bash
# Linting
ruff check scripts/src/ scripts/*.py tests/

# Tests
pytest tests/ -v --tb=short
```

## Project Structure

```
document_polishing/
├── AGENTS.md              # This file - AI assistant technical guide
├── CLAUDE.md              # Redirect to AGENTS.md (for Claude Code compatibility)
├── README.md              # User overview
├── SESSION_LOG.md         # Development history
├── TODO.md                # Pending tasks
├── requirements.txt       # Dependencies
├── scripts/               # Main scripts
│   ├── polish.py              # Main entry point (orchestrates step modules)
│   ├── extract_sections.py    # CLI: Extract sections from markdown
│   ├── init_sessions.py       # CLI: Initialize model sessions
│   ├── test_sections.py       # CLI: Test sections with models
│   ├── detect_ambiguities.py  # CLI: Detect ambiguities using judge
│   ├── generate_report.py     # CLI: Generate report and polished doc
│   ├── config.yaml            # Model configuration
│   └── src/                   # Core modules (step implementations)
│       ├── extraction_step.py      # Extract testable sections
│       ├── session_init_step.py    # Initialize model sessions
│       ├── testing_step.py         # Test sections with models
│       ├── detection_step.py       # Detect ambiguities
│       ├── reporting_step.py       # Generate reports
│       ├── model_interface.py      # Model communication
│       ├── document_processor.py   # Document parsing
│       ├── prompt_generator.py     # Prompt generation
│       ├── ambiguity_detector.py   # Ambiguity detection strategies
│       └── session_manager.py      # Session management
│   └── workspace/             # Generated session outputs
├── docs/                  # Documentation
│   ├── archive/               # Archived early design docs
│   ├── test/                  # Test documents and procedures
│   └── *.md                   # Design documentation
├── tests/                 # Automated tests (132 tests)
├── rules/                 # Project-specific rule overrides
└── temp/                  # Temporary files
```

## Configuration

**Models:** Configured in `scripts/config.yaml` - currently supports CLI-based models (claude, gemini, codex)

**Profiles:**
- `quick` - 2 models, 1 iteration
- `standard` - 3 models, 2 iterations (default)
- `thorough` - 3 models, 3 iterations

## How It Works

1. **Extract testable sections** from markdown documents
2. **Initialize sessions** with full document context (optional)
3. **Generate prompts** to test each section's clarity
4. **Query multiple AI models** via CLI interfaces
5. **LLM-as-Judge comparison** - Claude analyzes interpretations for disagreements
6. **Detect ambiguities** - Different interpretations, assumptions, unclear terms
7. **Generate report** with severity levels and detailed analysis
8. **Create polished document** with clarification markers

## Current Status

**✅ Increment 1 Complete:**
- Section extraction from markdown documents
- Multi-model CLI interface (claude, gemini, codex)
- Basic configuration system

**✅ Increment 2 Complete:**
- **LLM-as-Judge strategy** - Uses Claude to compare model interpretations
- **Session management** - Full document context maintained across queries (67% ambiguity reduction)
- Real ambiguity detection (not simulation)
- Detailed report generation with severity levels
- Model-reported ambiguities included in analysis
- Judge fail-fast error handling
- Code fence handling in section extraction
- 73 comprehensive automated tests

**✅ Modular Architecture Complete:**
- 5 step modules (extraction, session_init, testing, detection, reporting)
- 5 CLI scripts for standalone step execution
- Refactored polish.py to use modules
- New artifacts: sections.json, session_metadata.json
- Debug workflow: Re-run detection without model queries
- Full backward compatibility maintained

**🚧 In Progress:**
- Session management testing on remaining test documents
- Additional edge case handling

**📋 Planned:**
- Increment 2 Polish: Adversarial prompts
- Increment 3: Smart fix generation and iterative polishing
- Increment 4: API support, packaging, enhanced error handling

## Key Files Reference

**Configuration:** `scripts/config.yaml`
**Core orchestrator:** `scripts/polish.py`
**CLI scripts:** `scripts/extract_sections.py`, `scripts/test_sections.py`, `scripts/detect_ambiguities.py`, `scripts/generate_report.py`, `scripts/init_sessions.py`
**Step modules:** `scripts/src/*_step.py` (extraction, session_init, testing, detection, reporting)
**Supporting modules:** `scripts/src/model_interface.py`, `scripts/src/document_processor.py`, `scripts/src/prompt_generator.py`, `scripts/src/ambiguity_detector.py`, `scripts/src/session_manager.py`
**Testing:** `tests/test_*.py` (132 tests), `docs/test/` (test documents and procedures)
**Documentation:** `AGENTS.md` (this file), `README.md` (user guide), `docs/*.md` (design docs)
**Development:** `SESSION_LOG.md` (history), `TODO.md` (pending tasks)

## Integration Notes

- Inherits common rules from `../common_rules/`
- Override rules via `rules/{rulename}.md`
- Follow session log format from `common_rules/session_log.md`
- Project structure may change significantly during development

---

**Note:** This is an early-stage project under active development. Documentation and structure subject to change.
