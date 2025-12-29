# Expert Review Part 2: LLM-Optimized Documentation (Gemini Response)

**Model:** Gemini 3 pro
**Date:** [date]
**Prompt:** EXPERT_REVIEW_PROMPT_PART2.md

---

This integrated approach—**Test-Driven Documentation (TDD) for LLMs**—is a significant pivot that solves the "unstructured data" problem. By treating documentation as a formal specification rather than a prose narrative, you enable deterministic testing.

Below is the expert review of the integrated system.

---

## 🎓 Educational Assessment Specialist

### Question 1: Structure-Driven Assessment Design

To enable effective testing, documentation must move from *describing* to *asserting*.

* **Structural Elements**: Use **Assertion Blocks**. Instead of a paragraph, use a list of unique, testable claims.
* **Marking Testables**: Wrap critical constraints in `<claim id="req-1">...</claim>` tags.
* **Learning Objectives (LOs)**: Map every section to a "Capability": *e.g., "After reading this, a model should be able to [Authenticate] using [Method X]."*

### Question 2: Hybrid Question Generation Workflow

**Workflow: The "Distractor-First" Approach**

1. **Extract Assertion**: Pull `value: 30 seconds` from the YAML metadata.
2. **Generate Distractors**: Use an LLM to generate 3 *incorrect* but plausible values (e.g., 60s, infinite, 5s).
3. **Construct "Contextualized" Item**: Instead of asking "What is the timeout?", ask: *"A user reports a 'Gateway Timeout' after 45 seconds of waiting. Is this expected behavior according to the config?"*
4. **Verification**: A separate LLM (the Judge) ensures the answer cannot be found by simple string matching of the question text.

### Question 3: LLM-Specific Assessment Considerations

LLMs fail at **Inference Chains**. While a human understands that "Authentication is required" implies "Anonymous requests will fail," an LLM might not.

* **Instruction vs. Comprehension**: Test if the model can *reverse* the logic. "If I want to avoid a timeout, what is the maximum duration I can allow a request to run?"
* **Use vs. Answer**: The ultimate test is a **Performance Task**. Provide the model with a broken request and the docs; ask it to fix the request.

---

## 📝 Technical Communication Researcher

### Question 1: Documentation Format Design (The "Spec-Doc" Format)

LLMs thrive on **Semantic Proximity**. Proximity between a "trigger" (error code) and a "resolution" is more important than narrative flow.

**Concrete Example (Markdown + Embedded YAML):**

