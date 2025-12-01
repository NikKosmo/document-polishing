# Documentation Polishing Workflow

**Version:** 1.0  
**Date:** 2025-11-19  
**Purpose:** Automated workflow for identifying and eliminating ambiguities in documentation through multi-model and multi-agent testing

---

## Overview

This workflow provides a systematic, automated approach to **polish documentation** by detecting ambiguities through parallel testing with multiple AI models and agents. The goal is to ensure documentation is interpreted consistently across different AI systems, reducing implementation failures and debugging time.

### Core Principle
**Test with multiple perspectives → Identify disagreements → Clarify ambiguities → Validate consistency**

### Key Features
- **Multi-model testing** (Claude, Gemini, GPT, Llama, etc.)
- **Multi-agent testing** (parallel instances with identical prompts)
- **Automated ambiguity detection**
- **Version control and change tracking**
- **Configurable testing depth**
- **Comprehensive reporting**

---

## Prerequisites

### Required Tools
```bash
# Core requirements
- Python 3.8+
- Git for version control
- JSON/YAML processors (jq, yq)

# Model access (at least 2 required)
- API keys or CLI tools for AI models
- Examples: Claude API, Gemini CLI, OpenAI API, Ollama local models
```

### Directory Structure
```
documentation-polishing/
├── config/
│   ├── models.yaml              # Model configuration
│   ├── test_profiles.yaml       # Testing depth profiles
│   └── prompts/                 # Test prompt templates
├── scripts/
│   ├── polish_document.py       # Main orchestration script
│   ├── test_runner.py           # Parallel testing executor
│   ├── ambiguity_detector.py   # Disagreement analyzer
│   ├── fix_generator.py        # Ambiguity resolution
│   └── validator.py             # Consistency checker
├── workspace/
│   ├── originals/               # Backup of original documents
│   ├── iterations/              # Each polishing iteration
│   └── reports/                 # Analysis reports
└── logs/
    └── polishing_sessions.log   # Detailed execution logs
```

---

## Configuration Files

### models.yaml
```yaml
models:
  claude:
    type: "api"
    endpoint: "${CLAUDE_API_ENDPOINT}"
    key: "${CLAUDE_API_KEY}"
    model: "claude-3-opus-20240229"
    max_tokens: 4096
    temperature: 0.1  # Low for consistency
    
  gemini:
    type: "cli"
    command: "gemini"
    flags: "-p"
    temperature: 0.1
    
  gpt4:
    type: "api"
    endpoint: "${OPENAI_API_ENDPOINT}"
    key: "${OPENAI_API_KEY}"
    model: "gpt-4-turbo"
    temperature: 0.1
    
  llama:
    type: "local"
    command: "ollama run llama2:70b"
    temperature: 0.1

# Minimum models required for testing
minimum_models: 2
preferred_models: 3
```

### test_profiles.yaml
```yaml
profiles:
  quick:
    name: "Quick Surface Test"
    extract_sections: ["key_instructions", "examples"]
    test_iterations: 1
    agents_per_model: 1
    
  standard:
    name: "Standard Testing"
    extract_sections: ["all_instructions", "examples", "edge_cases"]
    test_iterations: 2
    agents_per_model: 3
    
  thorough:
    name: "Deep Testing"
    extract_sections: ["all"]
    test_iterations: 3
    agents_per_model: 5
    include_stress_tests: true
    
  critical:
    name: "Critical Documentation"
    extract_sections: ["all"]
    test_iterations: 5
    agents_per_model: 10
    include_stress_tests: true
    include_edge_cases: true
    require_unanimous_agreement: true
```

---

## Workflow Steps

### Step 1: Initialize Polishing Session

```bash
python scripts/polish_document.py init \
  --document ./path/to/WORKFLOW.md \
  --profile standard \
  --models claude,gemini,gpt4
```

**Actions:**
1. Create session ID (timestamp-based)
2. Backup original to `workspace/originals/`
3. Initialize iteration counter (starts at 0)
4. Create session directory structure
5. Parse document structure
6. Log session start

**Output:**
```
Session initialized: polish_20251119_143052
Original backed up: workspace/originals/WORKFLOW_20251119_143052.md
Profile: standard (3 models, 3 agents each)
Ready to begin polishing iteration 1
```

---

### Step 2: Extract Testable Sections

