# Document Polishing System - Technical Guide

**Version:** 0.2.0 (Active Development - Increment 2 Complete)

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
├── AGENTS.md              # This file - AI assistant technical guide
├── CLAUDE.md              # Redirect to AGENTS.md (for Claude Code compatibility)
├── README.md              # User overview
├── SESSION_LOG.md         # Development history
├── TODO.md                # Pending tasks
├── config.yaml            # Model configuration
├── requirements.txt       # Dependencies
├── scripts/               # Main scripts
│   ├── polish.py              # Main entry point
│   └── src/                   # Core modules
│   │   ├── model_interface.py     # Model communication
│   │   ├── document_processor.py  # Document parsing
│   │   └── prompt_generator.py    # Prompt generation
│   └── workspace/             # Generated session outputs
├── test/                  # Test documents
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
- **Session management** - Full document context maintained across queries
- Real ambiguity detection (not simulation)
- Detailed report generation with severity levels
- Model-reported ambiguities included in analysis

**🚧 In Progress:**
- Context window monitoring
- Non-compliant model response handling
- Additional test coverage

**📋 Planned:**
- Increment 3: Smart fix generation and iterative polishing
- Increment 4: API support, packaging, enhanced error handling

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
