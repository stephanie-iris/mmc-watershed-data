from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mmc_watershed_data.analysis import (  # noqa: E402
    RainfallRecord,
    detect_events,
    load_rainfall_records,
)


class AnalysisTests(unittest.TestCase):
    def test_load_rainfall_records_reads_processed_csv(self) -> None:
        path = ROOT / "tests" / "fixtures" / "processed-rainfall-sample.csv"

        records = load_rainfall_records(path)

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].station_name, "Lake Ogletree")
        self.assertAlmostEqual(records[1].rain_in, 0.25)

    def test_detect_events_merges_station_observations_and_tracks_stations(self) -> None:
        start = datetime(2026, 1, 1, 0, 0)
        records = [
            RainfallRecord("Auburn", "a", "Auburn A", start, 0.1),
            RainfallRecord("Auburn", "a", "Auburn A", start + timedelta(minutes=10), 0.2),
            RainfallRecord("Opelika", "b", "Opelika B", start + timedelta(minutes=30), 0.3),
            RainfallRecord("Auburn", "a", "Auburn A", start + timedelta(hours=3), 0.4),
        ]

        events = detect_events(records)

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].station_names, ("Auburn A", "Opelika B"))
        self.assertAlmostEqual(events[0].total_rain_in, 0.6)
        self.assertEqual(events[0].duration_minutes, 30)
        self.assertEqual(events[1].station_names, ("Auburn A",))

    def test_zero_rainfall_is_not_an_event(self) -> None:
        records = [
            RainfallRecord(
                "Auburn",
                "a",
                "Auburn A",
                datetime(2026, 1, 1),
                0.0,
            )
        ]

        self.assertEqual(detect_events(records), [])


if __name__ == "__main__":
    unittest.main()
