from __future__ import annotations

from dataclasses import dataclass

from app.llm_client import LLMClientError, get_llm_client
from app.runtime.artifacts import ArtifactType
from app.runtime.errors import ProviderStepError, ValidationStepError
from app.runtime.retry import DEFAULT_RETRY_POLICY, RetryPolicy
from app.runtime.types import RunState, StepResult


@dataclass(slots=True)
class DraftPostStep:
    name: str = "draft_post"
    retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY

    def run(self, state: RunState) -> StepResult:
        if not state.synthesis:
            raise ValidationStepError("Cannot draft post without synthesis.")

        system_prompt = """
You are a technical content drafting engine.

Write a neutral, source-grounded LinkedIn post draft.

Rules:
- Use only the provided synthesis.
- Do not exaggerate.
- Do not invent claims or statistics.
- Keep the draft concise and professional.
- Avoid hashtags.
- Output plain text only.
""".strip()

        user_prompt = self._build_user_prompt(topic=state.topic, synthesis=state.synthesis)

        client = get_llm_client()

        try:
            raw_output = client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                task="draft",
            )
        except TypeError:
            try:
                raw_output = client.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.3,
                )
            except LLMClientError as exc:
                raise ProviderStepError(str(exc)) from exc
        except LLMClientError as exc:
            raise ProviderStepError(str(exc)) from exc

        draft_post = raw_output.strip()
        if not draft_post:
            raise ValidationStepError("Draft post step returned empty content.")

        return StepResult.success(
            step_name=self.name,
            state_updates={"draft_post": draft_post},
            artifacts=[
                {
                    "artifact_type": ArtifactType.DRAFT_POST,
                    "payload": {"text": draft_post},
                    "metadata": {
                        "topic": state.topic,
                        "source_synthesis_artifact_id": state.latest_artifact_id_by_type.get(
                            ArtifactType.SYNTHESIS.value
                        ),
                    },
                }
            ],
            message="Neutral draft post created successfully.",
            metrics={
                "draft_length_chars": len(draft_post),
            },
        )

    def _build_user_prompt(self, *, topic: str, synthesis: dict) -> str:
        context = synthesis.get("context", "")
        insights = synthesis.get("insights", [])
        implications = synthesis.get("implications", [])
        contrarian_angle = synthesis.get("contrarian_angle", "")

        sections: list[str] = [
            f"Topic: {topic}",
            "",
            f"Context: {context}",
            "",
            "Insights:",
        ]
        sections.extend(f"- {item}" for item in insights)

        sections.append("")
        sections.append("Implications:")
        sections.extend(f"- {item}" for item in implications)

        if contrarian_angle:
            sections.append("")
            sections.append(f"Contrarian angle: {contrarian_angle}")

        return "\n".join(sections).strip()