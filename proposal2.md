# LFX Mentorship 2026 Proposal
## Jaeger: GenAI-Native Trace Visualization in Jaeger UI

**Program:** LFX Mentorship, CNCF  
**Applicant:** [YOUR NAME] | **Email:** [YOUR EMAIL] | **GitHub:** [YOUR GITHUB] | **Timezone:** [YOUR TIMEZONE]

---

## About You

### Why Are You Interested In This Specific Project?

[[FILL in your own voice — suggested direction below, replace with personal story]]

Every developer building LLM applications eventually ends up staring at a waterfall timeline wondering which 45ms gap is a tool call and which is a raw HTTP POST to the inference endpoint. The standard Jaeger view is truthful — all spans are there — but it optimizes for the wrong question. For a microservice trace, you ask "where is the latency?" For an agent trace, you ask "why did the agent do that?" These are structurally different questions and deserve structurally different views.

This project is the "flip side" of the existing AI-for-Jaeger initiatives — instead of using AI to help Jaeger, we are using Jaeger to help developers build better AI. Building on ADR-0006's new side-panel infrastructure and the existing `OtelTraceFacade` abstraction layer makes this the right moment to do it properly, and I want to be the one who does it.

### Relevant Experience

[[FILL: replace with actual proof points — projects, PRs, coursework]]

- React and TypeScript: production UI component development, Redux state management
- Ant Design: component usage, customization, theming
- OpenTelemetry semantic conventions and trace data modeling
- LLM application patterns: prompting, RAG pipelines, tool-use, agent loops
- Test-first OSS contribution workflow: fixture-driven unit tests, CI integration

### Open Source Experience

[[FILL: link notable PRs/issues]]

- Jaeger contributions: [link]
- CNCF / observability: [link]
- React/TypeScript UI: [link]

### Time Commitments

[[FILL: weekly hours, timezone overlap with mentors, any exam/internship conflicts]]

---

## About the Project

### How I Understand What Needs to Be Done

I studied the jaeger-ui codebase and ADR-0006 before writing this proposal.

**The specific problem.** Distributed tracing is the backbone of GenAI observability. However, observing an AI Agent is fundamentally different from observing a microservice. A microservice trace focuses on network latency and error codes; an AI trace focuses on the reasoning process — what the agent decided to do, what it sent to the model, what tool it called, and why. Today, `TraceTimelineViewer` renders every trace identically regardless of what the spans represent. A span with `gen_ai.operation.name = "chat"` looks identical to a span with `http.method = "POST"`. Developers must click into each span and manually scan key-value attribute tables to distinguish a logical "Tool Call" from a technical "HTTP POST." Long-form content like multi-paragraph prompts, completions, and tool payloads renders as truncated strings inside the standard `SpanDetail` accordions. Media references in `gen_ai.*` attributes are not rendered at all. That is the gap.

**What already exists and will be reused directly:**

- ADR-0006 side-panel architecture (`SpanDetailSidePanel/index.tsx`) is fully implemented. It provides the independent-scroll right panel, adjustable width via `VerticalResizer`, and the `detailPanelMode` Redux state — exactly the surface a rich GenAI detail view needs.
- `OtelTraceFacade.ts` and `OtelSpanFacade.ts` wrap `Trace`/`Span` into `IOtelTrace`/`IOtelSpan` with pre-computed fields (`_attributes`, `_events`, `_kind`, `_status`). Adding a cached `genAIKind` classification follows the exact same pattern — computed once at facade construction, no render-path cost.
- `generateRowStates.ts`'s `buildVisibleRows()` already implements "classify early, filter late" for service pruning using `isPrunedPlaceholder` rows when children are hidden. The Logical View toggle is a direct extension of this established pattern — a new `logicalViewEnabled` parameter, not a rewrite.
- `SpanBarRow.tsx` already receives `span: IOtelSpan` as a direct prop. Adding an icon badge to the name column is an additive change to one component.
- `SearchResults/index.tsx` already uses `AltViewOptions` for view-mode switching and works with `IOtelTrace[]`. A compact table mode slots in alongside existing card rendering without touching the data layer.

