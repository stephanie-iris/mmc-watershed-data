"""MMC Watershed Data package."""

import logging

__version__ = "0.3.0"


# Library imports stay quiet unless the CLI or dashboard configures handlers.
logging.getLogger(__name__).addHandler(logging.NullHandler())