```bash
python scripts/polish_document.py extract \
  --session polish_20251119_143052
```

**Process:**
1. Parse document structure (headers, lists, code blocks)
2. Identify instruction sections based on keywords:
   - "Step", "must", "should", "required", "format"
   - Command examples, JSON/YAML structures
   - Numbered/bulleted procedures
3. Extract based on profile depth
4. Generate test catalog

**Output File:** `workspace/iterations/1/test_catalog.json`
```json
{
  "document": "WORKFLOW.md",
  "sections": [
    {
      "id": "step_4_json_creation",
      "type": "instruction",
      "line_start": 135,
      "line_end": 160,
      "content": "### Step 4: Claude Writes `pending_cards.json`...",
      "testable_elements": [
        "number_of_json_entries_per_word",
        "json_structure_requirements",
        "overwrite_vs_append_behavior"
      ]
    }
  ],
  "total_sections": 24,
  "total_testable_elements": 67
}
```

---

### Step 3: Generate Test Prompts

```bash
python scripts/polish_document.py generate-prompts \
  --session polish_20251119_143052
```

**Template Example:** `config/prompts/instruction_test.txt`
```
Read the following documentation section carefully:

---
{section_content}
---

Based on these instructions, perform the following task:
{specific_task}

Provide your response in this exact JSON format:
{
  "interpretation": "What you understand you should do",
  "implementation": "Step-by-step actions you would take",
  "assumptions": ["Any assumptions you had to make"],
  "ambiguities": ["Any unclear points you noticed"]
}
```

**Generated Prompts:** `workspace/iterations/1/test_prompts.json`

---

### Step 4: Run Parallel Tests

```bash
python scripts/test_runner.py \
  --session polish_20251119_143052 \
  --parallel true
```

**Execution:**
1. Load test prompts and model configurations
2. For each test prompt:
   - Spawn N agents per model (based on profile)
   - Send identical prompt to all agents
   - Collect responses with timeout handling
   - Store raw responses
3. Handle failures gracefully (retry logic)
4. Generate execution report

**Output:** `workspace/iterations/1/test_responses.json`
```json
{
  "test_id": "step_4_json_creation",
  "prompt": "...",
  "responses": {
    "claude_agent_1": {
      "interpretation": "Create 3 JSON entries for nouns",
      "implementation": ["Create RU->DE entry", "Create DE->RU entry", "Create Cloze entry"],
      "assumptions": [],
      "ambiguities": []
    },
    "gemini_agent_1": {
      "interpretation": "Create 1 JSON entry that will be expanded",
      "implementation": ["Create single entry with all data"],
      "assumptions": ["Script will generate multiple cards from single entry"],
      "ambiguities": ["Unclear if 'N cards' means N JSON entries"]
    }
  }
}
```

---

### Step 5: Detect Ambiguities

```bash
python scripts/ambiguity_detector.py \
  --session polish_20251119_143052
```

**Analysis Process:**
1. Compare interpretations across all agents
2. Identify disagreements using multiple methods:
   - **Semantic similarity** (embedding-based)
   - **Structural comparison** (implementation steps)
   - **Assumption analysis** (different assumptions = ambiguity)
3. Classify ambiguity severity:
   - **Critical**: Different implementations entirely
   - **Major**: Same goal, different methods
   - **Minor**: Small variations in understanding
4. Generate ambiguity report

**Output:** `workspace/iterations/1/ambiguity_report.json`
```json
{
  "ambiguities": [
    {
      "section_id": "step_4_json_creation",
      "severity": "critical",
      "disagreement_type": "implementation_count",
      "interpretations": {
        "group_1": {
          "models": ["claude_agent_1", "claude_agent_2"],
          "interpretation": "Create multiple JSON entries per word"
        },
        "group_2": {
          "models": ["gemini_agent_1", "gpt4_agent_1"],
          "interpretation": "Create single JSON entry per word"
        }
      },
      "root_cause": "Ambiguous phrasing: 'Create N cards' vs JSON structure",
      "evidence": {
        "line": 157,
        "text": "**Important:** File is overwritten each time (not appended)"
      }
    }
  ],
  "summary": {
    "total_ambiguities": 7,
    "critical": 2,
    "major": 3,
    "minor": 2
  }
}
```

---

### Step 6: Generate Fixes

