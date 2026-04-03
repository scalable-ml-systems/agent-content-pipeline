from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.store.repository import SQLiteRuntimeRepository


@dataclass(slots=True)
class ReplayResult:
    run: dict[str, Any]
    step_runs: list[dict[str, Any]]
    artifacts: list[dict[str, Any]]

    def to_timeline(self) -> list[dict[str, Any]]:
        """
        Flatten the replay into a step-by-step timeline that is easy to inspect.

        Each row represents one persisted step attempt.
        """
        timeline: list[dict[str, Any]] = []

        for step_run in self.step_runs:
            timeline.append(
                {
                    "kind": "step_run",
                    "step_name": step_run["step_name"],
                    "attempt": step_run["attempt"],
                    "status": step_run["status"],
                    "message": step_run.get("message"),
                    "error": step_run.get("error"),
                    "duration_ms": step_run.get("duration_ms"),
                    "metrics": step_run.get("metrics", {}),
                    "started_at": step_run.get("started_at"),
                    "finished_at": step_run.get("finished_at"),
                }
            )

        return timeline

    def artifacts_by_step(self) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for artifact in self.artifacts:
            grouped.setdefault(artifact["step_name"], []).append(artifact)
        return grouped


@dataclass(slots=True)
class RuntimeReplayer:
    repository: SQLiteRuntimeRepository

    def replay_run(self, run_id: str) -> ReplayResult:
        bundle = self.repository.get_run_bundle(run_id)
        if bundle is None:
            raise ValueError(f"No persisted run found for run_id='{run_id}'")

        return ReplayResult(
            run=bundle["run"],
            step_runs=bundle["step_runs"],
            artifacts=bundle["artifacts"],
        )

    def render_text_report(self, run_id: str) -> str:
        replay = self.replay_run(run_id)

        lines: list[str] = []
        lines.append("RUN REPLAY")
        lines.append("=" * 80)
        lines.append(f"run_id       : {replay.run['run_id']}")
        lines.append(f"topic        : {replay.run['topic']}")
        lines.append(f"status       : {replay.run['status']}")
        lines.append(f"failed_step  : {replay.run['failed_step']}")
        lines.append(f"error        : {replay.run['error']}")
        lines.append(f"started_at   : {replay.run['started_at']}")
        lines.append(f"finished_at  : {replay.run['finished_at']}")
        lines.append("")

        lines.append("STEP ATTEMPTS")
        lines.append("-" * 80)
        for step_run in replay.step_runs:
            lines.append(
                f"[{step_run['status']}] "
                f"step={step_run['step_name']} "
                f"attempt={step_run['attempt']} "
                f"duration_ms={step_run['duration_ms']}"
            )
            if step_run.get("message"):
                lines.append(f"  message: {step_run['message']}")
            if step_run.get("error"):
                lines.append(f"  error  : {step_run['error']}")
            metrics = step_run.get("metrics") or {}
            if metrics:
                lines.append(f"  metrics: {metrics}")
        lines.append("")

        lines.append("ARTIFACTS")
        lines.append("-" * 80)
        for artifact in replay.artifacts:
            lines.append(
                f"type={artifact['artifact_type']} "
                f"step={artifact['step_name']} "
                f"artifact_id={artifact['artifact_id']}"
            )
            metadata = artifact.get("metadata") or {}
            if metadata:
                lines.append(f"  metadata: {metadata}")

        return "\n".join(lines)