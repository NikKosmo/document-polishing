# Expert Design Task: Question-Based Testing for LLM Documentation Evaluation

**Your Role:** You are a leading expert in LLM evaluation methodologies, documentation quality assurance, and adversarial testing. You have deep knowledge of industry standards including Constitutional AI, Chain-of-Verification, Metamorphic Testing, Red Teaming, and LLM testing frameworks (Giskard, DeepEval, etc.).

**Your Task:** Design a comprehensive question-based testing framework for an LLM documentation polishing system.

---

## Problem Statement

Current LLM-based documentation testing systems evaluate **interpretation** ("How does the model understand this section?") but don't evaluate **comprehension through questioning** ("Can the model correctly answer questions about the document?").

**Gap identified:**
- Interpretation testing catches disagreements between models on what text means
- **Missing:** Testing whether models can correctly USE the documentation to answer questions
- **Missing:** Testing whether document parts conflict when considered holistically
- **Missing:** Adversarial probing to find edge cases and robustness issues

**Your objective:** Design a question-based testing approach that operates at TWO levels:

### Level 1: Section-Level Questions
Test specific comprehension of individual sections.
- **Purpose:** Verify models understand each part correctly
- **Scope:** Questions reference specific section content
- **Example:** For "Step 2: Sanitize Data" → "What should happen to PII if priority_level is High-Security?"

### Level 2: Document-Level Questions
Test holistic understanding and cross-section consistency.
- **Purpose:** Detect internal conflicts, verify overall workflow understanding
- **Scope:** Questions span multiple sections or entire document
- **Example:** For a 5-step workflow → "If Step 3 fails, can Step 4 still execute?" (tests cross-step dependencies)
- **Critical value:** When asking models to act on workflow or implement tasks, we need to verify their overall understanding WITHOUT specifying which exact part of the document to reference. This reveals if conflicting parts exist.

**Why document-level matters:**
- Models implementing a workflow need holistic understanding
- Internal contradictions may not be visible when analyzing sections in isolation
- Cross-reference ambiguities only appear when considering full document context

---

## Current System Architecture

**Pipeline (5 modular steps):**
1. **Extraction** (`extraction_step.py`): Parse markdown → extract testable sections
2. **Session Init** (`session_init_step.py`): Initialize model sessions with full document context
3. **Testing** (`testing_step.py`): Query models for section interpretations
4. **Detection** (`detection_step.py`): LLM-as-Judge compares interpretations, detects ambiguities
5. **Reporting** (`reporting_step.py`): Generate report + polished document

**Current testing methodology:**
- **Input:** Section content + document context (via session)
- **Output:** Model provides {interpretation, steps, assumptions, ambiguities}
- **Detection:** Claude (judge) compares interpretations for semantic disagreement
- **Result:** Ambiguity objects with severity levels (critical/high/medium/low)

**Modular design principles:**
- Each step is independent module with Result dataclass
- All results have save/load methods (JSON artifacts)
- CLI scripts wrap modules for standalone execution
- Single source of truth (no duplication)

---

## Your Design Task

Create comprehensive documentation for a **question-based testing framework** that complements the existing interpretation-based approach.

### Research & Design Areas

#### 1. Question-Based Testing Methodology

**Research industry standards:**
- How do **Giskard** and **DeepEval** frameworks test LLM comprehension?
- What question types are standard in LLM evaluation literature?
- How does **Chain-of-Verification (CoVe)** approach self-checking?
- What are best practices from QA systems and reading comprehension benchmarks?

**Design requirements:**
- **Question generation:** Automated strategy to create questions from documentation
  - Section-level: Questions about specific parts
  - Document-level: Questions about overall workflow, cross-references, conflicts
- **Question types:** Categorization and purpose of each type
  - Factual (verify specific facts are understood)
  - Procedural (verify step sequences are understood)
  - Conditional (verify if/then logic is understood)
  - Cross-reference (verify relationships between sections)
  - Conflict detection (reveal internal contradictions)
- **Answer evaluation:** How to determine correctness
  - Reference answers vs model answers
  - LLM-as-Judge comparison
  - Semantic similarity scoring
  - Structured answer validation
