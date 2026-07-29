from __future__ import annotations

import logging
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mmc_watershed_data.logging_config import configure_logging  # noqa: E402


class LoggingConfigTests(unittest.TestCase):
    def tearDown(self) -> None:
        configure_logging(verbose=False, log_file=None)

    def test_verbose_console_and_file_have_different_detail_levels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "logs" / "mmc.log"
            stderr = StringIO()
            logger = logging.getLogger("mmc_watershed_data.test")

            with redirect_stderr(stderr):
                configure_logging(verbose=True, log_file=log_path)
                logger.debug("file diagnostic")
                logger.info("console milestone")

            self.assertIn("console milestone", stderr.getvalue())
            self.assertNotIn("file diagnostic", stderr.getvalue())
            file_text = log_path.read_text(encoding="utf-8")
            self.assertIn("file diagnostic", file_text)
            self.assertIn("console milestone", file_text)
            configure_logging(verbose=False, log_file=None)

    def test_logs_do_not_include_the_api_key_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "mmc.log"
            secret = "secret-test-key"
            logger = logging.getLogger("mmc_watershed_data.test")

            configure_logging(verbose=False, log_file=log_path)
            logger.info("request configured with a key")

            self.assertNotIn(secret, log_path.read_text(encoding="utf-8"))
            configure_logging(verbose=False, log_file=None)


if __name__ == "__main__":
    unittest.main()