**What the OpenTelemetry GenAI Semantic Conventions provide:**

The OTel GenAI spec defines the detection surface for this project:

| Attribute | Meaning |
|-----------|---------|
| `gen_ai.operation.name` | Operation type: `"chat"`, `"text_completion"`, `"embeddings"`, `"retrieve"`, `"execute_tool"` |
| `gen_ai.system` | Provider: `"openai"`, `"anthropic"`, `"bedrock"`, etc. |
| `gen_ai.request.model` | Model name/version |
| `gen_ai.input.messages` (opt-in) | Serialized prompt / chat history |
| `gen_ai.output.messages` (opt-in) | Serialized completion |
| `gen_ai.tool.name` | Tool identifier |
| `gen_ai.tool.call.arguments` / `.result` (opt-in) | Tool payload |
| `gen_ai.usage.input_tokens` / `output_tokens` | Token counts |

`gen_ai.operation.name` is required for well-instrumented traces and is the primary classification signal. There is zero existing code in `jaeger-ui` that reads or specializes rendering for any of these attributes. This proposal adds that layer — additive, architecturally consistent with the facade pattern, and fully backward-compatible.

**A brief analysis of how current GenAI tools visualize traces:**

- **Arize Phoenix / Langfuse**: strong text inspection for prompts, completions, and tool logs, but not centered on a full distributed trace hierarchy. No waterfall, no infra span context.
- **LangSmith**: excellent agent reasoning graphs showing decision flow, but detached from infrastructure spans and existing Jaeger workflows.
- **Braintrust**: side-by-side prompt comparison views useful for debugging regressions, but not a trace tool.
- **Weights & Biases**: rich media logging including image and audio, but experiment-centric rather than trace-centric.

The opportunity for Jaeger is to unify both worlds in one place — agentic reasoning flow on top of the complete distributed trace — without forcing users into a separate product. My proposal prioritizes a "logical flow on top of complete trace" approach rather than replacing Jaeger's timeline model.

---

### Proposed Solution

This proposal adds one new capability layer on top of the existing `jaeger-ui` architecture: a GenAI presentation mode that activates automatically when `gen_ai.*` signals are detected and enriches the trace view without altering the underlying data model.

#### How GenAI Mode Travels Through the Stack

See [`genai-stack-flow.mmd`](genai-stack-flow.mmd) for the full architecture diagram.

The flow in summary: `span.attributes: IAttribute[]` → pure classifier → `OtelSpanFacade.genAIKind` + `OtelTraceFacade.genAIMode` (both added to their respective interfaces) → `TracePageHeader` mode badge + `TraceViewSettings` Logical View toggle → `duck.ts` Redux state → `VirtualizedTraceView` → `buildVisibleRows()` (6th param) + `SpanBarRow` icon badge + `SpanDetailSidePanel` GenAI tab → `SearchResults` table/card toggle.

#### Automatic GenAI Mode Detection

`OtelTraceFacade` already wraps `this.spans: IOtelSpan[]` (the full span list constructed from the legacy `Trace`). A `genAIMode` derived property scans `this.spans` once after construction:

```
Full mode:    ≥1 span has gen_ai.operation.name in span.attributes
Partial mode: ≥1 span has any gen_ai.* attribute but none have gen_ai.operation.name
None:         no gen_ai.* attributes → standard Jaeger view, no UI changes
```

This three-level policy avoids false positives on older or partially-instrumented traces. The default trace view is unchanged when `genAIMode === 'none'` — no spans hidden, no icons, no extra UI elements.

`genAIMode` is added to the `IOtelTrace` interface so that `TracePage`, `TracePageHeader`, and `SearchResults` components can all read it through the same typed interface. `transform-trace-data.ts` is not touched — `asOtelTrace()` already lazily initializes `OtelTraceFacade`, which is where `genAIMode` lives.

A non-intrusive badge in `TracePageHeader` shows the detected mode when `genAIMode !== 'none'`.

#### Agentic Hierarchy and Iconography

