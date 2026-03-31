agent-content-pipeline/
│
├── app/
│   ├── pipeline/              # Phase 1 (legacy path - keep working)
│   │   ├── steps/
│   │   └── runner.py
│
│   ├── runtime/               # 🆕 Phase 2 core (NEW SYSTEM)
│   │   ├── orchestrator.py
│   │   ├── graph.py
│   │   ├── step_registry.py
│   │   ├── types.py
│   │   ├── contracts.py
│   │   ├── artifacts.py
│   │   ├── validators.py
│   │   ├── errors.py
│   │   └── telemetry.py
│
│   ├── steps/                 # 🆕 refactored steps (shared)
│   │   ├── search_web.py
│   │   ├── extract_facts.py
│   │   ├── retrieve_context.py   # RAG
│   │   ├── summarize.py
│   │   ├── draft_post.py
│   │   └── ...
│
│   ├── agents/                # 🆕 Phase 2 grouping
│   │   ├── research_agent.py
│   │   ├── retrieval_agent.py
│   │   ├── synthesis_agent.py
│   │   ├── drafting_agent.py
│   │   └── verification_agent.py
│
│   ├── retrieval/             # 🆕 RAG layer
│   │   ├── index.py
│   │   ├── chunking.py
│   │   ├── query_builder.py
│   │   └── retriever.py
│
│   ├── store/                 # 🆕 persistence
│   │   ├── models.py
│   │   └── repository.py
│
│   ├── evals/                 # 🆕 evaluation harness
│   │   ├── runner.py
│   │   └── scoring.py
│
│   └── llm_client.py          # shared (you already have this)
│
├── outputs/                   # run artifacts
├── docs/
│   ├── phase1.md
│   ├── PHASE_2.md
│   └── architecture.md
│
├── main.py                    # entrypoint
└── Makefile / scripts