# LFX Mentorship Journal: Jaeger AI Skills Framework (Phase 2)

**Mentee:** [YOUR NAME]  
**Mentors:** Yuri Shkuro, [other mentors]  
**Term:** 2026 Term 2 (Jun - Aug)

---

## Roadmap

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| M0: Local setup reproduced (Jaeger v2 + MCP + AI gateway + Gemini sidecar) | Week 0 | [ ] |
| M1: Skills Engine loads, validates, and exposes skills via MCP `prompts/list` | End of Month 1 (Week 4) | [ ] |
| M2: Sidecar uses selected skill (prompt + tool filter) in agentic loop | Mid Month 2 (Week 6) | [ ] |
| M3: Contextual-tool browser relay wired end-to-end (RFC-0002 completion) | End of Month 2 (Week 8) | [ ] |
| M4: Local-first validated (Ollama), UI skill selection + reasoning display | Mid Month 3 (Week 10) | [ ] |
| M5: Documentation, benchmarks, polish, all CI green | End of Month 3 (Week 12) | [ ] |

---

## Technical Designs / Discussion

<!-- Use this section for design notes, mentor feedback, and decisions made during the project. -->

### Open Questions (To Confirm With Mentors)

- [ ] Exact V1 skill schema fields — is `constraints` a list of strings or structured rules?
- [ ] Should skills be exposed via MCP `prompts/list` + `prompts/get`, or a separate `/api/skills` endpoint, or both?
- [ ] Local-first target: Ollama only, or also llama.cpp / other OpenAI-compatible?
- [ ] GenAI logical view: in scope for this term, or deferred?
- [ ] Benchmark harness: mentor preference on canonical trace fixtures (reuse existing integration test data vs. new fixtures)?
- [ ] Watch mode / hot-reload: V1 or deferred?

### Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| | | |

---

## Journal

---

### Week of Jun 16, 2026
#### Community Bonding / Week 0

**Goals:**
- [ ] Reproduce the full Jaeger v2 + MCP + AI gateway + Gemini sidecar setup locally
- [ ] Read and annotate the existing ADR, RFC, and sidecar code to build a mental map of data flow
- [ ] Confirm V1 skill schema, built-in skill list, local-first target, and UI scope with mentors
- [ ] Convert proposal into a short implementation design doc referencing existing ADR/RFC files
- [ ] Identify which changes belong in `jaeger` repo vs. `jaeger-ui` submodule

**Progress:**

**{date}**
{provide details about what you did, what worked well & what did not}

**{date}**
{provide details about what you did, what worked well & what did not}

---

### Week of Jun 23, 2026
#### Month 1 / Week 1

**Goals:**
- [ ] Enable Jaeger to parse and validate skill YAML files at startup (schema.go, validator.go)
- [ ] Research: finalize tool-output shapes for the two built-in skills by studying existing MCP handler responses
- [ ] Set up test fixtures (valid, invalid, malformed skill files) for the validation pipeline

**Progress:**

**{date}**
{provide details about what you did, what worked well & what did not}

**{date}**
{provide details about what you did, what worked well & what did not}

---

### Week of Jun 30, 2026
#### Month 1 / Week 2

**Goals:**
- [ ] Enable skill registry to store validated skills in memory and serve them via `prompts/list`
- [ ] Add `Skills` config block to `jaegermcp/config.go` with validation
- [ ] Write unit tests covering: allowedTools check against registered MCP tools, duplicate name rejection, prompt length limits

**Progress:**

**{date}**
{provide details about what you did, what worked well & what did not}

**{date}**
{provide details about what you did, what worked well & what did not}

---

### Week of Jul 07, 2026
#### Month 1 / Week 3

**Goals:**
- [ ] Ship the first two bundled skills: natural-language trace search and contextual trace explanation
- [ ] Wire skills engine into `jaegermcp` server startup so skills load before the server accepts connections
- [ ] Enable `prompts/get` to return the full skill definition including system prompt and allowed tools
- [ ] All tests pass: `make fmt && make lint && make test`

**Progress:**

**{date}**
{provide details about what you did, what worked well & what did not}

**{date}**
{provide details about what you did, what worked well & what did not}

---

### Week of Jul 14, 2026
#### Month 1 / Week 4 (Milestone M1 target)

**Goals:**
- [ ] M1 checkpoint: Jaeger binary loads skill files, validates them, exposes via MCP prompts
- [ ] Submit PR(s) for skills engine; address review feedback
- [ ] Prepare for Month 2: read Gemini sidecar code path for prompt + tool injection

