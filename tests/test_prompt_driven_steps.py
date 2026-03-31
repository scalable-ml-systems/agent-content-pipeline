from __future__ import annotations

from app.pipeline import run_pipeline


def test_prompt_driven_pipeline_generates_summary() -> None:
    state = run_pipeline("Agent validation in content systems")
    summary = state["derived"]["summary"]

    assert summary["context"]
    assert isinstance(summary["insights"], list)
    assert len(summary["insights"]) >= 1


def test_prompt_driven_pipeline_generates_styled_post() -> None:
    state = run_pipeline("Planning and groundedness in agent workflows")
    styled_post = state["derived"]["styled_post"]

    assert styled_post
    assert isinstance(styled_post, str)


def test_prompt_driven_pipeline_sets_validation_flags() -> None:
    state = run_pipeline("Tool orchestration and validation")
    assert isinstance(state["validation"]["draft_ok"], bool)
    assert isinstance(state["validation"]["style_ok"], bool)