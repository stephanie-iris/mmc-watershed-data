from __future__ import annotations

import argparse
from datetime import date

from . import __version__
from .auburn import collect_all as collect_auburn
from .config import project_root
from .models import StationFailure, StationResult
from .opelika import collect_all as collect_opelika


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect Auburn and Opelika rainfall data.")
    parser.add_argument("--version", action="version", version=f"mmc {__version__}")
    parser.add_argument("--start-date", required=True, help="Start date in YYYY-MM-DD format.")
    parser.add_argument("--end-date", required=True, help="End date in YYYY-MM-DD format.")
    return parser.parse_args()


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def print_banner(start_date: date, end_date: date) -> None:
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
    print(city)
    print("-" * len(city))
    for index, result in enumerate(results, start=1):
        print(f"[{index}/{len(results)}] {result.station.name}")
        print(f"    raw json   -> {result.raw_json_path}")
        print(f"    raw csv    -> {result.raw_csv_path}")
        print(f"    processed  -> {result.processed_path}")
        print(f"    rows       -> raw {result.raw_rows}, processed {result.processed_rows}")
    for failure in failures:
        print(f"  ! {failure.station.name}: {failure.error}")
    print()


def print_summary(
    all_results: list[StationResult],
    all_failures: list[StationFailure],
) -> None:
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
    args = parse_args()
    start_date = parse_date(args.start_date)
    end_date = parse_date(args.end_date)
    if start_date > end_date:
        raise SystemExit("--start-date must be earlier than or equal to --end-date")

    root = project_root()
    print_banner(start_date, end_date)

    auburn_results, auburn_failures = collect_auburn(start_date, end_date, root)
    print_city_results("Auburn", auburn_results, auburn_failures)

    opelika_results, opelika_failures = collect_opelika(start_date, end_date, root)
    print_city_results("Opelika", opelika_results, opelika_failures)

    print_summary(auburn_results + opelika_results, auburn_failures + opelika_failures)
    return 0
