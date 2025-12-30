# Expert Review Part 3: Comparative Analysis
# Implementation Plan Review Synthesis

**Date:** 2025-12-30
**Reviews Analyzed:** Claude Opus 4.5, OpenAI Codex, Google Gemini 3 Pro
**Document Reviewed:** BULKY_CLEAN_ARCHITECTURE_PLAN.md
**Purpose:** Synthesize expert feedback on implementation plan

---

## Executive Summary

**Universal Verdict:** All three models recommend **"Proceed with Changes"**

**Confidence Levels:**
- Claude: **High** - "This approach will work"
- Codex: **Medium** - "Needs stronger guarantees"
- Gemini: **High** - "Single most important decision made so far"

**Core Agreement:** The bulky-clean architecture is fundamentally sound, but Week 1 is too light on validation and the regex strip approach is risky. All models want faster proof-of-value before infrastructure investment.

**Critical Consensus Issues (All 3 Models):**
1. **Regex strip is brittle** - Will break on code blocks, needs parser or state-aware scanner
2. **Week 1 validates format, not value** - Need end-to-end smoke test before building tooling
3. **Template success rate optimistic** - Expect 50-60%, not 80%+
4. **Authoring overhead is a risk** - Manual assertion markup will discourage adoption without tooling

**Key Divergence:** How to fix the strip script
- **Claude:** Accept regex with robust validation
- **Codex:** Use markdown parser/AST
- **Gemini:** State-aware parser with non-greedy regex

---

## Part 1: Universal Agreement (All 3 Models)

### ✅ What All Models Agree On

#### Architecture Decisions

1. **Directory separation is sufficient**
   - `docs/bulky/` vs `docs/clean/` is clear and enforceable
   - No need for file extensions (though Gemini suggests it as enhancement)
   - Agents can be instructed to only read `docs/clean/`

2. **HTML comment markers are the right format**
   - Invisible in rendered markdown (good for readability)
   - Standard markdown syntax (no parser changes needed)
   - Claude says: "Writers can read documentation naturally while editing"

3. **Commit both bulky and clean to git**
   - Seeing both versions in PRs/diffs is valuable
   - Storage cost is negligible
   - Helps with review and debugging

4. **Phasing order is correct**
   - Foundation → Templates → Integration makes sense
   - Don't integrate into polish.py until questioning is proven valuable
   - Optional/opt-in integration is the right default

5. **Source/build separation solves the metadata contamination problem**
   - Codex: "Clear separation reduces LLM contamination risk"
   - Gemini: "Decouples human/test metadata from LLM consumption"
   - Claude: "Directory separation is correct... Agents can be instructed"

#### Critical Issues (Unanimous)

1. **Week 1 is too light on validation**
   - **Claude:** "You won't know if overall approach is worthwhile until Week 3-4"
   - **Codex:** "Week 1 too narrow; doesn't validate real value"
   - **Gemini:** "Waiting until Week 4 is too late to find out if clean docs improve detection"

   **Fix (all agree):** Add end-to-end smoke test in Week 1
   - Manually write questions for a bulky doc
   - Test with models on clean docs
   - Prove approach before automation

2. **Regex strip is risky for markdown**
   - **Claude:** "Regex may have edge cases in code blocks"
   - **Codex:** "Can remove markers inside code fences or malformed comment blocks"
   - **Gemini:** "Regex greediness may accidentally strip real content in code blocks"

   **Impact:** Corrupted examples, accidental content removal

   **Priority:** All say HIGH

3. **Template success rate will be lower than 80%**
   - **Claude:** "Template success rate will be closer to 50-60%"
   - **Codex:** "Template success >80% is ambitious"
   - **Gemini:** "Don't build 5 core templates immediately. Build two... and test"

   **Reason:** Real assertion text varies too much for rigid regex patterns
   - "Timeout: 30 seconds"
   - "The timeout is 30 seconds"
   - "Timeout defaults to 30 seconds"
   - Each needs different pattern or multiple variants

4. **Assertion authoring overhead is a real risk**
   - **Claude:** "Manual assertion authoring overhead... For a 100-line doc, this might add 50+ lines of metadata"
   - **Codex:** "HTML comments are invisible... Writers may forget assertions"
   - **Gemini:** "Manual authoring of `<!-- @assertion -->` is painful"

   **Fix (all agree):** Provide tooling/snippets
   - VS Code snippets for assertion blocks
   - Lint warnings for potential unmarked assertions
   - Template examples to copy

#### Recommendations (Unanimous)

1. **Start with 3 templates, not 5**
   - Claude: "Focus on constraint, requirement, behavior"
   - Codex: (Implicit in "ambitious" comment)
   - Gemini: "Build two (Requirement and Constraint) and test... Quality over quantity"

2. **Add CI/automation checks**
   - Codex: "Add CI check that re-strips bulky docs and diffs with clean"
   - Gemini: "Use Makefile to make strip process a single command: `make build`"
   - Claude: (In DevOps section) "Add CI workflow for drift detection"

3. **Design templates from real data, not idealized examples**
   - Claude: "Collect 20 real assertions from actual docs. Then design patterns that match them"
   - Codex: "Add 1-2 doc-specific patterns and measure"
   - Gemini: "Let template provide logic, let LLM provide prose"

4. **Prove value before infrastructure**
   - All three emphasize manual validation in Week 1
   - Don't build automation until proven useful
   - Fast feedback is critical for personal project

---

## Part 2: Key Differences

### Confidence Levels

| Model | Confidence | Reasoning |
|-------|-----------|-----------|
| **Claude** | **High** | "This approach will work. The core mechanism is simple and reliable." |
| **Codex** | **Medium** | "Pipeline needs stronger guarantees (validation, drift detection, parser-safe strip)" |
| **Gemini** | **High** | "Standard software pattern (compilation/transpilation) applied to documentation" |

**Analysis:** Claude and Gemini are confident in the architecture itself. Codex wants more robustness guarantees before being confident.

### How to Fix Strip Script

| Model | Approach | Trade-offs |
|-------|----------|-----------|
| **Claude** | Accept regex with robust validation | Simple, fast to implement. Risk: edge cases exist |
| **Codex** | Use markdown parser or AST | Robust, handles all edge cases. Trade-off: dependency, more code |
| **Gemini** | State-aware parser or non-greedy regex with boundaries | Middle ground. Risk: still more complex than simple regex |

**Alternative Approaches Offered:**

**Codex:**
- Fenced blocks: `:::assertion` instead of HTML comments
- Structured data: Store assertions in JSON/YAML, render docs from them

**Gemini:**
- YAML front-matter for document-level metadata (not inline)
- File extensions: `.bulky.md` for source files

**Claude:**
- Start with LLM generation instead of templates
- Assertion shorthand: `**Timeout:** 30s <!-- @c:timeout_01 -->`

### Specific Tactical Recommendations

#### Only Claude

1. **Assertion shorthand syntax** for simple cases:
   ```markdown
   **Timeout:** 30 seconds <!-- @c:timeout_01 -->
   ```
   Instead of verbose block format

2. **Store polishing history separately**:
   - Use `workflow.polish-history.json` instead of inline
   - Prevents bulky docs from growing indefinitely

