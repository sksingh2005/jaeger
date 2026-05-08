# LFX Mentorship 2026 Proposal: GenAI-Native Trace Visualization in Jaeger UI

**Program:** LFX Mentorship (CNCF)  
**Organization / Project:** Jaeger / Jaeger UI  
**Project Theme:** GenAI Observability UX in Jaeger  
**Term:** 2026 Term 2 (Jun-Aug)  
**Applicant:** [YOUR NAME]  
**Email:** [YOUR EMAIL]  
**GitHub:** [YOUR GITHUB]

---

## About Me

### Why This Project

[[FILL: 1-2 short paragraphs in your own voice.]]

### Relevant Experience

[[FILL: concrete experience + links.]]

- React + TypeScript UI development
- Ant Design component usage and customization
- Observability/telemetry data modeling
- OpenTelemetry semantic conventions
- Test-first OSS contribution workflow

### Open Source Work (Optional)

[[FILL: notable PR links.]]

### Time Commitment

[[FILL: hours/week, timezone overlap, known conflicts.]]

---

## Project Understanding

Today, Jaeger UI renders GenAI traces in the same generic timeline used for microservices. This is correct technically, but not sufficient for agent debugging. A developer needs to understand "what the agent was trying to do" (prompting, tool use, retrieval, planning), not only transport-level spans.

The project goal is to make Jaeger UI adapt when GenAI signals are present, while preserving Jaeger's core strengths:

- lossless trace model
- fast timeline rendering on large traces
- predictable, explainable UI state

