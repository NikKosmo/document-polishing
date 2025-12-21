# Test Document Generation Prompts

This file contains prompts for generating test documents to validate context-dependent chunk handling in the documentation polishing system.

**Context:** We chunk documents based on markdown headers. Each chunk is sent to AI models for interpretation. We're testing session management that provides full document context to improve interpretation quality.

**Document Structure:** All test documents must follow the structure defined in `document_structure.md` (provided separately).

---

## Test Document 1: Terms and Definitions

**Filename:** `test_context_terms_definitions.md`

**Prompt:**

```
Create a workflow document following the structure in `document_structure.md` that tests context-dependent term usage.

GOAL: Test how models handle technical terms that are defined in early sections but used without explanation in later sections.

REQUIREMENTS:

1. **Document Type:** A procedural workflow (can be artificial/synthetic)
2. **Length:** 6-8 sections following the document_structure.md template
3. **Context Dependencies:**
   - Section 2-3: Define 4-6 domain-specific terms with clear explanations
   - Section 4-8: Use these terms naturally without re-explaining them
   - Terms should be essential for understanding the later sections

4. **Term Types to Include:**
   - Technical terms (e.g., "validation pipeline", "artifact registry")
   - Domain concepts (e.g., "atomic transaction", "idempotent operation")
   - Process-specific terminology (e.g., "pre-flight check", "rollback procedure")

5. **Success Criteria:**
   WITHOUT SESSION (no full document context):
   - Models should struggle to understand sections 4-8
   - Models should list "undefined term X" in their assumptions
   - Interpretations should be vague or incorrect

   WITH SESSION (full document context):
   - Models should correctly interpret all sections
   - Models should use the defined terms appropriately
   - Interpretations should be precise and aligned

EXAMPLE PATTERN:

Section 2 (Required Files):
"The validation pipeline consists of three stages: schema validation, business rule validation, and cross-reference validation."

Section 5 (Steps):
"Run the validation pipeline on the processed data."
^ Without context, models won't know what this means
^ With context, models will reference the three stages

OUTPUT: A complete markdown document following document_structure.md template
```

---

## Test Document 2: Abbreviations and Acronyms

**Filename:** `test_context_abbreviations_acronyms.md`

**Prompt:**

```
Create a workflow document following the structure in `document_structure.md` that tests context-dependent abbreviation usage.

GOAL: Test how models handle abbreviations/acronyms that are spelled out initially but used in abbreviated form later.

REQUIREMENTS:

1. **Document Type:** A procedural workflow (can be artificial/synthetic)
2. **Length:** 6-8 sections following the document_structure.md template
3. **Context Dependencies:**
   - Section 1-2: Introduce terms with full spelling: "Configuration Management Database (CMDB)"
   - Section 3+: Use only abbreviations: "Update the CMDB with the new entries"
   - Include 5-7 different abbreviations/acronyms

4. **Abbreviation Types:**
   - Standard acronyms (TLA - Three Letter Acronyms)
   - Compound terms shortened (e.g., "Data Quality Framework" → "DQF")
   - Process names abbreviated (e.g., "Automated Integration Testing" → "AIT")

5. **Success Criteria:**
   WITHOUT SESSION:
   - Models should report "unknown acronym" in assumptions
   - Models should guess or misinterpret what abbreviations mean
   - Steps involving abbreviated terms should be unclear

   WITH SESSION:
   - Models should correctly expand all abbreviations
   - Models should understand the full context of abbreviated references
   - Interpretations should be consistent with initial definitions

EXAMPLE PATTERN:

Section 1 (Purpose):
"This workflow manages the Continuous Integration/Continuous Deployment (CI/CD) pipeline for the Data Quality Framework (DQF)."

Section 4 (Steps):
"Trigger the CI/CD pipeline to validate the DQF rules."
^ Without context: What is CI/CD? What is DQF?
^ With context: Clear reference to previously defined terms

OUTPUT: A complete markdown document following document_structure.md template
```

---

## Test Document 3: Prerequisites and Setup

**Filename:** `test_context_prerequisites_setup.md`

**Prompt:**

