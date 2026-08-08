"""Offline tests for Thiessen geometry and watershed rainfall behavior."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mmc_watershed_data.analysis import RainfallRecord  # noqa: E402
from mmc_watershed_data.geospatial import StationPoint  # noqa: E402
from mmc_watershed_data.spatial import (  # noqa: E402
    ANALYSIS_CRS,
    SpatialAnalysisError,
    align_to_ten_minutes,
    analyze_spatial_rainfall,
    create_spatial_products,
    expected_timeline,
)


POINTS = (
    StationPoint("Auburn", "west", "West", 32.58, -85.53),
    StationPoint("Auburn", "north", "North", 32.66, -85.48),
    StationPoint("Opelika", "east", "East", 32.58, -85.42),
    StationPoint("Opelika", "far", "Far", 32.72, -85.35),
)
BOUNDARY = (
    (32.55, -85.55),
    (32.55, -85.40),
    (32.67, -85.40),
    (32.67, -85.55),
    (32.55, -85.55),
)


def complete_records() -> list[RainfallRecord]:
    """Return one complete synthetic day for every test station."""

    records: list[RainfallRecord] = []
    for index, point in enumerate(POINTS, start=1):
        for timestamp in expected_timeline(date(2026, 1, 1), date(2026, 1, 1)):
            records.append(
                RainfallRecord(
                    city=point.city,
                    station_key=point.station_key,
                    station_name=point.station_name,
                    timestamp=timestamp,
                    rain_in=index / 100,
                )
            )
    return records


class SpatialTests(unittest.TestCase):
    def test_timestamps_round_to_nearest_interval_with_ties_forward(self) -> None:
        self.assertEqual(
            align_to_ten_minutes(datetime(2026, 1, 1, 10, 4, 59)),
            datetime(2026, 1, 1, 10, 0),
        )
        self.assertEqual(
            align_to_ten_minutes(datetime(2026, 1, 1, 10, 5)),
            datetime(2026, 1, 1, 10, 10),
        )

    def test_complete_records_cover_watershed_and_weights_sum_to_one(self) -> None:
        with (
            patch(
                "mmc_watershed_data.spatial.load_station_points", return_value=POINTS
            ),
            patch(
                "mmc_watershed_data.spatial.load_watershed_boundary",
                return_value=BOUNDARY,
            ),
        ):
            result = analyze_spatial_rainfall(
                ROOT, complete_records(), date(2026, 1, 1), date(2026, 1, 1)
            )

        self.assertEqual(result.eligible_count, 4)
        self.assertGreater(result.watershed_area_m2, 1_000_000)
        self.assertAlmostEqual(sum(row.weight for row in result.weights), 1.0)
        self.assertEqual(len(result.rainfall), 144)
        self.assertTrue(all(row.quality_flag == "complete" for row in result.rainfall))
        self.assertAlmostEqual(
            result.rainfall[0].rain_in or 0,
            sum(
                row.weight * ((index + 1) / 100)
                for index, row in enumerate(result.weights)
            ),
        )

    def test_missing_positive_weight_record_remains_incomplete(self) -> None:
        records = complete_records()
        records = [
            record
            for record in records
            if not (
                record.station_key == "west"
                and record.timestamp == datetime(2026, 1, 1)
            )
        ]
        with (
            patch(
                "mmc_watershed_data.spatial.load_station_points", return_value=POINTS
            ),
            patch(
                "mmc_watershed_data.spatial.load_watershed_boundary",
                return_value=BOUNDARY,
            ),
        ):
            result = analyze_spatial_rainfall(
                ROOT, records, date(2026, 1, 1), date(2026, 1, 1)
            )

        first = result.rainfall[0]
        self.assertEqual(first.quality_flag, "incomplete")
        self.assertIsNone(first.rain_in)
        self.assertIsNone(first.simple_mean_rain_in)
        self.assertLess(first.coverage_fraction, 1.0)

    def test_auburn_values_in_one_aligned_interval_are_summed(self) -> None:
        records = complete_records()
        records.append(
            RainfallRecord(
                "Auburn", "west", "West", datetime(2026, 1, 1, 0, 0, 30), 0.2
            )
        )
        with (
            patch(
                "mmc_watershed_data.spatial.load_station_points", return_value=POINTS
            ),
            patch(
                "mmc_watershed_data.spatial.load_watershed_boundary",
                return_value=BOUNDARY,
            ),
            self.assertLogs("mmc_watershed_data.spatial", level="INFO") as logs,
        ):
            result = analyze_spatial_rainfall(
                ROOT, records, date(2026, 1, 1), date(2026, 1, 1)
            )

        west = next(row for row in result.weights if row.station_key == "west")
        baseline = sum(
            weight.weight * ((index + 1) / 100)
            for index, weight in enumerate(result.weights)
        )
        self.assertTrue(west.eligible)
        self.assertEqual(west.aggregated_observation_count, 1)
        self.assertAlmostEqual(
            result.rainfall[0].rain_in or 0, baseline + 0.2 * west.weight
        )
        self.assertIn("Summed 1 additional Auburn interval", " ".join(logs.output))

    def test_opelika_values_in_one_aligned_interval_are_summed(self) -> None:
        records = complete_records()
        records.append(
            RainfallRecord(
                "Opelika", "east", "East", datetime(2026, 1, 1, 0, 0, 30), 0.2
            )
        )
        with (
            patch(
                "mmc_watershed_data.spatial.load_station_points", return_value=POINTS
            ),
            patch(
                "mmc_watershed_data.spatial.load_watershed_boundary",
                return_value=BOUNDARY,
            ),
            self.assertLogs("mmc_watershed_data.spatial", level="INFO") as logs,
        ):
            result = analyze_spatial_rainfall(
                ROOT, records, date(2026, 1, 1), date(2026, 1, 1)
            )

        east = next(row for row in result.weights if row.station_key == "east")
        baseline = sum(
            weight.weight * ((index + 1) / 100)
            for index, weight in enumerate(result.weights)
        )
        self.assertTrue(east.eligible)
        self.assertAlmostEqual(
            result.rainfall[0].rain_in or 0, baseline + 0.2 * east.weight
        )
        self.assertIn("Summed 1 additional Opelika interval", " ".join(logs.output))

    def test_exact_duplicate_is_ignored_without_double_counting(self) -> None:
        records = complete_records()
        records.append(
            RainfallRecord("Opelika", "east", "East", datetime(2026, 1, 1), 0.03)
        )
        with (
            patch(
                "mmc_watershed_data.spatial.load_station_points", return_value=POINTS
            ),
            patch(
                "mmc_watershed_data.spatial.load_watershed_boundary",
                return_value=BOUNDARY,
            ),
            self.assertLogs("mmc_watershed_data.spatial", level="INFO") as logs,
        ):
            result = analyze_spatial_rainfall(
                ROOT, records, date(2026, 1, 1), date(2026, 1, 1)
            )

        baseline = sum(
            weight.weight * ((index + 1) / 100)
            for index, weight in enumerate(result.weights)
        )
        east = next(row for row in result.weights if row.station_key == "east")
        self.assertAlmostEqual(result.rainfall[0].rain_in or 0, baseline)
        self.assertEqual(east.aggregated_observation_count, 0)
        self.assertIn("Ignored 1 exact duplicate", " ".join(logs.output))

    def test_conflicting_values_at_exact_timestamp_exclude_station(self) -> None:
        records = complete_records()
        records.append(
            RainfallRecord("Auburn", "west", "West", datetime(2026, 1, 1), 0.2)
        )
        with (
            patch(
                "mmc_watershed_data.spatial.load_station_points", return_value=POINTS
            ),
            patch(
                "mmc_watershed_data.spatial.load_watershed_boundary",
                return_value=BOUNDARY,
            ),
        ):
            result = analyze_spatial_rainfall(
                ROOT, records, date(2026, 1, 1), date(2026, 1, 1)
            )

        west = next(row for row in result.weights if row.station_key == "west")
        self.assertFalse(west.eligible)
        self.assertEqual(
            west.exclusion_reason, "conflicting duplicate timestamp values"
        )
        self.assertEqual(result.eligible_count, 3)

    def test_products_use_stable_names_and_schemas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                patch(
                    "mmc_watershed_data.spatial.load_station_points",
                    return_value=POINTS,
                ),
                patch(
                    "mmc_watershed_data.spatial.load_watershed_boundary",
                    return_value=BOUNDARY,
                ),
            ):
                result = create_spatial_products(
                    root,
                    complete_records(),
                    date(2026, 1, 1),
                    date(2026, 1, 1),
                )

            assert result.outputs is not None
            self.assertTrue(result.outputs.weights_csv.exists())
            self.assertTrue(result.outputs.polygons_geojson.exists())
            self.assertTrue(result.outputs.areal_rainfall_csv.exists())
            self.assertIn("analysis_crs", result.outputs.weights_csv.read_text())
            self.assertIn(ANALYSIS_CRS, result.outputs.weights_csv.read_text())
            self.assertIn(
                "aggregated_observation_count",
                result.outputs.weights_csv.read_text(),
            )
            self.assertIn("quality_flag", result.outputs.areal_rainfall_csv.read_text())

    def test_fewer_than_three_eligible_stations_fails(self) -> None:
        sparse = [
            record
            for record in complete_records()
            if record.station_key in {"west", "north"}
        ]
        with (
            patch(
                "mmc_watershed_data.spatial.load_station_points", return_value=POINTS
            ),
            patch(
                "mmc_watershed_data.spatial.load_watershed_boundary",
                return_value=BOUNDARY,
            ),
            self.assertRaisesRegex(SpatialAnalysisError, "at least three eligible"),
        ):
            analyze_spatial_rainfall(ROOT, sparse, date(2026, 1, 1), date(2026, 1, 1))


if __name__ == "__main__":
    unittest.main()
