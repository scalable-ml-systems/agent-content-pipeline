from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml_template(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    data = yaml.safe_load(file_path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"Template at {path} must load as a dictionary.")

    return data
