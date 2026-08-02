"""Shared collection workflow for the CLI and future dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .auburn import collect_all as collect_auburn
from .models import StationFailure, StationResult
from .opelika import collect_all as collect_opelika


@dataclass(frozen=True)
class CollectionRequest:
    """User-selected date window shared by every station."""

    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        """Reject a reversed inclusive date window before network access."""

        if self.start_date > self.end_date:
            raise ValueError("start date must be earlier than or equal to end date")


@dataclass(frozen=True)
class CollectionResult:
    """Results and failures from one complete multi-city collection."""

    request: CollectionRequest
    station_results: tuple[StationResult, ...]
    station_failures: tuple[StationFailure, ...]


def collect_rainfall(request: CollectionRequest, root: Path) -> CollectionResult:
    """Collect both city feeds using one shared date request."""

    auburn_results, auburn_failures = collect_auburn(
        request.start_date,
        request.end_date,
        root,
    )
    opelika_results, opelika_failures = collect_opelika(
        request.start_date,
        request.end_date,
        root,
    )
    return CollectionResult(
        request=request,
        station_results=tuple(auburn_results + opelika_results),
        station_failures=tuple(auburn_failures + opelika_failures),
    )
