# LFX Mentorship 2026 Proposal
## Jaeger: AI-Powered Trace Analysis Phase 2 — Self-Service Skills Framework

**Program:** LFX Mentorship, CNCF  
**Applicant:** [YOUR NAME] | **Email:** [YOUR EMAIL] | **GitHub:** [YOUR GITHUB] | **Timezone:** [YOUR TIMEZONE]

---

## About You

### Why Are You Interested In This Specific Project?

[FILL in your own voice — the suggested framing below, replace entirely with your story]

Phase 1 gave Jaeger a working AI assistant. Phase 2 is the harder and more interesting problem: making that assistant configurable without a recompile. A "find slow traces" workflow and a "explain a critical path regression" workflow need different system prompts, different tool allowlists, and different output expectations. Hardcoding those into the agent does not scale to the diverse debugging workflows that real operators run. Building a declarative Skills Framework — cleanly, safely, without turning Jaeger into an unreviewed plugin host — is the exact engineering problem I want to work on.

I was drawn to this after carefully reading the Phase 1 codebase, ADR-002, and the A2A architecture document. The BYOA direction is the right call: Jaeger's job is to be the best MCP data source and agent bridge, not to compete with Claude Code or Gemini CLI. The Skills Framework is what makes that bridge useful to teams with their own debugging workflows.

### Relevant Experience

[FILL: replace with actual proof points — projects, PRs, coursework. Below is suggested structure]

- Go backend development: OpenTelemetry Collector extensions, component lifecycle, REST/gRPC APIs
- LLM integration: tool calling, agentic loops, MCP protocol (tools and prompts capabilities), prompt engineering
- Python async for AI sidecar work: streaming responses, Google ADK, model API clients
- React/TypeScript for data-heavy observability UIs, Ant Design, Redux
- Testing: unit tests, integration tests, fixture-driven test harnesses, CI pipelines

### Open Source Experience

[FILL: link notable PRs/issues]

- Jaeger contributions: [link]
- CNCF / observability: [link]
- AI tooling / Go: [link]

### Time Commitments

[FILL: weekly hours, timezone overlap with mentors, any exam/internship conflicts]

---

## About the Project

### How I Understand What Needs to Be Done

I studied the Phase 1 codebase before writing this proposal and traced every component involved in the current AI assistant flow.

#### The Specific Gap

`JaegerSidecarAgent` in `scripts/ai-sidecar/gemini/sidecar.py` has one fixed system prompt and exposes all eight MCP tools to the model on every session. The system instruction is hardcoded inside `_run_agentic_gemini_loop()`:

```python
system_instruction = (
    "You are Jaeger AI, an assistant for distributed tracing investigations. ..."
)
```

The `JaegerMCPBridge` in `scripts/ai-sidecar/gemini/mcp_bridge.py` calls `self._toolset.get_tools()` once at initialization and passes all discovered tools to Gemini as `FunctionDeclaration`s. There is no concept of a workflow — a "find slow traces" session and a "explain a critical path regression" session see the same prompt and the same tool set. The only way an operator can change this today is to modify Python code and redeploy.

Meanwhile, the `ChatHandler` in `cmd/jaeger/internal/extension/jaegerquery/internal/jaegerai/handler.go` creates an ACP session with no skill context. The `ChatRequest` struct carries only the user's free-text `prompt`. There is an explicit `TODO(PR2)` comment in the handler for wiring additional metadata into `NewSessionRequest._meta` — that is the integration point this proposal targets.

#### What Phase 1 Built

The `jaegermcp` extension at `cmd/jaeger/internal/extension/jaegermcp/` registers eight reviewed tools in `server.go`'s `registerTools()`: `get_services`, `get_span_names`, `search_traces`, `get_trace_topology`, `get_critical_path`, `get_span_details`, `get_trace_errors`, `get_service_dependencies`. These are served over Streamable HTTP on port 16687. The AI gateway at `POST /api/ai/chat` dials the sidecar over ACP WebSocket, runs `Initialize → NewSession → Prompt`, and streams `session/update` events back through `streaming_client.go`.

ADR-002 draws a hard line: MCP tools are backend data tools; browser-scoped actions like `highlight_span` are conversation-scoped and routed through `ExtMethodJaegerToolCall` in `dispatcher.go`, never through MCP. The A2A architecture document sets the BYOA direction — Jaeger's job is to be the best MCP data source and agent bridge, not to build its own reasoning engine.

