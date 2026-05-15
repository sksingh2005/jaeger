# LFX Mentorship 2026 Proposal: Jaeger AI-Powered Trace Analysis Phase 2
## Self-Service Skills Framework

**Program:** LFX Mentorship, CNCF  
**Organization / Project:** Jaeger  
**Project:** AI-Powered Trace Analysis: Phase 2 - Self-Service Skills Framework  
**Term:** 2026 Term 2, Jun-Aug  
**Applicant:** [YOUR NAME]  
**Email:** [YOUR EMAIL]  
**GitHub:** [YOUR GITHUB PROFILE]  
**Timezone:** [YOUR TIMEZONE]

---

## About You

### Why Are You Interested In This Specific Project?

[[FILL: Write this in your own voice. Suggested direction: I am interested in this project because it sits at the intersection of distributed tracing, OpenTelemetry, and practical agentic AI. Jaeger is already used by real engineering teams for production debugging, so adding AI here is not just about building a chatbot; it is about making trace investigation faster, safer, and more explainable.]]

[[FILL: Mention why Phase 2 specifically matters to you. Suggested direction: Phase 1 gave Jaeger a baseline AI assistant, but Phase 2 is the more interesting systems problem: turning hard-coded AI behavior into a self-service Skills Framework where users can teach Jaeger organization-specific debugging workflows without recompiling the binary.]]

### What Relevant Experience Or Skills Will Help You Be Successful?

[[FILL: Replace these with your actual proof points: projects, coursework, internships, PRs, or demos. Keep it concrete.]]

- Go backend development and API design.
- OpenTelemetry, distributed tracing, and Jaeger concepts.
- LLM agents, tool calling, MCP/ACP-style protocol integration, and prompt design.
- React/TypeScript frontend work for data-heavy interfaces.
- Testing discipline: unit tests, integration tests, fixtures, CI, and documentation.

### Optional Open Source Experience

[[FILL: Link notable PRs/issues/reviews. If you do not have major open-source PRs yet, mention smaller contributions honestly and focus on how you plan to communicate during the mentorship.]]

- Jaeger PRs/issues: [link]
- CNCF / observability contributions: [link]
- AI tooling / Go / React contributions: [link]

### Time Commitments During The Mentorship Term

[[FILL: Weekly hours, timezone overlap with mentors, exam/internship conflicts, and preferred communication cadence.]]

---

## About The Project

### How Do You Understand What Needs To Be Done?

My understanding is that Phase 2 should make Jaeger AI configurable by users. A user should be able to add a declarative skill such as "Analyze Critical Path" or "Detect N+1 Queries" and have the agent follow that workflow without rebuilding Jaeger.

The main boundary I would keep is that V1 skills configure how the agent uses existing Jaeger MCP tools. They should contain prompt material, constraints, examples, output expectations, and a tool allowlist. They should not register new runtime behavior. If Jaeger needs a new tool, that should be added through normal Jaeger/MCP code review and testing first.

This aligns with the current Jaeger codebase:

- `cmd/jaeger/internal/extension/jaegermcp` already implements Jaeger's MCP server as an OpenTelemetry Collector extension.
- `cmd/jaeger/internal/extension/jaegermcp/server.go` already registers reviewed MCP tools such as `get_services`, `get_span_names`, `search_traces`, `get_trace_topology`, `get_span_details`, `get_trace_errors`, `get_critical_path`, and `get_service_dependencies`.
- `docs/adr/002-mcp-server.md` already establishes progressive disclosure: search, map, diagnose, inspect, instead of loading full traces into model context.
- `cmd/jaeger/internal/extension/jaegerquery/internal/jaegerai` already provides the AI gateway through `POST /api/ai/chat`.
- `docs/rfc/0002-ai-gateway-contextual-tools.md` already defines the ACP extension-method approach for UI-driven contextual tools while keeping `jaegermcp` focused on backend data tools.
- `scripts/ai-sidecar/gemini/sidecar.py` already has the MCP discovery, Gemini agentic loop, hard-coded system prompt, and contextual-tool merge point where skill selection can be integrated.

My implementation would fit into this architecture:

- Extend `cmd/jaeger/internal/extension/jaegermcp/config.go` with a nested `Skills` config block for enable/disable, directories, watch mode, and size limits.
- Add `cmd/jaeger/internal/extension/jaegermcp/internal/skills/` for loading, parsing, validating, and storing skills.
- Validate each skill's `allowedTools` against the MCP tool names registered from `server.go`.
- Expose loaded skills through MCP prompts using `prompts/list` and `prompts/get`, with Jaeger-specific metadata for allowed tools and output expectations.
- Update the reference sidecar so it fetches the selected skill, replaces the fixed system prompt with skill prompt material, and filters MCP tool declarations to the skill's allowlist.
- Keep UI actions such as `highlight_span` in the gateway/contextual-tool path because they are browser-scoped, not backend data tools.

For the skill format, I would start with YAML:

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
    sections:
      - summary
      - evidence
      - likely_cause
      - next_steps
