# Session Management Testing Procedure

**Purpose:** Reusable procedure to validate session management effectiveness by comparing context-dependent chunk interpretation with and without full document context.

**Version:** 1.0
**Last Updated:** 2025-12-12

---

## Overview

This procedure tests whether providing full document context (via session management) improves model interpretation of context-dependent sections.

**Test Methodology:**
1. Run polish script with session management OFF (baseline)
2. Run polish script with session management ON (test)
3. Compare results to measure improvement

**Expected Outcome:** Models with full document context should produce fewer ambiguities and more accurate interpretations of sections that depend on earlier definitions.

---

## Prerequisites

- Test document created (following `TEST_DOCUMENT_GENERATION_PROMPTS.md`)
- Test document placed in `test/` directory
- Polish script configured in `scripts/config.yaml`
- Models enabled: claude, gemini, codex (or subset)

---

## Testing Workflow

### Phase 1: Baseline Run (Sessions OFF)

**Goal:** Establish baseline behavior when models analyze sections in isolation.

#### Step 1: Configure Session Management

Edit `scripts/config.yaml`:
```yaml
session_management:
  enabled: false  # Disable sessions for baseline
  mode: "auto-recreate"
  query_format: "resend-chunk"
  purpose_prompt: |
    This document defines standards for creating workflow and instruction
    documents that AI models execute reliably. Please analyze sections
    within this context.
  timeout: 600
  max_retries: 1
  retry_delay_seconds: 2
```

#### Step 2: Run Polish Script

```bash
cd scripts
python3 polish.py ../test/{test_document_name}.md --profile standard
```

**Replace `{test_document_name}` with actual filename** (e.g., `test_context_terms_definitions`)

**Wait for completion.** Expected runtime: 5-10 minutes.

#### Step 3: Preserve Output

```bash
# Get the most recent workspace directory
WORKSPACE=$(ls -t workspace | grep "polish_{test_document_name}" | head -1)

# Rename to indicate baseline run
mv "workspace/$WORKSPACE" "workspace/${WORKSPACE}_baseline_sessions_off"

# Verify
ls -l workspace/*baseline_sessions_off/
```

**Expected outputs:**
- `polish.log` - Execution log
- `test_results.json` - Model interpretations per section
- `ambiguities.json` - Detected ambiguities with severity
- `report.md` - Human-readable analysis

---

### Phase 2: Test Run (Sessions ON)

**Goal:** Test whether session context improves interpretation.

#### Step 1: Configure Session Management

Edit `scripts/config.yaml`:
```yaml
session_management:
  enabled: true   # Enable sessions for test
  mode: "auto-recreate"
  query_format: "resend-chunk"
  purpose_prompt: |
    This document defines standards for creating workflow and instruction
    documents that AI models execute reliably. Please analyze sections
    within this context.
  timeout: 600
  max_retries: 1
  retry_delay_seconds: 2
```

#### Step 2: Run Polish Script

```bash
cd scripts
python3 polish.py ../test/{test_document_name}.md --profile standard
```

**Wait for completion.** Expected runtime: 5-10 minutes.

#### Step 3: Preserve Output

```bash
# Get the most recent workspace directory
WORKSPACE=$(ls -t workspace | grep "polish_{test_document_name}" | head -1)

# Rename to indicate test run
mv "workspace/$WORKSPACE" "workspace/${WORKSPACE}_test_sessions_on"

# Verify
ls -l workspace/*test_sessions_on/
```

---

### Phase 3: Compare Results

**Goal:** Quantify and qualify the improvement from session management.

#### Quantitative Comparison

**1. Count Total Ambiguities:**
```bash
echo "=== Ambiguity Count Comparison ==="
echo "Baseline (sessions OFF):"
jq 'length' workspace/*baseline_sessions_off/ambiguities.json

echo "Test (sessions ON):"
jq 'length' workspace/*test_sessions_on/ambiguities.json
```

