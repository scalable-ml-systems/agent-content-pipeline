from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.config import get_settings
from app.models import PipelineOutput, Summary, ValidationState
from app.utils.files import ensure_directory
from app.utils.json_io import write_json_file


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def build_output(state: dict) -> dict:
    output = PipelineOutput(
        run_id=state["run_id"],
        topic=state["topic"],
        post=state["derived"]["styled_post"],
        image_prompts=state["derived"]["image_prompts"],
        sources=state["sources"],
        facts=state["derived"]["facts"],
        summary=Summary(**state["derived"]["summary"]),
        validation=ValidationState(**state["validation"]),
        errors=state["errors"],
    )

    payload = output.model_dump(mode="json")

    settings = get_settings()
    output_dir = ensure_directory(settings.output_dir)
    output_path = Path(output_dir) / f"{state['run_id']}.json"

    payload["metadata"] = {
        "artifact_version": "phase1.v1",
        "created_at": state["metadata"].get("created_at", ""),
        "persisted_at": _utc_now_iso(),
        "template_version": state["metadata"].get("template_version", ""),
        "models": state["metadata"].get("models", {}),
        "output_path": str(output_path),
        "step_count": len(state.get("step_logs", [])),
        "issue_count": len(state.get("validation", {}).get("issues", [])),
        "error_count": len(state.get("errors", [])),
        "status": (
            "error"
            if state.get("errors")
            else "degraded"
            if state.get("validation", {}).get("issues")
            else "ok"
        ),
    }

    state["final_output"] = payload
    write_json_file(output_path, payload)
    state["metadata"]["output_path"] = str(output_path)

    return state