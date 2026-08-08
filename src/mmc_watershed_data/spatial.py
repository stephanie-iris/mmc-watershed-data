"""Thiessen geometry and watershed-average rainfall analysis."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta
import json
import logging
import math
from pathlib import Path
from typing import Any, Iterable, Sequence

from pyproj import Transformer
from shapely import make_valid, voronoi_polygons
from shapely.geometry import MultiPoint, Point, Polygon, box, mapping
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform, unary_union

from .analysis import RainfallRecord
from .geospatial import StationPoint, load_station_points, load_watershed_boundary
from .storage import write_csv, write_json


logger = logging.getLogger(__name__)
ANALYSIS_CRS = "EPSG:32616"
DISPLAY_CRS = "EPSG:4326"
TEMPORAL_COVERAGE_THRESHOLD = 0.90
INTERVAL_MINUTES = 10
AREA_RELATIVE_TOLERANCE = 1e-7


class SpatialAnalysisError(RuntimeError):
    """Report a condition that prevents a trustworthy spatial result."""


@dataclass(frozen=True)
class StationWeight:
    """One station's eligibility decision, clipped area, and fixed weight."""

    station_key: str
    station_name: str
    city: str
    latitude: float
    longitude: float
    eligible: bool
    exclusion_reason: str
    temporal_coverage: float
    watershed_area_m2: float
    thiessen_area_m2: float
    weight: float
    geometry: BaseGeometry | None = None
    aggregated_observation_count: int = 0

    @property
    def thiessen_area_km2(self) -> float:
        """Return the clipped Thiessen area in square kilometers."""

        return self.thiessen_area_m2 / 1_000_000

    @property
    def area_percent(self) -> float:
        """Return the station's percentage of the watershed area."""

        return self.weight * 100


@dataclass(frozen=True)
class ArealRainfall:
    """One nominal interval of watershed rainfall and quality metadata."""

    timestamp: datetime
    rain_in: float | None
    simple_mean_rain_in: float | None
    coverage_fraction: float
    stations_used: int
    eligible_station_count: int
    quality_flag: str


@dataclass(frozen=True)
class SpatialOutputPaths:
    """Paths written for one period's spatial products."""

    weights_csv: Path
    polygons_geojson: Path
    areal_rainfall_csv: Path


@dataclass(frozen=True)
class SpatialAnalysis:
    """Auditable period-level Thiessen geometry and rainfall results."""

    start_date: date
    end_date: date
    weights: tuple[StationWeight, ...]
    rainfall: tuple[ArealRainfall, ...]
    watershed_area_m2: float
    coverage_threshold: float
    outputs: SpatialOutputPaths | None = None

    @property
    def eligible_count(self) -> int:
        """Return the number of stations that passed the period policy."""

        return sum(weight.eligible for weight in self.weights)

    @property
    def excluded_count(self) -> int:
        """Return the number of stations excluded from the period analysis."""

        return len(self.weights) - self.eligible_count


def align_to_ten_minutes(timestamp: datetime) -> datetime:
    """Round to the nearest 10-minute label, sending exact ties forward."""

    midnight = datetime.combine(timestamp.date(), time.min)
    elapsed = timestamp - midnight
    interval_seconds = INTERVAL_MINUTES * 60
    rounded_intervals = math.floor(
        (elapsed.total_seconds() + interval_seconds / 2) / interval_seconds
    )
    return midnight + timedelta(seconds=rounded_intervals * interval_seconds)


def expected_timeline(start_date: date, end_date: date) -> tuple[datetime, ...]:
    """Return every nominal 10-minute label in an inclusive whole-day range."""

    if start_date > end_date:
        raise ValueError("start date must be on or before end date")
    start = datetime.combine(start_date, time.min)
    stop = datetime.combine(end_date + timedelta(days=1), time.min)
    interval = timedelta(minutes=INTERVAL_MINUTES)
    values: list[datetime] = []
    current = start
    while current < stop:
        values.append(current)
        current += interval
    return tuple(values)


