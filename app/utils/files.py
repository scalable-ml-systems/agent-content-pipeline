from __future__ import annotations

from pathlib import Path


def repo_path(relative_path: str) -> Path:
    return Path(relative_path)


def ensure_directory(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def read_text_file(path: str | Path, encoding: str = "utf-8") -> str:
    file_path = Path(path)
    return file_path.read_text(encoding=encoding).strip()