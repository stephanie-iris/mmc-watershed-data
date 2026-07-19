from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DownloadWindow:
    start: datetime
    end: datetime


@dataclass(frozen=True)
class RainRecord:
    timestamp_utc: datetime
    timestamp_local: datetime
    rain_in: float


@dataclass(frozen=True)
class DownloadSummary:
    station: str
    row_count: int
    raw_path: str
    processed_path: str

