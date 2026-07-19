from __future__ import annotations

from pathlib import Path

from .models import RainRecord


def ensure_output_dirs(root: Path) -> tuple[Path, Path]:
    raw_dir = root / "data" / "raw"
    processed_dir = root / "data" / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir, processed_dir


def write_processed_csv(processed_dir: Path, filename: str, records: list[RainRecord], station: str) -> Path:
    path = processed_dir / filename
    lines = ["timestamp_utc,timestamp_local,rain_in,station"]
    for record in records:
        lines.append(
            f"{record.timestamp_utc.isoformat()},{record.timestamp_local.isoformat()},"
            f"{record.rain_in},{station}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path