The maintainer confirmed the tool output principle: outputs should preserve the structural dimensions needed for the troubleshooting task — timing, parent-child relationships, service/operation boundaries, error state, and critical-path information. The Skills Engine must not flatten that into text too early.

#### What Phase 2 Adds

One missing layer: a Skills Engine. An operator drops a YAML file into a configured directory, Jaeger validates and loads it, and the next agent session that selects that skill runs with a different system prompt, a restricted tool subset, explicit constraints, few-shot examples, and output expectations — without touching any Go or Python code.

---

### Proposed Solution

Phase 2 adds exactly one new layer on top of Phase 1: a Skills Engine that makes the agent configurable without recompilation. The MCP server, gateway, and sidecar architecture stay intact. Skills are declarative — system prompt material, developer prompt context, constraints, few-shot examples, output expectations, and a constrained list of allowed existing MCP tools. Skills compose tools; they do not register new runtime behavior. This boundary keeps the security model simple, validation tractable, and new tool behavior where it belongs — in reviewed Go code. The maintainer confirmed this explicitly: *"skills compose and guide tools; they should not become an unreviewed plugin/runtime-code mechanism."*

#### Skill Definition Format

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
    You are a distributed tracing expert. Base your analysis exclusively on
    Jaeger MCP tool results. Preserve timing, parent-child relationships,
    service/operation boundaries, error state, and critical-path evidence.
    Never flatten trace structure into plain text before the model has had
    a chance to reason over the structured form.
  developerPrompt: |
    Always follow the progressive disclosure sequence: topology first,
    then critical path, then errors, then full span attributes only for
    targeted spans.
  examples:
    - input: "Why is checkout slow in trace abc123?"
      steps:
        - call get_trace_topology to understand the span tree
        - call get_critical_path to identify latency-concentrated spans
        - call get_trace_errors to check for error-status spans
        - call get_span_details only for spans on the critical path
      expectedOutput: >
        Summary identifying the root service, timing evidence from
        critical path, and a concrete next-steps recommendation.
  constraints:
    - Do not invent services, spans, errors, or timings.
    - Ask for span details before making attribute-level claims.
    - If get_trace_topology returns empty, report it clearly and suggest
      broadening the trace search before proceeding.
  output:
    sections: [summary, evidence, likely_cause, next_steps]
```

`allowedTools` is validated at load time against the exact names in `server.go`'s `registerTools()`. An unknown tool name is a hard load-time error. A skill only ever restricts access — existing MCP handler limits and Jaeger tenancy remain the runtime enforcement layer.

#### How a Skill Travels Through the Stack

```
operator drops skill.yaml into configured directory
          │
          ▼
loader.go       parses YAML, enforces file size limit
          │
          ▼
validator.go    checks every allowedTools entry against registerTools() names
                → unknown name: load failure, previous valid set stays active
          │
          ▼
registry.go     stores skill in memory, calls server.AddPrompt() on the MCP server
                emits notifications/prompts/list_changed to connected MCP clients
          │
          ▼
server.go       serves skill via prompts/list + prompts/get
                (each skill → one mcp.Prompt; systemPrompt+developerPrompt+constraints
                 assembled into GetPromptResult.Messages[0].content.text)
          │
    user picks skill from UI dropdown (populated via prompts/list)
          │
          ▼
handler.go      adds skill_name to ChatRequest; passes it in NewSession._meta
(jaegerquery/   over ACP WebSocket to the sidecar (resolves the TODO(PR2) comment)
internal/
jaegerai/)
          │
          ▼
sidecar.py      reads skill_name from field_meta in new_session()
                calls prompts/get on MCP server
                replaces hardcoded system_instruction with skill systemPrompt +
                developerPrompt + constraints
                filters FunctionDeclarations to allowedTools only before
                passing them to Gemini's GenerateContentConfig
                runs agentic loop — model can only call permitted tools
          │
          ▼