def analyze_spatial_rainfall(
    root: Path,
    records: Iterable[RainfallRecord],
    start_date: date,
    end_date: date,
    *,
    coverage_threshold: float = TEMPORAL_COVERAGE_THRESHOLD,
) -> SpatialAnalysis:
    """Build fixed Thiessen weights and a strict watershed rainfall series.

    Raises ``SpatialAnalysisError`` when station coverage, timestamps, or
    geometry cannot support an auditable areal estimate.
    """

    if not 0 <= coverage_threshold <= 1:
        raise ValueError("coverage threshold must be between zero and one")
    points = load_station_points(root)
    boundary = load_watershed_boundary(root)
    timeline = expected_timeline(start_date, end_date)
    aligned, alignment_conflicts, aggregation_counts = _align_records(
        records, set(timeline)
    )
    coverage = {
        point.station_key: len(aligned.get(point.station_key, {})) / len(timeline)
        for point in points
    }
    eligibility = _station_eligibility(
        points, coverage, coverage_threshold, alignment_conflicts
    )
    eligible_points = [point for point in points if eligibility[point.station_key][0]]
    _validate_eligible_points(eligible_points)
    weights = _thiessen_weights(
        points,
        eligible_points,
        boundary,
        eligibility,
        aggregation_counts,
    )
    rainfall = _calculate_areal_rainfall(timeline, aligned, weights)
    watershed_area = weights[0].watershed_area_m2
    logger.info(
        "Spatial analysis used %d eligible stations, excluded %d, and covered %.3f km2.",
        len(eligible_points),
        len(points) - len(eligible_points),
        watershed_area / 1_000_000,
    )
    return SpatialAnalysis(
        start_date=start_date,
        end_date=end_date,
        weights=weights,
        rainfall=rainfall,
        watershed_area_m2=watershed_area,
        coverage_threshold=coverage_threshold,
    )


def create_spatial_products(
    root: Path,
    records: Iterable[RainfallRecord],
    start_date: date,
    end_date: date,
) -> SpatialAnalysis:
    """Analyze rainfall, write all period spatial artifacts, and return them."""

    analysis = analyze_spatial_rainfall(root, records, start_date, end_date)
    output_dir = root / "data" / "processed" / "spatial"
    period = f"{start_date.isoformat()}_to_{end_date.isoformat()}"
    paths = SpatialOutputPaths(
        weights_csv=output_dir / f"mmc_thiessen_weights_{period}.csv",
        polygons_geojson=output_dir / f"mmc_thiessen_polygons_{period}.geojson",
        areal_rainfall_csv=output_dir / f"mmc_areal_rainfall_{period}.csv",
    )
    write_csv(paths.weights_csv, _weight_rows(analysis.weights), _weight_fields())
    write_json(paths.polygons_geojson, spatial_geojson(analysis))
    write_csv(
        paths.areal_rainfall_csv,
        _rainfall_rows(analysis.rainfall),
        _rainfall_fields(),
    )
    logger.info("Spatial products written under %s.", output_dir)
    return replace(analysis, outputs=paths)


def spatial_geojson(analysis: SpatialAnalysis) -> dict[str, Any]:
    """Return clipped eligible Thiessen polygons as a GeoJSON feature collection."""

    features: list[dict[str, Any]] = []
    for weight in analysis.weights:
        if not weight.eligible:
            continue
        properties = _weight_row(weight)
        properties.update(
            {
                "start_date": analysis.start_date.isoformat(),
                "end_date": analysis.end_date.isoformat(),
            }
        )
        geometry = None
        if weight.geometry is not None and not weight.geometry.is_empty:
            geometry = mapping(weight.geometry)
        features.append(
            {"type": "Feature", "properties": properties, "geometry": geometry}
        )
    return {
        "type": "FeatureCollection",
        "name": "MMC clipped Thiessen polygons",
        "crs": {"type": "name", "properties": {"name": DISPLAY_CRS}},
        "features": features,
    }


def spatial_download_bytes(analysis: SpatialAnalysis) -> tuple[bytes, bytes, bytes]:
    """Serialize all spatial products for dashboard download buttons."""

    import csv
    import io

    def csv_bytes(rows: list[dict[str, object]], fields: list[str]) -> bytes:
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        return buffer.getvalue().encode("utf-8")

    return (
        csv_bytes(_weight_rows(analysis.weights), _weight_fields()),
        json.dumps(spatial_geojson(analysis), indent=2).encode("utf-8"),
        csv_bytes(_rainfall_rows(analysis.rainfall), _rainfall_fields()),
    )


