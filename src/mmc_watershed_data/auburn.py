from __future__ import annotations

import time as time_module
from datetime import UTC, date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from .api import chunk_dates, post_json
from .models import Station, StationFailure, StationResult
from .stations import (
    AUBURN_API_URL,
    AUBURN_DASHBOARD_UUID,
    AUBURN_METRIC_NAME,
    AUBURN_STATIONS,
)
from .storage import write_csv, write_json


FIXED_UTC_MINUS_6 = timezone(timedelta(hours=-6))
CHUNK_DAYS = 7
LIMIT = 10000
MAX_RETRIES = 3
REQUEST_DELAY_SECONDS = 0.4


def build_headers() -> dict[str, str]:
    return {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "origin": "https://www.licor.cloud",
        "referer": f"https://www.licor.cloud/dashboards/public/{AUBURN_DASHBOARD_UUID}/true",
        "user-agent": "python-requests",
    }


def _to_epoch_ms(value: datetime) -> int:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    else:
        value = value.astimezone(UTC)
    return int(value.timestamp() * 1000)


def _local_day_window(start_date: date, end_date: date) -> tuple[datetime, datetime]:
    start_local = datetime.combine(start_date, time.min, FIXED_UTC_MINUS_6)
    end_local = datetime.combine(end_date + timedelta(days=1), time.min, FIXED_UTC_MINUS_6)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


def _build_body(station: Station, start_utc: datetime, end_utc: datetime) -> dict[str, Any]:
    return {
        "dashboardUUID": AUBURN_DASHBOARD_UUID,
        "channels": [
            {
                "channelUUID": station.identifier,
                "channelType": "dataChannel",
                "metricName": AUBURN_METRIC_NAME,
                "limit": LIMIT,
                "aggregationFunction": "avg",
                "aggregationInterval": {"value": 10, "unit": "minutes"},
            }
        ],
        "time": {
            "absolute": {
                "from": _to_epoch_ms(start_utc),
                "to": _to_epoch_ms(end_utc),
            }
        },
    }


def _extract_raw_rows(payload: dict[str, Any], station: Station) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    records = payload.get("value", {}).get("records", [])
    for record in records:
        for timestamp_ms, value in record.get("datum", {}).get("valid", []):
            rows.append(
                {
                    "city": station.city,
                    "station_key": station.key,
                    "station_name": station.name,
                    "timestamp_ms": timestamp_ms,
                    "value": value,
                }
            )
    return rows


def _convert_processed_rows(
    raw_rows: list[dict[str, Any]],
    station: Station,
) -> list[dict[str, Any]]:
    processed: list[dict[str, Any]] = []
    offset = timedelta(hours=-6)
    for row in raw_rows:
        timestamp_utc = datetime.fromtimestamp(int(row["timestamp_ms"]) / 1000, tz=UTC)
        date_hour = (timestamp_utc + offset).replace(tzinfo=None).isoformat(sep=" ")
        processed.append(
            {
                "city": station.city,
                "station_key": station.key,
                "station_name": station.name,
                "Date_hour": date_hour,
                "RainIn": row["value"],
            }
        )
    processed.sort(key=lambda item: item["Date_hour"])

    deduplicated: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in processed:
        key = row["Date_hour"]
        if key not in seen:
            seen.add(key)
            deduplicated.append(row)
    return deduplicated


def collect_station(
    station: Station,
    start_date: date,
    end_date: date,
    raw_dir: Path,
    processed_dir: Path,
) -> StationResult:
    windows = chunk_dates(start_date, end_date, CHUNK_DAYS)
    headers = build_headers()
    raw_rows: list[dict[str, Any]] = []
    raw_windows: list[dict[str, Any]] = []

    for window_start, window_end in windows:
        last_error: str | None = None
        payload: dict[str, Any] | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                payload = post_json(
                    AUBURN_API_URL,
                    _build_body(station, *_local_day_window(window_start, window_end)),
                    headers,
                )
                break
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                if attempt < MAX_RETRIES:
                    time_module.sleep(attempt)
        if payload is None:
            raise RuntimeError(last_error or "Auburn request failed.")
        raw_windows.append(
            {
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
                "payload": payload,
            }
        )
        raw_rows.extend(_extract_raw_rows(payload, station))
        time_module.sleep(REQUEST_DELAY_SECONDS)

    processed_rows = _convert_processed_rows(raw_rows, station)

    raw_json_path = raw_dir / f"{station.key}_{start_date.isoformat()}_to_{end_date.isoformat()}_raw.json"
    raw_csv_path = raw_dir / f"{station.key}_{start_date.isoformat()}_to_{end_date.isoformat()}_raw.csv"
    processed_path = (
        processed_dir
        / f"{station.key}_{start_date.isoformat()}_to_{end_date.isoformat()}_processed.csv"
    )

    raw_fieldnames = ["city", "station_key", "station_name", "timestamp_ms", "value"]
    processed_fieldnames = ["city", "station_key", "station_name", "Date_hour", "RainIn"]

    write_json(
        raw_json_path,
        {
            "source": "auburn",
            "station": station.name,
            "station_key": station.key,
            "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "windows": raw_windows,
        },
    )
    write_csv(raw_csv_path, raw_rows, raw_fieldnames)
    write_csv(processed_path, processed_rows, processed_fieldnames)

    return StationResult(
        station=station,
        raw_json_path=raw_json_path,
        raw_csv_path=raw_csv_path,
        processed_path=processed_path,
        raw_rows=len(raw_rows),
        processed_rows=len(processed_rows),
        chunks=len(windows),
    )


def collect_all(
    start_date: date,
    end_date: date,
    root: Path,
) -> tuple[list[StationResult], list[StationFailure]]:
    raw_dir = root / "data" / "raw" / "auburn"
    processed_dir = root / "data" / "processed" / "auburn"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    results: list[StationResult] = []
    failures: list[StationFailure] = []
    for station in AUBURN_STATIONS:
        try:
            results.append(collect_station(station, start_date, end_date, raw_dir, processed_dir))
        except Exception as exc:  # noqa: BLE001
            failures.append(StationFailure(station, str(exc)))
    return results, failures
