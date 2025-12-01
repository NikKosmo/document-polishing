# Documentation Polishing - Quick Reference Guide

**Version:** 1.0  
**Date:** 2025-11-19  
**Purpose:** Quick reference and practical checklist for documentation polishing

---

## 🚀 Quick Start Commands

### One-Line Polish (Default Settings)
```bash
# Basic polish with 2 models
python polish_document.py auto --document WORKFLOW.md

# With specific models
python polish_document.py auto --document WORKFLOW.md --models claude,gemini,gpt4

# Thorough polish for critical docs
python polish_document.py auto --document CRITICAL.md --profile critical --require-unanimous
```

### Step-by-Step Polish
```bash
# 1. Initialize session
python polish_document.py init --document WORKFLOW.md --profile standard

# 2. Run tests
python test_runner.py --session polish_20251119_143052

# 3. Detect ambiguities
python ambiguity_detector.py --session polish_20251119_143052

# 4. Generate fixes
python fix_generator.py --session polish_20251119_143052

# 5. Apply fixes
python polish_document.py apply-fixes --session polish_20251119_143052

# 6. Validate
python validator.py --session polish_20251119_143052
```

---

## 📋 Pre-Polish Checklist

### Document Readiness
- [ ] Document is complete (no TODOs or placeholders)
- [ ] All examples are included and tested
- [ ] Version number and date are current
- [ ] Document is in version control
- [ ] Backup created

### Environment Setup
- [ ] Python 3.8+ installed
- [ ] Required packages installed (`pip install -r requirements.txt`)
- [ ] At least 2 AI models configured
- [ ] API keys set in environment variables
- [ ] Sufficient API credits/quota

### Model Configuration
```bash
# Set environment variables
export CLAUDE_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GEMINI_CLI_PATH="/usr/local/bin/gemini"

# Test connectivity
python test_connectivity.py
```

---

## 🎯 Ambiguity Detection Patterns

### Critical Ambiguities (Must Fix)

| Pattern | Example | Why It's Ambiguous |
|---------|---------|-------------------|
| Quantifier confusion | "Create N cards" | N per word? N total? |
| Implicit expansion | "..." or "etc." | What's included? |
| Pronoun without antecedent | "Do this for each" | Each what? |
| Conditional without else | "If X, do Y" | What if not X? |
| Format assumption | "Standard format" | Which standard? |

### Major Ambiguities (Should Fix)

| Pattern | Example | Why It's Ambiguous |
|---------|---------|-------------------|
| Order dependency | "First X then Y" | Can Y happen without X? |
| Scope unclear | "All words" | All in document? All in section? |
| Default behavior | "Usually does X" | When doesn't it? |
| Example mismatch | Text says X, example shows Y | Which is correct? |

### Minor Ambiguities (Consider Fixing)

| Pattern | Example | Why It's Ambiguous |
|---------|---------|-------------------|
| Passive voice | "Is processed" | By what/whom? |
| Missing units | "Timeout: 30" | Seconds? Minutes? |
| Relative terms | "Large file" | How large? |

---

## 🔧 Fix Strategies Quick Reference

### Strategy Selection Matrix

| Ambiguity Type | Best Strategy | Example Fix |
|----------------|---------------|-------------|
| Quantity unclear | Explicit table | Use exact numbers in table format |
| Process order | Numbered steps | Convert to 1, 2, 3 format |
| Format unclear | Complete example | Show full JSON/YAML example |
| Multiple interpretations | Explicit NOT/CORRECT | State what NOT to do, then correct way |
| Edge cases missing | Comprehensive list | Add "Edge Cases" section |
| Conditional branches | Decision tree | Use if-then-else flowchart |

### Fix Templates

#### Explicit Clarification Template
```markdown
**CLARIFICATION:** 
- ❌ NOT: [incorrect interpretation]
- ✅ CORRECT: [correct interpretation]
- 📝 SPECIFICALLY: [detailed explanation]
```

#### Structured Table Template
```markdown
| Requirement | Details | Example |
|-------------|---------|---------|
| What to create | [specific] | [example] |
| How many | [exact number] | [example] |
| Format | [exact format] | [example] |
```

#### Complete Example Template
```markdown
**Complete Example:**
Input: [exact input]
Process: [step-by-step what happens]
Output: [exact output]
Note: [key point to remember]
```

---

## 📊 Testing Depth Profiles

### Profile Comparison

| Profile | Use Case | Sections Tested | Agents/Model | Iterations | Time (est.) |
|---------|----------|-----------------|---------------|------------|-------------|
| `quick` | Rapid check | Key sections only | 1 | 1 | 5-10 min |
| `standard` | Most docs | All instructions | 3 | 2 | 15-30 min |
| `thorough` | Important docs | Everything | 5 | 3 | 45-60 min |
| `critical` | Compliance/Legal | Everything + stress | 10 | 5 | 2-3 hours |

### When to Use Each Profile

```yaml
quick:
  - Draft documents
  - Minor updates
  - Time-sensitive fixes
  
standard:
  - Production documentation
  - Process workflows
  - API documentation
  
thorough:
  - User-facing guides
  - Installation instructions
  - Migration guides
  
critical:
  - Security procedures
  - Compliance documentation
  - Financial processes
  - Healthcare protocols
```

---

## 🎬 Common Scenarios

### Scenario 1: New Workflow Documentation
```bash
# 1. Start with quick profile to catch obvious issues
python polish_document.py auto --document NEW_WORKFLOW.md --profile quick

# 2. Review and fix critical issues
# 3. Run standard polish
python polish_document.py auto --document NEW_WORKFLOW.md --profile standard

# 4. Final validation with multiple models
python polish_document.py auto --document NEW_WORKFLOW.md --models claude,gemini,gpt4,llama
```