def _align_records(
    records: Iterable[RainfallRecord], timeline: set[datetime]
) -> tuple[dict[str, dict[datetime, float]], set[str], dict[str, int]]:
    """Deduplicate exact rows, align timestamps, and sum distinct interval values."""

    aligned: dict[str, dict[datetime, float]] = {}
    conflicts: set[str] = set()
    station_names: dict[str, str] = {}
    station_cities: dict[str, str] = {}
    aggregation_counts: dict[str, int] = {}
    duplicate_counts: dict[str, int] = {}
    original_values: dict[str, dict[datetime, float]] = {}
    for record in records:
        station_names[record.station_key] = record.station_name
        station_cities[record.station_key] = record.city
        station_original_values = original_values.setdefault(record.station_key, {})
        if record.timestamp in station_original_values:
            if math.isclose(
                station_original_values[record.timestamp],
                record.rain_in,
                rel_tol=0.0,
                abs_tol=1e-12,
            ):
                duplicate_counts[record.station_key] = (
                    duplicate_counts.get(record.station_key, 0) + 1
                )
            else:
                conflicts.add(record.station_key)
            continue
        station_original_values[record.timestamp] = record.rain_in

        label = align_to_ten_minutes(record.timestamp)
        if label not in timeline:
            continue
        station_values = aligned.setdefault(record.station_key, {})
        if label in station_values:
            station_values[label] += record.rain_in
            aggregation_counts[record.station_key] = (
                aggregation_counts.get(record.station_key, 0) + 1
            )
            continue
        station_values[label] = record.rain_in
    for station_key, count in aggregation_counts.items():
        logger.info(
            "Summed %d additional %s interval value(s) into shared 10-minute "
            "labels for %s.",
            count,
            station_cities[station_key],
            station_names[station_key],
        )
    for station_key, count in duplicate_counts.items():
        logger.info(
            "Ignored %d exact duplicate processed observation(s) for %s.",
            count,
            station_names[station_key],
        )
    for station_key in sorted(conflicts):
        logger.warning(
            "Station %s has conflicting values at an identical processed "
            "timestamp and will be excluded.",
            station_names[station_key],
        )
    return aligned, conflicts, aggregation_counts


def _station_eligibility(
    points: Sequence[StationPoint],
    coverage: dict[str, float],
    threshold: float,
    alignment_conflicts: set[str],
) -> dict[str, tuple[bool, str, float]]:
    """Apply deterministic coordinate and temporal eligibility rules."""

    coordinate_counts: dict[tuple[float, float], int] = {}
    for point in points:
        coordinate = (point.latitude, point.longitude)
        coordinate_counts[coordinate] = coordinate_counts.get(coordinate, 0) + 1

    result: dict[str, tuple[bool, str, float]] = {}
    for point in points:
        station_coverage = coverage.get(point.station_key, 0.0)
        coordinate = (point.latitude, point.longitude)
        reason = ""
        if not all(math.isfinite(value) for value in coordinate):
            reason = "invalid coordinates"
        elif coordinate_counts[coordinate] > 1:
            reason = "duplicate coordinates"
        elif point.station_key in alignment_conflicts:
            reason = "conflicting duplicate timestamp values"
        elif station_coverage == 0:
            reason = "no processed observations"
        elif station_coverage < threshold:
            reason = f"temporal coverage below {threshold:.0%}"
        result[point.station_key] = (not reason, reason, station_coverage)
    return result


def _validate_eligible_points(points: Sequence[StationPoint]) -> None:
    """Require at least three unique, non-collinear eligible locations."""

    if len(points) < 3:
        raise SpatialAnalysisError(
            "Thiessen analysis requires at least three eligible stations; "
            f"found {len(points)}. Check period coverage and station KMZ files."
        )
    coordinates = [(point.longitude, point.latitude) for point in points]
    if MultiPoint(coordinates).convex_hull.geom_type != "Polygon":
        raise SpatialAnalysisError(
            "Thiessen analysis requires at least three non-collinear station locations."
        )


