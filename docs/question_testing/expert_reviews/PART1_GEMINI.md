# Expert Review: Question-Based Testing Framework (Gemini Response)

**Model:** Gemini 3 pro
**Date:** [date]
**Prompt:** EXPERT_REVIEW_PROMPT.md

---

This review evaluates the **Question-Based Testing Framework** from five expert perspectives, drawing on the design specifications in `QUESTION_BASED_TESTING_FRAMEWORK.md` and the implementation status in `PHASE_3_4_5_REVIEW_REPORT.md`.

---

## 1. Educational Assessment Specialist

*Expert in test design, reading comprehension evaluation, and item writing.*

### ✅ Strengths

* **Systematic Taxonomy**: The framework adopts a clear taxonomy of question types (Factual, Procedural, Conditional, etc.) and difficulty levels, which is standard practice in educational psychometrics to ensure balanced assessment.
* **Validation Rules**: The inclusion of explicit validation rules (e.g., Rule 2: No leakage, Rule 4: Single concept) mirrors professional "item review" processes used to ensure test reliability.

### ⚠️ Concerns

* **Item Cueing (Leakage)**: The primary failure in current implementation—questions like *"Does the documentation mention '30 seconds'?"*—is a classic "item cueing" error where the question contains the answer, testing search skills rather than comprehension.
* **Low Cognitive Depth**: Most templates currently target the "Knowledge" or "Recall" level of Bloom’s Taxonomy. They do not sufficiently challenge the "Application" or "Synthesis" levels required for technical documentation.

### 💡 Recommendations

1. **Prioritize Inferential & Conditional Questions**:
* **Why**: Factual questions are easily "cheated" by LLM pattern matching. Inferential questions force the model to construct a mental model.
* **Implementation**: Shift target distribution to 40% Conditional/Inference questions.
* **Priority**: High.


2. **Use Distractor-Based Validation**:
* **Why**: To avoid leakage, ensure the question uses synonyms or descriptions rather than quoting the exact "element_text" it's testing.
* **Implementation**: Update `Rule 2` to require that the question text has zero token overlap with the specific target value (e.g., the "30 seconds").
* **Priority**: High.



---

## 2. Technical Communication Researcher

*Expert in documentation usability, clarity metrics, and user comprehension.*

### ✅ Strengths

* **Action-Oriented Testing**: The focus on "whether models can correctly USE documentation" aligns with the "Documentation as a Tool" philosophy in tech comm, moving beyond passive readability scores.
* **Document-Level Conflict Detection**: Identifying contradictions across sections solves a major pain point in complex software manuals where isolated sections may be clear but the system as a whole is inconsistent.

### ⚠️ Concerns

* **Model-User Gap**: While LLM disagreement is a signal, it may not perfectly correlate with human user confusion. LLMs might struggle with formatting or tokens that humans find trivial.
* **Missing Task-Based Scenarios**: Documentation users usually have a goal (e.g., "Install the SDK"). The current templates are "micro-tests" and may miss the "macro-flow" experience.

### 💡 Recommendations

1. **Scenario-Based Question Generation**:
* **Why**: Real users follow workflows. Procedural questions should focus on the "Goal -> Action" relationship.
* **Implementation**: Create templates that ask: "Given [Goal], which [Section] provides the first step?" or "What is the prerequisite for [Command]?".
* **Priority**: Medium.


2. **Weighted Coverage by Element Type**:
* **Why**: Requirements ("must") and Constraints ("maximum") are higher risk than simple descriptions.
* **Implementation**: Increase "Requirement" element coverage to 100%, while keeping general "Factual" elements at 60%.
* **Priority**: Medium.



---

## 3. NLP/LLM Evaluation Researcher

*Expert in question-answering systems, benchmark design, and LLM testing.*

### ✅ Strengths

* **Multi-Model Consensus**: Using multiple models to identify ambiguity is a robust technique to filter out model-specific hallucinations versus documentation-rooted errors.
* **Integration of Modern Research**: The design incorporates Chain-of-Verification (CoVe) and Metamorphic Testing, which are current state-of-the-art methods for reducing hallucination.

### ⚠️ Concerns

* **Judge Bias (Self-Preference)**: Using an LLM-as-Judge can lead to "sycophancy bias" where the judge prefers answers that look like its own style.
* **Template Rigidity**: The current implementation review shows 0/6 questions passed validation. Rigid templates often fail to adapt to the varied linguistic structure of technical docs.