```markdown
## Authentication
:::requirement {id: "auth_01", type: "hard_constraint"}
All requests to `/api/*` require an `Authorization` header with a Bearer token.
:::

:::scenario {focus: "error_handling"}
- **Input**: Request missing header
- **Output**: 401 Unauthorized
- **Logic**: Header check occurs before routing
:::

```

### Question 2: Testability Patterns

**Anti-pattern**: "Use the standard configuration for security."
**Better (Testable)**:

```markdown
:::config {element: "security_protocol"}
Standard configuration DEFINED AS:
- TLS 1.3 only
- Header 'X-Content-Type-Options' set to 'nosniff'
:::

```

### Question 3: Documentation-Test Co-Design

Implement **Doc-Coverage-as-a-Service**.

* **Workflow**: For every `:::requirement` tag in the Markdown, the CI/CD pipeline *must* find a corresponding test case in the `questions.json` file. If a requirement is added without a testable scenario, the documentation build fails.

---

## 🔬 NLP/LLM Evaluation Researcher

### Question 1: Structure-to-Question Transformation

**Transformation Rules:**

* **IF** `type: procedure` AND `step.prerequisites` EXISTS
* **THEN** generate **Counterfactual Question**: "If [Step N-1] is skipped, why will [Step N] fail?"
* **USING LLM to**: Synthesize a realistic error message based on the step description.

### Question 2: Hybrid Generation Pipeline

1. **Skeleton Parser**: Extract YAML metadata (assertions, constraints, prerequisites).
2. **LLM Prompting**: "Given these 3 constraints [A, B, C], describe a scenario where a user violates B but follows A and C. Formulate it as a 'What happens if...' question."
3. **Diversity Check**: Use an embedding similarity check to ensure the new question isn't 90% similar to existing questions.

### Question 3: LLM-Specific Question Types

* **Constraint Satisfaction**: "We have 100 users and a 30s timeout. If each user takes 5s, will the system bottle-neck?"
* **Cross-Reference Resolution**: "Section 2 mentions a 'Token'. Section 5 mentions a 'Secret'. Are these the same object?"

---

## 🧠 Cognitive Psychologist

### Question 1: LLM Mental Models

LLMs build "Probabilistic Textbases," not true situational mental models. They lack **Functional Persistence**—they might "know" a rule in step 1 but "forget" it when reasoning about step 10.

* **Testing Strategy**: Use **State-Change Probing**. Ask: "After step 2, what is the state of the database? After step 3?" If the model can't track state, its comprehension is surface-level.

### Question 2: Structure and Comprehension

Headings are high-signal for LLMs. **Hierarchical Anchoring** helps.

* **Recommendation**: Every technical limit should be a child of the specific component it affects. LLMs struggle with "Global Notes" buried at the end of a document.

### Question 3: Testing Transfer and Application

To distinguish memorization from understanding, use **Analogy Testing**.

* **Pattern**: "This documentation describes an Installation for *Linux*. Apply these principles to describe how you would conceptually handle a *Unix* installation where the `apt` command is replaced by `pkg`."

---

## 🏗️ Software Architect

### Question 1: Documentation Format Specification

Use **Extended Markdown (MDX/Custom Containers)**. It preserves human readability in Git while being strictly parsable.

```yaml
# schema/doc_element.yaml
type: object
properties:
  id: {type: string}
  category: {enum: [requirement, constraint, procedure, state]}
  content: {type: string}
  validation:
    question_type: {type: string}
    expected_value: {type: string}

```

### Question 2: Question Generation Service Architecture

1. **Watcher**: Triggers on `.md` change.
2. **Doc-Parser**: Converts Markdown containers to JSON objects.
3. **Gen-Engine**: Sends JSON + Few-Shot Prompt to LLM.
4. **Validator**: Runs the generated question against a "Baseline Model." If the baseline gets it wrong, the question is flagged for human review.

### Question 3: Documentation-Test Integration

**The "Doc-Lint" Workflow:**

* **Pre-commit**: Developer writes documentation.
* **Lint Step**: Script checks if all `:::requirement` blocks have `test_hints`.
* **CI Step**: Automated generation creates questions; "Judge LLM" verifies they are answerable and leakage-free.
* **Merge**: Only possible if "Documentation Test Coverage" > 80%.

---

## Final Synthesis

### 1. Integration Assessment

* **Fundamental Logic**: Linking format to generation is the only way to achieve 0% leakage. If the structure is `key: value`, the question can be generated as `What is the [key]?` while the LLM masks the `[value]` using synonyms.
* **Biggest Risk**: **Maintenance Burden**. Writers may resist "coding" their documentation in YAML/Structured Markdown.

### 2. Practical Recommendation (The MVP)

1. **Build First**: A **Markdown Linter** that enforces a specific "Testable" block format (e.g., `:::assertion`).
2. **The MVP**: A script that takes these `:::assertion` blocks and uses a single LLM call to generate one "Scenario" question per block.
3. **Defer**: Cross-document conflict detection. Start with intra-page consistency.

### 3. Success Criteria

* **Metric 1: Model Disagreement Rate**. Does a higher disagreement rate on these structured questions correlate with human-reported bugs in the docs?
* **Metric 2: Leakage Score**. Automated check: `WordOverlap(Question, Answer) < 10%`.
* **Done**: When 100% of "Hard Requirements" in the documentation have at least one validated comprehension question associated with them.
