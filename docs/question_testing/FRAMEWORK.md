# Question-Based Testing Framework for LLM Documentation Evaluation

**Version:** 1.0  
**Date:** December 2025  
**Author:** Document Polishing System Design Team  
**Purpose:** Comprehensive design specification for question-based testing to complement interpretation-based ambiguity detection

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Research Findings](#2-research-findings)
3. [Question-Based Testing Design](#3-question-based-testing-design)
4. [Adversarial Testing Design](#4-adversarial-testing-design)
5. [Multi-Level Testing Strategy](#5-multi-level-testing-strategy)
6. [Integration Architecture](#6-integration-architecture)
7. [Implementation Specification](#7-implementation-specification)
8. [Success Metrics & Validation](#8-success-metrics--validation)

---

## 1. Executive Summary

### 1.1 Problem Statement

The current document polishing system evaluates documentation quality through **interpretation testing**: models are asked "How do you understand this section?" and disagreements reveal ambiguities. While effective, this approach has a fundamental gap:

**Interpretation testing catches HOW models understand text, but not WHETHER they can correctly USE that understanding.**

Consider documentation with a 5-step workflow. Even if all models interpret each step identically, they might still:
- Fail to correctly answer "What happens if Step 3 is skipped?"
- Not recognize that Step 1 and Step 4 contain contradictory requirements
- Make incorrect inferences when combining information from multiple sections

### 1.2 Proposed Solution

A **Question-Based Testing Framework** operating at two levels:

| Level | Scope | Purpose | Key Benefit |
|-------|-------|---------|-------------|
| **Section-Level** | Individual sections | Verify specific comprehension | Catches granular misunderstandings |
| **Document-Level** | Entire document | Test holistic understanding | Reveals cross-section conflicts |

This framework complements (not replaces) existing interpretation testing by:
1. **Generating questions automatically** from documentation structure
2. **Evaluating answers** using LLM-as-Judge methodology
3. **Including adversarial probes** inspired by red-teaming practices
4. **Detecting conflicts** that only appear when considering the full document

### 1.3 Key Innovations

1. **Dual-Level Testing**: Unlike single-scope approaches, tests both specific comprehension AND holistic understanding
2. **Automated Question Generation**: No manual curation required—questions derived from document structure
3. **Conflict Detection Questions**: Document-level questions specifically designed to reveal internal contradictions
4. **Adversarial Categories**: Systematic probing based on red-teaming taxonomy (trick questions, edge cases, contradiction exploits)
5. **Chain-of-Verification Integration**: Self-checking mechanisms adapted from CoVe methodology

---

## 2. Research Findings

### 2.1 Industry Standards Identified

#### 2.1.1 LLM Evaluation Frameworks

**Giskard Framework**
- Uses automated test generation from knowledge base content
- RAGET (RAG Evaluation Toolkit) generates 6 question types automatically
- Employs LLM-as-Judge for answer evaluation
- Key insight: Questions test both retrieval AND generation quality

**DeepEval Framework**
- "Pytest for LLMs" approach with unit-test-like syntax
- 30+ prebuilt metrics including answer relevancy and factual consistency
- Supports G-Eval (LLM-based evaluation with criteria)
- Key insight: Combines deterministic checks with LLM-based semantic evaluation

**OpenAI Evals**
- Registry of evaluation templates for various tasks
- Supports both ground-truth and model-graded evaluation
- CI/CD integration capability
- Key insight: Modular evaluation design enables custom metric addition

#### 2.1.2 Chain-of-Verification (CoVe)

From Meta AI's 2023 paper "Chain-of-Verification Reduces Hallucination in Large Language Models":

**Four-Step Process:**
1. Generate baseline response
2. Plan verification questions to fact-check the response
3. Answer verification questions independently
4. Generate final verified response

**Key Adaptation for Documentation Testing:**
- Use verification questions to check document comprehension
- Independent answering prevents confirmation bias
- Cross-check answers against document source

**Execution Variants:**
| Variant | Description | Best For |
|---------|-------------|----------|
| Joint | Single prompt for questions + answers | Speed |
| 2-Step | Separate prompts for questions and answers | Quality |
| Factored | Each question answered independently | Accuracy |
| Factor+Revise | Cross-check for inconsistencies | Thoroughness |

**Recommendation:** Use **Factored** variant for section-level questions, **Factor+Revise** for document-level questions.

#### 2.1.3 Metamorphic Testing

From literature including METAL framework (2023) and LLMorph (2025):

**Core Concept:** Test relationships between inputs/outputs without requiring ground truth labels.

**Metamorphic Relations (MRs) for Documentation:**

| Relation Type | Description | Example |
|---------------|-------------|---------|
| Invariance | Output unchanged under certain transformations | Rephrasing question shouldn't change answer |
| Equivalence | Different inputs produce equivalent outputs | Synonym substitution yields same interpretation |
| Negation | Negated input produces negated output | "Should NOT do X" yields opposite of "Should do X" |
| Subsumption | Broader query includes narrower query results | "All steps" includes "Step 1" |

**Key Finding:** Metamorphic testing exposed 18% failure rate in LLMs across NLP tasks (LLMorph study with 561,267 tests).

#### 2.1.4 Red Teaming Methodologies

From Microsoft, Anthropic, and DeepTeam frameworks:

**Vulnerability Categories:**

1. **Jailbreaking**: Bypassing safety guardrails
2. **Prompt Injection**: Malicious prompt manipulation
3. **Hallucination Inducement**: Questions designed to trigger false claims
4. **Sycophancy Exploitation**: Leading questions that bias responses
5. **Context Manipulation**: Exploiting missing or ambiguous context

**Adversarial Attack Patterns:**

| Pattern | Description | Documentation Application |
|---------|-------------|---------------------------|
| Assumption Injection | Include false premise in question | "Since Step 3 requires X (it doesn't), what happens when..." |
| Contradiction Probing | Ask about conflicting requirements | "How do you reconcile Step 2's requirement with Step 5's?" |
| Edge Case Stress | Push boundaries of stated rules | "What if the input has 0 items? 10 million items?" |
| Malicious Compliance | Follow instructions "correctly" but harmfully | "Step says 'validate all fields'—including user passwords?" |

### 2.2 Best Practices from QA Research

#### 2.2.1 SQuAD Benchmark Methodology

The Stanford Question Answering Dataset established:

**Question Types:**
- Factual (who, what, when, where)
- Reasoning-required (why, how)
- Numerical (how many, what percentage)
- Yes/No with justification
- Unanswerable (SQuAD 2.0 addition)

**Evaluation Metrics:**
- **Exact Match (EM)**: Percentage of exact answer matches
- **F1 Score**: Token-level overlap between prediction and ground truth
- **Semantic Equivalence**: LLM-as-Judge for meaning preservation

**Key Insight for Documentation:** Including **unanswerable questions** tests whether models correctly recognize when documentation doesn't provide sufficient information.

#### 2.2.2 Question Generation Strategies

From reading comprehension literature:

| Strategy | Description | Quality |
|----------|-------------|---------|
| Template-based | Fill slots in question templates | High consistency, lower diversity |
| Entity-based | Generate questions about extracted entities | Good for factual questions |
| Clause-based | Transform declarative sentences to questions | Natural language quality |
| LLM-generated | Use LLM to generate questions from content | High diversity, needs validation |

**Recommendation:** Use **hybrid approach**—template-based for structural questions (step sequences, requirements), LLM-generated for reasoning questions (why, how, implications).

### 2.3 Relevant Citations and References

| Source | Key Contribution | Year |
|--------|------------------|------|
| Dhuliawala et al., "Chain-of-Verification Reduces Hallucination" | CoVe methodology | 2023 |
| Hyun et al., "METAL: Metamorphic Testing for LLMs" | MR framework for LLMs | 2023 |
| Rajpurkar et al., "SQuAD" | Reading comprehension benchmark | 2016 |
| Giskard Team, "RAGET Toolkit" | RAG evaluation questions | 2024 |
| Microsoft, "Planning Red Teaming for LLMs" | Red teaming methodology | 2024 |
| Confident AI, "DeepEval" | LLM evaluation framework | 2024 |

---

## 3. Question-Based Testing Design

### 3.1 Question Generation Strategy

#### 3.1.1 Automated Generation Pipeline

```
Document → Parse Structure → Identify Testable Elements → Select Templates → Generate Questions → Validate Questions → Question Catalog
```

**Stage 1: Parse Structure**
- Extract headers, sections, code blocks
- Identify lists (numbered, bulleted)
- Detect cross-references
- Mark instruction keywords

**Stage 2: Identify Testable Elements**

| Element Type | Extraction Pattern | Example |
|--------------|-------------------|---------|
| Steps | "Step N:", numbered lists | "Step 3: Validate input..." |
| Requirements | "must", "required", "shall" | "File must be UTF-8 encoded" |
| Conditionals | "if", "when", "unless" | "If input is empty, return error" |
| Outputs | "produces", "generates", "returns" | "Returns a JSON object" |
| Inputs | "accepts", "takes", "requires" | "Takes a file path argument" |
| Constraints | "maximum", "minimum", "at least" | "Maximum 1000 entries" |
| Defaults | "by default", "defaults to" | "Timeout defaults to 30 seconds" |
| Exceptions | "except", "unless", "but not" | "All fields except timestamps" |

**Stage 3: Template Selection**

For each testable element, select appropriate question templates based on element type and surrounding context.

**Stage 4: Question Generation**

Apply templates to extracted elements, using LLM for complex reasoning questions.

**Stage 5: Validation**

- Ensure question is answerable from document
- Verify question doesn't leak answer
- Check question is grammatically correct
- Confirm question tests single concept

#### 3.1.2 Section-Level Question Templates

**Factual Questions:**
```
Template: "According to [section], what is [specific_detail]?"
Example: "According to Step 3, what format should the output file use?"

Template: "What does [section] specify about [element]?"
Example: "What does the Configuration section specify about timeout values?"
```

**Procedural Questions:**
```
Template: "What is the [ordinal] step in [process]?"
Example: "What is the third step in the validation process?"

Template: "What must be completed before [step]?"
Example: "What must be completed before running the export command?"
```

**Conditional Questions:**
```
Template: "What happens when [condition] in [section]?"
Example: "What happens when the input file is empty in the Processing section?"

Template: "Under what circumstances does [action] occur?"
Example: "Under what circumstances does the system retry the connection?"
```

**Quantitative Questions:**
```
Template: "How many [items] does [section] require?"
Example: "How many validation passes does Step 2 require?"

Template: "What is the [maximum/minimum] [measurement] specified?"
Example: "What is the maximum file size specified for uploads?"
```

**Existence Questions:**
```
Template: "Does [section] mention [concept]?"
Example: "Does the Error Handling section mention timeout exceptions?"

Template: "Is [action] required or optional according to [section]?"
Example: "Is logging required or optional according to the Configuration section?"
```

#### 3.1.3 Document-Level Question Templates

**Cross-Reference Questions:**
```
Template: "How does [section_A] relate to [section_B]?"
Example: "How does the Input Validation section relate to Error Handling?"

Template: "What output from [section_A] is used as input in [section_B]?"
Example: "What output from Step 2 is used as input in Step 5?"
```

**Dependency Questions:**
```
Template: "Can [section_B] be executed without completing [section_A]?"
Example: "Can Step 4 be executed without completing Step 2?"

Template: "What are all the prerequisites for [section]?"
Example: "What are all the prerequisites for running the final export?"
```

**Conflict Detection Questions:**
```
Template: "Is there any conflict between [requirement_A] and [requirement_B]?"
Example: "Is there any conflict between the 'validate all fields' requirement and the 'skip null values' instruction?"

Template: "How should [conflicting_instruction] be interpreted given [other_instruction]?"
Example: "How should 'process immediately' be interpreted given 'wait for batch completion'?"
```

**Holistic Understanding Questions:**
```
Template: "What is the overall goal of this workflow?"
Example: "What is the overall goal of the data migration workflow?"

Template: "Summarize the complete process in [N] steps."
Example: "Summarize the complete validation process in 3 steps."

Template: "What are all the possible outcomes of this workflow?"
Example: "What are all the possible outcomes of the authentication flow?"
```

### 3.2 Question Taxonomy

#### 3.2.1 Primary Categories

| Category | Purpose | Scope | Generation Method |
|----------|---------|-------|-------------------|
| **Factual** | Verify specific facts are understood | Section | Template-based |
| **Procedural** | Verify step sequences are understood | Section/Document | Template-based |
| **Conditional** | Verify if/then logic is understood | Section | Template + LLM |
| **Cross-Reference** | Verify relationships between sections | Document | LLM-generated |
| **Conflict Detection** | Reveal internal contradictions | Document | LLM-generated |
| **Inference** | Test implied/derived understanding | Section/Document | LLM-generated |
| **Unanswerable** | Test recognition of missing info | Section | Template + LLM |

#### 3.2.2 Difficulty Levels

| Level | Description | Example |
|-------|-------------|---------|
| **Basic** | Direct extraction from single sentence | "What is the timeout value?" |
| **Intermediate** | Requires combining 2-3 facts | "What is the first step after validation?" |
| **Advanced** | Requires inference or cross-section reasoning | "If retry fails, what alternative exists?" |
| **Expert** | Requires holistic understanding + edge case reasoning | "What happens if Steps 2 and 4 both fail?" |

#### 3.2.3 Question Properties Schema

```json
{
  "question_id": "q_001",
  "question_text": "What format should the output file use?",
  "category": "factual",
  "difficulty": "basic",
  "scope": "section",
  "target_sections": ["section_3"],
  "expected_answer": "JSON format with UTF-8 encoding",
  "answer_source_lines": [45, 46],
  "generation_method": "template",
  "template_id": "factual_format_01",
  "is_adversarial": false,
  "adversarial_type": null,
  "requires_inference": false,
  "cross_references": []
}
```

### 3.3 Answer Evaluation Methodology

#### 3.3.1 Evaluation Approaches

**Approach 1: Exact Match**
- Use for: Numerical answers, specific terms, yes/no
- Pros: Fast, deterministic
- Cons: Fails on paraphrasing

**Approach 2: Semantic Similarity**
- Use for: Descriptive answers, explanations
- Method: Sentence embeddings + cosine similarity
- Threshold: 0.85 for equivalence, 0.40 for difference
- Pros: Handles paraphrasing
- Cons: May miss subtle distinctions

**Approach 3: LLM-as-Judge** *(Recommended)*
- Use for: All question types
- Method: Judge model compares expected vs actual answer
- Pros: Nuanced evaluation, handles reasoning
- Cons: Slower, requires additional API calls

#### 3.3.2 LLM-as-Judge Prompt

```
You are evaluating whether a model's answer correctly responds to a question based on documentation.

## Documentation Context
{document_excerpt}

## Question
{question_text}

## Expected Answer
{expected_answer}

## Model's Answer
{model_answer}

## Evaluation Criteria
1. Factual Correctness: Does the answer contain accurate information from the document?
2. Completeness: Does the answer address all parts of the question?
3. Relevance: Is the answer focused on what was asked?
4. No Hallucination: Does the answer avoid adding information not in the document?

## Your Task
Evaluate the model's answer and provide:
1. Score: correct / partially_correct / incorrect / unanswerable
2. Reasoning: Explain your scoring decision
3. Evidence: Quote the document text that supports your evaluation

Respond in JSON format:
{
  "score": "correct|partially_correct|incorrect|unanswerable",
  "reasoning": "...",
  "evidence": "..."
}
```

#### 3.3.3 Scoring Matrix

| Judge Score | Meaning | Action |
|-------------|---------|--------|
| `correct` | Answer matches expected meaning | Pass |
| `partially_correct` | Answer is incomplete or imprecise | Flag for review |
| `incorrect` | Answer contradicts expected answer | Fail - Potential ambiguity |
| `unanswerable` | Model correctly recognized missing info | Pass (for unanswerable questions) |
| `hallucinated` | Answer includes fabricated information | Fail - Critical issue |

### 3.4 Coverage Metrics

#### 3.4.1 Section Coverage

```
Section Coverage = (Sections with ≥1 question) / (Total testable sections)
Target: ≥ 95%
```

#### 3.4.2 Element Coverage

```
Element Coverage = (Tested elements) / (Total testable elements)
Target: ≥ 80%
```

#### 3.4.3 Question Type Distribution

| Category | Target % |
|----------|----------|
| Factual | 30-40% |
| Procedural | 20-25% |
| Conditional | 15-20% |
| Cross-Reference | 10-15% |
| Conflict Detection | 5-10% |
| Inference | 5-10% |
| Unanswerable | 5% |

#### 3.4.4 Difficulty Distribution

| Level | Target % |
|-------|----------|
| Basic | 40% |
| Intermediate | 35% |
| Advanced | 20% |
| Expert | 5% |

---

## 4. Adversarial Testing Design

### 4.1 Adversarial Categories

Based on red teaming literature and documentation-specific failure modes:

#### 4.1.1 Category Taxonomy

| Category | Description | Purpose |
|----------|-------------|---------|
| **Trick Questions** | Grammatically valid but misleading | Test careful reading |
| **Edge Case Probes** | Boundary conditions and limits | Test completeness |
| **Contradiction Exploits** | Highlight internal conflicts | Find documentation bugs |
| **Assumption Tests** | Questions with false premises | Test critical thinking |
| **Context Manipulation** | Exploit missing context | Find gaps |
| **Malicious Compliance** | Literal interpretation traps | Test clarity |

#### 4.1.2 Trick Questions

**Purpose:** Test whether models read carefully vs. pattern match.

**Generation Patterns:**

| Pattern | Example |
|---------|---------|
| Negation confusion | "Which step does NOT require validation?" (when all do) |
| Similar term swap | Ask about "input file" when doc says "output file" |
| Quantity distortion | "What are the 5 steps?" (when there are only 4) |
| False attribution | "According to Section 3..." (when info is in Section 5) |

**Template:**
```
Trick Question Type: Negation Confusion
Document states: "All API calls must be authenticated."
Trick Question: "Which API calls can bypass authentication?"
Expected Response: Recognition that no API calls can bypass authentication.
Pass Criteria: Model explicitly states no exceptions exist.
```

#### 4.1.3 Edge Case Probes

**Purpose:** Test handling of boundary conditions not explicitly covered.

**Generation Patterns:**

| Pattern | Example |
|---------|---------|
| Zero/empty input | "What if the input list is empty?" |
| Maximum limits | "What if there are 1 million entries?" |
| Null/missing values | "What if required field is null?" |
| Type edge cases | "What if ID is negative?" |
| Concurrent operations | "What if two users run this simultaneously?" |

**Template:**
```
Edge Case Type: Empty Input
Document states: "Process all items in the list."
Edge Question: "What happens if the list contains zero items?"
Expected Behavior: Model acknowledges edge case is not specified OR provides reasonable inference.
Pass Criteria: Model does not hallucinate a specific behavior not in document.
```

#### 4.1.4 Contradiction Exploits

**Purpose:** Explicitly test for internal document conflicts.

**Generation Strategy:**
1. Identify statements that could conflict
2. Formulate question requiring reconciliation
3. Evaluate whether model detects the conflict

**Examples:**

| Statement A | Statement B | Exploit Question |
|-------------|-------------|------------------|
| "Timeout: 30 seconds" | "All operations complete within 10s" | "What happens if an operation takes 20 seconds?" |
| "Validate all fields" | "Skip empty fields" | "Should an empty required field be validated?" |
| "Process in order" | "Parallelize for speed" | "Can steps 3 and 4 run simultaneously?" |

**Template:**
```
Contradiction Type: Conflicting Requirements
Statement 1 (Line 45): "All fields must be validated."
Statement 2 (Line 89): "Empty fields should be skipped."
Contradiction Question: "When processing a record, should an empty 'email' field be validated or skipped?"
Expected Response: Model identifies the contradiction OR asks for clarification.
Pass Criteria: Model does not confidently give a single answer without acknowledging ambiguity.
```

#### 4.1.5 Assumption Tests

**Purpose:** Test whether models accept false premises in questions.

**Generation Pattern:**
1. Identify a document fact
2. Formulate question with opposite assumption
3. Check if model corrects the assumption

**Examples:**

| Document Fact | False Assumption | Question |
|---------------|------------------|----------|
| "Uses JSON format" | Assumes XML | "How should the XML output be formatted?" |
| "Runs on Linux" | Assumes Windows | "Where is the Windows registry key stored?" |
| "Requires authentication" | Assumes public | "How do anonymous users access this?" |

**Template:**
```
Assumption Type: False Premise
Document states: "The system uses JSON format for all outputs."
False Assumption Question: "What XPath expressions should be used to parse the XML output?"
Expected Response: Model corrects the premise—outputs are JSON, not XML.
Pass Criteria: Model rejects the premise rather than answering based on false assumption.
Failure Mode: Model provides XPath expressions (hallucination).
```

#### 4.1.6 Context Manipulation

**Purpose:** Probe for missing context or unstated dependencies.

**Generation Strategy:**
1. Identify implicit context in documentation
2. Ask questions that require explicit context
3. Check if model recognizes the gap

**Examples:**

| Implicit Context | Explicit Question |
|------------------|-------------------|
| Assumes network connection | "What if the system is offline?" |
| Assumes admin privileges | "Can regular users perform this?" |
| Assumes specific version | "Does this work with version 1.0?" |

#### 4.1.7 Malicious Compliance

**Purpose:** Test whether literal interpretation leads to unreasonable outcomes.

**Generation Pattern:**
1. Find instructions that could be interpreted too literally
2. Formulate question exposing the literal interpretation
3. Check if model applies reasonable bounds

**Examples:**

| Instruction | Malicious Literal Reading | Question |
|-------------|---------------------------|----------|
| "Retry until success" | Infinite retry loop | "Should retries continue for 24 hours?" |
| "Log all activity" | Log sensitive data | "Should passwords be included in logs?" |
| "Process all files" | Process system files | "Should /etc/passwd be processed?" |

### 4.2 Generation Patterns

#### 4.2.1 Pattern-Based Generation

For each adversarial category, define patterns that can be applied to document elements:

```python
# Pseudocode for adversarial generation
adversarial_patterns = {
    "negation_confusion": {
        "trigger": "statements with 'all', 'every', 'must'",
        "transform": "ask which ones are exceptions",
        "expected_behavior": "recognize no exceptions"
    },
    "false_premise": {
        "trigger": "definitive statements (format, platform, etc.)",
        "transform": "assume opposite in question",
        "expected_behavior": "correct the false premise"
    },
    "edge_case": {
        "trigger": "quantitative statements",
        "transform": "ask about boundary values",
        "expected_behavior": "acknowledge unspecified or infer reasonably"
    }
}
```

#### 4.2.2 Mutation of Positive Questions

Start with correctly-generated positive questions and mutate:

| Original Question | Mutation Type | Adversarial Version |
|-------------------|---------------|---------------------|
| "What format is used?" | False premise | "Why is XML used instead of JSON?" |
| "How many steps?" | Quantity distortion | "What happens in the 6th step?" (only 5 exist) |
| "When is retry triggered?" | Negation | "When should retry be skipped?" (never) |

#### 4.2.3 LLM-Assisted Adversarial Generation

**Prompt for Generating Adversarial Questions:**

```
You are a documentation quality tester. Given this documentation section, generate adversarial questions that test the model's ability to:
1. Reject false premises
2. Recognize missing information
3. Identify edge cases
4. Detect contradictions

## Documentation Section
{section_content}

## Generate 3 adversarial questions for each category:
- Trick Question (misleading but grammatically valid)
- Edge Case (boundary conditions)
- False Premise (includes incorrect assumption)

For each question, provide:
- Question text
- Adversarial type
- Expected correct behavior
- What failure would look like

Output as JSON array.
```

### 4.3 Success Criteria

#### 4.3.1 Passing Adversarial Tests

| Adversarial Type | Pass Criteria |
|------------------|---------------|
| Trick Question | Recognizes the trick, answers correctly |
| Edge Case | Acknowledges unspecified OR provides reasonable inference with caveat |
| Contradiction | Identifies conflict OR asks for clarification |
| False Premise | Corrects the premise before answering |
| Context Manipulation | Recognizes missing context |
| Malicious Compliance | Applies reasonable bounds |

#### 4.3.2 Failure Indicators

| Failure Type | Description | Severity |
|--------------|-------------|----------|
| Falls for trick | Answers incorrect question | Medium |
| Hallucinated edge case | Invents behavior not in doc | High |
| Ignores contradiction | Picks one side without acknowledgment | Critical |
| Accepts false premise | Answers based on wrong assumption | High |
| Overconfident | Claims certainty on ambiguous points | Medium |

### 4.4 Fair Testing Principles

#### 4.4.1 What Makes a Test "Fair"

Adversarial tests should be:
1. **Answerable from context**: Either the document addresses it, or it's legitimately missing
2. **Not require external knowledge**: Don't test general knowledge, test document comprehension
3. **Have clear success criteria**: Unambiguous what constitutes passing
4. **Be proportionate**: Difficulty matches document complexity

#### 4.4.2 What Makes a Test "Unfair"

Avoid tests that:
1. **Require reasoning beyond document scope**: "How would this compare to competitor's approach?"
2. **Are purely linguistic tricks**: "Answer this question without using the letter 'e'"
3. **Test implementation, not comprehension**: "Write the code for this step"
4. **Have no reasonable answer**: Purely philosophical questions

#### 4.4.3 Fairness Validation Checklist

```
□ Can a human expert answer this from the document alone?
□ Is there a clear correct/incorrect distinction?
□ Does failure indicate a documentation problem (not a model problem)?
□ Is the adversarial element realistic (could occur in practice)?
```

---

## 5. Multi-Level Testing Strategy

### 5.1 Section-Level Questions

#### 5.1.1 Scope Definition

Section-level questions:
- Reference content within a single section (header to next header)
- Can be answered without reading other sections
- Test specific, granular comprehension
- Identify localized ambiguities

#### 5.1.2 Generation Process

```
For each section in document:
    1. Extract testable elements (requirements, steps, conditions)
    2. Classify section type (instruction, configuration, reference)
    3. Select appropriate templates for section type
    4. Generate 2-5 questions per section based on element count
    5. Include at least 1 adversarial question per section
    6. Validate questions against section content
```

#### 5.1.3 Section Type → Question Strategy Mapping

| Section Type | Primary Question Types | Example |
|--------------|------------------------|---------|
| Procedure/Steps | Procedural, Conditional | "What is the order of steps?" |
| Configuration | Factual, Edge Cases | "What is the default timeout?" |
| Reference | Existence, Cross-reference | "Is X mentioned in this section?" |
| Requirements | Conditional, Constraint | "When is X required?" |
| Examples | Inference, Application | "What would be the output for input Y?" |

### 5.2 Document-Level Questions

#### 5.2.1 Scope Definition

Document-level questions:
- Span multiple sections or the entire document
- Require synthesizing information from different parts
- Test holistic understanding of the workflow/system
- Reveal cross-section conflicts and dependencies

**Critical Insight:** When asking models to implement a workflow, they need holistic understanding. Document-level questions simulate this by NOT specifying which section to reference.

#### 5.2.2 Generation Process

```
For entire document:
    1. Build dependency graph (which sections reference others)
    2. Identify potential conflict pairs (statements that could contradict)
    3. Map workflow flow (inputs → processing → outputs)
    4. Generate cross-reference questions from dependency graph
    5. Generate conflict detection questions from conflict pairs
    6. Generate holistic understanding questions from workflow
    7. Include summary and "what-if" questions
```

#### 5.2.3 Document-Level Question Types

| Type | Purpose | Generation Source |
|------|---------|-------------------|
| **Workflow Summary** | Test overall understanding | Document structure |
| **Dependency Chain** | Test prerequisite understanding | Section references |
| **Conflict Detection** | Find contradictions | Statement pair analysis |
| **Missing Link** | Find gaps between sections | Workflow analysis |
| **Integration** | Test combined requirements | Multiple sections |

#### 5.2.4 Examples

**Workflow Summary:**
```
Question: "Summarize the complete data processing workflow in 4 key steps."
Scope: Entire document
Expected: Model synthesizes Steps 1-8 into 4 high-level phases
Failure: Model lists all 8 steps OR misses critical steps
```

**Dependency Chain:**
```
Question: "What must be completed before the export step can run?"
Scope: Multiple sections
Expected: Model identifies all prerequisites across sections
Failure: Model only mentions immediate predecessor
```

**Conflict Detection:**
```
Question: "Section 2 says 'validate all fields' and Section 5 says 'skip optional fields'. How should the system handle an empty optional field?"
Scope: Sections 2 and 5
Expected: Model identifies the tension and either reconciles OR flags as ambiguous
Failure: Model confidently picks one interpretation without acknowledging the other
```

### 5.3 Rationale for Dual-Level Approach

#### 5.3.1 Why Section-Level Alone Is Insufficient

| Limitation | Example |
|------------|---------|
| Misses cross-references | "Uses output from Step 2" in Step 5 isn't tested |
| Can't detect conflicts | "Validate all" vs "Skip empty" in different sections |
| No workflow testing | Model may understand parts but not the whole |
| Context isolation | Real usage requires connecting sections |

#### 5.3.2 Why Document-Level Alone Is Insufficient

| Limitation | Example |
|------------|---------|
| Misses granular issues | Specific format requirements unclear |
| Too broad to pinpoint | Failure could be in any section |
| Lower coverage | Can't ask about every detail |
| Harder to fix | Ambiguity location unclear |

#### 5.3.3 Complementary Benefits

| Aspect | Section-Level | Document-Level | Combined |
|--------|---------------|----------------|----------|
| Granularity | High | Low | Both |
| Conflict Detection | None | High | Full |
| Coverage | High | Medium | Complete |
| Fix Targeting | Precise | Broad | Precise + Broad |
| Real-World Simulation | Low | High | Balanced |

### 5.4 Question Scoping Rules

#### 5.4.1 Scope Assignment Logic

```
if question_references_single_section:
    scope = "section"
    target_sections = [referenced_section]
elif question_references_multiple_sections:
    scope = "document"
    target_sections = [all_referenced_sections]
elif question_is_holistic_summary:
    scope = "document"
    target_sections = ["full_document"]
elif question_tests_dependency:
    scope = "document"
    target_sections = [dependent_sections]
else:
    scope = "section"  # default to narrower scope
```

#### 5.4.2 Scope Validation

Each question should pass:
```
□ Scope matches question content (section vs document)
□ Target sections are correctly identified
□ Expected answer aligns with scope
□ Difficulty is appropriate for scope
```

---

## 6. Integration Architecture

### 6.1 Pipeline Placement

#### 6.1.1 Current Pipeline (5 Steps)

```
1. Extraction → 2. Session Init → 3. Testing → 4. Detection → 5. Reporting
                                    ↑
                            (Interpretation testing)
```

#### 6.1.2 Extended Pipeline with Question Testing

**Option A: New Step After Detection (Recommended)**

```
1. Extraction → 2. Session Init → 3. Testing → 4. Detection → 5. Questioning → 6. Reporting
                                                                    ↑
                                                        (Question-based testing)
```

**Rationale:**
- Question testing builds on extraction results
- Can use same model sessions
- Results combine naturally with interpretation ambiguities
- Maintains modularity

**Option B: Parallel to Interpretation Testing**

```
                              ┌→ 3a. Interpretation Testing → 4a. Interpretation Detection ┐
1. Extraction → 2. Session Init                                                              → 5. Combined Reporting
                              └→ 3b. Question Testing → 4b. Question Evaluation ─────────────┘
```

**Rationale:**
- Independent execution possible
- Can run in parallel for speed
- Clear separation of concerns

**Recommendation:** **Option A** for initial implementation (simpler), with architecture supporting Option B for future optimization.

### 6.2 Artifact Specification

#### 6.2.1 Questions Artifact

**File:** `questions.json`

```json
{
  "document_path": "path/to/document.md",
  "generation_timestamp": "2025-12-27T10:30:00Z",
  "generator_version": "1.0.0",
  "statistics": {
    "total_questions": 45,
    "section_level": 35,
    "document_level": 10,
    "adversarial": 12,
    "by_category": {
      "factual": 15,
      "procedural": 10,
      "conditional": 8,
      "cross_reference": 5,
      "conflict_detection": 4,
      "inference": 3
    }
  },
  "questions": [
    {
      "question_id": "q_001",
      "question_text": "What format should the output file use?",
      "category": "factual",
      "difficulty": "basic",
      "scope": "section",
      "target_sections": ["section_3"],
      "expected_answer": {
        "text": "JSON format with UTF-8 encoding",
        "source_lines": [45, 46],
        "confidence": "high"
      },
      "generation_method": "template",
      "template_id": "factual_format_01",
      "is_adversarial": false,
      "adversarial_type": null,
      "metadata": {
        "testable_element": "output_format",
        "keywords": ["format", "JSON", "UTF-8"]
      }
    },
    {
      "question_id": "q_012",
      "question_text": "How should the system handle an empty optional field given the 'validate all' requirement?",
      "category": "conflict_detection",
      "difficulty": "advanced",
      "scope": "document",
      "target_sections": ["section_2", "section_5"],
      "expected_answer": {
        "text": "Ambiguity should be recognized - conflicting requirements exist",
        "source_lines": [23, 89],
        "confidence": "medium"
      },
      "generation_method": "llm",
      "is_adversarial": true,
      "adversarial_type": "contradiction_exploit",
      "metadata": {
        "conflict_pair": ["validate_all", "skip_optional"],
        "expected_failure_mode": "picks_one_without_acknowledgment"
      }
    }
  ]
}
```

#### 6.2.2 Answers Artifact

**File:** `answers.json`

```json
{
  "session_id": "polish_20251227_103000",
  "questions_file": "questions.json",
  "testing_timestamp": "2025-12-27T10:45:00Z",
  "models_tested": ["claude", "gemini", "gpt4"],
  "answers": [
    {
      "question_id": "q_001",
      "model_answers": {
        "claude": {
          "answer_text": "The output should be in JSON format, encoded as UTF-8.",
          "response_time_ms": 1234,
          "raw_response": "...",
          "confidence_stated": null
        },
        "gemini": {
          "answer_text": "JSON with UTF-8 encoding is required.",
          "response_time_ms": 987,
          "raw_response": "...",
          "confidence_stated": null
        },
        "gpt4": {
          "answer_text": "According to the documentation, outputs must be JSON-formatted and use UTF-8 encoding.",
          "response_time_ms": 1456,
          "raw_response": "...",
          "confidence_stated": null
        }
      }
    }
  ]
}
```

#### 6.2.3 Question Results Artifact

**File:** `question_results.json`

```json
{
  "session_id": "polish_20251227_103000",
  "evaluation_timestamp": "2025-12-27T11:00:00Z",
  "judge_model": "claude",
  "statistics": {
    "total_evaluated": 45,
    "correct": 38,
    "partially_correct": 4,
    "incorrect": 2,
    "unanswerable": 1,
    "agreement_score": 0.89,
    "adversarial_pass_rate": 0.75
  },
  "results": [
    {
      "question_id": "q_001",
      "question_text": "What format should the output file use?",
      "expected_answer": "JSON format with UTF-8 encoding",
      "model_evaluations": {
        "claude": {
          "score": "correct",
          "reasoning": "Answer correctly identifies JSON format and UTF-8 encoding.",
          "evidence": "Line 45: 'Output files must be JSON-formatted with UTF-8 encoding.'"
        },
        "gemini": {
          "score": "correct",
          "reasoning": "Equivalent answer, different phrasing.",
          "evidence": "Same source line."
        },
        "gpt4": {
          "score": "correct",
          "reasoning": "Complete and accurate.",
          "evidence": "Same source line."
        }
      },
      "consensus": "correct",
      "issue_detected": false,
      "issue_type": null
    },
    {
      "question_id": "q_012",
      "question_text": "How should the system handle an empty optional field given the 'validate all' requirement?",
      "expected_answer": "Ambiguity should be recognized - conflicting requirements exist",
      "model_evaluations": {
        "claude": {
          "score": "correct",
          "reasoning": "Model recognized the conflicting requirements and flagged ambiguity.",
          "evidence": "Model stated: 'There appears to be a conflict between...'"
        },
        "gemini": {
          "score": "incorrect",
          "reasoning": "Model confidently answered 'skip the field' without acknowledging conflict.",
          "evidence": "Model stated: 'Empty optional fields should be skipped.'"
        },
        "gpt4": {
          "score": "partially_correct",
          "reasoning": "Model mentioned both requirements but did not flag as conflicting.",
          "evidence": "Model described both behaviors as applicable."
        }
      },
      "consensus": "disagreement",
      "issue_detected": true,
      "issue_type": "conflict_not_detected",
      "severity": "high",
      "recommendation": "Clarify how 'validate all' interacts with optional field handling in Section 2 or Section 5."
    }
  ]
}
```

### 6.3 Result Combination

#### 6.3.1 Question Issues → Ambiguity Objects

When question testing reveals issues, convert to Ambiguity objects compatible with existing system:

```python
# Pseudocode
def question_issue_to_ambiguity(question_result):
    return Ambiguity(
        section_id=question_result.target_sections[0],
        section_header=get_header(question_result.target_sections[0]),
        section_content=get_content(question_result.target_sections),
        severity=map_severity(question_result.severity),
        detection_method="question_testing",
        question_context={
            "question_id": question_result.question_id,
            "question_text": question_result.question_text,
            "category": question_result.category,
            "is_adversarial": question_result.is_adversarial
        },
        interpretations=format_as_interpretations(question_result.model_evaluations),
        comparison_details={
            "expected_answer": question_result.expected_answer,
            "consensus": question_result.consensus,
            "recommendation": question_result.recommendation
        }
    )
```

#### 6.3.2 Severity Mapping

| Question Issue Type | Mapped Severity |
|---------------------|-----------------|
| Conflict not detected | CRITICAL |
| False premise accepted | HIGH |
| Incorrect answer | HIGH |
| Partially correct | MEDIUM |
| Edge case hallucination | HIGH |
| Adversarial failure | MEDIUM |

#### 6.3.3 Combined Report Structure

```markdown
# Document Polishing Report

## Executive Summary
- Interpretation Testing: X ambiguities found
- Question Testing: Y issues found
- Combined: Z total issues

## Interpretation Ambiguities
[Existing format]

## Question Testing Results
### Summary
- Questions Generated: 45
- Pass Rate: 89%
- Adversarial Pass Rate: 75%

### Issues Detected
#### Issue 1: Conflict Not Detected
- Question: "How should..."
- Section: 2, 5
- Models: gemini (failed), gpt4 (partial)
- Recommendation: Clarify...

### Coverage Report
- Section Coverage: 95%
- Element Coverage: 82%
- Question Distribution: [chart]
```

### 6.4 Modular Design

#### 6.4.1 New Step Module: `questioning_step.py`

```python
"""
Questioning Step - Generate and evaluate questions for documentation

This module provides Step 5 of the extended document polishing pipeline.
It generates questions from document structure, queries models, and
evaluates answers to detect comprehension issues.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path
import json


@dataclass
class Question:
    """Single question with metadata."""
    question_id: str
    question_text: str
    category: str
    difficulty: str
    scope: str
    target_sections: List[str]
    expected_answer: Dict
    generation_method: str
    is_adversarial: bool
    adversarial_type: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class QuestionAnswer:
    """Model's answer to a question."""
    question_id: str
    model_name: str
    answer_text: str
    response_time_ms: int
    raw_response: str


@dataclass
class QuestionEvaluation:
    """Judge's evaluation of an answer."""
    question_id: str
    model_name: str
    score: str  # correct, partially_correct, incorrect, unanswerable
    reasoning: str
    evidence: str


@dataclass
class QuestionResult:
    """Complete result for a question across all models."""
    question: Question
    answers: Dict[str, QuestionAnswer]
    evaluations: Dict[str, QuestionEvaluation]
    consensus: str
    issue_detected: bool
    issue_type: Optional[str]
    severity: Optional[str]
    recommendation: Optional[str]


@dataclass
class QuestioningResult:
    """
    Result of question-based testing.
    
    Contains generated questions, model answers, evaluations, and 
    detected issues ready for integration with interpretation results.
    """
    questions: List[Question] = field(default_factory=list)
    results: List[QuestionResult] = field(default_factory=list)
    statistics: Dict = field(default_factory=dict)
    
    def save(self, output_dir: str):
        """Save questions, answers, and results to separate files."""
        pass
    
    @classmethod
    def load(cls, input_dir: str) -> 'QuestioningResult':
        """Load questioning results from directory."""
        pass
    
    def to_ambiguities(self) -> List['Ambiguity']:
        """Convert detected issues to Ambiguity objects."""
        pass


class QuestioningStep:
    """
    Step 5: Question-based testing of documentation.
    
    Usage:
        step = QuestioningStep(config)
        questions = step.generate_questions(sections, document_text)
        answers = step.collect_answers(questions, models)
        result = step.evaluate(questions, answers, judge_model)
        result.save('output/')
    """
    
    def __init__(self, config: Dict):
        self.config = config
        
    def generate_questions(
        self, 
        sections: List[Dict], 
        document_text: str
    ) -> List[Question]:
        """Generate section-level and document-level questions."""
        pass
    
    def collect_answers(
        self, 
        questions: List[Question], 
        models: List[str]
    ) -> Dict[str, List[QuestionAnswer]]:
        """Query each model with each question."""
        pass
    
    def evaluate(
        self,
        questions: List[Question],
        answers: Dict[str, List[QuestionAnswer]],
        judge_model: str
    ) -> QuestioningResult:
        """Evaluate answers and detect issues."""
        pass
```

#### 6.4.2 New CLI Script: `test_questions.py`

```bash
# Usage examples

# Generate questions only
python test_questions.py generate sections.json document.md --output questions.json

# Run full question testing
python test_questions.py test questions.json --models claude,gemini --judge claude --output results/

# Evaluate existing answers
python test_questions.py evaluate questions.json answers.json --judge claude --output results/

# Generate and test in one command
python test_questions.py auto document.md --models claude,gemini --profile standard
```

#### 6.4.3 Integration with `polish.py`

```python
# In polish.py orchestrator

def run_polishing(document_path, config):
    # Existing steps
    sections = extraction_step.extract(document_path)
    sessions = session_init_step.init(sections, config)
    test_results = testing_step.test(sections, config.models)
    ambiguities = detection_step.detect(test_results)
    
    # NEW: Question-based testing
    if config.enable_question_testing:
        questioning = QuestioningStep(config)
        questions = questioning.generate_questions(sections, document_text)
        answers = questioning.collect_answers(questions, config.models)
        question_results = questioning.evaluate(questions, answers, config.judge)
        
        # Convert to ambiguities and merge
        question_ambiguities = question_results.to_ambiguities()
        all_ambiguities = ambiguities + question_ambiguities
    else:
        all_ambiguities = ambiguities
    
    # Reporting with combined results
    report = reporting_step.generate(all_ambiguities, question_results)
    
    return report
```

---

## 7. Implementation Specification

### 7.1 Question Generation Algorithm

#### 7.1.1 High-Level Algorithm

```
FUNCTION generate_all_questions(document, sections):
    questions = []
    
    # Phase 1: Section-level questions
    FOR section IN sections:
        elements = extract_testable_elements(section)
        section_questions = generate_section_questions(section, elements)
        questions.extend(section_questions)
    
    # Phase 2: Document-level questions
    dependency_graph = build_dependency_graph(sections)
    conflict_pairs = identify_conflict_pairs(sections)
    doc_questions = generate_document_questions(
        dependency_graph, conflict_pairs, document
    )
    questions.extend(doc_questions)
    
    # Phase 3: Adversarial questions
    adversarial = generate_adversarial_questions(sections, document)
    questions.extend(adversarial)
    
    # Phase 4: Validation
    validated = validate_questions(questions, document)
    
    RETURN validated
```

#### 7.1.2 Testable Element Extraction

```
FUNCTION extract_testable_elements(section):
    elements = []
    
    # Pattern matching
    FOR pattern IN element_patterns:
        matches = regex_match(section.content, pattern.regex)
        FOR match IN matches:
            elements.append(Element(
                type=pattern.type,
                text=match.text,
                line=match.line,
                context=match.surrounding_text
            ))
    
    # NLP-based extraction (for complex elements)
    IF section.type == "instruction":
        steps = extract_ordered_steps(section.content)
        conditions = extract_conditions(section.content)
        elements.extend(steps + conditions)
    
    RETURN elements
```

#### 7.1.3 Template Application

```
FUNCTION generate_section_questions(section, elements):
    questions = []
    templates = get_templates_for_section_type(section.type)
    
    FOR element IN elements:
        applicable_templates = filter_templates(templates, element.type)
        
        # Select templates to balance coverage
        selected = select_templates(
            applicable_templates,
            count=min(3, len(applicable_templates)),
            diversity=True
        )
        
        FOR template IN selected:
            question = apply_template(template, element, section)
            IF is_valid(question):
                questions.append(question)
    
    RETURN questions
```

#### 7.1.4 Document-Level Question Generation

```
FUNCTION generate_document_questions(dep_graph, conflicts, document):
    questions = []
    
    # Dependency chain questions
    FOR node IN dep_graph.nodes:
        IF node.has_dependencies:
            q = generate_dependency_question(node, node.dependencies)
            questions.append(q)
    
    # Conflict detection questions
    FOR (stmt_a, stmt_b) IN conflicts:
        q = generate_conflict_question(stmt_a, stmt_b)
        questions.append(q)
    
    # Holistic understanding questions
    workflow = extract_workflow(document)
    summary_q = generate_summary_question(workflow)
    outcome_q = generate_outcomes_question(workflow)
    questions.extend([summary_q, outcome_q])
    
    RETURN questions
```

### 7.2 Answer Evaluation Approach

#### 7.2.1 Evaluation Pipeline

```
FUNCTION evaluate_answers(questions, answers, judge):
    results = []
    
    FOR question IN questions:
        model_evals = {}
        
        FOR model, answer IN answers[question.id].items():
            # Build evaluation prompt
            prompt = build_judge_prompt(
                question=question,
                expected=question.expected_answer,
                actual=answer,
                document_context=get_context(question.target_sections)
            )
            
            # Query judge
            judge_response = judge.query(prompt)
            evaluation = parse_judge_response(judge_response)
            model_evals[model] = evaluation
        
        # Determine consensus
        consensus = calculate_consensus(model_evals)
        issue = detect_issue(question, model_evals, consensus)
        
        results.append(QuestionResult(
            question=question,
            evaluations=model_evals,
            consensus=consensus,
            issue_detected=issue.detected,
            issue_type=issue.type,
            severity=issue.severity,
            recommendation=issue.recommendation
        ))
    
    RETURN results
```

#### 7.2.2 Consensus Calculation

```
FUNCTION calculate_consensus(evaluations):
    scores = [e.score for e in evaluations.values()]
    
    IF all_equal(scores):
        RETURN scores[0]  # unanimous
    ELIF majority_exists(scores):
        RETURN "majority_" + majority_score(scores)
    ELSE:
        RETURN "disagreement"
```

#### 7.2.3 Issue Detection

```
FUNCTION detect_issue(question, evaluations, consensus):
    # Any incorrect answer is an issue
    IF any(e.score == "incorrect" for e in evaluations.values()):
        RETURN Issue(
            detected=True,
            type="incorrect_answer",
            severity=map_severity(question),
            recommendation=generate_recommendation(question, evaluations)
        )
    
    # Disagreement is an issue
    IF consensus == "disagreement":
        RETURN Issue(
            detected=True,
            type="comprehension_disagreement",
            severity="medium",
            recommendation="Clarify section to ensure consistent interpretation"
        )
    
    # Adversarial failure is an issue
    IF question.is_adversarial AND adversarial_failed(question, evaluations):
        RETURN Issue(
            detected=True,
            type=question.adversarial_type + "_failure",
            severity="medium",
            recommendation=adversarial_recommendation(question)
        )
    
    RETURN Issue(detected=False)
```

### 7.3 Workflow Steps

#### 7.3.1 Complete Workflow

```
Step 1: Generate Questions
├── Input: sections.json, document.md
├── Process: Apply templates, LLM generation, validation
├── Output: questions.json
└── Artifacts: questions.json, generation_log.json

Step 2: Collect Answers
├── Input: questions.json, model list
├── Process: Query each model with each question
├── Output: answers.json
└── Artifacts: answers.json, query_log.json

Step 3: Evaluate Answers
├── Input: questions.json, answers.json, judge model
├── Process: LLM-as-Judge evaluation
├── Output: question_results.json
└── Artifacts: question_results.json, evaluation_log.json

Step 4: Aggregate Results
├── Input: question_results.json
├── Process: Calculate statistics, detect issues, map to ambiguities
├── Output: questioning_summary.json
└── Artifacts: questioning_summary.json

Step 5: Integrate with Reporting
├── Input: ambiguities.json, questioning_summary.json
├── Process: Merge results, generate combined report
├── Output: report.md, polished_document.md
└── Artifacts: combined_report.md
```

### 7.4 Data Structures

#### 7.4.1 Question Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "question_id": {
      "type": "string",
      "pattern": "^q_[0-9]{3,}$"
    },
    "question_text": {
      "type": "string",
      "minLength": 10
    },
    "category": {
      "type": "string",
      "enum": ["factual", "procedural", "conditional", "cross_reference", "conflict_detection", "inference", "unanswerable"]
    },
    "difficulty": {
      "type": "string",
      "enum": ["basic", "intermediate", "advanced", "expert"]
    },
    "scope": {
      "type": "string",
      "enum": ["section", "document"]
    },
    "target_sections": {
      "type": "array",
      "items": {"type": "string"},
      "minItems": 1
    },
    "expected_answer": {
      "type": "object",
      "properties": {
        "text": {"type": "string"},
        "source_lines": {
          "type": "array",
          "items": {"type": "integer"}
        },
        "confidence": {
          "type": "string",
          "enum": ["high", "medium", "low"]
        }
      },
      "required": ["text"]
    },
    "generation_method": {
      "type": "string",
      "enum": ["template", "llm", "hybrid"]
    },
    "template_id": {
      "type": ["string", "null"]
    },
    "is_adversarial": {
      "type": "boolean"
    },
    "adversarial_type": {
      "type": ["string", "null"],
      "enum": [null, "trick_question", "edge_case", "contradiction_exploit", "assumption_test", "context_manipulation", "malicious_compliance"]
    },
    "metadata": {
      "type": "object"
    }
  },
  "required": ["question_id", "question_text", "category", "difficulty", "scope", "target_sections", "expected_answer", "generation_method", "is_adversarial"]
}
```

#### 7.4.2 Answer Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "question_id": {"type": "string"},
    "model_name": {"type": "string"},
    "answer_text": {"type": "string"},
    "response_time_ms": {"type": "integer"},
    "raw_response": {"type": "string"},
    "confidence_stated": {"type": ["string", "null"]}
  },
  "required": ["question_id", "model_name", "answer_text", "response_time_ms"]
}
```

#### 7.4.3 Evaluation Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "question_id": {"type": "string"},
    "model_name": {"type": "string"},
    "score": {
      "type": "string",
      "enum": ["correct", "partially_correct", "incorrect", "unanswerable", "hallucinated"]
    },
    "reasoning": {"type": "string"},
    "evidence": {"type": "string"}
  },
  "required": ["question_id", "model_name", "score", "reasoning"]
}
```

#### 7.4.4 Question Result Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "question_id": {"type": "string"},
    "question_text": {"type": "string"},
    "expected_answer": {"type": "string"},
    "model_evaluations": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "score": {"type": "string"},
          "reasoning": {"type": "string"},
          "evidence": {"type": "string"}
        }
      }
    },
    "consensus": {
      "type": "string",
      "enum": ["correct", "partially_correct", "incorrect", "disagreement", "majority_correct", "majority_incorrect"]
    },
    "issue_detected": {"type": "boolean"},
    "issue_type": {"type": ["string", "null"]},
    "severity": {
      "type": ["string", "null"],
      "enum": [null, "critical", "high", "medium", "low"]
    },
    "recommendation": {"type": ["string", "null"]}
  },
  "required": ["question_id", "question_text", "model_evaluations", "consensus", "issue_detected"]
}
```

---

## 8. Success Metrics & Validation

### 8.1 Measuring Effectiveness

#### 8.1.1 Detection Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Issue Detection Rate | Issues found by Q-testing / Total issues in document | ≥ 30% unique (not found by interpretation) |
| False Positive Rate | Incorrectly flagged issues / Total flagged | ≤ 15% |
| Coverage Completeness | Sections with questions / Total sections | ≥ 95% |
| Adversarial Pass Rate | Passed adversarial tests / Total adversarial | ≥ 70% |

#### 8.1.2 Quality Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Question Validity | Valid questions / Generated questions | ≥ 95% |
| Answer Agreement | Unanimous correct / Total questions | ≥ 80% |
| Judge Consistency | Same judge result on retry / Total | ≥ 90% |

### 8.2 Successful Detection Criteria

#### 8.2.1 What Constitutes Successful Ambiguity Detection?

A question-based test successfully detects an ambiguity when:

1. **Interpretation difference manifests**: Models give different answers
2. **Answer is verifiably incorrect**: At least one model's answer contradicts document
3. **Conflict is revealed**: Document-level question exposes cross-section inconsistency
4. **Adversarial probe fails**: Model accepts false premise or misses trick

#### 8.2.2 Detection Quality Indicators

| Indicator | Meaning |
|-----------|---------|
| High disagreement rate (>20%) | Document has significant ambiguity |
| Low adversarial pass rate (<60%) | Document has robustness issues |
| Multiple conflict detections | Document has internal inconsistencies |
| Consistent partial_correct | Document is underspecified |

### 8.3 Validation Approach

#### 8.3.1 Ground Truth Validation

1. **Expert Annotation**: Have documentation experts annotate known ambiguities in test documents
2. **Detection Comparison**: Compare Q-testing detections with expert annotations
3. **Metrics**:
   - Precision = True positives / (True positives + False positives)
   - Recall = True positives / (True positives + False negatives)
   - F1 = 2 × (Precision × Recall) / (Precision + Recall)

**Target**: F1 ≥ 0.70 for ambiguity detection

#### 8.3.2 A/B Testing

1. **Control**: Interpretation-only testing
2. **Treatment**: Interpretation + Question testing
3. **Measure**: 
   - Additional ambiguities found
   - Ambiguity severity distribution
   - Fix generation quality

#### 8.3.3 User Study Validation

1. **Participants**: Documentation authors and consumers
2. **Task**: Rate quality of detected issues
3. **Metrics**:
   - Usefulness rating (1-5)
   - Would-fix rate (% of issues users would address)
   - False positive identification

### 8.4 Continuous Improvement

#### 8.4.1 Feedback Loop

```
Questions → Answers → Evaluations → Issues → Fixes → Improved Document
     ↑                                                      |
     └──────────────── Learning from fixes ←────────────────┘
```

#### 8.4.2 Template Refinement

Track which templates produce:
- Highest issue detection rate
- Lowest false positive rate
- Most actionable recommendations

Prune ineffective templates, expand effective ones.

#### 8.4.3 Adversarial Evolution

As documents improve, adversarial tests should evolve:
1. Retire tests that always pass (no longer challenging)
2. Add new tests for emerging patterns
3. Increase difficulty for mature documents

---

## Appendix A: Question Templates Library

### A.1 Factual Templates

```yaml
factual_templates:
  - id: factual_format_01
    pattern: "What [format/structure/type] should [element] use?"
    triggers: ["format", "structure", "type", "encoding"]
    scope: section
    difficulty: basic
    
  - id: factual_value_01
    pattern: "What is the [default/configured/required] value for [parameter]?"
    triggers: ["default", "value", "parameter", "setting"]
    scope: section
    difficulty: basic
    
  - id: factual_location_01
    pattern: "Where should [element] be [placed/stored/defined]?"
    triggers: ["location", "path", "directory", "file"]
    scope: section
    difficulty: basic
```

### A.2 Procedural Templates

```yaml
procedural_templates:
  - id: procedural_order_01
    pattern: "What is the [first/next/last] step in [process]?"
    triggers: ["step", "process", "workflow", "procedure"]
    scope: section
    difficulty: basic
    
  - id: procedural_prereq_01
    pattern: "What must be completed before [step/action]?"
    triggers: ["before", "prerequisite", "requires", "after"]
    scope: document
    difficulty: intermediate
    
  - id: procedural_sequence_01
    pattern: "In what order should [steps/actions] be performed?"
    triggers: ["order", "sequence", "first", "then"]
    scope: section
    difficulty: intermediate
```

### A.3 Conditional Templates

```yaml
conditional_templates:
  - id: conditional_if_01
    pattern: "What happens when [condition]?"
    triggers: ["if", "when", "unless", "condition"]
    scope: section
    difficulty: intermediate
    
  - id: conditional_else_01
    pattern: "What is the alternative if [condition] is not met?"
    triggers: ["else", "otherwise", "alternative", "default"]
    scope: section
    difficulty: intermediate
    
  - id: conditional_error_01
    pattern: "What error occurs when [invalid_condition]?"
    triggers: ["error", "exception", "fail", "invalid"]
    scope: section
    difficulty: advanced
```

### A.4 Document-Level Templates

```yaml
document_templates:
  - id: doc_dependency_01
    pattern: "Can [section_B] execute without completing [section_A]?"
    triggers: ["output", "input", "requires", "uses"]
    scope: document
    difficulty: advanced
    
  - id: doc_conflict_01
    pattern: "How should [requirement_A] be interpreted given [requirement_B]?"
    triggers: ["conflict", "contradiction", "inconsistent"]
    scope: document
    difficulty: expert
    
  - id: doc_summary_01
    pattern: "What are the [N] main steps in the complete [workflow]?"
    triggers: ["workflow", "process", "procedure"]
    scope: document
    difficulty: intermediate
```

---

## Appendix B: Adversarial Test Patterns

### B.1 Trick Question Patterns

```yaml
trick_patterns:
  - id: trick_negation_01
    name: "Negation Confusion"
    description: "Ask about exceptions when none exist"
    template: "Which [items] are NOT required to [action]?"
    condition: "All items are required"
    expected_behavior: "Recognize no exceptions exist"
    
  - id: trick_quantity_01
    name: "Quantity Distortion"
    description: "Reference non-existent items"
    template: "What happens in step [N+1]?" 
    condition: "Only N steps exist"
    expected_behavior: "Recognize step doesn't exist"
```

### B.2 Edge Case Patterns

```yaml
edge_case_patterns:
  - id: edge_empty_01
    name: "Empty Input"
    template: "What happens if [collection] is empty?"
    condition: "Document doesn't specify empty handling"
    expected_behavior: "Acknowledge unspecified or infer reasonably"
    
  - id: edge_max_01
    name: "Maximum Limit"
    template: "What if there are [very_large_number] [items]?"
    condition: "No explicit limit stated"
    expected_behavior: "Acknowledge no limit specified"
```

### B.3 Contradiction Exploit Patterns

```yaml
contradiction_patterns:
  - id: contra_validate_01
    name: "Validation Conflict"
    template: "Should [field_type] fields be validated given both 'validate all' and 'skip [field_type]' instructions?"
    condition: "Both instructions present in different sections"
    expected_behavior: "Identify the conflict"
```

---

## Appendix C: Evaluation Prompt Templates

### C.1 Standard Evaluation Prompt

```
You are evaluating whether a model correctly answered a question about documentation.

## Context
{document_excerpt}

## Question
{question}

## Expected Answer
{expected_answer}

## Model's Answer
{model_answer}

## Evaluate on these criteria:
1. Correctness: Does the answer match the document?
2. Completeness: Does it address the full question?
3. Accuracy: Does it avoid adding unsupported claims?

## Respond with:
{
  "score": "correct|partially_correct|incorrect|unanswerable",
  "reasoning": "<your analysis>",
  "evidence": "<relevant quote from document>"
}
```

### C.2 Adversarial Evaluation Prompt

```
You are evaluating whether a model correctly handled an adversarial question.

## Adversarial Type: {adversarial_type}

## Context
{document_excerpt}

## Adversarial Question
{question}

## What Makes This Adversarial
{adversarial_description}

## Expected Correct Behavior
{expected_behavior}

## Model's Response
{model_answer}

## Evaluate:
Did the model correctly handle the adversarial element?

{
  "passed": true|false,
  "reasoning": "<analysis of how model handled the adversarial element>",
  "failure_mode": "<if failed, what went wrong>"
}
```

---

## Appendix D: Implementation Checklist

### D.1 Phase 1: Core Infrastructure
- [ ] Question data structures (Question, Answer, Evaluation)
- [ ] Template library (factual, procedural, conditional)
- [ ] Question generation algorithm
- [ ] questions.json artifact format

### D.2 Phase 2: Question Generation
- [ ] Section-level question generator
- [ ] Document-level question generator
- [ ] Template application logic
- [ ] LLM-based question generation
- [ ] Question validation

### D.3 Phase 3: Answer Collection
- [ ] Model querying infrastructure
- [ ] answers.json artifact format
- [ ] Session management integration
- [ ] Error handling for timeouts

### D.4 Phase 4: Evaluation
- [ ] LLM-as-Judge prompts
- [ ] Evaluation parsing
- [ ] Consensus calculation
- [ ] Issue detection logic
- [ ] question_results.json artifact

### D.5 Phase 5: Adversarial Testing
- [ ] Adversarial templates
- [ ] Adversarial generation patterns
- [ ] Adversarial evaluation criteria
- [ ] Pass/fail determination

### D.6 Phase 6: Integration
- [ ] QuestioningStep module
- [ ] CLI script (test_questions.py)
- [ ] polish.py integration
- [ ] Combined reporting

### D.7 Phase 7: Validation
- [ ] Unit tests for all components
- [ ] Integration tests
- [ ] Validation against known ambiguities
- [ ] Performance benchmarking

---

**Document Version History:**
- v1.0 (December 2025): Initial comprehensive design based on industry research

**References:**
1. Dhuliawala et al. (2023). "Chain-of-Verification Reduces Hallucination in Large Language Models." ACL Anthology.
2. Hyun et al. (2023). "METAL: Metamorphic Testing Framework for Analyzing Large-Language Model Qualities." arXiv:2312.06056.
3. Rajpurkar et al. (2016). "SQuAD: 100,000+ Questions for Machine Comprehension of Text." EMNLP.
4. Giskard Documentation. "RAG Evaluation Toolkit (RAGET)."
5. Microsoft Azure. "Planning Red Teaming for Large Language Models."
6. DeepEval Documentation. "LLM Evaluation Framework."
7. Confident AI. "What is LLM Red Teaming?"
