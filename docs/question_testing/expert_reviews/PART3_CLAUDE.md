# Expert Review Part 3: Implementation Plan Review
# Response from Anthropic Claude

**Review Date:** 2025-12-30
**Prompt:** PART3_PROMPT.md
**Plan Reviewed:** BULKY_CLEAN_ARCHITECTURE_PLAN.md
**Model:** Claude 4.5 opus
**Perspectives:** (paste perspectives covered)

---

# Expert Review Part 3: Bulky-Clean Architecture Implementation Plan

**Review Date:** December 30, 2025  
**Document Reviewed:** BULKY_CLEAN_ARCHITECTURE_PLAN.md  
**Context:** Personal project, iterative improvement, LLM-targeted documentation

---

# Section 1: Overall Assessment

## Verdict: **Proceed with Changes**

## Rationale

The plan is fundamentally sound and addresses the right problems. The source/build approach (bulky → clean) is the correct architecture for separating test infrastructure from LLM-consumable output. However, the plan is slightly over-engineered for a personal project. The phasing is appropriate, but Week 1 is too light while Week 2-3 carries too much risk without early validation.

## Confidence: **High**

This approach will work. The core mechanism (regex strip of HTML comments) is simple and reliable. The main risk isn't technical—it's whether the overhead of maintaining bulky docs pays off. That's a value question only real usage will answer.

---

# Section 2: Critical Issues

## Issue 1: Week 1 Validates Format, Not Value

**Issue:** Phase 1 (Week 1) only builds the strip script and format spec. You won't know if the overall approach is worthwhile until Week 3-4 when templates are working.

**Impact:** You could build infrastructure for 2 weeks before discovering the approach doesn't provide enough value for the overhead.

**Fix:** Add a "smoke test" to Week 1: Manually write 5 questions for a bulky doc's assertions. Test them with models. If you can't write good questions manually, templates won't help.

**Priority:** High

## Issue 2: Template Regex Will Miss Common Patterns

**Issue:** The template patterns are too specific:
- `"{subject} (is|are|must be) {value}"` won't match "Timeout: 30 seconds" or "The timeout defaults to 30 seconds"
- `"(On|When) {trigger}: {outcome}"` won't match "If the input is empty, return an error"

**Impact:** Template success rate will be closer to 50-60% than 80%+. The 20% "LLM fallback" will actually be 40-50%.

**Fix:** Design templates with multiple pattern variants OR accept lower template coverage initially and iterate based on real data.

**Priority:** High

## Issue 3: No Rollback Plan

**Issue:** If the approach fails at Week 3-4, there's no documented fallback. What happens to the bulky docs you've created?

**Impact:** Wasted effort if approach doesn't work; messy state with partial bulky/clean docs.

**Fix:** Add explicit decision points: "If template success < 60% at Week 2, STOP and reassess." Specify what "reassess" means—simplify templates? Abandon questioning? Use pure LLM generation?

**Priority:** Medium

---

# Section 3: Architecture Feedback

## What's Good

1. **Directory separation is correct**: `docs/bulky/` vs `docs/clean/` is clear and sufficient. Agents can be instructed to read only `docs/clean/`. No need for file extensions.

2. **HTML comment markers are invisible**: Unlike custom syntax, `<!-- @assertion -->` renders as nothing in standard markdown viewers. Writers can read the documentation naturally while editing the source.

3. **Commit both bulky and clean (Option A)**: Correct choice. Seeing both versions in PRs/diffs is valuable. Clean docs are small; git storage cost is negligible.

4. **Idempotent strip**: Making `strip(strip(doc)) == strip(doc)` is important and correctly specified.

5. **Phasing order is correct**: Foundation → Templates → Integration is the right sequence. You need the format before you can write templates; you need templates before integration adds value.

## What's Risky

