# Ambiguity Detection - Design Clarifications

**Date:** 2025-12-06  
**Context:** Review of Increment 2 implementation

---

## Three Types of Ambiguity Signals

The system collects three distinct signals from model responses. All three should be used.

| Signal | Field | What It Means | Detection |
|--------|-------|---------------|-----------|
| **Divergent understanding** | `interpretation` | Models understood the text differently | Compare interpretations |
| **Implicit gaps** | `assumptions` | Models had to guess/fill in missing info | Check if assumptions were made |
| **Recognized confusion** | `ambiguities` | Models understood but flagged unclear parts | Check if ambiguities were noted |

---

## Current State vs Desired State

### Judge Prompt (LLM-as-Judge Strategy)

**Current:** Sends `interpretation`, `steps`, `assumptions` to judge  
**Missing:** `ambiguities` field not included

**Fix:** In `ambiguity_detector.py`, `_build_comparison_prompt()`:
```python
# Add after assumptions block:
if interp.ambiguities:
    interp_text += f"Noted ambiguities: {', '.join(interp.ambiguities)}\n"
```

### Edge Case: Agreement with Shared Ambiguity

**Scenario:** All models interpret the same way, but all note the same ambiguity.

**Example from todo.md test:**
- Claude, Gemini, Codex all interpret "priority levels" the same way
- But all three note: "What does the date represent - due date or creation date?"

**Current behavior:** Not flagged (models agree)  
**Desired behavior:** Flag as LOW severity - documentation has a gap even if consistently interpreted

**Implementation idea:**
```python
# After checking agreement
if comparison['agree']:
    # Check if multiple models noted the same ambiguity
    all_ambiguities = [interp.ambiguities for interp in interpretations.values()]
    common_ambiguities = find_common_themes(all_ambiguities)  # fuzzy match
    if common_ambiguities:
        # Flag as LOW severity with reason
        return Ambiguity(severity=LOW, reason="Consistent interpretation but shared confusion")
```

---

## Data Flow for Fix Generation (Increment 3)

Model-reported ambiguities are valuable input for fix generation:

```
Model Response
    └── ambiguities: ["What does date represent?", "Are P0-P3 the only levels?"]
            │
            ▼
Fix Generator
    └── Generates: "Clarify that date is creation date, not due date"
    └── Generates: "Add note: P0-P3 are the standard levels, custom levels not supported"
```

**Recommendation:** Store raw ambiguities in the Ambiguity object for later use:
```python
@dataclass
class Ambiguity:
    # ... existing fields ...
    model_noted_ambiguities: Dict[str, List[str]] = field(default_factory=dict)
```

---

## Implementation Status

### ✅ Completed (Increment 2)
1. **Filter empty interpretations** - Implemented in PR #8 (2025-12-10)
   - Filters out error responses, empty strings, whitespace-only interpretations
   - Comprehensive test coverage in `tests/test_filter_faulty_interpretations.py`

2. **Include ambiguities in judge prompt** - Implemented in PR #7 (2025-12-10)
   - Added `ambiguities` field to `_build_comparison_prompt()`
   - Judge now receives all three ambiguity signals
   - Test coverage in `tests/test_judge_prompt_content.py`

### 📋 Remaining Work

#### P2 - Polish Increment 2:
3. **Flag agreement-with-shared-ambiguity** - Edge case, but valuable signal
   - When models agree on interpretation but all note the same ambiguity
   - Should flag as LOW severity (documentation has gap even if consistently interpreted)

#### Increment 3 - Fix Generation:
4. **Use ambiguities for fix generation** - Natural extension when building fix_generator.py
   - Model-reported ambiguities provide valuable input for automated fixes
   - Consider adding `model_noted_ambiguities` field to Ambiguity dataclass

---

## Testing Recommendation

After implementing the judge prompt fix, re-run on `todo.md` and check:
1. Does the judge now mention model-noted ambiguities in its analysis?
2. Are any new ambiguities detected due to the richer context?

Expected: The "Cross-Project TODOs" section might get more detailed analysis since Claude noted 8 specific ambiguities in that section.