```

For trace and metrics context, I would choose tool-output shapes based on the debugging task. Metrics workflows may need bucketed values for trends and spikes. Trace workflows need span timing, hierarchy, service/operation names, errors, and latency contributors. I would keep this evidence structured and use realistic troubleshooting benchmarks before recommending schemas for skill authors.

The two user-facing analysis features I would polish through skills are:

- **Natural Language Trace Search:** convert user intent into structured calls to `get_services`, `get_span_names`, and `search_traces`, then show the assumptions and candidate traces.
- **Contextual Trace Explanation:** use the active trace plus `get_trace_topology`, `get_critical_path`, `get_trace_errors`, and targeted `get_span_details` calls to produce an evidence-backed explanation.

For local-first support, I would keep the model runtime in the sidecar/BYOA layer and validate at least one local setup, such as Ollama or another OpenAI-compatible endpoint. The sidecar should report a clear error if the selected model cannot perform tool calling reliably.

For UI integration, I would keep the default Jaeger trace view unchanged and add skill selection, reasoning/tool-step visibility, and trace-linked actions such as span highlighting. If GenAI/logical view work is included, I would make it tolerant of partial telemetry: full rendering when key GenAI attributes exist, generic partial rendering when only some `gen_ai.*` attributes exist, and normal Jaeger rendering when none exist.

### What Technical Challenges Do You Foresee And How Would You Address Them?

The first challenge is safety. I would keep V1 skills declarative only: no custom code, no shell commands, no hidden network access, and no dynamic backend tool registration. Skills would only control how existing Jaeger MCP tools are used.

The second challenge is permission and validation. A skill should not expand model access. I would validate `allowedTools` against registered MCP tools and enforce that allowlist in the sidecar before passing tools to the model. Existing Jaeger tenancy, response limits, and query validation should remain in the MCP handlers.

The third challenge is large trace context. Full traces can be too large and can reduce reasoning quality. I would keep the progressive-disclosure workflow already described in Jaeger's MCP ADR: search first, topology next, critical path/errors next, and full span details only for selected spans.

The fourth challenge is output schema quality. I would compare candidate schemas with troubleshooting prompts such as slow checkout, downstream wait, N+1 database calls, and root-cause-vs-symptom errors. The comparison should measure correctness, groundedness, latency, token size, and ability to cite evidence.

The fifth challenge is local model reliability. Local-first is important for privacy, but local tool calling varies by model. I would document tested models, detect tool-calling failures clearly, and include deterministic fixtures and expected tool flows where possible.

The sixth challenge is backend/UI coordination. The work touches `jaegermcp`, `jaegerai`, sidecars, and `jaeger-ui`, so I would split it into small PRs: skill registry, MCP prompt exposure, sidecar skill use, then gateway/UI events.

### How Do You Plan To Approach The Project?

**Community Bonding / Week 0**

- Reproduce the current Jaeger v2 + MCP + AI gateway + Gemini sidecar setup locally.
- Confirm with mentors the exact V1 skill schema, built-in skills, local-first target, and UI expectations.
- Convert this proposal into a short implementation design that references the existing ADR/RFC files.
- Identify which changes belong in `jaeger` and which must happen in the `jaeger-ui` submodule/repository.

**Month 1: Skills Engine In The MCP Extension**

- Add `Skills` configuration to `cmd/jaeger/internal/extension/jaegermcp/config.go`.
- Implement `cmd/jaeger/internal/extension/jaegermcp/internal/skills/` with loader, parser, validator, registry, and last-known-good reload behavior.
- Validate skill `allowedTools` against the MCP tools registered in `server.go`.
- Add bundled skills for natural-language trace search and contextual trace explanation.
- Expose skills through MCP prompts from the existing `jaegermcp` server.
- Add tests in `config_test.go`, `server_test.go`, and `internal/skills/*_test.go`.

**Month 2: Skill-Aware Agent Execution**

- Update `scripts/ai-sidecar/gemini/sidecar.py` so `_run_agentic_gemini_loop` fetches the selected skill, uses its prompt material, and filters MCP tools.
- Add or scaffold a LangChainGo reference sidecar that follows the same skill + MCP + tool-calling contract.
- Implement the two polished built-in skill flows: natural-language trace search and contextual trace explanation.
- Complete or extend the contextual-tool gateway path in `cmd/jaeger/internal/extension/jaegerquery/internal/jaegerai/handler.go` and `dispatcher.go` where the current PR2 TODOs already identify the integration point.
- Start the schema benchmark harness for trace-context candidates.

**Month 3: UI, Local-First, Documentation, And Polish**

- Add Jaeger UI skill selection and reasoning/tool-step display.
- Wire trace-linked UI actions such as span highlighting through the contextual-tool path.
- Validate a local-first setup with Ollama or another OpenAI-compatible local endpoint.
- Add fixtures for complete, partial, and normal GenAI spans if logical-view fallback is in scope.
- Write the custom skill authoring guide with schema, examples, validation rules, and safe authoring patterns.
- Run the required Jaeger workflow: `make fmt`, `make lint`, and `make test`, and fix issues.

By the end of the mentorship, a Jaeger operator should be able to add a skill file, have Jaeger validate and expose it through MCP, use it in the sidecar's tool-calling loop, and see the selected skill plus reasoning/tool steps in the UI.
