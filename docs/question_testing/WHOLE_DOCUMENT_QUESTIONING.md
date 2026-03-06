# Whole-Document Questioning

**Status:** Design
**Created:** 2026-03-05
**Source:** FRAMEWORK.md (design principles, question types, evaluation model, success metrics)
**Supersedes:** Template-based questioning (abandoned), per-section manual questions (shelved)

---

## 1. Context

### What Was Tried

Two prior approaches to question-based comprehension testing were attempted:

**Template-based questions** extracted elements from individual sections using regex, then applied question templates. The approach had a fundamental flaw: the answer was derived from the same text inserted into the question, causing 100% answer leakage. Beyond that bug, the abstraction was wrong — regex element extraction is too rigid for the variety of instructional text.

**Manual per-section questions** were hand-crafted scenario questions tested against a real document. Results validated the concept decisively:

| Scenario | Accuracy | What It Proves |
|----------|----------|----------------|
| Cold (no document) | 13% | Models invent exceptions from "common practice" |
| Old document (flawed) | 13% | Document errors propagate faithfully to model answers |
| Current document (corrected) | 88% | Clear documentation produces correct comprehension |

The questions worked. The problem was **maintenance overhead** — writing, aligning, and tracking questions per section per document doesn't scale.

### Why Whole-Document

| Per-Section Problem | Whole-Document Solution |
|---------------------|------------------------|
| Must track which questions map to which sections | Questions reference the document as a whole |
| Section changes invalidate mapped questions | Questions test document-level comprehension, resilient to restructuring |
| N sections x M questions = combinatorial tracking | One question set per document, flat file |
| Question scope too narrow to test cross-section understanding | Questions naturally span multiple sections |

The key insight from the manual experiment: the best questions were **scenario-based** — they presented realistic situations that required understanding multiple rules simultaneously. These are inherently whole-document questions.

---

## 2. Design Principles

### P1: Questions test comprehension, not mention

Bad: "Does the document mention merge authorization?"
Good: "I have full CI approval on a security fix. Should I execute the merge?"

The model must *apply* its understanding, not just locate text.

### P2: Questions create realistic pressure

The most revealing questions are ones where models are tempted to invent exceptions. Patterns that trigger this:
- Urgency ("production is down")
- Social proof ("two senior engineers approved")
- Triviality ("just a typo fix")
- Common practice ("most teams allow this")

### P3: Expected answers are key points, not exact text

A correct answer must hit specific key points. Evaluation checks for conceptual coverage, not string matching.

### P4: One question set per document

All questions for a document live in a single YAML file. No cross-file dependencies, no section-mapping bookkeeping.

### P5: Questions are human-authored

Automated question generation was the template approach. It failed. Questions require human judgment about what comprehension gaps matter. Authoring cost is acceptable because:
- One question set per document (not per section)
- 4-8 questions per document is sufficient
- Questions change rarely (tied to document purpose, not wording)

---

## 3. Question Schema

### Question

```yaml
id: "q_merge_auth"             # Unique within question set
question: |                    # Scenario-based, multi-sentence
  I've created a PR that fixes a critical security vulnerability.
  All CI checks passed and two senior engineers approved.
  Should I execute the merge command?
category: "authorization"      # Free-form tag for grouping
difficulty: "standard"         # basic | standard | advanced
assertions:                    # Optional link to @assertion IDs in bulky doc
  - "rule3_merge_authorization"
  - "rule7_agent_permissions"
expected:
  key_points:                  # What a correct answer MUST include
    - "Only the user can execute merge commands"
    - "Agent must NOT run gh pr merge"
    - "Approval does not grant agent merge authority"
  anti_points:                 # What a correct answer must NOT include
    - "Yes, proceed with the merge"
    - "Execute the merge command"
  notes: |                     # Rationale for question design
    Tests whether urgency + approval overrides agent boundaries.
    LLMs commonly conflate "PR is ready" with "I can merge it".
```

### Question Set

```yaml
version: "1.0"
document: "git_workflow.md"               # Identifier (metadata, not a file path)
bulky_source: "git_workflow_bulky.md"    # Optional, if bulky-clean is used
created: "2026-03-05"
author: "nik"
description: |
  Comprehension tests for [document purpose].
  Focus: [what the questions target].

questions:
  - id: "q_example_1"
    question: |
      ...
    # (full schema as above)

  - id: "q_example_2"
    question: |
      ...

metadata:
  question_count: 4
  categories: ["category1", "category2"]
  coverage_notes: |
    What the questions cover and what they don't.
```

