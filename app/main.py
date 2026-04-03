from __future__ import annotations

import json
from uuid import uuid4

from app.runtime.bootstrap import build_orchestrator
from app.runtime.replay import RuntimeReplayer
from app.runtime.types import RunState
from app.store.repository import SQLiteRuntimeRepository


def main() -> None:
    db_path = "data/runtime.db"
    orchestrator = build_orchestrator(db_path=db_path)

    state = RunState(
        run_id=str(uuid4()),
        topic="KV cache in LLM inference",
        facts=[
            {
                "fact": "KV cache stores prior attention keys and values so they can be reused during decoding.",
                "source_title": "LLM systems overview",
                "source_url": "https://example.com/kv-cache",
                "evidence_snippet": "Keys and values from earlier tokens are reused.",
            },
            {
                "fact": "Longer contexts increase memory pressure because cached attention state grows with sequence length.",
                "source_title": "Inference scaling notes",
                "source_url": "https://example.com/long-context",
                "evidence_snippet": "Memory footprint rises as cached sequence state grows.",
            },
        ],
    )

    final_state = orchestrator.run(state)

    print("Run status:", final_state.status.value)
    print("Completed steps:", final_state.completed_steps)
    print("Failed step:", final_state.failed_step)
    print("Error:", final_state.error)

    print("\nFinal output:")
    print(json.dumps(final_state.final_output, indent=2))

    replayer = RuntimeReplayer(repository=SQLiteRuntimeRepository(db_path=db_path))
    report = replayer.render_text_report(final_state.run_id)

    print("\n" + report)


if __name__ == "__main__":
    main()