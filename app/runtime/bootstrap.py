from __future__ import annotations

from app.runtime.orchestrator import Orchestrator
from app.runtime.step_registry import StepRegistry
from app.steps.apply_style import ApplyStyleStep
from app.steps.build_output import BuildOutputStep
from app.steps.draft_post import DraftPostStep
from app.steps.generate_image_prompts import GenerateImagePromptsStep
from app.steps.summarize import SummarizeStep
from app.steps.validate_draft import ValidateDraftStep
from app.steps.validate_style import ValidateStyleStep


def build_orchestrator() -> Orchestrator:
    registry = StepRegistry()
    registry.register(SummarizeStep())
    registry.register(DraftPostStep())
    registry.register(ValidateDraftStep())
    registry.register(ApplyStyleStep())
    registry.register(ValidateStyleStep())
    registry.register(GenerateImagePromptsStep())
    registry.register(BuildOutputStep())
    return Orchestrator(registry=registry)