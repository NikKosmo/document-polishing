# Context Injection Options

**Date:** 2025-12-06  
**Purpose:** Document alternative approaches for context injection, for potential future implementation

---

## Current Decision

**Selected approach:** Prior Sections (N=2, configurable)

This document captures other options considered, for future reference if needs change.

---

## Option 1: Prior Sections (SELECTED)

Include N sections that appear before the current section in document order.

### Pros
- Simple to implement - just track section indices
- Predictable behavior - always the same sections
- Resource efficient - bounded token usage
- No special document structure required
- Works with any markdown document

### Cons
- May miss relevant context that appears *after* current section
- May include irrelevant prior sections (e.g., unrelated sibling)
- Assumes document is written in logical top-down order
- N is arbitrary - optimal value may vary by document

### What needs to be done
- Add `context_sections: int` parameter to `PromptGenerator.create_interpretation_prompt()`
- Pass prior N sections from `DocumentProcessor` to prompt generator
- Add `--context-sections N` CLI flag (default: 2)
- Truncate context if it exceeds token budget (configurable max)

---

## Option 2: Whole File

Include entire document as context for every section test.

### Pros
- Complete context - no information missed
- Simplest implementation - just prepend full content
- Models can reference any part of document

### Cons
- Token expensive - multiplies cost by document length
- Noise - irrelevant sections dilute attention
- May exceed context window for large documents
- Not viable with CLI tools on subscriptions (your constraint)

### What needs to be done
- Prepend full document content (marked as context) to each prompt
- Add token counting and warnings for large documents
- Consider summarization for documents exceeding threshold

---

## Option 3: Hierarchical (Parent + Siblings)

Include parent section and sibling sections based on document structure.

### Pros
- Structurally relevant context
- Respects document organization
- More targeted than "prior N sections"

### Cons
- Requires parsing document hierarchy (complex)
- Assumes well-structured documents with clear nesting
- Limits tool applicability to hierarchical docs
- Flat documents (all H2s) get no benefit

### What needs to be done
- Build document tree structure during extraction
- Track parent-child relationships between sections
- Modify `DocumentProcessor` to expose hierarchy
- Add logic to select parent + siblings for each section
- Handle edge cases: root sections, deeply nested sections

---

## Option 4: Smart Related (Semantic Similarity)

Use embeddings to find sections most semantically related to current section.

### Pros
- Finds actually relevant context regardless of position
- Handles forward references (later sections that define terms)
- Can surface non-obvious relationships

### Cons
- Requires embedding model (new dependency)
- Additional API calls or local model
- Slower - must embed all sections first
- May surface surprising/wrong relationships
- Harder to debug - "why did it include that section?"

### What needs to be done
- Add embedding generation for all sections (FastEmbed or API)
- Compute similarity matrix between sections
- Select top-K most similar sections as context
- Cache embeddings to avoid recomputation
- Add similarity threshold to filter weak matches

---

## Option 5: Explicit References

Parse section content for explicit references to other sections, include those.

### Pros
- Follows document's own linking logic
- Includes exactly what the section references
- No arbitrary N or similarity threshold
- Respects author intent

### Cons
- Only works if document has explicit references
- Many documents don't cross-reference sections
- Requires parsing various reference formats ("see X", "as described in Y", etc.)
- May miss implicit dependencies

### What needs to be done
- Build regex/patterns for common reference formats
- Parse each section for references to other section headers
- Resolve references to actual section content
- Handle missing/broken references gracefully
- Consider transitive references (A→B→C)

---

## Option 6: Hybrid (Tiered Approach)

Combine multiple strategies with priority ordering.

**Example tier:**
1. Always include immediate prior section (cheap, usually relevant)
2. Include explicitly referenced sections (if any found)
3. Fill remaining budget with semantically similar sections

### Pros
- Best of multiple approaches
- Graceful degradation - works even if one strategy fails
- Can tune tiers for different document types

### Cons
- Most complex to implement
- Multiple dependencies (embeddings for semantic)
- Harder to explain/debug behavior
- May over-engineer for current needs

### What needs to be done
- Implement each component strategy
- Build orchestrator that combines results
- Define token budget allocation across tiers
- Add configuration for enabling/disabling tiers
- Extensive testing for interaction effects

---

## Comparison Matrix

| Option | Complexity | Token Cost | Accuracy | Dependencies |
|--------|------------|------------|----------|--------------|
| Prior Sections | Low | Low-Medium | Medium | None |
| Whole File | Very Low | High | High* | None |
| Hierarchical | Medium | Low | Medium | None |
| Smart Related | High | Low | High | Embeddings |
| Explicit References | Medium | Very Low | Medium | None |
| Hybrid | Very High | Configurable | Highest | Multiple |

*High accuracy but high noise - may not translate to better results

---

## Recommendation Path

**Now:** Implement Option 1 (Prior Sections) - simple, good enough

**If needed later:**
- If documents have clear hierarchy → Add Option 3
- If semantic relevance matters → Add Option 4 (already have FastEmbed in Someday/Maybe)
- If documents cross-reference heavily → Add Option 5

**Avoid for now:** Option 6 (Hybrid) - over-engineering risk

---

## Notes for Future Implementation

When adding alternative strategies, consider:

1. **Strategy interface** - Abstract base class so strategies are swappable
2. **Configuration** - Allow per-document or per-run strategy selection
3. **Composition** - Design so strategies can be combined later
4. **Metrics** - Track which strategy produces better ambiguity detection

```
# Future structure (conceptual)
class ContextStrategy(ABC):
    def get_context(self, current_section, all_sections) -> List[Section]

class PriorSectionsStrategy(ContextStrategy): ...
class SemanticStrategy(ContextStrategy): ...
class HybridStrategy(ContextStrategy): ...
```
