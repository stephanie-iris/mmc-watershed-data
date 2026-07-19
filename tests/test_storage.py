from datetime import datetime
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mmc_watershed_data.models import RainRecord
from mmc_watershed_data.storage import ensure_output_dirs, write_processed_csv


class StorageTests(unittest.TestCase):
    def test_ensure_output_dirs_creates_expected_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir, processed_dir = ensure_output_dirs(root)

            self.assertTrue(raw_dir.exists())
            self.assertTrue(processed_dir.exists())
            self.assertEqual(raw_dir.name, "raw")
            self.assertEqual(processed_dir.name, "processed")

    def test_write_processed_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            records = [
                RainRecord(datetime(2026, 1, 1, 0, 0), datetime(2025, 12, 31, 18, 0), 0.5),
            ]

            output = write_processed_csv(path, "output.csv", records, "Station")

            self.assertEqual(
                output.read_text(encoding="utf-8"),
                (
                    "timestamp_utc,timestamp_local,rain_in,station\n"
                    "2026-01-01T00:00:00,2025-12-31T18:00:00,0.5,Station\n"
                ),
            )


if __name__ == "__main__":
    unittest.main()
