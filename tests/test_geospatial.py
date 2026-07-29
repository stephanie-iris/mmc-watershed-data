from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mmc_watershed_data.geospatial import (  # noqa: E402
    load_station_points,
    load_watershed_boundary,
)


class GeospatialTests(unittest.TestCase):
    def test_station_kmzs_contain_all_known_stations(self) -> None:
        points = load_station_points(ROOT)

        self.assertEqual(len(points), 9)
        self.assertEqual(sum(point.city == "Auburn" for point in points), 5)
        self.assertEqual(sum(point.city == "Opelika" for point in points), 4)
        self.assertIn("Lake Ogletree", {point.station_name for point in points})

    def test_watershed_kmz_contains_a_polygon_boundary(self) -> None:
        boundary = load_watershed_boundary(ROOT)

        self.assertGreater(len(boundary), 100)
        self.assertTrue(all(-86 < longitude < -84 for _, longitude in boundary))
        self.assertTrue(all(32 < latitude < 34 for latitude, _ in boundary))


if __name__ == "__main__":
    unittest.main()
