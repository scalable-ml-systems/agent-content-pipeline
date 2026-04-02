from __future__ import annotations

from dataclasses import dataclass, field

from app.runtime.contracts import Step


@dataclass(slots=True)
class StepRegistry:
    _steps_by_name: dict[str, Step] = field(default_factory=dict)
    _ordered_names: list[str] = field(default_factory=list)

    def register(self, step: Step) -> None:
        if not step.name or not isinstance(step.name, str):
            raise ValueError("Step must define a non-empty string 'name'.")

        if step.name in self._steps_by_name:
            raise ValueError(f"Duplicate step registration: '{step.name}'")

        self._steps_by_name[step.name] = step
        self._ordered_names.append(step.name)

    def get(self, step_name: str) -> Step:
        try:
            return self._steps_by_name[step_name]
        except KeyError as exc:
            raise KeyError(f"Unknown step: '{step_name}'") from exc

    def ordered_steps(self) -> list[Step]:
        return [self._steps_by_name[name] for name in self._ordered_names]

    def names(self) -> list[str]:
        return list(self._ordered_names)

    def __len__(self) -> int:
        return len(self._ordered_names)