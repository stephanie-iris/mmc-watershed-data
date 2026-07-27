from __future__ import annotations

from .models import Station


AUBURN_DASHBOARD_UUID = "52f7495a-bd9c-48ff-a568-20431bc95b60"
AUBURN_API_URL = "https://www.licor.cloud/api/v2/timeseriesdata"
AUBURN_METRIC_NAME = "com.onset.sensordata.rain_us"

OPELIKA_API_BASE = "https://360.thormobile.net/thorcloud/api/"
OPELIKA_ENDPOINT = f"{OPELIKA_API_BASE}weatherpacketsbyinterval"

AUBURN_STATIONS: tuple[Station, ...] = (
    Station(
        "auburn",
        "Auburn",
        "wrm_office",
        "WRM Office",
        "37a674cc-ac08-404b-a53f-95e74bc540c6",
    ),
    Station(
        "auburn",
        "Auburn",
        "lake_ogletree",
        "Lake Ogletree",
        "b41b722b-ed1a-4295-94b2-22c3847837e9",
    ),
    Station(
        "auburn",
        "Auburn",
        "northside_wpcf",
        "Northside WPCF",
        "ce88cb8e-e006-497e-9028-46821fe99514",
    ),
    Station(
        "auburn",
        "Auburn",
        "nw_auburn_tank",
        "NW Auburn Tank",
        "ebb84196-f534-401d-82ea-fa898fe31a41",
    ),
    Station(
        "auburn",
        "Auburn",
        "hc_morgan_wpcf",
        "HC Morgan WPCF",
        "e8cf2c10-c489-47a9-95fc-8d2d11c1ac71",
    ),
)

OPELIKA_STATIONS: tuple[Station, ...] = (
    Station("opelika", "Opelika", "sportsplex", "Sportsplex", "236"),
    Station("opelika", "Opelika", "floral_park", "Floral Park", "339"),
    Station("opelika", "Opelika", "west_ridge_park", "West Ridge Park", "338"),
    Station("opelika", "Opelika", "covington_center", "Covington Center", "337"),
)
