from __future__ import annotations

from app.runtime.graph import RuntimeGraph
from app.runtime.orchestrator import Orchestrator
from app.runtime.persistence import RuntimePersistence
from app.runtime.step_registry import StepRegistry
from app.steps.apply_style import ApplyStyleStep
from app.steps.build_output import BuildOutputStep
from app.steps.draft_post import DraftPostStep
from app.steps.generate_image_prompts import GenerateImagePromptsStep
from app.steps.revise_draft import ReviseDraftStep
from app.steps.revise_style import ReviseStyleStep
from app.steps.summarize import SummarizeStep
from app.steps.validate_draft import ValidateDraftStep
from app.steps.validate_style import ValidateStyleStep
from app.store.repository import SQLiteRuntimeRepository


def build_orchestrator(db_path: str = "data/runtime.db") -> Orchestrator:
    registry = StepRegistry()
    registry.register(SummarizeStep())
    registry.register(DraftPostStep())
    registry.register(ValidateDraftStep())
    registry.register(ReviseDraftStep())
    registry.register(ApplyStyleStep())
    registry.register(ValidateStyleStep())
    registry.register(ReviseStyleStep())
    registry.register(GenerateImagePromptsStep())
    registry.register(BuildOutputStep())

    graph = RuntimeGraph()
    graph.set_entry_step("summarize")

    graph.add_edge(from_step="summarize", to_step="draft_post")
    graph.add_edge(from_step="draft_post", to_step="validate_draft")

    graph.add_edge(
        from_step="validate_draft",
        to_step="apply_style",
        condition="on_draft_validation_passed",
    )
    graph.add_edge(
        from_step="validate_draft",
        to_step="revise_draft",
        condition="on_draft_validation_failed",
    )
    graph.add_edge(from_step="revise_draft", to_step="validate_draft")

    graph.add_edge(from_step="apply_style", to_step="validate_style")

    graph.add_edge(
        from_step="validate_style",
        to_step="generate_image_prompts",
        condition="on_style_validation_passed",
    )
    graph.add_edge(
        from_step="validate_style",
        to_step="revise_style",
        condition="on_style_validation_failed",
    )
    graph.add_edge(from_step="revise_style", to_step="validate_style")

    graph.add_edge(from_step="generate_image_prompts", to_step="build_output")

    repository = SQLiteRuntimeRepository(db_path=db_path)
    persistence = RuntimePersistence(repository=repository)

    return Orchestrator(
        registry=registry,
        graph=graph,
        persistence=persistence,
    )