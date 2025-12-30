# Bulky-Clean Document Architecture Plan (Revised)

**Created:** 2025-12-30
**Revised:** 2025-12-30
**Status:** Active
**Context:** Practical implementation for polishing real documents, starting with git_workflow.md

---

## Executive Summary

**Goal:** Create source/build system for documentation that separates test metadata from LLM-consumable content.

**Approach:** Practice-focused, hands-on workflow using real documents that need polishing.

**Primary Document:** `git_workflow.md` (critical - robust git operation rules needed)

**Key Decisions (Based on Expert Review Synthesis):**
- ✅ Week 1: Minimal viable, practice workflow (not heavy validation)
- ✅ Strip: Non-regex, rule-based (newlines, exact line starts)
- ✅ Templates: Start with 2 (Constraint + Requirement)
- ✅ LLM Fallback: 40-50% expected and acceptable
- ✅ Integration: After proving value (Week 4)
- ✅ Tooling: JetBrains IDE, GitHub Actions, no pre-commit hooks
- ✅ Success: Polish 3-5 critical docs, establish working system

---

## Background

### The Problem

Documentation has two competing needs:
1. **For testing/maintenance:** Needs metadata, assertions, polishing history
2. **For LLM consumption:** Needs to be clean, focused, no artifacts

### The Solution

**Source/Build approach:**
- **Bulky docs** (source of truth): Contains all metadata, test markers
- **Clean docs** (build artifacts): Stripped for LLM consumption
- **Transform pipeline:** Deterministic, rule-based strip operation

### Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    DOCUMENT LIFECYCLE                         │
└──────────────────────────────────────────────────────────────┘

SOURCE: common_rules/bulky/git_workflow.md
├─ Document metadata (version, dates, status)
├─ Assertion markers (for question generation)
└─ Content (mixed with metadata)

         │
         ├──[strip.py]──────► common_rules/clean/git_workflow.md
         │                    └─► polish.py (comprehension)
         │                        └─► polished output
         │
         └──[extract.py]────► assertions.json
                              └─► generate_questions.py (SEPARATE)
                                  └─► test comprehension

DIRECTORY STRUCTURE:
projects/
├── common_rules/
│   ├── bulky/          # Source of truth (agents should NOT read)
│   │   └── git_workflow.md  # Has @meta, @assertion markers
│   │
│   └── clean/          # For LLM consumption (agents READ these)
│       └── git_workflow.md  # Stripped, pure documentation

PHASING:
  Phase 1: Practice workflow with git_workflow.md
  Phase 2: Add question templates (Constraint + Requirement)
  Phase 3: Integrate into polish.py (after proving value)
```

---

## Phase 1: Foundation (Week 1)

**Goal:** Practice the full workflow hands-on with real document
**Time:** 4-6 hours total
**Document:** `git_workflow.md` (441 lines, critical for git operations)

### 1.1 Bulky Document Format Specification

**Metadata Format (HTML comments with strict rules):**

**Design Principles:**
1. ✅ Always on own line (never inline)
2. ✅ Starts at beginning of line (`^<!--`)
3. ✅ Ends on own line (`-->$`)
4. ✅ Blank lines before/after for clarity

**This makes strip operation simple without regex.**

**Example Format:**

```markdown
<!-- @meta
version: 1.0
created: 2025-12-30
last_polished: never
status: active
-->

# Git Workflow Rules

**Purpose:** Define standard Git workflow for all projects.

<!-- @assertion id="rule1_requirement" type="requirement" priority="critical" -->
**Rule 1: NEVER Push Directly to Main**

CRITICAL: Always use feature branches and pull requests.
<!-- @/assertion -->

---

## Branch Protection

<!-- @assertion id="public_repos_constraint" type="constraint" priority="high" -->
### Public Repositories
- Branch protection enabled via GitHub (strict mode)
- Requires pull request with 1 approval
<!-- @/assertion -->
```

**Assertion Types (Starting with 2):**

| Type | Description | Example | Template Priority |
|------|-------------|---------|------------------|
| **requirement** | Must/required/shall statements | "All input MUST be validated" | **Phase 2 Week 1** |
| **constraint** | Limits, boundaries, thresholds | "Max retries: 3", "Timeout: 30s" | **Phase 2 Week 1** |
| behavior | If/when/then conditions | "If error, retry" | Phase 2 Week 2 (optional) |
| error | Failure conditions | "Throws ValidationError" | Defer |
| sequence | Order-dependent steps | "Step 1 before Step 2" | Defer |

**Assertion Metadata Fields:**

```markdown
<!-- @assertion
    id="unique_id"           # Required: snake_case, doc-unique
    type="requirement"       # Required: see types above
    priority="critical"      # Optional: critical|high|medium|low
    difficulty="easy"        # Optional: trivial|easy|medium|hard
