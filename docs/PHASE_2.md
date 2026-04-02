# PHASE 2 — Bounded Agent Runtime with RAG-Augmented Execution

## Overview

Phase 2 evolves the system from a fixed sequential pipeline into a bounded, graph-capable orchestration runtime with retrieval-augmented grounding (RAG).

The system transitions from:

```
linear execution
        ↓
adaptive, validation-driven execution with structured state, retrieval, and persistence
```

The goal is to build a system that is:

- **Grounded** — evidence-backed
- **Inspectable** — full traceability
- **Bounded** — no uncontrolled loops
- **Replayable** — persistent state
- **Adaptive** — conditional routing
- **Measurable** — evaluation + observability

---

## Core Principle

> Deterministic execution harness with bounded nondeterministic generation and retrieval-constrained context

**Deterministic runtime behavior:**
- graph traversal
- retries and limits
- branching conditions
- state transitions

**Probabilistic LLM behavior, constrained via:**
- structured inputs
- RAG-bounded context
- validators as execution gates

---

## Phase 1 → Phase 2 Evolution

| Dimension | Phase 1 | Phase 2 |
|---|---|---|
| Execution | Sequential pipeline | Graph-capable runtime |
| Context | Raw search → prompt chaining | Retrieval-augmented context (RAG) |
| Artifacts | Raw text chaining | Typed artifacts |
| Validation | Post-check | Validation-driven control flow |
| State | None | Persistent execution state |
| Agents | None | Specialized agents |
| Evaluation | None | Evaluation harness |

---

## System Architecture

### High-Level Flow

```
topic
  ↓
Orchestrator Runtime
  ↓
Execution Graph (bounded)
  ↓
Research → Evidence → Retrieval → Synthesis → Draft → Validation → Style
  ↓
Persistent State Store (DB)
  ↓
Final Output + Full Execution Trace
```

### Pipeline (Phase 2)

```
topic
  └── search_web                → raw sources
  └── extract_facts             → atomic facts
  └── retrieve_context (RAG)    → top-k evidence chunks
  └── validate_retrieval        → quality + coverage check
  └── summarize                 → structured synthesis
  └── draft_post                → neutral post
  └── validate_draft            → groundedness check
  └── apply_style               → voice transformation
  └── validate_style            → drift detection
  └── generate_image_prompts    → visual prompts
  └── build_output              → persisted artifact
```

---

## Runtime Components

### 1. Orchestrator (Control Plane)

Responsible for:
- graph traversal
- retry + backoff
- branching decisions
- state updates
- safe termination

> The orchestrator never generates content.

### 2. Execution Graph

A bounded DAG with conditional edges:

```
extract_facts
  → retrieve_context
  → validate_retrieval
      → sufficient     → summarize
      → insufficient   → expand_search → extract_facts

validate_draft
  → pass → apply_style
  → fail → revise_draft

validate_style
  → pass → generate_image_prompts
  → fail → revise_style
```

**Constraints:**
- no infinite loops
- bounded retries
- explicit termination conditions

### 3. Central Run State

All steps operate on a shared structured state:

```python
@dataclass
class RunState:
    run_id: str
    topic: str

    search_results: list
    source_documents: list

    facts: list
    retrieved_context: list
    retrieval_report: dict

    synthesis: dict | None

    draft_post: str | None
    draft_validation: dict | None

    styled_post: str | None
    style_validation: dict | None

    image_prompts: list[str]

    status: str
```

---

## RAG Layer (NEW)

### Purpose

Replace raw prompt-to-prompt context propagation with retrieval of bounded, relevant, source-linked evidence.

### Step: `retrieve_context`

**Input:**
- topic
- extracted facts
- source documents

**Output:**

```json
{
  "retrieved_context": [
    {
      "chunk_id": "doc_12_chunk_03",
      "source_url": "https://example.com/article",
      "title": "Example article",
      "text": "Retrieved passage...",
      "score": 0.87
    }
  ]
}
```

### Retrieval Strategy

1. Chunk source documents
2. Embed chunks
3. Vector search (top-k)
4. Query built from topic, extracted facts, and key entities

### Step: `validate_retrieval`

Ensures:
- sufficient coverage of facts
- source diversity
- minimal duplication
- relevance threshold

### Why RAG Matters

| Without RAG | With RAG |
|---|---|
| Prompt size grows uncontrollably | Bounded context |
| Grounding weakens | Explicit provenance |
| Hallucination risk increases | Smaller prompts |
| No traceability | Stronger validation |

---

## Step Contracts

Each step is a typed unit:

```python
class Step(Protocol):
    name: str

    def run(self, state: RunState) -> StepResult:
        ...
```

Each step defines:
- inputs (from state)
- outputs (to state)
- retry policy
- model routing
- validation hooks

---

## Agent Specialization

| Agent | Responsibility |
|---|---|
| `ResearchAgent` | search + expansion |
| `EvidenceAgent` | fact extraction |
| `RetrievalAgent` | RAG retrieval + ranking |
| `SynthesisAgent` | summarization |
| `DraftingAgent` | draft + style |
| `VerificationAgent` | validation |
| `Orchestrator` | execution control |

---

## Validators (Execution Gates)

| Validator | Purpose |
|---|---|
| Retrieval Validator | ensures evidence quality |
| Fact Coverage Validator | ensures sufficient information |
| Groundedness Validator | checks unsupported claims |
| Style Drift Validator | prevents exaggeration |

Validators can:
- allow progression
- trigger retry
- trigger branch
- terminate execution

---

## Retry Policy

```
MAX_STEP_RETRIES = 2
BACKOFF = [1s, 2s]
```

Applied to:
- LLM failures
- retrieval failures
- validation failures

---

## Persistent Execution Layer

### Tables

**`runs`**
- `run_id`
- `topic`
- `status`
- `timestamps`

**`step_runs`**
- `step_name`
- `attempt`
- `status`
- `latency`
- `error`

**`artifacts`**
- `type` (facts, retrieval, draft, etc.)
- `payload` (JSON)

### Observability

Each step emits:
- `step_name`
- `model_used`
- `latency`
- `token_usage`
- `retrieval_scores`
- `validation_scores`
- `retry_count`

---

## Evaluation Harness

**Metrics:**
- groundedness score
- unsupported claims
- retrieval quality score
- style drift score
- retry frequency
- token usage
- latency

---

## Execution Model

### Deterministic Control
- graph traversal fixed
- retries bounded
- validation gates enforced

### Controlled Non-Determinism
- LLM outputs probabilistic
- retrieval results ranked
- outputs constrained via schema + validators

---

## Design Constraints

- No unbounded loops
- No raw prompt chaining across steps
- All context must be retrieved or structured
- Every output must be traceable to a source
- All steps must be replayable

---

## Definition of Done

Phase 2 is complete when the system can:

- [ ] Execute via graph with conditional routing
- [ ] Retrieve and validate evidence via RAG
- [ ] Operate on structured artifacts (not raw text)
- [ ] Retry steps safely
- [ ] Persist and replay runs
- [ ] Enforce validation before progression
- [ ] Evaluate quality across runs

---

## Outcome

At the end of Phase 2, the system becomes a **production-grade, retrieval-augmented agent runtime** capable of grounded, adaptive, and observable execution with bounded control.