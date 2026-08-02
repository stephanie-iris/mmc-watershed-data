"""Command-line interface for repeatable Auburn and Opelika collections."""

from __future__ import annotations

import argparse
from datetime import date
import logging
from pathlib import Path

from . import __version__
from .config import project_root
from .models import StationFailure, StationResult
from .logging_config import LoggingSetupError, configure_logging
from .workflow import CollectionRequest, collect_rainfall


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse date-range, logging, and version options for ``mmc``."""

    parser = argparse.ArgumentParser(
        description="Collect Auburn and Opelika rainfall data for whole calendar days.",
        epilog=(
            "Example: mmc --start-date 2026-01-01 --end-date 2026-01-08\n"
            "Outputs are written under data/raw/ and data/processed/."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"mmc {__version__}")
    parser.add_argument(
        "--start-date", required=True, help="First whole day, in YYYY-MM-DD format."
    )
    parser.add_argument(
        "--end-date", required=True, help="Last whole day, in YYYY-MM-DD format."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Write operational INFO messages to the terminal.",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        metavar="PATH",
        help="Write detailed DEBUG logs to PATH.",
    )
    return parser.parse_args()


def parse_date(value: str) -> date:
    """Parse an ISO date or let the CLI report an invalid date."""

    return date.fromisoformat(value)


def print_banner(start_date: date, end_date: date) -> None:
    """Print the selected period and project output locations."""

    print("========================================")
    print("MMC Watershed Data")
    print("========================================")
    print(f"Period : {start_date.isoformat()} to {end_date.isoformat()}")
    print("Cities : Auburn, Opelika")
    print("Output : data/raw/ and data/processed/")
    print()


def print_city_results(
    city: str,
    results: list[StationResult],
    failures: list[StationFailure],
) -> None:
    """Print successful and failed station outputs for one city."""

    print(city)
    print("-" * len(city))
    for index, result in enumerate(results, start=1):
        print(f"[{index}/{len(results)}] {result.station.name}")
        print(f"    raw json   -> {result.raw_json_path}")
        print(f"    raw csv    -> {result.raw_csv_path}")
        print(f"    processed  -> {result.processed_path}")
        print(
            f"    rows       -> raw {result.raw_rows}, processed {result.processed_rows}"
        )
    for failure in failures:
        print(f"  ! {failure.station.name}: {failure.error}")
    print()


def print_summary(
    all_results: list[StationResult],
    all_failures: list[StationFailure],
) -> None:
    """Print aggregate row and station counts after collection."""

    raw_total = sum(result.raw_rows for result in all_results)
    processed_total = sum(result.processed_rows for result in all_results)
    print("========================================")
    print("Download complete")
    print("========================================")
    print(f"Stations processed : {len(all_results)}")
    print(f"Raw rows           : {raw_total}")
    print(f"Processed rows     : {processed_total}")
    print(f"Stations failed    : {len(all_failures)}")


def main() -> int:
    """Run one complete date-range collection and return a process status."""

    args = parse_args()
    try:
        configure_logging(verbose=args.verbose, log_file=args.log_file)
    except LoggingSetupError as exc:
        raise SystemExit(str(exc)) from exc

    try:
        request = CollectionRequest(
            start_date=parse_date(args.start_date),
            end_date=parse_date(args.end_date),
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    root = project_root()
    print_banner(request.start_date, request.end_date)
    logger.info(
        "Starting MMC collection for %s through %s.",
        request.start_date,
        request.end_date,
    )

    collection = collect_rainfall(request, root)
    auburn_results = [
        result
        for result in collection.station_results
        if result.station.city == "Auburn"
    ]
    auburn_failures = [
        failure
        for failure in collection.station_failures
        if failure.station.city == "Auburn"
    ]
    print_city_results("Auburn", auburn_results, auburn_failures)

    opelika_results = [
        result
        for result in collection.station_results
        if result.station.city == "Opelika"
    ]
    opelika_failures = [
        failure
        for failure in collection.station_failures
        if failure.station.city == "Opelika"
    ]
    print_city_results("Opelika", opelika_results, opelika_failures)

    print_summary(
        list(collection.station_results),
        list(collection.station_failures),
    )
    logger.info("MMC collection finished.")
    return 0
