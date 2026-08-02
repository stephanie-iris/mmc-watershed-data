"""Select processed rainfall inputs for a reproducible Quarto report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re

from .analysis import RainfallRecord, load_rainfall_records


PROCESSED_NAME = re.compile(
    r"_(?P<start>\d{4}-\d{2}-\d{2})_to_"
    r"(?P<end>\d{4}-\d{2}-\d{2})_processed\.csv$"
)


@dataclass(frozen=True)
class ReportDataset:
    """Records, period, and provenance selected for one report render."""

    records: tuple[RainfallRecord, ...]
    source_files: tuple[Path, ...]
    start_date: date
    end_date: date
    selection: str


def load_report_dataset(
    root: Path,
    *,
    input_path: Path | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> ReportDataset:
    """Load an explicit or latest saved processed collection for reporting.

    A directory of MMC outputs is grouped by the date range encoded in each
    processed filename. Without explicit dates, the most recently modified
    range is selected. When no generated collection exists, the bundled report
    dataset keeps the authoritative report reproducible offline.
    """

    if (start_date is None) != (end_date is None):
        raise ValueError("Report start and end dates must be provided together.")
    if start_date is not None and end_date is not None and start_date > end_date:
        raise ValueError("Report start date must be on or before report end date.")

    if input_path is not None:
        resolved_input = input_path if input_path.is_absolute() else root / input_path
        paths = _csv_paths(resolved_input)
        selection = "configured processed input"
    else:
        paths = _csv_paths(root / "data" / "processed", allow_missing=True)
        selection = "latest saved MMC collection"
        if not paths:
            paths = [
                root
                / "reports"
                / "data"
                / "mmc_report_2026-07-01_to_2026-08-01_processed.csv"
            ]
            selection = "bundled reproducible report dataset"

    groups = _period_groups(paths)
    selected_paths: list[Path]
    selected_start: date | None = start_date
    selected_end: date | None = end_date
    if groups:
        if start_date is not None and end_date is not None:
            try:
                selected_paths = groups[(start_date, end_date)]
            except KeyError as exc:
                raise FileNotFoundError(
                    f"No processed CSV collection exists for {start_date} through {end_date}."
                ) from exc
        else:
            selected_start, selected_end = max(
                groups,
                key=lambda period: (
                    max(path.stat().st_mtime_ns for path in groups[period]),
                    period,
                ),
            )
            selected_paths = groups[(selected_start, selected_end)]
    else:
        selected_paths = paths

    records = tuple(
        record for path in selected_paths for record in load_rainfall_records(path)
    )
    if not records:
        raise RuntimeError(
            "The selected processed collection contains no rainfall records."
        )

    if selected_start is None:
        selected_start = min(record.timestamp.date() for record in records)
    if selected_end is None:
        selected_end = max(record.timestamp.date() for record in records)

    filtered_records = tuple(
        record
        for record in records
        if selected_start <= record.timestamp.date() <= selected_end
    )
    if not filtered_records:
        raise RuntimeError(
            f"No rainfall records fall between {selected_start} and {selected_end}."
        )

    return ReportDataset(
        records=filtered_records,
        source_files=tuple(selected_paths),
        start_date=selected_start,
        end_date=selected_end,
        selection=selection,
    )


def parse_optional_date(value: str, name: str) -> date | None:
    """Parse an optional ISO report date from an environment variable."""

    if not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError(f"{name} must use YYYY-MM-DD format.") from exc


def _csv_paths(path: Path, *, allow_missing: bool = False) -> list[Path]:
    """Return CSV files from one file or directory in stable order."""

    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(path.rglob("*.csv"))
    if allow_missing:
        return []
    raise FileNotFoundError(f"Report input was not found: {path}")


def _period_groups(paths: list[Path]) -> dict[tuple[date, date], list[Path]]:
    """Group standard processed filenames by their requested date range."""

    groups: dict[tuple[date, date], list[Path]] = {}
    for path in paths:
        match = PROCESSED_NAME.search(path.name)
        if match is None:
            continue
        period = (
            date.fromisoformat(match.group("start")),
            date.fromisoformat(match.group("end")),
        )
        groups.setdefault(period, []).append(path)
    return groups
