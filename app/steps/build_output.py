from __future__ import annotations

from dataclasses import dataclass

from app.runtime.artifacts import ArtifactType
from app.runtime.errors import ValidationStepError
from app.runtime.retry import RetryPolicy
from app.runtime.types import RunState, StepResult


NO_RETRY_POLICY = RetryPolicy(max_attempts=1, backoff_seconds=())


@dataclass(slots=True)
class BuildOutputStep:
    name: str = "build_output"
    retry_policy: RetryPolicy = NO_RETRY_POLICY

    def run(self, state: RunState) -> StepResult:
        if not state.synthesis:
            raise ValidationStepError("Cannot build output without synthesis.")
        if not state.draft_post:
            raise ValidationStepError("Cannot build output without draft_post.")
        if not state.draft_validation:
            raise ValidationStepError("Cannot build output without draft_validation.")
        if not state.styled_post:
            raise ValidationStepError("Cannot build output without styled_post.")
        if not state.style_validation:
            raise ValidationStepError("Cannot build output without style_validation.")

        final_output = {
            "run_id": state.run_id,
            "topic": state.topic,
            "status": state.status.value,
            "artifacts": {
                "synthesis_artifact_id": state.latest_artifact_id_by_type.get(
                    ArtifactType.SYNTHESIS.value
                ),
                "draft_post_artifact_id": state.latest_artifact_id_by_type.get(
                    ArtifactType.DRAFT_POST.value
                ),
                "draft_validation_artifact_id": state.latest_artifact_id_by_type.get(
                    ArtifactType.DRAFT_VALIDATION.value
                ),
                "styled_post_artifact_id": state.latest_artifact_id_by_type.get(
                    ArtifactType.STYLED_POST.value
                ),
                "style_validation_artifact_id": state.latest_artifact_id_by_type.get(
                    ArtifactType.STYLE_VALIDATION.value
                ),
                "image_prompts_artifact_id": state.latest_artifact_id_by_type.get(
                    ArtifactType.IMAGE_PROMPTS.value
                ),
            },
            "synthesis": state.synthesis,
            "draft_post": state.draft_post,
            "draft_validation": state.draft_validation,
            "styled_post": state.styled_post,
            "style_validation": state.style_validation,
            "image_prompts": state.image_prompts,
            "completed_steps": list(state.completed_steps),
        }

        return StepResult.success(
            step_name=self.name,
            state_updates={"final_output": final_output},
            artifacts=[
                {
                    "artifact_type": ArtifactType.FINAL_OUTPUT,
                    "payload": final_output,
                    "metadata": {
                        "topic": state.topic,
                        "run_id": state.run_id,
                    },
                }
            ],
            message="Final output artifact built successfully.",
            metrics={
                "completed_step_count": len(state.completed_steps),
                "image_prompt_count": len(state.image_prompts),
            },
        )