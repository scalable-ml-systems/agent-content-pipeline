from __future__ import annotations

import time
from dataclasses import dataclass

from app.runtime.artifacts import ArtifactType, new_artifact
from app.runtime.errors import StateContractError
from app.runtime.step_registry import StepRegistry
from app.runtime.types import (
    ExecutionEvent,
    RunState,
    RunStatus,
    StepResult,
    StepStatus,
    utc_now,
)


@dataclass(slots=True)
class Orchestrator:
    registry: StepRegistry

    def run(self, state: RunState) -> RunState:
        if state.status not in {RunStatus.PENDING, RunStatus.RUNNING}:
            raise ValueError(
                f"Cannot run orchestrator with state status '{state.status}'."
            )

        state.mark_running()

        for step in self.registry.ordered_steps():
            final_result = self._execute_step_with_retry(state=state, step=step)

            if final_result.status == StepStatus.FAILED:
                state.mark_failed(
                    step_name=step.name,
                    error=final_result.error or "Step failed without an error message.",
                )
                return state

            try:
                self._commit_artifacts(state=state, step_name=step.name, result=final_result)
                state.apply_updates(final_result.state_updates)
            except Exception as exc:
                error_message = f"Failed to commit outputs from '{step.name}': {exc}"
                state.mark_failed(step_name=step.name, error=error_message)
                return state

            state.completed_steps.append(step.name)

            gate_error = self._check_validation_gate(step_name=step.name, state=state)
            if gate_error is not None:
                state.mark_failed(step_name=step.name, error=gate_error)
                return state

        state.mark_succeeded()

        # Keep final_output.status aligned with real final run status if final_output exists.
        if state.final_output and isinstance(state.final_output, dict):
            state.final_output["status"] = state.status.value

        return state

    def _execute_step_with_retry(self, *, state: RunState, step) -> StepResult:
        attempt = 1

        while True:
            started_at = utc_now()

            try:
                result = step.run(state)
                finished_at = utc_now()

                self._validate_step_result(expected_step_name=step.name, result=result)

                state.events.append(
                    ExecutionEvent(
                        run_id=state.run_id,
                        step_name=step.name,
                        attempt=attempt,
                        status=result.status,
                        started_at=started_at,
                        finished_at=finished_at,
                        message=result.message,
                        error=result.error,
                        metrics=result.metrics,
                    )
                )

                return result

            except Exception as exc:
                finished_at = utc_now()
                error_message = f"{type(exc).__name__}: {exc}"

                state.events.append(
                    ExecutionEvent(
                        run_id=state.run_id,
                        step_name=step.name,
                        attempt=attempt,
                        status=StepStatus.FAILED,
                        started_at=started_at,
                        finished_at=finished_at,
                        error=error_message,
                    )
                )

                if not step.retry_policy.should_retry(exc, attempt):
                    return StepResult.failure(
                        step_name=step.name,
                        error=error_message,
                        message="Step failed and retry policy was exhausted.",
                    )

                time.sleep(step.retry_policy.backoff_for(attempt))
                attempt += 1

    def _commit_artifacts(
        self,
        *,
        state: RunState,
        step_name: str,
        result: StepResult,
    ) -> None:
        for item in result.artifacts:
            artifact_type = item["artifact_type"]
            payload = item["payload"]
            metadata = item.get("metadata", {})

            if not isinstance(artifact_type, ArtifactType):
                raise StateContractError(
                    f"Artifact emitted by '{step_name}' must use ArtifactType enum."
                )

            artifact = new_artifact(
                artifact_type=artifact_type,
                step_name=step_name,
                payload=payload,
                metadata=metadata,
            )
            artifact_id = state.artifact_store.write(artifact)
            state.register_artifact(artifact_type=artifact_type, artifact_id=artifact_id)

    def _check_validation_gate(self, *, step_name: str, state: RunState) -> str | None:
        if step_name == "validate_draft":
            report = state.draft_validation
            if isinstance(report, dict) and report.get("ok") is False:
                return "Draft validation failed."

        if step_name == "validate_style":
            report = state.style_validation
            if isinstance(report, dict) and report.get("ok") is False:
                return "Style validation failed."

        return None

    @staticmethod
    def _validate_step_result(expected_step_name: str, result: StepResult) -> None:
        if result.step_name != expected_step_name:
            raise StateContractError(
                f"StepResult step_name mismatch: expected '{expected_step_name}', "
                f"got '{result.step_name}'"
            )

        if result.status not in {
            StepStatus.SUCCEEDED,
            StepStatus.FAILED,
            StepStatus.SKIPPED,
        }:
            raise StateContractError(
                f"Unsupported StepResult status: '{result.status}'"
            )