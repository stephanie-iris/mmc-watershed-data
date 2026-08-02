"""Allow the package to run as ``python -m mmc_watershed_data``."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
