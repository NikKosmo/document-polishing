# Expert Review Part 3: Implementation Plan Review
# Response from OpenAI Codex (gpt-5.2-codex)

**Review Date:** 2025-12-30
**Prompt:** PART3_PROMPT.md
**Plan Reviewed:** BULKY_CLEAN_ARCHITECTURE_PLAN.md
**Model:** gpt-5.2-codex (OpenAI Codex v0.77.0)
**Perspectives:** Software Architecture, Technical Writing, LLM/NLP, DevOps/Tooling, Project Management

---

**Software Architecture Expert**

**Section 1: Overall Assessment**  
**Verdict:** Proceed with Changes  
**Rationale:** The source/build split is sound and aligns with your need for “clean” LLM inputs, but the pipeline needs stronger guarantees (schema validation, drift detection, and parser‑safe stripping) to be reliable long‑term. The current strip plan is too regex‑centric for a core transformation step.  
**Confidence:** Medium

**Section 2: Critical Issues (If Any)**  
1. **Issue:** Strip script uses regex over raw Markdown.  
   - **Impact:** Can remove markers inside code fences or malformed comment blocks, leading to corrupted examples or accidental content removal.  
   - **Fix:** Use a Markdown parser or a fenced‑block aware scanner; explicitly skip code fences and HTML blocks not matching `@meta/@assertion/@polishing_results`.  
   - **Priority:** High  
2. **Issue:** No enforcement of bulky→clean determinism in CI.  
   - **Impact:** Clean docs can drift silently, breaking the “source of truth” contract.  
   - **Fix:** Add a CI check (or pre‑commit) that re‑strips bulky docs and diffs with `docs/clean`.  
   - **Priority:** High

**Section 3: Architecture Feedback**  
**What’s Good:**  
- Clear separation of source (bulky) and build (clean) reduces LLM contamination risk.  
- Phased rollout keeps core polish functionality stable.  
- Optional question testing integration avoids forcing unproven steps.  

**What’s Risky:**  
- Regex transformation is brittle for Markdown.  
- Dual‑format version control invites divergence.  
- Assertion IDs and metadata are not validated, risking broken automation later.  

**Suggestions:**  
- Introduce a minimal “lint” script for bulky docs: validate IDs, schema, and markers.  
- Add a build target (`make clean-docs`) and CI step to enforce pipeline integrity.  
- Define a stable JSON schema for `@meta` and `@assertion` in Phase 1.  

**Section 4: Phase‑by‑Phase Review**  
**Phase 1: Foundation**  
- **Feasibility:** Realistic, but missing validation/lint work.  
- **Risks:** Regex strip breaks code examples; metadata drift without CI.  
- **Suggestions:** Add parser‑safe strip + lint + CI drift check in Week 1.  
- **Priority:** Critical  

**Phase 2: Fix Question Templates**  
- **Feasibility:** Possible, but template success >80% is ambitious without structure‑specific patterns.  
- **Risks:** Regex templates won’t match real assertions; coverage low.  
- **Suggestions:** Add 1–2 doc‑specific patterns and measure; plan for template iteration.  
- **Priority:** Important  

**Phase 3: Integrate into polish.py**  
- **Feasibility:** OK if Phase 2 stabilizes.  
- **Risks:** Integration adds complexity before questions are reliable.  
- **Suggestions:** Keep it opt‑in and add a “dry‑run” mode that only reports coverage.  
- **Priority:** Important  

**Section 5: Missing Considerations**  
- **Schema validation:** No explicit schema for `@meta/@assertion` blocks.  
- **Drift detection:** Need automated checks that `docs/clean` is truly generated.  
- **Authoring ergonomics:** No tooling to insert markers safely.  

**Section 6: Alternative Approach (Optional)**  
**Alternative:** Use a single Markdown source with fenced blocks like `:::assertion` instead of HTML comments and parse with a Markdown AST.  
**Why it’s better:** Less brittle, easier to lint, and safer to strip.  
**Trade‑offs:** Requires a parser dependency and more upfront code.

