# Documentation Polishing System

**Version:** 0.2.0
**Status:** Increment 2 Complete (Ambiguity Detection Working)

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
- Real-time documentation updates

## Architecture

### Document Lifecycle

```
SOURCE: workflow.bulky.md
├─ Metadata (version, dates, polishing history)
├─ Assertions (testable claims for question generation)
└─ Content (mixed with test markers)

         │
         ├──[strip]───────► workflow.md (clean)
         │                  └─► polish.py (ambiguity detection)
         │                      └─► polished output
         │
         └──[extract]─────► assertions.json
                            └─► generate_questions.py
                                └─► comprehension testing

FUTURE: polished + bulky ─[merge]─► updated bulky doc
```

**Key Concepts:**
- **Bulky docs**: Source of truth with metadata and test markers
- **Clean docs**: Stripped for LLM consumption (what models actually see)
- **Transform pipeline**: Deterministic strip/merge operations
- **Polishing**: Tests clean docs for comprehension issues
- **Question testing**: Validates understanding using assertions from bulky docs

## ✅ Current Status - Increment 2 Complete

### What Works:
- ✅ Extract testable sections from markdown documents
- ✅ Test sections with multiple CLI-based AI models
- ✅ **LLM-as-Judge strategy** - Claude compares model interpretations
- ✅ **Session management** - Full document context maintained across queries
- ✅ Detect ambiguities with severity levels (high/medium/low)
- ✅ Generate detailed reports showing disagreements and assumptions
- ✅ Create polished documents with clarification markers
- ✅ Support for multiple models (claude, gemini, codex)
- ✅ Configurable via YAML with profiles (quick/standard/thorough)

### Working Commands:
```bash
# Show version
cd scripts && python polish.py --version

# List available models
cd scripts && python polish.py --list-models

# Polish a document (uses default models from config)
cd scripts && python polish.py ../docs/test/test_context_terms_definitions.md

# Use specific models
cd scripts && python polish.py ../docs/test/test_context_terms_definitions.md --models claude,gemini

# Use a profile
cd scripts && python polish.py document.md --profile standard
```

## Installation

### Requirements:
- Python 3.8+
- PyYAML

### Setup:
```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
cd scripts && python polish.py --version
```

## Configuration

Edit `config.yaml` to configure models:

```yaml
models:
  claude:
    type: cli
    command: claude        # Path to CLI command
    args: []              # Additional arguments
    timeout: 30           # Timeout in seconds
    enabled: true

  gemini:
    type: cli
    command: gemini
    timeout: 30
    enabled: true
```

## Usage Examples

### Basic Usage:
```bash
cd scripts && python polish.py ../docs/test/test_context_terms_definitions.md
```

Output files created in `workspace/polish_TIMESTAMP/`:
- `report.md` - Detailed analysis report
- `test_context_terms_definitions_polished.md` - Document with clarification notes
- `test_results.json` - Raw test results (JSON)

### Example Report Output:

```
# Documentation Polish Report

**Session ID:** polish_20251122_075228
**Document:** docs/test/test_context_terms_definitions.md
**Date:** 2025-11-22 07:52:28

## Summary
- **Sections Tested:** 3
- **Ambiguities Found:** 3
- **Models Used:** claude, gemini

## Ambiguities Detected

### 1. Step 2: Generate Output (high severity)

**Original Text:**
Create N cards per word with the required information.

**Different Interpretations:**
- **claude:** Create N separate JSON entries per word, where N depends on word type
- **gemini:** Create a single JSON entry per word, with N being a parameter in the entry

**Assumptions Made:**
- **claude:** N varies by word type, JSON format is required, Each entry = one card
- **gemini:** N is a field/parameter, not the number of entries, Expansion happens in later step
```

## How It Works

1. **Extract Sections**: Scans markdown document for sections containing instructions
2. **Generate Prompts**: Creates specific prompts to test each section
3. **Query Models**: Sends prompts to multiple AI models via CLI
4. **Compare Responses**: Analyzes responses to find differences in interpretation
5. **Detect Ambiguities**: Identifies where models disagree or make assumptions
6. **Generate Report**: Creates detailed report with findings
7. **Create Polished Version**: Adds clarification markers to ambiguous sections

## Project Structure