1. **Regex may have edge cases in code blocks**:
   ```markdown
   ```python
   # This comment <!-- @something --> inside code won't render
   # but your regex will strip it
   ```
   ```
   **Risk:** Low (unlikely pattern), but worth a test case.

2. **Assertion ID uniqueness across documents**: The plan specifies IDs are unique *within* a doc. If you later aggregate questions across docs, collisions occur.
   **Risk:** Low now, but consider prefixing: `workflow_step1_req_01` instead of `step1_req_01`.

3. **Polishing results inline vs separate file**: Storing `@polishing_results` inline will make bulky docs grow indefinitely with history.
   **Risk:** Medium. After 10 polish runs, the metadata could be longer than the content.

4. **Manual assertion authoring overhead**: Every testable claim needs a `<!-- @assertion -->` wrapper. For a 100-line doc, this might add 50+ lines of metadata.
   **Risk:** Medium. Overhead may discourage adoption.

## Suggestions

1. **Add assertion linter early**: Week 1 should include a simple linter that warns about potential assertions without markers (sentences with "must", "is required", values like "30 seconds"). This helps authors find what to mark.

2. **Store polishing results separately**: Instead of inline `@polishing_results`, use `docs/bulky/workflow.polish-history.json`. Reference from the doc: `<!-- @polishing_history file="workflow.polish-history.json" -->`. Keeps bulky docs manageable.

3. **Consider assertion shorthand**: For simple assertions, allow inline format:
   ```markdown
   **Timeout:** 30 seconds <!-- @assert:constraint:timeout_01 -->
   ```
   vs. the verbose:
   ```markdown
   <!-- @assertion id="timeout_01" type="constraint" -->
   **Timeout:** 30 seconds
   <!-- @/assertion -->
   ```
   This reduces visual noise significantly.

---

# Section 4: Phase-by-Phase Review

## Phase 1: Foundation (Week 1)

### Feasibility: ✅ Realistic

The deliverables (strip script, format spec, 1 example) are achievable in a few hours of focused work. A week is plenty.

### Risks

1. **Too light on validation**: You'll have a working strip script but no evidence the overall approach is valuable.
2. **Format spec might evolve**: Locking in the format before trying templates could require rework.

### Suggestions

1. **Add manual question-writing exercise**: Before finishing Week 1, write 5 questions manually for your test doc's assertions. Time yourself. Evaluate if questions are good. This proves the approach before automating.

2. **Add "clean doc validation"**: After stripping, verify the clean doc:
   - Contains no `@meta`, `@assertion`, `@polishing` strings
   - Parses as valid markdown
   - Has no orphaned HTML comment closers (`-->` without `<!--`)

3. **Start with simpler assertions**: The format spec shows fairly complex assertions. For Week 1's example, use only `type="constraint"` assertions (the easiest template). Prove the simple case first.

### Priority: **Critical** (must complete before Phase 2)

---

## Phase 2: Fix Question Templates (Week 2-3)

### Feasibility: ⚠️ Optimistic Timeline

Two weeks for 5 templates with >80% success rate is aggressive. Template design requires iteration—you'll write a pattern, test it, find it misses cases, revise. Each cycle takes time.

### Risks

1. **Regex patterns won't match real text**: The plan's patterns assume very structured assertion text. Real assertions will vary: "Timeout is 30 seconds", "Timeout: 30 seconds", "The default timeout value is 30 seconds". Each variation needs either a more flexible pattern or multiple patterns.

2. **80% success rate target may be unrealistic**: If your assertion text isn't written to fit templates, you'll hit 50-60% match rate. The "fix" is either rewrite assertions (defeats the purpose) or accept lower template coverage.

3. **Validation edge cases**: The 10% leakage threshold is reasonable, but edge cases exist. "What is the maximum batch size?" / "100 items" has 0% overlap. But "What is the timeout?" / "30 seconds timeout" has overlap on "timeout". Is that leakage?

### Suggestions

