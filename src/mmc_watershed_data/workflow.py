"""Shared station and spatial collection workflow for CLI and dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import logging
from pathlib import Path

from .auburn import collect_all as collect_auburn
from .analysis import load_rainfall_records
from .models import StationFailure, StationResult
from .opelika import collect_all as collect_opelika
from .spatial import SpatialAnalysis, SpatialAnalysisError, create_spatial_products


logger = logging.getLogger(__name__)


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
    spatial_analysis: SpatialAnalysis | None = None
    spatial_failure: str | None = None


def collect_rainfall(request: CollectionRequest, root: Path) -> CollectionResult:
    """Collect both city feeds and derive spatial products for the same period."""

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
    station_results = tuple(auburn_results + opelika_results)
    spatial_analysis: SpatialAnalysis | None = None
    spatial_failure: str | None = None
    try:
        records = [
            record
            for result in station_results
            for record in load_rainfall_records(result.processed_path)
        ]
        spatial_analysis = create_spatial_products(
            root,
            records,
            request.start_date,
            request.end_date,
        )
    except (OSError, ValueError, SpatialAnalysisError) as exc:
        spatial_failure = str(exc)
        logger.warning(
            "Station collection completed, but spatial products were not created: %s",
            exc,
        )
    return CollectionResult(
        request=request,
        station_results=station_results,
        station_failures=tuple(auburn_failures + opelika_failures),
        spatial_analysis=spatial_analysis,
        spatial_failure=spatial_failure,
    )
