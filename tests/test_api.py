from __future__ import annotations

from contextlib import redirect_stdout
from datetime import date
from io import StringIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mmc_watershed_data import cli
from mmc_watershed_data.api import chunk_dates, date_range, first_seen_fieldnames


class ApiTests(unittest.TestCase):
    def test_chunk_dates_splits_range(self) -> None:
        windows = chunk_dates(date(2026, 1, 1), date(2026, 1, 10), 7)

        self.assertEqual(
            windows,
            [
                (date(2026, 1, 1), date(2026, 1, 7)),
                (date(2026, 1, 8), date(2026, 1, 10)),
            ],
        )

    def test_date_range_includes_both_ends(self) -> None:
        self.assertEqual(
            date_range(date(2026, 1, 1), date(2026, 1, 3)),
            [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)],
        )

    def test_first_seen_fieldnames_preserves_order(self) -> None:
        rows = [
            {"b": 2, "a": 1},
            {"a": 3, "c": 4},
        ]

        self.assertEqual(first_seen_fieldnames(rows), ["b", "a", "c"])

    def test_version_flag_prints_version(self) -> None:
        buffer = StringIO()
        with patch.object(sys, "argv", ["mmc", "--version"]), redirect_stdout(buffer):
            with self.assertRaises(SystemExit) as exc:
                cli.parse_args()

        self.assertEqual(exc.exception.code, 0)
        self.assertEqual(buffer.getvalue().strip(), "mmc 0.6.0")


if __name__ == "__main__":
    unittest.main()
