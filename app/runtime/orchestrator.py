from __future__ import annotations

import time
from dataclasses import dataclass

from app.runtime.artifacts import ArtifactType, new_artifact
from app.runtime.errors import StateContractError
from app.runtime.graph import RuntimeGraph
from app.runtime.step_registry import StepRegistry
from app.runtime.types import (
    ExecutionEvent,
    RunState,
    RunStatus,
    StepResult,
    StepStatus,
    utc_now,
)

MAX_DRAFT_RECOVERY_LOOPS = 1
MAX_STYLE_RECOVERY_LOOPS = 1


@dataclass(slots=True)
class Orchestrator:
    registry: StepRegistry
    graph: RuntimeGraph

    def run(self, state: RunState) -> RunState:
        if state.status not in {RunStatus.PENDING, RunStatus.RUNNING}:
            raise ValueError(
                f"Cannot run orchestrator with state status '{state.status}'."
            )

        state.mark_running()

        current_step_name: str | None = self.graph.entry_step()

        while current_step_name is not None:
            step = self.registry.get(current_step_name)
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

            next_step_name = self._resolve_next_step(state=state, current_step_name=step.name)
            if next_step_name is None and step.name != "build_output":
                state.mark_failed(
                    step_name=step.name,
                    error=f"No valid next step found after '{step.name}'.",
                )
                return state

            current_step_name = next_step_name

        state.mark_succeeded()

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

    def _resolve_next_step(
        self,
        *,
        state: RunState,
        current_step_name: str,
    ) -> str | None:
        outgoing = self.graph.outgoing(current_step_name)
        if not outgoing:
            return None

        for edge in outgoing:
            if self._edge_matches(state=state, edge_condition=edge.condition):
                return edge.to_step

        return None

    def _edge_matches(self, *, state: RunState, edge_condition: str) -> bool:
        if edge_condition == "always":
            return True

        if edge_condition == "on_draft_validation_passed":
            report = state.draft_validation
            return isinstance(report, dict) and report.get("ok") is True

        if edge_condition == "on_draft_validation_failed":
            report = state.draft_validation
            if not (isinstance(report, dict) and report.get("ok") is False):
                return False
            if state.get_branch_counter("draft_recovery") >= MAX_DRAFT_RECOVERY_LOOPS:
                return False
            state.increment_branch_counter("draft_recovery")
            return True

        if edge_condition == "on_style_validation_passed":
            report = state.style_validation
            return isinstance(report, dict) and report.get("ok") is True

        if edge_condition == "on_style_validation_failed":
            report = state.style_validation
            if not (isinstance(report, dict) and report.get("ok") is False):
                return False
            if state.get_branch_counter("style_recovery") >= MAX_STYLE_RECOVERY_LOOPS:
                return False
            state.increment_branch_counter("style_recovery")
            return True

        raise StateContractError(f"Unknown edge condition '{edge_condition}'")

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