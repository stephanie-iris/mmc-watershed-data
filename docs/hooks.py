"""Copy tracked documentation artifacts that live outside the MkDocs tree."""

from pathlib import Path
import shutil
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def on_post_build(config: Any, **_: Any) -> None:
    """Add the committed Quarto PDF to the generated documentation site."""

    source = ROOT / "reports" / "mmc-rainfall-report.pdf"
    destination = Path(config.site_dir) / "reports" / source.name
    if not source.is_file():
        raise FileNotFoundError(f"Rendered report is missing: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
