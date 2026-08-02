"""Pure rainfall analysis functions used by the dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from os import PathLike
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class RainfallRecord:
    """One trusted processed rainfall observation."""

    city: str
    station_key: str
    station_name: str
    timestamp: datetime
    rain_in: float


@dataclass(frozen=True)
class RainfallEvent:
    """One merged rainfall event across the selected stations."""

    start: datetime
    end: datetime
    total_rain_in: float
    station_names: tuple[str, ...]

    @property
    def duration_minutes(self) -> float:
        """Return the event duration between its first and last observations."""

        return (self.end - self.start).total_seconds() / 60


@dataclass
class _EventGroup:
    """Mutable accumulator used while merging positive rainfall records."""

    start: datetime
    end: datetime
    total_rain_in: float
    station_names: set[str]


def load_rainfall_records(path: str | PathLike[str]) -> list[RainfallRecord]:
    """Load processed CSV rows into typed records.

    The dashboard passes a ``Path`` here, but accepting a path-like object keeps
    this helper easy to use in tests and future data-loading clients.
    """

    import csv

    records: list[RainfallRecord] = []
    with Path(path).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            records.append(
                RainfallRecord(
                    city=row["city"],
                    station_key=row["station_key"],
                    station_name=row["station_name"],
                    timestamp=datetime.fromisoformat(row["Date_hour"]),
                    rain_in=float(row["RainIn"]),
                )
            )
    return records


def detect_events(
    records: Iterable[RainfallRecord],
    *,
    merge_tolerance: timedelta = timedelta(hours=1),
) -> list[RainfallEvent]:
    """Detect positive-rain station events and merge overlapping regional events."""

    station_groups: dict[str, list[RainfallRecord]] = {}
    for record in records:
        if record.rain_in > 0:
            station_groups.setdefault(record.station_key, []).append(record)

    station_events: list[_EventGroup] = []
    for station_records in station_groups.values():
        ordered = sorted(station_records, key=lambda item: item.timestamp)
        current: _EventGroup | None = None
        previous_timestamp: datetime | None = None
        for record in ordered:
            if (
                current is None
                or previous_timestamp is None
                or record.timestamp - previous_timestamp > merge_tolerance
            ):
                if current is not None:
                    station_events.append(current)
                current = _EventGroup(
                    start=record.timestamp,
                    end=record.timestamp,
                    total_rain_in=record.rain_in,
                    station_names={record.station_name},
                )
            else:
                current.end = record.timestamp
                current.total_rain_in += record.rain_in
                current.station_names.add(record.station_name)
            previous_timestamp = record.timestamp
        if current is not None:
            station_events.append(current)

    regional_groups: list[_EventGroup] = []
    for station_event in sorted(station_events, key=lambda item: item.start):
        if (
            not regional_groups
            or station_event.start > regional_groups[-1].end + merge_tolerance
        ):
            regional_groups.append(
                _EventGroup(
                    start=station_event.start,
                    end=station_event.end,
                    total_rain_in=station_event.total_rain_in,
                    station_names=set(station_event.station_names),
                )
            )
            continue
        group = regional_groups[-1]
        group.end = max(group.end, station_event.end)
        group.total_rain_in += station_event.total_rain_in
        group.station_names.update(station_event.station_names)

    return [
        RainfallEvent(
            start=group.start,
            end=group.end,
            total_rain_in=group.total_rain_in,
            station_names=tuple(sorted(group.station_names)),
        )
        for group in regional_groups
    ]