```
Create a workflow document following the structure in `document_structure.md` that tests context-dependent prerequisite handling.

GOAL: Test how models handle later steps that assume prerequisites or setup mentioned only in early sections.

REQUIREMENTS:

1. **Document Type:** A procedural workflow (can be artificial/synthetic)
2. **Length:** 7-9 sections following the document_structure.md template
3. **Context Dependencies:**
   - Section 2-3: Detailed setup requirements, configuration, prerequisites
   - Section 5+: Steps that assume setup is complete, reference configuration values
   - No re-statement of prerequisites in later sections

4. **Prerequisite Types:**
   - Environment variables that must be set
   - Required directory structures
   - Configuration files with specific values
   - System state requirements

5. **Success Criteria:**
   WITHOUT SESSION:
   - Models should flag "missing setup information" in assumptions
   - Models should be uncertain about configuration values
   - Steps should appear incomplete or confusing

   WITH SESSION:
   - Models should reference the setup requirements correctly
   - Models should understand configuration context
   - Steps should be interpreted as complete procedures

EXAMPLE PATTERN:

Section 2 (Required Files):
"Environment variables:
- REPO_ROOT: Path to repository root (e.g., /home/user/project)
- BUILD_CONFIG: Path to build configuration (e.g., $REPO_ROOT/config/build.yaml)"

Section 6 (Steps):
"Execute the build script located at $REPO_ROOT/scripts/build.sh using settings from BUILD_CONFIG."
^ Without context: Where is REPO_ROOT? What is BUILD_CONFIG?
^ With context: Clear reference to environment variables defined earlier

OUTPUT: A complete markdown document following document_structure.md template
```

---

## Test Document 4: Cross-References and Step Dependencies

**Filename:** `test_context_cross_references_steps.md`

**Prompt:**

```
Create a workflow document following the structure in `document_structure.md` that tests context-dependent cross-referencing.

GOAL: Test how models handle steps that explicitly reference earlier steps or build upon previous outputs.

REQUIREMENTS:

1. **Document Type:** A procedural workflow (can be artificial/synthetic)
2. **Length:** 7-9 sections following the document_structure.md template
3. **Context Dependencies:**
   - Steps that reference earlier steps by number: "Using the result from Step 3..."
   - Steps that use outputs from previous steps without re-describing them
   - Steps that reference earlier validation criteria or rules

4. **Cross-Reference Types:**
   - Direct step references: "Take the output from Step 2 and..."
   - Numbered list references: "Repeat the process from item 3 above for each..."
   - Output references: "Use the generated token from the previous step..."
   - Conditional branches referencing earlier conditions

5. **Success Criteria:**
   WITHOUT SESSION:
   - Models should report "undefined reference" in assumptions
   - Models should be unclear about what "previous step" means
   - Dependencies between steps should be lost

   WITH SESSION:
   - Models should correctly identify referenced steps
   - Models should understand the data flow between steps
   - Dependencies should be clear in interpretations

EXAMPLE PATTERN:

Section 4 - Step 2:
"Generate authentication token and save to $WORKSPACE/auth_token.txt"

Section 5 - Step 3:
"Using the authentication token from Step 2, call the API endpoint."
^ Without context: What token? What was Step 2?
^ With context: Clear reference to token generation in previous section

OUTPUT: A complete markdown document following document_structure.md template
```

---

## Test Document 5: Constraints and Rules

**Filename:** `test_context_constraints_rules.md`

**Prompt:**

```
Create a workflow document following the structure in `document_structure.md` that tests context-dependent rule application.

GOAL: Test how models handle rules and constraints defined early but applied in later sections without re-statement.

REQUIREMENTS:

1. **Document Type:** A procedural workflow (can be artificial/synthetic)
2. **Length:** 7-9 sections following the document_structure.md template
3. **Context Dependencies:**
   - Section 2-3: Define global rules, constraints, validation criteria
   - Section 5+: Steps that must follow these rules but don't re-state them
   - Implicit assumption that rules are still in effect

4. **Rule Types:**
   - Data validation rules (formats, ranges, required fields)
   - Business constraints (limits, restrictions, allowed values)
   - Quality criteria (standards that must be met)
   - Error handling policies

5. **Success Criteria:**
   WITHOUT SESSION:
   - Models should omit rule checking in their interpretations
   - Models should not mention constraints when describing steps
   - Validation criteria should be ignored or forgotten

   WITH SESSION:
   - Models should apply rules consistently across all steps
   - Models should mention constraint checking where applicable
   - Validation criteria should be included in interpretations

EXAMPLE PATTERN:

Section 2 (Input):
"Constraints:
- File size must not exceed 10MB
- Content must be UTF-8 encoded
- Line count must be between 1-1000 lines"

Section 6 (Steps - Step 4):
"Read the input file and process each line."
^ Without context: No mention of size/encoding/line count validation
^ With context: Models should include validation of constraints before processing

OUTPUT: A complete markdown document following document_structure.md template
```

