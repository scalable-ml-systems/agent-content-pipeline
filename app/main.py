from __future__ import annotations

from uuid import uuid4

from app.runtime.bootstrap import build_orchestrator
from app.runtime.types import RunState


def main() -> None:
    orchestrator = build_orchestrator()

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

    print("\nDraft validation:")
    print(final_state.draft_validation)

    print("\nStyle validation:")
    print(final_state.style_validation)

    print("\nImage prompts:")
    print(final_state.image_prompts)

    print("\nFinal output:")
    print(final_state.final_output)

    print("\nLatest artifact IDs by type:")
    print(final_state.latest_artifact_id_by_type)

    print("\nArtifacts:")
    for artifact in final_state.artifact_store.all():
        print(
            {
                "artifact_id": artifact.artifact_id,
                "type": artifact.artifact_type.value,
                "step_name": artifact.step_name,
                "metadata": artifact.metadata,
            }
        )

    print("\nExecution events:")
    for event in final_state.events:
        print(
            {
                "step": event.step_name,
                "attempt": event.attempt,
                "status": event.status.value,
                "duration_ms": event.duration_ms,
                "error": event.error,
            }
        )


if __name__ == "__main__":
    main()