# Expert Review: Question-Based Testing Framework (Claude Response)

**Model:** Claude 4.5 opus
**Date:** [date]
**Prompt:** EXPERT_REVIEW_PROMPT.md

---

# Expert Review: Question-Based Testing Framework

**Document:** Question-Based Testing Framework for LLM Documentation Evaluation  
**Implementation Status:** Phases 3-5 implemented, templates broken  
**Review Date:** December 29, 2025

---

## Educational Assessment Specialist

### ✅ Strengths

- **Sound taxonomic foundation**: The question taxonomy (factual, procedural, conditional, cross-reference, conflict detection, inference, unanswerable) maps well to Bloom's revised taxonomy levels. This structured approach ensures systematic coverage of comprehension dimensions.

- **Difficulty stratification**: The four-level difficulty progression (basic → intermediate → advanced → expert) with clear definitions and target distributions (40/35/20/5%) reflects established item difficulty calibration practices from standardized testing.

- **Inclusion of unanswerable questions**: Adding questions where documentation genuinely lacks information (SQuAD 2.0 style) is a sophisticated assessment practice that tests meta-cognitive awareness—do models know what they don't know?

- **Multi-scope approach**: Testing at both section-level (granular comprehension) and document-level (holistic understanding) mirrors how reading comprehension assessments test both literal comprehension and text integration skills.

### ⚠️ Concerns

- **Answer leakage in templates is a fundamental item construction flaw**: The identified issue—"Does the documentation mention {element_text}?" yielding answer "{element_text}"—violates a core principle of item writing. When the answer appears in the question stem, you're testing recognition memory, not comprehension. This renders the entire template set invalid.

- **Binary evaluation masks partial understanding**: The current scoring (correct/partially_correct/incorrect/unanswerable) conflates comprehension depth with accuracy. A model might understand the concept but express it imprecisely. Professional assessments distinguish between conceptual errors (misunderstanding) and expression errors (correct understanding, poor articulation).

- **No distractor analysis**: Unlike multiple-choice assessment, free-response evaluation through LLM-as-Judge doesn't systematically analyze *types* of wrong answers. In educational measurement, wrong answer patterns reveal what misconceptions exist—crucial for improving documentation.

- **Coverage metrics may create perverse incentives**: Targeting "70% sections, 60% elements" could encourage generating low-quality questions just to hit quotas. Educational testing prioritizes item quality (discrimination power, reliability) over quantity.

- **No reliability coefficient**: There's no mechanism to measure whether the same question produces consistent results across repeated testing. Test-retest reliability is fundamental to meaningful measurement.

### 💡 Recommendations

1. **Redesign templates using "indirect reference" pattern**
   - Why: Current templates ask directly about content, causing leakage. Professional reading tests ask questions that *require* knowing the content to answer, without stating it.
   - How: Transform `"Does the documentation mention {element}?"` to `"What value does the documentation specify for [category of element]?"`. Example: Instead of "Does it mention 'timeout defaults to 30 seconds'?", ask "What is the default timeout value?"
   - Priority: **Critical** (blocks all validation)

2. **Add response coding scheme for wrong answers**
   - Why: Wrong answers reveal documentation problems. If 3 models all give the *same* wrong answer, that's a documentation clarity issue. If they give *different* wrong answers, that's an ambiguity issue.
   - How: Extend AnswerEvaluator to categorize incorrect responses: {hallucination, misinterpretation, incomplete, contradicts_source, out_of_scope}. Track error type distributions per section.
   - Priority: High

3. **Implement item discrimination analysis**
   - Why: Not all questions are equally useful. Some questions all models answer correctly (too easy = useless). Some all answer wrong (too hard OR bad question). You want questions where model performance varies meaningfully.
   - How: Calculate discrimination index: (high_performer_correct_rate - low_performer_correct_rate). Remove or revise items with discrimination < 0.3.
   - Priority: Medium

4. **Replace coverage quotas with quality-weighted coverage**
   - Why: 10 excellent questions beat 50 trivial ones. Current metrics incentivize quantity.
   - How: Weight coverage by question difficulty and discrimination. A section with 2 high-discrimination advanced questions counts more than one with 5 basic questions all models ace.
   - Priority: Medium

5. **Add inter-rater reliability for LLM-as-Judge**
   - Why: If the judge model is inconsistent, your entire evaluation is unreliable.
   - How: Have the judge evaluate the same answer twice (different sessions) and calculate Cohen's kappa. Target κ > 0.8. If lower, your judge prompts need refinement.
   - Priority: High

