from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mmc_watershed_data.models import Station
from mmc_watershed_data.opelika import collect_station
from mmc_watershed_data.validation import MmcDataValidationError


class OpelikaTests(unittest.TestCase):
    def test_collect_station_converts_cumulative_rain(self) -> None:
        station = Station("opelika", "Opelika", "sportsplex", "Sportsplex", "236")
        payload = [
            {"CreatedDT": "2026-01-01 00:00:00", "RainToday": 0.1, "Other": "x"},
            {"CreatedDT": "2026-01-01 01:00:00", "RainToday": 0.3, "Other": "y"},
            {"CreatedDT": "2026-01-01 02:00:00", "RainToday": 0.2, "Other": "z"},
        ]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir = root / "raw"
            processed_dir = root / "processed"
            with patch("mmc_watershed_data.opelika.get_json", return_value=payload):
                result = collect_station(
                    station,
                    date(2026, 1, 1),
                    date(2026, 1, 1),
                    raw_dir,
                    processed_dir,
                )

            self.assertEqual(result.raw_rows, 3)
            self.assertEqual(result.processed_rows, 3)
            self.assertTrue(result.raw_json_path.exists())
            self.assertTrue(result.raw_csv_path.exists())
            self.assertTrue(result.processed_path.exists())
            raw_text = result.raw_csv_path.read_text(encoding="utf-8")
            raw_json = result.raw_json_path.read_text(encoding="utf-8")
            processed_text = result.processed_path.read_text(encoding="utf-8")
            self.assertIn('"request"', raw_json)
            self.assertIn("CreatedDT,RainToday", raw_text)
            self.assertIn("Date_hour,RainIn", processed_text)
            self.assertIn("2026-01-01 02:00:00,0.2", processed_text)

    def test_invalid_payload_keeps_raw_json_evidence(self) -> None:
        station = Station("opelika", "Opelika", "sportsplex", "Sportsplex", "236")
        payload = [{"CreatedDT": "bad-date", "RainToday": 0.2}]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                patch("mmc_watershed_data.opelika.get_json", return_value=payload),
                patch("mmc_watershed_data.opelika.time_module.sleep"),
            ):
                with self.assertRaises(MmcDataValidationError):
                    collect_station(
                        station,
                        date(2026, 1, 1),
                        date(2026, 1, 1),
                        root / "raw",
                        root / "processed",
                    )

            raw_path = root / "raw" / "sportsplex_2026-01-01_to_2026-01-01_raw.json"
            self.assertTrue(raw_path.exists())
            self.assertIn("bad-date", raw_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
