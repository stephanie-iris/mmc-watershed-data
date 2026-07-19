from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    dashboard_uuid: str = "52f7495a-bd9c-48ff-a568-20431bc95b60"
    channel_uuid: str = "b41b722b-ed1a-4295-94b2-22c3847837e9"
    metric_name: str = "com.onset.sensordata.rain_us"
    api_url: str = "https://www.licor.cloud/api/v2/timeseriesdata"
    station: str = "City of Auburn - Ogletree"
    interval_minutes: int = 10
    chunk_days: int = 7
    limit: int = 10_000
    request_delay_seconds: float = 0.4
    max_retries: int = 3
    timezone_offset_hours: int = -6
def project_root() -> Path:
    return Path(__file__).resolve().parents[2]
