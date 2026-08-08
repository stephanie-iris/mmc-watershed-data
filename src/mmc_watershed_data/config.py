"""Project-path helpers used by the command line tool and dashboard."""

from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    """Return the repository root or current output directory when installed."""

    repository_root = Path(__file__).resolve().parents[2]
    if (repository_root / "pyproject.toml").is_file():
        return repository_root
    return Path.cwd()