1. **Start with 3 templates, not 5**: Focus on `constraint`, `requirement`, and `behavior`. These cover 80% of assertion types. Add `error` and `sequence` in Week 3 if needed.

2. **Design patterns from real assertions, not idealized examples**: Before writing patterns, collect 20 real assertions from your actual docs. Then design patterns that match them. Don't design patterns for ideal text you'll never write.

3. **Define fallback explicitly**: When templates don't match, what happens? Options:
   - Skip (no question for this assertion)
   - LLM generation (use Claude to generate question)
   - Human review queue (flag for manual question writing)
   
   Currently the plan says "LLM fallback 20%" but doesn't specify how or when.

4. **Add "template match rate" metric early**: In Week 2, Day 1-2, run templates on your test doc. Measure match rate immediately. If < 60%, pause and refine patterns before writing more code.

### Priority: **Critical** (core value prop depends on this)

---

## Phase 3: Integrate into polish.py (Week 4)

### Feasibility: ✅ Realistic

Integration is mechanical once Phases 1-2 work. The architecture in the plan is clean.

### Risks

1. **Integration before validation**: You're integrating into polish.py before proving question testing catches real issues. You might ship a feature that doesn't provide value.

2. **Opt-in default**: `enable_question_testing: false` is conservative, but means the feature might never get used.

### Suggestions

1. **Prove value before integration**: Before Week 4, run question testing manually on 2-3 docs. Document what issues it found. If it found nothing useful, reconsider integration.

2. **Consider "side car" mode**: Instead of integrating into polish.py, keep question testing as a separate script initially:
   ```bash
   python scripts/question_test.py docs/bulky/workflow.md
   ```
   This allows iteration without changing polish.py. Integrate only after proving value.

3. **Report format**: The plan shows question testing results nested in polish output. Consider a separate section or file for question results—they're a different kind of finding than ambiguity detection.

### Priority: **Important** but not critical (value comes from templates, not integration)

---

## Phase 4: Merge Script (Future/Deferred)

### Feasibility: ✅ Correctly Deferred

Merge is complex and depends on having auto-fix. Deferring is right.

### Suggestion

Don't just defer—mark it as **"May Never Be Needed"**. For a personal project, you might manually update bulky docs based on polish results. A merge script is nice-to-have automation.

---

# Section 5: Missing Considerations

## Gap 1: What Makes a "Good" Assertion?

**Description:** The plan specifies assertion format but not assertion quality. Not everything should be marked as an assertion. The plan risks either:
- Too few assertions (missing coverage)
- Too many assertions (testing trivial things)

**Why it matters:** If writers mark every sentence, you'll drown in questions testing unimportant details. If they mark too little, you miss real comprehension needs.

**Recommendation:** Add guidance: "Mark as assertion if an LLM failing to understand this would cause incorrect behavior." Don't mark explanatory/background text.

---

## Gap 2: No Assertion Authoring Workflow

**Description:** The plan assumes bulky docs with assertions exist. It doesn't describe how writers create them efficiently.

**Why it matters:** If marking assertions is tedious, adoption fails.

**Recommendation:** Add to Week 1:
- Snippet/template for assertion block
- Linter that suggests potential assertions
- Example workflow: "When writing a new doc, add assertions as you write. When converting existing doc, add assertions section-by-section."

---

## Gap 3: How Do You Know Questions Test the Right Thing?

**Description:** The plan validates question format (no leakage, grammar) but not question utility. A technically valid question might test something trivial.

**Why it matters:** You could generate 50 valid questions that all test the same type of knowledge, missing critical comprehension aspects.

**Recommendation:** Add manual review step: After generating questions, human reviews sample of 5-10. Asks: "Would an LLM failing this question indicate a real documentation problem?"

---

## Gap 4: Clean Doc Validation

**Description:** Strip script produces clean docs, but there's no verification that clean docs are truly clean and complete.

**Why it matters:** A strip bug could leave metadata fragments or remove actual content.

