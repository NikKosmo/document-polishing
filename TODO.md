# Document Polishing TODO

**Documentation ambiguity detection system tasks**

---

## Active

- [P1] [ ] Integrate `ambiguity_detector.py` into `polish.py` `2025-12-01` #increment2 #integration
- [P1] [ ] Wire up LLM-as-Judge strategy (use existing model as judge) `2025-12-01` #increment2 #core

## Backlog

### Increment 2 - Ambiguity Detection (In Progress)
- [P1] [ ] Add document name to output folder for easy identification `2025-12-01` #ux #quick-win
- [P2] [ ] Add context injection (include prior sections in prompts) `2025-12-01` #improvement #context-blind-spot
- [P2] [ ] Add adversarial/red-team prompt variant `2025-12-01` #improvement #gemini-feedback

### Increment 3 - Fix Generation
- [P2] [ ] Implement `fix_generator.py` with real fix strategies `2025-12-01` #increment3
- [P2] [ ] Implement `fix_applier.py` to modify documents `2025-12-01` #increment3
- [P2] [ ] Add iteration support (re-test after fixes) `2025-12-01` #increment3
- [P2] [ ] Implement agreement scoring (% of models that agree) `2025-12-01` #increment3

### Increment 4 - Polish & Package
- [P3] [ ] Add FastEmbed strategy as optional optimization `2025-12-01` #optimization #optional
- [P3] [ ] Implement hybrid strategy (embeddings filter → LLM verify) `2025-12-01` #optimization
- [P3] [ ] Add readability scoring to prevent robotic writing `2025-12-01` #quality #gemini-feedback
- [P3] [ ] Create setup.py / pyproject.toml `2025-12-01` #packaging
- [P3] [ ] Create proper README.md with usage instructions `2025-12-01` #docs
- [P3] [ ] Add .env.example for API keys `2025-12-01` #packaging

## Completed

- [P1] [✓] Increment 1 - Core system working `2025-11-30` #increment1
- [P1] [✓] Cleanup temp files and remove outdated/unused files `2025-11-30` #cleanup
- [P1] [✓] Reorganize project structure `2025-11-30` #refactor
- [P1] [✓] Test Increment 1 with real CLI tools `2025-12-01` #testing #increment1
- [P1] [✓] Create `ambiguity_detector.py` module with pluggable strategies `2025-12-01` #increment2
- [P1] [✓] Research sentence embeddings options (Gemini) `2025-12-01` #research

## Blocked

(No blockers)

## Someday/Maybe

- [P3] [ ] Document real-world use cases and examples `#docs`
- [P3] [ ] Create demo video/walkthrough `#docs #marketing`
- [P3] [ ] Add "When NOT to use this tool" section to docs `#docs #gemini-feedback`
- [P3] [ ] API model support (OpenAI, Anthropic direct) `#feature`
- [P3] [ ] Web UI for reports `#feature`

---

## Research Findings (Reference)

### Embedding Options (from Gemini research 2025-12-01)
| Option | Install Size | Speed (CPU) | Best For |
|--------|--------------|-------------|----------|
| FastEmbed | ~150MB | ~20ms/pair | Production use |
| sentence-transformers | ~600MB+ | ~30ms/pair | If PyTorch already installed |
| OpenAI API | <10MB | ~300ms | Zero local setup |
| LLM-as-Judge | <10MB | ~1-2s | Highest accuracy, low volume |

**Decision:** Start with LLM-as-Judge (no new deps, catches semantic contradictions). Add FastEmbed later as optimization if needed.

### Hybrid Strategy (Future)
```
If similarity > 0.95 → Agree (skip LLM)
If similarity < 0.6  → Disagree (skip LLM)
If 0.6 - 0.95        → Ask LLM to verify
```

---

**Format:** `[Priority] [Status] Task description \`date\` #tags`