---

## Technical Communication Researcher

### ✅ Strengths

- **Focus on procedural comprehension**: The emphasis on testing "can models correctly USE understanding" addresses a real gap. Much technical documentation fails not because content is wrong, but because users can't successfully execute procedures from it.

- **Cross-reference and conflict detection**: These document-level question types target exactly the problems technical writers struggle with—inconsistencies between sections, unclear dependencies, contradictory requirements. These are documentation bugs, not just ambiguities.

- **Element type taxonomy aligns with technical writing concerns**: The extracted elements (steps, requirements, conditionals, outputs, inputs, constraints, defaults, exceptions) represent the structural components technical writers consciously craft. Testing comprehension of these validates whether the writer's intent transmitted.

- **Adversarial testing for edge cases**: Testing "What if the input is empty?" and "What happens beyond stated limits?" targets the implicit assumptions writers make but don't document—a major source of user confusion.

### ⚠️ Concerns

- **Model comprehension ≠ Human comprehension**: The fundamental validity question remains unaddressed. LLMs process text differently than humans. A passage that confuses Claude but not humans (or vice versa) yields misleading quality signals. Without human validation, you're optimizing for LLM readability, not user readability.

- **No task performance validation**: Testing if a model can *answer questions* about documentation doesn't prove it can *follow* the documentation. Reading comprehension and task execution are different cognitive processes. A model might answer "What's the first step?" correctly but still fail to execute Step 1.

- **Missing audience calibration**: Technical documentation has different audiences (novice vs. expert users). A section might be perfectly clear to experts but confusing to novices. The framework doesn't account for audience-specific comprehension requirements.

- **Over-reliance on explicit content**: Template-based questions primarily test explicit information recall. Much technical documentation fails because of what's *implicit* or *assumed*—prerequisites, environmental context, user skill level. The framework may miss these gaps.

- **No usability metric integration**: Technical communication research uses established metrics (readability scores, Cloze test scores, task completion rates). This framework exists in isolation without connecting to proven documentation quality measures.

### 💡 Recommendations

1. **Add human validation benchmark**
   - Why: Without human ground truth, you can't claim this finds "real" documentation problems. You might be optimizing for LLM quirks.
   - How: Create a gold-standard set of 50-100 questions with human-validated answers. Run human users through the same questions. Calculate correlation between model performance and human performance per documentation section.
   - Priority: **High** (fundamental validity)

2. **Implement task-based validation questions**
   - Why: Answering "What's the timeout?" is different from successfully configuring a timeout. Task-oriented questions better simulate real use.
   - How: Add "application" question type: "Given [scenario], what sequence of actions should you perform?" "What would be the output if you provided [input]?" These test applied understanding, not just recall.
   - Priority: High

3. **Add audience personas to question generation**
   - Why: Documentation clarity is audience-relative. A novice needs different explanation than an expert.
   - How: Tag questions with intended audience level. For critical sections, generate questions at multiple levels: "What is Step 3?" (novice) vs. "What edge cases aren't addressed in Step 3?" (expert).
   - Priority: Medium

4. **Integrate implicit knowledge detection**
   - Why: Many documentation failures are omissions—assumed context never stated.
   - How: Add "context probe" questions: "What prerequisites does this section assume?" "What prior knowledge is required to follow Step 2?" If models give inconsistent answers, the implicit context is under-specified.
   - Priority: Medium

5. **Connect to established readability metrics**
   - Why: This framework should complement, not replace, existing documentation quality tools.
   - How: Correlate question-based ambiguity detection with Flesch-Kincaid, Gunning Fog, and automated readability indices. Identify whether this approach finds issues those metrics miss (and vice versa).
   - Priority: Low

---

## NLP/LLM Evaluation Researcher

### ✅ Strengths

- **Principled evaluation design**: The framework draws appropriately from established benchmarks (SQuAD, RAGET) and evaluation methodologies (LLM-as-Judge, Chain-of-Verification). This isn't reinventing the wheel—it's applying proven techniques to a novel domain.

- **Multi-model consensus as signal**: Using agreement/disagreement across multiple models to detect ambiguity is clever. If Claude, GPT-4, and Gemini all interpret a passage differently, that's strong evidence of genuine ambiguity (not just one model's quirk).

- **Separation of question generation from evaluation**: The pipeline architecture (generate → collect → evaluate → consensus) enables systematic ablation studies. You can swap evaluation methods, add models, or change question generation independently.

