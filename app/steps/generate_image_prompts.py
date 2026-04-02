from __future__ import annotations

from dataclasses import dataclass

from app.llm_client import LLMClientError, get_llm_client
from app.runtime.artifacts import ArtifactType
from app.runtime.errors import ProviderStepError, ValidationStepError
from app.runtime.retry import DEFAULT_RETRY_POLICY, RetryPolicy
from app.runtime.types import RunState, StepResult


@dataclass(slots=True)
class GenerateImagePromptsStep:
    name: str = "generate_image_prompts"
    retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY

    def run(self, state: RunState) -> StepResult:
        source_text = (state.styled_post or state.draft_post or "").strip()
        if not source_text:
            raise ValidationStepError(
                "Cannot generate image prompts without draft or styled post."
            )

        system_prompt = """
You are a visual concept generation engine.

Generate 2 to 4 image prompts for editorial-style illustrations based on the provided post.

Rules:
- Focus on systems, architecture, engineering, evidence flow, validation, and grounded technical themes.
- Do not include text overlays.
- Keep prompts visually clear and professional.
- Output valid JSON only with this shape:
{
  "image_prompts": ["string", "string"]
}
""".strip()

        user_prompt = self._build_user_prompt(
            topic=state.topic,
            source_text=source_text,
        )

        client = get_llm_client()

        try:
            raw_output = client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5,
                task="generate_image_prompts",
            )
        except TypeError:
            try:
                raw_output = client.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.5,
                )
            except LLMClientError as exc:
                raise ProviderStepError(str(exc)) from exc
        except LLMClientError as exc:
            raise ProviderStepError(str(exc)) from exc

        image_prompts = self._parse_image_prompts(raw_output)

        return StepResult.success(
            step_name=self.name,
            state_updates={"image_prompts": image_prompts},
            artifacts=[
                {
                    "artifact_type": ArtifactType.IMAGE_PROMPTS,
                    "payload": {"image_prompts": image_prompts},
                    "metadata": {
                        "topic": state.topic,
                        "source_styled_artifact_id": state.latest_artifact_id_by_type.get(
                            ArtifactType.STYLED_POST.value
                        ),
                        "source_draft_artifact_id": state.latest_artifact_id_by_type.get(
                            ArtifactType.DRAFT_POST.value
                        ),
                    },
                }
            ],
            message="Image prompts generated successfully.",
            metrics={"image_prompt_count": len(image_prompts)},
        )

    def _build_user_prompt(self, *, topic: str, source_text: str) -> str:
        return f"Topic: {topic}\n\nPost:\n{source_text}".strip()

    def _parse_image_prompts(self, raw_output: str) -> list[str]:
        import json

        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise ValidationStepError(
                f"GenerateImagePrompts step returned invalid JSON: {exc}"
            ) from exc

        prompts = data.get("image_prompts")
        if not isinstance(prompts, list):
            raise ValidationStepError(
                "GenerateImagePrompts response missing list 'image_prompts'."
            )

        cleaned: list[str] = []
        for item in prompts:
            if isinstance(item, str) and item.strip():
                cleaned.append(item.strip())

        if not cleaned:
            raise ValidationStepError("GenerateImagePrompts returned no usable prompts.")

        return cleaned[:4]