def _thiessen_weights(
    all_points: Sequence[StationPoint],
    eligible_points: Sequence[StationPoint],
    boundary: Sequence[tuple[float, float]],
    eligibility: dict[str, tuple[bool, str, float]],
    aggregation_counts: dict[str, int],
) -> tuple[StationWeight, ...]:
    """Project, associate, clip, and validate Thiessen influence regions."""

    to_projected = Transformer.from_crs(
        DISPLAY_CRS, ANALYSIS_CRS, always_xy=True
    ).transform
    to_display = Transformer.from_crs(
        ANALYSIS_CRS, DISPLAY_CRS, always_xy=True
    ).transform
    watershed_wgs84 = Polygon([(lon, lat) for lat, lon in boundary])
    if watershed_wgs84.is_empty:
        raise SpatialAnalysisError("The MMC watershed boundary geometry is empty.")
    if not watershed_wgs84.is_valid:
        logger.warning("Repairing the tracked MMC boundary topology before projection.")
        repaired = make_valid(watershed_wgs84)
        if repaired.geom_type not in {"Polygon", "MultiPolygon"} or repaired.is_empty:
            raise SpatialAnalysisError(
                "The MMC watershed boundary could not be repaired as polygon geometry."
            )
        watershed_wgs84 = repaired
    watershed = transform(to_projected, watershed_wgs84)
    watershed_area = watershed.area
    if watershed_area <= 0:
        raise SpatialAnalysisError(
            "The projected MMC watershed has no measurable area."
        )

    projected_points = {
        point.station_key: transform(
            to_projected, Point(point.longitude, point.latitude)
        )
        for point in eligible_points
    }
    point_collection = MultiPoint(list(projected_points.values()))
    extent = _construction_extent(watershed, point_collection)
    cells = list(voronoi_polygons(point_collection, extend_to=extent).geoms)
    associated: dict[str, BaseGeometry] = {}
    for point in eligible_points:
        station_point = projected_points[point.station_key]
        matches = [cell for cell in cells if cell.covers(station_point)]
        if len(matches) != 1:
            raise SpatialAnalysisError(
                f"Could not associate one Thiessen polygon with {point.station_name}."
            )
        associated[point.station_key] = matches[0]

    clipped = {
        key: geometry.intersection(watershed) for key, geometry in associated.items()
    }
    _validate_clipped_geometry(watershed, tuple(clipped.values()))

    rows: list[StationWeight] = []
    for point in all_points:
        eligible, reason, temporal_coverage = eligibility[point.station_key]
        geometry = clipped.get(point.station_key)
        area = geometry.area if geometry is not None else 0.0
        display_geometry = (
            transform(to_display, geometry)
            if geometry is not None and not geometry.is_empty
            else geometry
        )
        rows.append(
            StationWeight(
                station_key=point.station_key,
                station_name=point.station_name,
                city=point.city,
                latitude=point.latitude,
                longitude=point.longitude,
                eligible=eligible,
                exclusion_reason=reason,
                temporal_coverage=temporal_coverage,
                watershed_area_m2=watershed_area,
                thiessen_area_m2=area,
                weight=area / watershed_area,
                geometry=display_geometry,
                aggregated_observation_count=aggregation_counts.get(
                    point.station_key, 0
                ),
            )
        )
    positive_sum = sum(row.weight for row in rows if row.weight > 0)
    if not math.isclose(positive_sum, 1.0, rel_tol=AREA_RELATIVE_TOLERANCE):
        raise SpatialAnalysisError(
            f"Positive Thiessen weights sum to {positive_sum:.9f}, not 1.0."
        )
    return tuple(rows)


def _construction_extent(
    watershed: BaseGeometry, station_points: BaseGeometry
) -> BaseGeometry:
    """Create a finite envelope that contains the watershed and all stations."""

    min_x, min_y, max_x, max_y = unary_union([watershed, station_points]).bounds
    span = max(max_x - min_x, max_y - min_y, 1.0)
    margin = span * 2
    return box(min_x - margin, min_y - margin, max_x + margin, max_y + margin)


def _validate_clipped_geometry(
    watershed: BaseGeometry, geometries: Sequence[BaseGeometry]
) -> None:
    """Reject invalid, overlapping, or incomplete clipped polygon coverage."""

    if any(not geometry.is_valid for geometry in geometries):
        raise SpatialAnalysisError("A clipped Thiessen geometry is invalid.")
    area_tolerance = max(watershed.area * AREA_RELATIVE_TOLERANCE, 0.01)
    total_area = sum(geometry.area for geometry in geometries)
    union_area = unary_union(list(geometries)).area
    if total_area - union_area > area_tolerance:
        raise SpatialAnalysisError(
            "Clipped Thiessen polygons overlap within the watershed."
        )
    if abs(union_area - watershed.area) > area_tolerance:
        raise SpatialAnalysisError(
            "Clipped Thiessen polygons do not cover the watershed."
        )
    if abs(total_area - watershed.area) > area_tolerance:
        raise SpatialAnalysisError(
            "Clipped Thiessen areas do not sum to watershed area."
        )


