from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ArtifactType(str, Enum):
    SEARCH_RESULTS = "search_results"
    SOURCE_DOCUMENTS = "source_documents"
    FACTS = "facts"
    RETRIEVED_CONTEXT = "retrieved_context"
    RETRIEVAL_REPORT = "retrieval_report"
    SYNTHESIS = "synthesis"
    DRAFT_POST = "draft_post"
    DRAFT_VALIDATION = "draft_validation"
    STYLED_POST = "styled_post"
    STYLE_VALIDATION = "style_validation"
    IMAGE_PROMPTS = "image_prompts"
    FINAL_OUTPUT = "final_output"


@dataclass(slots=True, frozen=True)
class Artifact:
    artifact_id: str
    artifact_type: ArtifactType
    step_name: str
    created_at: datetime
    payload: Any
    metadata: dict[str, Any] = field(default_factory=dict)


def new_artifact(
    *,
    artifact_type: ArtifactType,
    step_name: str,
    payload: Any,
    metadata: dict[str, Any] | None = None,
) -> Artifact:
    return Artifact(
        artifact_id=str(uuid4()),
        artifact_type=artifact_type,
        step_name=step_name,
        created_at=utc_now(),
        payload=payload,
        metadata=metadata or {},
    )


class ArtifactStore:
    def __init__(self) -> None:
        self._artifacts_by_id: dict[str, Artifact] = {}
        self._artifact_ids_by_type: dict[ArtifactType, list[str]] = {}

    def write(self, artifact: Artifact) -> str:
        self._artifacts_by_id[artifact.artifact_id] = artifact
        self._artifact_ids_by_type.setdefault(artifact.artifact_type, []).append(
            artifact.artifact_id
        )
        return artifact.artifact_id

    def get(self, artifact_id: str) -> Artifact:
        try:
            return self._artifacts_by_id[artifact_id]
        except KeyError as exc:
            raise KeyError(f"Unknown artifact_id: '{artifact_id}'") from exc

    def list_by_type(self, artifact_type: ArtifactType) -> list[Artifact]:
        artifact_ids = self._artifact_ids_by_type.get(artifact_type, [])
        return [self._artifacts_by_id[artifact_id] for artifact_id in artifact_ids]

    def all(self) -> list[Artifact]:
        return list(self._artifacts_by_id.values())