---

## 4. File Organization

The polishing tool does not prescribe where question sets live. The user provides the path via CLI flag:

```
--questions path/to/questions.yaml
```

The YAML file's `document` field is a metadata identifier — it records which document the questions target but is not used as a file path. The actual document is always provided separately (via `--document` flag in standalone mode, or from pipeline context in `polish.py`). No naming conventions are enforced — the user controls file names and locations.

---

## 5. Workflow

### Authoring

```
                    +----------------------+
                    |  Read the document   |
                    |  (what models see)   |
                    +----------+-----------+
                               |
                    +----------v-----------+
                    |  Identify key rules  |
                    |  and edge cases      |
                    +----------+-----------+
                               |
                    +----------v-----------+
                    |  Write 4-8 scenario  |
                    |  questions with      |
                    |  expected key_points  |
                    +----------+-----------+
                               |
                    +----------v-----------+
                    |  (Optional) Link to  |
                    |  @assertion IDs      |
                    +----------+-----------+
                               |
                    +----------v-----------+
                    |  Save as YAML file   |
                    +----------------------+
```

### Authoring Heuristics

When writing questions, target these comprehension failure modes (proven by experiment):

| Failure Mode | Pattern | Example |
|--------------|---------|---------|
| **Exception invention** | Model adds exceptions the doc doesn't have | "Trivial fixes can skip review" |
| **Authority conflation** | Model confuses readiness with permission | "Approved PR = I can merge" |
| **Urgency override** | Model bypasses rules under time pressure | "Production down = skip process" |
| **Default override** | Model picks non-default option when default applies | "47 commits = preserve history" |
| **Common practice substitution** | Model follows industry norms instead of stated rules | "Most teams allow direct main commits for hotfixes" |

### Question Types

Questions can test different aspects of comprehension (from FRAMEWORK.md):

| Type | Purpose | Typical Difficulty |
|------|---------|-------------------|
| **Factual** | Verify understanding of specific stated rules | basic |
| **Procedural** | Test knowledge of correct step sequences | standard |
| **Conditional** | Test edge case and exception handling | standard |
| **Cross-reference** | Test connections between different parts of the document | advanced |
| **Conflict detection** | Expose contradictions between sections | advanced |
| **Inference** | Test conclusions that require combining multiple rules | advanced |

---

## 6. Testing

### Integration with polish.py

Question testing is Step 5, skippable. When no `--questions` flag is provided, Step 5 logs "skipped" and the pipeline proceeds to Step 6 (reporting).

```
Step 1: Extract sections
Step 2: Init sessions
Step 3: Test sections (interpretation)
Step 4: Detect ambiguities
Step 5: Question testing (skipped if no --questions flag)
    5a. Load question set
    5b. Init fresh sessions with document context
    5c. Query models with questions
    5d. Save model responses
    5e. Evaluate answers with LLM-as-Judge
Step 6: Generate report (includes question results when available)
```

### Sessions

Step 5 creates its own fresh sessions with the document context. This ensures comprehension testing is not influenced by prior interpretation queries from Step 3.

**Why not reuse Step 2 sessions:**
- Step 3 queries prime models with specific section-level questions, which may influence answers
- If a session errored or timed out in Step 3, it may be in a bad state
- Comprehension testing should measure fresh understanding, not recall from prior prompts

A `--reuse-sessions` flag can be added later if session initialization cost becomes a concern.

### Model Response Storage

Model responses are saved separately, following the same pattern as Step 3:

```
workspace/polish_TIMESTAMP/
  test_results.json           # Step 3: interpretation responses
  ambiguities.json            # Step 4: detected ambiguities
  question_responses.json     # Step 5: question answers (raw)
  question_evaluations.json   # Step 5: judge verdicts
  report.md                   # Step 6: final report
```

`question_responses.json` contains the raw model answers per question per model. `question_evaluations.json` contains the LLM-as-Judge verdicts, reasoning, and evidence. This separation allows re-evaluation with a different judge without re-querying models.

---

## 7. Evaluation Model

### Answer Verdict

Each model answer receives one of four verdicts:

| Verdict | Meaning | Criteria |
|---------|---------|----------|
| **correct** | Fully comprehends the rule | All key_points matched, no anti_points present |
| **partial** | Understands some but not all | 50-99% key_points matched, no anti_points |
| **incorrect** | Fails to comprehend | <50% key_points OR any anti_point present |
| **evasive** | Refuses to answer or gives generic advice | No key_points matched, no anti_points, response is vague |

