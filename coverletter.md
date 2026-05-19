# Cover Letter — LFX Mentorship 2026
## Jaeger: AI-Powered Trace Analysis Phase 2 — Self-Service Skills Framework

**Applicant:** [YOUR NAME]
**Email:** d87manish@gmail.com
**GitHub:** [YOUR GITHUB]
**Timezone:** [YOUR TIMEZONE]

---

### How I Found This Program

[FILL: e.g. "I discovered LFX Mentorship through the CNCF community while following Jaeger's development. After reading the Phase 1 pull requests and the A2A architecture document, I found the Phase 2 issue and knew this was the project I wanted to apply for."]

---

### Why I Am Interested

Jaeger is not a hobby project — it is production observability infrastructure used by real engineering teams under real pressure. Adding AI to it is not about building a chatbot; it is about making trace investigation faster, safer, and more explainable for on-call engineers who need answers in minutes, not hours.

Phase 1 established the foundation: an MCP server with eight reviewed tools, an AI gateway, and a Gemini sidecar. Phase 2 is the harder and more interesting problem. A "detect N+1 database queries" workflow and a "explain a critical path regression" workflow need different system prompts, different tool subsets, and different output constraints. Hardcoding that into the agent does not scale. The Skills Framework — a declarative layer that lets operators configure agent behavior without touching Go or Python code — is the missing piece, and it is exactly the kind of systems problem I want to work on.

What draws me specifically is the constraint: skills must be purely declarative. No templating engines, no shell access, no arbitrary runtime code. Enforcing that boundary cleanly — at load time in the Go registry and at session start in the sidecar — while keeping the system extensible is a precise engineering challenge. The BYOA direction in the A2A architecture document is the right call: Jaeger should be the best MCP data source and agent bridge, not compete with Claude Code or Gemini CLI. Phase 2 is what makes that bridge genuinely useful to teams with their own debugging workflows.

---

### Applicable Experience and Skills

**Go and distributed systems.** I have worked on Go backends involving REST and gRPC APIs, component lifecycle management, and structured configuration patterns — directly applicable to building the `internal/skills/` package (loader, validator, registry) and extending `config.go` with the `SkillsConfig` block.

**OpenTelemetry and observability.** I understand the OTel Collector extension model, how components are wired together, and how Jaeger's MCP extension fits within that. My contributions to Jaeger include migrating alert rules to Jaeger v2 otelcol metrics and converting a React component to hooks — work that required reading the full stack, not just isolated files.

**LLM agents and protocol integration.** I have worked with agentic loops, tool calling, and MCP/ACP-style protocol design. I understand the failure modes — context exhaustion, infinite loops, silent degradation on missing tool calls — and how to build circuit breakers and deterministic fallbacks around them.

**React and TypeScript for observability UIs.** The GenAI Logical View and skill dropdown require careful UI work: lazy-loading massive prompt payloads, three-rule fallback rendering based on `gen_ai.*` attribute presence, and surfacing reasoning steps from a streaming `session/update` channel. I have built data-heavy React interfaces before and understand the performance trade-offs.

**Testing and documentation discipline.** The benchmark harness — four canonical trace fixtures, task-level correctness as the primary metric, mock MCP server for sidecar testing without a live LLM — requires the same rigour I have applied in contributions across Jaeger, PostgreSQL tooling (pgmoneta, pgexporter, pgagroal), and Kubeflow.

**Breadth across real codebases.** Beyond Jaeger, I have merged contributions to PostgreSQL tooling projects (Grafana dashboard updates, AES encryptor optimization, Prometheus integration, CLI test coverage) and Kubeflow (TrainJob events API, Volcano scheduler fix). Working across these projects has given me the habit of reading unfamiliar code carefully before writing any.

---

### What I Hope to Get Out of This Experience

**Depth on production-grade AI system design.** Building a Skills Framework that is secure, testable, and operator-friendly — inside a real CNCF project with real users — is not something I can replicate in a side project. I want to understand what "production-ready" actually means for agentic systems: not just whether the agent returns a correct answer, but whether the system degrades gracefully, logs failures clearly, and stays maintainable as new skills are added.

**Mentorship from engineers who have shipped observability infrastructure at scale.** The maintainers have made deliberate architectural choices — the declarative skills boundary, the BYOA direction, the MCP prompts capability over a custom API — and I want to understand the reasoning behind each of those decisions directly, not just by reading code.

**A concrete, merged contribution.** By the end of the term I want the Skills Engine, the skill-aware sidecar, the GenAI UI view, and the authoring guide to be in the Jaeger codebase — reviewed, tested, and usable by the community. A shipped feature, not a prototype.

**Foundation for continued open source work.** LFX Mentorship is not a one-time project for me. I plan to stay involved in Jaeger and the broader CNCF observability ecosystem after the term ends. The relationships and review discipline built during mentorship are as valuable as the code.
