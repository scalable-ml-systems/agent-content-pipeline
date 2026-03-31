
---

# Locked Phase 1 repo tree

```text
agent-content-pipeline/
├── README.md
├── Makefile
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── pipeline.py
│   ├── state.py
│   ├── models.py
│   │
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
│   │
│   ├── clients/
│   │   ├── search_client.py
│   │   └── llm_client.py
│   │
│   ├── prompts/
│   │   ├── extract_facts.txt
│   │   ├── summarize.txt
│   │   ├── draft_post.txt
│   │   ├── validate_draft.txt
│   │   ├── apply_style.txt
│   │   ├── validate_style.txt
│   │   └── generate_image_prompts.txt
│   │
│   ├── templates/
│   │   └── linkedin_style.yaml
│   │
│   └── utils/
│       ├── ids.py
│       ├── time.py
│       ├── logging.py
│       ├── files.py
│       └── json_io.py
│
├── data/
│   ├── inputs/
│   └── outputs/
│
├── tests/
│   ├── test_state.py
│   ├── test_models.py
│   ├── test_pipeline.py
│   ├── test_search_web.py
│   ├── test_extract_facts.py
│   ├── test_summarize.py
│   ├── test_draft_post.py
│   ├── test_apply_style.py
│   ├── test_validate_draft.py
│   └── test_validate_style.py
│
├── docs/
│   ├── tech-spec.md
│   ├── architecture.md
│   ├── phase-plan.md
│   └── prompts.md
│
└── examples/
    ├── kv-aware-routing-topic.txt
    └── sample-run-output.json