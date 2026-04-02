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
class SummarizeStep:
    name: str = "summarize"
    retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY

    def run(self, state: RunState) -> StepResult:
        evidence_blocks = self._build_evidence_blocks(state)

        if not evidence_blocks:
            raise ValidationStepError(
                "Cannot summarize without facts or retrieved context."
            )

        system_prompt = """
You are a structured synthesis engine.

Return valid JSON only with this shape:
{
  "context": "string",
  "insights": ["string"],
  "implications": ["string"],
  "contrarian_angle": "string"
}

Rules:
- Use only the evidence provided.
- Do not invent unsupported claims.
- Keep insights concise and concrete.
- Return JSON only.
""".strip()

        user_prompt = self._build_user_prompt(
            topic=state.topic,
            evidence_blocks=evidence_blocks,
        )

        client = get_llm_client()

        try:
            raw_output = client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2,
                task="summarize",
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

        synthesis = self._parse_synthesis(raw_output)

        return StepResult.success(
            step_name=self.name,
            state_updates={"synthesis": synthesis},
            artifacts=[
                {
                    "artifact_type": ArtifactType.SYNTHESIS,
                    "payload": synthesis,
                    "metadata": {
                        "topic": state.topic,
                        "fact_count": len(state.facts),
                        "retrieved_context_count": len(state.retrieved_context),
                    },
                }
            ],
            message="Structured synthesis created successfully.",
            metrics={
                "evidence_block_count": len(evidence_blocks),
                "fact_count": len(state.facts),
                "retrieved_context_count": len(state.retrieved_context),
            },
        )

    def _build_evidence_blocks(self, state: RunState) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []

        for fact in state.facts[:12]:
            fact_text = str(fact.get("fact", "")).strip()
            if not fact_text:
                continue

            blocks.append(
                {
                    "type": "fact",
                    "text": fact_text,
                    "source_title": fact.get("source_title"),
                    "source_url": fact.get("source_url"),
                    "evidence_snippet": fact.get("evidence_snippet"),
                }
            )

        for chunk in state.retrieved_context[:8]:
            chunk_text = str(chunk.get("text", "")).strip()
            if not chunk_text:
                continue

            blocks.append(
                {
                    "type": "retrieved_context",
                    "text": chunk_text,
                    "source_title": chunk.get("title"),
                    "source_url": chunk.get("source_url"),
                    "score": chunk.get("score"),
                }
            )

        return blocks

    def _build_user_prompt(
        self,
        *,
        topic: str,
        evidence_blocks: list[dict[str, Any]],
    ) -> str:
        payload = {
            "topic": topic,
            "evidence": evidence_blocks,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def _parse_synthesis(self, raw_output: str) -> dict[str, Any]:
        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise ValidationStepError(
                f"Summarize step returned invalid JSON: {exc}"
            ) from exc

        required_keys = {
            "context": str,
            "insights": list,
            "implications": list,
            "contrarian_angle": str,
        }

        for key, expected_type in required_keys.items():
            if key not in data:
                raise ValidationStepError(
                    f"Summarize step response missing required key '{key}'."
                )
            if not isinstance(data[key], expected_type):
                raise ValidationStepError(
                    f"Summarize step key '{key}' must be of type "
                    f"{expected_type.__name__}."
                )

        return data