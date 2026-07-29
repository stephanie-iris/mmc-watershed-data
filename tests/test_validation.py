from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mmc_watershed_data.validation import (  # noqa: E402
    MmcDataValidationError,
    validate_auburn_payload,
    validate_opelika_records,
)


class ValidationTests(unittest.TestCase):
    def test_auburn_validation_accepts_the_fields_used_by_processing(self) -> None:
        payload = {
            "value": {
                "records": [
                    {"datum": {"valid": [[1767225600000, 0.12]]}},
                ],
            },
        }

        validated = validate_auburn_payload(payload)

        self.assertEqual(validated.value.records[0].datum.valid[0], (1767225600000, 0.12))

    def test_auburn_validation_reports_the_invalid_field(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "auburn-invalid.json"

        with self.assertRaisesRegex(MmcDataValidationError, "valid.0.0"):
            validate_auburn_payload(json.loads(fixture.read_text(encoding="utf-8")))

    def test_opelika_validation_accepts_and_parses_source_fields(self) -> None:
        validated = validate_opelika_records(
            [{"CreatedDT": "2026-01-01 00:00:00", "RainToday": 0.2}]
        )

        self.assertEqual(validated[0].created_dt.year, 2026)
        self.assertEqual(validated[0].rain_today, 0.2)

    def test_opelika_validation_reports_invalid_datetime(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "opelika-invalid.json"

        with self.assertRaisesRegex(MmcDataValidationError, "CreatedDT"):
            validate_opelika_records(json.loads(fixture.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
