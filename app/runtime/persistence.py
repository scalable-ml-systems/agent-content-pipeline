from __future__ import annotations

from dataclasses import dataclass

from app.runtime.artifacts import Artifact
from app.runtime.types import ExecutionEvent, RunState
from app.store.repository import SQLiteRuntimeRepository


@dataclass(slots=True)
class RuntimePersistence:
    repository: SQLiteRuntimeRepository

    def create_run(self, state: RunState) -> None:
        self.repository.create_run(state)

    def update_run(self, state: RunState) -> None:
        self.repository.update_run(state)

    def record_step_event(self, run_id: str, event: ExecutionEvent) -> None:
        self.repository.insert_step_event(run_id, event)

    def record_artifact(self, run_id: str, artifact: Artifact) -> None:
        self.repository.insert_artifact(run_id, artifact)

    def get_run_summary(self, run_id: str) -> dict | None:
        run = self.repository.get_run(run_id)
        if run is None:
            return None

        return {
            "run": {
                "run_id": run.run_id,
                "topic": run.topic,
                "status": run.status,
                "error": run.error,
                "failed_step": run.failed_step,
                "started_at": run.started_at,
                "finished_at": run.finished_at,
                "created_at": run.created_at,
            },
            "step_runs": self.repository.list_step_runs(run_id),
            "artifacts": self.repository.list_artifacts(run_id),
        }