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

from mmc_watershed_data.models import StationFailure, StationResult  # noqa: E402
from mmc_watershed_data.stations import AUBURN_STATIONS, OPELIKA_STATIONS  # noqa: E402
from mmc_watershed_data.workflow import (  # noqa: E402
    CollectionRequest,
    collect_rainfall,
)


class WorkflowTests(unittest.TestCase):
    def test_request_rejects_a_backwards_date_range(self) -> None:
        with self.assertRaisesRegex(ValueError, "start date"):
            CollectionRequest(date(2026, 1, 2), date(2026, 1, 1))

    def test_workflow_reuses_one_request_for_both_city_collectors(self) -> None:
        request = CollectionRequest(date(2026, 1, 1), date(2026, 1, 3))
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch(
                    "mmc_watershed_data.workflow.collect_auburn",
                    return_value=([], []),
                ) as auburn,
                patch(
                    "mmc_watershed_data.workflow.collect_opelika",
                    return_value=([], []),
                ) as opelika,
            ):
                result = collect_rainfall(request, Path(tmp))

        auburn.assert_called_once_with(date(2026, 1, 1), date(2026, 1, 3), Path(tmp))
        opelika.assert_called_once_with(date(2026, 1, 1), date(2026, 1, 3), Path(tmp))
        self.assertEqual(result.request, request)
        self.assertEqual(result.station_results, ())
        self.assertEqual(result.station_failures, ())


if __name__ == "__main__":
    unittest.main()
