from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.runtime.artifacts import ArtifactStore, ArtifactType


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(slots=True)
class ExecutionEvent:
    run_id: str
    step_name: str
    attempt: int
    status: StepStatus
    started_at: datetime
    finished_at: datetime
    message: str | None = None
    error: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> int:
        delta = self.finished_at - self.started_at
        return int(delta.total_seconds() * 1000)


@dataclass(slots=True)
class StepResult:
    step_name: str
    status: StepStatus
    state_updates: dict[str, Any] = field(default_factory=dict)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    message: str | None = None
    error: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(
        cls,
        *,
        step_name: str,
        state_updates: dict[str, Any] | None = None,
        artifacts: list[dict[str, Any]] | None = None,
        message: str | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> "StepResult":
        return cls(
            step_name=step_name,
            status=StepStatus.SUCCEEDED,
            state_updates=state_updates or {},
            artifacts=artifacts or [],
            message=message,
            metrics=metrics or {},
        )

    @classmethod
    def failure(
        cls,
        *,
        step_name: str,
        error: str,
        message: str | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> "StepResult":
        return cls(
            step_name=step_name,
            status=StepStatus.FAILED,
            state_updates={},
            artifacts=[],
            message=message,
            error=error,
            metrics=metrics or {},
        )


@dataclass(slots=True)
class RunState:
    run_id: str
    topic: str
    status: RunStatus = RunStatus.PENDING

    search_results: list[dict[str, Any]] = field(default_factory=list)
    source_documents: list[dict[str, Any]] = field(default_factory=list)
    facts: list[dict[str, Any]] = field(default_factory=list)
    retrieved_context: list[dict[str, Any]] = field(default_factory=list)
    retrieval_report: dict[str, Any] | None = None
    synthesis: dict[str, Any] | None = None
    draft_post: str | None = None
    draft_validation: dict[str, Any] | None = None
    styled_post: str | None = None
    style_validation: dict[str, Any] | None = None
    image_prompts: list[str] = field(default_factory=list)
    final_output: dict[str, Any] | None = None

    artifact_store: ArtifactStore = field(default_factory=ArtifactStore)
    artifact_ids_by_type: dict[str, list[str]] = field(default_factory=dict)
    latest_artifact_id_by_type: dict[str, str] = field(default_factory=dict)

    events: list[ExecutionEvent] = field(default_factory=list)
    completed_steps: list[str] = field(default_factory=list)
    failed_step: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    def mark_running(self) -> None:
        self.status = RunStatus.RUNNING
        if self.started_at is None:
            self.started_at = utc_now()

    def mark_succeeded(self) -> None:
        self.status = RunStatus.SUCCEEDED
        self.finished_at = utc_now()

    def mark_failed(self, *, step_name: str | None, error: str) -> None:
        self.status = RunStatus.FAILED
        self.failed_step = step_name
        self.error = error
        self.finished_at = utc_now()

    def apply_updates(self, updates: dict[str, Any]) -> None:
        for key, value in updates.items():
            if not hasattr(self, key):
                raise ValueError(f"RunState has no field named '{key}'")
            setattr(self, key, value)

    def register_artifact(self, artifact_type: ArtifactType, artifact_id: str) -> None:
        type_key = artifact_type.value
        self.artifact_ids_by_type.setdefault(type_key, []).append(artifact_id)
        self.latest_artifact_id_by_type[type_key] = artifact_id