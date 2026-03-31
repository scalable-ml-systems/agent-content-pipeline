from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.state import append_error, append_step_log, create_initial_state, utc_now_iso

# Phase 1 starter placeholders.
# These modules should be implemented next.
from app.steps.apply_style import apply_style
from app.steps.build_output import build_output
from app.steps.draft_post import draft_post
from app.steps.extract_facts import extract_facts
from app.steps.generate_image_prompts import generate_image_prompts
from app.steps.search_web import search_web
from app.steps.summarize import summarize
from app.steps.validate_draft import validate_draft
from app.steps.validate_style import validate_style

State = dict[str, Any]
StepFn = Callable[[State], State]


def _run_step(step_name: str, step_fn: StepFn, state: State) -> State:
    started_at = utc_now_iso()

    try:
        next_state = step_fn(state)
        ended_at = utc_now_iso()
        return append_step_log(
            next_state,
            step=step_name,
            status="ok",
            started_at=started_at,
            ended_at=ended_at,
        )
    except Exception as exc:
        ended_at = utc_now_iso()
        append_error(state, f"{step_name} failed: {exc}")
        return append_step_log(
            state,
            step=step_name,
            status="error",
            started_at=started_at,
            ended_at=ended_at,
            message=str(exc),
        )


def run_pipeline(topic: str) -> State:
    state = create_initial_state(topic)

    steps: list[tuple[str, StepFn]] = [
        ("search_web", search_web),
        ("extract_facts", extract_facts),
        ("summarize", summarize),
        ("draft_post", draft_post),
        ("validate_draft", validate_draft),
        ("apply_style", apply_style),
        ("validate_style", validate_style),
        ("generate_image_prompts", generate_image_prompts),
        ("build_output", build_output),
    ]

    for step_name, step_fn in steps:
        state = _run_step(step_name, step_fn, state)

    return state