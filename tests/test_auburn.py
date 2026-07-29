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

from mmc_watershed_data.auburn import collect_station
from mmc_watershed_data.models import Station
from mmc_watershed_data.validation import MmcDataValidationError


class AuburnTests(unittest.TestCase):
    def test_collect_station_writes_raw_and_processed_csv(self) -> None:
        station = Station("auburn", "Auburn", "lake_ogletree", "Lake Ogletree", "channel-id")
        payload = {
            "value": {
                "records": [
                    {"datum": {"valid": [[1767225600000, 0.12], [1767229200000, 0.34]]}}
                ]
            }
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir = root / "raw"
            processed_dir = root / "processed"
            with patch("mmc_watershed_data.auburn.post_json", return_value=payload):
                result = collect_station(
                    station,
                    date(2026, 1, 1),
                    date(2026, 1, 1),
                    raw_dir,
                    processed_dir,
                )

            self.assertEqual(result.raw_rows, 2)
            self.assertEqual(result.processed_rows, 2)
            self.assertTrue(result.raw_json_path.exists())
            self.assertTrue(result.raw_csv_path.exists())
            self.assertTrue(result.processed_path.exists())
            self.assertIn("windows", result.raw_json_path.read_text(encoding="utf-8"))
            self.assertIn("timestamp_ms,value", result.raw_csv_path.read_text(encoding="utf-8"))
            self.assertIn("Date_hour,RainIn", result.processed_path.read_text(encoding="utf-8"))

    def test_invalid_payload_keeps_raw_json_evidence(self) -> None:
        station = Station("auburn", "Auburn", "lake_ogletree", "Lake Ogletree", "channel-id")
        payload = {"value": {"records": [{"datum": {"valid": [["bad", 0.12]]}}]}}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir = root / "raw"
            processed_dir = root / "processed"
            with patch("mmc_watershed_data.auburn.post_json", return_value=payload), patch(
                "mmc_watershed_data.auburn.time_module.sleep"
            ):
                with self.assertRaises(MmcDataValidationError):
                    collect_station(
                        station,
                        date(2026, 1, 1),
                        date(2026, 1, 1),
                        raw_dir,
                        processed_dir,
                    )

            raw_path = raw_dir / "lake_ogletree_2026-01-01_to_2026-01-01_raw.json"
            self.assertTrue(raw_path.exists())
            self.assertIn("bad", raw_path.read_text(encoding="utf-8"))

    def test_request_failure_is_retried_and_reported(self) -> None:
        station = Station("auburn", "Auburn", "lake_ogletree", "Lake Ogletree", "channel-id")

        with tempfile.TemporaryDirectory() as tmp:
            with patch(
                "mmc_watershed_data.auburn.post_json",
                side_effect=RuntimeError("service unavailable"),
            ) as post, patch("mmc_watershed_data.auburn.time_module.sleep"):
                with self.assertRaisesRegex(RuntimeError, "service unavailable"):
                    collect_station(
                        station,
                        date(2026, 1, 1),
                        date(2026, 1, 1),
                        Path(tmp) / "raw",
                        Path(tmp) / "processed",
                    )

            self.assertEqual(post.call_count, 3)


if __name__ == "__main__":
    unittest.main()