**Section 7: Quick Wins**  
1. Implement a code‑fence‑aware strip + golden tests.  
2. Add a CI check: `strip(bulky) == clean`.  

---

**Technical Writing Expert**

**Section 1: Overall Assessment**  
**Verdict:** Proceed with Changes  
**Rationale:** The plan creates a clean authoring/testing split, but authoring friction is a risk. Writers will need guardrails and templates to avoid inconsistent markup.  
**Confidence:** Medium

**Section 2: Critical Issues (If Any)**  
1. **Issue:** HTML comments are invisible in rendered views.  
   - **Impact:** Writers may forget assertions or misplace metadata.  
   - **Fix:** Provide authoring templates and a lint report that flags missing assertions.  
   - **Priority:** High  

**Section 3: Architecture Feedback**  
**What’s Good:**  
- Assertion markers create an explicit contract between prose and tests.  
- Metadata history is helpful for future maintenance.  

**What’s Risky:**  
- Writers may skip or misuse markers; consistency may degrade quickly.  
- The bulky format isn’t documented for onboarding.  

**Suggestions:**  
- Provide copy‑paste snippets for common assertion types.  
- Create a “bulky authoring guide” and a checklist.  
- Add a lightweight `bulky-lint` that surfaces missing/assertion density.  

**Section 4: Phase‑by‑Phase Review**  
**Phase 1:**  
- **Feasibility:** OK with clear authoring guidance.  
- **Risks:** Confusing markers; accidental omissions.  
- **Suggestions:** Draft a one‑page guide + starter template in Week 1.  
- **Priority:** Critical  

**Phase 2:**  
- **Feasibility:** Reasonable if assertions are consistent.  
- **Risks:** Templates fail on poorly structured prose.  
- **Suggestions:** Add guidance on “assertion writing” style.  
- **Priority:** Important  

**Phase 3:**  
- **Feasibility:** Good if prior steps stable.  
- **Risks:** More complexity for writers if output isn’t actionable.  
- **Suggestions:** Ensure reports show exact assertion IDs and suggested fixes.  
- **Priority:** Important  

**Section 5: Missing Considerations**  
- **Authoring style guide:** How to write assertions vs explanations.  
- **Assertion coverage targets:** What “good enough” coverage looks like.  
- **Migration ergonomics:** How to convert existing docs efficiently.  

**Section 6: Alternative Approach (Optional)**  
**Alternative:** Use visible tags like `> [assertion] ...` in Markdown.  
**Why it’s better:** Writers see and maintain assertions easily.  
**Trade‑offs:** Might clutter human‑readable docs.  

**Section 7: Quick Wins**  
1. Create a bulky doc template with 3 assertion examples.  
2. Convert one real doc and run a manual question pass.  

---

**LLM/NLP Expert**

**Section 1: Overall Assessment**  
**Verdict:** Proceed with Changes  
**Rationale:** The separation of bulky/clean is the right move for LLM input quality, but validation and testing of “cleanliness” must be explicit. Pure regex templates may struggle with natural language variance.  
**Confidence:** Medium

**Section 2: Critical Issues (If Any)**  
1. **Issue:** No validation that clean docs are actually free of markers.  
   - **Impact:** LLMs could still see metadata, biasing answers.  
   - **Fix:** Add automated “cleanliness” checks and spot‑test with LLMs.  
   - **Priority:** High  

**Section 3: Architecture Feedback**  
**What’s Good:**  
- Assertion‑driven generation allows low‑leakage question creation.  
- Optional integration keeps experimentation isolated.  

**What’s Risky:**  
- Template matching will fail on varied assertion phrasing.  
- “Answerability” check is substring‑based and can be too strict or too lax.  

**Suggestions:**  
- Normalize assertions (lowercase, punctuation stripping) for extraction.  
- Add a fallback LLM paraphrase step only after template succeeds.  
- Validate by running a multi‑model check on clean outputs.  

