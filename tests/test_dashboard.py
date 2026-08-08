from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import sys
import unittest

from shapely.geometry import Polygon


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mmc_watershed_data.analysis import RainfallRecord  # noqa: E402
from mmc_watershed_data.dashboard import (  # noqa: E402
    CITY_COLORS,
    _build_map,
    _build_spatial_map,
    _station_totals,
)
from mmc_watershed_data.geospatial import StationPoint  # noqa: E402
from mmc_watershed_data.spatial import SpatialAnalysis, StationWeight  # noqa: E402


class DashboardTests(unittest.TestCase):
    def test_map_uses_openstreetmap_and_city_colors(self) -> None:
        points = (
            StationPoint("Auburn", "a", "Auburn A", 32.6, -85.5),
            StationPoint("Opelika", "b", "Opelika B", 32.65, -85.4),
        )

        station_map = _build_map(points, ((32.5, -85.6), (32.7, -85.6), (32.7, -85.3)))
        html = station_map.get_root().render()

        self.assertIn("OpenStreetMap", html)
        self.assertIn(CITY_COLORS["Auburn"], html)
        self.assertIn(CITY_COLORS["Opelika"], html)

    def test_station_totals_are_derived_from_processed_records(self) -> None:
        records = [
            RainfallRecord("Auburn", "a", "Auburn A", datetime(2026, 1, 1), 0.2),
            RainfallRecord("Auburn", "a", "Auburn A", datetime(2026, 1, 1, 1), 0.3),
        ]

        self.assertEqual(_station_totals(records), {"a": 0.5})

    def test_spatial_map_contains_thiessen_watershed_and_station_layers(self) -> None:
        points = (
            StationPoint("Auburn", "a", "Auburn A", 32.6, -85.5),
            StationPoint("Opelika", "b", "Opelika B", 32.6, -85.4),
        )
        boundary = (
            (32.55, -85.55),
            (32.55, -85.35),
            (32.65, -85.35),
            (32.65, -85.55),
            (32.55, -85.55),
        )
        weights = (
            StationWeight(
                "a",
                "Auburn A",
                "Auburn",
                32.6,
                -85.5,
                True,
                "",
                1.0,
                100.0,
                50.0,
                0.5,
                Polygon(
                    [
                        (-85.55, 32.55),
                        (-85.45, 32.55),
                        (-85.45, 32.65),
                        (-85.55, 32.65),
                    ]
                ),
            ),
            StationWeight(
                "b",
                "Opelika B",
                "Opelika",
                32.6,
                -85.4,
                True,
                "",
                1.0,
                100.0,
                50.0,
                0.5,
                Polygon(
                    [
                        (-85.45, 32.55),
                        (-85.35, 32.55),
                        (-85.35, 32.65),
                        (-85.45, 32.65),
                    ]
                ),
            ),
        )
        analysis = SpatialAnalysis(
            date(2026, 1, 1),
            date(2026, 1, 1),
            weights,
            (),
            100.0,
            0.9,
        )

        html = _build_spatial_map(points, boundary, analysis).get_root().render()

        self.assertIn("OpenStreetMap", html)
        self.assertIn("Clipped Thiessen polygons", html)
        self.assertIn("MMC watershed boundary", html)
        self.assertIn("Station eligibility", html)
        self.assertIn("Auburn A", html)
        self.assertIn("Opelika B", html)


if __name__ == "__main__":
    unittest.main()
