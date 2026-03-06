# Documentation Polishing System

**Version:** 0.3.0
**Status:** Core pipeline working. Questioning approach pivoting to whole-document.

## Overview

Automated tool that detects ambiguities in documentation by testing it with multiple AI models and identifying where interpretations differ.

## Project Scope

**Type:** Personal project for iterative documentation improvement
**Target:** Documentation written for LLM consumption (workflows, instructions, standards)
**Users:** Single user (document creator, polisher, consumer)
**Goal:** Create clear, robust documentation that LLMs can follow reliably without requiring human intervention to course-correct

### Use Cases
- Instruction documents for personal LLM workflows
- Workflow descriptions and procedures
- Standard practices and guidelines
- Technical documentation on specific topics

**Not Intended For:**
- Critical production applications
- Multi-team documentation
- Public-facing API references

## How It Works

The core pipeline sends each document section to multiple LLMs, collects their interpretations, and uses LLM-as-Judge to find disagreements:

```
Step 1: Extract sections    - Parse markdown into testable instructional sections
Step 2: Init sessions       - (Optional) Create model sessions with full document context
Step 3: Test sections       - Query all models for interpretation of each section
Step 4: Detect ambiguities  - LLM-as-Judge compares interpretations, finds disagreements
Step 5: Generate report     - Markdown report + polished document with clarification markers
```

### Ambiguity Detection

Three signals trigger ambiguity flags:
1. **Model disagreement** — Models interpret the same section differently (severity based on similarity)
2. **Assumption-making** — Models agree but required assumptions to do so
3. **Shared concerns** — Models agree but both independently note the same ambiguity

Two comparison strategies:
- **LLM-as-Judge** (default) — Claude evaluates all interpretations together
- **Simple comparison** — Keyword/Jaccard similarity (no API calls)

## Installation

### Requirements
- Python 3.11+
- PyYAML
- CLI access to `claude`, `gemini`, and/or `codex`

### Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Full pipeline (recommended)
```bash
python scripts/polish.py path/to/document.md
python scripts/polish.py path/to/document.md --models claude,gemini
python scripts/polish.py path/to/document.md --profile standard
python scripts/polish.py path/to/document.md --judge claude
python scripts/polish.py path/to/document.md --resume  # resume from crash
```

### Individual steps
```bash
python scripts/extract_sections.py document.md -o workspace/sections.json
python scripts/init_sessions.py workspace/sections.json document.md
python scripts/test_sections.py workspace/sections.json -o workspace/
python scripts/detect_ambiguities.py workspace/test_results.json
python scripts/generate_report.py workspace/test_results.json workspace/ambiguities.json
```

### Output
Files created in `scripts/workspace/polish_TIMESTAMP/`:
- `report.md` — Detailed analysis report
- `*_polished.md` — Document with clarification markers
- `test_results.json` — Raw model interpretations
- `ambiguities.json` — Detected ambiguities
- `judge_responses.log` — LLM judge decision log

## Configuration

`scripts/config.yaml`:

```yaml
models:
  claude:
    type: cli
    command: claude
    timeout: 30
    enabled: true
  gemini:
    type: cli
    command: gemini
    timeout: 30
    enabled: true
  codex:
    type: cli
    command: codex
    timeout: 30
    enabled: true

profiles:
  quick:    [claude, gemini]       # 2 models, 1 iteration
  standard: [claude, gemini, codex] # 3 models, 1 iteration
  thorough: [claude, gemini, codex] # 3 models, 2 iterations

session_management:
  enabled: true
  mode: auto-recreate  # or fail-fast
```

## Project Structure

