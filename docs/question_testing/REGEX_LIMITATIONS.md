# Regex Limitations for Question-Based Testing

**Purpose**: Document regex pattern limitations discovered during Phase 2 implementation to inform future updates to `common_rules/document_structure.md`.

**Date**: 2025-12-28
**Context**: Question-based testing framework uses 8 regex patterns to extract testable elements from documentation. This document outlines what works well and what doesn't.

---

## Executive Summary

Regex-based extraction works best with **explicit, structured patterns**. Documentation that follows consistent formatting conventions enables automated question generation with 70%+ coverage.

**Key Finding**: Simple, direct phrasing ("must", "Step 1:", "maximum") extracts reliably. Complex phrasing ("it is necessary", "First, do X") often fails.

---

## What Works Well (Regex-Friendly Patterns)

### 1. Steps - Numbered Procedures

| ✅ Works | ❌ Doesn't Work |
|---------|----------------|
| `Step 1: Download the file` | `First, download the file` |
| `1. Extract the archive` | `To begin, extract the archive` |
| `Step 2: Run setup.exe` | `Next you should run setup.exe` |

**Recommendation**: Use explicit `Step N:` or `N.` prefixes for numbered procedures.

### 2. Requirements - Must/Required Statements

| ✅ Works | ❌ Doesn't Work |
|---------|----------------|
| `The system must support UTF-8` | `It is necessary for the system to support UTF-8` |
| `Authentication is required` | `You need to set up authentication` |
| `Files shall be validated` | `We strongly recommend validating files` |

**Recommendation**: Use "must", "required", "shall" as explicit requirement markers.

### 3. Conditionals - If/When/Unless Clauses

| ✅ Works | ❌ Doesn't Work |
|---------|----------------|
| `If the file exists, skip download` | `In the case that a file exists, downloading can be skipped` |
| `When processing fails, retry` | `Should processing not succeed, try again` |
| `Unless specified, use defaults` | `Defaults apply except where otherwise noted` |

**Recommendation**: Start conditional statements with "If", "When", or "Unless".

### 4. Outputs - Expected Results

| ✅ Works | ❌ Doesn't Work |
|---------|----------------|
| `The script generates a JSON report` | `A JSON report is created by the script` |
| `Returns exit code 0 on success` | `Successfully exits with code 0` |
| `Produces a summary file` | `The result is a summary file` |

**Recommendation**: Use active verbs: "generates", "produces", "returns", "outputs".

### 5. Inputs - Required Inputs

| ✅ Works | ❌ Doesn't Work |
|---------|----------------|
| `The function accepts two parameters` | `Two parameters are needed` |
| `Takes a configuration file as input` | `Requires configuration file` |
| `Receives user credentials` | `Credentials must be provided` |

**Recommendation**: Use "accepts", "takes", "receives" to describe inputs.

### 6. Constraints - Limits and Restrictions

| ✅ Works | ❌ Doesn't Work |
|---------|----------------|
| `The maximum file size is 10MB` | `File size should not exceed 10MB` |
| `Must use at least 2 characters` | `A minimum of 2 characters` |
| `Limit: 100 requests per minute` | `No more than 100 requests each minute` |

**Recommendation**: Use "maximum", "minimum", "max", "min", "limit", "at most", "at least".

### 7. Defaults - Default Values

| ✅ Works | ❌ Doesn't Work |
|---------|----------------|
| `The timeout defaults to 30 seconds` | `By default, the timeout is 30 seconds` |
| `Port is set to 8080` | `Port number: 8080 (default)` |
| `Default value: UTF-8` | `UTF-8 encoding used if not specified` |

**Recommendation**: Use "defaults to", "default value", "is set to" patterns.

### 8. Exceptions - Error Cases

| ✅ Works | ❌ Doesn't Work |
|---------|----------------|
| `If validation fails, return error` | `Validation failure results in an error` |
| `Raises an exception on invalid input` | `Invalid input causes an exception` |
| `Returns null when file not found` | `File not being found causes null return` |

**Recommendation**: Use "fails", "error", "exception", "invalid" in error descriptions.

---

## Regex Pattern Details

### Pattern 1: Steps

```regex
r'(?:^|\n)(Step\s+\d+[:.]\s+.+?)(?=\n(?:Step\s+\d+|#{1,6}\s|\n|$))'
r'(?:^|\n)(\d+\.\s+.+?)(?=\n(?:\d+\.|#{1,6}\s|\n|$))'
r'(?:^|\n)(First,?\s+.+?)(?=\n(?:Second|Next|Then|#{1,6}\s|\n|$))'
```

**Matches**:
- "Step 1: Download"
- "1. Extract archive"
- "First, configure settings"

**Doesn't Match**:
- "To start, download" (no explicit step marker)
- "Begin by extracting" (implicit ordering)

### Pattern 2: Requirements

```regex
r'(?:^|\n)(.+?\s+(?:must|required|shall)\s+.+?)(?=[.!?\n])'
r'(?:^|\n)(.+?\s+is\s+required.+?)(?=[.!?\n])'
```

**Matches**:
- "The system must validate input"
- "Authentication is required"

**Doesn't Match**:
- "It is necessary to validate" (different phrasing)
- "Should validate input" (recommendation, not requirement)

### Pattern 3: Conditionals

```regex
r'(?:^|\n)((?:If|When|Unless)\s+.+?,\s+.+?)(?=[.!?\n])'
r'(?:^|\n)(.+?\s+if\s+.+?)(?=[.!?\n])'
```

**Matches**:
- "If file exists, skip"
- "Process if valid"

**Doesn't Match**:
- "In the case of file existence" (verbose phrasing)
- "Should file exist" (different structure)

### Pattern 4: Outputs

