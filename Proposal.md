# LFX Mentorship 2026 Proposal
## Jaeger: AI-Powered Trace Analysis Phase 2 — Self-Service Skills Framework

**Program:** LFX Mentorship, CNCF  
**Applicant:** [YOUR NAME] | **Email:** [YOUR EMAIL] | **GitHub:** [YOUR GITHUB] | **Timezone:** [YOUR TIMEZONE]

---

## About You

### Why Are You Interested In This Specific Project?

[[FILL in your own voice — suggested direction below, replace with personal story]]

Phase 1 gave Jaeger a working AI assistant. Phase 2 is the harder problem: making it configurable without recompiling. A "detect N+1 queries" workflow and a "explain a critical path regression" workflow need different tool allowlists, different investigation sequences, and different output constraints. Hardcoding those into the agent does not scale. Building a declarative Skills Framework that lives inside an OpenTelemetry Collector extension — cleanly, safely, without turning it into an unreviewed plugin system — is the specific engineering problem I want to solve.

I was drawn to this after reading through the Phase 1 codebase and the A2A architecture document. The BYOA direction is the right call: Jaeger should be the best MCP data source and agent bridge, not compete with Claude Code or Gemini CLI. Phase 2 is what makes that bridge useful to teams with their own debugging workflows.

### Relevant Experience

[[FILL: replace with actual proof points — projects, PRs, coursework]]

- Go backend development: OpenTelemetry Collector extensions, component lifecycle, REST/gRPC APIs
- LLM integration: tool calling, agentic loops, MCP/ACP protocol, prompt design
- Python async for AI sidecar work: streaming responses, model API clients
- React/TypeScript for data-heavy observability UIs
- Testing: unit tests, integration tests, fixtures, CI pipelines

### Open Source Experience

[[FILL: link notable PRs/issues]]

- Jaeger contributions: [link]
- CNCF / observability: [link]
- AI tooling / Go: [link]

### Time Commitments

[[FILL: weekly hours, timezone overlap with mentors, any exam/internship conflicts]]

---

## About the Project

### How I Understand What Needs to Be Done

I studied the Phase 1 codebase before writing this proposal. Here is what is already built and what Phase 2 adds on top.

**What Phase 1 built.** `cmd/jaeger/internal/extension/jaegermcp/` is a complete OTel Collector extension with eight reviewed MCP tools: `get_services`, `get_span_names`, `search_traces`, `get_trace_topology`, `get_critical_path`, `get_span_details`, `get_trace_errors`, `get_service_dependencies`. The AI gateway at `POST /api/ai/chat` speaks ACP over WebSocket to the Gemini sidecar (`scripts/ai-sidecar/gemini/sidecar.py`), which discovers the tools, runs an agentic loop, and streams results back. RFC-0002 (`docs/rfc/0002-ai-gateway-contextual-tools.md`) already defines the clean separation: MCP tools are backend data tools; UI actions like `highlight_span` are conversation-scoped contextual tools routed through the ACP extension method, not through MCP. `dispatcher.go` already handles `ExtMethodJaegerToolCall` but currently returns a placeholder — completing that browser round-trip is confirmed as next LFX scope, not this term.

**What Phase 2 adds.** One new layer: a Skills Engine that makes the agent configurable without recompilation. Everything else stays intact. The maintainer was explicit: skills are declarative — system prompt material, constraints, output expectations, and a constrained list of allowed existing MCP tools. New tool behavior goes through normal code review first. Skills compose tools; they do not register new runtime behavior.

**Skill format:**

```yaml
apiVersion: jaegertracing.io/v1alpha1
kind: AISkill
metadata:
  name: contextual-trace-explanation
  version: "1"
  description: Explain why a trace is slow or failing using structured evidence.
spec:
  allowedTools:
    - get_trace_topology
    - get_critical_path
    - get_trace_errors
    - get_span_details
  systemPrompt: |
    Base the analysis on Jaeger MCP tool results.
    Preserve timing, parent-child relationships, service/operation boundaries,
    error state, and critical-path evidence.
  constraints:
    - Do not invent services, spans, errors, or timings.
    - Ask for span details before making attribute-level claims.
  output:
    sections: [summary, evidence, likely_cause, next_steps]
```

`allowedTools` is validated at load time against the tool names registered in `server.go`'s `registerTools()`. An unknown name is a load-time error. Existing MCP handler limits (`max_span_details_per_request`, `max_search_results`) and Jaeger tenancy remain the runtime enforcement layer — a skill never expands access, only restricts it.

Skills are exposed to MCP clients via `prompts/list` and `prompts/get` — MCP's first-class prompts capability supported by the Go SDK already used in the repo. This makes skills discoverable by any MCP client without new protocol work. On `NewSession`, the sidecar reads an optional `skill_name`, fetches the skill via `prompts/get`, replaces the hard-coded system prompt with the skill's content, and filters `FunctionDeclaration`s to the allowlist. A sidecar without a skill name falls back to all tools and the default `INSTRUCTIONS.md` — fully backward compatible.