- **Adversarial category design**: The adversarial taxonomy (trick questions, edge cases, false premises, contradiction exploits) is well-grounded in LLM red-teaming literature. Testing whether models "fall for" these patterns reveals documentation vulnerabilities.

### ⚠️ Concerns

- **Template-based generation severely limits diversity**: Pure template-based question generation produces formulaic questions that may miss natural comprehension challenges. All "What is the default value of {X}?" questions test the same thing. Real ambiguity might exist in complex conditional structures templates can't capture.

- **LLM-as-Judge has known failure modes**: Judge models exhibit systematic biases (preference for longer answers, own-model preference, position bias). Using Claude to judge Claude and GPT answers introduces measurement confounds. The judge might consistently favor Claude-style responses.

- **No calibration against known ambiguities**: The framework has no ground truth. How do you know detected "issues" are real ambiguities? Without a validation set of documents with known ambiguities, precision/recall are unmeasurable.

- **Model consensus may reflect shared training biases**: If all models were trained on similar data, they might share the same misunderstandings. Three models confidently giving the same wrong answer doesn't mean the documentation is clear—it might mean all models have the same blind spot.

- **Answer extraction relies on brittle JSON parsing**: The implementation shows response parsing that expects specific JSON structures. LLMs frequently deviate from requested formats, especially under unusual prompts. High parse failure rates would silently reduce evaluation coverage.

### 💡 Recommendations

1. **Implement hybrid question generation (templates + LLM)**
   - Why: Templates provide consistency and control; LLM generation provides diversity and naturalism. Neither alone is sufficient.
   - How: Use templates for structural questions (defaults, steps, requirements). Use LLM generation for reasoning questions (implications, edge cases, conflicts). Target 40% template / 60% LLM-generated.
   - Priority: **High**

2. **Add judge calibration and cross-validation**
   - Why: LLM-as-Judge reliability is crucial to the entire framework's validity.
   - How: (1) Use multiple judge models and require consensus. (2) Include "canary" questions with known correct/incorrect answers to measure judge accuracy. (3) Randomize answer presentation order to detect position bias. (4) Calculate inter-judge agreement (κ > 0.7 required).
   - Priority: **High**

3. **Create gold-standard validation corpus**
   - Why: Without ground truth, you can't measure whether this works.
   - How: Manually annotate 10-20 documentation samples with known ambiguities. Create questions that should detect these ambiguities. Measure detection rate (recall) and false positive rate (precision). Target: >80% recall, >70% precision.
   - Priority: **High**

4. **Add model diversity analysis**
   - Why: Consensus among similar models isn't meaningful. You need genuinely different perspectives.
   - How: Include models with different architectures/training (e.g., Claude, GPT, Gemini, Llama, Mistral). Calculate inter-model correlation. If correlation > 0.9, models aren't providing independent signals—add more diverse models.
   - Priority: Medium

5. **Implement robust response parsing with fallbacks**
   - Why: Brittle parsing causes silent failures. The implementation already shows this is a concern.
   - How: (1) Allow multiple response formats (JSON, structured text, free text). (2) Use extraction prompts if initial parse fails: "Extract just the answer from: {response}". (3) Track parse failure rate per model and question type. (4) Flag questions with high parse failure for template revision.
   - Priority: Medium

---

## Cognitive Psychologist

### ✅ Strengths

- **Tests multiple comprehension levels**: The taxonomy implicitly maps to comprehension theory. Factual questions test surface code (explicit text). Procedural questions test textbase (integrated propositions). Cross-reference questions test situation model (coherent mental representation of the described system).

- **Adversarial testing probes inference processes**: Questions with false premises or unstated edge cases test whether models (like humans) build accurate situation models rather than just surface-level text representations. Falling for tricks suggests shallow processing.

- **Document-level questions require text integration**: Asking about conflicts between Section 2 and Section 5 requires building a coherent representation of the entire document. This tests the kind of global coherence that determines whether users can actually use documentation.

- **Unanswerable questions test metacognition**: Recognizing "the documentation doesn't say" requires monitoring your own knowledge state—a sophisticated metacognitive process. This distinguishes genuine comprehension from confident hallucination.

### ⚠️ Concerns

- **No distinction between comprehension and memory**: Current questions might be answerable through shallow pattern matching ("the documentation says X near where I saw Y") without genuine understanding. A model might correctly answer "What's the timeout?" by retrieving the sentence with "timeout" without understanding what timeouts do or why this value matters.