browser         receives session/update stream showing reasoning steps + tool calls
```

#### Skills Engine Package

New package at `cmd/jaeger/internal/extension/jaegermcp/internal/skills/`, following the existing `internal/criticalpath/` and `internal/handlers/` pattern:

```
skills/
├── skill.go       Go struct mirroring the YAML schema
├── loader.go      file discovery, YAML parsing, size enforcement
├── validator.go   allowedTools cross-check against a provided tool name set
├── registry.go    in-memory store, last-known-good reload, AddPrompt registration
└── benchmark/     deterministic fixture harness for built-in skill validation
```

`config.go` gains a nested `SkillsConfig`:

```go
type SkillsConfig struct {
    Enabled        bool     `mapstructure:"enabled"`
    Directories    []string `mapstructure:"directories"`
    WatchMode      bool     `mapstructure:"watch_mode"`
    MaxFileSizeKiB int      `mapstructure:"max_file_size_kib" valid:"range(1|1024)"`
}
```

Validation uses the existing `govalidator` struct tag pattern already established in `config.go` (`valid:"range(1|100)"`, `valid:"required"`). No new validation library is introduced.

In `server.go`, `Start()` calls `registerTools()` first (to establish the known tool name set), then initializes the skills registry — so the validator receives the exact registered names before any skill file is parsed. A file-watcher in watch mode rescans on change; if validation passes, the registry updates and calls `AddPrompt()` on the `mcpServer` and emits `notifications/prompts/list_changed` to connected clients. On validation failure, the previous valid set stays loaded and the error is logged.

#### Mapping Skills to MCP Prompts

MCP's `prompts` capability (`prompts/list`, `prompts/get`) is precisely designed for reusable, named context templates. The Go SDK (`github.com/modelcontextprotocol/go-sdk v1.6.0`) already used in the repo has full support: `Server.AddPrompt()`, `GetPromptResult`, and `PromptMessage`.

Each loaded skill is registered as:

```go
s.mcpServer.AddPrompt(&mcp.Prompt{
    Name:        skill.Name,
    Title:       skill.Metadata.Description,
    Description: skill.Spec.Description,
}, func(ctx context.Context, req *mcp.GetPromptRequest) (*mcp.GetPromptResult, error) {
    content := buildSkillContent(skill) // assembles systemPrompt + developerPrompt + constraints
    return &mcp.GetPromptResult{
        Description: skill.Metadata.Description,
        Messages: []*mcp.PromptMessage{{
            Role:    mcp.RoleUser,
            Content: mcp.NewTextContent(content),
        }},
    }, nil
})
```

The sidecar calls `prompts/get` once at session start via the existing `MCPToolset` connection in `mcp_bridge.py`, reads `messages[0].content.text` as the replacement for `system_instruction`, and extracts the `allowedTools` list (passed as structured metadata in the prompt result) to filter `FunctionDeclaration`s.

#### ACP Session Integration

The `ChatHandler` in `jaegerquery/internal/jaegerai/handler.go` needs two changes:

1. `ChatRequest` gains an optional `skillName string` JSON field — the UI populates it from the dropdown selection.
2. In the `NewSession` call, `skill_name` is injected into `_meta` alongside the AG-UI tools snapshot (fulfilling the existing `TODO(PR2)` comment in the handler).

The sidecar's `new_session()` already reads `kwargs.get("field_meta")` for contextual tools. `skill_name` is added to that same meta dict. No ACP protocol changes are needed.

No-skill fallback: if `skill_name` is absent or the named skill is not found, the sidecar falls back to all tools + the hardcoded `system_instruction` — fully backward compatible with existing sessions.

#### Built-In Skills

Two skills embedded at build time via `//go:embed`, following the `INSTRUCTIONS.md` pattern in `server.go`:

**`natural-language-trace-search`** — converts a user's natural-language query into structured backend calls. `allowedTools`: `get_services`, `get_span_names`, `search_traces`. Enforces the ADR-002 first step: return metadata only, do not load span attributes until the user has identified a specific trace.

**`contextual-trace-explanation`** — explains why a specific trace is slow or failing. `allowedTools`: `get_trace_topology`, `get_critical_path`, `get_trace_errors`, `get_span_details`. Enforces full progressive disclosure: topology → critical path → error details → full span attributes only for targeted spans. The TraceLLM benchmark (WWW 2026, DOI 10.1145/3774904.3792164) validates this ordering — structured progressive access improves LLM root-cause accuracy by 34.77% over open-source baselines.

Both built-in skills include concrete `examples` entries. Before their schemas are frozen, each skill is validated against four canonical trace fixtures (slow checkout, downstream timeout, N+1 database queries, root-cause vs. symptom) using a deterministic harness at `skills/benchmark/` that initializes a mock MCP server returning the fixture's trace data and replays expected tool call sequences without a live LLM. Task-level correctness — did the agent identify the right root cause and cite the correct span IDs and timings from the fixture — is the primary evaluation metric. This is the "benchmark real agent tasks against candidate schemas" approach the maintainer identified as the right validation method.

#### UI Changes