### Key Point Matching

Key point matching is **semantic, not lexical**. The evaluator (LLM-as-Judge) determines whether the answer conceptually covers each key point, not whether specific words appear.

The judge receives the question, key_points, anti_points, and the model's raw answer. For each key point it determines coverage (yes/no with reasoning). For each anti-point it checks presence (yes/no). Then it assigns an overall verdict.

### Consensus Across Models

When multiple models answer the same question:

| Pattern | Interpretation | Action |
|---------|---------------|--------|
| All correct | Document is clear on this topic | None needed |
| All incorrect (same way) | Document likely has a gap or misleading phrasing | Flag for document improvement |
| Mixed (some correct, some not) | Ambiguity exists — some models parse it correctly, others don't | Flag as ambiguity |
| All evasive | Question may be poorly formed, or models lack domain context | Review question design |

### Scoring

Per-question score:
```
score = matched_key_points / total_key_points
penalty = 1.0 if any anti_point present, else 0.0
final = max(0, score - penalty)
```

Per-document score:
```
document_score = mean(question_scores)
```

### Issue-to-Ambiguity Mapping

When question testing detects issues, they are converted to ambiguity objects compatible with the existing pipeline. This allows the report to present a unified view of all detected issues regardless of detection method.

| Question Issue Type | Mapped Severity |
|---------------------|-----------------|
| Conflict not detected | CRITICAL |
| False premise accepted | HIGH |
| Incorrect answer | HIGH |
| Partially correct | MEDIUM |
| Adversarial failure | MEDIUM |

---

## 8. Report Extension

When question testing runs, the report gains a comprehension testing section:

```
## Comprehension Testing

Questions tested: N
Models: [model list]

| Question | Model A | Model B | Model C |
|----------|---------|---------|---------|
| [id]     | verdict | verdict | verdict |
| ...      | ...     | ...     | ...     |

Score: X/Y (Z%)

### Issues Detected

#### [Question ID]: [short description]
**Question:** [scenario text]
**Expected:** [key points summary]
**[Model] answered:** [problematic answer summary]
**Issue:** [what went wrong and suggested improvement]
```

The format is generic — it works for any document, any question set, any model combination.

---

## 9. CLI

### Standalone (test_questions.py)

Like other pipeline steps, questioning has its own standalone script. Both `--questions` and `--document` are required:

```
# Run question testing independently:
test_questions.py --questions path/to/questions.yaml --document path/to/doc.md

# Specify models and judge:
test_questions.py --questions path/to/questions.yaml --document path/to/doc.md \
  --models claude,gemini --judge claude

# Output to specific directory:
test_questions.py --questions path/to/questions.yaml --document path/to/doc.md \
  -o workspace/
```

The YAML's `document` field is metadata identifying which document the questions target. It is not used as a file path — the document is always provided via CLI flag or pipeline context.

### Integrated (polish.py)

```
# Run full pipeline with question testing:
polish.py document.md --questions path/to/questions.yaml

# Without --questions, Step 5 is skipped:
polish.py document.md
```

When integrated, `polish.py` passes the already-loaded document content to Step 5. No path resolution from the YAML is needed.

---

## 10. Success Metrics

From FRAMEWORK.md, adapted for whole-document questioning:

| Metric | What It Measures | Target |
|--------|-----------------|--------|
| Issue detection rate | Issues found by questioning that interpretation missed | >= 30% unique |
| False positive rate | Incorrectly flagged issues / total flagged | <= 15% |
| Answer agreement | Questions where all models answer correctly | >= 80% |
| Judge consistency | Same judge result on retry | >= 90% |

The primary signal is the **answer agreement rate** — if all models answer a question correctly, the document is clear on that topic. Questions where models disagree or fail indicate document improvement opportunities.

---

## 11. Open Questions

1. **Threshold for "document needs improvement"?** The manual experiment showed 88% on a corrected document. What score triggers a flag? Likely configurable per use case. See FRAMEWORK.md Section 8 for detailed success criteria discussion.

2. **Question set versioning?** When the document changes significantly, should the question set be re-validated? A simple `document_hash` field in the YAML could track staleness.

3. **LLM-assisted question authoring?** The human writes the scenario and key_points, but an LLM could suggest additional questions based on the document's @assertion markers. This avoids the template trap while reducing authoring effort. Out of scope for initial implementation.
