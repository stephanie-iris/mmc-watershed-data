from datetime import datetime
from pathlib import Path
import sys
from io import StringIO
from contextlib import redirect_stdout
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mmc_watershed_data import cli
from mmc_watershed_data.api import build_body, build_windows, dedupe_and_sort, fetch_window
from mmc_watershed_data.config import AppConfig
from mmc_watershed_data.models import DownloadWindow, RainRecord


class ApiTests(unittest.TestCase):
    def test_build_windows_splits_range(self) -> None:
        windows = build_windows(
            datetime(2026, 1, 1, 0, 0),
            datetime(2026, 1, 10, 0, 0),
            7,
        )

        self.assertEqual(
            windows,
            [
                DownloadWindow(datetime(2026, 1, 1, 0, 0), datetime(2026, 1, 8, 0, 0)),
                DownloadWindow(datetime(2026, 1, 8, 0, 0), datetime(2026, 1, 10, 0, 0)),
            ],
        )

    def test_build_body_uses_config_and_window(self) -> None:
        config = AppConfig()
        window = DownloadWindow(datetime(2026, 1, 1, 0, 0), datetime(2026, 1, 2, 0, 0))

        body = build_body(config, window)

        self.assertEqual(body["dashboardUUID"], config.dashboard_uuid)
        self.assertEqual(body["channels"][0]["channelUUID"], config.channel_uuid)
        self.assertEqual(body["time"]["absolute"]["from"], 1767225600000)
        self.assertEqual(body["time"]["absolute"]["to"], 1767312000000)

    def test_dedupe_and_sort_keeps_latest_by_timestamp(self) -> None:
        records = [
            RainRecord(datetime(2026, 1, 2, 0, 0), datetime(2026, 1, 1, 18, 0), 1.0),
            RainRecord(datetime(2026, 1, 1, 0, 0), datetime(2025, 12, 31, 18, 0), 2.0),
            RainRecord(datetime(2026, 1, 2, 0, 0), datetime(2026, 1, 1, 18, 0), 3.0),
        ]

        output = dedupe_and_sort(records)

        self.assertEqual(
            output,
            [
                RainRecord(datetime(2026, 1, 1, 0, 0), datetime(2025, 12, 31, 18, 0), 2.0),
                RainRecord(datetime(2026, 1, 2, 0, 0), datetime(2026, 1, 1, 18, 0), 3.0),
            ],
        )

    def test_fetch_window_parses_records(self) -> None:
        def fake_post_json(url: str, payload: dict, headers: dict, timeout: int) -> dict:
            self.assertEqual(url, AppConfig().api_url)
            self.assertEqual(timeout, 90)
            return {
                "value": {
                    "records": [
                        {"datum": {"valid": [[1767225600000, 0.12], [1767229200000, 0.34]]}}
                    ]
                }
            }

        from mmc_watershed_data import api as api_module

        original = api_module.post_json
        api_module.post_json = fake_post_json
        try:
            config = AppConfig(max_retries=1)
            window = DownloadWindow(
                datetime(2026, 1, 1, 0, 0),
                datetime(2026, 1, 2, 0, 0),
            )

            records, payload = fetch_window(config, window)
        finally:
            api_module.post_json = original

        self.assertEqual(payload["value"]["records"][0]["datum"]["valid"][0][1], 0.12)
        self.assertEqual(records[0].rain_in, 0.12)
        self.assertEqual(records[1].timestamp_local, datetime(2025, 12, 31, 19, 0))

    def test_version_flag_prints_version(self) -> None:
        buffer = StringIO()
        with patch.object(sys, "argv", ["mmc", "--version"]), redirect_stdout(buffer):
            with self.assertRaises(SystemExit) as exc:
                cli.parse_args()

        self.assertEqual(exc.exception.code, 0)
        self.assertEqual(buffer.getvalue().strip(), "mmc 0.1.0")


if __name__ == "__main__":
    unittest.main()
