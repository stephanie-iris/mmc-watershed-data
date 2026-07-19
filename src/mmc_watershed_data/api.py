from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib import error, request

from .config import AppConfig
from .models import DownloadWindow, RainRecord


def dt_to_ms(value: datetime) -> int:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return int(value.timestamp() * 1000)


def build_windows(start: datetime, end: datetime, chunk_days: int) -> list[DownloadWindow]:
    windows: list[DownloadWindow] = []
    cursor = start
    step = timedelta(days=chunk_days)
    while cursor < end:
        next_end = min(cursor + step, end)
        windows.append(DownloadWindow(start=cursor, end=next_end))
        cursor = next_end
    return windows


def build_body(config: AppConfig, window: DownloadWindow) -> dict[str, Any]:
    return {
        "dashboardUUID": config.dashboard_uuid,
        "channels": [
            {
                "channelUUID": config.channel_uuid,
                "channelType": "dataChannel",
                "metricName": config.metric_name,
                "limit": config.limit,
                "aggregationFunction": "avg",
                "aggregationInterval": {"value": config.interval_minutes, "unit": "minutes"},
            }
        ],
        "time": {
            "absolute": {
                "from": dt_to_ms(window.start),
                "to": dt_to_ms(window.end),
            }
        },
    }


def build_headers(config: AppConfig) -> dict[str, str]:
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "origin": "https://www.licor.cloud",
        "referer": f"https://www.licor.cloud/dashboards/public/{config.dashboard_uuid}/true",
        "user-agent": "python-requests",
    }
    return headers


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: int) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')[:500]}") from exc


def _extract_records(payload: dict[str, Any], tz_offset_hours: int) -> list[RainRecord]:
    records = payload.get("value", {}).get("records", [])
    rows: list[RainRecord] = []
    offset = timedelta(hours=tz_offset_hours)
    for record in records:
        for ts_ms, value in record.get("datum", {}).get("valid", []):
            timestamp_utc = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
            rows.append(
                RainRecord(
                    timestamp_utc=timestamp_utc.replace(tzinfo=None),
                    timestamp_local=(timestamp_utc + offset).replace(tzinfo=None),
                    rain_in=float(value),
                )
            )
    return rows


def fetch_window(
    config: AppConfig,
    window: DownloadWindow,
) -> tuple[list[RainRecord], dict[str, Any]]:
    last_error: str | None = None
    headers = build_headers(config)
    payload: dict[str, Any] | None = None

    for attempt in range(1, config.max_retries + 1):
        try:
            payload = post_json(config.api_url, build_body(config, window), headers, timeout=90)
            break
        except Exception as exc:
            last_error = str(exc)
        if attempt < config.max_retries:
            time.sleep(attempt)
    else:
        raise RuntimeError(last_error or "Request failed.")

    assert payload is not None
    rows = _extract_records(payload, config.timezone_offset_hours)
    return rows, payload


def save_raw_payload(raw_dir: Path, window: DownloadWindow, payload: dict[str, Any]) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"ogletree_{window.start.date().isoformat()}_to_{window.end.date().isoformat()}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def dedupe_and_sort(records: list[RainRecord]) -> list[RainRecord]:
    unique: dict[datetime, RainRecord] = {}
    for record in records:
        unique[record.timestamp_utc] = record
    return sorted(unique.values(), key=lambda row: row.timestamp_utc)