```bash
python scripts/fix_generator.py \
  --session polish_20251119_143052 \
  --strategy multi-option
```

**Fix Generation Strategies:**
1. **Explicit clarification**: Add explicit instructions
2. **Example enhancement**: Provide comprehensive examples
3. **Table/structured format**: Use tables for clarity
4. **Redundant specification**: State in multiple ways
5. **Negative examples**: Show what NOT to do

**Output:** `workspace/iterations/1/proposed_fixes.json`
```json
{
  "fixes": [
    {
      "ambiguity_id": "step_4_json_creation",
      "original": "### Step 4: Claude Writes `pending_cards.json`",
      "options": [
        {
          "strategy": "explicit_clarification",
          "confidence": 0.95,
          "replacement": "### Step 4: Claude Writes `pending_cards.json`\n\n**IMPORTANT:** Create exactly N separate JSON entries per word:\n- Nouns: 3 entries (RU→DE, DE→RU, Cloze)\n- Verbs: 2 entries (RU→DE, DE→RU)\n\n**Each entry in the JSON array represents one flashcard.**",
          "rationale": "Explicitly states entry count requirement"
        },
        {
          "strategy": "structured_table",
          "confidence": 0.90,
          "replacement": "### Step 4: Claude Writes `pending_cards.json`\n\n| Word Type | JSON Entries Required | Cards Generated |\n|-----------|----------------------|----------------|\n| Noun | 3 separate entries | 3 cards |\n| Verb | 2 separate entries | 2 cards |",
          "rationale": "Table format eliminates ambiguity"
        }
      ],
      "recommended": 0
    }
  ]
}
```

---

### Step 7: Apply Fixes

```bash
python scripts/polish_document.py apply-fixes \
  --session polish_20251119_143052 \
  --strategy recommended
```

**Process:**
1. Load proposed fixes
2. Apply selected fixes (recommended or manual selection)
3. Create new document version
4. Track all changes
5. Generate diff report

**Output:** 
- `workspace/iterations/1/WORKFLOW_polished_iter1.md`
- `workspace/iterations/1/changes.diff`
- `workspace/iterations/1/change_log.json`

---

### Step 8: Validate Consistency

```bash
python scripts/validator.py \
  --session polish_20251119_143052 \
  --document workspace/iterations/1/WORKFLOW_polished_iter1.md
```

**Validation Process:**
1. Re-run tests on polished document
2. Check for interpretation consistency
3. Verify ambiguities are resolved
4. Calculate agreement scores
5. Determine if another iteration is needed

**Success Criteria:**
```yaml
validation_criteria:
  agreement_threshold: 0.95  # 95% interpretation agreement
  max_iterations: 5
  early_stop_improvement: 0.02  # Stop if improvement < 2%
```

**Output:** `workspace/iterations/1/validation_report.json`
```json
{
  "iteration": 1,
  "agreement_score": 0.87,
  "resolved_ambiguities": 5,
  "remaining_ambiguities": 2,
  "recommendation": "continue_iteration",
  "improved_sections": ["step_4_json_creation"],
  "problematic_sections": ["step_2_gemini_validation"]
}
```

---

### Step 9: Iterate or Finalize

**If continuation needed:**
```bash
python scripts/polish_document.py iterate \
  --session polish_20251119_143052
```
- Increments iteration counter
- Uses previous polished version as input
- Returns to Step 2 with remaining ambiguities

**If criteria met:**
```bash
python scripts/polish_document.py finalize \
  --session polish_20251119_143052
```

**Finalization:**
1. Copy final polished document to output location
2. Generate comprehensive session report
3. Create change summary
4. Archive session data
5. Update document metadata

---

## Complete Automation Script

### one_command_polish.sh
```bash
#!/bin/bash
# One-command document polishing

DOCUMENT=$1
PROFILE=${2:-standard}
MODELS=${3:-"claude,gemini,gpt4"}

# Run complete polishing workflow
python scripts/polish_document.py auto \
  --document "$DOCUMENT" \
  --profile "$PROFILE" \
  --models "$MODELS" \
  --max-iterations 5 \
  --agreement-threshold 0.95 \
  --output-dir "./polished" \
  --verbose
```

**Usage:**
```bash
./one_command_polish.sh ./WORKFLOW.md thorough claude,gemini,gpt4,llama
```

---

## Reports and Outputs