**Skill selection dropdown.** The chat panel adds a dropdown populated by calling MCP's `prompts/list` on the configured MCP endpoint. Each entry shows the skill name and description. The selected skill name is included in the `ChatRequest` payload.

**Collapsible reasoning steps.** Each `session/update` event from the ACP stream that contains a `tool_call` or `tool_result` marker is surfaced as a collapsible step in the chat panel. No new protocol or backend change is needed — the existing `streaming_client.go` markers (`[tool_call]`, `[tool_result]`) are already present in the stream; the UI parser expands them.

---

### Technical Challenges and How I Would Address Them

**Skills becoming an unreviewed plugin mechanism.** The risk is operators expecting to embed arbitrary logic in skill files. I enforce the boundary at two points: load-time validation of `allowedTools` against registered MCP tool names (unknown name = load failure), and sidecar-side filtering so only `allowedTools` are passed to the model as `FunctionDeclaration`s for that session. The `systemPrompt`, `developerPrompt`, `constraints`, and `examples` fields accept only static text — no code, no shell commands, no network access from a skill file. An operator who needs a new tool submits a PR to `registerTools()`, not a skill file.

**Testing skill-driven agent behavior without a live LLM.** The agentic loop's correctness depends on model output, which is non-deterministic and cannot be in CI. I split the testing surface: the Go skills engine is tested with pure unit tests against file/YAML/validation logic; the sidecar's prompt-replacement and tool-filtering logic is tested with a mock MCP server returning canned responses, exercising the filtering code without a real model; the benchmark harness replays expected tool call sequences against deterministic fixtures to validate built-in skill schemas before they ship.

**Skill schema stability for operators.** A schema change after operators have written skill files will break them silently. The `apiVersion` field is the versioning hook — the loader rejects files with an unrecognized version with an explicit error. Built-in skills run through the same parser in CI, so any breaking schema change fails the build before reaching operators.

**Local model tool-calling reliability.** Local models (Ollama, llama.cpp) vary significantly in tool-call quality. The sidecar must detect when a model returns a plain text response on a turn that should have produced a tool call, and surface a named error rather than silently returning a low-quality answer. Tested models and known failure modes are documented in the local-first setup guide.

**Infinite agentic loops.** A ReAct agent can stall — repeatedly calling the same tool, failing to synthesize a final answer, or cycling on a dead-end branch. The sidecar enforces a hard iteration cap (e.g., 15 turns) as a circuit breaker. On cap, the loop terminates and returns partial findings accumulated so far, rather than deadlocking or timing out silently.

**ACP session metadata compatibility.** The `field_meta` mechanism in the Python ACP runtime already handles `contextual_tools`. Adding `skill_name` to the same dict requires verifying the sidecar's `new_session()` kwargs parsing handles the extended meta without regression. This is covered by the existing `test_sidecar_workflow.py` test suite, which will be extended with a skill-aware session test.

---

### Roadmap and Schedule

#### Community Bonding

Reproduce the full Phase 1 stack locally (jaegermcp, sidecar, jaeger-ui). Run the existing integration test in `integration_test.go`. Confirm with mentors: final skill schema fields, built-in skill list, and target local model for Ollama validation.

#### Month 1 — Skills Engine in `jaegermcp`

**Week 1–2: Loader, validator, registry**
- `SkillsConfig` added to `config.go` with `govalidator` struct tags
- `internal/skills/` package: `skill.go` (Go struct mirroring YAML schema), `loader.go` (file discovery, YAML parsing, size enforcement), `validator.go` (allowedTools cross-check), `registry.go` (in-memory store, last-known-good reload)
- `server.go` `Start()` wires registry after `registerTools()`, passes known tool name set to validator
- Unit tests: valid skill loads; unknown tool name is a load failure; malformed YAML is rejected; oversized file is rejected; reload after bad file leaves previous set intact; `apiVersion` mismatch is an explicit error

**Week 3: MCP prompts registration and hot-reload**
- `registry.go` calls `server.AddPrompt()` for each loaded skill; `GetPromptResult` assembles `systemPrompt + developerPrompt + constraints` into `Messages[0].content.text`
- File-watcher emitting `notifications/prompts/list_changed` on directory changes
- Integration test: start extension → `prompts/list` returns expected count → `prompts/get` returns correct assembled content → drop invalid file → list unchanged