```
document_polishing/
├── scripts/
│   ├── polish.py                 # Main orchestrator (Steps 1-5)
│   ├── extract_sections.py       # Standalone section extraction
│   ├── init_sessions.py          # Standalone session init
│   ├── test_sections.py          # Standalone section testing
│   ├── detect_ambiguities.py     # Standalone ambiguity detection
│   ├── generate_report.py        # Standalone report generation
│   ├── generate_questions.py     # Question generation CLI (not integrated)
│   ├── test_questions.py         # Question testing CLI (not integrated)
│   ├── strip_metadata.py         # Bulky -> clean doc transform
│   ├── config.yaml               # Model and pipeline configuration
│   ├── templates/                # Question templates (abandoned - see below)
│   ├── src/
│   │   ├── extraction_step.py    # Step 1: Section extraction
│   │   ├── session_init_step.py  # Step 2: Session initialization
│   │   ├── testing_step.py       # Step 3: Multi-model testing
│   │   ├── detection_step.py     # Step 4: Ambiguity detection
│   │   ├── reporting_step.py     # Step 5: Report generation
│   │   ├── model_interface.py    # CLI model abstraction layer
│   │   ├── session_manager.py    # Session lifecycle management
│   │   ├── session_handlers.py   # Per-model session handlers
│   │   ├── document_processor.py # Markdown parsing
│   │   ├── ambiguity_detector.py # Comparison strategies
│   │   ├── prompt_generator.py   # Interpretation prompts
│   │   └── questioning_step.py   # Question framework (not integrated)
│   └── workspace/                # Session outputs (generated)
├── docs/
│   ├── bulky/                    # Source docs with @meta/@assertion markers
│   ├── clean/                    # Stripped docs for LLM consumption
│   ├── test/                     # Test fixtures and procedures
│   ├── question_testing/         # Framework design and plans
│   └── archive/                  # Historical design docs
├── tests/                        # 132 passing tests
├── temp/                         # Work artifacts from experiments
├── AGENTS.md                     # Authoritative project reference
└── TODO.md                       # Active task tracking
```

## Questioning Approaches — What Was Tried

The core pipeline detects HOW models interpret text differently. A complementary question-based approach would test WHETHER models can correctly USE their understanding. Three approaches were tried:

### 1. Template-Based Questions (Abandoned)

Regex-based element extraction + template patterns to auto-generate questions from section content. Infrastructure built (2,000 LOC, 47 tests), but templates had a fundamental design flaw: the extracted answer was the same text substituted into the question, causing 100% answer leakage. The validator correctly rejected every generated question. The template approach itself was the wrong abstraction — too rigid, too fragile.

**Status:** Code remains in `questioning_step.py`. Templates in `scripts/templates/` are dead.

### 2. Manual Per-Section Questions (Shelved)

Hand-crafted scenario questions tested against `git_workflow.md` in 3 conditions (cold, old doc, new doc) x 2 models (Gemini, Codex). Results: cold 13%, old doc 13%, new doc 88% accuracy. **This proved the concept works** — focused questions catch real comprehension failures.

However, writing and maintaining per-section questions for every document block is too cumbersome to track and align. The overhead doesn't scale.

**Status:** Experiment artifacts in `temp/`. Approach shelved.

### 3. Whole-Document Questions (Next)

Ask targeted questions about the entire document rather than section-by-section. Easier to store in one place, easier to track, easier to extract. The session infrastructure already supports this — models get full document context via `session_management`.

**Status:** Not started. This is the next direction.

## Bulky-Clean Architecture

Source/build system for documentation:
- **Bulky docs** (`docs/bulky/`): Source of truth with `@meta` blocks and `@assertion` markers
- **Clean docs** (`docs/clean/`): Stripped versions for LLM consumption
- **Transform:** `strip_metadata.py` — deterministic line-by-line state machine

Week 1 exercises completed: format spec, strip script, manual question validation, authoring guide (`docs/bulky/BULKY_FORMAT_GUIDE.md`). Not yet integrated into `polish.py`.

## Testing

```bash
source .venv/bin/activate
pytest tests/ -v            # 132 tests, ~0.4s
ruff check .                # Linting
ruff format --check .       # Format verification
pyright scripts/src/        # Type checking (0 errors, warnings only)
```

## Known Limitations

- Fix generation is basic (adds clarification markers, no smart rewrites)
- No iterative polishing (run once, review, manually improve)
- CLI models only (no direct API support)
- Cannot control model context window limits
- Some models don't follow JSON prompt format consistently

## Next Steps

1. **Whole-document questioning** — Design question format, implement collection/evaluation
2. **Integration** — Wire questioning into `polish.py` as optional Step 6
3. **Fix generation** — Smart fix strategies beyond clarification markers
4. **Packaging** — Proper `pyproject.toml` build, `.env.example`

## Version History

- **0.3.0** (2026-02-25) — Modular architecture, fail-fast judge, intermediate saves, resume support, bulky-clean Week 1
- **0.2.0** (2025-12-21) — LLM-as-Judge, session management, shared ambiguity detection
- **0.1.0** (2025-11-22) — Core system, CLI model support, basic ambiguity detection

## License

MIT