- **Coverage metrics:** Ensure comprehensive testing
  - What percentage of document is tested?
  - Are all critical elements covered?

#### 2. Adversarial Testing (Red Team Approach)

**Research adversarial methodologies:**
- How is **Red Teaming** applied to LLMs? (Goal: break the instruction, find loopholes)
- What are **Constitutional AI** patterns for robustness testing?
- How does **Metamorphic Testing** apply? (Predictable output changes for input variations)
- What adversarial categories exist in LLM security research?

**Design requirements:**
- **Adversarial categories:** Systematic classification
  - Trick questions (misleading but grammatically valid)
  - Edge cases (boundary conditions, missing data)
  - Contradictions (conflicting instructions within document)
  - Malicious compliance (formally correct but wrong interpretation)
  - Context manipulation (questions that exploit missing context)
- **Generation strategy:** How to systematically create adversarial questions
  - Pattern-based generation
  - Mutation of positive questions
  - Targeted probing of detected weak points
- **Success criteria:** What constitutes passing adversarial tests?
  - Model refuses to answer (recognizes trap)
  - Model asks for clarification
  - Model identifies contradiction
  - Model provides correct answer despite adversarial framing
- **Fair testing:** Distinguish between legitimate ambiguity and unfair trick questions

#### 3. Multi-Level Question Strategy

**Section-level questions:**
- Scope: Single section content
- Purpose: Test specific comprehension
- Generation: Parse section → identify key elements → generate questions
- Example workflow section: "What is the first step?" "What happens if X fails?"

**Document-level questions:**
- Scope: Entire document or multiple sections
- Purpose: Test holistic understanding, find internal conflicts
- Generation: Analyze cross-references → identify dependencies → test consistency
- Example multi-step workflow: "Can Step 4 execute if Step 2 was skipped?" "Do validation checks cover all steps?"

**Critical insight for document-level:**
When models are asked to implement a task from documentation, they must understand:
- The big picture (overall goal)
- Cross-section dependencies (Step 3 needs output from Step 1)
- Internal consistency (no contradictions between sections)

**Questions WITHOUT section specification reveal:**
- Whether models can navigate the document correctly
- Whether conflicting instructions exist
- Whether the document works as a cohesive whole

#### 4. Integration Architecture

**Design the integration:**
- **Where does question-based testing fit?**
  - New step after Detection? (6th step)
  - Enhancement to Testing step? (test interpretations AND answers)
  - Parallel to interpretation testing? (separate analysis track)
- **How do results combine?**
  - Question failures → new Ambiguity type?
  - Question results feed into existing severity scoring?
  - Separate report section for Q&A results?
- **Artifact design:**
  - `questions.json` - Generated questions with metadata
  - `answers.json` - Model answers to questions
  - `question_results.json` - Evaluation of answer correctness
- **Modular implementation:**
  - New step module: `questioning_step.py`?
  - New CLI script: `test_questions.py`?
  - Integration with existing detection logic?

#### 5. Practical Implementation Specifications

**Question generation algorithm:**
- Input: Document sections, metadata (types, cross-references)
- Process: Parsing → element extraction → question template application
- Output: Question objects with {question, expected_answer, type, scope, section_id}

**Answer evaluation approach:**
- Positive questions: Correctness scoring (exact match, semantic similarity, judge comparison)
- Adversarial questions: Robustness scoring (refused, clarified, trapped)
- Aggregation: Per-section scores, document-level scores

**Data structures (JSON schemas):**
- Question object format
- Answer object format
- QuestionResult object format (similar to existing Ambiguity object)

**Workflow specification:**
1. Question generation (when? automated or manual review?)
2. Model querying (sessions? stateless?)
3. Answer evaluation (judge? automatic?)
4. Results aggregation (how to combine with interpretation results?)

---

## Industry Standards & References

**Your research should reference:**

**LLM Testing Frameworks:**
- Giskard - Consistency and hallucination metrics
- DeepEval - LLM evaluation patterns
- Constitutional AI (Anthropic) - Model alignment and robustness
- Chain-of-Verification (CoVe) - Self-checking mechanisms