**Recommendation:** Add to strip script:
- Assert no `@meta`, `@assertion`, `@polishing` strings remain
- Assert clean doc has same number of headers as bulky (structure preserved)
- Optionally: diff clean against known-good clean version

---

## Gap 5: When to Stop Iterating

**Description:** The plan has success metrics (80% template rate, 0% leakage) but no "good enough" definition for the overall project.

**Why it matters:** Personal projects can iterate forever without shipping value.

**Recommendation:** Add explicit "done" criteria:
- Phase 1: "Done when strip script works and 1 bulky doc exists"
- Phase 2: "Done when we can generate 10+ valid questions from a real doc"
- Phase 3: "Done when polish.py runs question testing without errors"
- Project: "Done when 3 critical workflows have bulky versions and question testing has found ≥1 real issue"

---

# Section 6: Alternative Approach

## Alternative: Start with LLM Generation, Not Templates

### Proposed Approach

Skip template-based generation entirely. Use Claude to generate questions from assertions:

```python
def generate_question(assertion_text: str, assertion_type: str) -> dict:
    prompt = f"""
    Generate a comprehension question for this {assertion_type} assertion:
    "{assertion_text}"
    
    Rules:
    - Question should test if someone understood the assertion
    - Answer must be extractable from the assertion text
    - Do not include the answer in the question
    
    Output JSON: {{"question": "...", "answer": "..."}}
    """
    response = claude.generate(prompt)
    return parse_json(response)
```

### Why It Might Be Better

1. **Faster to implement**: No pattern design, no regex debugging
2. **Higher coverage**: LLM handles any assertion phrasing
3. **Lower maintenance**: No templates to update when assertion styles change

### Trade-offs

1. **Higher cost**: API call per assertion vs. free regex
2. **Less consistent**: LLM might generate different questions for same input
3. **Harder to debug**: Why did LLM generate a bad question?

### Recommendation

For a personal project with small doc counts, LLM generation is viable. Consider:
- Use templates for simple patterns (constraint, sequence)
- Use LLM for complex patterns (behavior, error, cross-reference)
- This reduces API calls while handling variability

---

# Section 7: Quick Wins (Week 1 Validation)

## Quick Win 1: Manual Question Writing Test (2 hours)

Before writing any code:
1. Pick your most complex workflow doc
2. Read through it, marking sentences you think are "testable"
3. Write 10 questions manually
4. Send questions to Claude/GPT, see if they answer correctly
5. Note which questions reveal comprehension issues

**What this proves:** Whether question-based testing can find real issues. If manual questions find nothing interesting, automation won't help.

---

## Quick Win 2: Regex Feasibility Test (1 hour)

Before finalizing format:
1. Collect 20 sentences from existing docs that would be assertions
2. Try to write regex patterns that match them
3. Count: How many can a single pattern match?

**What this proves:** Whether template-based generation is feasible. If you need 10 patterns to match 20 sentences, templates are too brittle.

---

## Quick Win 3: LLM Generation Spike (1 hour)

Test LLM generation quality:
1. Take 5 assertion sentences
2. Ask Claude to generate questions for each
3. Validate: Is there leakage? Are questions good?

**What this proves:** Whether LLM fallback is viable. If Claude generates good questions, you might use it more than templates.

---

## Quick Win 4: Overhead Estimation (30 minutes)

