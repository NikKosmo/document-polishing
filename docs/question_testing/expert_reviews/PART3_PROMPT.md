# Expert Review Part 3: Implementation Plan Review

**Date:** 2025-12-30
**Context:** Bulky-Clean Document Architecture Implementation Plan
**Audience:** Expert panel (multiple perspectives)

---

## Background

In Part 2, you reviewed our integrated approach to LLM-optimized documentation and question generation. Based on your recommendations, we've designed a **source/build system** for documentation.

### Key Design Decisions (Based on Your Recommendations)

1. **Dual-format approach:** Bulky docs (source with test markers) → Clean docs (for LLM consumption)
2. **Directory separation:** `docs/bulky/` (agents don't read) vs `docs/clean/` (agents read)
3. **HTML comment markers:** `<!-- @assertion -->` format (Claude's recommendation)
4. **Hybrid generation:** Template-first (80%), LLM fallback (20%)
5. **3-phase implementation:** Foundation → Fix Templates → Integration

### What We Need

We've created a detailed implementation plan (attached). We need your expert review to validate:
- Is the implementation approach sound?
- Are we missing critical considerations?
- What risks should we watch for?
- What would you do differently?

---

## Your Task

Review the attached **BULKY_CLEAN_ARCHITECTURE_PLAN.md** from your expert perspective.

**Focus on:**

1. **Feasibility:** Can this actually work in practice?
2. **Risks:** What could go wrong? What are we overlooking?
3. **Priorities:** Are we tackling things in the right order?
4. **Gaps:** What's missing from the plan?
5. **Alternatives:** Would you approach this differently?

---

## Specific Review Areas

### 1. Architecture Soundness

**The Plan:**
- Bulky docs in `docs/bulky/` (source of truth, with metadata)
- Clean docs in `docs/clean/` (generated, for LLM consumption)
- Strip script removes `<!-- @meta`, `<!-- @assertion`, `<!-- @polishing_results -->` blocks
- Deterministic transformation (idempotent, fast)

**Questions:**
- Is directory separation sufficient to prevent agents from reading bulky docs?
- Should we use different file extensions instead? (e.g., `.src.md` vs `.md`)
- What happens if strip script has bugs? How do we validate output?
- Should clean docs be committed to git, or generated on-demand?

### 2. Metadata Format Design

**The Plan:**
```markdown
<!-- @meta
version: 1.0
created: 2025-12-30
last_polished: 2025-12-30
status: active
known_issues: []
-->

<!-- @assertion id="step1_req_01" type="requirement" priority="critical" -->
**Requirement:** All fields must be validated.
<!-- @/assertion -->

<!-- @polishing_results
- run_date: 2025-12-30
  models: [claude, gpt4, gemini]
  issues:
    - section: "Step 1"
      type: "model_disagreement"
      ...
-->
```

**Questions:**
- Is this format practical for manual authoring?
- Will HTML comments work reliably across markdown renderers?
- Should metadata be YAML, JSON, or custom format?
- Is `@polishing_results` better in separate file (not inline)?
- What about schema validation? Should we validate metadata structure?

### 3. Phase 1: Strip Script

**The Plan:**
- Single Python script with regex: `r'<!--\s*@\w+.*?-->'`
- Removes all `@`-prefixed HTML comments
- Preserves content and structure
- Idempotent operation
- Target: < 100ms for typical doc

**Questions:**
- Is regex sufficient? Or do we need proper HTML/markdown parser?
- What edge cases could break this? (nested comments, code blocks with HTML, etc.)
- Should we validate stripped output (e.g., no metadata leaked)?
- How do we test this thoroughly? What test cases are critical?
- Performance: Is 100ms realistic? What's acceptable upper bound?

### 4. Phase 2: Template Redesign

**The Plan:**
- 5 core templates (constraint, requirement, behavior, error, sequence)
- Pattern matching with named groups: `(?P<subject>...) is (?P<value>...)`
- Validation: leakage < 10%, answerability, grammar, uniqueness
- Target: 80%+ template success rate

**Questions:**
- Are 5 templates enough for Phase 2? Or start with 3?
- Will regex patterns handle real-world assertion variations?
- Is 10% leakage threshold too strict? Too lenient?
- How do we measure "template success rate" objectively?
- What happens with the 20% that templates can't handle?

### 5. Phase 3: Integration into polish.py

**The Plan:**
- polish.py accepts bulky docs
- Automatically strips to clean before testing
- Question generation runs on bulky (has assertions)
- Comprehension testing runs on clean (what LLMs see)
- Optional flag: `enable_question_testing: false` (opt-in)

**Questions:**
- Should questioning be opt-in or opt-out?
- Should strip happen inside polish.py, or as preprocessing step?
- What if bulky doc is invalid (malformed metadata)? Fail or fallback?
- How do we report question testing results? Inline with ambiguity detection?
- Integration testing: How do we validate end-to-end workflow?

### 6. Phasing Strategy

**The Plan:**
```
Phase 1 (Week 1): Strip script + format spec
Phase 2 (Week 2-3): Fix templates
Phase 3 (Week 4): Integration into polish.py
Future: Merge script (polishing results back to bulky)
```

**Questions:**
- Is this the right order? Or should templates come before strip?
- Week 1 seems light (just strip script). What else should we include?
- Should we do a small end-to-end test in Week 1 (before committing to format)?
- When should we test with real documents? Week 2 or Week 3?
- What are the critical decision points? When do we pivot vs persevere?

### 7. Personal Project Context

**Important constraints:**
- **Personal project** (single user, iterative)
- **Non-critical** (failures waste time, not catastrophic)
- **LLM-targeted docs** (workflows, instructions, standards)
- **Manual doc creation** (user generates from prompts)
- **Gradual adoption** (start with 1-2 docs, expand if valuable)

**Questions:**
- Given this is personal/iterative, are we over-engineering?
- What's the minimum viable implementation for Week 1?
- Should we skip some phases entirely? (e.g., merge script may never be needed)
- What's the simplest thing that could work? Are we adding unnecessary complexity?
- How do we avoid "perfect is enemy of good" trap?

---

## Output Format

Please structure your review as follows:

### Section 1: Overall Assessment

**Verdict:** [Proceed / Proceed with Changes / Rethink / Stop]

**Rationale:** [2-3 sentences on why]

**Confidence:** [High / Medium / Low] that this approach will work

### Section 2: Critical Issues (If Any)

List any showstopper problems that must be addressed:

1. **Issue:** [Description]
   - **Impact:** [What breaks]
   - **Fix:** [How to resolve]
   - **Priority:** [Blocker / High / Medium]

### Section 3: Architecture Feedback

**What's Good:**
- [What you like about the approach]

**What's Risky:**
- [Potential problems or weak points]

**Suggestions:**
- [Specific improvements or alternatives]

### Section 4: Phase-by-Phase Review

For each phase (1-3), provide:

**Phase [N]: [Name]**
- **Feasibility:** [Can this work? Realistic timeline?]
- **Risks:** [What could go wrong?]
- **Suggestions:** [Improvements or additions]
- **Priority:** [Critical / Important / Nice-to-have]

### Section 5: Missing Considerations

What's not in the plan that should be?

- [Gap 1]: [Description + why it matters]
- [Gap 2]: ...

### Section 6: Alternative Approach (Optional)

If you'd do this differently, describe:

**Alternative:**
[Your proposed approach]

**Why it's better:**
[Advantages over current plan]

**Trade-offs:**
[What you lose with this approach]

### Section 7: Quick Wins

What could we do in Week 1 to validate the approach with minimal effort?

1. [Concrete action that proves/disproves key assumption]
2. ...

---

## Specific Questions for Each Perspective

### Software Architecture Expert
- Is the directory separation approach robust?
- Should we use a build tool (Make, npm scripts) instead of manual strip?
- How do we handle version control for two formats?
- What's the testing strategy for transformation pipeline?

### Technical Writing Expert
- Will writers actually use HTML comment markers?
- Is the assertion format too technical? Too simple?
- How do we document the bulky format for future maintainers?
- Should we provide templates/snippets to ease authoring?

### LLM/NLP Expert
- Will HTML comments in markdown confuse LLMs if not stripped?
- Is template-based generation the right approach? Or should we use LLM from start?
- How do we validate that stripped docs are truly "clean" for LLMs?
- Should we test with multiple markdown renderers?

### DevOps/Tooling Expert
- Should this be a CLI tool, library, or both?
- How do we handle errors gracefully?
- What's the CI/CD integration story?
- Should we use existing tools (pandoc, etc.) instead of custom strip script?

### Project Management / Pragmatist
- Is 3-4 weeks realistic for a personal project?
- What's the minimum we can ship in Week 1 to get feedback?
- How do we avoid scope creep?
- When do we declare "good enough" and move on?

---

## Context You Should Know

### Project Scope
- **Personal project** (not team, not production-critical)
- **Iterative improvement** (polish docs gradually, not all at once)
- **User controls doc structure** (generates docs, can enforce format)
- **Already have working polish.py** (ambiguity detection works)

### Current State
- **questioning_step.py exists** (2,009 lines, but templates broken)
- **Templates generate 0 valid questions** (100% answer leakage)
- **Expert reviews completed** (Part 1 + Part 2)
- **Ready to implement** (plan created, need validation)

### Success Criteria
- **Template success > 80%** (assertions → valid questions)
- **0% answer leakage** (questions don't contain answers)
- **Process sustainable** (low overhead, not burdensome)
- **Documents measurably better** (LLMs follow them reliably)

---

## Your Review Deliverable

**Format:** Markdown document
**Length:** No limit (be thorough)
**Tone:** Constructive and practical
**Focus:** Implementation reality, not theory

**What we value most:**
1. **Practical concerns** we've overlooked
2. **Risks** we haven't considered
3. **Simplifications** we could make
4. **Quick wins** to validate approach early
5. **Hard truths** if this won't work

**What we value least:**
- Repeating what we already know
- Theoretical perfection (we need practical progress)
- Scope expansion (we need focused execution)

---

## Thank You

Your Part 2 reviews were invaluable in shaping this plan. We're looking forward to your implementation feedback.

**File attached:** BULKY_CLEAN_ARCHITECTURE_PLAN.md

---

**Prompt Version:** 3.0 (Implementation Plan Review)
**Date:** 2025-12-30
**Expected Review Time:** 15-30 minutes per expert perspective