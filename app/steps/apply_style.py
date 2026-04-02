from __future__ import annotations

from dataclasses import dataclass

from app.llm_client import LLMClientError, get_llm_client
from app.runtime.artifacts import ArtifactType
from app.runtime.errors import ProviderStepError, ValidationStepError
from app.runtime.retry import DEFAULT_RETRY_POLICY, RetryPolicy
from app.runtime.types import RunState, StepResult


@dataclass(slots=True)
class ApplyStyleStep:
    name: str = "apply_style"
    retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY

    def run(self, state: RunState) -> StepResult:
        if not state.draft_post or not state.draft_post.strip():
            raise ValidationStepError("Cannot apply style without draft post.")

        system_prompt = """
You are a style rewriting engine.

Rewrite the provided draft in this style:
- warm
- professional
- credible
- reflective
- grounded
- technically literate
- no hype inflation
- no hashtags

Rules:
- Preserve the original meaning.
- Do not add unsupported claims.
- Do not add statistics or facts not already present.
- Keep the output concise.
- Output plain text only.
""".strip()

        user_prompt = self._build_user_prompt(
            topic=state.topic,
            draft_post=state.draft_post,
        )

        client = get_llm_client()

        try:
            raw_output = client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.4,
                task="apply_style",
            )
        except TypeError:
            try:
                raw_output = client.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.4,
                )
            except LLMClientError as exc:
                raise ProviderStepError(str(exc)) from exc
        except LLMClientError as exc:
            raise ProviderStepError(str(exc)) from exc

        styled_post = raw_output.strip()
        if not styled_post:
            raise ValidationStepError("ApplyStyle step returned empty content.")

        return StepResult.success(
            step_name=self.name,
            state_updates={"styled_post": styled_post},
            artifacts=[
                {
                    "artifact_type": ArtifactType.STYLED_POST,
                    "payload": {"text": styled_post},
                    "metadata": {
                        "topic": state.topic,
                        "source_draft_artifact_id": state.latest_artifact_id_by_type.get(
                            ArtifactType.DRAFT_POST.value
                        ),
                    },
                }
            ],
            message="Styled post created successfully.",
            metrics={
                "styled_length_chars": len(styled_post),
            },
        )

    def _build_user_prompt(self, *, topic: str, draft_post: str) -> str:
        sections = [
            f"Topic: {topic}",
            "",
            "Draft:",
            draft_post,
        ]
        return "\n".join(sections).strip()