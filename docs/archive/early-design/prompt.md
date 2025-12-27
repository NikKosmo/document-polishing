# Documentation Polishing System - Implementation Continuation

## Context
You are continuing work on a documentation polishing system. The goal is to create a working tool that detects ambiguities in documentation by testing with multiple AI models and automatically fixes them.

## What Has Been Done
Three files have been created (attached):
1. **DOCUMENTATION_POLISHING_WORKFLOW.md** - ✅ COMPLETE
   - Describes 9-step automated polishing process
   - Includes configuration specs, validation criteria, reporting structure
   - This is the blueprint for what needs to be built

2. **DOCUMENTATION_POLISHING_QUICK_REFERENCE.md** - ✅ COMPLETE
   - Quick reference guide with commands, checklists, patterns
   - References commands and scripts that don't exist yet
   - Will become accurate once implementation is complete

3. **DOCUMENTATION_POLISHING_IMPLEMENTATION.md** - ⚠️ INCOMPLETE
   - Contains pseudo-code and example snippets
   - Has placeholders like "# This is where you'd call actual model APIs"
   - Shows the structure but not working implementation
   - Needs to be converted to actual runnable code

## What Needs To Be Done

Transform the IMPLEMENTATION.md examples into working code that can be executed immediately.

### Priority Order (complete in increments):

#### Increment 1: Core System (Minimum Viable)
- [ ] Create `polish.py` - main entry point that actually works
- [ ] Create `src/document_processor.py` - extract sections from markdown
- [ ] Create `src/model_interface.py` - working interface for at least 2 models:
  - CLI models (subprocess calls to `claude`, `ollama`, etc.)
  - At least one API model with proper error handling
- [ ] Create basic `config.yaml` with model configurations
- [ ] Test with simple document and verify it runs end-to-end

#### Increment 2: Ambiguity Detection
- [ ] Implement real `src/ambiguity_detector.py` (not simulation)
- [ ] Create working comparison logic (can use simple string matching)
- [ ] Generate actual ambiguity reports
- [ ] Add `src/prompt_generator.py` with real prompt templates

#### Increment 3: Fix Generation
- [ ] Implement `src/fix_generator.py` with actual fix strategies
- [ ] Create `src/fix_applier.py` to modify documents
- [ ] Add iteration support (multiple rounds of polishing)
- [ ] Implement validation checking

#### Increment 4: Polish & Package
- [ ] Create `setup.py` for easy installation
- [ ] Add `requirements.txt` with minimal dependencies
- [ ] Create `.env.example` for configuration
- [ ] Write `README.md` with actual usage instructions
- [ ] Add error handling and progress indicators

## Task Completion Criteria

The task is COMPLETE when:

### Functional Requirements Met:
- [ ] Can run: `python polish.py test_document.md`
- [ ] Successfully connects to at least 2 different AI models
- [ ] Detects at least 1 ambiguity in a test document
- [ ] Generates a fixed version of the document
- [ ] Outputs both polished document and report

### Files Created and Working:
```
polish_system/
├── polish.py                    # ✓ Runs without errors
├── requirements.txt              # ✓ Minimal dependencies
├── config.yaml                   # ✓ Default configuration
├── .env.example                  # ✓ Template for API keys
├── src/
│   ├── __init__.py
│   ├── document_processor.py    # ✓ Extracts sections
│   ├── model_interface.py       # ✓ Calls real models
│   ├── ambiguity_detector.py    # ✓ Finds disagreements
│   ├── fix_generator.py         # ✓ Creates fixes
│   ├── fix_applier.py          # ✓ Applies fixes
│   └── prompt_generator.py      # ✓ Generates prompts
├── test/
│   └── test_simple.md           # ✓ Test document with ambiguities
└── output/
    └── [generated at runtime]
```

### Verification Tests Pass:
1. **Setup Test**: `python polish.py --version` shows version
2. **Model Test**: `python polish.py --list-models` shows available models
3. **Simple Polish**: `python polish.py test/test_simple.md` completes successfully
4. **Output Check**: Creates `output/test_simple_polished.md` and `output/report.md`
5. **Ambiguity Found**: Report shows at least 1 detected ambiguity

## Implementation Guidelines

1. **Start Simple**: Get basic functionality working before adding features
2. **Real Calls**: Replace ALL simulated responses with actual model calls
3. **Graceful Degradation**: Continue working even if some models fail
4. **No Heavy Dependencies**: Avoid sklearn, tensorflow, etc. Use simple Python
5. **Clear Progress**: Show what's happening with print statements
6. **Save Progress**: After each increment, ensure the code runs

## Test Document to Include

Create `test/test_simple.md` with intentionally ambiguous instructions:
```markdown
# Test Workflow

## Step 1: Process Data
Process all items in the batch.

## Step 2: Generate Output
Create N cards per word with the required information.

## Step 3: Validate Results
Check the output using the standard validation process.
```

## Current Session Instructions

1. Read all three attached MD files to understand the system design
2. Start with Increment 1 - get basic system running
3. Save and test after each increment
4. If interrupted, note which increment was completed
5. Next session can continue from the last completed increment

## Success Indicator
You know you're done when you can run:
```bash
python polish.py test/test_simple.md --models claude,ollama
```
And it produces:
- A polished version with clearer instructions
- A report showing what ambiguities were found and fixed
- No simulation or placeholder code remains