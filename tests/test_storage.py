from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mmc_watershed_data.storage import ensure_output_dirs, write_csv


class StorageTests(unittest.TestCase):
    def test_ensure_output_dirs_creates_expected_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir, processed_dir = ensure_output_dirs(root, "auburn")

            self.assertTrue(raw_dir.exists())
            self.assertTrue(processed_dir.exists())
            self.assertEqual(raw_dir.parts[-2:], ("raw", "auburn"))
            self.assertEqual(processed_dir.parts[-2:], ("processed", "auburn"))

    def test_write_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.csv"
            output = write_csv(
                path,
                [{"name": "Lake Ogletree", "rain_in": 0.5}],
                ["name", "rain_in"],
            )

            self.assertEqual(
                output.read_text(encoding="utf-8"),
                "name,rain_in\nLake Ogletree,0.5\n",
            )


if __name__ == "__main__":
    unittest.main()