**Section 4: Phase‑by‑Phase Review**  
**Phase 1:**  
- **Feasibility:** Good.  
- **Risks:** “Clean” isn’t guaranteed without tests.  
- **Suggestions:** Build a “clean doc audit” in Week 1.  
- **Priority:** Critical  

**Phase 2:**  
- **Feasibility:** OK if assertions are formulaic.  
- **Risks:** Low match rate on real docs.  
- **Suggestions:** Add doc‑specific patterns and a coverage report.  
- **Priority:** Important  

**Phase 3:**  
- **Feasibility:** Fine as opt‑in.  
- **Risks:** Model answers vary without consistent prompt framing.  
- **Suggestions:** Standardize prompts and log model disagreement.  
- **Priority:** Important  

**Section 5: Missing Considerations**  
- **Prompt stability:** Need consistent prompt templates and versioning.  
- **Renderer variance:** Markdown renderers differ; should test with 1–2.  
- **Noise controls:** Ensure LLMs never see bulky docs.  

**Section 6: Alternative Approach (Optional)**  
**Alternative:** Structured data first: store assertions in JSON/YAML and render docs.  
**Why it’s better:** LLM input is fully controlled; question gen is deterministic.  
**Trade‑offs:** Larger authoring change; tooling cost.  

**Section 7: Quick Wins**  
1. Strip one bulky doc and run 3 models on clean vs bulky to compare leakage.  
2. Measure template match rate on 20 assertions.  

---

**DevOps/Tooling Expert**

**Section 1: Overall Assessment**  
**Verdict:** Proceed with Changes  
**Rationale:** The plan is straightforward for a personal project, but tooling should enforce correctness and reduce manual steps.  
**Confidence:** Medium

**Section 2: Critical Issues (If Any)**  
1. **Issue:** No CI/automation for clean doc generation.  
   - **Impact:** Inconsistent outputs and manual errors.  
   - **Fix:** Add a `make`/script target and CI verification.  
   - **Priority:** High  

**Section 3: Architecture Feedback**  
**What’s Good:**  
- CLI‑first approach aligns with current project structure.  
- Optional features prevent destabilizing core workflow.  

**What’s Risky:**  
- Error handling not specified for strip or pipeline steps.  
- No standard build entry point.  

**Suggestions:**  
- Create a single `scripts/build_docs.py` wrapper or Makefile target.  
- Add structured errors (exit codes, clear messages).  
- Keep core logic in a library module, CLI in thin wrappers.  

**Section 4: Phase‑by‑Phase Review**  
**Phase 1:**  
- **Feasibility:** Easy.  
- **Risks:** Silent failures in strip.  
- **Suggestions:** Add unit tests + CI; check performance on larger docs.  
- **Priority:** Critical  

**Phase 2:**  
- **Feasibility:** OK.  
- **Risks:** Validation logic too loose/tight without metrics.  
- **Suggestions:** Add logging of failure reasons and counts.  
- **Priority:** Important  

**Phase 3:**  
- **Feasibility:** Good.  
- **Risks:** Configuration sprawl.  
- **Suggestions:** Add defaults and `--enable-question-testing` flag for CLI.  
- **Priority:** Important  

**Section 5: Missing Considerations**  
- **CI integration:** A minimal workflow for strip + tests.  
- **Artifact management:** Where to store generated JSON outputs.  
- **Error reporting:** Should be explicit, not `print`.  

**Section 6: Alternative Approach (Optional)**  
**Alternative:** Use Pandoc filters for stripping metadata.  
**Why it’s better:** More robust Markdown handling.  
**Trade‑offs:** Adds a dependency and integration overhead.  

**Section 7: Quick Wins**  
1. Add `make clean-docs` and a CI check.  
2. Add a dry‑run mode that reports changes without writing.  

---

**Project Management / Pragmatist**

**Section 1: Overall Assessment**  
**Verdict:** Proceed with Changes  
**Rationale:** The plan is achievable but slightly over‑scoped for a personal project. You can shrink Week 1 and validate assumptions faster.  
**Confidence:** Medium