Two built-in skills ship embedded with Jaeger: `natural-language-trace-search` (allowedTools: `get_services`, `get_span_names`, `search_traces`) and `contextual-trace-explanation` (allowedTools: `get_trace_topology`, `get_critical_path`, `get_trace_errors`, `get_span_details`). Both follow the progressive disclosure workflow from the MCP ADR, which TraceLLM (WWW 2026) independently validates: structured progressive access to trace data significantly improves LLM reasoning accuracy over raw trace dumps.

For the GenAI Logical View, the maintainer approved a three-rule fallback: full Agentic View when `gen_ai.operation.name` is present, partial rendering with a generic AI icon when at least one `gen_ai.*` attribute exists, and normal Jaeger view otherwise. Sensible defaults apply automatically (switch to GenAI view on attribute detection) while keeping customizability. The default trace view is unchanged.

---

### Technical Challenges and How I Would Address Them

**Skills becoming an unreviewed plugin mechanism.** The risk is that operators expect to embed arbitrary logic in skill files. I enforce the boundary at two points: load-time validation of `allowedTools` against registered MCP tool names (unknown name = load failure), and sidecar-side filtering so only `allowedTools` are passed to the model as `FunctionDeclaration`s for that session. Prompt and constraint fields accept only static text. No code, no shell commands, no network access from a skill file.

**Hot-reload without restart.** A file-watcher triggers a re-scan when skill files change. If validation passes, the registry updates and the server emits `notifications/prompts/list_changed` to connected MCP clients. If validation fails, the previous valid set stays loaded and the error is logged — last-known-good behavior. No session is disrupted by a bad skill file.

**Large trace context degrading reasoning quality.** The ADR's progressive disclosure workflow must be the enforced default in built-in skills, not an optional suggestion. I validate both built-in skills against a benchmark harness with four canonical troubleshooting scenarios (slow checkout, downstream timeout, N+1 database calls, root-cause vs symptom error) before declaring the output schema stable. Primary metric is task-level correctness — did the agent identify the actual root cause and cite specific span IDs and timings — not token count alone. This follows the TraceLLM evaluation methodology.

**Local model tool-calling reliability.** Local models vary significantly in their ability to produce valid tool calls. The sidecar must surface a specific error — not silent degradation — when a model fails. I would document tested models, provide deterministic fixture-based integration tests with expected tool call sequences, and validate the two built-in skills end-to-end against at least one local runner (Ollama or an OpenAI-compatible endpoint).

**Coordinating changes across three components.** The work touches `jaegermcp` (skills engine, prompts), the Gemini sidecar (skill-aware loop), and `jaeger-ui` (skill selection, reasoning display). I split into small independently-testable PRs: skill registry and validation first, MCP prompt exposure next, sidecar skill use, then UI. Each PR passes `make fmt && make lint && make test` on its own.

---

### Roadmap and Schedule

#### Community Bonding / Week 0
Reproduce the full Phase 1 stack locally. Confirm with mentors: exact V1 skill schema fields, built-in skill scope, local-first target, and whether the GenAI Logical View is in scope for the term.

#### Month 1 — Skills Engine

**Week 1–2: Loader and validator**
- Add `SkillsConfig` block to `config.go` (enabled, directories, watch_mode, max_file_size_kib)
- Create `cmd/jaeger/internal/extension/jaegermcp/internal/skills/` with `skill.go`, `loader.go`, `validator.go`, `registry.go`
- Unit tests: valid skills, unknown `allowedTools`, malformed YAML, size limit, last-known-good reload

**Week 3: MCP prompts exposure**
- Register skills via `prompts/list` and `prompts/get` in `server.go`
- File-watcher emitting `notifications/prompts/list_changed` on skill file changes
- Integration test: start extension → list prompts → get by name → verify allowlist

**Week 4: Built-in skills and benchmark harness**
- Embed `natural-language-trace-search` and `contextual-trace-explanation`
- Build harness with four canonical trace fixtures; validate both skills before schema is stable

#### Month 2 — Skill-Aware Execution

**Week 5–6: Sidecar skill selection**
- Read `skill_name` from `NewSession` metadata → `prompts/get` → replace system prompt → filter `FunctionDeclaration`s
- Backward-compatible fallback when no skill specified
- Integration test with mock MCP server

**Week 7–8: Local-first validation and benchmark**
- Validate both built-in skills with Ollama (or OpenAI-compatible endpoint)
- Document tested models, clear error messages for tool-calling failures
- Run benchmark harness end-to-end; finalize built-in skill output schemas

#### Month 3 — UI, GenAI View, Documentation

**Week 9–10: Jaeger UI**
- Skill selection dropdown fetching `prompts/list`
- Reasoning/tool-step display (collapsible tool call steps from `session/update` stream)
- GenAI Logical View three-rule fallback (if in scope)

**Week 11–12: Documentation and polish**
- Custom skill authoring guide: schema reference, safe authoring patterns, examples with benchmark results, validation rules
- `make fmt && make lint && make test` passing across all changed packages

#### Milestone Summary

| End of | Shippable output |
|--------|-----------------|
| Week 4 | Skills engine, MCP prompts, two built-in skills, benchmark harness |
| Week 6 | Skill-aware sidecar |
| Week 8 | Local-first validated, benchmark finalized |
| Week 10 | UI skill selection, reasoning steps, GenAI view |
| Week 12 | Authoring guide, operator docs, final test pass |
