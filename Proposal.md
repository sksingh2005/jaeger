# LFX Mentorship 2026 Proposal: Jaeger AI-Powered Trace Analysis (Phase 2)  
## Self-Service Skills Framework (CNCF - Jaeger)

**Program:** LFX Mentorship (CNCF)  
**Organization / Project:** Jaeger  
**Project:** AI-Powered Trace Analysis: Phase 2 - Self-Service Skills Framework  
**Term:** 2026 Term 2 (Jun-Aug)  
**Applicant:** [YOUR NAME]  
**Email:** [YOUR EMAIL]  
**GitHub:** [YOUR GITHUB PROFILE]  
**Timezone:** [YOUR TIMEZONE]

---

## About Me

### Why I Am Interested In This Project

[[FILL: 1-2 short paragraphs in your own voice on why this project matters to you, and why Jaeger specifically.]]

### Relevant Experience and Skills

[[FILL: concrete experience with links or short proof points.]]

- Go development and backend systems design  
- OpenTelemetry / distributed tracing familiarity  
- LLM agents, tool-calling, MCP/ACP ecosystem  
- React/TypeScript frontend work for observability UX  
- Testing and CI discipline in open-source repositories

### Open Source Experience (Optional)

[[FILL: links to notable PRs/issues/reviews.]]

- Jaeger PRs: [link]  
- Other observability/CNCF PRs: [link]  
- AI tooling PRs: [link]

### Time Commitment During Mentorship

[[FILL: weekly hours, timezone overlap with mentors, known conflicts.]]

---

## Project Understanding

### What Exists Today (Phase 1 Baseline)

From the current repository state:

- `jaegermcp` extension is already live and exposes static trace-analysis tools over MCP Streamable HTTP.
- `jaegermcp` already includes non-trace aggregate capability through `get_service_dependencies`, which matters for future metrics expansion discussions.
- `jaegerquery/internal/jaegerai` already provides `POST /api/ai/chat`, speaks ACP to a sidecar, and streams `session/update` messages.
- The Gemini reference sidecar in `scripts/ai-sidecar/gemini` already executes an agentic loop with MCP tools and supports the contextual-tool extension method path.
- Jaeger Query already serves SPM-style metrics via `/api/metrics/*` when metrics storage is configured, but there is no equivalent MCP metrics tool yet.
- The contextual tool relay is intentionally incomplete (`TODO(PR2)` path in `handler.go` / placeholder in `dispatcher.go`), which is a key Phase 2 implementation target.

### What Phase 2 Must Deliver

My reading of Phase 2 is straightforward: move from fixed AI behavior to a safe, extensible, operator-controlled platform.

1. **Self-service Skills Engine** in Jaeger backend: dynamic discovery, validation, load/reload of declarative skills from config.
2. **Skill-aware analysis UX**: natural language trace search and contextual trace explanation powered by selected skills.
3. **BYOA-compatible architecture**: skills must guide existing tools, not become an arbitrary runtime plugin mechanism.
4. **Local-first path**: reproducible, privacy-preserving operation with local models (e.g., Ollama via tool-calling sidecar path) without requiring public cloud calls.
5. **UI integration** in Jaeger UI (`jaeger-ui` repo): skill selection, reasoning/tool steps, and trace-to-chat interaction loop.
6. **Authoring docs** so users can define skills safely and correctly.

### A2A Architecture Alignment

The A2A architecture notes map well to this proposal and strengthen the BYOA direction:

- treat Jaeger as **data plane** (`jaegermcp` tools over MCP) + **control plane** (agent orchestration bridge)
- keep the model/agent runtime in a swappable **sidecar/facade layer**
- standardize capability discovery (agent card-style metadata) and event streaming to UI
- keep AG-UI/UI-driving actions (e.g., `highlight_span`) first-class in the conversation loop

This means Phase 2 should avoid coupling Jaeger backend logic to any one proprietary agent SDK and should favor protocol-bound contracts.
I will implement Phase 2 in alignment with the existing A2A architecture guidance, without redefining that architecture here.
The concrete implementation path in current Jaeger remains ACP (gateway-to-sidecar) plus MCP (sidecar-to-tools); this proposal builds on that path while preserving BYOA portability.

---

## Technical Approach

### 1) Skills as Declarative Artifacts (Not Runtime Code)

Following maintainer guidance, V1 skills are **declarative only**:

- system/developer prompt material
- allowed existing MCP tools (allowlist)
- examples
- output expectations / constraints
- optional metadata (name, description, tags, version)