**Section 2: Critical Issues (If Any)**  
1. **Issue:** Week 1 too narrow; doesn’t validate real value.  
   - **Impact:** You may invest in format before proving question generation works.  
   - **Fix:** Add a tiny end‑to‑end pilot in Week 1.  
   - **Priority:** High  

**Section 3: Architecture Feedback**  
**What’s Good:**  
- Phased plan reduces risk.  
- Explicit success metrics (template success, leakage) are good.  

**What’s Risky:**  
- Phase 2 success threshold may be optimistic.  
- Potential scope creep with merge script.  

**Suggestions:**  
- Define clear pivot points after Weeks 1 and 2.  
- Defer merge script indefinitely unless real need appears.  

**Section 4: Phase‑by‑Phase Review**  
**Phase 1:**  
- **Feasibility:** Easy, but value unclear without a pilot.  
- **Risks:** Over‑engineering before validation.  
- **Suggestions:** Add a single doc pilot + 10 question test.  
- **Priority:** Critical  

**Phase 2:**  
- **Feasibility:** Moderate; templates may require several iterations.  
- **Risks:** Low success rate causes delay.  
- **Suggestions:** Set a “stop‑loss” threshold (e.g., <50% success after 2 iterations).  
- **Priority:** Important  

**Phase 3:**  
- **Feasibility:** OK, but optional.  
- **Risks:** Premature integration.  
- **Suggestions:** Only integrate after Phase 2 success.  
- **Priority:** Nice‑to‑have  

**Section 5: Missing Considerations**  
- **Decision points:** When to pause or pivot.  
- **Time boxing:** Define max effort per phase.  
- **Definition of “good enough”:** Practical stopping criteria.  

**Section 6: Alternative Approach (Optional)**  
**Alternative:** Build a “micro‑pilot” before any tooling: manually annotate 1 doc and generate questions by hand.  
**Why it’s better:** Fast validation without engineering overhead.  
**Trade‑offs:** Not scalable; only proves concept.  

**Section 7: Quick Wins**  
1. Annotate 1 doc, run strip, and manually craft 5 questions from assertions.  
2. Run the validation checks on those questions to validate criteria.  

---

If you want, I can also map each section back to concrete TODOs in `plans/BULKY_CLEAN_ARCHITECTURE_PLAN.md`.
tokens used
23,752
**Software Architecture Expert**

**Section 1: Overall Assessment**  
**Verdict:** Proceed with Changes  
**Rationale:** The source/build split is sound and aligns with your need for “clean” LLM inputs, but the pipeline needs stronger guarantees (schema validation, drift detection, and parser‑safe stripping) to be reliable long‑term. The current strip plan is too regex‑centric for a core transformation step.  
**Confidence:** Medium

**Section 2: Critical Issues (If Any)**  
1. **Issue:** Strip script uses regex over raw Markdown.  
   - **Impact:** Can remove markers inside code fences or malformed comment blocks, leading to corrupted examples or accidental content removal.  
   - **Fix:** Use a Markdown parser or a fenced‑block aware scanner; explicitly skip code fences and HTML blocks not matching `@meta/@assertion/@polishing_results`.  
   - **Priority:** High  
2. **Issue:** No enforcement of bulky→clean determinism in CI.  
   - **Impact:** Clean docs can drift silently, breaking the “source of truth” contract.  
   - **Fix:** Add a CI check (or pre‑commit) that re‑strips bulky docs and diffs with `docs/clean`.  
   - **Priority:** High

**Section 3: Architecture Feedback**  
**What’s Good:**  
- Clear separation of source (bulky) and build (clean) reduces LLM contamination risk.  
- Phased rollout keeps core polish functionality stable.  
- Optional question testing integration avoids forcing unproven steps.  

**What’s Risky:**  
- Regex transformation is brittle for Markdown.  
- Dual‑format version control invites divergence.  
- Assertion IDs and metadata are not validated, risking broken automation later.  