**Testing Methodologies:**
- Metamorphic Testing - Predictable transformations
- Red Teaming - Adversarial probing techniques
- Reading Comprehension benchmarks (SQuAD, etc.)
- QA system evaluation metrics

**Documentation Quality:**
- Google Technical Writing courses - Ambiguity elimination
- Vale prose linter - Rule pattern structures
- "Docs Like Code" - CI/CD for documentation
- "Docs for Developers" - Testing documentation

**Apply industry best practices where they exist. Be opinionated based on research.**

---

## Required Documentation Output

Structure your documentation with these sections:

### 1. Executive Summary
- Problem statement
- Proposed solution approach
- Key innovations beyond current interpretation testing

### 2. Research Findings
- Industry standards identified
- Best practices from LLM evaluation field
- Relevant methodologies and frameworks
- Citations and references

### 3. Question-Based Testing Design
- **Question generation strategy** (section-level and document-level)
- **Question taxonomy** (types and purposes)
- **Answer evaluation methodology**
- **Coverage and metrics**
- **Positive scenario approach** (verify correct understanding)

### 4. Adversarial Testing Design
- **Adversarial categories** (trick, edge case, contradiction, etc.)
- **Generation patterns** (how to systematically create adversarial questions)
- **Success criteria** (what constitutes passing/failing)
- **Fair testing principles** (avoid unfair tricks)
- **Red team scenario approach** (test robustness)

### 5. Multi-Level Testing Strategy
- **Section-level questions** (specific comprehension)
- **Document-level questions** (holistic understanding, conflict detection)
- **Rationale** for dual-level approach
- **Question scoping rules**

### 6. Integration Architecture
- **Pipeline placement** (where question testing fits)
- **Artifact specification** (JSON schemas)
- **Result combination** (how question results merge with interpretation results)
- **Modular design** (new step modules, CLI scripts)

### 7. Implementation Specification
- **Question generation algorithm** (detailed methodology)
- **Answer evaluation approach** (correctness determination)
- **Workflow steps** (generation → querying → evaluation → reporting)
- **Data structures** (schemas for questions, answers, results)

### 8. Success Metrics & Validation
- How to measure effectiveness of question-based testing
- What constitutes successful detection of ambiguities
- How to validate the approach works

---

## Documentation Requirements

**What to include:**
- ✅ Industry-standard approaches (research-backed)
- ✅ Detailed reasoning for each design choice
- ✅ JSON schemas for all artifacts
- ✅ Clear integration guidance with existing architecture
- ✅ Both positive and adversarial scenarios
- ✅ Section-level AND document-level testing
- ✅ Automated question generation strategies
- ✅ Answer evaluation methodologies
- ✅ References to research and standards

**What to exclude:**
- ❌ Code implementation (will be implemented separately)
- ❌ Specific library/framework requirements (keep language-agnostic)
- ❌ UI/UX considerations (CLI-focused system)

**Writing style:**
- Expert-level technical documentation
- Opinionated based on research (recommend specific approaches)
- Detailed specifications with clear rationale
- Implementable without code examples

---

## Key Design Principles

1. **Industry-first:** Prefer established standards over novel approaches
2. **Automated:** Questions generated automatically, not manually curated
3. **Dual-level:** Section comprehension AND document-level coherence
4. **Artifact-based:** Questions saved for review, versioning, reproducibility
5. **Modular:** Fits existing architecture patterns (Result dataclasses, CLI scripts)
6. **Incremental:** Support phased implementation (start simple, add complexity)
7. **Research-backed:** Each decision references industry standards or research

---

## Expected Outcome

Documentation that enables implementation of:
- **Question generation system** that automatically creates section-level and document-level questions
- **Answer evaluation system** that determines correctness using industry-standard approaches
- **Adversarial testing system** with multiple categories (trick, edge case, contradiction, etc.)
- **Integration with existing pipeline** that enhances (not replaces) interpretation testing
- **Artifact generation** that produces reviewable question sets

The documentation should be comprehensive enough that a developer familiar with the existing codebase can implement the entire question-based testing framework without additional design work.

---

**You are the expert. Apply your knowledge of industry standards, research, and best practices to design the optimal question-based testing framework for LLM documentation evaluation.**