- **Missing inference depth stratification**: The framework doesn't distinguish near-inference (combining adjacent sentences) from far-inference (integrating distant information) from elaborative inference (applying world knowledge). These require different cognitive processes and reveal different comprehension issues.

- **No coherence break detection**: Comprehension research shows readers detect coherence breaks (logical gaps, topic shifts, contradictions). The framework doesn't explicitly test whether models notice when documentation stops making sense—a crucial reader skill.

- **Ignores situation model accuracy**: You can answer questions correctly from a flawed mental model if the questions don't probe the flawed parts. A model might understand individual steps but misunderstand how they connect into a workflow.

- **No processing depth manipulation**: Cognitive research uses techniques like priming, interference, and delayed recall to probe processing depth. The framework tests immediate comprehension only, missing whether understanding persists or was superficial.

### 💡 Recommendations

1. **Add paraphrase/transfer questions to test deep comprehension**
   - Why: Surface comprehension allows answering in original terms. Deep comprehension allows answering in novel terms.
   - How: For key concepts, generate questions using different vocabulary than the source. "The documentation specifies a 30-second timeout" → "How long will the system wait before giving up?" If models fail paraphrased versions while passing literal ones, comprehension is shallow.
   - Priority: **High**

2. **Implement inference chain questions**
   - Why: Multi-step inference reveals whether models build integrated representations.
   - How: Generate questions requiring 2-3 inference steps: "Step 3 produces X. Step 7 requires Y. If X differs from Y, what happens?" Track failure rate by inference depth. Higher failure at deeper levels suggests fragile situation models.
   - Priority: High

3. **Add coherence monitoring probes**
   - Why: Good readers notice when text stops making sense. LLMs often don't.
   - How: Introduce questions like "Is there any logical gap between Section 3 and Section 4?" "Does the transition from configuration to execution make sense?" Correct detection of coherence breaks (or lack thereof) indicates deep processing.
   - Priority: Medium

4. **Test situation model through scenario application**
   - Why: Accurate mental models allow applying knowledge to novel situations.
   - How: Add "scenario" questions: "A user tries [novel action not in docs]. Based on the documented system behavior, what would happen?" Correct answers require simulating the documented system—impossible without an accurate situation model.
   - Priority: Medium

5. **Add delayed testing option**
   - Why: Immediate correct answers might reflect temporary activation, not durable understanding.
   - How: For critical sections, test twice: immediately and after processing intervening content. Significant performance drop suggests superficial initial processing. (Note: This is complex with LLMs since "forgetting" works differently than with humans.)
   - Priority: Low

---

## Software Architect

### ✅ Strengths

- **Clean separation of concerns**: The 5-class architecture (CrossReferenceAnalyzer, ConflictDetector, AnswerCollector, AnswerEvaluator, ConsensusCalculator) follows single-responsibility principle well. Each class has a clear purpose and can be tested/modified independently.

- **Pipeline architecture enables flexibility**: The sequential flow (Sections → Questions → Answers → Evaluations → Consensus → Issues) allows inserting new stages, swapping implementations, or adding parallel paths without restructuring.

- **Artifact-based data flow**: Using JSON artifacts (questions.json, answers.json, question_results.json) between stages enables debugging, caching, and resumption. You can inspect intermediate outputs and re-run stages independently.

- **Session management integration**: Properly managing LLM sessions (initializing with document context, reusing across questions) shows good understanding of the LLM integration requirements.

- **Dataclass usage for type safety**: Using dataclasses (Question, QuestionAnswer, QuestionEvaluation, QuestionResult) provides structure and IDE support, reducing stringly-typed errors.

### ⚠️ Concerns

- **2000+ line monolithic file**: Cramming all Phase 1-5 classes into a single `questioning_step.py` file violates modularity principles. This makes navigation difficult, testing harder, and merge conflicts more likely.

- **Inconsistent data model (header vs. title)**: The KeyError bugs from `section['header']` vs `section.get('title')` reveal unstable data contracts. The section dict structure isn't documented or enforced, leading to defensive coding patterns throughout.

- **Fragile regex patterns for semantic extraction**: Using regex to detect cross-references (`See Section X`) and conflicts (`must` vs `must not`) is brittle. Natural language variation will defeat these patterns. Consider: "Refer to section three", "required but not mandatory", "should always but might sometimes".