-->
Content here (can be multiple lines, paragraphs, code blocks)
<!-- @/assertion -->
```

**Document Metadata Fields:**

```markdown
<!-- @meta
version: 1.0              # Semantic version
created: YYYY-MM-DD       # Creation date
last_polished: YYYY-MM-DD # Last polishing run (or "never")
status: active            # active|deprecated|draft
-->
```

**Authoring Guidelines (What to Mark as Assertion):**

✅ **Mark these:**
- Requirements (must/required/shall/always/never)
- Constraints (limits, boundaries, max/min values)
- Critical rules (CRITICAL/IMPORTANT/WARNING)
- Failure conditions (errors, exceptions)
- Ordered sequences (Step 1, Step 2, etc.)

❌ **Don't mark these:**
- Background information
- Explanations of "why"
- Examples (unless example IS the requirement)
- Summaries or overviews
- Transitional text

**Rule of thumb:** "Would an LLM failing to understand this cause incorrect behavior?"

### 1.2 Strip Metadata Script (Non-Regex, Rule-Based)

**File:** `scripts/strip_metadata.py`

**Design Principles:**
1. No regex (hard to debug, fails on edge cases)
2. Line-by-line state machine
3. Track if we're inside metadata block
4. Only remove lines that match strict rules

**Algorithm:**

```
For each line:
  1. Check if line starts with "<!-- @" → Start of metadata block
  2. If inside metadata block:
     - Skip line (don't output)
     - Check if line is "-->" → End of metadata block
  3. If not inside metadata block:
     - Output line unchanged
  4. Clean up excessive blank lines at end
```

**Implementation (Simple, ~30 lines):**

```python
#!/usr/bin/env python3
"""
Strip metadata from bulky markdown documents.

Removes HTML comment blocks that start with @meta, @assertion, etc.
Uses line-by-line parsing, no regex.
"""

def strip_metadata(content: str) -> str:
    """
    Remove @-prefixed HTML comment blocks.

    Rules:
    - Metadata comments start with "<!-- @" at beginning of line
    - End with "-->" on its own line
    - Everything between is removed

    Args:
        content: Bulky markdown with metadata

    Returns:
        Clean markdown without metadata
    """
    lines = content.splitlines(keepends=True)
    output = []
    inside_metadata = False

    for line in lines:
        # Check if starting metadata block
        if line.lstrip().startswith('<!-- @'):
            inside_metadata = True
            continue

        # Check if ending metadata block
        if inside_metadata and line.strip() == '-->':
            inside_metadata = False
            continue

        # If inside metadata, skip
        if inside_metadata:
            continue

        # Otherwise, keep line
        output.append(line)

    # Join and clean up excessive blank lines
    result = ''.join(output)

    # Replace 3+ consecutive newlines with 2
    while '\n\n\n' in result:
        result = result.replace('\n\n\n', '\n\n')

    return result.strip() + '\n'


def validate_clean(bulky: str, clean: str) -> dict:
    """
    Validate that strip operation was successful.

    Checks:
    - No metadata leaked
    - Structure preserved (same number of headers)
    - Idempotent (strip(strip(x)) == strip(x))

    Returns:
        dict with 'valid' (bool) and 'issues' (list)
    """
    issues = []

    # Check: No leakage
    for marker in ['@meta', '@assertion']:
        if marker in clean:
            issues.append(f"Leaked marker: {marker}")

    # Check: Structure preserved (same headers)
    bulky_headers = [line for line in bulky.splitlines() if line.startswith('#')]
    clean_headers = [line for line in clean.splitlines() if line.startswith('#')]

    if len(bulky_headers) != len(clean_headers):
        issues.append(
            f"Header count mismatch: {len(bulky_headers)} bulky vs "
            f"{len(clean_headers)} clean"
        )

    # Check: Idempotent
    double_strip = strip_metadata(clean)
    if double_strip != clean:
        issues.append("Not idempotent: strip(strip(x)) != strip(x)")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'lines_removed': len(bulky.splitlines()) - len(clean.splitlines())
    }


