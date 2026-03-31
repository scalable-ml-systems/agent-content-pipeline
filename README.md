# Agent Content Pipeline — Phase 1

> A bare-metal, framework-free agentic content pipeline built in plain Python.
> Give it a topic. Get a source-grounded LinkedIn post, structured facts, and image prompts — with full execution traceability.

---

## What this is

This project converts a topic into a fully sourced, validated LinkedIn post by running it through a fixed, inspectable pipeline of steps.

But content generation is only half the story.

The deeper goal is to understand agentic systems from first principles — how state flows between steps, where hallucination enters, where validation belongs, and what an orchestration framework is actually doing under the hood. Phase 1 builds all of that by hand, deliberately, without any AI framework magic.

This is the foundation that will later evolve into a multi-agent system.

---

## What it produces

From a single topic, the pipeline outputs:

- a set of sourced search results
- atomic extracted facts with provenance
- a structured synthesis (context, insights, implications)
- a neutral draft post
- a styled LinkedIn-ready post
- validation reports for both the draft and the styled version
- 2–4 image prompts
- a full JSON run artifact saved to disk

---

## Pipeline

```
topic
  └── search_web          → raw search results + sources
  └── extract_facts       → atomic, source-grounded facts
  └── summarize           → context, insights, implications
  └── draft_post          → neutral LinkedIn skeleton
  └── validate_draft      → checks for unsupported claims
  └── apply_style         → rewrites in preferred voice
  └── validate_style      → checks for drift or hype inflation
  └── generate_image_prompts → 2–4 visual prompt ideas
  └── build_output        → final JSON artifact persisted to disk
```

Each step reads specific fields from shared state, performs one bounded transformation, and writes structured output back. Nothing is hidden. Nothing is implicit.

---

## State model

The entire pipeline operates over one explicit shared state object:

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
        "summary": {},
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
    "metadata": {}
}
```

`raw` holds unprocessed data. `derived` holds transformed outputs. `validation` holds trust signals. Nothing mixes.

---

## Design principles

- **No hidden orchestration** — execution is visible in code and easy to reason about
- **State is the source of truth** — every meaningful artifact lives in state
- **Raw ≠ derived** — search results and interpreted outputs are never mixed
- **Preserve grounding** — every fact carries provenance; every rewrite is checked
- **Validate before trusting** — two explicit validation checkpoints, after draft and after styling
- **Fail visibly** — no silent failures; every step writes a log entry; every exception is captured
- **Build for inspectability** — every run saves a traceable JSON artifact to disk

---

## Project structure

```
agent-content-pipeline/
├── pipeline/
│   ├── runner.py               # pipeline runner — sequencing only, no business logic
│   ├── state.py                # state initialisation and shape
│   ├── steps/
│   │   ├── search_web.py
│   │   ├── extract_facts.py
│   │   ├── summarize.py
│   │   ├── draft_post.py
│   │   ├── validate_draft.py
│   │   ├── apply_style.py
│   │   ├── validate_style.py
│   │   ├── generate_image_prompts.py
│   │   └── build_output.py
│   └── contracts.py            # data contracts and schema definitions
├── outputs/                    # run artifacts saved here
├── tests/
│   ├── test_contracts.py
│   └── test_pipeline.py
├── config.py
├── requirements.txt
└── README.md
```

---

## Getting started

### 1. Clone the repo

```bash
git clone https://github.com/your-username/agent-content-pipeline.git
cd agent-content-pipeline
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

```bash
export ANTHROPIC_API_KEY=your_key_here
export SEARCH_API_KEY=your_search_key_here   # e.g. Tavily or SerpAPI
```

### 4. Run the pipeline

```bash
python -m pipeline.runner --topic "the rise of AI agents in enterprise software"
```

### 5. Inspect the output

The full run artifact is saved under `outputs/` as a timestamped JSON file:

```
outputs/
└── run_20240315_143022.json
```

---

## Data contracts

Every artifact in the pipeline has an explicit schema.

**Fact**
```json
{
  "fact": "",
  "source_url": "",
  "source_title": "",
  "fact_type": "stat | claim | definition | trend | contradiction",
  "evidence_snippet": "",
  "confidence": "high | medium | low"
}
```

**Step log**
```json
{
  "step": "",
  "status": "ok | warning | error",
  "started_at": "",
  "ended_at": "",
  "items_in": 0,
  "items_out": 0,
  "message": ""
}
```

**Final output artifact**
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

## Validation

Validation is a first-class part of the runtime, not an afterthought.

Two checkpoints run on every execution:

- **validate_draft** — checks the neutral draft against the extracted fact set. Flags unsupported claims, unsourced numbers, and drift from the source material.
- **validate_style** — checks the styled post against the same fact set. Flags hype inflation, semantic drift, or new claims introduced during the style rewrite.

Validation failures do not halt the run in Phase 1, but they are always logged and surfaced in the final artifact.

---

## Failure handling

Phase 1 does not implement production-grade retries, but it never fails silently.

- Every step writes a log entry regardless of outcome
- Every exception is captured into `state["errors"]`
- Degraded runs (too few results, low fact count, empty prompts) continue with warnings and remain fully inspectable
- Partial output is acceptable if clearly marked in the artifact

---

## Why no framework?

Most agent projects reach for LangGraph, CrewAI, or AutoGen too early.

That builds familiarity with abstractions before you understand what those abstractions are doing.

Phase 1 skips the framework intentionally, so that every mechanic — state shape, step boundaries, tool calls, validation placement, error capture — is written and understood by hand.

Phase 2 will introduce a proper multi-agent execution model. It will be meaningful because Phase 1 already taught the internals.

---

## Phase 2 roadmap

Once Phase 1 is stable, the system will evolve into:

- step-to-agent decomposition
- planner-based dynamic routing
- conditional edges and branching
- bounded retries with backoff
- persistent DB-backed state
- evaluation harness and groundedness metrics
- richer observability (traces, dashboards, run replay)
- enterprise integrations

---

## Running tests

```bash
pytest tests/
```

Tests cover core data contracts, state initialisation, and the full pipeline execution path.

---

## License

APACHE 2.0