**Suggestions:**  
- Introduce a minimal “lint” script for bulky docs: validate IDs, schema, and markers.  
- Add a build target (`make clean-docs`) and CI step to enforce pipeline integrity.  
- Define a stable JSON schema for `@meta` and `@assertion` in Phase 1.  

**Section 4: Phase‑by‑Phase Review**  
**Phase 1: Foundation**  
- **Feasibility:** Realistic, but missing validation/lint work.  
- **Risks:** Regex strip breaks code examples; metadata drift without CI.  
- **Suggestions:** Add parser‑safe strip + lint + CI drift check in Week 1.  
- **Priority:** Critical  

**Phase 2: Fix Question Templates**  
- **Feasibility:** Possible, but template success >80% is ambitious without structure‑specific patterns.  
- **Risks:** Regex templates won’t match real assertions; coverage low.  
- **Suggestions:** Add 1–2 doc‑specific patterns and measure; plan for template iteration.  
- **Priority:** Important  

**Phase 3: Integrate into polish.py**  
- **Feasibility:** OK if Phase 2 stabilizes.  
- **Risks:** Integration adds complexity before questions are reliable.  
- **Suggestions:** Keep it opt‑in and add a “dry‑run” mode that only reports coverage.  
- **Priority:** Important  

**Section 5: Missing Considerations**  
- **Schema validation:** No explicit schema for `@meta/@assertion` blocks.  
- **Drift detection:** Need automated checks that `docs/clean` is truly generated.  
- **Authoring ergonomics:** No tooling to insert markers safely.  

**Section 6: Alternative Approach (Optional)**  
**Alternative:** Use a single Markdown source with fenced blocks like `:::assertion` instead of HTML comments and parse with a Markdown AST.  
**Why it’s better:** Less brittle, easier to lint, and safer to strip.  
**Trade‑offs:** Requires a parser dependency and more upfront code.

**Section 7: Quick Wins**  
1. Implement a code‑fence‑aware strip + golden tests.  
2. Add a CI check: `strip(bulky) == clean`.  

---

**Technical Writing Expert**

**Section 1: Overall Assessment**  
**Verdict:** Proceed with Changes  
**Rationale:** The plan creates a clean authoring/testing split, but authoring friction is a risk. Writers will need guardrails and templates to avoid inconsistent markup.  
**Confidence:** Medium

**Section 2: Critical Issues (If Any)**  
1. **Issue:** HTML comments are invisible in rendered views.  
   - **Impact:** Writers may forget assertions or misplace metadata.  
   - **Fix:** Provide authoring templates and a lint report that flags missing assertions.  
   - **Priority:** High  

**Section 3: Architecture Feedback**  
**What’s Good:**  
- Assertion markers create an explicit contract between prose and tests.  
- Metadata history is helpful for future maintenance.  

**What’s Risky:**  
- Writers may skip or misuse markers; consistency may degrade quickly.  
- The bulky format isn’t documented for onboarding.  

**Suggestions:**  
- Provide copy‑paste snippets for common assertion types.  
- Create a “bulky authoring guide” and a checklist.  
- Add a lightweight `bulky-lint` that surfaces missing/assertion density.  

**Section 4: Phase‑by‑Phase Review**  
**Phase 1:**  
- **Feasibility:** OK with clear authoring guidance.  
- **Risks:** Confusing markers; accidental omissions.  
- **Suggestions:** Draft a one‑page guide + starter template in Week 1.  
- **Priority:** Critical  

**Phase 2:**  
- **Feasibility:** Reasonable if assertions are consistent.  
- **Risks:** Templates fail on poorly structured prose.  
- **Suggestions:** Add guidance on “assertion writing” style.  
- **Priority:** Important  

**Phase 3:**  
- **Feasibility:** Good if prior steps stable.  
- **Risks:** More complexity for writers if output isn’t actionable.  
- **Suggestions:** Ensure reports show exact assertion IDs and suggested fixes.  
- **Priority:** Important  

**Section 5: Missing Considerations**  
- **Authoring style guide:** How to write assertions vs explanations.  
- **Assertion coverage targets:** What “good enough” coverage looks like.  
- **Migration ergonomics:** How to convert existing docs efficiently.  