if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        print("Usage: python strip_metadata.py <bulky-file>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        bulky_content = f.read()

    clean_content = strip_metadata(bulky_content)

    # Validate
    result = validate_clean(bulky_content, clean_content)

    if not result['valid']:
        print("ERROR: Validation failed:", file=sys.stderr)
        for issue in result['issues']:
            print(f"  - {issue}", file=sys.stderr)
        sys.exit(1)

    # Output clean content
    print(clean_content, end='')

    # Report to stderr
    print(f"Stripped {result['lines_removed']} lines", file=sys.stderr)
```

**Usage:**

```bash
# Strip bulky doc to stdout
python scripts/strip_metadata.py common_rules/bulky/git_workflow.md

# Save to clean directory
python scripts/strip_metadata.py common_rules/bulky/git_workflow.md > common_rules/clean/git_workflow.md

# Verify it worked
git check-ignore -v common_rules/clean/git_workflow.md  # Should be clean
grep -n '@assertion' common_rules/clean/git_workflow.md  # Should be empty
```

### 1.3 Week 1 Deliverables (Practice Workflow)

**Hands-on exercises to learn the system:**

#### Exercise 1: Create Bulky Version of git_workflow.md (2 hours)

**Steps:**

1. **Read current document** (15 min)
   - Location: `../common_rules/git_workflow.md`
   - Note: This is currently a "clean" doc (no metadata)

2. **Add @meta block** (15 min)
   ```markdown
   <!-- @meta
   version: 1.0
   created: 2025-12-02
   last_polished: never
   status: active
   -->
   ```

3. **Identify 5-8 assertions** (45 min)

   **Look for:**
   - CRITICAL/NEVER statements → `type="requirement" priority="critical"`
   - Rules (Rule 1, Rule 2) → `type="requirement"`
   - Branch protection settings → `type="constraint"`
   - Merge strategy defaults → `type="constraint"`
   - Workflow steps → `type="sequence"`

   **Example assertions to add:**

   ```markdown
   <!-- @assertion id="rule1_never_push_main" type="requirement" priority="critical" -->
   ### Rule 1: NEVER Push Directly to Main

   **CRITICAL:** Always use feature branches and pull requests. This rule applies
   regardless of branch protection status.
   <!-- @/assertion -->
   ```

   ```markdown
   <!-- @assertion id="merge_auth_constraint" type="requirement" priority="critical" -->
   **Merge authorization:**
   - ONLY the user can merge PRs - Claude Code must NOT execute merge commands
   - Claude can create PRs, review code, suggest changes, but merge requires explicit user action
   - User executes: `gh pr merge --rebase --delete-branch` (or equivalent)
   <!-- @/assertion -->
   ```

   ```markdown
   <!-- @assertion id="merge_strategy_default" type="constraint" priority="high" -->
   **Merge strategies:**
   - **Rebase and squash** (default) - Linear history, logically grouped commits
   - **Squash merge** - Alternative: single commit per PR (use for small changes)
   <!-- @/assertion -->
   ```

4. **Save as bulky version** (5 min)
   - Create: `common_rules/bulky/git_workflow.md`
   - Keep original clean version for comparison

5. **Validate format** (10 min)
   - All `<!-- @assertion` start at line beginning?
   - All have matching `<!-- @/assertion -->`?
   - Blank lines before/after?
   - IDs are unique?

**Success Criteria:**
- ✅ Bulky doc has @meta block
- ✅ 5-8 assertions added
- ✅ All assertions follow format rules
- ✅ Document still readable

#### Exercise 2: Build & Test Strip Script (1 hour)

**Steps:**

1. **Create strip script** (30 min)
   - File: `scripts/strip_metadata.py`
   - Copy implementation from section 1.2 above
   - Make executable: `chmod +x scripts/strip_metadata.py`

2. **Test on git_workflow.md** (15 min)
   ```bash
   # Strip to stdout
   python scripts/strip_metadata.py common_rules/bulky/git_workflow.md

   # Check: No @meta or @assertion in output
   python scripts/strip_metadata.py common_rules/bulky/git_workflow.md | grep '@assertion'
   # Should be empty

   # Save to clean dir
   mkdir -p common_rules/clean
   python scripts/strip_metadata.py common_rules/bulky/git_workflow.md > common_rules/clean/git_workflow.md
   ```

3. **Compare with original** (15 min)
   ```bash
   # Original clean doc
   wc -l common_rules/git_workflow.md

   # New clean doc
   wc -l common_rules/clean/git_workflow.md

   # Diff (should only show removed metadata lines)
   diff common_rules/git_workflow.md common_rules/clean/git_workflow.md
   ```

**Success Criteria:**
- ✅ Script runs without errors
- ✅ Clean output has no @meta or @assertion
- ✅ All headers preserved
- ✅ Content unchanged (except metadata removal)
- ✅ Idempotent: `strip(strip(x)) == strip(x)`

#### Exercise 3: Manual Question Writing (1 hour)

**Goal:** Practice writing questions from assertions to validate approach

**Steps:**

1. **Pick 3 assertions** from git_workflow.md (5 min)
   - Example: "NEVER push directly to main"
   - Example: "Merge authorization - ONLY user can merge"
   - Example: "Default merge strategy is rebase"

2. **Write 3 questions manually** (30 min)

   **Question 1 (from "NEVER push main"):**
   ```
   Q: According to the git workflow rules, when is it acceptable to commit
      directly to the main branch?
   A: Never, with exceptions only for: initial repo setup, emergency hotfixes
      (with notification), automated bot commits, and meta-repo submodule updates.

   Leakage check: Does question contain "never", "main", or "feature branch"?
   - "never" → YES (minimal, acceptable)
   - "main" → YES (necessary to identify subject)
   - "feature branch" → NO ✓
   ```

   **Question 2 (from "Merge authorization"):**
   ```
   Q: Who is authorized to execute the merge command for pull requests?
   A: Only the user. Claude Code can create PRs and review code but must NOT
      execute merge commands.

   Leakage check: Does question contain "user", "Claude", "merge"?
   - "merge" → YES (necessary to identify subject)
   - "user" or "Claude" → NO ✓
   ```

   **Question 3 (from "Default merge strategy"):**
   ```
   Q: What is the default merge strategy for pull requests?
   A: Rebase and squash (creates linear history with logically grouped commits)

   Leakage check: Does question contain "rebase", "squash", "default"?
   - "default" → YES (from question itself)
   - "rebase" or "squash" → NO ✓
   ```

3. **Test questions with LLM** (15 min)
   ```bash
   # Test: Give LLM clean doc + question
   # Does it answer correctly?
   # Does it fail if we remove the assertion?
   ```

4. **Evaluate** (10 min)
   - Were questions easy to write? (time per question)
   - Do they test real comprehension?
   - Would template generation work for these?

**Success Criteria:**
- ✅ 3 questions written
- ✅ Each took <10 minutes
- ✅ Questions found ≥1 real comprehension issue
- ✅ Leakage <10% (rough estimate)

#### Exercise 4: JetBrains IDE Snippet (30 min)

**Goal:** Reduce authoring friction with IDE tooling

**Steps:**

1. **Create live template** in IntelliJ/PyCharm
   - Settings → Editor → Live Templates
   - Add new template group: "Markdown Metadata"

2. **Add "assert" template:**
   ```
   Abbreviation: assert
   Description: Assertion block for bulky docs
   Template text:

   <!-- @assertion id="$ID$" type="$TYPE$" priority="$PRIORITY$" -->
   $CONTENT$
   <!-- @/assertion -->

   Variables:
   - ID: suggestVariableName()
   - TYPE: enum("requirement", "constraint", "behavior", "error", "sequence")
   - PRIORITY: enum("critical", "high", "medium", "low")
   - CONTENT: (cursor position)
   ```

3. **Add "meta" template:**
   ```
   Abbreviation: docmeta
   Description: Document metadata block
   Template text:

   <!-- @meta
   version: $VERSION$
   created: $DATE$
   last_polished: never
   status: active
   -->

   Variables:
   - VERSION: "1.0"
   - DATE: date("yyyy-MM-dd")
   ```

4. **Test templates:**
   - Type `assert` + Tab → Assertion block appears
   - Type `docmeta` + Tab → Metadata block appears

**Success Criteria:**
- ✅ Snippets installed
- ✅ Tested and working
- ✅ Reduces typing by ~80%

#### Exercise 5: Authoring Guide (30 min)

**Goal:** Document the format for future use

**File:** `docs/question_testing/BULKY_FORMAT_GUIDE.md`

**Contents:**
1. What is bulky vs clean (2 paragraphs)
2. When to use assertions (guidelines from 1.1)
3. Assertion format examples (copy from 1.1)
4. How to regenerate clean docs (command)
5. IDE snippet instructions

**Success Criteria:**
- ✅ One-page guide created
- ✅ Includes copy-paste examples
- ✅ Clear enough for future reference

### 1.4 Week 1 Success Criteria

**Must Complete:**
- [x] Bulky version of git_workflow.md created (5-8 assertions)
- [x] Strip script implemented and tested
- [x] Clean version generated and verified
- [x] 3 manual questions written
- [x] JetBrains snippet created

**Quality Checks:**
- [x] Clean doc has no @meta or @assertion strings
- [x] Clean doc has same headers as bulky
- [x] Strip is idempotent
- [x] Manual questions took <10 min each
- [x] Assertions are meaningful (test real comprehension)

**Decision Point:**
- **If manual questions find ≥1 real issue** → Proceed to Phase 2 ✅
- **If manual questions find 0 issues** → Reassess (are there real issues with git_workflow.md? try different doc?)

### 1.5 Optional: GitHub Actions Integration

**Only add if Week 1 goes smoothly and you want automation.**

**File:** `.github/workflows/check-bulky-clean.yml`

```yaml
name: Verify Bulky-Clean Sync

on:
  pull_request:
    paths:
      - 'common_rules/bulky/**'
      - 'common_rules/clean/**'

jobs:
  check-sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Check clean docs are stripped correctly
        run: |
          # Re-strip bulky docs
          for bulky_file in common_rules/bulky/*.md; do
            filename=$(basename "$bulky_file")
            clean_file="common_rules/clean/$filename"

            # Strip and compare
            python scripts/strip_metadata.py "$bulky_file" > /tmp/expected_clean.md

            if ! diff /tmp/expected_clean.md "$clean_file"; then
              echo "ERROR: $clean_file doesn't match stripped $bulky_file"
              exit 1
            fi
          done

          echo "✓ All clean docs match stripped bulky docs"

      - name: Check for metadata leakage
        run: |
          # Ensure no @meta or @assertion in clean docs
          if grep -r '@meta\|@assertion' common_rules/clean/; then
            echo "ERROR: Found metadata in clean docs"
            exit 1
          fi

          echo "✓ No metadata leakage in clean docs"
```

**Defer this to post-Week 1 unless you really want it.**

---

## Phase 2: Question Templates (Week 2-3)

**Goal:** Build templates for Requirement and Constraint assertion types
**Time:** 4-6 hours total
**Target:** 60%+ match rate (realistic, not 80%)

### 2.1 Design Templates from Real Data

**Approach:** Don't design patterns from idealized examples. Use actual assertions from git_workflow.md.

**Step 1: Extract All Assertions (30 min)**

After completing Phase 1, you'll have git_workflow.md with assertions. Extract them:

```bash
# Manual extraction for now
grep -A 5 '<!-- @assertion' common_rules/bulky/git_workflow.md > assertions_sample.txt

# Count by type
grep 'type="requirement"' assertions_sample.txt | wc -l
grep 'type="constraint"' assertions_sample.txt | wc -l
```

**Expected:** 5-8 assertions total, mix of requirement and constraint types.

**Step 2: Analyze Patterns (1 hour)**

For each type, look for common patterns:

**Requirement patterns (from git_workflow.md):**
- "NEVER [action]"
- "ONLY [subject] can [action]"
- "Always use [thing]"
- "MUST [action]"
- "[Subject] requires [condition]"

**Constraint patterns (from git_workflow.md):**
- "[Setting]: [value]"
- "Default [setting] is [value]"
- "[Thing] (default)"
- "Max/Min [thing]: [value]"

### 2.2 Build Template 1: Requirement

**Template:** `scripts/templates/requirement.py`

**Strategy:** Extract subject/action pairs, generate "what is required?" questions

```python
def match_requirement(assertion_text: str) -> dict | None:
    """
    Match requirement-type assertions.

    Patterns:
    - "NEVER [action]"
    - "ONLY [subject] can [action]"
    - "MUST [action]"
    - "Always use [thing]"

    Returns dict with question/answer or None if no match.
    """
    # Normalize text
    text = assertion_text.strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # Pattern 1: NEVER statements
    for line in lines:
        if 'NEVER' in line.upper() or 'never' in line:
            # Extract what should never be done
            # "NEVER push directly to main" →
            # Q: "When is it acceptable to push directly to main?"
            # A: "Never, with documented exceptions"

            # Simple heuristic: Look for verb after NEVER
            parts = line.lower().split('never')
            if len(parts) > 1:
                action = parts[1].strip(' :,.')
                return {
                    'question': f"When is it acceptable to {action}?",
                    'answer': extract_answer_from_assertion(assertion_text)
                }

    # Pattern 2: ONLY statements
    for line in lines:
        if 'ONLY' in line.upper():
            # "ONLY the user can merge PRs" →
            # Q: "Who is authorized to merge pull requests?"
            # A: "Only the user"

            parts = line.split('ONLY')
            if len(parts) > 1:
                subject_action = parts[1].strip(' :,.')
                # Extract action (can, must, etc.)
                if ' can ' in subject_action:
                    subject, action = subject_action.split(' can ', 1)
                    return {
                        'question': f"Who is authorized to {action.strip()}?",
                        'answer': f"Only {subject.strip()}"
                    }

    # Pattern 3: MUST/Required statements
    for line in lines:
        if 'MUST' in line.upper() or 'required' in line.lower():
            # Extract requirement
            # "All PRs MUST have approval" →
            # Q: "What is required for pull requests?"
            # A: "All PRs must have approval"

            if ' MUST ' in line:
                subject, requirement = line.split(' MUST ', 1)
                return {
                    'question': f"What is required for {subject.strip().lower()}?",
                    'answer': requirement.strip()
                }

    # No match
    return None

def extract_answer_from_assertion(assertion_text: str) -> str:
    """
    Extract answer text from assertion.

    Simple heuristic: Use first paragraph or first 2 sentences.
    """
    # Remove HTML comments
    text = assertion_text

    # Get first paragraph
    paragraphs = text.split('\n\n')
    first_para = paragraphs[0].strip()

    # Limit to ~200 chars
    if len(first_para) > 200:
        sentences = first_para.split('. ')
        return '. '.join(sentences[:2]) + '.'

    return first_para
```

**Note:** This is a starting point. Refine based on actual match rate.

### 2.3 Build Template 2: Constraint

**Template:** `scripts/templates/constraint.py`

**Strategy:** Extract setting/value pairs, generate "what is the [setting]?" questions

```python
def match_constraint(assertion_text: str) -> dict | None:
    """
    Match constraint-type assertions.

    Patterns:
    - "[Setting]: [value]"
    - "Default [setting] is [value]"
    - "Max/Min [thing]: [value]"

    Returns dict with question/answer or None if no match.
    """
    text = assertion_text.strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # Pattern 1: "Default X is Y" or "X (default)"
    for line in lines:
        if 'default' in line.lower():
            # "Default merge strategy is rebase" →
            # Q: "What is the default merge strategy?"
            # A: "Rebase and squash"

            if ' is ' in line.lower():
                parts = line.lower().split(' is ')
                subject = parts[0].replace('default', '').strip()
                value = parts[1].strip(' :,.')

                return {
                    'question': f"What is the default {subject}?",
                    'answer': value
                }

            # "Rebase (default)" format
            if '(default)' in line.lower():
                value = line.split('(')[0].strip()
                # Need to infer subject from context
                # This is harder - may need LLM fallback
                return None

    # Pattern 2: "Setting: Value" format
    for line in lines:
        if ':' in line and not line.startswith('#'):
            parts = line.split(':', 1)
            if len(parts) == 2:
                setting = parts[0].strip()
                value = parts[1].strip()

                # Avoid matching markdown syntax
                if not setting.startswith('[') and len(setting.split()) < 5:
                    return {
                        'question': f"What is the {setting.lower()}?",
                        'answer': value
                    }

    # Pattern 3: "Max/Min X: Y" format
    for line in lines:
        for keyword in ['max', 'min', 'maximum', 'minimum']:
            if keyword in line.lower() and ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    subject = parts[0].strip()
                    value = parts[1].strip()

                    return {
                        'question': f"What is the {subject.lower()}?",
                        'answer': value
                    }

    return None
```

### 2.4 Question Validation

**Validation Checks (from expert reviews):**

1. **Leakage Check:** Answer words shouldn't appear in question
   ```python
   def check_leakage(question: str, answer: str) -> float:
       """
       Calculate % of answer words that appear in question.

       Target: <10% leakage
       """
       q_words = set(question.lower().split())
       a_words = set(answer.lower().split())

       # Remove stopwords
       stopwords = {'the', 'a', 'an', 'is', 'are', 'to', 'of', 'for', 'in', 'on'}
       a_words_meaningful = a_words - stopwords

       if not a_words_meaningful:
           return 0.0

       overlap = q_words & a_words_meaningful
       leakage = len(overlap) / len(a_words_meaningful) * 100

       return leakage
   ```

2. **Answerability Check:** Answer text must exist in assertion
   ```python
   def check_answerable(assertion: str, answer: str) -> bool:
       """
       Verify answer can be extracted from assertion.

       Simple check: answer text (or close variation) in assertion
       """
       assertion_lower = assertion.lower()
       answer_lower = answer.lower()

       # Direct match
       if answer_lower in assertion_lower:
           return True

       # Word-level overlap (at least 50% of answer words present)
       answer_words = set(answer_lower.split())
       assertion_words = set(assertion_lower.split())

       overlap = len(answer_words & assertion_words)
       threshold = len(answer_words) * 0.5

       return overlap >= threshold
   ```

3. **Grammar Check:** Question ends with '?', answer is complete sentence
   ```python
   def check_grammar(question: str, answer: str) -> list[str]:
       """Basic grammar validation"""
       issues = []

       if not question.strip().endswith('?'):
           issues.append("Question doesn't end with ?")

       if not question[0].isupper():
           issues.append("Question doesn't start with capital")

       if len(answer.strip()) < 5:
           issues.append("Answer too short")

       return issues
   ```

### 2.5 LLM Fallback (40-50% Expected)

**When templates don't match, use LLM generation:**

```python
def generate_question_llm(assertion_text: str, assertion_type: str) -> dict:
    """
    Use LLM to generate question when templates fail.

    This will handle 40-50% of assertions.
    """
    prompt = f"""Generate a comprehension question for this {assertion_type} assertion:

{assertion_text}

Rules:
- Question should test if someone understood the assertion
- Answer must be extractable from the assertion text
- Do not include the answer in the question
- Aim for <10% word overlap between question and answer

Output JSON:
{{"question": "...", "answer": "...", "confidence": "high|medium|low"}}
"""

    # Call your preferred LLM
    response = call_llm(prompt)  # claude, gpt, gemini via CLI

    return parse_json_response(response)
```

**Budget:** ~$0.40 per document (50 assertions × 40% fallback × $0.02/call)

### 2.6 Week 2 Deliverables

**Must Complete:**
- [ ] Requirement template implemented
- [ ] Constraint template implemented
- [ ] Validation functions (leakage, answerability, grammar)
- [ ] LLM fallback function
- [ ] Template match rate measured on git_workflow.md

**Success Criteria:**
- ✅ Template match rate ≥50% (realistic target)
- ✅ Generated questions have <10% leakage
- ✅ All questions pass answerability check
- ✅ LLM fallback works for non-matching assertions

**Decision Point:**
- **If template match ≥50%** → Proceed to Week 3 (refine) ✅
- **If template match <50%** → Acceptable, increase LLM fallback budget
- **If templates completely fail (<20%)** → Pivot to pure LLM generation

### 2.7 Week 3: Refinement & Testing

**Activities:**

1. **Test on second document** (1 hour)
   - Candidate: `model_usage.md` (from Skills Migration task)
   - Add assertions to bulky version
   - Run question generation
   - Measure match rate

2. **Refine templates based on failures** (2 hours)
   - Analyze which assertions didn't match
   - Add pattern variants
   - Re-test on both docs

3. **Add optional 3rd template: Behavior** (2 hours, optional)
   - Pattern: "If X then Y", "When X, do Y"
   - Only if first 2 templates are successful

**Week 3 Success Criteria:**
- ✅ Tested on 2 documents
- ✅ Templates stable (match rate consistent)
- ✅ LLM fallback handles edge cases
- ✅ Ready to integrate

---

## Phase 3: Integration (Week 4)

**Goal:** Integrate question testing into polish.py as opt-in feature
**Precondition:** Phase 2 must find ≥1 real comprehension issue
**Time:** 2-3 hours

### 3.1 Pre-Integration Validation

**Before integrating, prove value:**

1. **Run question testing manually on 2-3 docs** (1 hour)
   ```bash
   python scripts/generate_questions.py common_rules/bulky/git_workflow.md > questions.json
   python scripts/test_comprehension.py questions.json --doc common_rules/clean/git_workflow.md
   ```

2. **Document issues found** (30 min)
   - Did questions reveal comprehension problems?
   - Did LLM fail any questions when reading clean doc?
   - Were failures legitimate (real doc issues)?

3. **Decision:**
   - **If ≥1 real issue found** → Proceed with integration ✅
   - **If 0 real issues found** → Keep as separate tool, don't integrate

### 3.2 Integration Approach

**Option A: Opt-in flag (Recommended)**

Add to polish.py:

```python
# config.py
enable_question_testing: bool = False  # Opt-in

# polish.py
if config.enable_question_testing:
    # 1. Generate questions from bulky doc assertions
    questions = generate_questions(bulky_doc_path)

    # 2. Test comprehension with clean doc
    results = test_comprehension(questions, clean_doc_path)

    # 3. Report findings separately
    report_question_results(results)
```

**Option B: Separate script (Alternative)**

Keep as standalone:

```bash
# Existing workflow
python scripts/polish.py docs/clean/git_workflow.md

# New step (manual)
python scripts/question_test.py docs/bulky/git_workflow.md --clean docs/clean/git_workflow.md
```

**Recommendation:** Start with Option B, move to Option A after 3-5 successful runs.

### 3.3 Week 4 Deliverables

**Must Complete:**
- [ ] Value demonstrated (≥1 issue found)
- [ ] Integration decision made (integrate vs keep separate)
- [ ] If integrating: Add opt-in flag to polish.py
- [ ] If separate: Document workflow in README

**Success Criteria:**
- ✅ End-to-end workflow functional
- ✅ Question testing adds value
- ✅ Process is sustainable (not too much overhead)

---

## Phase 4: Merge Script (Deferred)

**Status:** Deferred indefinitely, possibly not needed

**Why defer:**
- All models agree merge is complex and may not be needed
- For personal project, manual updates to bulky docs are fine
- Polishing results can be stored separately (JSON)

**Add back only if:** Real need emerges (e.g., handling 10+ docs, frequent polishing runs)

---

## Success Metrics

### Phase 1 Success

- ✅ git_workflow.md has bulky version with 5-8 assertions
- ✅ Strip script works (validated, idempotent)
- ✅ Clean doc generated (no leakage)
- ✅ Manual questions written (3 total)
- ✅ JetBrains snippet created
- ✅ Time: 4-6 hours total

### Phase 2 Success

- ✅ 2 templates working (Requirement + Constraint)
- ✅ Template match rate ≥50%
- ✅ LLM fallback handles remaining 40-50%
- ✅ Validation passing (<10% leakage, answerable)
- ✅ Tested on 2 documents

### Phase 3 Success

- ✅ Found ≥1 real comprehension issue
- ✅ Integration decision made
- ✅ End-to-end workflow documented
- ✅ Process is sustainable

### Project Success

- ✅ 3-5 critical docs polished and have bulky versions
- ✅ Question testing found ≥3 real issues across docs
- ✅ System is usable for new docs
- ✅ Authoring overhead is acceptable

---

## Risks & Mitigations

### Risk 1: Manual Questions Don't Find Issues

**Scenario:** Week 1 Exercise 3 - Manual questions don't reveal comprehension problems

**Response:**
1. Check: Are there real issues with git_workflow.md?
   - Ask: "Does the doc have ambiguities or confusing parts?"
   - If yes: Questions should catch them
   - If no: Try different doc (model_usage.md?)

2. Adjust question difficulty:
   - Make questions more specific
   - Test edge cases, not just happy path

3. If still no issues: Reconsider whether question testing adds value

### Risk 2: Template Match Rate Low (<50%)

**Scenario:** Week 2 - Templates only match 30-40% of assertions

**Response:**
1. **Accept it** - 40% is still useful, LLM handles rest
2. Budget: ~$0.60 per doc instead of $0.40 (60% LLM vs 40%)
3. Alternative: Pure LLM generation from start

**Not a blocker** - Expert reviews say 50-60% is realistic, 40% is acceptable

### Risk 3: Authoring Overhead Too High

**Scenario:** Adding assertions takes too long, discouraged from using format

**Response:**
1. Use JetBrains snippet (reduces 80% of typing)
2. Add fewer assertions (focus on critical ones only)
3. Consider shorthand: `**Rule:** Never push main <!-- @r:rule1 -->`

**Acceptable threshold:** <5 min per assertion with snippet

### Risk 4: Strip Script Breaks on Edge Cases

**Scenario:** Line-based parser fails on malformed metadata

**Response:**
1. Add more validation (reject malformed input)
2. Enforce strict rules (metadata must be well-formed)
3. If repeated issues: Switch to markdown AST parser (Codex's suggestion)

**Mitigation:** Strict format rules prevent most issues

---

## Decision Points

| Checkpoint | Metric | Threshold | Action if Fail |
|------------|--------|-----------|----------------|
| **End of Week 1, Exercise 3** | Manual questions find issues | ≥1 issue | Check if doc has real issues; try different doc |
| **End of Week 2** | Template match rate | ≥40% | Acceptable; increase LLM budget |
| **End of Week 2** | Leakage rate | ≤10% | Refine question generation |
| **End of Week 3** | Value demonstrated | ≥1 real issue found | Keep as separate tool; don't integrate |
| **End of Week 4** | Process sustainable | Can polish 1 doc in <1 hour | Simplify or accept manual steps |

---

## Tooling Summary

### JetBrains IDE

**Live Templates Created:**
- `assert` → Assertion block
- `docmeta` → Document metadata block

### GitHub Actions

**Workflow:** `.github/workflows/check-bulky-clean.yml`
- Verifies clean docs match stripped bulky docs
- Checks for metadata leakage
- **Status:** Optional, defer to post-Week 1

### Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/strip_metadata.py` | Strip bulky → clean | **Week 1** |
| `scripts/templates/requirement.py` | Requirement template | Week 2 |
| `scripts/templates/constraint.py` | Constraint template | Week 2 |
| `scripts/validate_questions.py` | Leakage/grammar checks | Week 2 |
| `scripts/generate_questions.py` | Full question generation | Week 3 |
| `scripts/test_comprehension.py` | Test questions with LLM | Week 3 |

---

## Next Actions

### Immediate (Week 1)

1. **Read git_workflow.md** - Understand current state
2. **Create bulky version** - Add @meta and 5-8 assertions
3. **Build strip script** - Implement section 1.2
4. **Test strip** - Verify clean output
5. **Write manual questions** - 3 questions from assertions
6. **Create JetBrains snippet** - Reduce authoring friction

### Week 2

7. Extract assertions from git_workflow.md
8. Analyze patterns
9. Build Requirement template
10. Build Constraint template
11. Add validation checks
12. Test template match rate

### Week 3

13. Test on second document (model_usage.md)
14. Refine templates
15. Add LLM fallback
16. Measure overall success rate

### Week 4

17. Run end-to-end on 2-3 docs
18. Document issues found
19. Decide: Integrate vs keep separate
20. Update README with workflow

---

## Appendix A: Real Documents for Polishing

**From Skills Migration task (todo.md lines 58-70):**

1. **git_workflow.md** (Phase 1 document)
   - Status: Current clean doc at `../common_rules/git_workflow.md`
   - Priority: Critical (robust git operations needed)
   - Assertions: 5-8 expected (rules, constraints, workflows)
   - Goal: Polish → Convert to Skills (feature-branch-workflow, pr-creation)

2. **model_usage.md** (Phase 2/3 document)
   - Status: Current clean doc at `../common_rules/model_usage.md`
   - Priority: High (model selection guide)
   - Assertions: 10-15 expected (constraints, requirements, guidelines)
   - Goal: Polish → Convert to model-selection-guide Skill

**Additional candidates:**
- `naming_conventions.md`
- `project_practices.md`
- `document_structure.md`

**Goal:** Polish 3-5 critical docs, convert suitable ones to Claude Skills

---

## Appendix B: Format Examples

### Example: git_workflow.md with assertions

```markdown
<!-- @meta
version: 1.0
created: 2025-12-02
last_polished: never
status: active
-->

# Git Workflow Rules

**Purpose:** Define standard Git workflow for all projects to maintain code quality and prevent accidental damage.

**Applies to:** All projects in the workspace

---

## Branch Protection

### Public Repositories

<!-- @assertion id="public_branch_protection" type="constraint" priority="high" -->
- **Branch protection enabled** via GitHub (strict mode)
- Requires pull request with 1 approval
- Prevents force pushes and branch deletion
- Enforced for all users including admins
<!-- @/assertion -->

---

## Standard Workflow

<!-- @assertion id="rule1_never_push_main" type="requirement" priority="critical" -->
### Rule 1: NEVER Push Directly to Main

**CRITICAL:** Always use feature branches and pull requests. This rule applies regardless of branch protection status.
<!-- @/assertion -->

**Always use feature branches:**

```bash
# Create feature branch
git checkout -b feature/add-flashcards
```

<!-- @assertion id="branch_naming_convention" type="constraint" priority="medium" -->
**Branch naming conventions:**
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions
<!-- @/assertion -->

<!-- @assertion id="merge_authorization" type="requirement" priority="critical" -->
**Merge authorization:**
- **ONLY the user can merge PRs** - Claude Code must NOT execute merge commands
- Claude can create PRs, review code, suggest changes, but merge requires explicit user action
- User executes: `gh pr merge --rebase --delete-branch` (or equivalent)
<!-- @/assertion -->

<!-- @assertion id="merge_strategy_default" type="constraint" priority="high" -->
**Merge strategies:**
- **Rebase and squash** (default) - Linear history, logically grouped commits
- **Squash merge** - Alternative: single commit per PR (use for small changes)
- **Rebase merge** - Rare: preserve individual commits (use for large, well-structured PRs)
- **Merge commit** - Avoid: creates non-linear history
<!-- @/assertion -->
```

**Stripped clean version would remove all `<!-- @... -->` blocks, keeping only the content.**

---

**Last Updated:** 2025-12-30
**Next Review:** After Week 1 completion
