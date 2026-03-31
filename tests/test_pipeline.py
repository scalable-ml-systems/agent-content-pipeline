from pathlib import Path

def test_pipeline_persists_output_artifact() -> None:
    state = run_pipeline("Agent reliability and validation")
    output_path = state["metadata"].get("output_path")

    assert output_path
    assert Path(output_path).exists()
