from __future__ import annotations

import json
from dataclasses import dataclass

from app.llm_client import LLMClientError, get_llm_client
from app.runtime.artifacts import ArtifactType
from app.runtime.errors import ProviderStepError, ValidationStepError
from app.runtime.retry import DEFAULT_RETRY_POLICY, RetryPolicy
from app.runtime.types import RunState, StepResult


@dataclass(slots=True)
class ReviseStyleStep:
    name: str = "revise_style"
    retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY

    def run(self, state: RunState) -> StepResult:
        if not state.draft_post or not state.draft_post.strip():
            raise ValidationStepError("Cannot revise style without draft_post.")
        if not state.styled_post or not state.styled_post.strip():
            raise ValidationStepError("Cannot revise style without styled_post.")
        if not state.style_validation:
            raise ValidationStepError("Cannot revise style without style_validation.")

        issues = state.style_validation.get("issues", [])
        if not issues:
            raise ValidationStepError("Cannot revise style without validation issues.")

        system_prompt = """
You are a style revision engine.

Revise the styled post so that it resolves the validator issues.

Rules:
- Preserve the meaning of the original draft.
- Remove hype inflation and unsupported additions.
- Keep the writing warm, professional, credible, and grounded.
- Output plain text only.
""".strip()

        user_prompt = json.dumps(
            {
                "topic": state.topic,
                "draft_post": state.draft_post,
                "styled_post": state.styled_post,
                "issues": issues,
            },
            ensure_ascii=False,
            indent=2,
        )

        client = get_llm_client()

        try:
            raw_output = client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2,
                task="revise_style",
            )
        except TypeError:
            try:
                raw_output = client.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.2,
                )
            except LLMClientError as exc:
                raise ProviderStepError(str(exc)) from exc
        except LLMClientError as exc:
            raise ProviderStepError(str(exc)) from exc

        revised_style = raw_output.strip()
        if not revised_style:
            raise ValidationStepError("ReviseStyle step returned empty content.")

        return StepResult.success(
            step_name=self.name,
            state_updates={
                "styled_post": revised_style,
                "style_validation": None,
            },
            artifacts=[
                {
                    "artifact_type": ArtifactType.STYLED_POST,
                    "payload": {"text": revised_style},
                    "metadata": {
                        "topic": state.topic,
                        "revision": True,
                        "source_validation_artifact_id": state.latest_artifact_id_by_type.get(
                            ArtifactType.STYLE_VALIDATION.value
                        ),
                    },
                }
            ],
            message="Styled post revised successfully.",
            metrics={
                "issue_count": len(issues),
                "styled_length_chars": len(revised_style),
            },
        )