```
polish_system/
├── polish.py                    # Main entry point
├── config.yaml                  # Configuration
├── requirements.txt             # Dependencies
├── src/
│   ├── __init__.py
│   ├── model_interface.py       # Model communication layer
│   ├── document_processor.py    # Document parsing
│   └── prompt_generator.py      # Prompt templates
├── docs/test/                   # Test documents
│   ├── test_context_terms_definitions.md
│   └── test_context_abbreviations_acronyms.md
├── workspace/                   # Session workspaces (generated)
│   └── polish_TIMESTAMP/
│       ├── report.md
│       ├── test_results.json
│       └── *_polished.md
└── output/                      # Final outputs (generated)
```

## Testing with Mock Models

For development/testing without real AI models, mock CLI tools are provided:
- `mock_claude` - Simulates Claude responses
- `mock_gemini` - Simulates Gemini responses (with different interpretations)

These are already configured in `config.yaml` for testing.

## Detected Ambiguity Types

The system currently detects:

1. **Different Interpretations** (High Severity)
   - Models understand instructions completely differently
   - Example: "Create N cards" → some think N entries, others think N is a parameter

2. **Assumption-Based** (Medium/Low Severity)
   - Models agree but required assumptions
   - Example: "standard validation" → assumes what "standard" means

3. **Pattern-Based** (In Progress)
   - Vague quantifiers (N, several, some, many)
   - Implicit references (the process, this output)
   - Undefined terms (standard, required, appropriate)

## Known Limitations

**Current (Increment 2):**
- ❌ Fix generation is basic (just adds clarification notes)
- ❌ No iterative polishing yet
- ❌ No validation of polished documents
- ❌ CLI models only (no API support yet)
- ⚠️ Cannot control model context window limits (may lose initial document)
- ⚠️ Some models don't follow prompt format consistently

**Addressed in Increment 2:**
- ✅ LLM-as-Judge replaces simple text comparison
- ✅ Session management provides full document context
- ✅ Model-reported ambiguities included in analysis

These will be addressed in Increments 3-4.

## Next Steps (Roadmap)

### Increment 2: Ambiguity Detection ✅ COMPLETE
- ✅ LLM-as-Judge comparison (not just text matching)
- ✅ Ambiguity severity classification
- ✅ Session management for document context

### Current: Bulky-Clean Architecture (In Progress)
**Goal:** Implement source/build system for documentation with test markers

**Phase 1:** Foundation (Week 1)
- [ ] Bulky document format specification
- [ ] Strip metadata script (bulky → clean)
- [ ] Test round-trip conversion
- [ ] Convert 1 example document

**Phase 2:** Question Testing (Week 2-3)
- [ ] Fix question templates (expert review recommendations)
- [ ] Reduce answer leakage to 0%
- [ ] Template success rate > 80%
- [ ] Test on bulky documents

**Phase 3:** Integration (Week 4)
- [ ] Integrate questioning into polish.py as optional step
- [ ] End-to-end workflow: bulky → strip → polish → questions
- [ ] Update configuration for question testing

**See:** `docs/question_testing/plans/BULKY_CLEAN_ARCHITECTURE_PLAN.md`

### Future: Fix Generation & Merge
- [ ] Smart fix strategies
- [ ] Merge polishing results back to bulky docs
- [ ] Iterative polishing workflow
- [ ] Auto-fix where possible

## Troubleshooting

### "Command not found" errors:
```bash
# Check model configuration in config.yaml
cd scripts && python polish.py --list-models

# Verify CLI command exists
which claude
which gemini
```

### No ambiguities detected:
- Document may already be clear
- Try using more models: `--models claude,gemini,codex`
- Check if sections were extracted: look for "Found X sections" in output

### Permission errors:
```bash
# Make sure mock CLIs are executable
chmod +x mock_*
```

## Example Test Document

```markdown
# Test Workflow

## Step 1: Process Data
Process all items in the batch.

## Step 2: Generate Output
Create N cards per word with the required information.

## Step 3: Validate Results
Check the output using the standard validation process.
```

Run: `cd scripts && python polish.py ../docs/test/test_context_terms_definitions.md`

Expected: Detects 3 ambiguities (sequential vs parallel, N entries vs N parameter, standard validation undefined)

## Contributing

This is an active development project. Current focus: Increment 1 → Increment 2.

## License

MIT (to be added)

## Version History

- **0.2.0** (2025-12-21) - Increment 2 Complete
  - LLM-as-Judge strategy implemented
  - Session management with full document context
  - Severity-based ambiguity classification
  - Enhanced report generation

- **0.1.0** (2025-11-22) - Increment 1 Complete
  - Core system working
  - CLI model support
  - Basic ambiguity detection
  - Report generation
