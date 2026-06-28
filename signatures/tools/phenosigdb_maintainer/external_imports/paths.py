from __future__ import annotations

from pathlib import Path

from ..io import DATA_DIR, repo_root

EXTERNAL_IMPORTS_DIR = DATA_DIR / "external_imports"
EXTERNAL_CACHE_DIR = EXTERNAL_IMPORTS_DIR / "_cache"


def display_path(path: str | Path) -> str:
    target = Path(path)
    root = repo_root()
    try:
        return str(target.relative_to(root))
    except ValueError:
        return str(target)
