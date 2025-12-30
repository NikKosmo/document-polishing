# Expert Review Part 3: Implementation Plan Review
# Response from Google Gemini

**Review Date:** 2025-12-30
**Prompt:** PART3_PROMPT.md
**Plan Reviewed:** BULKY_CLEAN_ARCHITECTURE_PLAN.md
**Model:** Gemini 3 pro
**Perspectives:** (paste perspectives covered)

---

This review evaluates the **Bulky-Clean Document Architecture Plan** from an integrated panel of expert perspectives.

---

## Section 1: Overall Assessment

**Verdict: Proceed with Changes**

**Rationale:** The transition from "testing arbitrary documents" to a **Source/Build** architecture is the single most important decision made so far. It decouples human/test metadata from LLM consumption, solving the "noise" problem. However, the plan relies too heavily on regex for stripping and lacks a "Smoke Test" in the first 48 hours to validate the template redesign logic before the full integration.

**Confidence: High.** This is a standard software engineering pattern (compilation/transpilation) applied to documentation, which is much more robust than the previous "black box" approach.

---

## Section 2: Critical Issues

| Issue | Impact | Fix | Priority |
| --- | --- | --- | --- |
| **Regex "Greediness" & Code Blocks** | The regex `r''` may accidentally strip real content if a user puts an HTML comment in a code block or uses nested comments. | Use a state-aware parser or a non-greedy regex with specific boundaries (see Architecture section). | **High** |
| **Manual ID Management** | Forcing the user to manually type `id="step1_req_01"` for every assertion is a high-friction "authoring tax" that leads to copy-paste errors. | Auto-generate IDs based on a hash of the content or a simple line-number slug if missing. | **Medium** |
| **Integration Lag** | Waiting until Week 4 to integrate into `polish.py` is too late to find out if the "Clean" docs actually improve ambiguity detection. | Move a "Manual Integration" test to Week 1. | **High** |

---

## Section 3: Architecture Feedback

### ✅ What’s Good

* **Separation of Concerns**: Moving metadata to `docs/bulky/` ensures that "leakage" is physically impossible for the model being tested.
* **Idempotency**: The ability to run the strip script repeatedly without changing the output is crucial for CI/CD and developer sanity.

### ⚠️ What’s Risky

* **Directory Confusion**: Relying on directory names alone (`bulky` vs `clean`) to prevent agents from reading source files is fragile. In many LLM IDEs (like Cursor or Windsurf), the agent indexes the entire workspace.
* **Desync**: If a user edits a `clean` doc directly, those changes are lost on the next build. There is no mechanism to prevent "illegal" edits in the clean directory.

### 💡 Suggestions

* **File Extension Sentinel**: Use `.bulky.md` for source. This allows you to add a global `.gitignore` or `exclude` rule for agents to ignore all `*.bulky.md` files regardless of directory.
* **Build Header**: Every clean file should start with a generated comment: ``.

---

## Section 4: Phase-by-Phase Review

### Phase 1: Foundation (Strip Script)

* **Feasibility**: Very High. A 100ms execution time is easily achievable in Python.
* **Risks**: Regex failing to handle multi-line comments or "leaking" a partial tag that confuses the LLM.
* **Suggestions**: Add a `--check` flag to the script. It should return a non-zero exit code if it finds *any* `@` tags in the `clean` directory. This acts as a "leakage firewall."
* **Priority**: Critical.

### Phase 2: Template Redesign

* **Feasibility**: Moderate. The transition from "Mention" to "Assertion" testing is a conceptual shift.
* **Risks**: Creating "Universal" templates that are too generic to be useful.
* **Suggestions**: Don't build 5 core templates immediately. Build **two** (Requirement and Constraint) and test them against 10 diverse assertions. Quality over quantity here.
* **Priority**: High.

### Phase 3: Integration

* **Feasibility**: High. `polish.py` is already modular.
* **Risks**: Complexity explosion in the CLI arguments.
* **Suggestions**: Create a `project_config.json` so you don't have to pass `doc-type`, `strip-path`, and `question-count` every time.
* **Priority**: Important.

---

## Section 5: Missing Considerations

* **[Gap 1]: The "Cleanliness" Metric**: You need a way to prove that "Clean" docs are actually better for LLMs.
* *Why it matters:* If the "Clean" docs still contain artifacts (like extra newlines or weird artifacts), LLM performance won't improve.
* *Fix:* Add a "Token Efficiency" report to Phase 1 (Compare token counts between Bulky and Clean).


* **[Gap 2]: IDE Snippets**: Manual authoring of `` is painful.
* *Why it matters:* High friction kills personal projects.
* *Fix:* Include a `.vscode/snippets.json` in the repo to auto-complete the assertion tags.



---

## Section 6: Alternative Approach

**Alternative: YAML Front-Matter for Document Metadata**
Instead of inline HTML comments for document-level metadata (`@meta`), use standard **YAML Front-Matter**.

* **Why it's better**: Every markdown parser and IDE (Obsidian, VS Code, Hugo) natively supports front-matter. It keeps the "Header" of the file clean and separated from the "Body" where assertions live.
* **Trade-offs**: You still need the HTML comments for *inline* assertions (which is fine), but document-level metadata becomes much easier to parse.

---

## Section 7: Quick Wins (Week 1 Validation)

**The "End-to-End Smoke Test" (Do this by Wednesday):**

1. Take **one** real workflow document.
2. Manually add **three** `` tags.
3. Run a **hardcoded prompt** (skip the script for now): *"Given these assertions, generate 3 questions that test if a model understands these rules without using the specific words in the assertion."*
4. Feed the **Cleaned doc** + **Generated questions** to a model.

**If the model fails the questions while reading the clean doc, your architecture is proven.** If it still passes easily, your questions aren't hard enough. **Validate this before writing the strip script.**

---

## Section 8: Expert Perspectives (Specific Questions)

* **Software Architect**: "Is directory separation robust?" **No.** Use file extensions (`.bulky.md`) and a `.cursorrules` or `.gitignore` file to explicitly hide them from agents. Use a `Makefile` to make the strip process a single command: `make build`.
* **Technical Writing Expert**: "Will writers use HTML markers?" Only if they have **snippets**. Authoring tags manually will fail within 2 weeks of usage.
* **LLM/NLP Expert**: "LLM from start or templates?" Use **LLM-assisted templates**. Let the template provide the *logic* (e.g., "Ask about a violation of this constraint") and let the LLM provide the *prose*.
* **Project Management**: "Is 3-4 weeks realistic?" **Yes**, but only if you skip the "Merge Results Back to Bulky" script. Keep the polishing results in a separate JSON for now. Focus on the generation-validation loop.