Skills will **not** register new executable tool behavior. New tool logic remains in reviewed Jaeger/MCP code, then skills compose those tools.

Proposed file format (YAML):

```yaml
name: contextual_trace_explanation
version: "1"
description: Explain trace behavior with structural evidence
allowed_tools:
  - get_trace_topology
  - get_critical_path
  - get_span_details
  - get_trace_errors
system_prompt: |
  Analyze traces using structured tool outputs.
  Preserve timing, parent/child relationships, service boundaries,
  error states, and critical-path evidence.
examples:
  - user: "Why is this trace slow?"
    assistant_steps:
      - "get_trace_topology(trace_id)"
      - "get_critical_path(trace_id)"
output_expectations:
  - root_cause
  - evidence
  - recommended_next_steps
```

### 2) Skills Engine in `jaegermcp`

Add a new internal package under `cmd/jaeger/internal/extension/jaegermcp/internal/skills/`:

- **Loader**: discover and parse skill files from configured `skills_dir`.
- **Validator**: schema + semantic checks (non-empty prompt, valid IDs, known tools, size limits, duplicates).
- **Registry**: immutable snapshot of active skills with atomic swap on reload.
- **Watcher**: debounced FS watch for hot reload.

Add config:

- `extensions.jaeger_mcp.skills_dir` (optional)
- if unset, load bundled built-in skills

### 3) MCP-Native Exposure via Prompts

Expose skills through MCP prompts (`prompts/list`, `prompts/get`) so any MCP-aware sidecar/agent can discover and use them.

- This aligns with MCP semantics: prompts are server-defined reusable instruction templates.
- Emit `notifications/prompts/list_changed` on hot reload for compliant clients.

This keeps skills transport-standard and BYOA-friendly.

### 4) Skill Execution Contract with Sidecars

Sidecars (Gemini reference and future BYOA sidecars) should:

1. Discover skills via MCP prompts.
2. Fetch chosen skill prompt content.
3. Enforce `allowed_tools` by only exposing filtered tool declarations to the model in that turn.
4. Run reasoning loop with normal tool calling.

This separation preserves security and avoids coupling skill logic to a single sidecar implementation.

### 4.1) LangChainGo Reference Deliverable

To align with the project requirement, I will include a reference Go sidecar scaffold using `langchaingo` that:

- consumes Jaeger MCP tools and skill prompts
- enforces per-skill `allowed_tools`
- runs a tool-calling reasoning loop
- streams reasoning/tool updates back through the gateway contract

This deliverable is a reference implementation for BYOA, not a replacement for existing sidecars.

### 5) Trace Output Shape: Evidence-Driven, Not Flattened

Per maintainer guidance, #8409 should be treated as evidence for preserving task-critical dimensions, not a universal schema rule.

For trace tasks, skills should consume structured outputs that preserve:

- timing / durations
- parent-child relationships
- service / operation boundaries
- error state
- critical path segments

I will avoid flattening into prose before reasoning is done. Candidate response schemas for trace tools will be benchmarked against real troubleshooting tasks before finalizing authoring recommendations.

### 5.1) Metrics/SPM Alignment and Benchmark Plan (`#8409` Principle)

I will apply the same maintainer guidance directly:

- do not choose output shape by preference
- benchmark candidate schemas on real troubleshooting tasks
- keep first-class structure needed for the task

For metrics-capable deployments, this means:

- if/when `get_service_metrics` is added, it should be gated by metrics-store availability
- candidate output formats (summary-only vs per-bucket/per-step series vs hybrid) should be A/B tested on concrete agent tasks
- skills should adapt to tool availability from discovery (`tools/list`), so the same skill can work with or without metrics configured

This keeps the proposal aligned with current implementation and avoids overfitting to one schema prematurely.

### 6) Complete PR2 Contextual Tool Relay

In `jaegerquery/internal/jaegerai`:

- include frontend contextual tools in `NewSessionRequest.Meta`
- persist per-session snapshot in `ContextualToolsStore`
- replace placeholder in `handleJaegerToolCall` with full browser round-trip
- evolve streaming protocol from plain text to typed event payloads for reasoning/tool step visibility

This closes the loop for UI-driven tools like `highlight_span`.

### 7) UI Plan (Jaeger UI Repository)

In `jaeger-ui` (separate repo), integrate AI features with existing components:

- Search results enhancements in `SearchTracePage/SearchResults`
- Trace view controls in `TracePage` / `TracePageHeader`
- Agentic indicators for `gen_ai.*` spans
- Skill picker and reasoning-step panel tied to backend chat stream

