# Related Tools — Document Polishing Ecosystem

Tools in the documentation quality and prompt optimization space. Relevant for potential integration or inspiration.

---

## DSPy (Most Relevant — Potential Integration)

**What it is:** Programming framework for optimizing LLM prompts and pipelines algorithmically.

**Origin:** Stanford NLP Group (widely used with Google models, referenced as "the Google one")

**How it works:**
- You define a "signature" (what you want in, what you want out — e.g., "document → ambiguities")
- DSPy *compiles* your pipeline by running optimization loops against a metric
- Each loop tests how close the current prompt gets to target measurements
- Outputs an optimized prompt that demonstrably achieves the target

**Reference video:** https://www.youtube.com/watch?v=6Q76EnHVRms

**Key difference from our tool:**
- DSPy optimizes prompts *to produce correct outputs*
- Our tool checks documents for *ambiguity in interpretation*
- Related problem space, different angle — DSPy is about the prompt, we're about the document

**Integration potential:**
1. Use DSPy to auto-optimize the judge prompt (currently hand-crafted in `ambiguity_detector.py`)
2. Use DSPy to optimize the model query prompts in `prompt_generator.py`
3. Could auto-tune what "good document" looks like by compiling against examples

**Install:** `pip install dspy-ai`

**Docs:** https://dspy.ai

---

## OPRO — Optimization by PROmpting (Research Reference)

**What it is:** Google DeepMind research (2023) on using LLMs to optimize prompts iteratively.

**How it works:** LLM generates prompt variants, measures against accuracy metrics, iterates toward better prompts.

**Relation to us:** Same principle as DSPy but research paper form, not a library. DSPy is the practical implementation of this idea.

**Paper:** https://arxiv.org/abs/2309.03409

---

## Promptfoo (Closest Existing Tool)

**What it is:** Open-source framework for testing and evaluating LLM outputs.

**GitHub:** https://github.com/promptfoo/promptfoo (~6k stars)

**How it works:**
- Run a prompt/document against multiple LLMs
- Assert expected behaviors, catch regressions
- Compare model outputs, score consistency

**Key difference from our tool:**
- Promptfoo: "does my prompt still work after I changed it?" (regression testing)
- Our tool: "is my document itself ambiguous?" (quality assessment)
- Different angle but overlapping machinery

**Integration potential:**
- Could use Promptfoo as the multi-model query layer (replace `model_interface.py`)
- Built-in scoring and comparison could replace parts of `ambiguity_detector.py`
- More mature tooling for the model communication layer

---

## Vale (Not Directly Relevant — Human Readability)

**What it is:** Open-source prose linter for human-readable style.

**What it does:** Enforces style guides (Microsoft, Google), grammar rules, consistency.

**Why it's different:** Checks for human readability, not LLM comprehension. Different problem.

**Not worth integrating** unless we add a "human readability" score to reports.

---

## RAGAS (RAG Pipeline Evaluation)

**What it is:** Framework for evaluating Retrieval-Augmented Generation pipelines.

**Only relevant if:** Our documents are consumed via RAG (retrieval + LLM generation).

**Not relevant for:** Direct document → LLM consumption (our current use case).

---

## Integration Roadmap Ideas

### Near-term (low effort)
- Use DSPy to optimize the judge prompt in `ambiguity_detector.py`
  - Current: hand-crafted prompt string
  - With DSPy: compiled prompt that provably improves detection accuracy

### Medium-term
- Replace manual model query layer with Promptfoo
  - Get their retry logic, response normalization, and model abstraction for free
  - Would simplify `model_interface.py` significantly

### Long-term (doc improvement vision)
- Full DSPy pipeline: document → ambiguity detection → auto-fix suggestions
  - DSPy compiles the fix-generation prompt (Increment 3 scope)
  - Measures quality of fixes against a held-out test set of known-good documents