Estimate assertion markup overhead:
1. Take a 100-line doc
2. Mark what would be assertions (don't write full syntax, just highlight)
3. Count: How many assertions? What % of doc?
4. Estimate: How many lines of metadata would this add?

**What this proves:** Whether the overhead is acceptable. If assertions double doc length, the format is too verbose.

---

# Section 8: Specific Expert Perspectives

## Software Architecture

### Is directory separation robust?

**Yes.** `docs/bulky/` vs `docs/clean/` is clear and enforceable. Agents can be instructed: "Only read files in `docs/clean/`". No need for file extensions—directory is sufficient.

### Should we use a build tool (Make, npm scripts)?

**Not yet.** For a personal project, direct script invocation is fine:
```bash
python scripts/strip_metadata.py docs/bulky/workflow.md -o docs/clean/workflow.md
```

If you add CI/CD later, wrap in a Makefile then. Premature tooling adds complexity.

### Version control for two formats?

**Commit both** (Option A in plan). Seeing clean docs in diffs is valuable for reviewing what LLMs will actually see. Storage cost is negligible.

### Testing strategy for transformation?

The plan's tests are good. Add:
- Test with code blocks containing HTML-like strings
- Test with actual markdown links, images, tables (ensure preserved)
- Property-based test: for any clean doc, `strip(clean) == clean`

---

## Technical Writing

### Will writers actually use HTML comment markers?

**Probably, with tooling.** Raw HTML comments are tedious. Provide:
- VS Code snippet: type `assert` → expands to full block
- Linter that highlights potential unmarked assertions
- Example template they can copy

### Is assertion format too technical?

**The verbose format is too much.** Consider shorthand for simple cases:
```markdown
**Timeout:** 30 seconds <!-- @c:timeout_01 -->
```
Where `@c` = constraint, `@r` = requirement, `@b` = behavior.

The verbose form is still available for complex assertions or when you need priority/difficulty.

### How to document bulky format for future maintainers?

Add a `docs/bulky/README.md` that:
- Explains bulky vs clean distinction
- Shows format with examples
- Lists all assertion types
- Explains how to regenerate clean docs

---

## LLM/NLP

### Will HTML comments in markdown confuse LLMs if not stripped?

**Possibly.** Most LLMs process HTML comments as noise, but some might:
- Treat them as instructions
- Get confused by `@` symbols (looks like mentions)
- Have tokenization issues with YAML inside comments

**Mitigation:** Always test on clean docs. Never give LLMs bulky docs.

### Is template-based generation the right approach?

**For constraints and sequences, yes.** These have predictable structure.

**For behavior and error, questionable.** Natural language variation is high. Consider LLM generation for these types from the start.

### How to validate clean docs are truly clean?

Add to strip script output:
```python
def validate_clean(content: str) -> list[str]:
    issues = []
    if '@meta' in content:
        issues.append("Contains @meta")
    if '@assertion' in content:
        issues.append("Contains @assertion")
    if '@polishing' in content:
        issues.append("Contains @polishing")
    if re.search(r'<!--\s*@', content):
        issues.append("Contains @-prefixed comment")
    return issues
```

---

## DevOps/Tooling

### Should this be CLI tool, library, or both?

**CLI first, library later.** For personal use, CLI is sufficient:
```bash
python strip.py input.md -o output.md
```

If you later want to import in python (`from doctools import strip_metadata`), refactor then. Don't over-engineer upfront.

### Graceful error handling?

Plan is weak here. Add:
- Invalid markdown → Log warning, continue (don't crash)
- Missing input file → Clear error message
- Write failure → Report which file, why

### CI/CD integration?

**Defer.** For a personal project, manual workflow is fine. If you add CI later:
```yaml
on: push
jobs:
  build-clean-docs:
    steps:
      - run: python scripts/build_clean_docs.py
      - run: git diff --exit-code docs/clean/  # Fail if clean docs out of sync
```

### Use existing tools (pandoc)?

**No.** Pandoc doesn't strip HTML comments selectively. A 20-line Python script is simpler than configuring pandoc filters.

---

## Pragmatist

### Is 3-4 weeks realistic?

**Yes, but with different scope.** If you're heads-down, this is achievable:
- Week 1: Strip script + format (2-3 hours actual work)
- Week 2: Template implementation (4-6 hours)
- Week 3: Testing and iteration (2-4 hours)
- Week 4: Integration (2-3 hours)

That's 10-16 hours total. Spread over 4 weeks, very achievable.

### Minimum viable Week 1?

1. Strip script that works (regex, 20 lines)
2. One bulky doc converted from existing clean doc
3. Manual question-writing test (proves value)

Skip: Format spec document, elaborate testing, validation script.

### What can we skip entirely?

1. **Merge script (Phase 4):** Likely never needed. Manual updates are fine.
2. **Polishing history inline:** Store separately or not at all initially.
3. **Difficulty metadata:** Add later if needed; not essential.
4. **5 templates:** Start with 3 (constraint, requirement, behavior).

### Simplest thing that could work?

```python
# strip.py (15 lines)
import re
import sys

def strip(content):
    return re.sub(r'<!--\s*@\w+.*?-->', '', content, flags=re.DOTALL)

if __name__ == '__main__':
    content = open(sys.argv[1]).read()
    print(strip(content))
```

```bash
python strip.py docs/bulky/workflow.md > docs/clean/workflow.md
```

That's it. Week 1 done. Build from there.

### How to avoid "perfect is enemy of good"?

1. **Time-box:** "I will spend max 2 hours on the strip script, then it's done."
2. **Ship ugly:** First version can have hardcoded paths, no error handling, no tests.
3. **Prove value first:** Before polish, test manually. Before automating, do it by hand.
4. **Define "done":** Write down what success looks like. Stop when you reach it.

---

# Section 9: Revised Week 1 Recommendation

Based on this review, here's a revised Week 1 plan:

## Day 1 (2 hours): Validation

1. **Manual question test** (1 hour)
   - Pick your hardest workflow doc
   - Write 5 questions by hand
   - Test with Claude: Does it answer correctly?
   - Result: "Question testing can/cannot find real issues"

2. **Regex feasibility test** (30 min)
   - Collect 10 would-be assertions from your docs
   - Write one regex pattern for "constraint" type
   - Count matches
   - Result: "Templates can match X% of real assertions"

3. **Decision point**: If both tests fail, STOP. Rethink approach.

## Day 2 (2 hours): Minimum Implementation

4. **Strip script** (30 min)
   - 15-line Python script
   - Test on one file
   - Works? Ship it.

5. **One bulky doc** (1 hour)
   - Take your simplest workflow
   - Add @meta block
   - Add 3-5 @assertion blocks (constraint type only)
   - Strip it, verify output

6. **Validate round-trip** (30 min)
   - Original clean doc vs stripped bulky
   - Should be identical (minus formatting)
   - If not, debug strip script

## Day 3 (Optional): Documentation

7. **README for format** (30 min)
   - What is bulky vs clean
   - How to add assertions
   - How to regenerate clean

**Week 1 Success Criteria:**
- Strip script works
- One bulky doc exists with 3+ assertions
- Manual testing showed question testing is valuable (or not)
- Decision: Proceed to Week 2 or pivot

---

# Summary

## Proceed with these changes:

1. **Add validation before automation** (Week 1: manual question test)
2. **Start with 3 templates, not 5** (constraint, requirement, behavior)
3. **Design patterns from real assertions**, not idealized examples
4. **Add explicit decision points** (if template match < 60%, pause)
5. **Consider LLM generation earlier** for behavior/error types
6. **Store polishing history separately**, not inline
7. **Define "done" explicitly** for each phase
8. **Keep integration separate initially** (don't modify polish.py until value proven)

## Top risks to watch:

1. Template patterns won't match real assertion text (mitigate: design from real data)
2. Assertion authoring overhead discourages use (mitigate: provide shortcuts)
3. Question testing doesn't find valuable issues (mitigate: prove manually first)
4. Scope creep ("while I'm here, let me also...") (mitigate: time-box ruthlessly)

## The bottom line:

The plan is good. The architecture is right. The phasing is correct. But you're carrying risk too long before validation. **Prove the approach works manually in Week 1 before building infrastructure.** If manual question testing finds real issues, templates are worth building. If it doesn't, save yourself 3 weeks.
