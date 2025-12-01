# Document Polishing System - Technical Guide

**Version:** 0.1.0 (Active Development - Expect Changes)

## Purpose

Automated tool that detects ambiguities in documentation by testing it with multiple AI models and identifying where interpretations differ.

## Core Concept

Test documentation → Compare model interpretations → Detect disagreements → Generate fixes → Validate consistency

## Quick Commands

```bash
# Polish a document
cd scripts && python3 polish.py ../test/test_simple.md

# Use specific models/profile
cd scripts && python3 polish.py document.md --models claude,gemini --profile thorough

# List models and version
cd scripts && python3 polish.py --list-models
cd scripts && python3 polish.py --version
```

## Project Structure

```
document_polishing/
├── CLAUDE.md              # This file - technical guide
├── README.md              # User overview
├── SESSION_LOG.md         # Development history
├── TODO.md                # Pending tasks
├── config.yaml            # Model configuration
├── requirements.txt       # Dependencies
├── scripts/               # Main scripts
│   ├── polish.py              # Main entry point
│   └── src/                   # Core modules
│       ├── model_interface.py     # Model communication
│       ├── document_processor.py  # Document parsing
│       └── prompt_generator.py    # Prompt generation
├── test/                  # Test documents
├── workspace/             # Generated session outputs
├── rules/                 # Project-specific rule overrides
└── temp/                  # Temporary files
```

## Configuration

**Models:** Configured in `config.yaml` - currently supports CLI-based models (claude, gemini, codex)

**Profiles:**
- `quick` - 2 models, 1 iteration
- `standard` - 3 models, 2 iterations (default)
- `thorough` - 3 models, 3 iterations

## How It Works

1. Extract testable sections from markdown
2. Generate prompts to test each section
3. Query multiple AI models
4. Compare responses for disagreements
5. Detect ambiguities (different interpretations, assumptions)
6. Generate report + polished document with clarification markers

## Current Status

**Working (Increment 1):**
- Section extraction, multi-model testing, ambiguity detection, report generation

**Planned:**
- Increment 2: Better ambiguity detection (semantic similarity)
- Increment 3: Smart fix generation and iterative polishing
- Increment 4: API support, packaging, error handling

## Key Files Reference

**Configuration:** `config.yaml`
**Core:** `scripts/polish.py`, `scripts/src/*.py`
**Documentation:** `DOCUMENTATION_POLISHING_WORKFLOW.md` (full design), `README.md` (user guide)
**Development:** `SESSION_LOG.md` (history), `TODO.md` (pending tasks)

## Integration Notes

- Inherits common rules from `../common_rules/`
- Override rules via `rules/{rulename}.md`
- Follow session log format from `common_rules/session_log.md`
- Project structure may change significantly during development

---

**Note:** This is an early-stage project under active development. Documentation and structure subject to change.