### 💡 Recommendations

1. **Implement LLM-Assisted Question Generation**:
* **Why**: Pure templates are too fragile. Using an LLM to *paraphrase* or *generate* the question from a template "seed" increases diversity and avoids leakage.
* **Implementation**: Adopt the "Hybrid Approach" recommended in the design doc.
* **Priority**: High.


2. **Add "Unanswerable" Probes**:
* **Why**: A key measure of documentation quality is whether it correctly omits irrelevant info. Asking questions that *cannot* be answered from the doc tests if the model knows its limits.
* **Priority**: Low.



---

## 4. Cognitive Psychologist

*Expert in text comprehension, mental models, and inference processes.*

### ✅ Strengths

* **Focus on Situation Models**: The "Document-Level" questions correctly target the "Situation Model"—the mental representation of the system—rather than just the "Textbase" (the words on the page).
* **Adversarial Probing**: Categories like "Assumption Injection" are excellent for testing whether a model has truly understood the underlying logic or is just performing statistical completion.

### ⚠️ Concerns

* **Surface-Level Mimicry**: LLMs are proficient at "Surface-Level" processing. If questions are too similar to the source text, the model can answer correctly without forming a functional mental model.
* **Inference vs. Recall**: The framework doesn't yet clearly distinguish between "explicit information" and "implicit information" required for deep understanding.

### 💡 Recommendations

1. **"What-If" Scenario Probing**:
* **Why**: To distinguish memorization from understanding, ask about the consequences of changing a variable mentioned in the doc.
* **Implementation**: Generate questions like: "If [Parameter X] is increased beyond [Limit Y], what error is triggered in [Section Z]?"
* **Priority**: Medium.


2. **Detect Misconceptions**:
* **Why**: Ambiguity often stems from text that allows for two plausible but contradictory mental models.
* **Implementation**: Use the "Contradiction Exploit" category specifically to find where two sections allow for different "mental paths".
* **Priority**: High.



---

## 5. Software Architect

*Expert in system design, API design, and maintainability.*

### ✅ Strengths

* **Modular Class Design**: The 5-class architecture (`CrossReferenceAnalyzer`, `ConflictDetector`, etc.) provides a clean separation of concerns and follows the Single Responsibility Principle.
* **Automatic Session Management**: Integrating session handling into `QuestioningStep` is a critical "usability" fix for the API, ensuring context is always preserved without manual overhead.

### ⚠️ Concerns

* **Zero Test Coverage**: The Phase 3-5 implementation has **zero unit tests**. This is a major risk for a system intended to find bugs in other documents.
* **Scaling and Cost**: Running multiple models for collection and another for evaluation across every section of a large documentation set will be computationally expensive and slow.

### 💡 Recommendations

1. **Implement Comprehensive Unit Tests**:
* **Why**: To ensure the `CrossReferenceAnalyzer` and `ConflictDetector` logic (which had KeyError bugs) is stable.
* **Implementation**: Add 25+ tests for Phase 3-4 classes immediately.
* **Priority**: High (CRITICAL BLOCKER).


2. **Caching and Parallelization**:
* **Why**: The "Judge" step and multi-model "Collection" are bottlenecks.
* **Implementation**: Cache question results and parallelize LLM calls across sections.
* **Priority**: Medium.



---

## Final Synthesis

### Overall Assessment

The approach is **fundamentally sound** and addresses a critical gap in documentation testing: functional comprehension. The transition from "open-ended interpretation" to "structured QA" provides measurable, actionable signals for documentation writers. However, the current implementation is **critically blocked** by a "Knowledge" level bias in its templates, leading to trivial questions that fail validation.

### Priority Recommendations

1. **Redesign Templates (Production)**: Move from "mention" patterns to "relationship" and "outcome" patterns to eliminate answer leakage.
2. **Add Phase 3-5 Unit Tests (Production)**: Stabilize the core logic of the 5 new classes before production use.
3. **Validate against Real Ambiguities (Research)**: Run the framework on a known "buggy" document to confirm that LLM disagreements actually point to human-readable issues.

### Alternative Approaches

* **Cloze Testing (Fill-in-the-blank)**: Instead of generating questions, hide key technical details (like port numbers or limits) and ask models to fill them in based on the rest of the text. This is easier to automate and harder to "leak" answers to.
* **Hybrid Human-in-the-Loop**: Use the automated generator to propose 50 questions, have a human select the 10 most "challenging" ones, and then automate the multi-model evaluation.
