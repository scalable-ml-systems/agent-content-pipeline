# Architecture — Phase 1 Agent Content Pipeline

## Purpose

Phase 1 builds a deterministic content pipeline in plain Python.

The goal is to learn the mechanics of agentic systems directly:
- state
- tool boundaries
- step-wise transformations
- validation
- persistence
- degraded execution behavior

This phase intentionally avoids orchestration frameworks.

---

## System Shape

```text
topic
  → search_web
  → extract_facts
  → summarize
  → draft_post
  → validate_draft
  → apply_style
  → validate_style
  → generate_image_prompts
  → build_output

The control flow is fixed.

The system is not yet planner-driven or multi-agent.
It is a single-process runtime built to make every transformation explicit.

Core Components
1. Shared State

The pipeline operates over one explicit state object.

The state stores:

raw inputs
derived artifacts
validation results
step logs
errors
metadata

This makes execution inspectable and debuggable.

2. Steps

Each step has one bounded responsibility.

Examples:

search_web collects normalized external inputs
extract_facts converts sources into atomic evidence
summarize produces structured understanding
draft_post converts understanding into communicable form
validators check grounding and drift
generate_image_prompts derives visual representations
build_output persists the final artifact
3. Clients

Provider-specific logic is kept behind clients.

Current boundaries:

search_client.py
llm_client.py

This keeps step logic independent from transport and provider details.

Data Flow
Search Layer

search_web reads the topic and stores normalized search results.

Output:

title
url
snippet
Fact Layer

extract_facts transforms search results into atomic facts with provenance.

Each fact includes:

fact
source_url
source_title

This is the grounding layer of the system.

Synthesis Layer

summarize converts facts into:

context
insights
implications
contrarian angle
Drafting Layer

draft_post produces a neutral first draft.

Validation Layer

validate_draft and validate_style act as trust gates.

They exist because generation and rewriting can introduce drift.

Style Layer

apply_style rewrites the neutral draft into a more personal tone while preserving meaning.

Visual Layer

generate_image_prompts turns the final post into image prompts for later use with image models.

Output Layer

build_output assembles and saves the final artifact.

Persistence

Each run is persisted as a JSON artifact in data/outputs/.

This gives the system:

replayable evidence
inspectable outputs
future eval data
a simple audit trail
Degraded Execution

Phase 1 does not yet implement retries or branching workflows.

But it does implement visible degraded behavior:

provider failures append errors
parsing failures append validation issues
fallback outputs are used where appropriate
runs remain inspectable even when not ideal

This is important because agentic systems are defined as much by how they fail as by how they succeed.

Why This Architecture Exists

This architecture is intentionally simpler than modern multi-agent frameworks.

It exists to teach:

what state is required before orchestration
where evidence is introduced
where drift enters
where validation belongs
how outputs should be persisted
what later becomes an agent node

Phase 1 is the baseline.

Phase 2 will add:

specialized agents
planning
branching
retries
richer observability
more durable memory/state