**Progress:**

**{date}**
{provide details about what you did, what worked well & what did not}

**Retrospective:**
- What went well this month:
- What did not go well:
- What I would do differently:

---

### Week of Jul 21, 2026
#### Month 2 / Week 5

**Goals:**
- [ ] Enable the Gemini sidecar to fetch a selected skill and replace the hard-coded system prompt
- [ ] Enable the sidecar to filter MCP tool declarations to the skill's allowlist before passing to the model
- [ ] Research: prototype LangChainGo sidecar scaffold to unblock local-first milestone

**Progress:**

**{date}**
{provide details about what you did, what worked well & what did not}

**{date}**
{provide details about what you did, what worked well & what did not}

---

### Week of Jul 28, 2026
#### Month 2 / Week 6 (Milestone M2 target)

**Goals:**
- [ ] M2 checkpoint: a user can select a skill, and the sidecar uses its prompt + tool filter in the agentic loop
- [ ] Enable the two built-in skill flows end-to-end: NL trace search and contextual trace explanation
- [ ] Start wiring the contextual-tool browser relay (RFC-0002 completion) in handler.go/dispatcher.go

**Progress:**

**{date}**
{provide details about what you did, what worked well & what did not}

**{date}**
{provide details about what you did, what worked well & what did not}

---

### Week of Aug 04, 2026
#### Month 2 / Week 7

**Goals:**
- [ ] Enable trace-linked UI actions (highlight_span, show_flamegraph) to flow through the contextual-tool path end-to-end
- [ ] Start the benchmark harness: define canonical trace fixtures and 3-5 evaluation tasks
- [ ] Submit PR(s) for sidecar skill support; address review feedback

**Progress:**

**{date}**
{provide details about what you did, what worked well & what did not}

**{date}**
{provide details about what you did, what worked well & what did not}

---

### Week of Aug 11, 2026
#### Month 2 / Week 8 (Milestone M3 target)

**Goals:**
- [ ] M3 checkpoint: contextual-tool relay works end-to-end (browser -> gateway -> sidecar -> LLM -> browser)
- [ ] Run benchmark harness against built-in skills and document results (accuracy, token usage, latency)
- [ ] Begin Jaeger UI work: skill selection dropdown and reasoning/tool-step display

**Progress:**

**{date}**
{provide details about what you did, what worked well & what did not}

**Retrospective:**
- What went well this month:
- What did not go well:
- What I would do differently:

---

### Week of Aug 18, 2026
#### Month 3 / Week 9

**Goals:**
- [ ] Enable a user to select a skill and see reasoning/tool steps in the Jaeger UI
- [ ] Validate local-first setup with Ollama (or other OpenAI-compatible endpoint)
- [ ] Document tested local models and their tool-calling reliability

**Progress:**

**{date}**
{provide details about what you did, what worked well & what did not}

**{date}**
{provide details about what you did, what worked well & what did not}

---

### Week of Aug 25, 2026
#### Month 3 / Week 10 (Milestone M4 target)

**Goals:**
- [ ] M4 checkpoint: local-first validated, UI skill selection and reasoning display working
- [ ] If in scope: add GenAI view fixtures (complete, partial, normal spans) and 3-rule fallback rendering
- [ ] Start writing the "How to Author Custom AI Skills for Jaeger" guide

**Progress:**

**{date}**
{provide details about what you did, what worked well & what did not}

**{date}**
{provide details about what you did, what worked well & what did not}

---

### Week of Sep 01, 2026
#### Month 3 / Week 11

**Goals:**
- [ ] Complete the skill authoring guide with schema, examples, validation rules, and safe patterns
- [ ] Address all pending PR review feedback across jaeger and jaeger-ui repos
- [ ] Fix any remaining lint/test failures: `make fmt && make lint && make test`

**Progress:**

**{date}**
{provide details about what you did, what worked well & what did not}

**{date}**
{provide details about what you did, what worked well & what did not}

---

### Week of Sep 08, 2026
#### Month 3 / Week 12 (Milestone M5 target)

**Goals:**
- [ ] M5 checkpoint: all PRs merged or ready for final review, CI green, documentation complete
- [ ] Enable a Jaeger operator to add a skill file, have Jaeger validate and expose it, use it in the sidecar, and see results in the UI
- [ ] Write final mentorship summary / blog post

**Progress:**

**{date}**
{provide details about what you did, what worked well & what did not}

**Final Retrospective:**
- What went well this term:
- What did not go well:
- What I would do differently:
- What I learned:
