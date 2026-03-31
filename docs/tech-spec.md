# Tech Spec — Phase 1: Bare-Metal Agent Content Pipeline

## 1. Purpose

Build a bare-metal, loop-based agent-content pipeline in plain Python that converts a topic into:

- source set
- extracted facts
- structured synthesis
- neutral draft
- styled LinkedIn post
- image prompts
- final run artifact

This phase is intentionally framework-free.

The goal is to learn the mechanics of agentic systems directly:
- state
- step boundaries
- tool usage
- data contracts
- validation
- execution flow
- traceability

This is not a multi-agent framework build.
This is the foundational runtime that later becomes one.

---

## 2. Why We Are Building It This Way

Most agent projects hide the hard parts behind orchestration frameworks too early.

That creates abstraction familiarity without systems understanding.

Phase 1 avoids that trap.

We are building the pipeline manually first so we can understand:

- what state actually needs to exist
- how information moves across steps
- where hallucination enters
- where validation belongs
- what should later become an agent node
- how to make outputs inspectable and debuggable

This phase is the learning spine for later multi-agent and production-grade upgrades.

---

## 3. Phase 1 Goals

### 3.1 Learning Goal
Understand the first principles of an agentic pipeline by implementing it directly in code.

### 3.2 Utility Goal
Generate source-grounded LinkedIn-ready technical content quickly from a topic.

### 3.3 Architecture Goal
Create a pipeline shape that can cleanly evolve into:

- planner-based routing
- multi-agent decomposition
- graph orchestration
- retries and fault handling
- persistent memory/state
- evaluation and observability
- enterprise integrations

---

## 4. Non-Goals

Phase 1 explicitly does **not** include:

- multi-agent orchestration
- LangGraph / CrewAI / AutoGen / Semantic Kernel
- dynamic planning
- branching workflows
- retries with backoff
- async fan-out
- persistent DB-backed memory
- queue-based execution
- distributed workers
- human approval gates
- enterprise connectors
- automatic publishing to LinkedIn
- image generation API execution

These belong to later phases.

---

## 5. System Overview

Phase 1 is a single-process Python runtime that executes a fixed ordered pipeline over explicit shared state.

Execution model:

topic → search → extract → summarize → draft → validate → style → validate → image-prompts → output

The control flow is deterministic.
The content generation steps may use probabilistic model outputs, but execution order and state transitions are fixed and inspectable.

Each step:
- reads specific fields from shared state
- performs one bounded transformation
- writes structured outputs back to state
- appends execution metadata
- returns updated state

---

## 6. Design Principles

### 6.1 No hidden orchestration
Execution should be visible in code and easy to reason about.

### 6.2 Shared state is the source of truth
Every meaningful artifact must live in state.

### 6.3 Separate raw from derived data
Search results and raw LLM outputs must not be mixed with interpreted outputs.

### 6.4 Preserve grounding
Facts, summaries, drafts, and styled posts must remain source-grounded.

### 6.5 Validate before trusting
Any rewriting step can introduce drift. Validation is mandatory.

### 6.6 Build for inspectability
Each run should leave behind a traceable artifact.

### 6.7 Make future migration easy
Each step should later map cleanly to a dedicated agent node or graph node.

---

## 7. Phase 1 Execution Progression

Phase 1 is built in this exact progression:

1. state model
2. data/output contracts
3. pipeline runner
4. search client
5. extract facts step
6. summarize step
7. draft step
8. style step
9. validators
10. image prompts
11. run artifact persistence
12. basic tests

This order is locked because it teaches the system from the inside out.

---

## 8. Execution Flow

The Phase 1 runtime executes this pipeline:

1. `search_web`
2. `extract_facts`
3. `summarize`
4. `draft_post`
5. `validate_draft`
6. `apply_style`
7. `validate_style`
8. `generate_image_prompts`
9. `build_output`

The pipeline runner is responsible only for:
- sequencing
- step timing
- error capture
- final artifact assembly

Business logic belongs in steps, not in the runner.

---

## 9. State Model

The system operates over one explicit shared state object.

Example shape:

```python
state = {
    "run_id": "",
    "topic": "",
    "raw": {
        "search_results": [],
        "llm_outputs": {}
    },
    "derived": {
        "facts": [],
        "summary": {
            "context": "",
            "insights": [],
            "implications": [],
            "contrarian_angle": ""
        },
        "draft": "",
        "styled_post": "",
        "image_prompts": []
    },
    "sources": [],
    "validation": {
        "draft_ok": False,
        "style_ok": False,
        "issues": []
    },
    "step_logs": [],
    "errors": [],
    "metadata": {
        "created_at": "",
        "template_version": "v1",
        "models": {}
    }
}


## 10. State Semantics

### 10.1 raw
Holds unprocessed or near-unprocessed artifacts:
- Search results
- Raw LLM outputs if needed for debugging

### 10.2 derived
Holds transformed artifacts:
- Facts
- Summary
- Draft
- Styled output
- Image prompts

### 10.3 validation
Holds trust signals:
- Whether draft passed checks
- Whether style pass preserved truth
- Structured issues discovered

### 10.4 step_logs
Execution metadata for each step:
- Status
- Timing
- Item counts
- Warning/error messages

### 10.5 errors
Run-level errors that must never be silently discarded

---

## 11. Data Contracts

### 11.1 Search Result
```json
{
    "title": "",
    "url": "",
    "snippet": ""
}
```

### 11.2 Fact
```json
{
    "fact": "",
    "source_url": "",
    "source_title": "",
    "fact_type": "stat|claim|definition|trend|contradiction",
    "evidence_snippet": "",
    "confidence": "high|medium|low"
}
```

### 11.3 Summary
```json
{
    "context": "",
    "insights": [],
    "implications": [],
    "contrarian_angle": ""
}
```

### 11.4 Validation Issue
```json
{
    "step": "",
    "severity": "low|medium|high",
    "message": ""
}
```

### 11.5 Step Log
```json
{
    "step": "",
    "status": "ok|warning|error",
    "started_at": "",
    "ended_at": "",
    "items_in": 0,
    "items_out": 0,
    "message": ""
}
```

### 11.6 Final Output Artifact
```json
{
    "run_id": "",
    "topic": "",
    "post": "",
    "image_prompts": [],
    "sources": [],
    "facts": [],
    "summary": {},
    "validation": {},
    "errors": []
}
```

---

## 12. Step Contracts

Every step must declare:
- Required input fields
- Output fields written
- Fields it must not mutate
- Degraded-mode behavior
- Failure behavior

Steps should be designed to be pure with respect to business logic as much as possible.

---

## 13. Functional Modules

### 13.1 `search_web(state)`

**Reads:** `state["topic"]`

**Writes:**
- `state["raw"]["search_results"]`
- `state["sources"]`

**Responsibilities:**
- Call configured search provider
- Fetch top relevant results
- Normalize raw source artifacts

**Rules:**
- No summarization
- No interpretation
- No invented data

**Degraded Mode:** If fewer than target results are found, continue with warning

---

### 13.2 `extract_facts(state)`

**Reads:** `state["raw"]["search_results"]`

**Writes:**
- `state["derived"]["facts"]`
- Optional raw extraction trace under `state["raw"]["llm_outputs"]`

**Responsibilities:**
- Extract atomic, source-grounded facts
- Identify: stats, claims, definitions, trends, contradictions

**Rules:**
- No final synthesis
- No style
- Every fact must carry provenance

**Degraded Mode:** If fact count is low, continue but mark warning

---

### 13.3 `summarize(state)`

**Reads:** `state["derived"]["facts"]`

**Writes:** `state["derived"]["summary"]`

**Responsibilities:** Convert facts into structured brief: context, 3–5 insights, implications, optional contrarian angle

**Rules:**
- Neutral tone only
- Summarize only from facts
- No unsupported additions

---

### 13.4 `draft_post(state)`

**Reads:** `state["derived"]["summary"]`

**Writes:** `state["derived"]["draft"]`

**Responsibilities:** Convert structured summary into a LinkedIn-ready skeleton: hook, body, example or implication, takeaway, closing line / CTA

**Rules:**
- Preserve meaning exactly
- No style mimicry yet
- No unsupported factual additions

---

### 13.5 `validate_draft(state)`

**Reads:**
- `state["derived"]["draft"]`
- `state["derived"]["facts"]`

**Writes:**
- `state["validation"]["draft_ok"]`
- Appends issues to `state["validation"]["issues"]`

**Responsibilities:**
- Detect unsupported claims
- Detect unsourced numbers/statements
- Flag drift from fact set

**Rules:**
- Validation must be explicit and visible
- Failure does not have to halt the run in Phase 1, but must be logged

---

### 13.6 `apply_style(state, templates)`

**Reads:**
- `state["derived"]["draft"]`
- Style templates

**Writes:** `state["derived"]["styled_post"]`

**Responsibilities:** Rewrite draft into preferred voice and structure

**Rules:**
- Preserve meaning
- Do not add facts
- Avoid hype inflation
- Remain concrete and credible

---

### 13.7 `validate_style(state)`

**Reads:**
- `state["derived"]["styled_post"]`
- `state["derived"]["facts"]`

**Writes:**
- `state["validation"]["style_ok"]`
- Appends issues to `state["validation"]["issues"]`

**Responsibilities:**
- Detect unsupported claims introduced during styling
- Detect semantic drift relative to facts/draft

---

### 13.8 `generate_image_prompts(state)`

**Reads:** `state["derived"]["styled_post"]`

**Writes:** `state["derived"]["image_prompts"]`

**Responsibilities:** Produce 2–4 visual prompts based on final post meaning

**Rules:**
- No text inside image
- Prefer minimal, high-contrast, LinkedIn-friendly visuals
- Reflect the post's core metaphor or system idea

---

### 13.9 `build_output(state)`

**Reads:** Final state

**Writes:**
- Final returned artifact
- Optional persisted JSON under outputs directory

**Responsibilities:**
- Normalize final output contract
- Save run artifact for inspection and reuse

---

## 14. Pipeline Runner Responsibilities

The pipeline runner does not contain business logic. It only:
- Initializes state
- Executes steps in fixed order
- Captures timing
- Captures exceptions
- Appends step logs
- Assembles final artifact
- Optionally persists output

This separation is important because later: runner logic becomes orchestration/runtime logic, and steps become agent nodes.

---

## 15. Validation Philosophy

Validation is a first-class part of the runtime. It exists because:
- Summarization can compress too aggressively
- Drafting can generalize too much
- Styling can introduce drift or exaggeration

Phase 1 includes two validation points: after drafting and after styling. These are the earliest trust layers in the system.

Later phases may add: source coverage scoring, groundedness metrics, evaluator agents, policy gates.

---

## 16. Observability in Phase 1

Phase 1 uses lightweight observability.

**Required:**
- Run ID
- Per-step logs
- Timing
- Warning/error capture
- Final run artifact saved to disk

This is intentionally minimal, but it creates the habit of inspectable execution.

Later phases may add: traces, metrics, dashboards, run replay views, evaluator telemetry.

---

## 17. Failure Handling in Phase 1

Phase 1 does not implement production-grade retries, but it must fail visibly.

**Rules:**
- No silent failures
- Every step writes a log entry
- Every exception is captured into errors
- Degraded runs remain inspectable
- Partial output is acceptable if clearly marked

**Example degraded conditions:**
- Too few search results
- Too few facts
- Validation failure
- Empty image prompts

---

## 18. Output Persistence

Each run should be saved as a JSON artifact under an outputs directory. Why:
- Inspectability
- Reproducibility
- Portfolio examples
- Future evaluation dataset
- Replay support later

This is the beginning of durable agent-system thinking.

---

## 19. Phase 1 Definition of Done

Phase 1 is complete when:
- Repo scaffold is created
- State model is implemented
- Data contracts are implemented
- Pipeline runner executes in fixed order
- Search step works
- Fact extraction works
- Summary generation works
- Draft generation works
- Style rewrite works
- Both validation steps work
- Image prompts are generated
- Final artifact is saved to disk
- Basic tests exist for core contracts and pipeline path

---

## 20. Why This Phase Matters

Phase 1 is not a toy prelude. It is the systems foundation.

By building this phase manually, we learn:
- What state must exist before orchestration
- Where quality breaks
- Where validation belongs
- How agent roles should later be split
- What memory and observability should capture
- How to evolve a pipeline into a real agent runtime

This is what makes Phase 2 meaningful rather than cosmetic.

---

## 21. Phase 2 Upgrade Path

After Phase 1 is stable, the system will evolve into a multi-agent execution model.

**Expected upgrades:**
- Step-to-agent decomposition
- Planner-based routing
- Conditional edges
- Bounded retries
- Persistent state
- Evaluation harness
- Richer observability
- Enterprise integrations

Phase 1 teaches the internals. Phase 2 formalizes them into an agent system.