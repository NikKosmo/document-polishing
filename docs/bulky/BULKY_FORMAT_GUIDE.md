# Bulky Format Authoring Guide

**Version:** 1.0
**Created:** 2026-01-11
**Purpose:** Guide for writing documentation using the bulky-clean architecture

---

## Table of Contents

1. [Overview](#overview)
2. [Format Reference](#format-reference)
3. [Assertion Guidelines](#assertion-guidelines)
4. [Examples](#examples)
5. [Workflow](#workflow)
6. [Best Practices](#best-practices)

---

## Overview

### What is Bulky-Clean Architecture?

Bulky-clean is a **source/build system for documentation** that separates:

- **Bulky docs** (source): Documentation with embedded metadata, assertions, and test markers
- **Clean docs** (build): Stripped versions for LLM consumption with metadata removed

### Why Use This Format?

1. **Testability**: Assertions enable automated comprehension testing
2. **Traceability**: Metadata tracks versions, sources, and polish history
3. **Quality**: Questions derived from assertions validate LLM understanding
4. **Maintainability**: Single source of truth with clear test markers

### Key Principle

**Bulky docs are the source of truth. Clean docs are generated artifacts.**

Never edit clean docs directly - always edit bulky source and regenerate.

---

## Format Reference

### Metadata Format

Bulky format uses **HTML comments** for metadata, making it:
- Tool-agnostic (works in any text editor)
- Markdown-compatible (doesn't break rendering)
- Easy to strip (simple line-by-line processing)

### Two Metadata Types

| Type | Purpose | Stripped Output |
|------|---------|-----------------|
| **Block** | Document-level metadata | Removed entirely (all lines) |
| **Wrapper** | Section-level metadata around content | Tags removed, content preserved |

---

## Format Reference: @meta Blocks

### Purpose

Document-level metadata providing context about the entire document.

### Syntax

```markdown
<!-- @meta
key1: value1
key2: value2
key3: value3
-->
```

### Standard Fields

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `version` | Yes | Semantic version | `1.0`, `2.1` |
| `created` | Yes | Creation date | `2026-01-11` |
| `last_polished` | Yes | Last polish date or "never" | `2026-01-10`, `never` |
| `status` | Yes | Document status | `draft`, `active`, `deprecated` |
| `source` | No | Origin/authority | `Industry research + user interview` |
| `polished_by` | No | Polishing system | `polish.py v1.2.3` |
| `test_results` | No | Last test summary | `8 assertions, 88% accuracy` |

### Example

```markdown
<!-- @meta
version: 2.0
created: 2026-01-10
last_polished: never
status: active
source: Industry research + user workflow interview
-->

# Git Workflow Rules
```

### Strip Behavior

**Entire block removed** - all lines from opening `<!-- @meta` to closing `-->` are deleted.

---

## Format Reference: @assertion Wrappers

### Purpose

Mark testable content sections that will be used to generate comprehension questions.

### Syntax

```markdown
<!-- @assertion id="unique_id" type="assertion_type" priority="level" -->
[Content to be tested]
<!-- @/assertion -->
```

### Required Attributes

| Attribute | Required | Description | Values |
|-----------|----------|-------------|--------|
| `id` | Yes | Unique identifier | `rule1_branch_creation` |
| `type` | Yes | Assertion category | See types below |
| `priority` | Yes | Importance level | `critical`, `high`, `medium`, `low` |

### Assertion Types

| Type | Description | Use When | Example |
|------|-------------|----------|---------|
| `requirement` | Must-have behavior | Mandatory actions | "All work must be done on feature branches" |
| `constraint` | Limitation or boundary | Restrictions, limits | "Maximum 1000 entries per batch" |
| `behavior` | Expected system action | How system responds | "System retries on connection failure" |
| `sequence` | Ordered steps | Workflows, procedures | "Step 1: Init, Step 2: Process, Step 3: Export" |
| `error` | Error conditions | Failure modes | "Returns 404 if resource not found" |

### Priority Levels

| Level | Meaning | Use When | Impact if Wrong |
|-------|---------|----------|-----------------|
| `critical` | Core functionality | Violations break system | Severe (data loss, security) |
| `high` | Important feature | Violations degrade experience | High (incorrect behavior) |
| `medium` | Supporting detail | Violations cause confusion | Medium (unclear process) |
| `low` | Nice-to-know | Violations minor annoyance | Low (cosmetic) |

### ID Naming Convention

Format: `section_concept_detail`

**Examples:**
- `rule1_branch_creation` - Rule 1, concept: branch creation
- `rule3_merge_strategy` - Rule 3, concept: merge strategy
- `rule5_hotfix_workflow` - Rule 5, concept: hotfix workflow
- `error_timeout_handling` - Error section, concept: timeout handling

**Guidelines:**
- Use lowercase with underscores
- Start with section identifier (rule1, config, error, etc.)
- Be descriptive but concise
- Avoid version numbers (they change)

### Example

```markdown
<!-- @assertion id="rule1_branch_creation" type="requirement" priority="high" -->
**All work must be done on feature branches, never directly on main.**

Branch naming conventions:
- `feature/description` - New features
- `fix/description` - Bug fixes
- `hotfix/description` - Emergency production fixes
<!-- @/assertion -->
```

### Strip Behavior

**Tags removed, content preserved** - only the `<!-- @assertion ... -->` and `<!-- @/assertion -->` lines are removed. All content between them remains.

**Before strip:**
```markdown
<!-- @assertion id="example" type="requirement" priority="high" -->
**Content here.**
<!-- @/assertion -->
```

**After strip:**
```markdown
**Content here.**
```

---

## Assertion Guidelines

### Writing Effective Assertions

#### 1. Single Concept Per Assertion

❌ **Bad** (multiple concepts):
```markdown
<!-- @assertion id="rules_everything" type="requirement" priority="high" -->
All PRs require review. Use feature branches. Merge with rebase+squash.
<!-- @/assertion -->
```

✅ **Good** (one concept):
```markdown
<!-- @assertion id="rule3_pr_review" type="requirement" priority="critical" -->
**Every PR must be reviewed before merge - no exceptions.**
<!-- @/assertion -->

<!-- @assertion id="rule3_merge_strategy" type="constraint" priority="critical" -->
**Default merge strategy: Rebase and squash.**
<!-- @/assertion -->
```

#### 2. Clear and Explicit

❌ **Bad** (ambiguous):
```markdown
Validate data appropriately before processing.
```

✅ **Good** (explicit):
```markdown
**All input fields must be validated before processing.**
- Check required fields are non-empty
- Verify field types match schema
- Reject if validation fails
```

#### 3. Testable Content

Ask: "Can I write a question to test this?"

❌ **Bad** (not testable):
```markdown
The system is designed to be scalable and maintainable.
```

✅ **Good** (testable):
```markdown
**The system supports up to 10,000 concurrent users.**
Performance degrades gracefully beyond this limit.
```

**Test question:** "What is the maximum number of concurrent users?"

#### 4. Include Context

Provide enough context for standalone understanding:

❌ **Bad** (missing context):
```markdown
Timeout is 30 seconds.
```

✅ **Good** (contextual):
```markdown
**API requests timeout after 30 seconds.**
After timeout, the system:
1. Logs the timeout error
2. Returns 504 Gateway Timeout
3. Does not retry automatically
```

### Assertion Density Guidelines

| Document Section | Assertions/Page | Reasoning |
|------------------|-----------------|-----------|
| Core rules | 3-5 | Dense coverage of critical behavior |
| Configuration | 2-3 | Each config option testable |
| Examples | 1-2 | Test interpretation of examples |
| Background/intro | 0-1 | Context, not testable rules |

### Priority Assignment

**Critical:** Ask "Would misunderstanding this cause data loss, security issue, or system breakage?"

**High:** Ask "Would misunderstanding this lead to incorrect behavior or workflow failure?"

**Medium:** Ask "Would misunderstanding this cause confusion but not prevent completion?"

**Low:** Ask "Is this a nice-to-know detail with minimal impact?"

---

## Examples

### Example 1: Requirement with List

```markdown
<!-- @assertion id="rule1_branch_creation" type="requirement" priority="high" -->
**All work must be done on feature branches, never directly on main.**

Branch naming conventions:
- `feature/description` - New features
- `fix/description` - Bug fixes
- `hotfix/description` - Emergency production fixes
- `refactor/description` - Code refactoring
<!-- @/assertion -->
```

**Testable questions:**
- "Where should all work be done?"
- "Is it allowed to commit directly to main?"
- "What branch naming convention is used for bug fixes?"

---

### Example 2: Constraint with Specifics

```markdown
<!-- @assertion id="rule3_merge_strategy" type="constraint" priority="critical" -->
**Default merge strategy: Rebase and squash.**

This creates one logical commit per PR with:
- All changes from the feature branch combined into single commit
- Linear history (no merge commits)
- Commit message from PR title/description

All PRs use rebase+squash unless user explicitly chooses alternative.
<!-- @/assertion -->
```

**Testable questions:**
- "What is the default merge strategy?"
- "How many commits are created per PR with the default strategy?"
- "When should alternatives to rebase+squash be used?"

---

### Example 3: Sequence with Steps

```markdown
<!-- @assertion id="rule5_hotfix_workflow" type="sequence" priority="critical" -->
**Even in emergencies, follow PR workflow with expedited review.**

Hotfix procedure:
1. Create hotfix branch from main: `hotfix/description`
2. Commit fix with clear description
3. Push and create PR with `[HOTFIX]` prefix in title
4. Notify team via Slack/email for expedited review
5. Review happens within minutes (not skipped)
6. User merges after approval

**Key principle:** Emergency = fast review, NOT no review.
<!-- @/assertion -->
```

**Testable questions:**
- "What is the first step in the hotfix workflow?"
- "Can reviews be skipped in emergencies?"
- "What does 'emergency' mean in the context of hotfixes?"

---

### Example 4: Behavior with Conditions

```markdown
<!-- @assertion id="error_retry_behavior" type="behavior" priority="high" -->
**System automatically retries failed API calls up to 3 times.**

Retry behavior:
- **Retry triggers:** Network errors, 5xx server errors, timeouts
- **No retry:** 4xx client errors (bad request, auth failure)
- **Backoff:** Exponential (1s, 2s, 4s)
- **After 3 failures:** Log error, return failure to caller
<!-- @/assertion -->
```

**Testable questions:**
- "How many times does the system retry failed API calls?"
- "Does the system retry on 404 errors?"
- "What is the backoff strategy between retries?"

---

### Example 5: Error Condition

```markdown
<!-- @assertion id="error_empty_input" type="error" priority="medium" -->
**Empty input files are rejected with error.**

When input file is empty (0 bytes):
- Log: "Input file empty: [filename]"
- Return: Error code 400 (Bad Request)
- Message: "Input file must contain at least one record"
- **Do not proceed** with processing
<!-- @/assertion -->
```

**Testable questions:**
- "What happens when the input file is empty?"
- "What error code is returned for empty input?"
- "Does the system attempt to process empty files?"

---

## Workflow

### 1. Write Bulky Source

Create or edit documentation with `@meta` blocks and `@assertion` wrappers:

```bash
# Work in bulky source directory
vim docs/bulky/git_workflow.md
```

**Include:**
- `@meta` block at top with version, dates, status
- `@assertion` wrappers around all testable content
- Clear IDs, appropriate types, accurate priorities

### 2. Strip to Generate Clean

Run strip script to generate clean version:

```bash
cd scripts
python3 strip_metadata.py ../docs/bulky/git_workflow.md > ../docs/clean/git_workflow.md
```

**Verify:**
- Metadata removed
- Content preserved
- Line counts match (content lines identical)

### 3. Test Comprehension

Generate questions from assertions and test LLM understanding:

```bash
# Future: Automated question generation from assertions
# For now: Manual question writing based on assertions

# Test with multiple models
cat docs/clean/git_workflow.md | gemini "Based on rules above: [question]"
cat docs/clean/git_workflow.md | codex exec "Based on rules above: [question]"
```

**Validate:**
- Questions answerable from assertions
- Questions don't leak answers
- Multiple models tested (3+ recommended)
- Results documented

### 4. Iterate Based on Results

**If tests reveal issues:**

1. Analyze which assertions caused failures
2. Edit bulky source to clarify
3. Re-strip to generate clean
4. Re-test to verify improvement

**Common fixes:**
- Add missing context to assertions
- Split multi-concept assertions
- Increase priority for commonly-failed items
- Remove contradictory assertions

### 5. Update Metadata

After polishing cycle, update `@meta` block:

```markdown
<!-- @meta
version: 2.1
created: 2026-01-10
last_polished: 2026-01-11
status: active
source: Industry research + user workflow interview
polished_by: manual testing, 2 models
test_results: 8 assertions, 88% accuracy (improved from 13%)
-->
```

---

## Best Practices

### DO ✅

1. **Write for LLMs**: Be explicit, avoid ambiguity, provide context
2. **Test-driven**: Ask "what question would test this?" when writing assertions
3. **Single source**: Keep bulky as source of truth, regenerate clean from it
4. **Version everything**: Update version numbers when content changes
5. **Prioritize accurately**: Critical = breakage, High = incorrect behavior, Medium = confusion, Low = cosmetic
6. **Use clear IDs**: Descriptive, unique, follow naming convention
7. **Include examples**: Concrete examples make assertions testable
8. **Document changes**: Update `last_polished` and `test_results` in @meta

### DON'T ❌

1. **Don't edit clean docs**: Always edit bulky source, then strip
2. **Don't nest assertions**: One level only, no assertions inside assertions
3. **Don't write multi-concept assertions**: Split into separate assertions
4. **Don't use vague language**: "Usually", "typically", "might" → be specific
5. **Don't forget strip verification**: Always check clean doc was generated correctly
6. **Don't skip priorities**: Every assertion needs explicit priority
7. **Don't reuse IDs**: Each assertion must have unique identifier
8. **Don't assume context**: Assertions should be understandable with surrounding text only

### Common Pitfalls

#### Pitfall 1: Assertion Too Broad

❌ **Problem:**
```markdown
<!-- @assertion id="everything" type="requirement" priority="high" -->
Follow the PR workflow including branching, review, and merge.
<!-- @/assertion -->
```

✅ **Solution:** Break into separate assertions:
```markdown
<!-- @assertion id="rule1_branching" type="requirement" priority="high" -->
Create feature branch for all work
<!-- @/assertion -->

<!-- @assertion id="rule3_review" type="requirement" priority="critical" -->
Every PR requires review before merge
<!-- @/assertion -->

<!-- @assertion id="rule3_merge" type="constraint" priority="critical" -->
Default merge strategy: rebase and squash
<!-- @/assertion -->
```

#### Pitfall 2: Missing Test Context

❌ **Problem:**
```markdown
<!-- @assertion id="timeout" type="constraint" priority="medium" -->
Timeout is 30 seconds.
<!-- @/assertion -->
```

✅ **Solution:** Add context for standalone understanding:
```markdown
<!-- @assertion id="api_timeout" type="constraint" priority="high" -->
**API requests timeout after 30 seconds.**
- System logs timeout error
- Returns 504 Gateway Timeout to client
- Does not retry automatically (see retry policy)
<!-- @/assertion -->
```

#### Pitfall 3: Contradictory Assertions

❌ **Problem:**
```markdown
<!-- @assertion id="validate" type="requirement" priority="high" -->
Validate all input fields.
<!-- @/assertion -->

<!-- @assertion id="skip" type="requirement" priority="high" -->
Skip validation for optional empty fields.
<!-- @/assertion -->
```

**Issue:** Contradictory - what happens with optional empty fields?

✅ **Solution:** Clarify the relationship:
```markdown
<!-- @assertion id="validation_rules" type="requirement" priority="high" -->
**All required input fields must be validated.**
- Required fields: validate even if empty (reject empty)
- Optional fields: skip validation if empty, validate if present
<!-- @/assertion -->
```

---

## Tool-Agnostic Design

### Why HTML Comments?

- ✅ Work in any text editor (VS Code, vim, Sublime, Notepad)
- ✅ Markdown-compatible (don't break rendering)
- ✅ Easy to parse (line-by-line state machine)
- ✅ Human-readable (no special tools needed to read)
- ✅ Version control friendly (git diff works normally)

### No Editor Requirements

You don't need:
- ❌ Special IDE plugins
- ❌ Custom markdown extensions
- ❌ Proprietary editors
- ❌ WYSIWYG tools

You only need:
- ✅ Any text editor
- ✅ Python 3.x for strip script
- ✅ LLM access for testing (via CLI or API)

### Future Automation

The bulky format is designed to enable (but doesn't require):
- Automated question generation from assertions
- Integration with document polishing pipeline
- CI/CD testing of documentation comprehension
- Assertion coverage reporting

But these are **optional enhancements** - the format works standalone.

---

## Summary

### Quick Reference

| Element | Format | Purpose | Strip Behavior |
|---------|--------|---------|----------------|
| `@meta` | Block | Document metadata | Remove entirely |
| `@assertion` | Wrapper | Testable content | Remove tags only |

### Assertion Attributes

```markdown
<!-- @assertion id="unique_id" type="requirement" priority="critical" -->
```

- **id**: Unique, descriptive, lowercase_with_underscores
- **type**: requirement, constraint, behavior, sequence, error
- **priority**: critical, high, medium, low

### Workflow Summary

```
Write bulky → Strip to clean → Test comprehension → Iterate → Update metadata
```

### Key Principles

1. **Bulky = source of truth** (never edit clean directly)
2. **One concept per assertion** (split multi-concept assertions)
3. **Test-driven authoring** (ask "what question tests this?")
4. **Tool-agnostic format** (HTML comments + markdown)
5. **Explicit over implicit** (LLMs need clarity)

---

**Document Version:** 1.0
**Last Updated:** 2026-01-11
**Status:** Active

For questions or improvements, see project documentation or raise an issue.