---

## Test Document 6: Comprehensive Mixed Dependencies

**Filename:** `test_context_comprehensive_mixed.md`

**Prompt:**

```
Create a workflow document following the structure in `document_structure.md` that combines ALL types of context dependencies.

GOAL: Comprehensive stress test with mixed context dependencies throughout the document.

REQUIREMENTS:

1. **Document Type:** A realistic procedural workflow (can be artificial but should feel real)
2. **Length:** 10-12 sections following the document_structure.md template
3. **Context Dependencies - Include ALL types:**
   - Term definitions (3-4 terms defined early, used later)
   - Abbreviations/acronyms (4-5 abbreviations)
   - Prerequisites/setup (environment, configuration)
   - Cross-references (steps referencing earlier steps)
   - Rules/constraints (global rules applied throughout)

4. **Subtlety Mix:**
   - 40% subtle (natural context dependencies)
   - 30% moderate (some explicit references like "as mentioned above")
   - 30% obvious (direct references to section numbers)

5. **Success Criteria:**
   WITHOUT SESSION:
   - Models should struggle significantly with sections 6+
   - Multiple types of "missing context" should appear in assumptions
   - Interpretations should be fragmented and incomplete
   - Steps should appear disconnected

   WITH SESSION:
   - Models should produce cohesive interpretations
   - All context dependencies should be resolved
   - Steps should connect logically
   - Rules should be applied consistently

6. **Complexity Requirements:**
   - At least 3 sections should be nearly incomprehensible without prior context
   - At least 2 sections should have multiple types of dependencies
   - The final validation section should reference rules, terms, and steps from throughout

EXAMPLE PATTERN (simplified):

Section 2: Define "validation pipeline", set ENV_ROOT variable, introduce CDF acronym
Section 3: Define rules: "all files must be < 5MB"
Section 5: "Run the validation pipeline using CDF located at $ENV_ROOT/cdf/"
           ^ Requires: term definition, acronym expansion, environment variable
Section 8: "Verify output meets the criteria from Section 3"
           ^ Requires: cross-reference to rules
Section 10: "Using results from Step 6, execute final CDF validation per the pipeline stages"
            ^ Requires: step reference, acronym, term definition, all combined

OUTPUT: A complete markdown document following document_structure.md template
```

---

## Usage Instructions

For each test document you want to generate:

1. Provide the thinking model with:
   - `document_structure.md` (the template to follow)
   - The specific prompt from above for the desired test type

2. The model will generate a complete markdown document

3. Save the generated document with the specified filename in the test documents directory

4. Run the polishing script on each test document with and without session management

5. Compare results to validate that session management improves context handling

---

## Validation Approach

After generating test documents:

1. **Baseline Test (Session Management OFF):**
   - Run polish script with `session_management.enabled: false`
   - Examine model interpretations for later sections
   - Expected: Many "missing context" assumptions, vague interpretations

2. **Session Test (Session Management ON):**
   - Run polish script with `session_management.enabled: true`
   - Examine model interpretations for same sections
   - Expected: Clear interpretations, correct context usage

3. **Success Metrics:**
   - Reduction in "assumption" count per section
   - Increase in interpretation accuracy
   - Fewer ambiguities detected by judge
   - More consistent interpretations across models

4. **Analysis:**
   - Compare ambiguity counts between baseline and session tests
   - Identify which context dependency types benefit most from sessions
   - Verify that session management resolves the specific context issues each document tests

---

**Version:** 1.0
**Created:** 2025-12-12