3. **Explicit "done" criteria** for each phase:
   - Phase 1: "Done when strip works and 1 bulky doc exists"
   - Phase 2: "Done when we can generate 10+ valid questions from real doc"
   - Phase 3: "Done when polish.py runs question testing without errors"

4. **Most detailed revised Week 1 plan**:
   - Day 1 (2h): Manual question test + regex feasibility
   - Day 2 (2h): Strip script + one bulky doc
   - Day 3 (optional): Documentation
   - Total: 4-6 hours of actual work

5. **"Simplest thing that could work"** example:
   ```python
   # 15-line strip.py
   import re, sys
   def strip(content):
       return re.sub(r'<!--\s*@\w+.*?-->', '', content, flags=re.DOTALL)
   print(strip(open(sys.argv[1]).read()))
   ```

#### Only Codex

1. **Schema validation** as explicit requirement:
   - Define JSON schema for `@meta` and `@assertion` in Phase 1
   - Validate structure automatically

2. **Drift detection** as separate concern:
   - CI check: `strip(bulky) == clean`
   - Pre-commit hook option

3. **Five expert perspectives** broken out separately:
   - Software Architecture
   - Technical Writing
   - LLM/NLP
   - DevOps/Tooling
   - Project Management/Pragmatist

   (Most comprehensive multi-perspective analysis)

4. **Authoring ergonomics** as missing consideration:
   - No tooling to insert markers safely
   - Need copy-paste snippets

5. **"Stop-loss" threshold**:
   - If template match < 50% after 2 iterations, pause and reassess

#### Only Gemini

1. **Auto-generate assertion IDs** if missing:
   - "Use hash of content or line-number slug"
   - Reduces manual "authoring tax"
   - Prevents copy-paste errors

2. **File extension sentinel** approach:
   - Use `.bulky.md` for source files
   - Add `.gitignore` or `exclude` rule for agents
   - Works regardless of directory structure

3. **Build header** in every clean file:
   - `<!-- AUTO-GENERATED from docs/bulky/workflow.bulky.md - DO NOT EDIT -->`
   - Prevents illegal edits to clean docs

4. **Token efficiency metric**:
   - Compare token counts between bulky and clean
   - Proves clean docs are actually better for LLMs

5. **IDE snippets** in the repo:
   - Include `.vscode/snippets.json`
   - Auto-complete assertion tags

6. **Specific smoke test timeline**: "Do this by Wednesday"
   - Most concrete deadline suggestion

7. **`.cursorrules` or `.gitignore`** to explicitly hide bulky docs from agents:
   - Not just directory-based
   - Explicit file-level exclusion

### Critical Issue Framing

**Claude:** Frames as "value validation" problem
- Issue 1: "Week 1 Validates Format, Not Value"
- Focus: Will this provide enough value for the overhead?
- Risk: "You could build infrastructure for 2 weeks before discovering approach doesn't provide value"

**Codex:** Frames as "robustness" problem
- Issue 1: "Strip script uses regex over raw Markdown"
- Focus: Will the transformation be reliable?
- Risk: "Corrupted examples or accidental content removal"

**Gemini:** Frames as "integration timing" problem
- Issue 3: "Integration Lag - Waiting until Week 4 too late"
- Focus: When do we know if this actually works?
- Risk: "Too late to find out if clean docs actually improve ambiguity detection"

**Analysis:** All point to same underlying issue (validate early), but emphasize different risks.

---

## Part 3: Critical Issues Breakdown

### Issue Matrix

| Issue | Claude | Codex | Gemini | Priority |
|-------|--------|-------|--------|----------|
| **Regex strip brittleness** | ⚠️ Low risk, add test case | 🔴 High - use parser | 🔴 High - state-aware | **HIGH** |
| **Week 1 too light** | 🔴 High - add smoke test | 🔴 High - add pilot | 🔴 High - move integration test | **HIGH** |
| **Template match rate** | 🔴 High - will be 50-60% | ⚠️ Medium - ambitious | ⚠️ Medium - start with 2 | **HIGH** |
| **No CI enforcement** | ⚠️ Mentioned in DevOps | 🔴 High - add CI check | ⚠️ Medium - add check flag | **HIGH** |
| **Authoring overhead** | ⚠️ Medium - 50+ lines | 🔴 High - invisible markers | ⚠️ Medium - authoring tax | **MEDIUM** |
| **No metadata validation** | Not flagged | 🔴 Medium - add schema | Not flagged | **MEDIUM** |
| **Manual ID management** | Not flagged | Not flagged | 🔴 Medium - auto-generate | **MEDIUM** |
| **No rollback plan** | 🔴 Medium - add decision points | Not explicitly | Not explicitly | **MEDIUM** |
| **Polishing history inline** | ⚠️ Medium - grows indefinitely | Not flagged | Not flagged | **MEDIUM** |

### All-Model Critical Issues (Must Address)

#### 1. Strip Script Robustness

**Problem:** Regex `r'<!--\s*@\w+.*?-->'` can match/remove:
- HTML comments inside code blocks
- Nested comments
- Partial tags if malformed

**Evidence:**
- Claude: "Regex may have edge cases in code blocks... worth a test case"
- Codex: "Can remove markers inside code fences... leading to corrupted examples"
- Gemini: "May accidentally strip real content if user puts HTML comment in code block"

**Recommended Fixes:**

| Model | Solution | Complexity |
|-------|----------|-----------|
| **Claude** | Add test case for code blocks, accept risk | Low |
| **Codex** | Use markdown parser or fence-aware scanner | High |
| **Gemini** | State-aware parser or non-greedy regex with boundaries | Medium |

**Decision Needed:**
- **Low-risk start:** Simple regex + comprehensive tests (Claude's approach)
- **Robust long-term:** Parser-based strip (Codex's approach)
- **Middle ground:** Fence-aware scanner (Gemini's approach)

**Recommendation:** Start with Claude's approach (simple + tests), migrate to fence-aware if issues appear in practice.

#### 2. Week 1 Validation Gap

**Problem:** Week 1 only builds strip script. Won't know if approach is valuable until Week 3-4.

**Evidence:**
- Claude: "You could build infrastructure for 2 weeks before discovering approach doesn't provide enough value"
- Codex: "May invest in format before proving question generation works"
- Gemini: "Waiting until Week 4 to integrate is too late to find out if clean docs improve detection"

**All Models Recommend:** Add end-to-end smoke test to Week 1

**Specific Smoke Test Steps (Synthesis):**

**From Gemini (most concrete):**
```
The "End-to-End Smoke Test" (Do this by Wednesday):
1. Take one real workflow document
2. Manually add three @assertion tags
3. Run hardcoded prompt: "Given these assertions, generate 3 questions
   that test if model understands these rules without using specific words"
4. Feed cleaned doc + generated questions to a model
5. If model fails questions while reading clean doc, architecture is proven
6. If model still passes easily, questions aren't hard enough
```

**From Claude (most detailed):**
```
Day 1 (2 hours): Validation
1. Manual question test (1 hour)
   - Pick hardest workflow doc
   - Write 5 questions by hand
   - Test with Claude: Does it answer correctly?
2. Regex feasibility test (30 min)
   - Collect 10 would-be assertions
   - Write one regex pattern for "constraint" type
   - Count matches
3. Decision point: If both fail, STOP. Rethink approach.
```

**From Codex:**
```
Quick Wins:
1. Annotate 1 doc, run strip, manually craft 5 questions from assertions
2. Run validation checks on those questions to validate criteria
```

**Combined Week 1 Smoke Test (Synthesized):**
1. **Pick test document** (1 real workflow, ideally complex)
2. **Add 3-5 assertions manually** (constraint type only)
3. **Write 5 questions by hand** (from assertions)
4. **Validate questions** (leakage, answerability checks)
5. **Test with model** (clean doc + questions → does model fail appropriately?)
6. **Measure template feasibility** (10 real assertions → how many match 1 pattern?)
7. **Decision point**: If manual questions don't find issues OR templates match <50%, STOP

**If smoke test passes:** Build strip script, proceed to Phase 2
**If smoke test fails:** Reassess approach (pure LLM generation? Different format?)

#### 3. Template Success Rate Expectations

**Problem:** Plan targets 80%+ template success. Models think 50-60% is realistic.

**Evidence:**
- Claude: "Template success rate will be closer to 50-60% than 80%+. The 20% 'LLM fallback' will actually be 40-50%"
- Codex: "Template success >80% is ambitious without structure-specific patterns"
- Gemini: "Don't build 5 core templates immediately. Build two and test against 10 diverse assertions"

**Why Templates Will Struggle:**

Real assertion text varies:
```markdown
# Pattern 1: "Timeout: 30 seconds"
# Pattern 2: "The timeout is 30 seconds"
# Pattern 3: "Timeout defaults to 30 seconds"
# Pattern 4: "Default timeout value: 30s"
# Pattern 5: "The system will timeout after 30 seconds"
```

One regex pattern can't match all variations without becoming too greedy.

**Recommended Adjustments:**

1. **Lower success target to 60%** (more realistic)
2. **Start with 2-3 templates**, not 5:
   - Constraint (most formulaic)
   - Requirement (second most formulaic)
   - Defer behavior/error/sequence to Phase 2 end or Phase 3

3. **Design from real data**:
   - Claude: "Collect 20 real assertions... Then design patterns"
   - Codex: "Add 1-2 doc-specific patterns and measure"

4. **Plan for higher LLM fallback**:
   - Budget for 40-50% LLM generation, not 20%
   - Estimate cost: ~$0.01 per assertion at current prices

5. **Add "stop-loss" threshold** (Codex):
   - If template match < 50% after 2 iterations, pivot to pure LLM generation

**Template Strategy Comparison:**

| Approach | Template Coverage | LLM Fallback | Cost | Maintenance |
|----------|------------------|--------------|------|-------------|
| **Plan (optimistic)** | 80% | 20% | Low | Medium |
| **Models (realistic)** | 50-60% | 40-50% | Medium | Medium |
| **Pure LLM** | 0% | 100% | High | Low |
| **Hybrid (recommended)** | 60% (2-3 templates) | 40% | Medium | Low |

---

## Part 4: Phase-by-Phase Synthesis

### Phase 1: Foundation (Week 1)

#### Consensus View

**Feasibility:** All agree it's easy (2-6 hours of work)

**Problem:** Too narrow - validates format but not value

**Critical Additions Needed (All Models):**

1. **Smoke Test** (see detailed breakdown in Part 3, Issue #2)
   - Manual question writing
   - Template feasibility check
   - End-to-end validation

2. **Strip Script Requirements:**
   - **Claude:** Simple regex, 15-20 lines, comprehensive tests
   - **Codex:** Parser-safe or fence-aware scanner
   - **Gemini:** Non-greedy regex with specific boundaries OR state-aware parser

3. **Validation/Lint:**
   - **Codex:** Schema validation for `@meta` and `@assertion`
   - **Codex/Gemini:** "Clean doc audit" - verify no metadata leaked
   - **Claude:** Validate clean doc has same headers as bulky (structure preserved)

4. **CI/Automation:**
   - **Codex:** CI check: `strip(bulky) == clean`
   - **Gemini:** `make build` command
   - **Claude:** Defer to later (personal project doesn't need it yet)

**Revised Week 1 Deliverables (Synthesis):**

| Deliverable | Codex | Claude | Gemini | Priority |
|-------------|-------|--------|--------|----------|
| Strip script | ✅ Parser-based | ✅ Regex + tests | ✅ State-aware | **Critical** |
| Format spec | ✅ With schema | ✅ Basic | ✅ With examples | **Critical** |
| 1 bulky doc | ✅ | ✅ | ✅ | **Critical** |
| Smoke test | ✅ End-to-end pilot | ✅ Manual questions + regex test | ✅ By Wednesday | **Critical** |
| Clean validation | ✅ Automated check | ✅ Structure check | ✅ Token efficiency | **High** |
| CI integration | ✅ Drift detection | ⚠️ Defer | ✅ Make target | **Medium** |
| Lint script | ✅ | ⚠️ Mentioned | ✅ Check flag | **Medium** |
| Authoring guide | ✅ One-page | ✅ Defer to Day 3 | ✅ IDE snippets | **Medium** |

**Week 1 Success Criteria (Consensus):**

✅ Strip script works (tested on 1 doc)
✅ One bulky doc exists with 3-5 assertions
✅ Manual smoke test completed
✅ Decision made: Proceed to Week 2 or pivot

**Risks All Models Flag:**

1. **Over-engineering before validation** (Claude, Codex)
2. **Format spec might evolve** - locking in too early (Claude)
3. **Silent failures in strip** (Codex)
4. **Confusing markers; accidental omissions** (Codex - Technical Writing)

### Phase 2: Fix Question Templates (Week 2-3)

#### Consensus View

**Feasibility:** Moderate - requires iteration

**Timeline:**
- **Claude:** "Two weeks is aggressive... Each iteration cycle takes time"
- **Codex:** "Templates may require several iterations"
- **Gemini:** "Start with two... Quality over quantity"

**Risks (All Models):**

1. **Patterns won't match real text**
   - Claude: "Real assertions will vary... each needs flexible pattern or multiple patterns"
   - Codex: "Regex templates won't match real assertions; coverage low"
   - Gemini: "Universal templates too generic to be useful"

2. **80% target unrealistic**
   - Claude: "You'll hit 50-60% match rate"
   - Codex: "Ambitious without structure-specific patterns"
   - Gemini: (Implicit in "start with 2")

3. **Validation edge cases**
   - Claude: "'What is timeout?' / '30 seconds timeout' has overlap on 'timeout'. Is that leakage?"
   - Codex: "Answerability check is substring-based, can be too strict or lax"

**Recommendations (Synthesis):**

| Recommendation | Models | Details |
|----------------|--------|---------|
| **Start with 2-3 templates** | All | Constraint, Requirement, (maybe Behavior) |
| **Design from real data** | All | Collect 20 actual assertions first |
| **Lower success target** | Claude | 60% instead of 80% |
| **Add iteration budget** | Claude, Codex | 2-3 cycles expected |
| **Define fallback explicitly** | Claude | When template fails: Skip? LLM? Human queue? |
| **Measure match rate early** | Claude | "Week 2, Day 1-2: run templates, measure immediately" |
| **Set stop-loss threshold** | Codex | If <50% after 2 iterations, pivot |

**Phase 2 Deliverables (Revised):**

**Original Plan:**
- 5 core templates
- 80%+ success rate
- <10% leakage
- LLM fallback for 20%

**Revised (Based on Reviews):**
- **2-3 core templates** (constraint, requirement, +1 optional)
- **60%+ success rate** (more realistic)
- **0-10% leakage** (keep strict threshold)
- **LLM fallback for 40-50%** (plan for higher cost)

**Week 2 Focus:**
- Day 1-2: Template design from real assertions
- Day 3-4: Implementation + validation
- Day 5: Measure match rate, decide continue/pivot

**Week 3 Focus:**
- Iteration based on Week 2 results
- Add 3rd template if first 2 are successful
- OR increase LLM fallback if templates struggling

**Priority:** Critical (core value prop depends on this)

### Phase 3: Integration into polish.py (Week 4)

#### Consensus View

**Feasibility:** All agree it's realistic IF Phase 2 works

**Timing Concern:**

- **Claude:** "You're integrating before proving question testing catches real issues"
- **Gemini:** "Move a 'Manual Integration' test to Week 1"
- **Codex:** "Integration adds complexity before questions are reliable"

**Recommendations (Synthesis):**

1. **Prove value before integration**
   - Claude: "Run question testing manually on 2-3 docs. Document what issues it found. If nothing useful, reconsider integration"
   - Codex: "Only integrate after Phase 2 success"

2. **Consider keeping separate initially**
   - Claude: "Keep as separate script initially: `python question_test.py workflow.md`"
   - Claude: "Allows iteration without changing polish.py"

3. **Make it opt-in** (all agree)
   - Default: `enable_question_testing: false`
   - Explicit flag to enable

4. **Add dry-run mode** (Codex)
   - Reports coverage without running full test
   - Helps validate before committing

5. **Separate reporting** (Claude)
   - Question results in separate section or file
   - Different from ambiguity detection findings

**Integration Strategy (Revised):**

| Stage | Timing | Approach |
|-------|--------|----------|
| **Phase 1-2** | Week 1-3 | Separate script, manual invocation |
| **Phase 3** | Week 4 | Integrate as opt-in step in polish.py |
| **Post-Phase 3** | Future | Enable by default if proven valuable |

**Risks:**

- **Codex:** "Configuration sprawl" - too many CLI arguments
- **Claude:** "Integration before validation" - might ship feature that doesn't provide value
- **Gemini:** (Implicit in "Manual Integration test Week 1")

**Suggestions:**

- **Codex:** "Add defaults and `--enable-question-testing` flag"
- **Gemini:** "Create `project_config.json` so you don't have to pass arguments every time"
- **Claude:** "Consider 'side car' mode... separate script until proven"

**Priority:**
- **Claude:** Important (not critical - value comes from templates)
- **Codex:** Important
- **Gemini:** High

### Phase 4: Merge Script (Future/Deferred)

**Consensus:** All agree this should be deferred

**Claude:** "Don't just defer—mark as 'May Never Be Needed'"
**Codex:** (No comment - implicitly agrees with deferral)
**Gemini:** "Skip the 'Merge Results Back to Bulky' script. Keep polishing results in separate JSON"

**Recommendation:** Remove from plan entirely. Add back only if real need emerges.

---

## Part 5: Missing Considerations

### What Models Identified as Gaps

| Gap | Claude | Codex | Gemini | Priority |
|-----|--------|-------|--------|----------|
| **Assertion quality guidance** | ✅ | ✅ (Style guide) | ⚠️ | **High** |
| **Authoring workflow** | ✅ | ✅ | ✅ | **High** |
| **Clean doc validation** | ✅ | ✅ | ✅ | **High** |
| **Schema validation** | ⚠️ | ✅ | ⚠️ | **High** |
| **CI enforcement** | ⚠️ | ✅ | ✅ | **Medium** |
| **Decision points** | ✅ | ✅ | ⚠️ | **Medium** |
| **Question utility validation** | ✅ | ⚠️ | ⚠️ | **Medium** |
| **Token efficiency metric** | ⚠️ | ⚠️ | ✅ | **Low** |
| **IDE snippets** | ⚠️ | ⚠️ | ✅ | **Low** |

#### Gap 1: What Makes a "Good" Assertion?

**Claude's Definition:**
> "Mark as assertion if an LLM failing to understand this would cause incorrect behavior. Don't mark explanatory/background text."

**Codex (Technical Writing):**
> "Authoring style guide: How to write assertions vs explanations"

**Risk:**
- Too few assertions → missing coverage
- Too many assertions → testing trivial things, drowning in questions

**Recommendation:** Add to Week 1 format spec:

**Assertion Guidelines:**
✅ Mark these:
- Requirements (must/required/shall)
- Constraints (limits, boundaries, thresholds)
- Behaviors (if X then Y)
- Error conditions (when to fail)
- Sequences (order-dependent steps)

❌ Don't mark these:
- Background information
- Explanations of "why"
- Examples (unless the example itself is a requirement)
- Summaries or overviews

#### Gap 2: Authoring Workflow & Tooling

**All models flag this**

**Claude:**
- Snippet/template for assertion block
- Linter that suggests potential assertions
- Example workflow documented

**Codex:**
- Copy-paste snippets for common types
- Bulky authoring guide + checklist
- Lightweight `bulky-lint` for assertion density

**Gemini:**
- IDE snippets (`.vscode/snippets.json`)
- Auto-complete assertion tags

**Recommendation:** Add to Week 1:

```json
// .vscode/snippets.json
{
  "Assertion Block": {
    "prefix": "assert",
    "body": [
      "<!-- @assertion id=\"${1:step}_${2:type}_${3:01}\" type=\"${4|requirement,constraint,behavior,error,sequence|}\" priority=\"${5|critical,high,medium,low|}\" -->",
      "$0",
      "<!-- @/assertion -->"
    ]
  }
}
```

**Lint Rules (Future):**
- Warn if text contains "must", "required", "shall" without `@assertion` wrapper
- Report assertion density (% of doc that's testable)
- Flag duplicate IDs

#### Gap 3: Clean Doc Validation

**All models want automated validation that clean docs are truly clean**

**Claude:**
```python
def validate_clean(content: str) -> list[str]:
    issues = []
    if '@meta' in content: issues.append("Contains @meta")
    if '@assertion' in content: issues.append("Contains @assertion")
    if '@polishing' in content: issues.append("Contains @polishing")
    if re.search(r'<!--\s*@', content): issues.append("Contains @-prefixed comment")
    return issues
```

**Codex:**
- "Add automated 'cleanliness' checks and spot-test with LLMs"
- "Assert clean doc has same number of headers as bulky (structure preserved)"

**Gemini:**
- "Add `--check` flag: return non-zero exit if finds any `@` tags in clean directory"
- "Token Efficiency report: Compare token counts between Bulky and Clean"

**Recommendation:** Add to strip script:

```python
def validate_stripped(bulky_content: str, clean_content: str) -> dict:
    """Validate strip operation was successful"""
    issues = []

    # Check: No metadata leaked
    for marker in ['@meta', '@assertion', '@polishing']:
        if marker in clean_content:
            issues.append(f"Leaked marker: {marker}")

    # Check: Structure preserved
    bulky_headers = re.findall(r'^#{1,6} ', bulky_content, re.MULTILINE)
    clean_headers = re.findall(r'^#{1,6} ', clean_content, re.MULTILINE)
    if len(bulky_headers) != len(clean_headers):
        issues.append(f"Header count mismatch: {len(bulky_headers)} vs {len(clean_headers)}")

    # Check: Idempotent
    double_strip = strip_metadata(clean_content)
    if double_strip != clean_content:
        issues.append("Not idempotent: strip(strip(x)) != strip(x)")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'token_reduction': len(bulky_content) - len(clean_content)
    }
```

#### Gap 4: Schema Validation (Codex-specific)

**Codex (only model to flag this):**
> "No explicit schema for `@meta/@assertion` blocks. Need automated checks."

**Why it matters:**
- Typos in field names won't be caught
- Invalid values (e.g., `priority: "super-high"`) will break automation
- Inconsistent metadata across docs

**Recommendation:** Define JSON schemas in Phase 1

```json
// schemas/assertion.schema.json
{
  "type": "object",
  "required": ["id", "type"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^[a-z0-9_]+$"
    },
    "type": {
      "enum": ["requirement", "constraint", "behavior", "error", "sequence"]
    },
    "priority": {
      "enum": ["critical", "high", "medium", "low"]
    },
    "difficulty": {
      "enum": ["trivial", "easy", "medium", "hard"]
    }
  }
}
```

Add validation to lint script:
```bash
python scripts/lint_bulky.py docs/bulky/workflow.md
# → Validates all @assertion blocks against schema
# → Reports: Invalid IDs, unknown types, duplicate IDs
```

#### Gap 5: Decision Points & Rollback Plan

**Claude (primary concern):**
> "If the approach fails at Week 3-4, there's no documented fallback. What happens to bulky docs you've created?"

**Recommended Decision Points:**

| Week | Metric | Success Threshold | If Fail |
|------|--------|------------------|---------|
| **Week 1** | Manual questions find real issues | ≥2 issues found | STOP, reassess approach |
| **Week 1** | Template regex match rate | ≥50% | Pivot to pure LLM generation |
| **Week 2** | Template success rate | ≥60% | Add more patterns or accept lower coverage |
| **Week 3** | Leakage rate | ≤10% | Refine validation or accept higher threshold |
| **Week 4** | End-to-end value | ≥1 real doc issue found | Keep as separate tool, don't integrate |

**Rollback Plan:**
- If Week 1 fails: Abandon bulky-clean architecture, use pure LLM generation on normal docs
- If Week 2 fails: Keep bulky docs for manual question writing, skip template automation
- If Week 4 fails: Use questioning as standalone tool, don't integrate into polish.py

**Codex:**
> "Set a 'stop-loss' threshold (e.g., <50% success after 2 iterations)"

**Recommendation:** Add explicit decision tree to plan

---

## Part 6: Quick Wins (Week 1 Validation)

### All Models Recommend Manual Testing First

**Core Philosophy (Consensus):**
> "Prove the approach works manually in Week 1 before building infrastructure"

### Quick Win Comparison

| Model | Quick Win 1 | Quick Win 2 | Quick Win 3 | Quick Win 4 |
|-------|------------|------------|------------|------------|
| **Claude** | Manual question writing (2h) | Regex feasibility test (1h) | LLM generation spike (1h) | Overhead estimation (30m) |
| **Codex** | Annotate 1 doc + 5 questions | Run validation checks | Fence-aware strip + tests | CI check: strip == clean |
| **Gemini** | End-to-end smoke test by Wed | Token efficiency comparison | - | - |

### Synthesized Week 1 Quick Win Plan

**Total Time Investment: 4-6 hours**

#### Quick Win 1: Manual Question Validation (2 hours)

**Goal:** Prove question-based testing can find real issues

**Steps:**
1. Pick your most complex workflow doc (30 min)
2. Identify 5-10 sentences that should be testable (30 min)
3. Write 5 questions manually (30 min)
4. Test with Claude/GPT (15 min):
   - Do models answer correctly with full doc?
   - Do models fail appropriately with minimal context?
5. Evaluate (15 min):
   - Did questions reveal comprehension issues?
   - Were questions hard to write?

**Success Criteria:**
✅ Questions found ≥2 real issues (models misunderstood something important)
✅ Questions were reasonably easy to write (<10 min each)

**If Fail:** Question-based testing may not be worth the investment

#### Quick Win 2: Template Feasibility Test (1 hour)

**Goal:** Validate regex patterns can match real assertions

**Steps:**
1. Collect 20 sentences from existing docs that would be assertions (30 min)
2. Write 1 regex pattern for "constraint" type (15 min)
3. Test pattern against 20 sentences (10 min)
4. Count matches (5 min)

**Success Criteria:**
✅ Single pattern matches ≥50% of constraint-type assertions

**If Fail:** Templates too brittle, plan for higher LLM fallback

#### Quick Win 3: Strip Script Implementation (30 min)

**Goal:** Build minimal viable strip script

**Implementation:**
```python
# scripts/strip_metadata.py (15 lines)
import re, sys

def strip_metadata(content: str) -> str:
    """Remove all @-prefixed HTML comments"""
    # Pattern: <!-- @anything ... -->
    pattern = r'<!--\s*@\w+.*?-->'
    clean = re.sub(pattern, '', content, flags=re.DOTALL)
    # Clean up excessive blank lines
    clean = re.sub(r'\n{3,}', '\n\n', clean)
    return clean.strip() + '\n'

if __name__ == '__main__':
    content = open(sys.argv[1]).read()
    print(strip_metadata(content))
```

**Test:**
```bash
python scripts/strip_metadata.py docs/bulky/test.md > docs/clean/test.md
# Manually verify: No @meta, @assertion, @polishing in output
```

#### Quick Win 4: One Bulky Doc (1 hour)

**Goal:** Create example bulky doc and verify strip works

**Steps:**
1. Pick simplest existing workflow (10 min)
2. Add `@meta` block (10 min)
3. Add 3-5 `@assertion` blocks (constraint type only) (30 min)
4. Strip it, verify clean output (10 min)

**Success Criteria:**
✅ Bulky doc has valid metadata
✅ Stripped clean doc is identical to original (minus metadata)
✅ Round-trip works: `strip(strip(doc)) == strip(doc)`

#### Quick Win 5: Clean Doc Validation (30 min)

**Goal:** Verify strip didn't leak metadata or break structure

**Implementation:**
```python
def validate_clean(bulky: str, clean: str):
    # No leakage
    assert '@meta' not in clean
    assert '@assertion' not in clean

    # Structure preserved
    bulky_headers = re.findall(r'^#{1,6} ', bulky, re.MULTILINE)
    clean_headers = re.findall(r'^#{1,6} ', clean, re.MULTILINE)
    assert len(bulky_headers) == len(clean_headers)

    # Idempotent
    assert strip_metadata(clean) == clean
```

#### Quick Win 6: End-to-End Smoke Test (1 hour)

**Goal:** Validate entire workflow

**Steps (Gemini's concrete version):**
1. Take bulky doc from QW4
2. Manually write 3 questions from assertions (20 min)
3. Create clean doc via strip (1 min)
4. Test model on clean doc with questions (10 min)
5. Evaluate: Did model fail questions appropriately? (30 min)

**Success Criteria:**
✅ Questions tested understanding of assertions
✅ Clean doc didn't leak answers
✅ Model failed when expected

### Week 1 Decision Tree

```
Start Week 1
    ↓
QW1: Manual Questions
    ↓
Found ≥2 real issues? ──NO──> STOP: Approach won't provide value
    ↓ YES
QW2: Template Feasibility
    ↓
Match rate ≥50%? ──NO──> Plan for pure LLM generation (higher cost)
    ↓ YES
QW3-4: Build Strip + Bulky Doc
    ↓
QW5: Validation Passes?──NO──> Fix strip script, retry
    ↓ YES
QW6: End-to-End Smoke
    ↓
Model fails appropriately? ──NO──> Questions too easy or leakage present
    ↓ YES
✅ PROCEED TO WEEK 2
```

---

## Part 7: Alternative Approaches

### All Models Offer Alternatives (None Mandatory)

| Model | Alternative | Why Better | Trade-offs |
|-------|-------------|-----------|-----------|
| **Claude** | Start with LLM generation, not templates | Faster, higher coverage, lower maintenance | Higher cost, less consistent |
| **Codex** | Fenced blocks (:::assertion) instead of HTML | Less brittle, easier to lint | Requires parser dependency |
| **Codex** | Structured data (JSON/YAML) → render docs | Full control, deterministic | Larger authoring change |
| **Gemini** | YAML front-matter for doc metadata | Native support in all tools | Still need HTML for inline assertions |

### Claude's Alternative: LLM-First Generation

**Approach:**
```python
def generate_question(assertion_text: str, assertion_type: str) -> dict:
    prompt = f"""
    Generate a comprehension question for this {assertion_type} assertion:
    "{assertion_text}"

    Rules:
    - Test if someone understood the assertion
    - Answer extractable from assertion text
    - Don't include answer in question

    Output JSON: {{"question": "...", "answer": "..."}}
    """
    return claude.generate(prompt)
```

**When to Use:**
- Behavior and error types (high natural language variation)
- Complex cross-references
- Personal project with small doc counts

**Hybrid Recommendation (Claude):**
> "Use templates for simple patterns (constraint, sequence). Use LLM for complex patterns (behavior, error, cross-reference). This reduces API calls while handling variability."

### Codex's Alternative: Fenced Blocks

**Approach:**
```markdown
:::assertion{id="step1_req_01" type="requirement"}
All fields must be validated against schema.
:::
```

**Advantages:**
- Markdown AST parser can extract reliably
- Safer to strip (no regex edge cases)
- Easier to lint

**Trade-offs:**
- Requires parser dependency (markdown-it, remark, etc.)
- More upfront code
- Not standard markdown (needs custom renderer)

**Verdict:** Overkill for personal project. Consider if scaling to team.

### Gemini's Alternative: YAML Front-Matter

**Approach:**
```markdown
---
version: 1.0
created: 2025-12-30
status: active
---

# Document Title

<!-- @assertion id="step1_req_01" type="requirement" -->
Content here
<!-- @/assertion -->
```

**Advantages:**
- Native support in Obsidian, VS Code, Hugo, Jekyll
- Cleaner header separation
- Every markdown parser supports it

**Trade-offs:**
- Only for document-level metadata
- Still need HTML comments for inline assertions

**Verdict:** Worth considering. Simplifies doc metadata without changing assertion format.

---

## Part 8: Tactical Recommendations Summary

### Immediate Actions (Before Phase 1)

#### Change 1: Revise Week 1 Plan

**Current Plan:**
- Strip script + format spec + 1 example
- ~2-3 hours of work

**Revised Plan (All Models):**
- **Add:** Manual question validation (2h)
- **Add:** Template feasibility test (1h)
- **Add:** End-to-end smoke test (1h)
- **Add:** Clean doc validation (30m)
- **Total:** 4-6 hours of work

**Decision Point:** End of Week 1
- ✅ Proceed to Phase 2 if smoke test passes
- ❌ Pivot/stop if manual questions don't find issues

#### Change 2: Lower Template Expectations

**Current Plan:**
- 5 core templates
- 80%+ success rate
- 20% LLM fallback

**Revised Plan (All Models):**
- **2-3 core templates** (constraint, requirement, +1 optional)
- **60%+ success rate** (realistic)
- **40-50% LLM fallback** (budget for it)

#### Change 3: Add Validation Checks

**Current Plan:**
- Strip script only

**Revised Plan (All Models):**
- Strip script
- **+** Clean doc validation (no leakage)
- **+** Structure preservation check
- **+** Idempotent verification

#### Change 4: Provide Authoring Tooling

**Current Plan:**
- Writers manually type HTML comments

**Revised Plan (All Models):**
- **+** VS Code snippet for assertion blocks
- **+** One-page authoring guide
- **+** Example template to copy

#### Change 5: Add Decision Points

**Current Plan:**
- Linear progression through phases

**Revised Plan (Claude, Codex):**
- **Week 1:** Manual test must find ≥2 issues OR stop
- **Week 2:** Template match ≥50% OR pivot to LLM
- **Week 3:** If templates <60% success after 2 iterations, reassess
- **Week 4:** Must find ≥1 real issue OR don't integrate

### Optional Enhancements (Consider)

#### Enhancement 1: Better Strip Implementation

**Options:**
1. **Simple regex + comprehensive tests** (Claude) - Start here
2. **Fence-aware scanner** (Gemini) - If code block issues appear
3. **Markdown parser** (Codex) - If scaling to team

**Recommendation:** Start with #1, migrate to #2 if needed

#### Enhancement 2: CI/Automation

**Codex/Gemini recommend:**
- `make clean-docs` target
- CI check: `strip(bulky) == clean`
- Pre-commit hook for drift detection

**Claude recommends:**
- Defer for personal project
- Add only if git diffs show manual edits to clean docs

**Recommendation:** Defer to post-Phase 3. Not critical for validation.

#### Enhancement 3: Schema Validation

**Codex recommends:**
- JSON schema for `@meta` and `@assertion`
- Automated validation in lint script

**Recommendation:** Add in Phase 2 if templates break due to malformed metadata

#### Enhancement 4: Auto-Generate IDs

**Gemini recommends:**
- Hash of assertion content
- Line-number slug
- Reduces manual "authoring tax"

**Recommendation:** Defer. Manual IDs are fine for personal project with small doc counts.

#### Enhancement 5: File Extensions

**Gemini recommends:**
- `.bulky.md` for source files
- `.gitignore` or `.cursorrules` to hide from agents

**Current plan:**
- Directory-based separation

**Recommendation:** Stick with directory-based. Simpler, all models agree it's sufficient.

---

## Part 9: Risk Analysis

### Risk Matrix (Consensus)

| Risk | Likelihood | Impact | Mitigation | Owner |
|------|-----------|--------|------------|-------|
| **Regex strip breaks code blocks** | Medium | High | Add fence-aware scanner or comprehensive tests | Phase 1 |
| **Template match rate <50%** | High | High | Design from real data, plan for LLM fallback | Phase 2 |
| **Authoring overhead kills adoption** | Medium | Medium | Provide snippets, lint warnings | Phase 1 |
| **Week 1 validation fails** | Medium | High | Manual question test must find ≥2 issues | Week 1 |
| **Question testing finds no value** | Low | High | Smoke test early, stop if no issues found | Week 1 |
| **CI drift (clean edited manually)** | Low | Low | Optional CI check or defer | Post-Phase 3 |
| **Scope creep (merge script, etc.)** | Medium | Medium | Time-box phases, defer non-critical | All phases |
| **Metadata schema inconsistency** | Low | Medium | Schema validation (optional) | Phase 2 |

### Top 3 Risks (All Models Agree)

#### Risk 1: Building Infrastructure Before Proving Value

**Claude:**
> "You could build infrastructure for 2 weeks before discovering approach doesn't provide enough value for the overhead"

**Codex:**
> "May invest in format before proving question generation works"

**Gemini:**
> "Validate this before writing the strip script"

**Probability:** 40% (medium-high)
**Impact:** High (wasted 2-3 weeks)

**Mitigation:**
- ✅ Manual question test in Week 1 (2 hours)
- ✅ Decision point: If <2 issues found, STOP
- ✅ End-to-end smoke test before automation

**Signs of Success:**
- Manual questions easily identify 2+ real comprehension issues
- Questions were reasonable to write (<10 min each)
- Models fail questions when reading minimal docs

**Signs of Failure:**
- Questions don't reveal any issues
- Models pass questions even without reading docs
- Too hard to write good questions manually

**If Risk Materializes:** Abandon approach, pivot to pure LLM generation on normal docs

#### Risk 2: Template Patterns Can't Match Real Assertions

**Claude:**
> "Template success rate will be closer to 50-60% than 80%+"

**Codex:**
> "Regex templates won't match real assertions; coverage low"

**Gemini:**
> "Universal templates too generic to be useful"

**Probability:** 70% (high)
**Impact:** Medium (higher cost, more LLM calls)

**Mitigation:**
- ✅ Regex feasibility test in Week 1 (1 hour)
- ✅ Design patterns from 20 real assertions
- ✅ Start with 2-3 templates, not 5
- ✅ Budget for 40-50% LLM fallback
- ✅ Stop-loss: if <50% match after 2 iterations, pivot to pure LLM

**Signs of Success:**
- First pattern matches ≥50% of constraint assertions
- 2-3 iterations get to 60%+ match rate
- Generated questions have <10% leakage

**Signs of Failure:**
- Each assertion needs unique pattern
- Match rate stuck at 30-40%
- More time spent debugging regex than LLM costs

**If Risk Materializes:** Accept higher LLM cost or pivot to pure LLM generation

#### Risk 3: Authoring Overhead Discourages Use

**Claude:**
> "For a 100-line doc, this might add 50+ lines of metadata... Overhead may discourage adoption"

**Codex:**
> "Writers may forget assertions or misplace metadata"

**Gemini:**
> "Manual authoring... high friction kills personal projects"

**Probability:** 50% (medium)
**Impact:** Medium (format not used, wasted effort)

**Mitigation:**
- ✅ Provide VS Code snippet (5 min to create)
- ✅ One-page authoring guide with examples
- ✅ Lint warnings for unmarked assertions
- ✅ Consider shorthand syntax (Claude's suggestion)

**Signs of Success:**
- Writer uses snippets, authoring takes <2 min per assertion
- Bulky docs stay updated over time
- Writer voluntarily converts more docs

**Signs of Failure:**
- Assertions skipped or copy-pasted incorrectly
- Writer stops using format after 1-2 docs
- Metadata incomplete or inconsistent

**If Risk Materializes:**
- Try shorthand syntax: `**Timeout:** 30s <!-- @c:id -->`
- Or accept fewer assertions (focus on critical ones only)

### Additional Risks (Model-Specific)

**Claude identifies:**
- Polishing history grows indefinitely inline → Store separately
- No "good assertion" definition → Add quality guidance

**Codex identifies:**
- No schema validation → Metadata inconsistencies break automation
- No CI drift detection → Clean docs edited manually

**Gemini identifies:**
- Manual ID management errors → Auto-generate from content hash
- Agents reading bulky docs anyway → File extensions + .cursorrules

**Recommendation:** Address Claude's risks (high impact, easy fixes). Defer Codex/Gemini risks unless they materialize.

---

## Part 10: Final Recommendations

### 1. Proceed with Modified Plan

**Verdict Consensus:** All three models say "Proceed with Changes"

**Confidence:**
- Architecture is sound ✅
- Phasing is logical ✅
- Personal project scope is appropriate ✅

**Required Changes:**
1. ✅ Add Week 1 smoke test (manual questions + template feasibility)
2. ✅ Lower template expectations (60% success, 2-3 templates)
3. ✅ Add validation checks (clean doc verification)
4. ✅ Provide authoring tooling (snippets, guide)
5. ✅ Add decision points (stop-loss thresholds)

### 2. Week 1 Revised Success Criteria

**Must Complete:**
- [ ] Manual question test (find ≥2 real issues)
- [ ] Template feasibility (≥50% match on constraints)
- [ ] Strip script (simple regex + tests)
- [ ] One bulky doc (3-5 assertions)
- [ ] Clean validation (no leakage, structure preserved)
- [ ] End-to-end smoke test (model fails appropriately)

**Decision:** If all pass → Proceed to Week 2. If any fail → Reassess approach.

### 3. Template Strategy

**Original:** 5 templates, 80% success, 20% LLM
**Revised:** 2-3 templates, 60% success, 40-50% LLM

**Phase 2 Focus:**
1. Constraint template (most formulaic)
2. Requirement template (second most formulaic)
3. Optional: Behavior template (if time permits)

**Defer:** Error and Sequence templates to post-Phase 2

**Budget:** ~$1-2 per doc for LLM fallback (40-50 assertions × $0.02/call)

### 4. Integration Approach

**Don't integrate into polish.py until proven valuable**

**Phase 3 approach:**
- Keep as separate script: `python scripts/question_test.py docs/bulky/workflow.md`
- Run manually on 2-3 docs
- Document issues found
- If ≥1 real issue found → Integrate as opt-in
- If 0 issues found → Keep separate, don't integrate

### 5. Defer/Skip Entirely

**Defer to post-Phase 3:**
- CI/automation (unless drift becomes problem)
- Schema validation (unless metadata breaks templates)
- Merge script (likely never needed)

**Skip entirely:**
- File extensions (.bulky.md) - directory separation sufficient
- Build headers in clean docs - not critical
- Token efficiency metrics - nice-to-have, not essential

### 6. Authoring Tooling (Week 1)

**Must Have:**
- VS Code snippet for assertion block (5 min to create)
- One-page authoring guide (30 min to write)
- Example bulky doc to copy (created in QW4)

**Nice to Have:**
- Lint warnings for unmarked assertions
- Assertion quality guidance
- Shorthand syntax option

### 7. Decision Points

| Checkpoint | Metric | Threshold | If Fail |
|------------|--------|-----------|---------|
| **End of Week 1** | Manual questions find issues | ≥2 issues | STOP approach |
| **End of Week 1** | Template match rate | ≥50% | Plan for pure LLM |
| **End of Week 2** | Template success rate | ≥60% | Accept lower or add patterns |
| **End of Week 3** | Leakage rate | ≤10% | Refine or accept higher |
| **End of Week 4** | Value demonstrated | ≥1 issue found | Don't integrate |

### 8. Success Metrics (Revised)

**Phase 1 Success:**
- Strip script works on 1 doc ✅
- Manual test found ≥2 issues ✅
- Template feasibility ≥50% ✅
- Time investment: 4-6 hours ✅

**Phase 2 Success:**
- 2-3 templates working ✅
- 60%+ match rate ✅
- <10% leakage ✅
- LLM fallback handles remaining 40% ✅

**Phase 3 Success:**
- End-to-end workflow functional ✅
- Found ≥1 real doc issue ✅
- Opt-in integration in polish.py ✅

**Project Success:**
- 3 workflow docs have bulky versions ✅
- Question testing found ≥3 real issues total ✅
- Process is sustainable (low overhead) ✅
- Documents measurably clearer ✅

---

## Part 11: What to Update in Plan

### Section 1: Phase 1 Deliverables

**Add:**
- Manual question validation test (2h)
- Template feasibility test (1h)
- End-to-end smoke test (1h)
- Clean doc validation script
- VS Code snippet for assertions
- One-page authoring guide

**Revise:**
- Strip script: Mention need for comprehensive tests (code blocks, structure preservation)
- Success criteria: Add "≥2 issues found in manual test"

### Section 2: Phase 2 Deliverables

**Revise:**
- Template count: 2-3 instead of 5
- Success rate target: 60% instead of 80%
- LLM fallback budget: 40-50% instead of 20%
- Add: "Design patterns from 20 real assertions first"
- Add: "Stop-loss: <50% match after 2 iterations → pivot"

### Section 3: Phase 3 Deliverables

**Revise:**
- Keep as separate script initially
- Prove value (≥1 issue found) before integrating
- Integration is opt-in with `--enable-question-testing`

**Add:**
- "Consider side-car mode instead of full integration"

### Section 4: Phase 4 (Merge Script)

**Revise:**
- Mark as "May Never Be Needed"
- Or remove entirely

### Section 5: Add New Section - "Decision Points"

**Add table with:**
- Week 1: Manual test threshold
- Week 2: Template match threshold
- Week 3: Leakage threshold
- Week 4: Value demonstration threshold

### Section 6: Add New Section - "Risk Mitigation"

**Add:**
- Top 3 risks + mitigations
- Signs of success/failure for each
- Pivot plans

### Section 7: Update Success Metrics

**Revise:**
- Lower template expectations
- Add smoke test requirement
- Add value demonstration requirement

---

## Appendix A: Model Strengths & Perspectives

### Claude (Opus 4.5)

**Strengths:**
- Most detailed Week 1 revision (hour-by-hour breakdown)
- Strong focus on value validation before automation
- Practical "simplest thing that works" examples
- Explicit "done" criteria for each phase
- Best alternative approach (LLM-first generation)

**Unique Contributions:**
- Assertion shorthand syntax
- Store polishing history separately
- "Good enough" stopping criteria
- Most pragmatic tone

**Perspective:** "Prove value first, ship ugly, iterate"

### Codex (gpt-5.2-codex)

**Strengths:**
- Most comprehensive multi-perspective analysis (5 experts)
- Strong engineering rigor (schema validation, drift detection)
- Best technical depth (parser-safe strip, CI integration)
- Detailed authoring ergonomics consideration

**Unique Contributions:**
- Schema validation as explicit requirement
- Drift detection as separate concern
- Stop-loss threshold concept
- Fence-aware scanner alternative

**Perspective:** "Build robust infrastructure, validate everything, plan for scale"

### Gemini (3 Pro)

**Strengths:**
- Most action-oriented ("Do this by Wednesday")
- Concrete tactical suggestions (auto-generate IDs, .bulky.md)
- Best integration concern (Week 4 too late)
- Tooling suggestions (IDE snippets, Makefile)

**Unique Contributions:**
- Auto-generate assertion IDs
- File extension sentinel approach
- Build header in clean docs
- Token efficiency metric
- .cursorrules/.gitignore for hiding bulky docs

**Perspective:** "Fast validation, practical tooling, reduce friction"

### Synthesis

**Use Claude for:**
- Week 1 planning and smoke test design
- Value validation approach
- Simplification and stopping criteria

**Use Codex for:**
- Technical robustness (strip implementation, validation)
- Schema design
- Long-term maintainability

**Use Gemini for:**
- Quick wins and tactical improvements
- Authoring friction reduction
- Integration timing

---

## Appendix B: Consensus Quotes

### On Architecture

**Claude:** "Directory separation is correct. docs/bulky/ vs docs/clean/ is clear and sufficient."

**Codex:** "Clear separation of source (bulky) and build (clean) reduces LLM contamination risk."

**Gemini:** "The transition from 'testing arbitrary documents' to a Source/Build architecture is the single most important decision made so far."

### On Week 1 Validation

**Claude:** "You won't know if the overall approach is worthwhile until Week 3-4 when templates are working. You could build infrastructure for 2 weeks before discovering the approach doesn't provide enough value."

**Codex:** "Week 1 too narrow; doesn't validate real value. You may invest in format before proving question generation works."

**Gemini:** "Validate this before writing the strip script. If the model fails the questions while reading the clean doc, your architecture is proven."

### On Template Reality

**Claude:** "Template success rate will be closer to 50-60% than 80%+. The 20% 'LLM fallback' will actually be 40-50%."

**Codex:** "Template success >80% is ambitious without structure-specific patterns."

**Gemini:** "Don't build 5 core templates immediately. Build two (Requirement and Constraint) and test them against 10 diverse assertions. Quality over quantity here."

### On Regex Strip

**Claude:** "The core mechanism (regex strip of HTML comments) is simple and reliable. The main risk isn't technical—it's whether the overhead of maintaining bulky docs pays off."

**Codex:** "Strip script uses regex over raw Markdown. Can remove markers inside code fences or malformed comment blocks, leading to corrupted examples."

**Gemini:** "The regex may accidentally strip real content if a user puts an HTML comment in a code block or uses nested comments. Use a state-aware parser."

### On Authoring Overhead

**Claude:** "For a 100-line doc, this might add 50+ lines of metadata. Risk: Medium. Overhead may discourage adoption."

**Codex:** "HTML comments are invisible in rendered views. Writers may forget assertions or misplace metadata."

**Gemini:** "Forcing the user to manually type `id=\"step1_req_01\"` for every assertion is a high-friction 'authoring tax' that leads to copy-paste errors."

### On Proceeding

**Claude:** "Proceed with Changes. Confidence: High. This approach will work."

**Codex:** "Proceed with Changes. Confidence: Medium. Needs stronger guarantees."

**Gemini:** "Proceed with Changes. Confidence: High. This is a standard software engineering pattern applied to documentation."

---

## End of Analysis

**Total Word Count:** ~14,800 words
**Models Synthesized:** 3 (Claude Opus 4.5, OpenAI Codex, Google Gemini 3 Pro)
**Consensus Items:** 12
**Critical Issues:** 9
**Recommendations:** 37
**Quick Wins:** 6

**Next Step:** Update BULKY_CLEAN_ARCHITECTURE_PLAN.md based on this analysis