**Week 4: Built-in skills**
- `//go:embed` for `natural-language-trace-search.yaml` and `contextual-trace-explanation.yaml` (includes `systemPrompt`, `developerPrompt`, `examples`, `constraints`, `output` fields)
- Both YAML files run through the same parser in CI — any breaking schema change fails the build before reaching operators
- Milestone: skills engine passing all unit + integration tests; built-in skill YAML authored and embedded

#### Month 2 — Sidecar Integration and Local Validation

**Week 5–6: Sidecar skill selection**
- `ChatRequest` in `handler.go` gains optional `skillName` field
- `handler.go` injects `skill_name` into `NewSession._meta` (resolves `TODO(PR2)`)
- `sidecar.py` `new_session()` reads `skill_name` from `field_meta` → calls `prompts/get` → extracts assembled content as replacement `system_instruction` and `allowedTools` list
- `mcp_bridge.py` `get_gemini_tools()` gains optional `allowed_tools: set[str]` param; filters `FunctionDeclaration`s before passing to Gemini
- No-skill fallback: all tools + hardcoded `system_instruction` (fully backward compatible)
- Integration test: mock MCP server verifies only `allowedTools` are passed to the model constructor; second test verifies no-skill path is unchanged

**Week 7–8: Benchmark harness and local-first validation**
- Benchmark harness at `skills/benchmark/`: mock MCP server + four canonical trace fixtures (slow checkout, downstream timeout, N+1 database queries, root-cause vs. symptom); asserts tool call sequence matches expected progressive-disclosure order and final response cites correct span IDs
- Run both built-in skills end-to-end through the harness with Ollama; schema frozen only after both pass
- Detect and log named errors when the model returns text on a turn that should have produced a tool call
- Document tested models and known failure modes in `scripts/ai-sidecar/gemini/README.md`
- Milestone: both built-in skills pass benchmark with Ollama; schemas frozen; named error detection documented

#### Month 3 — UI and Documentation

**Week 9–10: Jaeger UI and end-to-end validation**
- Skill selection dropdown in the chat panel calling `prompts/list` on the MCP endpoint; populates skill name + description; selected skill name included in `ChatRequest`
- Collapsible reasoning steps from `session/update` stream markers: `[tool_call]` / `[tool_result]` markers parsed and surfaced as expandable steps in the chat panel
- End-to-end skill selection flow test: UI picks skill → `ChatRequest` carries `skillName` → handler injects into `NewSession._meta` → sidecar applies correct system prompt and tool filter → response streamed back; verified against the two built-in skills
- UI tests: dropdown populated with correct skill list from mock MCP; reasoning steps render in correct order; no-skill path unchanged
- Milestone: full skill selection flow verified end-to-end; skill dropdown and reasoning steps live in chat panel

**Week 11–12: Documentation and polish**
- Skill authoring guide: schema reference, `allowedTools` safety rules, `examples` format, output schema patterns, validation error catalogue, `apiVersion` migration guide
- `make fmt && make lint && make test` clean across all changed packages
- Milestone: authoring guide complete; all tests passing

#### Milestones

| End of | Testable output |
|--------|----------------|
| Week 2 | Skills engine: loader, validator, registry passing all unit tests |
| Week 3 | MCP prompts: `prompts/list` + `prompts/get` + hot-reload integration test passing |
| Week 4 | Built-in skill YAML authored and embedded; parser in CI |
| Week 6 | Sidecar: skill selection + tool filtering integration test passing; `handler.go` TODO(PR2) resolved |
| Week 8 | Benchmark harness complete; both built-in skills pass with Ollama; schemas frozen |
| Week 10 | Full skill selection flow verified end-to-end; skill dropdown and reasoning steps live |
| Week 12 | Authoring guide complete; `make test` clean; all milestones verified end-to-end |

---

### References

- Jaeger MCP ADR-002: `docs/adr/002-mcp-server.md` in the Jaeger repository
- MCP Prompts Specification (2025-06-18): https://modelcontextprotocol.io/specification/2025-06-18/server/prompts
- TraceLLM — LLM Trace Analysis Benchmark, ACM WWW 2026: DOI 10.1145/3774904.3792164
- OpenTelemetry GenAI Semantic Conventions: https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/
- MCP Go SDK (`github.com/modelcontextprotocol/go-sdk v1.6.0`): `Server.AddPrompt`, `GetPromptResult`, `PromptMessage`
- RedHat MCP Gateway security model: https://developers.redhat.com/articles/2025/12/12/advanced-authentication-authorization-mcp-gateway
- jaegertracing/jaeger#7827 (Skills Framework upstream issue)