**Section 6: Alternative Approach (Optional)**  
**Alternative:** Use visible tags like `> [assertion] ...` in Markdown.  
**Why it’s better:** Writers see and maintain assertions easily.  
**Trade‑offs:** Might clutter human‑readable docs.  

**Section 7: Quick Wins**  
1. Create a bulky doc template with 3 assertion examples.  
2. Convert one real doc and run a manual question pass.  

---

**LLM/NLP Expert**

**Section 1: Overall Assessment**  
**Verdict:** Proceed with Changes  
**Rationale:** The separation of bulky/clean is the right move for LLM input quality, but validation and testing of “cleanliness” must be explicit. Pure regex templates may struggle with natural language variance.  
**Confidence:** Medium

**Section 2: Critical Issues (If Any)**  
1. **Issue:** No validation that clean docs are actually free of markers.  
   - **Impact:** LLMs could still see metadata, biasing answers.  
   - **Fix:** Add automated “cleanliness” checks and spot‑test with LLMs.  
   - **Priority:** High  

**Section 3: Architecture Feedback**  
**What’s Good:**  
- Assertion‑driven generation allows low‑leakage question creation.  
- Optional integration keeps experimentation isolated.  

**What’s Risky:**  
- Template matching will fail on varied assertion phrasing.  
- “Answerability” check is substring‑based and can be too strict or too lax.  

**Suggestions:**  
- Normalize assertions (lowercase, punctuation stripping) for extraction.  
- Add a fallback LLM paraphrase step only after template succeeds.  
- Validate by running a multi‑model check on clean outputs.  

**Section 4: Phase‑by‑Phase Review**  
**Phase 1:**  
- **Feasibility:** Good.  
- **Risks:** “Clean” isn’t guaranteed without tests.  
- **Suggestions:** Build a “clean doc audit” in Week 1.  
- **Priority:** Critical  

**Phase 2:**  
- **Feasibility:** OK if assertions are formulaic.  
- **Risks:** Low match rate on real docs.  
- **Suggestions:** Add doc‑specific patterns and a coverage report.  
- **Priority:** Important  

**Phase 3:**  
- **Feasibility:** Fine as opt‑in.  
- **Risks:** Model answers vary without consistent prompt framing.  
- **Suggestions:** Standardize prompts and log model disagreement.  
- **Priority:** Important  

**Section 5: Missing Considerations**  
- **Prompt stability:** Need consistent prompt templates and versioning.  
- **Renderer variance:** Markdown renderers differ; should test with 1–2.  
- **Noise controls:** Ensure LLMs never see bulky docs.  

**Section 6: Alternative Approach (Optional)**  
**Alternative:** Structured data first: store assertions in JSON/YAML and render docs.  
**Why it’s better:** LLM input is fully controlled; question gen is deterministic.  
**Trade‑offs:** Larger authoring change; tooling cost.  

**Section 7: Quick Wins**  
1. Strip one bulky doc and run 3 models on clean vs bulky to compare leakage.  
2. Measure template match rate on 20 assertions.  

---

**DevOps/Tooling Expert**

**Section 1: Overall Assessment**  
**Verdict:** Proceed with Changes  
**Rationale:** The plan is straightforward for a personal project, but tooling should enforce correctness and reduce manual steps.  
**Confidence:** Medium

**Section 2: Critical Issues (If Any)**  
1. **Issue:** No CI/automation for clean doc generation.  
   - **Impact:** Inconsistent outputs and manual errors.  
   - **Fix:** Add a `make`/script target and CI verification.  
   - **Priority:** High  

**Section 3: Architecture Feedback**  
**What’s Good:**  
- CLI‑first approach aligns with current project structure.  
- Optional features prevent destabilizing core workflow.  

**What’s Risky:**  
- Error handling not specified for strip or pipeline steps.  
- No standard build entry point.  