### Scenario 2: Updating Existing Documentation
```bash
# 1. Backup current version
cp EXISTING.md backups/EXISTING_$(date +%Y%m%d).md

# 2. Polish with focus on changed sections
python polish_document.py auto --document EXISTING.md --focus-changes

# 3. Generate diff report
python polish_document.py diff --old backups/EXISTING_*.md --new polished/EXISTING.md
```

### Scenario 3: Multi-Language Documentation
```bash
# Polish each language version
for lang in en de es fr; do
  python polish_document.py auto --document README_$lang.md --language $lang
done

# Cross-reference for consistency
python polish_document.py cross-reference --documents README_*.md
```

---

## 📈 Success Metrics

### Agreement Score Interpretation

| Score | Meaning | Action |
|-------|---------|--------|
| 95-100% | Excellent clarity | Ready for use |
| 90-94% | Good clarity | Minor fixes optional |
| 80-89% | Acceptable | Fix major ambiguities |
| 70-79% | Needs work | Significant revision needed |
| <70% | Poor clarity | Major rewrite recommended |

### Quality Indicators

✅ **Good Signs:**
- All models produce identical interpretations
- No assumptions needed by models
- Examples match descriptions
- Edge cases are covered

⚠️ **Warning Signs:**
- Models make different assumptions
- "I would assume..." appears in responses
- Examples conflict with text
- Missing error handling

❌ **Red Flags:**
- Completely different implementations by models
- Critical steps interpreted differently
- Safety/security instructions ambiguous
- Legal/compliance text unclear

---

## 🛠️ Troubleshooting Quick Fixes

### API Issues
```bash
# Rate limiting
--delay 2 --retry-count 3

# Timeout issues
--timeout 60 --batch-size 5

# Authentication problems
export CLAUDE_API_KEY="new_key"
python test_connectivity.py
```

### Performance Issues
```bash
# Large documents
--chunk-size 1000 --parallel-workers 5

# Memory problems
--low-memory-mode --clear-cache

# Slow processing
--profile quick --models claude,gemini  # Use fewer models
```

### Quality Issues
```bash
# Low agreement scores
--profile thorough --iterations 5

# Persistent ambiguities
--strategy redundant --add-examples

# Model disagreements
--require-majority --min-agreement 0.8
```

---

## 📝 Output Files Reference

### Session Directory Structure
```
workspace/polish_20251119_143052/
├── original.md                    # Backup of original
├── iterations/
│   ├── 1/
│   │   ├── test_catalog.json     # What was tested
│   │   ├── test_responses.json   # Model responses
│   │   ├── ambiguities.json      # Found issues
│   │   ├── fixes.json            # Proposed fixes
│   │   └── polished_v1.md       # Result of iteration 1
│   └── 2/                        # Second iteration...
├── reports/
│   ├── summary.md                # Human-readable report
│   ├── ambiguity_catalog.json   # All ambiguities found
│   ├── model_analysis.json      # Model behavior patterns
│   └── changes.diff             # All changes made
└── final/
    ├── polished.md              # Final polished document
    └── validation.json          # Final validation results
```

---

## 🏃 Quick Command Reference

### Essential Commands
```bash
# Test setup
python test_connectivity.py

# Quick polish
python polish_document.py auto --document FILE.md

# Check specific section
python polish_document.py test --document FILE.md --section "Step 4"

# View ambiguities without fixing
python polish_document.py analyze --document FILE.md --dry-run

# Apply specific fix strategy
python polish_document.py fix --document FILE.md --strategy explicit

# Validate existing document
python validator.py --document FILE.md --models claude,gemini,gpt4

# Generate report only
python report_generator.py --session SESSION_ID
```

### Advanced Commands
```bash
# Multi-agent consistency test
python test_runner.py multi-agent --document FILE.md --agents 10

# Stress test with edge cases
python polish_document.py stress --document FILE.md --include-edge-cases

# Compare two versions
python polish_document.py compare --old v1.md --new v2.md

# Batch polish multiple files
find . -name "*.md" -exec python polish_document.py auto --document {} \;

# Polish with custom prompt template
python polish_document.py auto --document FILE.md --prompt-template custom.txt

# Export results to different format
python polish_document.py export --session SESSION_ID --format html
```

---

## 🎯 Best Practices Summary

### DO ✅
- Start with `quick` profile for initial assessment
- Use at least 3 different models for critical docs
- Review and approve fixes before applying to production
- Keep original backups
- Document why changes were made
- Test polished docs with actual implementation

### DON'T ❌
- Skip validation after applying fixes
- Ignore minor ambiguities (they compound)
- Polish incomplete drafts
- Use only one model for testing
- Apply all fixes blindly
- Polish without version control

### ALWAYS 🔄
- Run at least 2 iterations
- Check examples match descriptions
- Validate with different model than generated fixes
- Update version number after polishing
- Create session logs
- Test edge cases

---

## 📚 Additional Resources

### Configuration Templates
- [`config/models.yaml`](./config/models.yaml) - Model configurations
- [`config/profiles.yaml`](./config/profiles.yaml) - Test profiles
- [`config/prompts/`](./config/prompts/) - Prompt templates

### Example Reports
- [`examples/report_summary.md`](./examples/report_summary.md)
- [`examples/ambiguity_catalog.json`](./examples/ambiguity_catalog.json)
- [`examples/polished_workflow.md`](./examples/polished_workflow.md)

### Scripts
- [`scripts/polish_document.py`](./scripts/polish_document.py) - Main script
- [`scripts/test_runner.py`](./scripts/test_runner.py) - Test executor
- [`scripts/validator.py`](./scripts/validator.py) - Validation tool

---

**Remember:** The goal is not perfection, but clarity that leads to consistent interpretation across different AI models and human readers.