Must-have deliverables:

- skill picker in AI chat flow
- reasoning-step visualization with tool call metadata
- deep-link / `highlight_span` interaction between AI output and trace timeline

Stretch deliverables (time permitting):

- GenAI-aware trace mode UX enhancements
- compact table/search options for analysis workflows

### 8) Local-First Strategy

Local-first support will focus on **validated tool-calling with local models**, likely via sidecar adapters rather than assuming native MCP in every runtime.

- verify end-to-end with Ollama-compatible tool-calling models
- keep MCP endpoint local (`jaegermcp` on localhost)
- document reproducible local setup paths and limitations
- include reproducible test fixtures and expected outputs

---

## Anticipated Technical Challenges and Mitigations

1. **Hot reload consistency under rapid file writes**  
   - Debounced watcher + atomic registry updates + versioned snapshots.

2. **Skill safety and misuse risks**  
   - Declarative-only format, strict allowlist validation, prompt size limits, parser hardening, and rejection of unknown tools.

3. **Schema drift vs reasoning quality**  
   - Task-benchmark harness to compare candidate trace and metrics output schemas on real debugging prompts.

4. **Gateway-side protocol evolution**  
   - Backward-compatible event format rollout with explicit versioning and integration tests.

5. **Cross-repo backend/UI coordination**  
   - milestone slicing into independently reviewable PRs with clear API contracts and mocks.

6. **BYOA compatibility**  
   - keep skills protocol-native (MCP prompts), sidecar-agnostic contracts, and docs for multiple sidecar implementations.

---

## Roadmap and Milestones

### Onboarding and Scope Alignment (Week 0)

- confirm success metrics with mentors (quality, latency, reproducibility, UX)
- finalize design notes and acceptance criteria
- reproduce current end-to-end stack locally

### Month 1: Skills Core + Contracts

- implement `skills` package (load/validate/register/hot-reload)
- expose skills through MCP prompts
- add tests for invalid/partial/mutating skill sets
- deliver initial skills ADR + schema spec draft

**Deliverable:** working skills engine with tests and prompt discovery.

### Month 2: Reference Skills + Gateway Integration

- add built-in reference skills:
  - `nl_trace_search`
  - `contextual_trace_explanation`
- add a reference `langchaingo` sidecar scaffold demonstrating skill-aware tool-calling against Jaeger MCP
- complete PR2 contextual tool relay path in `jaegerai`
- add structured reasoning/tool-step event flow
- run schema benchmarks for skill context assembly (trace-first; metrics-aware where tool support exists)
- integration tests from chat prompt to tool execution and response rendering

**Deliverable:** end-to-end skill-guided analysis with contextual tools.

### Month 3: UI + Local-First + Docs

- UI must-haves: skill picker, reasoning steps, and span highlight loop
- stretch UI items: GenAI-aware trace UX and compact analysis views
- local model validation workflow (Ollama/tool-calling path)
- document metrics-aware skill behavior (when metrics tools are present vs absent)
- complete authoring guide: “How to write custom Jaeger AI skills”
- polish, benchmarks, and maintainer feedback cycles

**Deliverable:** production-ready proposal scope completion with docs and demo scenarios.

---

## Validation and Success Criteria

I will treat the project as successful when:

- operators can add/update a skill file without rebuilding Jaeger
- agents discover and use skills through MCP-native mechanisms
- skills safely constrain tool usage and improve troubleshooting quality
- contextual UI tools round-trip correctly through ACP extension flow
- local-first workflow is documented and reproducibly tested
- users can author custom skills from documentation alone

---

## Documentation Outputs

Planned docs:

- `docs/skills-authoring.md` (schema, examples, validation rules, anti-patterns)
- `docs/adr/*` for skills engine architecture and protocol contracts
- updates to MCP/AI READMEs in `jaegermcp`, `jaegerai`, and sidecar docs
- operator runbooks for local-first and BYOA deployment paths

---

## References

- Jaeger MCP ADR: `docs/adr/002-mcp-server.md`
- AI Gateway + contextual tools RFC: `docs/rfc/0002-ai-gateway-contextual-tools.md`
- Jaeger MCP extension: `cmd/jaeger/internal/extension/jaegermcp`
- Jaeger AI gateway: `cmd/jaeger/internal/extension/jaegerquery/internal/jaegerai`
- Gemini sidecar reference: `scripts/ai-sidecar/gemini`
- MCP specification (prompts, transports): [modelcontextprotocol.io](https://modelcontextprotocol.io/)