**Suggestions:**  
- Create a single `scripts/build_docs.py` wrapper or Makefile target.  
- Add structured errors (exit codes, clear messages).  
- Keep core logic in a library module, CLI in thin wrappers.  

**Section 4: Phase‑by‑Phase Review**  
**Phase 1:**  
- **Feasibility:** Easy.  
- **Risks:** Silent failures in strip.  
- **Suggestions:** Add unit tests + CI; check performance on larger docs.  
- **Priority:** Critical  

**Phase 2:**  
- **Feasibility:** OK.  
- **Risks:** Validation logic too loose/tight without metrics.  
- **Suggestions:** Add logging of failure reasons and counts.  
- **Priority:** Important  

**Phase 3:**  
- **Feasibility:** Good.  
- **Risks:** Configuration sprawl.  
- **Suggestions:** Add defaults and `--enable-question-testing` flag for CLI.  
- **Priority:** Important  

**Section 5: Missing Considerations**  
- **CI integration:** A minimal workflow for strip + tests.  
- **Artifact management:** Where to store generated JSON outputs.  
- **Error reporting:** Should be explicit, not `print`.  

**Section 6: Alternative Approach (Optional)**  
**Alternative:** Use Pandoc filters for stripping metadata.  
**Why it’s better:** More robust Markdown handling.  
**Trade‑offs:** Adds a dependency and integration overhead.  

**Section 7: Quick Wins**  
1. Add `make clean-docs` and a CI check.  
2. Add a dry‑run mode that reports changes without writing.  

---

**Project Management / Pragmatist**

**Section 1: Overall Assessment**  
**Verdict:** Proceed with Changes  
**Rationale:** The plan is achievable but slightly over‑scoped for a personal project. You can shrink Week 1 and validate assumptions faster.  
**Confidence:** Medium

**Section 2: Critical Issues (If Any)**  
1. **Issue:** Week 1 too narrow; doesn’t validate real value.  
   - **Impact:** You may invest in format before proving question generation works.  
   - **Fix:** Add a tiny end‑to‑end pilot in Week 1.  
   - **Priority:** High  

**Section 3: Architecture Feedback**  
**What’s Good:**  
- Phased plan reduces risk.  
- Explicit success metrics (template success, leakage) are good.  

**What’s Risky:**  
- Phase 2 success threshold may be optimistic.  
- Potential scope creep with merge script.  

**Suggestions:**  
- Define clear pivot points after Weeks 1 and 2.  
- Defer merge script indefinitely unless real need appears.  

**Section 4: Phase‑by‑Phase Review**  
**Phase 1:**  
- **Feasibility:** Easy, but value unclear without a pilot.  
- **Risks:** Over‑engineering before validation.  
- **Suggestions:** Add a single doc pilot + 10 question test.  
- **Priority:** Critical  

**Phase 2:**  
- **Feasibility:** Moderate; templates may require several iterations.  
- **Risks:** Low success rate causes delay.  
- **Suggestions:** Set a “stop‑loss” threshold (e.g., <50% success after 2 iterations).  
- **Priority:** Important  

**Phase 3:**  
- **Feasibility:** OK, but optional.  
- **Risks:** Premature integration.  
- **Suggestions:** Only integrate after Phase 2 success.  
- **Priority:** Nice‑to‑have  

**Section 5: Missing Considerations**  
- **Decision points:** When to pause or pivot.  
- **Time boxing:** Define max effort per phase.  
- **Definition of “good enough”:** Practical stopping criteria.  

**Section 6: Alternative Approach (Optional)**  
**Alternative:** Build a “micro‑pilot” before any tooling: manually annotate 1 doc and generate questions by hand.  
**Why it’s better:** Fast validation without engineering overhead.  
**Trade‑offs:** Not scalable; only proves concept.  

**Section 7: Quick Wins**  
1. Annotate 1 doc, run strip, and manually craft 5 questions from assertions.  
2. Run the validation checks on those questions to validate criteria.  

---

If you want, I can also map each section back to concrete TODOs in `plans/BULKY_CLEAN_ARCHITECTURE_PLAN.md`.
