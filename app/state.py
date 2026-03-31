from __future__ import annotations

from copy import deepcopy
from datetime import datetime, UTC
from typing import Any
from uuid import uuid4

from app.models import StepLog, ValidationIssue


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def new_run_id() -> str:
    return f"run_{uuid4().hex[:12]}"


def create_initial_state(topic: str) -> dict[str, Any]:
    """Create a fresh pipeline state for a single topic run."""
    return {
        "run_id": new_run_id(),
        "topic": topic.strip(),
        "raw": {
            "search_results": [],
            "llm_outputs": {},
        },
        "derived": {
            "facts": [],
            "summary": {
                "context": "",
                "insights": [],
                "implications": [],
                "contrarian_angle": "",
            },
            "draft": "",
            "styled_post": "",
            "image_prompts": [],
        },
        "sources": [],
        "validation": {
            "draft_ok": False,
            "style_ok": False,
            "issues": [],
        },
        "step_logs": [],
        "errors": [],
        "metadata": {
            "created_at": utc_now_iso(),
            "template_version": "v1",
            "models": {},
        },
    }


def clone_state(state: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy of state to avoid accidental mutation side effects."""
    return deepcopy(state)


def append_step_log(
    state: dict[str, Any],
    *,
    step: str,
    status: str,
    started_at: str,
    ended_at: str,
    items_in: int = 0,
    items_out: int = 0,
    message: str = "",
) -> dict[str, Any]:
    log = StepLog(
        step=step,
        status=status,  # type: ignore[arg-type]
        started_at=started_at,
        ended_at=ended_at,
        items_in=items_in,
        items_out=items_out,
        message=message,
    )
    state["step_logs"].append(log.model_dump())
    return state


def append_error(state: dict[str, Any], message: str) -> dict[str, Any]:
    state["errors"].append(message)
    return state


def append_validation_issue(
    state: dict[str, Any],
    *,
    step: str,
    severity: str,
    message: str,
) -> dict[str, Any]:
    issue = ValidationIssue(
        step=step,
        severity=severity,  # type: ignore[arg-type]
        message=message,
    )
    state["validation"]["issues"].append(issue.model_dump())
    return state