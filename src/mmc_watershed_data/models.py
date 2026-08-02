"""Typed records exchanged by collection, storage, and presentation layers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class DateRange:
    """Inclusive calendar date range selected by a user."""

    start: date
    end: date


@dataclass(frozen=True)
class Station:
    """Configured station identity and provider-specific identifier."""

    source: str
    city: str
    key: str
    name: str
    identifier: str


@dataclass(frozen=True)
class StationResult:
    """Paths and row counts produced by one successful station collection."""

    station: Station
    raw_json_path: Path
    raw_csv_path: Path
    processed_path: Path
    raw_rows: int
    processed_rows: int
    chunks: int


@dataclass(frozen=True)
class StationFailure:
    """A station-specific failure that does not stop other stations."""

    station: Station
    error: str
