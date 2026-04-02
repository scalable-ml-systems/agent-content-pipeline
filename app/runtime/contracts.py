from __future__ import annotations

from typing import Protocol

from app.runtime.retry import RetryPolicy
from app.runtime.types import RunState, StepResult


class Step(Protocol):
    """
    Contract for all runtime steps.

    Steps may read from RunState, but they should not mutate it directly.
    They return a StepResult describing the proposed state updates.
    """

    name: str
    retry_policy: RetryPolicy

    def run(self, state: RunState) -> StepResult:
        """
        Execute the step against the current run state and return
        a structured result for the orchestrator to commit.
        """
        ...