### 1. Session Summary Report
**Location:** `workspace/reports/session_YYYYMMDD_HHMMSS_summary.md`

Contains:
- Document overview
- Ambiguities found by severity
- Fixes applied
- Before/after comparison
- Agreement scores per iteration
- Model consensus analysis

### 2. Detailed Ambiguity Catalog
**Location:** `workspace/reports/ambiguity_catalog.json`

Comprehensive record of all ambiguities:
- Location in document
- Interpretations by each model/agent
- Root cause analysis
- Fix applied
- Validation results

### 3. Model Behavior Analysis
**Location:** `workspace/reports/model_patterns.json`

Insights into model-specific interpretation patterns:
- Common assumption patterns by model
- Model-specific ambiguity sensitivity
- Reliability scores per model

### 4. Change Log
**Location:** `workspace/iterations/change_log.md`

Markdown-formatted log of all changes:
```markdown
## Iteration 1 - 2025-11-19 14:35:22

### Critical Fixes
- **Line 157**: Clarified JSON entry requirements
  - Before: "Create N cards per word"
  - After: "Create N separate JSON entries per word (1 entry = 1 card)"

### Major Fixes
- **Line 85**: Specified validation as mandatory
  - Before: "Validate with Gemini"
  - After: "Validate with Gemini (REQUIRED - do not skip)"
```

---

## Edge Cases and Advanced Features

### Handling Contradictions
When documentation contains internal contradictions:
1. Flag both locations
2. Analyze which interpretation is more consistent with rest
3. Generate resolution options
4. Mark as "requires human review" if unresolvable

### Multi-Language Documentation
For documentation with multiple languages:
```yaml
language_config:
  primary: "en"
  translations: ["de", "ru", "es"]
  test_all_languages: true
  cross_reference_translations: true
```

### Code Block Testing
For documentation with code examples:
1. Extract code blocks
2. Test if code matches described behavior
3. Validate syntax and completeness
4. Check for missing error handling

### Conditional Instructions
For "if-then" style instructions:
1. Test all branches
2. Verify condition clarity
3. Check for missing else cases
4. Validate mutual exclusivity

---

## Performance Optimization

### Caching Strategy
```yaml
cache:
  enabled: true
  location: "./cache"
  strategies:
    - model_responses: 24h  # Cache identical prompts
    - embeddings: 7d        # Cache semantic embeddings
    - test_results: 1h      # Short-term result cache
```

### Parallel Execution
```python
parallel_config = {
    "max_workers": 10,
    "timeout_per_test": 30,
    "retry_failed": True,
    "retry_count": 2
}
```

### Cost Optimization
```yaml
cost_optimization:
  start_with_cheapest: true
  escalate_on_disagreement: true
  model_tiers:
    tier_1: ["llama_local", "gpt3.5"]
    tier_2: ["claude-instant", "gemini-pro"]
    tier_3: ["gpt4", "claude-opus"]
```

---

## Troubleshooting

### Common Issues

**Issue:** Models timing out
```bash
# Increase timeout
python scripts/test_runner.py --timeout 60
```

**Issue:** Rate limiting
```bash
# Add delays between calls
python scripts/test_runner.py --delay 2
```

**Issue:** Memory issues with large documents
```bash
# Process in chunks
python scripts/polish_document.py --chunk-size 1000
```

**Issue:** Inconsistent model access
```bash
# Test model connectivity
python scripts/test_connectivity.py
```

---

## Best Practices

### 1. Pre-Polish Checklist
- [ ] Document is complete (not a draft)
- [ ] Examples are included
- [ ] No placeholder text
- [ ] Version controlled

### 2. Testing Strategy
- Start with `quick` profile for rapid feedback
- Use `standard` for most documentation
- Reserve `thorough` for critical processes
- Use `critical` for compliance/safety docs

### 3. Fix Selection
- Prefer explicit over implicit
- Use examples to support rules
- Add tables for complex relationships
- Include "NOT" examples for clarity

### 4. Validation
- Always run at least 2 iterations
- Require higher agreement for critical docs
- Manual review for legal/compliance text
- Test with actual implementation

---

## Version History

- **v1.0** (2025-11-19): Initial workflow design
  - Multi-model and multi-agent testing
  - Automated fix generation
  - Iterative polishing process
  - Comprehensive reporting