- **No error recovery strategy**: When AnswerCollector fails on one model, what happens? When JSON parsing fails, what happens? The code has try/except but no coherent strategy for partial failures.

- **Template system couples data and logic**: Templates are JSON data, but template application logic is hardcoded. Adding a new template type requires code changes, not just data updates.

- **Zero tests for critical paths**: 0% test coverage for Phases 3-5 means no confidence in correctness. The KeyError bugs that were found prove this concern is valid.

### 💡 Recommendations

1. **Split into separate modules**
   - Why: 2000+ lines is unmaintainable. Each phase should be importable independently.
   - How: Create module structure:
     ```
     questioning/
       __init__.py
       models.py          # Dataclasses
       extraction.py      # ElementExtractor, TemplateLoader
       generation.py      # QuestionGenerator, TemplateApplicator
       analysis.py        # CrossReferenceAnalyzer, ConflictDetector
       collection.py      # AnswerCollector
       evaluation.py      # AnswerEvaluator, ConsensusCalculator
       step.py           # QuestioningStep (orchestrator)
     ```
   - Priority: **High**

2. **Define explicit section schema with validation**
   - Why: The header/title confusion shows the section data model is undefined. This will cause more bugs.
   - How: Create a `Section` dataclass with explicit required/optional fields. Add validation on input. Convert all `section['field']` access to typed attribute access.
   - Priority: **High**

3. **Replace regex with configurable pattern system**
   - Why: Hardcoded regex is brittle and hard to extend.
   - How: Define patterns as configuration (YAML/JSON) with categories (cross_reference, conflict, element). Support multiple patterns per category. Allow easy addition of new patterns without code changes. Consider using spaCy for dependency parsing on high-value patterns.
   - Priority: Medium

4. **Implement graceful degradation strategy**
   - Why: Partial failures shouldn't crash the pipeline. Some results are better than none.
   - How: Define failure modes and fallbacks:
     - Model timeout → Skip model, continue with others
     - Parse failure → Store raw response, mark as unparsed
     - Validation failure → Log, skip question, continue
     - Include failure counts in final output for visibility.
   - Priority: Medium

5. **Add comprehensive Phase 3-5 tests**
   - Why: Zero tests is unacceptable for production code. The bugs found prove testing is needed.
   - How: Target 80% coverage. Write tests for:
     - CrossReferenceAnalyzer: explicit refs, implicit refs, cycles, orphans
     - ConflictDetector: contradictions, value conflicts, no-conflict case
     - AnswerCollector: success, timeout, parse failure
     - AnswerEvaluator: all score types, malformed responses
     - ConsensusCalculator: agreement, disagreement, failure modes
   - Priority: **Critical** (blocks production)

6. **Make template system extensible**
   - Why: New question types shouldn't require code changes.
   - How: Templates should declare their own application logic (what inputs they need, how to format output). Use template "plugins" that register capabilities. The core system routes to appropriate handler based on template metadata.
   - Priority: Low

---

## Final Synthesis

### Overall Assessment

**Is this approach fundamentally sound?**

Yes. The core insight—that asking comprehension questions can reveal documentation problems that interpretation testing misses—is valid and well-supported by research in reading comprehension, LLM evaluation, and technical communication. The dual-level (section/document) design and adversarial testing components add meaningful value.

However, the implementation has a critical flaw that renders it currently unusable: the template-based question generation creates answer leakage, causing 100% validation failure. Additionally, the absence of any validation against ground truth means we don't know if the approach actually works, even if the template issue is fixed.

**What are the biggest risks?**

1. **Template design is fundamentally broken** (Critical): Current templates cannot generate valid questions. This isn't a bug—it's a design flaw requiring rethinking how questions are constructed.

2. **No ground truth validation** (High): Without a corpus of documents with known ambiguities, there's no way to measure precision/recall. The framework might detect "issues" that aren't real problems.

3. **LLM-as-Judge reliability unknown** (High): The entire evaluation depends on the judge model's accuracy, but there's no calibration or cross-validation.

4. **Model consensus may be meaningless** (Medium): If models share training biases, consensus doesn't indicate clarity—it indicates shared blind spots.

5. **Zero tests for critical code paths** (High): The Phase 3-5 implementation has 0% test coverage, despite being ~1100 lines of code.

**What are the highest-value improvements?**

1. **Fix template design** (enables any testing at all)
2. **Add gold-standard validation corpus** (proves the approach works)
3. **Add judge calibration** (ensures evaluation is reliable)
4. **Add comprehensive tests** (prevents regressions)
5. **Add hybrid LLM question generation** (improves question diversity)