def _calculate_areal_rainfall(
    timeline: Sequence[datetime],
    aligned: dict[str, dict[datetime, float]],
    weights: Sequence[StationWeight],
) -> tuple[ArealRainfall, ...]:
    """Apply fixed positive weights without filling or redistributing gaps."""

    eligible = [weight for weight in weights if weight.eligible]
    positive = [weight for weight in eligible if weight.weight > 0]
    rows: list[ArealRainfall] = []
    for timestamp in timeline:
        available = [
            weight
            for weight in positive
            if timestamp in aligned.get(weight.station_key, {})
        ]
        coverage_fraction = sum(weight.weight for weight in available)
        complete = math.isclose(coverage_fraction, 1.0, rel_tol=AREA_RELATIVE_TOLERANCE)
        weighted_value: float | None = None
        simple_mean: float | None = None
        if complete:
            values = [aligned[weight.station_key][timestamp] for weight in positive]
            weighted_value = sum(
                weight.weight * aligned[weight.station_key][timestamp]
                for weight in positive
            )
            simple_mean = sum(values) / len(values)
        rows.append(
            ArealRainfall(
                timestamp=timestamp,
                rain_in=weighted_value,
                simple_mean_rain_in=simple_mean,
                coverage_fraction=coverage_fraction,
                stations_used=len(available),
                eligible_station_count=len(eligible),
                quality_flag="complete" if complete else "incomplete",
            )
        )
    return tuple(rows)


def _weight_row(weight: StationWeight) -> dict[str, object]:
    """Convert one station weight into its stable tabular representation."""

    return {
        "station_key": weight.station_key,
        "station_name": weight.station_name,
        "city": weight.city,
        "latitude": weight.latitude,
        "longitude": weight.longitude,
        "eligible": weight.eligible,
        "exclusion_reason": weight.exclusion_reason,
        "temporal_coverage": round(weight.temporal_coverage, 8),
        "watershed_area_m2": round(weight.watershed_area_m2, 3),
        "thiessen_area_m2": round(weight.thiessen_area_m2, 3),
        "thiessen_area_km2": round(weight.thiessen_area_km2, 8),
        "area_percent": round(weight.area_percent, 8),
        "weight": round(weight.weight, 10),
        "analysis_crs": ANALYSIS_CRS,
        "aggregated_observation_count": weight.aggregated_observation_count,
    }


def _weight_rows(weights: Sequence[StationWeight]) -> list[dict[str, object]]:
    """Convert all station weights into stable CSV rows."""

    return [_weight_row(weight) for weight in weights]


def _weight_fields() -> list[str]:
    """Return the stable weights CSV column order."""

    return [
        "station_key",
        "station_name",
        "city",
        "latitude",
        "longitude",
        "eligible",
        "exclusion_reason",
        "temporal_coverage",
        "watershed_area_m2",
        "thiessen_area_m2",
        "thiessen_area_km2",
        "area_percent",
        "weight",
        "analysis_crs",
        "aggregated_observation_count",
    ]


def _rainfall_rows(rows: Sequence[ArealRainfall]) -> list[dict[str, object]]:
    """Convert watershed rainfall values into stable CSV rows."""

    return [
        {
            "Date_hour": row.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "RainIn": "" if row.rain_in is None else round(row.rain_in, 10),
            "simple_mean_RainIn": ""
            if row.simple_mean_rain_in is None
            else round(row.simple_mean_rain_in, 10),
            "coverage_fraction": round(row.coverage_fraction, 10),
            "stations_used": row.stations_used,
            "eligible_station_count": row.eligible_station_count,
            "quality_flag": row.quality_flag,
            "method": "thiessen",
        }
        for row in rows
    ]


def _rainfall_fields() -> list[str]:
    """Return the stable watershed rainfall CSV column order."""

    return [
        "Date_hour",
        "RainIn",
        "simple_mean_RainIn",
        "coverage_fraction",
        "stations_used",
        "eligible_station_count",
        "quality_flag",
        "method",
    ]