**2. Severity Distribution:**
```bash
echo "=== Severity Distribution ==="
echo "Baseline:"
jq '[.[] | .severity] | group_by(.) | map({severity: .[0], count: length})' \
   workspace/*baseline_sessions_off/ambiguities.json

echo "Test:"
jq '[.[] | .severity] | group_by(.) | map({severity: .[0], count: length})' \
   workspace/*test_sessions_on/ambiguities.json
```

**3. Context-Dependent Sections:**

For documents testing specific section dependencies, extract those sections:
```bash
# Example: Extract sections 4-7 (adjust based on test document)
echo "=== Context-Dependent Sections ==="
for i in 4 5 6 7; do
    echo "Section $i - Baseline:"
    jq ".section_$i.results | to_entries[] | {model: .key, assumptions: .value.assumptions}" \
       workspace/*baseline_sessions_off/test_results.json

    echo "Section $i - Test:"
    jq ".section_$i.results | to_entries[] | {model: .key, assumptions: .value.assumptions}" \
       workspace/*test_sessions_on/test_results.json
done
```

#### Qualitative Analysis

**1. Open Reports Side by Side:**
```bash
# Open baseline report
open workspace/*baseline_sessions_off/report.md

# Open test report
open workspace/*test_sessions_on/report.md
```

**2. Focus Areas:**
- Sections that depend on earlier context (document-specific)
- Model assumptions about undefined terms
- Ambiguities related to missing context
- Model agreement vs disagreement on interpretations

**3. Look For:**
- **Baseline:** "Undefined term", "unclear reference", "assuming X means Y"
- **Test:** Correct references to earlier definitions, fewer assumptions

---

## Success Criteria

### Quantitative Thresholds

- ✅ **Overall Improvement:** At least 50% reduction in total ambiguities
- ✅ **Context Improvement:** At least 75% reduction in context-related ambiguities
- ✅ **Severity Improvement:** Reduction in high/critical severity ambiguities

### Qualitative Indicators

- ✅ **Term Understanding:** Models correctly reference definitions from early sections
- ✅ **Assumption Reduction:** Fewer "assuming X" statements in test run
- ✅ **Model Agreement:** Higher agreement between models when sharing context
- ✅ **No Undefined Terms:** Zero "undefined term" errors in test run for defined terms

---

## Comparison Script

**Automated comparison script:**

```bash
#!/bin/bash
# compare_sessions.sh
# Usage: ./compare_sessions.sh test_context_terms_definitions

TEST_DOC=$1
BASE_DIR="$(pwd)"

BASELINE_WS=$(ls -t workspace | grep "${TEST_DOC}.*baseline_sessions_off" | head -1)
TEST_WS=$(ls -t workspace | grep "${TEST_DOC}.*test_sessions_on" | head -1)

if [ -z "$BASELINE_WS" ] || [ -z "$TEST_WS" ]; then
    echo "ERROR: Could not find both baseline and test workspaces"
    echo "Baseline: $BASELINE_WS"
    echo "Test: $TEST_WS"
    exit 1
fi

echo "=== Session Management Testing Comparison ==="
echo ""
echo "Test Document: $TEST_DOC"
echo "Baseline: $BASELINE_WS"
echo "Test: $TEST_WS"
echo ""

echo "--- Ambiguity Counts ---"
BASELINE_COUNT=$(jq 'length' "workspace/$BASELINE_WS/ambiguities.json")
TEST_COUNT=$(jq 'length' "workspace/$TEST_WS/ambiguities.json")
IMPROVEMENT=$((BASELINE_COUNT - TEST_COUNT))
IMPROVEMENT_PCT=$(echo "scale=1; $IMPROVEMENT * 100 / $BASELINE_COUNT" | bc)

echo "Baseline: $BASELINE_COUNT ambiguities"
echo "Test: $TEST_COUNT ambiguities"
echo "Improvement: $IMPROVEMENT fewer ambiguities ($IMPROVEMENT_PCT% reduction)"
echo ""

echo "--- Severity Distribution ---"
echo "Baseline:"
jq '[.[] | .severity] | group_by(.) | map({severity: .[0], count: length})' \
   "workspace/$BASELINE_WS/ambiguities.json"
echo ""
echo "Test:"
jq '[.[] | .severity] | group_by(.) | map({severity: .[0], count: length})' \
   "workspace/$TEST_WS/ambiguities.json"
echo ""

echo "=== Analysis Complete ==="
echo "Review detailed reports:"
echo "  Baseline: workspace/$BASELINE_WS/report.md"
echo "  Test: workspace/$TEST_WS/report.md"
```

