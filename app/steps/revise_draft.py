from __future__ import annotations

import json
from dataclasses import dataclass

from app.llm_client import LLMClientError, get_llm_client
from app.runtime.artifacts import ArtifactType
from app.runtime.errors import ProviderStepError, ValidationStepError
from app.runtime.retry import DEFAULT_RETRY_POLICY, RetryPolicy
from app.runtime.types import RunState, StepResult


@dataclass(slots=True)
class ReviseDraftStep:
    name: str = "revise_draft"
    retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY

    def run(self, state: RunState) -> StepResult:
        if not state.synthesis:
            raise ValidationStepError("Cannot revise draft without synthesis.")
        if not state.draft_post or not state.draft_post.strip():
            raise ValidationStepError("Cannot revise draft without draft_post.")
        if not state.draft_validation:
            raise ValidationStepError("Cannot revise draft without draft_validation.")

        issues = state.draft_validation.get("issues", [])
        if not issues:
            raise ValidationStepError("Cannot revise draft without validation issues.")

        system_prompt = """
You are a draft revision engine.

Revise the provided draft so that it resolves the validator issues.

Rules:
- Use only the provided synthesis.
- Fix only the issues listed.
- Preserve valid content where possible.
- Do not add unsupported claims.
- Keep the draft concise and professional.
- Output plain text only.
""".strip()

        user_prompt = json.dumps(
            {
                "topic": state.topic,
                "synthesis": state.synthesis,
                "draft_post": state.draft_post,
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
                task="revise_draft",
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

        revised_draft = raw_output.strip()
        if not revised_draft:
            raise ValidationStepError("ReviseDraft step returned empty content.")

        return StepResult.success(
            step_name=self.name,
            state_updates={
                "draft_post": revised_draft,
                "draft_validation": None,
            },
            artifacts=[
                {
                    "artifact_type": ArtifactType.DRAFT_POST,
                    "payload": {"text": revised_draft},
                    "metadata": {
                        "topic": state.topic,
                        "revision": True,
                        "source_validation_artifact_id": state.latest_artifact_id_by_type.get(
                            ArtifactType.DRAFT_VALIDATION.value
                        ),
                    },
                }
            ],
            message="Draft revised successfully.",
            metrics={
                "issue_count": len(issues),
                "draft_length_chars": len(revised_draft),
            },
        )