This project is complementary to the earlier "AI for Jaeger" work (Issue #7832 direction): that work adds AI capabilities to Jaeger workflows; this work makes GenAI traces themselves understandable in Jaeger.

### Current Implementation Baseline (What I Will Reuse)

I will build directly on what already exists in `jaeger-ui`:

- ADR-0006 side-panel architecture is already implemented and production-ready.
- Timeline layout/settings state (`TraceViewSettings`, `store.layout.ts`, `store.timeline.ts`) already supports mode toggles.
- Row-derivation logic in `generateRowStates.ts` already applies "filter late" patterns (e.g., service pruning with placeholder preservation).
- Trace transformation + facades (`transform-trace-data.ts`, `OtelTraceFacade.ts`, `OtelSpanFacade.ts`) already provide a stable, lossless model layer.
- Search results components already have view toggles and sort controls, making compact-table mode a scoped extension rather than a full rewrite.

---

## Brief Analysis of Existing GenAI Observability UIs

- **Langfuse / Phoenix**: strong text inspection for prompts/completions and tool logs, but not centered on full distributed trace hierarchy.
- **LangSmith / Braintrust / W&B**: excellent reasoning and experiment views, but often detached from infrastructure spans and existing Jaeger workflows.
- **Opportunity for Jaeger**: unify both worlds in one place: agentic reasoning flow + infra spans, without forcing users into a separate product.

My proposal therefore prioritizes a "logical flow on top of complete trace" approach rather than replacing Jaeger's timeline model.

---

## Proposed UX (Wireframe)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trace: 8f1c...  [Agentic Mode ON]  [Logical View]  [Timeline] [Table View]│
├───────────────────────────────┬─────────────────────────────────────────────┤
│ TRACE TREE / TIMELINE         │ SIDE PANEL (ADR-0006)                      │
│ [AGENT] invoke_agent          │ Tab: GenAI Details                          │
│   ├─ [LLM] chat.completion    │ - Prompt (Markdown)                         │
│   ├─ [TOOL] execute_tool      │ - Completion (Markdown)                     │
│   │    └─ [INFRA] HTTP POST   │ - Tool Input/Output (Pretty JSON)          │
│   └─ [RAG] vector.search      │ - Media Preview (image/audio if present)    │
│                               │ - Token/Model metadata                      │
└───────────────────────────────┴─────────────────────────────────────────────┘
```

---

## Technical Plan (Aligned with Current Repo)

### 1) GenAI Mode Detection

Implement detection by scanning span attributes/events for `gen_ai.*` signals and related OTel GenAI keys.

Primary integration points:

- `packages/jaeger-ui/src/model/transform-trace-data.ts`
- `packages/jaeger-ui/src/model/OtelTraceFacade.ts`

Important constraint: keep transformation **lossless** (no span deletion in model layer).

---

### 2) Span Type Classification + Icon Mapping

Create a pure classifier utility (e.g., `model/genai/classify-span.ts`) and compute once per trace (cached in facade).

Planned classes:

- `agent` (invoke/create agent operations)
- `llm` (chat/completion/model calls)
- `tool` (execute tool / tool name attributes)
- `rag` (retrieval/search vector patterns)
- `infra` (generic HTTP/DB/network spans)

Initial mapping rules will prioritize explicit semantic convention attributes first, then conservative fallbacks.

UI rendering points:

- `TraceTimelineViewer/SpanBarRow.tsx` (icon badges in name column)
- optional header badges in `TracePageHeader` for mode status

---

### 3) Logical View: Classify Early, Filter Late

I will follow maintainer guidance exactly:

- **classify early** in model/facade
- **filter late** in row derivation/presentation

Concretely:

- Keep `transform-trace-data.ts` and `OtelTraceFacade` complete/lossless.
- Store logical-view toggle in UI state (existing store pattern).
- Apply visibility in `TraceTimelineViewer/generateRowStates.ts`.

Hierarchy safety rule:

- never hide spans in a way that makes parent-child flow misleading
- if infra spans are hidden, preserve structure using bridge spans and/or placeholder rows (similar to `PrunedSpanRow` behavior)

This guarantees instant switch back to full waterfall without rebuilding data.

Implementation intent: preserve model integrity and make Logical View a pure presentation mode, consistent with current timeline architecture.

---

### 4) Rich-Media Side Panel (ADR-0006)

Leverage existing side-panel architecture from ADR-0006:

- `TraceTimelineViewer/SpanDetailSidePanel/index.tsx`
- `TraceTimelineViewer/SpanDetail/index.tsx`

Add a GenAI-focused rendering layer:

- **Markdown** for long prompts/completions
- **Pretty JSON** for tool input/output payloads
- **Media preview** for image/audio references when present in attributes/events

This is additive and does not remove existing span details accordions.

---

### 5) Compact Table View on Search Results

Current search results are card-based in:

- `SearchTracePage/SearchResults/index.tsx`
- `SearchTracePage/SearchResults/ResultItem.tsx`

Add a compact table mode for scanning many traces quickly:

- toggle in search result view controls
- columns like trace id, root service/op, duration, spans, errors, GenAI indicator

No backend API change is required for initial table mode.

---

## Fallback Behavior for Partial / Older Traces

I propose an explicit 3-level behavior policy:

1. **Full GenAI mode**  
   Strong `gen_ai.*` signals present -> full iconography + logical view + rich panel enhancements.

2. **Partial enhancement**  
   Some GenAI attributes present but incomplete -> partial iconography/panel fields where evidence exists; no fabricated labels.

3. **Conservative fallback**  
   No reliable GenAI semantic signals -> standard Jaeger view, optional "GenAI signals not detected" hint, no auto-switch.

This avoids false positives while still helping with partially instrumented traces.

---

## Acceptance Criteria with Canonical Fixtures

I will include fixture-driven acceptance criteria (maintainer-requested) and tests.

### Canonical fixtures

1. **Agentic canonical fixture**  
   `invoke_agent` parent with:
   - one `execute_tool` child
   - one ordinary infra child (e.g., HTTP span)

2. **Partial-convention fixture**  
   Missing some latest OTel GenAI keys but still has meaningful GenAI metadata.

3. **Non-GenAI fixture**  
   Normal microservice trace with no GenAI metadata.

### Required acceptance outcomes

- Mode detection behavior matches policy for all three fixtures.
- Logical View preserves trustworthy hierarchy.
- Side panel renders long text/JSON/media appropriately when present.
- Full view <-> logical view switching is instant and lossless.
- Search page compact table works with existing sorting/filtering flow.

### Concrete review checks

- Given canonical fixture 1, users can visually distinguish `invoke_agent`, `execute_tool`, and infra spans in one pass.
- In Logical View ON, infra-heavy branches are reduced but path continuity remains understandable.
- In Logical View OFF, the original waterfall is unchanged from baseline behavior.
- For partial conventions fixture, UI applies only evidence-backed enhancements (no guessed labels).
- On large traces, interactions (row expand/select/filter toggle) remain responsive.

---

## Roadmap (with Research + Design First)

### Phase 0 (Week 1-2): Research and UX Spec

- Review GenAI observability patterns (Langfuse/Phoenix/LangSmith/Braintrust/W&B)
- Audit Jaeger UI architecture touchpoints
- Finalize icon mapping and fallback policy
- Produce wireframes + fixture definitions + acceptance checklist for mentor sign-off

### Phase 1 (Week 3-5): Detection + Classification + Icons

- Implement classifier + trace-level mode detection
- Add iconography in timeline rows
- Add unit tests for classification rules

### Phase 2 (Week 6-8): Logical View

- Add logical view toggle and row-level filtering in presentation layer
- Implement hierarchy-preserving hide/placeholder strategy
- Validate with canonical fixtures and large traces

### Phase 3 (Week 9-10): Rich-Media Side Panel

- Add GenAI detail rendering (markdown/json/media)
- Keep existing details available
- Add edge-case tests for missing/malformed payloads

### Phase 4 (Week 11-12): Search Table + Polish + Docs

- Implement compact trace table mode
- Final polish and perf checks
- Write user/developer docs and finalize demos

---

## Risks and Mitigations

- **Ambiguous semantic signals** -> conservative fallback policy + fixture-based validation
- **Hierarchy distortion in Logical View** -> filter late + placeholder/bridge strategy
- **UI performance on large traces** -> avoid O(n) recomputation in render path; cache classification
- **Over-scope risk** -> strict must-have vs stretch split

---

## Must-Have vs Stretch Scope

### Must-have

- GenAI mode detection
- span iconography classification
- logical view toggle (lossless model, filtered presentation)
- rich-media side panel rendering basics
- compact search table view
- fixture-based acceptance tests

### Stretch

- more advanced grouping/collapsing interactions for nested agent loops
- richer media inspection controls
- comparison helpers for prompt/completion variants

---

## Expected Outcomes

- Jaeger UI becomes materially more usable for GenAI agent debugging.
- Developers can read reasoning flow without losing distributed trace context.
- The implementation remains aligned with existing architecture and maintainable in upstream Jaeger UI.

---

## References

- `jaeger-ui/docs/adr/0006-side-panel-span-details.md`
- `jaeger-ui/packages/jaeger-ui/src/model/transform-trace-data.ts`
- `jaeger-ui/packages/jaeger-ui/src/model/OtelTraceFacade.ts`
- `jaeger-ui/packages/jaeger-ui/src/components/TracePage/TraceTimelineViewer/generateRowStates.ts`
- `jaeger-ui/packages/jaeger-ui/src/components/TracePage/TraceTimelineViewer/SpanDetailSidePanel/index.tsx`
- `jaeger-ui/packages/jaeger-ui/src/components/SearchTracePage/SearchResults/index.tsx`
- OTel Semantic Conventions for GenAI (resource listed in project statement)
- Jaeger issue #7832 (related AI project context)
