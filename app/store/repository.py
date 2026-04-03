from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.runtime.artifacts import Artifact
from app.runtime.types import ExecutionEvent, RunState
from app.store.schema import initialize_schema


@dataclass(slots=True)
class RunRecord:
    run_id: str
    topic: str
    status: str
    error: str | None
    failed_step: str | None
    started_at: str | None
    finished_at: str | None
    created_at: str


@dataclass(slots=True)
class SQLiteRuntimeRepository:
    db_path: str

    def __post_init__(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            initialize_schema(conn)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_run(self, state: RunState) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runs (
                    run_id, topic, status, error, failed_step,
                    started_at, finished_at, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    state.run_id,
                    state.topic,
                    state.status.value,
                    state.error,
                    state.failed_step,
                    state.started_at.isoformat() if state.started_at else None,
                    state.finished_at.isoformat() if state.finished_at else None,
                    state.started_at.isoformat() if state.started_at else None,
                ),
            )
            conn.commit()

    def update_run(self, state: RunState) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE runs
                SET status = ?,
                    error = ?,
                    failed_step = ?,
                    started_at = ?,
                    finished_at = ?
                WHERE run_id = ?
                """,
                (
                    state.status.value,
                    state.error,
                    state.failed_step,
                    state.started_at.isoformat() if state.started_at else None,
                    state.finished_at.isoformat() if state.finished_at else None,
                    state.run_id,
                ),
            )
            conn.commit()

    def insert_step_event(self, run_id: str, event: ExecutionEvent) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO step_runs (
                    run_id, step_name, attempt, status, message, error,
                    metrics_json, started_at, finished_at, duration_ms
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    event.step_name,
                    event.attempt,
                    event.status.value,
                    event.message,
                    event.error,
                    json.dumps(event.metrics, ensure_ascii=False),
                    event.started_at.isoformat(),
                    event.finished_at.isoformat(),
                    event.duration_ms,
                ),
            )
            conn.commit()

    def insert_artifact(self, run_id: str, artifact: Artifact) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO artifacts (
                    artifact_id, run_id, artifact_type, step_name,
                    created_at, payload_json, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact.artifact_id,
                    run_id,
                    artifact.artifact_type.value,
                    artifact.step_name,
                    artifact.created_at.isoformat(),
                    json.dumps(artifact.payload, ensure_ascii=False),
                    json.dumps(artifact.metadata, ensure_ascii=False),
                ),
            )
            conn.commit()

    def get_run(self, run_id: str) -> RunRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT run_id, topic, status, error, failed_step,
                       started_at, finished_at, created_at
                FROM runs
                WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()

        if row is None:
            return None

        return RunRecord(
            run_id=row["run_id"],
            topic=row["topic"],
            status=row["status"],
            error=row["error"],
            failed_step=row["failed_step"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            created_at=row["created_at"],
        )

    def list_step_runs(self, run_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT step_name, attempt, status, message, error,
                       metrics_json, started_at, finished_at, duration_ms
                FROM step_runs
                WHERE run_id = ?
                ORDER BY id ASC
                """,
                (run_id,),
            ).fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            results.append(
                {
                    "step_name": row["step_name"],
                    "attempt": row["attempt"],
                    "status": row["status"],
                    "message": row["message"],
                    "error": row["error"],
                    "metrics": json.loads(row["metrics_json"]),
                    "started_at": row["started_at"],
                    "finished_at": row["finished_at"],
                    "duration_ms": row["duration_ms"],
                }
            )
        return results

    def list_artifacts(self, run_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT artifact_id, artifact_type, step_name, created_at,
                       payload_json, metadata_json
                FROM artifacts
                WHERE run_id = ?
                ORDER BY created_at ASC
                """,
                (run_id,),
            ).fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            results.append(
                {
                    "artifact_id": row["artifact_id"],
                    "artifact_type": row["artifact_type"],
                    "step_name": row["step_name"],
                    "created_at": row["created_at"],
                    "payload": json.loads(row["payload_json"]),
                    "metadata": json.loads(row["metadata_json"]),
                }
            )
        return results