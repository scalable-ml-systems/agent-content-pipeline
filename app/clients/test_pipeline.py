from __future__ import annotations

from app.pipeline import run_pipeline


def test_pipeline_runs_end_to_end() -> None:
    topic = "KV-aware routing vs round robin in LLM inference"
    state = run_pipeline(topic)

    assert state["topic"] == topic
    assert "run_id" in state
    assert state["run_id"]

    assert "raw" in state
    assert "derived" in state
    assert "validation" in state
    assert "errors" in state
    assert "step_logs" in state

    assert len(state["raw"]["search_results"]) >= 1
    assert len(state["derived"]["facts"]) >= 1
    assert state["derived"]["draft"]
    assert state["derived"]["styled_post"]
    assert len(state["derived"]["image_prompts"]) >= 1

    assert "final_output" in state
    final_output = state["final_output"]

    assert final_output["topic"] == topic
    assert final_output["post"]
    assert isinstance(final_output["sources"], list)
    assert isinstance(final_output["facts"], list)
    assert isinstance(final_output["image_prompts"], list)
    assert isinstance(final_output["errors"], list)

    assert len(state["step_logs"]) == 9


def test_pipeline_validation_flags_are_present() -> None:
    state = run_pipeline("Agentic systems for content workflows")

    assert "draft_ok" in state["validation"]
    assert "style_ok" in state["validation"]
    assert "issues" in state["validation"]

    assert isinstance(state["validation"]["draft_ok"], bool)
    assert isinstance(state["validation"]["style_ok"], bool)
    assert isinstance(state["validation"]["issues"], list)


def test_pipeline_collects_structured_sources() -> None:
    state = run_pipeline("LLM serving architecture")
    final_output = state["final_output"]

    assert final_output["sources"]
    assert all(isinstance(item, str) for item in final_output["sources"])