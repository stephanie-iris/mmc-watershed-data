from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class DateRange:
    start: date
    end: date


@dataclass(frozen=True)
class Station:
    source: str
    city: str
    key: str
    name: str
    identifier: str


@dataclass(frozen=True)
class StationResult:
    station: Station
    raw_json_path: Path
    raw_csv_path: Path
    processed_path: Path
    raw_rows: int
    processed_rows: int
    chunks: int


@dataclass(frozen=True)
class StationFailure:
    station: Station
    error: str