### Priority Recommendations

#### Top 3 Changes Before Production

1. **Redesign question templates to eliminate answer leakage**
   - Transform from: `"Does the documentation mention {element_text}?"`
   - To: `"What value is specified for [element category]?"`
   - This is blocking all progress—nothing works until templates generate valid questions.

2. **Create gold-standard test corpus**
   - Select 10-20 documentation samples
   - Manually annotate known ambiguities
   - Create questions that should detect these
   - Measure detection rate
   - Target: >80% recall, >70% precision before production

3. **Add Phase 3-5 test coverage**
   - Write minimum 25 tests covering:
     - CrossReferenceAnalyzer (5 tests)
     - ConflictDetector (5 tests)
     - AnswerCollector (5 tests)
     - AnswerEvaluator (5 tests)
     - ConsensusCalculator (5 tests)
   - Target: >80% coverage for new code

#### Top 3 Research Questions to Answer

1. **Does model comprehension failure predict human comprehension failure?**
   - Run human subjects through same questions
   - Calculate correlation between model and human difficulty
   - If low correlation, this approach may be optimizing for wrong target

2. **What question types reveal the most actionable documentation issues?**
   - Track which question categories lead to documentation improvements
   - Some issues detected might be trivial or unfixable
   - Prioritize question types that find high-value issues

3. **How does model diversity affect ambiguity detection?**
   - Test with 3 models vs. 5 models vs. 7 models
   - Test with similar models (all GPT variants) vs. diverse models
   - Find optimal model selection for reliable detection

### Alternative Approaches

**Are there simpler ways to achieve the same goal?**

Yes, but with trade-offs:

1. **Pure LLM question generation (no templates)**
   - Simpler implementation, higher diversity
   - Risk: Less consistent, harder to control coverage
   - Verdict: Worth exploring as complement, not replacement

2. **Single-model interpretation with self-consistency**
   - Ask same model same question multiple times
   - Inconsistent answers suggest ambiguity
   - Simpler than multi-model, but weaker signal

3. **Readability metrics + manual review**
   - Use Flesch-Kincaid, etc. to flag complex sections
   - Human reviewers focus on flagged sections
   - Well-understood approach, but doesn't scale

**What hybrid approaches might work better?**

1. **Template + LLM generation pipeline**
   - Use templates for structural questions (60%)
   - Use LLM for reasoning/inference questions (40%)
   - Combines consistency with diversity

2. **Staged validation**
   - Stage 1: Automated question testing (catches obvious issues)
   - Stage 2: Human validation of flagged issues (confirms real problems)
   - Reduces human burden while ensuring accuracy

3. **Active learning loop**
   - Start with broad question generation
   - Track which questions lead to actual doc fixes
   - Prioritize generating similar questions
   - Continuously improves question quality over time

---

## Appendix: Template Redesign Recommendations

The current broken template pattern:
```
Q: "Does the documentation mention '{element_text}'?"
A: "{element_text}"
→ FAILS: Answer appears in question
```

Recommended redesign patterns:

### Factual Questions

**Current (broken):**
```json
{
  "template_id": "existence_mention_01",
  "question_pattern": "Does the documentation mention {element_text}?",
  "answer_extraction": {"keywords": []}
}
```

**Recommended:**
```json
{
  "template_id": "factual_value_01",
  "question_pattern": "What {element_category} does the documentation specify?",
  "element_category_map": {
    "defaults": "default value",
    "constraints": "limit or constraint",
    "requirements": "requirement"
  },
  "answer_extraction": {"source": "element_value"}
}
```

Example transformation:
- Element: "timeout defaults to 30 seconds"
- Old Q: "Does the documentation mention 'timeout defaults to 30 seconds'?"
- New Q: "What default value does the documentation specify for timeout?"
- A: "30 seconds"

### Procedural Questions

**Recommended:**
```json
{
  "template_id": "procedural_step_01",
  "question_pattern": "What action is performed in Step {step_number}?",
  "answer_extraction": {"source": "step_action_text"}
}
```

### Conditional Questions

**Recommended:**
```json
{
  "template_id": "conditional_outcome_01",
  "question_pattern": "What happens when {condition_trigger} occurs?",
  "answer_extraction": {"source": "condition_outcome"}
}
```

The key principle: **Ask about categories or effects, not about specific text.** The question should require knowledge of the content to answer, without stating that content.
