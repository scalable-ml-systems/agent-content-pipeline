# Recommended Build Path

## Phase 1 — Bare-metal Agent Pipeline
Build the system as plain Python with no agent framework.

### What You Learn Here
- What the state actually is
- What each step is allowed to do
- Where hallucination enters
- Where validation should sit
- How outputs degrade
- How tool boundaries should look

### What You Build
topic:
- `search_web`
- `extract_facts`
- `summarize`
- `draft_post`
- `validate_draft`
- `apply_style`
- `validate_style`
- `generate_image_prompts`
- `final_output`

### Required Capabilities
- Explicit state object
- Step logs
- Structured outputs
- Visible errors
- Saved run artifact

**This is your system’s foundation.**

---

## Phase 2 — Real Agent Decomposition
Once Phase 1 works, convert steps into specialized agents.

### Example Agent Mapping
to be implemented:
- PlannerAgent
- ResearchAgent
-
ExtractorAgent
-
SynthesizerAgent
-
WriterAgent
-
StyleAgent
-
CriticAgent
-
ImagePromptAgent

### What Changes
you are not changing the business flow yet.
you are changing the execution model.

definition:
From:
topic:
txt,
decorated with ordered function calls,
to:
topic:
txt,
over shared state with role-based nodes.
This teaches:
- Agent boundaries 
 - Task handoff 
 - Intermediate artifacts 
 - Role specialization 
 - Controlled delegation 
---
## Phase 3 — Planning + Routing
Now introduce actual agentic behavior.
Add:
- Planner decides whether research is sufficient.
- Critic can send draft back for rewrite.
Optional branches for "needs more evidence" and "skip image prompts".
### What You Learn
your system will understand:
e.g., conditional edges, re-entry into previous nodes, loop control, bounded retries, policy over execution.
this is where it becomes a real agent workflow.
---
## Phase 4 — Memory and Persistence
durable state addition:
such as file-based run persistence first, then SQLite/Postgres;
past runs as references; reusable source cache; template versioning.
### What You Learn
e.g., short-term vs persistent memory, replayability, run auditability, state recovery.
this is critical. Most “agent demos” collapse here.
---
## Phase 5 — Evaluation and Observability
enabling quality measurement:
groundedness checks, source coverage metrics, unsupported claim count, style-preservation checks, per-step latency, retry count, tool failure stats.
your system will be measured systems—not just working or not. Evals are part of runtime—this starts looking like production engineering.
'this is where you start looking like production engineering.'