A pure classifier `model/genai/classify-span.ts` takes `span.attributes: IAttribute[]` (already converted from tags by `OtelSpanFacade` at construction time) and returns a `GenAISpanKind`:

```typescript
export type GenAISpanKind =
  | 'llm'         // gen_ai.operation.name: "chat" | "text_completion" | "completion"
  | 'tool'        // gen_ai.operation.name: "execute_tool"  OR  gen_ai.tool.name present
  | 'embeddings'  // gen_ai.operation.name: "embeddings"
  | 'retrieval'   // gen_ai.operation.name: "retrieve"
  | 'agent'       // parent span with ≥1 llm/tool/retrieval child
  | 'infra';      // no gen_ai.* attributes at all
```

`OtelSpanFacade` computes `genAIKind` once during construction and stores it as a cached field, the same pattern used for `_kind` (extracted from span tags), `_status` (ERROR if error tag), and `_parentSpanID`. `genAIKind` is added to the `IOtelSpan` interface so all components that receive `span: IOtelSpan` can read it without casting.

`SpanBarRow.tsx` already receives `span: IOtelSpan` and already uses `react-icons` (e.g., for existing UI elements) — no new dependency. A `GenAISpanIcon` sub-component conditionally renders an icon badge before the operation name:

```
llm        →  brain icon      (BiBrain)
tool       →  wrench icon     (FaWrench)
retrieval  →  database icon   (IoServer)
embeddings →  layers icon     (IoLayersOutline)
agent      →  circuit icon    (TbCircuitGround)
infra      →  no badge        (standard behavior, zero cost)
```

The badge renders only when `trace.genAIMode !== 'none'`. When `genAIMode === 'partial'`, icons appear only on spans with confirmed `gen_ai.*` attribute evidence — no label is fabricated.

#### Simplified "Logical" View

The current `buildVisibleRows` signature in `generateRowStates.ts` is:

```typescript
buildVisibleRows(
  spans: IOtelSpan[],
  childrenHiddenIDs: Set<string>,
  detailStates: Map<string, DetailState>,
  detailPanelMode: 'inline' | 'sidepanel',
  prunedServices: Set<string>,
)
```

A sixth parameter `logicalViewEnabled: boolean` is added. When true, spans where `span.genAIKind === 'infra'` are skipped from row emission. If an infra span has at least one non-infra child, a `isPrunedPlaceholder` row is emitted in its place — identical to how `prunedServices` filtering already works — so parent-child continuity remains readable. Switching Logical View off requires no data recomputation; the next call to the memoized `buildVisibleRows` with `logicalViewEnabled = false` restores the full waterfall immediately.

`logicalViewEnabled: boolean` is added to `types/TTraceTimeline.ts` alongside the existing `detailPanelMode`, `timelineVisible`, and `sidePanelWidth` fields. `duck.ts` gains a `SET_LOGICAL_VIEW` action and reducer following the exact same pattern as the existing `SET_TIMELINE_VISIBLE` action. Preference persists to localStorage.

`TraceViewSettings.tsx` (the settings gear introduced by ADR-0006) already has "Show Timeline" and "Show Span in Sidebar" menu items. A third checkmark item "Logical View" is added in the same pattern — see [`genai-ui-layout.mmd`](genai-ui-layout.mmd) for the rendered dropdown. `VirtualizedTraceView.tsx` reads `logicalViewEnabled` from the Redux store and passes it to `buildVisibleRows()`. No changes are needed in `SpanBarRow.tsx` or `TracePage/index.tsx` for this feature.

#### UI Layout

See [`genai-ui-layout.mmd`](genai-ui-layout.mmd) for the full component layout diagram, covering the trace timeline with icon badges, Logical View (before/after), the GenAI side panel tab, and the compact search table.

#### Rich-Media Side Panel (ADR-0006)

`SpanDetailSidePanel/index.tsx` currently wraps the existing `SpanDetail` component directly. An Ant Design `Tabs` component is added to switch between two tabs:

- **"Span Details" tab**: the existing `SpanDetail` component with its Attributes, Resource, Events, Links, and Warnings accordions — completely unchanged.
- **"GenAI Details" tab**: a new `GenAISpanDetail.tsx` component, rendered only when `span.genAIKind !== 'infra'`.

`GenAISpanDetail.tsx` reads from `span.attributes: IAttribute[]` (already available on `IOtelSpan`) and renders:

- **Prompts / completions**: `gen_ai.input.messages` and `gen_ai.output.messages` values are parsed from their JSON string form and rendered with `react-markdown` (MIT licensed), showing role headings (`system`, `user`, `assistant`) and formatted message bodies.
- **Tool payloads**: `gen_ai.tool.call.arguments` and `gen_ai.tool.call.result` are pretty-printed with `JSON.stringify(value, null, 2)` inside a `<pre>` block.
- **Media**: attribute values matching `data:image/...;base64,...` or `data:audio/...;base64,...` render inline as `<img>` or `<audio controls>` elements.
- **Token metadata bar**: `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, and `gen_ai.request.model` rendered as a compact row of tags.

The GenAI Details tab content is **lazy-mounted** — it only renders when the tab is first activated. This prevents DOM cost from multi-kilobyte `gen_ai.input.messages` strings on traces with many LLM spans, consistent with the existing `eventsInitialVisibleCount` tuning that ADR-0006 already uses in the side panel for events.

#### Compact Table View on Search Results

`SearchResults/index.tsx` manages `traces: IOtelTrace[]` and already renders `AltViewOptions` for view-mode switching. A table/card toggle is added to `AltViewOptions`. In table mode, a new `TracesTable.tsx` replaces the `ResultItem` card list:

```typescript
// columns derived from existing IOtelTrace fields:
// traceID, traceName, duration, services (for span count), hasErrors(), genAIMode
```

| Trace ID | Root Service / Operation | Duration | Spans | Errors | GenAI |
|----------|--------------------------|----------|-------|--------|-------|

- All column data comes from the existing `IOtelTrace` interface — no new backend API.
- Sort controls reuse the existing `SelectSort` component already wired in `SearchResults/index.tsx`.
- `genAIMode` on `IOtelTrace` drives the GenAI indicator column.
- In the existing card view, `ResultItem.tsx` gains a small `genAIMode` badge alongside the existing service tags — a single additive line.
- View-mode preference (table vs. card) persists to localStorage following the `spanNameColumnWidth` pattern in `duck.ts`.

---

### Technical Challenges and How I Would Address Them

**Maintaining a lossless trace model.** Classification and mode detection must never delete or mutate span data. I enforce this at the boundary: `classifyGenAISpan()` is a pure function with no side effects; `OtelSpanFacade` stores `genAIKind` as a derived read-only field; `OtelTraceFacade` stores `genAIMode` as a derived property. `transform-trace-data.ts` is not modified. Logical View is a presentation filter only — the complete span tree is always available.

**Hierarchy distortion in Logical View.** Hiding infra spans naively breaks parent-child visual continuity. The `buildVisibleRows()` function already handles this for service pruning via `isPrunedPlaceholder` rows. I extend the same pattern: when an infra span is hidden but has visible-category children, a placeholder row is inserted showing the span name and hidden count. The trace tree remains comprehensible with Logical View on.

**Partial and ambiguous instrumentation.** Not all `gen_ai.*` traces will have `gen_ai.operation.name`. Fabricating a category from heuristics produces incorrect labels that erode trust. I enforce the three-level policy strictly: `partial` mode shows icons only where explicit attribute evidence exists, never guesses, and marks missing fields as absent rather than empty. The classifier returns `'infra'` for any span where evidence is insufficient.

**Performance on large traces.** `OtelSpanFacade` already pre-computes fields once at construction. `classifyGenAISpan()` runs at the same point — O(n) over attribute count, not in the render path. `generateRowStates.ts` memoizes the row list; `logicalViewEnabled` is added as a memoization parameter alongside the existing `detailPanelMode` parameter established in ADR-0006. Lazy rendering of large `gen_ai.input.messages` / `gen_ai.output.messages` in the side panel prevents DOM cost from multi-kilobyte attributes until the user opens the GenAI tab.

**OTel GenAI attribute name stability.** The GenAI Semantic Conventions are stabilizing but may evolve. I centralize all `gen_ai.*` attribute name constants in `model/genai/attributes.ts` as a single source of truth. Updating to a new convention version is a one-file change, not a hunt through component code.

**Testing without a live LLM.** Span classification is a pure function over `IOtelSpan` — it can be tested deterministically with fixture data. I will create three canonical JSON fixtures: a fully-instrumented agentic trace (`invoke_agent` → `chat.completion` + `execute_tool` + HTTP infra), a partially-instrumented trace (`gen_ai.*` attributes present but no `operation.name`), and a plain microservice trace (no `gen_ai.*` attributes at all). These fixtures drive acceptance tests for classification, mode detection, Logical View row output, and side panel field rendering — no LLM dependency in CI.

---

### Roadmap and Schedule

#### Community Bonding

Reproduce the full `jaeger-ui` development environment locally. Confirm with mentors: icon choices, canonical fixture JSON structure, which `gen_ai.*` attribute versions to target, and Logical View scope for the term.

#### Month 1 (June) — Detection, Classification, and Iconography

**Week 1–2: Classifier and facade integration**
- `model/genai/attributes.ts` — `gen_ai.*` attribute name constants (single source of truth)
- `model/genai/classify-span.ts` — pure `classifyGenAISpan(attributes: IAttribute[]): GenAISpanKind`; reads the `IAttribute[]` type already used throughout the codebase
- `OtelSpanFacade.ts` — `genAIKind: GenAISpanKind` cached field computed in constructor, alongside existing `_kind`, `_status`, `_parentSpanID` pattern
- `OtelTraceFacade.ts` — `genAIMode: 'full' | 'partial' | 'none'` derived property scanning `this.spans` after construction; `transform-trace-data.ts` is not modified
- `types/IOtelSpan.ts` / `types/IOtelTrace.ts` — `genAIKind` and `genAIMode` added to the public interfaces
- Unit tests against three canonical fixtures: fully-instrumented agentic trace, partial `gen_ai.*` trace, plain microservice trace; edge cases: unknown `operation.name`, `gen_ai.*` on span events, agent detection via child `genAIKind`

**Week 3–4: Icon badges, mode indicator, Logical View state**
- `TraceTimelineViewer/SpanBarRow.tsx` — `GenAISpanIcon` sub-component reading `span.genAIKind`; uses existing `react-icons` dependency; zero render cost when `genAIKind === 'infra'`
- `TracePage/TracePageHeader/TracePageHeader.tsx` — mode indicator badge, rendered only when `genAIMode !== 'none'`; wired through `TracePage/index.tsx` which already reads config and Redux state
- `types/TTraceTimeline.ts` — `logicalViewEnabled: boolean` added alongside `detailPanelMode`, `timelineVisible`, `sidePanelWidth`
- `TraceTimelineViewer/duck.ts` — `SET_LOGICAL_VIEW` action and reducer following exact `SET_TIMELINE_VISIBLE` pattern; localStorage persistence
- `TracePage/TracePageHeader/TraceViewSettings.tsx` — "Logical View" checkmark item added as third item in the existing settings gear dropdown after "Show Span in Sidebar"
- Snapshot tests for `GenAISpanIcon` across all `GenAISpanKind` values; unit tests for `SET_LOGICAL_VIEW` reducer

**Milestone (End of Week 4):** Icon badges visible on canonical agentic fixture; mode indicator correct for all three fixtures; `SET_LOGICAL_VIEW` action wired with no row-filtering logic yet.

#### Month 2 (July) — Logical View and Rich-Media Side Panel

**Week 5–6: Logical View row filtering**
- `TraceTimelineViewer/generateRowStates.ts` — `buildVisibleRows()` gains 6th parameter `logicalViewEnabled: boolean`; spans where `span.genAIKind === 'infra'` skip row emission; if an infra span has non-infra children, a `isPrunedPlaceholder` row is emitted using the existing `RowState` shape
- `TraceTimelineViewer/VirtualizedTraceView.tsx` — reads `logicalViewEnabled` from Redux state, passes to `buildVisibleRows()` as 6th argument; memoization key updated
- Acceptance tests: Logical View ON gives correct row count and placeholder rows on canonical fixture 1; switching OFF restores identical rows to Logical View OFF baseline; large trace (100+ spans) toggle measured for instant re-render

**Week 7–8: Rich-Media Side Panel**
- `TraceTimelineViewer/SpanDetailSidePanel/GenAISpanDetail.tsx` (new) — reads `span.attributes: IAttribute[]` from `IOtelSpan`; renders markdown for `gen_ai.input.messages` / `gen_ai.output.messages` via `react-markdown`; pretty-printed JSON for `gen_ai.tool.call.arguments` / `gen_ai.tool.call.result`; token metadata bar from `gen_ai.usage.*` and `gen_ai.request.model`; inline `<img>` / `<audio>` for base64 media attribute values; tab content lazy-mounted on first activation
- `TraceTimelineViewer/SpanDetailSidePanel/index.tsx` — Ant Design `Tabs` wrapper added; "Span Details" tab renders existing `SpanDetail` unchanged; "GenAI Details" tab renders `GenAISpanDetail`; GenAI tab shown only when `span.genAIKind !== 'infra'`
- Tests: all attribute fields render when present; all fields absent-gracefully when missing; malformed JSON in tool payload does not crash; base64 image renders `<img>`; base64 audio renders `<audio>`

**Milestone (End of Week 8):** Logical View toggle is lossless on all three canonical fixtures. Side panel GenAI tab renders markdown, JSON, token metadata, and media for canonical fixture 1. All existing side panel behavior unchanged.

#### Month 3 (August) — Compact Search Table, Polish, and Documentation

**Week 9–10: Compact table view on Search Results**
- `SearchTracePage/SearchResults/TracesTable.tsx` (new) — Ant Design `Table` over `traces: IOtelTrace[]`; columns from existing `IOtelTrace` fields: `traceID`, `traceName`, `duration`, `services` (span count), `hasErrors()`, `genAIMode` indicator; no new backend API
- `SearchTracePage/SearchResults/index.tsx` — table/card toggle added to existing `AltViewOptions`; view-mode preference persists to localStorage
- `SearchTracePage/SearchResults/ResultItem.tsx` — `genAIMode` badge added to existing card layout alongside service tags; single additive line
- Tests: table renders correct column data; `genAIMode` indicator present/absent matches fixture; `SelectSort` works in table mode

**Week 11–12: End-to-end validation and documentation**
- Full sweep across all four ADR-0006 layout combinations (inline/sidepanel × timeline/tree-only) with GenAI features active — confirm no regressions
- Performance check on a 500-span agent trace: Logical View toggle re-render, side panel lazy-mount timing
- `yarn lint && yarn test` clean across all changed packages
- Developer documentation: `attributes.ts` constant reference, classifier extension guide, fixture authoring guide
- User documentation: GenAI mode indicator, Logical View toggle, side panel GenAI tab

#### Milestones

| End of | Testable output |
|--------|----------------|
| Week 2 | `classifyGenAISpan` unit tests passing on all three canonical fixtures; `genAIKind` and `genAIMode` on interfaces |
| Week 4 | Icon badges on agentic fixture; mode indicator correct; `SET_LOGICAL_VIEW` reducer tested |
| Week 6 | `buildVisibleRows` with 6th param; Logical View lossless toggle confirmed; placeholder rows on fixture 1 |
| Week 8 | GenAI tab in side panel: markdown, JSON, token metadata, lazy mount; all three fixture acceptance tests passing |
| Week 10 | Compact search table with GenAI indicator; card view badge; `AltViewOptions` toggle |
| Week 12 | `yarn test` clean; all four ADR-0006 layout combinations verified; documentation complete |