**Save as:** `test/compare_sessions.sh`
**Usage:** `./test/compare_sessions.sh test_context_terms_definitions`

---

## Document-Specific Testing Notes

Each test document has specific context dependencies to validate. Document these for each test:

### Example: test_context_terms_definitions.md

**Context Dependencies:**
- Section 2 defines 4 technical terms: Ghost Node, Liquidity Injection, The Meridian, Glass Mode
- Sections 4-7 use these terms without re-explanation

**Focus Sections:** 4, 5, 6, 7

**Expected Baseline Behavior:**
- Models report "undefined term" for all 4 terms
- Models make conflicting assumptions about term meanings
- High severity ambiguities in sections 4-7

**Expected Test Behavior:**
- Models correctly reference definitions from section 2
- Models use consistent term interpretations
- Low/no ambiguities related to the 4 defined terms

**Term Validation:**
1. Ghost Node → "strictly local, in-memory-only database replica"
2. Liquidity Injection → "padding data payloads under 1KB with 0x00 bytes to 1024 bytes"
3. The Meridian → "calculated timestamp when network latency is historically lowest"
4. Glass Mode → "write-only state where read logs are suppressed"

---

## Troubleshooting

### Issue: Workspace Directory Not Found

**Symptom:** Cannot find workspace directory after run

**Solution:**
```bash
# List all workspaces with timestamp
ls -lt workspace/

# Find specific test document workspaces
ls -lt workspace/ | grep "test_context"
```

### Issue: Session Creation Fails

**Symptom:** Polish script reports session initialization errors

**Solution:**
- Verify CLI tools are installed: `claude --version`, `gemini --version`, `codex --version`
- Check `config.yaml` has correct command paths
- Try with single model: `--models claude`
- Check `workspace/polish_*/polish.log` for detailed errors

### Issue: No Improvement Observed

**Symptom:** Similar ambiguity counts in both runs

**Potential Causes:**
1. **Test document not context-dependent enough** - Review test document design
2. **Session management not actually enabled** - Verify config.yaml change
3. **Models already handle context well** - Test document may not challenge models sufficiently

**Investigation:**
```bash
# Verify sessions were used (check log)
grep "Step 1.5: Initializing model sessions" workspace/*test_sessions_on/polish.log

# If not found, sessions were NOT enabled - check config.yaml
```

---

## Results Documentation

After completing comparison, document results:

**Create:** `test/results/{test_document_name}_results_{date}.md`

**Template:**
```markdown
# Session Management Test Results

**Test Document:** {test_document_name}.md
**Date:** {YYYY-MM-DD}
**Models:** claude, gemini, codex

## Quantitative Results

| Metric | Baseline (OFF) | Test (ON) | Improvement |
|--------|----------------|-----------|-------------|
| Total Ambiguities | X | Y | Z (-P%) |
| Critical Severity | A | B | C (-Q%) |
| High Severity | D | E | F (-R%) |

## Qualitative Observations

### Baseline Behavior (Sessions OFF)
- List key observations
- Typical errors/assumptions
- Sections with most confusion

### Test Behavior (Sessions ON)
- Improvements observed
- Correct context usage
- Remaining issues

## Context-Specific Analysis

Focus sections: [list section numbers]

### Term/Concept: [Name]
- Baseline: [how models handled it]
- Test: [improvement observed]

## Conclusion

[Overall assessment: Did session management achieve its goal?]

## Next Steps

[Recommendations for configuration tuning or further testing]
```

---

## Notes

- Test one document at a time (sequential execution required)
- Preserve all workspace outputs for future reference
- Document any anomalies or unexpected behaviors
- If testing multiple documents, compare relative improvement across documents

---

**Version History:**
- 1.0 (2025-12-12): Initial procedure created
