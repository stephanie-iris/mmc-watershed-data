"""Opelika ThorArchive collection and cumulative-rainfall processing."""

from __future__ import annotations

import time as time_module
from datetime import date
import logging
from pathlib import Path
from typing import Any

from .api import first_seen_fieldnames, get_json, us_date
from .models import Station, StationFailure, StationResult
from .stations import OPELIKA_ENDPOINT, OPELIKA_STATIONS
from .storage import write_csv, write_json
from .validation import validate_opelika_records


MAX_RETRIES = 3
REQUEST_DELAY_SECONDS = 0.4
logger = logging.getLogger(__name__)


def _build_url(station: Station, start_date: date, end_date: date) -> str:
    """Build the station-specific ThorArchive URL for an inclusive date range."""

    return (
        f"{OPELIKA_ENDPOINT}?ids={station.identifier}"
        f"&startTime={us_date(start_date)}&endTime={us_date(end_date)}"
    )


def _extract_raw_rows(
    records: list[dict[str, Any]], station: Station
) -> list[dict[str, Any]]:
    """Validate provider records and add MMC station identity columns."""

    validated_records = validate_opelika_records(records)
    rows: list[dict[str, Any]] = []
    for record, _validated in zip(records, validated_records):
        row = {
            "city": station.city,
            "station_key": station.key,
            "station_name": station.name,
        }
        row.update(record)
        rows.append(row)
    return rows


def _convert_processed_rows(
    raw_rows: list[dict[str, Any]],
    station: Station,
) -> list[dict[str, Any]]:
    """Convert cumulative ``RainToday`` values into interval rainfall rows."""

    parsed: list[tuple[str, float]] = []
    for row in raw_rows:
        created = str(row.get("CreatedDT") or "").strip()
        cumulative_value = row.get("RainToday")
        if cumulative_value is None:
            continue
        try:
            cumulative = float(cumulative_value)
        except (TypeError, ValueError):
            continue
        if created:
            parsed.append((created, cumulative))

    parsed.sort(key=lambda item: item[0])

    processed: list[dict[str, Any]] = []
    previous: float | None = None
    for created, cumulative in parsed:
        if previous is None:
            rain_in = cumulative
        else:
            rain_in = cumulative - previous
            if rain_in < 0:
                rain_in = cumulative
        processed.append(
            {
                "city": station.city,
                "station_key": station.key,
                "station_name": station.name,
                "Date_hour": created,
                "RainIn": rain_in,
            }
        )
        previous = cumulative
    return processed


def collect_station(
    station: Station,
    start_date: date,
    end_date: date,
    raw_dir: Path,
    processed_dir: Path,
) -> StationResult:
    """Collect, preserve, validate, and write one Opelika station's outputs."""

    raw_rows: list[dict[str, Any]] = []
    last_error: str | None = None
    payload: Any | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                "Requesting Opelika station %s for %s through %s (attempt %d).",
                station.name,
                start_date,
                end_date,
                attempt,
            )
            payload = get_json(_build_url(station, start_date, end_date))
            break
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
            logger.warning(
                "Opelika request failed for %s on attempt %d: %s",
                station.name,
                attempt,
                exc,
            )
            if attempt < MAX_RETRIES:
                time_module.sleep(attempt)
    if payload is None:
        raise RuntimeError(last_error or "Opelika request failed.")
    if not isinstance(payload, list):
        raise RuntimeError("The endpoint response was not a JSON list.")

    raw_json_path = (
        raw_dir
        / f"{station.key}_{start_date.isoformat()}_to_{end_date.isoformat()}_raw.json"
    )
    raw_csv_path = (
        raw_dir
        / f"{station.key}_{start_date.isoformat()}_to_{end_date.isoformat()}_raw.csv"
    )
    processed_path = (
        processed_dir
        / f"{station.key}_{start_date.isoformat()}_to_{end_date.isoformat()}_processed.csv"
    )

    processed_fieldnames = [
        "city",
        "station_key",
        "station_name",
        "Date_hour",
        "RainIn",
    ]

    write_json(
        raw_json_path,
        {
            "source": "opelika",
            "station": station.name,
            "station_key": station.key,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "request": {
                "startTime": us_date(start_date),
                "endTime": us_date(end_date),
                "payload": payload,
            },
        },
    )
    logger.info("Saved Opelika raw JSON evidence to %s.", raw_json_path)

    raw_rows.extend(_extract_raw_rows(payload, station))
    raw_fieldnames = first_seen_fieldnames(raw_rows) or [
        "city",
        "station_key",
        "station_name",
    ]
    processed_rows = _convert_processed_rows(raw_rows, station)
    write_csv(raw_csv_path, raw_rows, raw_fieldnames)
    write_csv(processed_path, processed_rows, processed_fieldnames)
    logger.info("Saved Opelika raw and processed CSV files for %s.", station.name)

    return StationResult(
        station=station,
        raw_json_path=raw_json_path,
        raw_csv_path=raw_csv_path,
        processed_path=processed_path,
        raw_rows=len(raw_rows),
        processed_rows=len(processed_rows),
        chunks=1,
    )


def collect_all(
    start_date: date,
    end_date: date,
    root: Path,
) -> tuple[list[StationResult], list[StationFailure]]:
    """Collect every configured Opelika station and isolate station failures."""

    raw_dir = root / "data" / "raw" / "opelika"
    processed_dir = root / "data" / "processed" / "opelika"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    results: list[StationResult] = []
    failures: list[StationFailure] = []
    for station in OPELIKA_STATIONS:
        try:
            results.append(
                collect_station(station, start_date, end_date, raw_dir, processed_dir)
            )
        except Exception as exc:  # noqa: BLE001
            failures.append(StationFailure(station, str(exc)))
    return results, failures
