from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class Edge:
    from_step: str
    to_step: str
    condition: str = "always"
    description: str | None = None


@dataclass(slots=True)
class RuntimeGraph:
    """
    Bounded runtime graph.

    This graph does not evaluate arbitrary predicates.
    Instead, it supports a small set of explicit conditions that the
    orchestrator understands.

    Supported conditions:
    - always
    - on_draft_validation_failed
    - on_draft_validation_passed
    - on_style_validation_failed
    - on_style_validation_passed
    """

    _edges_from: dict[str, list[Edge]] = field(default_factory=dict)
    _entry_step: str | None = None

    def set_entry_step(self, step_name: str) -> None:
        self._entry_step = step_name

    def add_edge(
        self,
        *,
        from_step: str,
        to_step: str,
        condition: str = "always",
        description: str | None = None,
    ) -> None:
        edge = Edge(
            from_step=from_step,
            to_step=to_step,
            condition=condition,
            description=description,
        )
        self._edges_from.setdefault(from_step, []).append(edge)

    def entry_step(self) -> str:
        if not self._entry_step:
            raise ValueError("RuntimeGraph entry step has not been set.")
        return self._entry_step

    def outgoing(self, step_name: str) -> list[Edge]:
        return list(self._edges_from.get(step_name, []))