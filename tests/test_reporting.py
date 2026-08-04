"""Tests for automatic report-period and processed-file selection."""

from datetime import date
from pathlib import Path
import shutil
import tempfile
import unittest

from mmc_watershed_data.reporting import load_report_dataset, parse_optional_date


ROOT = Path(__file__).resolve().parents[1]
CSV_HEADER = "city,station_key,station_name,Date_hour,RainIn\n"


class ReportingTests(unittest.TestCase):
    """Verify that a report follows the user's saved collection period."""

    def test_explicit_period_selects_all_station_files_in_that_collection(self) -> None:
        """A requested range loads every matching processed station CSV."""

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            processed = root / "data" / "processed"
            processed.mkdir(parents=True)
            (processed / "station_a_2026-01-01_to_2026-01-08_processed.csv").write_text(
                CSV_HEADER + "Auburn,a,Station A,2026-01-02 00:00:00,0.20\n",
                encoding="utf-8",
            )
            (processed / "station_b_2026-01-01_to_2026-01-08_processed.csv").write_text(
                CSV_HEADER + "Opelika,b,Station B,2026-01-03 00:00:00,0.30\n",
                encoding="utf-8",
            )

            dataset = load_report_dataset(
                root,
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 8),
            )

        self.assertEqual(len(dataset.source_files), 2)
        self.assertEqual(len(dataset.records), 2)
        self.assertEqual(dataset.start_date, date(2026, 1, 1))
        self.assertEqual(dataset.end_date, date(2026, 1, 8))

    def test_latest_saved_range_is_selected_automatically(self) -> None:
        """Without dates, the newest saved collection controls the report."""

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            processed = root / "data" / "processed"
            processed.mkdir(parents=True)
            older = processed / "station_2026-01-01_to_2026-01-02_processed.csv"
            newer = processed / "station_2026-02-01_to_2026-02-02_processed.csv"
            older.write_text(
                CSV_HEADER + "Auburn,a,Station A,2026-01-01 00:00:00,0.10\n",
                encoding="utf-8",
            )
            newer.write_text(
                CSV_HEADER + "Auburn,a,Station A,2026-02-01 00:00:00,0.40\n",
                encoding="utf-8",
            )
            older.touch()
            newer.touch()

            dataset = load_report_dataset(root)

        self.assertEqual(dataset.start_date, date(2026, 2, 1))
        self.assertEqual(dataset.end_date, date(2026, 2, 2))
        self.assertEqual(dataset.records[0].rain_in, 0.40)

    def test_optional_date_reports_the_variable_name_on_failure(self) -> None:
        """Invalid date configuration produces an actionable message."""

        with self.assertRaisesRegex(ValueError, "MMC_REPORT_START_DATE"):
            parse_optional_date("January 1", "MMC_REPORT_START_DATE")

    def test_bundled_dataset_rebuilds_report_without_generated_data(self) -> None:
        """A clean project can load the committed offline report fallback."""

        bundled_name = "mmc_report_2026-07-01_to_2026-08-01_processed.csv"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            report_data = root / "reports" / "data"
            report_data.mkdir(parents=True)
            shutil.copyfile(
                ROOT / "reports" / "data" / bundled_name, report_data / bundled_name
            )

            dataset = load_report_dataset(root)

        self.assertEqual(dataset.selection, "bundled reproducible report dataset")
        self.assertEqual(dataset.start_date, date(2026, 7, 1))
        self.assertEqual(dataset.end_date, date(2026, 8, 1))
        self.assertGreater(len(dataset.records), 0)


if __name__ == "__main__":
    unittest.main()