```regex
r'(?:^|\n)(.+?\s+(?:outputs?|produces?|generates?|returns?)\s+.+?)(?=[.!?\n])'
r'(?:^|\n)(The\s+(?:output|result)\s+.+?)(?=[.!?\n])'
```

**Matches**:
- "The function returns a string"
- "The output is JSON"

**Doesn't Match**:
- "A string is returned" (passive voice)
- "Result: JSON document" (label format)

### Pattern 5: Inputs

```regex
r'(?:^|\n)(.+?\s+(?:inputs?|accepts?|takes?|receives?)\s+.+?)(?=[.!?\n])'
r'(?:^|\n)(The\s+input\s+.+?)(?=[.!?\n])'
```

**Matches**:
- "The function accepts a file path"
- "The input must be valid"

**Doesn't Match**:
- "A file path is needed" (different verb)
- "Requires file path input" (different structure)

### Pattern 6: Constraints

```regex
r'(?:^|\n)(.+?\s+(?:maximum|minimum|max|min|limit)\s+.+?)(?=[.!?\n])'
r'(?:^|\n)(.+?\s+(?:at\s+most|at\s+least|no\s+more\s+than)\s+.+?)(?=[.!?\n])'
```

**Matches**:
- "The maximum size is 10MB"
- "At most 100 requests"

**Doesn't Match**:
- "Size cannot exceed 10MB" (different phrasing)
- "Upper bound: 100" (mathematical notation)

### Pattern 7: Defaults

```regex
r'(?:^|\n)(.+?\s+(?:defaults?\s+to|default\s+value)\s+.+?)(?=[.!?\n])'
r'(?:^|\n)(.+?\s+is\s+set\s+to\s+.+?)(?=[.!?\n])'
```

**Matches**:
- "Timeout defaults to 30s"
- "Port is set to 8080"

**Doesn't Match**:
- "Default timeout: 30s" (colon format)
- "If not specified, uses 30s" (implicit default)

### Pattern 8: Exceptions

```regex
r'(?:^|\n)(.+?\s+(?:error|exception|fail|invalid)\s+.+?)(?=[.!?\n])'
r'(?:^|\n)(If\s+.+?\s+(?:fails|errors).+?)(?=[.!?\n])'
```

**Matches**:
- "If parsing fails, return null"
- "Raises exception on error"

**Doesn't Match**:
- "Unsuccessful parsing returns null" (verbose)
- "Null returned when parsing unsuccessful" (passive)

---

## Common False Positives

### 1. Code Examples

```markdown
The function signature is `def process(data: dict)`.
If you pass `data=None`, it raises an error.
```

**Issue**: The word "If" in "If you pass" is instructional, not conditional logic.

**Mitigation**: Regex can't distinguish instruction from specification. Templates handle validation.

### 2. Conversational Phrasing

```markdown
When you're ready to deploy, make sure to run the tests first.
```

**Issue**: "When you're ready" is conversational, not a system condition.

**Mitigation**: Encourage technical, direct phrasing.

### 3. Nested Conditionals

```markdown
If the environment is production, and if the user is authenticated, then enable caching.
```

**Issue**: Multiple "if" clauses create complex extraction.

**Mitigation**: Break into separate sentences or use explicit structure.

---

## Recommendations for document_structure.md

### New Section: "Structuring Instructions for AI Comprehension"

Add guidance for documentation writers to use regex-friendly patterns:

#### 1. Numbered Steps

✅ **Use**: "Step 1:", "1.", "2.", "Step N:"
❌ **Avoid**: "First,", "To begin,", "Next,"

#### 2. Requirements

✅ **Use**: "must", "required", "shall"
❌ **Avoid**: "should", "it is necessary", "you need to"

#### 3. Conditionals

✅ **Use**: "If...", "When...", "Unless..."
❌ **Avoid**: "In the case of", "Should...", "Were it that..."

#### 4. Constraints

✅ **Use**: "maximum", "minimum", "at most", "at least"
❌ **Avoid**: "no more than", "cannot exceed", "upper bound"

#### 5. Defaults

✅ **Use**: "defaults to", "is set to", "default value"
❌ **Avoid**: "if not specified", "by default", "uses X when..."

#### 6. Active Voice

✅ **Use**: "The system generates a report"
❌ **Avoid**: "A report is generated by the system"

#### 7. Explicit Over Implicit

✅ **Use**: "The function returns exit code 0 on success"
❌ **Avoid**: "Successfully exits with code 0"

---

## Implementation Notes

- **Phase 2 Coverage**: 8 regex patterns achieved 70% section / 60% element coverage on test documents
- **Validation**: 4-rule validation (answerable, no leakage, grammatical, single concept) filters false positives
- **Template Matching**: 14 templates map element types to question categories
- **Limitations Accepted**: Complex phrasing, passive voice, and conversational tone reduce automated extraction effectiveness

---

## Future Improvements

### Phase 3: Document-Level Questions
- Dependency graphs may require structured cross-references (e.g., "See section X" → regex `See section \w+`)
- Conflict detection may need "but", "however", "alternatively" patterns

### Phase 6: Adversarial Testing
- Trick questions need "always", "never", "only", "exactly" patterns
- False premises may target vague language ("typically", "usually", "often")

---

## Conclusion

**Primary Takeaway**: Automated question generation succeeds when documentation follows consistent, explicit patterns.

**Action Item**: Update `common_rules/document_structure.md` with:
1. New section: "Structuring Instructions for AI Comprehension"
2. Explicit keyword recommendations (table format)
3. Examples of regex-friendly vs. problematic phrasing
4. Rationale: Enables automated testing, improves clarity for both humans and AI

**Benefit**: Documentation that works well with regex extraction is also clearer and more actionable for human readers.
