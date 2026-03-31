from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    search_top_k: int = 5
    min_facts_for_summary: int = 3
    min_insights: int = 3
    output_dir: Path = Path("data/outputs")
    template_version: str = "v1"


def get_settings() -> Settings:
    return Settings()
