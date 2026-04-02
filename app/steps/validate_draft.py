from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.llm_client import LLMClientError, get_llm_client
from app.runtime.artifacts import ArtifactType
from app.runtime.errors import ProviderStepError, ValidationStepError
from app.runtime.retry import DEFAULT_RETRY_POLICY, RetryPolicy
from app.runtime.types import RunState, StepResult


@dataclass(slots=True)
class ValidateDraftStep:
    name: str = "validate_draft"
    retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY

    def run(self, state: RunState) -> StepResult:
        if not state.synthesis:
            raise ValidationStepError("Cannot validate draft without synthesis.")
        if not state.draft_post or not state.draft_post.strip():
            raise ValidationStepError("Cannot validate empty draft post.")

        system_prompt = """
You are a strict draft validation engine.

Return valid JSON only with this shape:
{
  "ok": true,
  "issues": [
    {
      "type": "string",
      "detail": "string"
    }
  ]
}

Rules:
- Validate the draft only against the provided synthesis.
- Flag unsupported claims.
- Flag hype or exaggeration.
- Flag factual drift from the synthesis.
- Return JSON only.
""".strip()

        user_prompt = self._build_user_prompt(
            topic=state.topic,
            synthesis=state.synthesis,
            draft_post=state.draft_post,
        )

        client = get_llm_client()

        try:
            raw_output = client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.0,
                task="validate_draft",
            )
        except TypeError:
            try:
                raw_output = client.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.0,
                )
            except LLMClientError as exc:
                raise ProviderStepError(str(exc)) from exc
        except LLMClientError as exc:
            raise ProviderStepError(str(exc)) from exc

        report = self._parse_validation_report(raw_output)

        return StepResult.success(
            step_name=self.name,
            state_updates={"draft_validation": report},
            artifacts=[
                {
                    "artifact_type": ArtifactType.DRAFT_VALIDATION,
                    "payload": report,
                    "metadata": {
                        "topic": state.topic,
                        "source_draft_artifact_id": state.latest_artifact_id_by_type.get(
                            ArtifactType.DRAFT_POST.value
                        ),
                        "source_synthesis_artifact_id": state.latest_artifact_id_by_type.get(
                            ArtifactType.SYNTHESIS.value
                        ),
                    },
                }
            ],
            message="Draft validation completed.",
            metrics={
                "issue_count": len(report.get("issues", [])),
                "ok": bool(report.get("ok", False)),
            },
        )

    def _build_user_prompt(
        self,
        *,
        topic: str,
        synthesis: dict[str, Any],
        draft_post: str,
    ) -> str:
        payload = {
            "topic": topic,
            "synthesis": synthesis,
            "draft_post": draft_post,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def _parse_validation_report(self, raw_output: str) -> dict[str, Any]:
        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise ValidationStepError(
                f"ValidateDraft step returned invalid JSON: {exc}"
            ) from exc

        if "ok" not in data or not isinstance(data["ok"], bool):
            raise ValidationStepError(
                "ValidateDraft response missing boolean 'ok' field."
            )

        issues = data.get("issues")
        if not isinstance(issues, list):
            raise ValidationStepError(
                "ValidateDraft response missing list 'issues' field."
            )

        for issue in issues:
            if not isinstance(issue, dict):
                raise ValidationStepError("Each validation issue must be an object.")
            if "type" not in issue or "detail" not in issue:
                raise ValidationStepError(
                    "Each validation issue must contain 'type' and 'detail'."
                )

        return data