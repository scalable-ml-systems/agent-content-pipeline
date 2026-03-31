from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json_file(path: str | Path, payload: Any) -> Path:
    file_path = Path(path)
    file_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return file_path


def read_json_file(path: str | Path) -> Any:
    file_path = Path(path)
    return json.loads(file_path.read_text(encoding="utf-8"))