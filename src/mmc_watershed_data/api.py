from __future__ import annotations

import json
import ssl
from datetime import date, timedelta
from typing import Any
from urllib import error, parse, request


def _ssl_context() -> ssl.SSLContext:
    return ssl._create_unverified_context()


def get_json(url: str, headers: dict[str, str] | None = None, timeout: int = 90) -> Any:
    req = request.Request(url, headers=headers or {}, method="GET")
    try:
        with request.urlopen(req, timeout=timeout, context=_ssl_context()) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc


def post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
    timeout: int = 90,
) -> Any:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers=headers or {}, method="POST")
    try:
        with request.urlopen(req, timeout=timeout, context=_ssl_context()) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"HTTP {exc.code}: {body_text}") from exc


def chunk_dates(start: date, end: date, chunk_days: int) -> list[tuple[date, date]]:
    if start > end:
        return []

    windows: list[tuple[date, date]] = []
    cursor = start
    step = timedelta(days=chunk_days - 1)
    while cursor <= end:
        window_end = min(cursor + step, end)
        windows.append((cursor, window_end))
        cursor = window_end + timedelta(days=1)
    return windows


def date_range(start: date, end: date) -> list[date]:
    if start > end:
        return []

    dates: list[date] = []
    cursor = start
    while cursor <= end:
        dates.append(cursor)
        cursor += timedelta(days=1)
    return dates


def first_seen_fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    headers: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                headers.append(key)
    return headers


def us_date(value: date) -> str:
    return f"{value.month}/{value.day}/{value.year}"

