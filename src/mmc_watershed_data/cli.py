from __future__ import annotations

import argparse
from datetime import date, datetime, time
from pathlib import Path

from .api import build_windows, dedupe_and_sort, fetch_window, save_raw_payload
from .config import AppConfig, project_root
from . import __version__
from .storage import ensure_output_dirs, write_processed_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect Auburn Ogletree rainfall data.")
    parser.add_argument(
        "--version",
        action="version",
        version=f"mmc {__version__}",
    )
    parser.add_argument("--start-date", required=True, help="Start date in YYYY-MM-DD format.")
    parser.add_argument("--end-date", required=True, help="End date in YYYY-MM-DD format.")
    return parser.parse_args()


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def print_banner(station: str, start_date: date, end_date: date) -> None:
    print("========================================")
    print("MMC Watershed Data")
    print("========================================")
    print(f"Station : {station}")
    print(f"Dates   : {start_date.isoformat()} to {end_date.isoformat()}")
    print("Output  : data/raw/ and data/processed/")
    print()


def print_window_status(index: int, total: int, window_start: date) -> None:
    print(f"[{index}/{total}] Fetching {window_start.isoformat()} ...")


def print_final_summary(record_count: int, raw_count: int, raw_dir: Path, processed_path: Path) -> None:
    print()
    print("========================================")
    print("Download complete")
    print("========================================")
    print(f"Raw files      : {raw_count}")
    print(f"Processed rows : {record_count}")
    print(f"Raw folder     : {raw_dir}")
    print(f"Processed file : {processed_path}")


def main() -> int:
    args = parse_args()
    start_date = parse_date(args.start_date)
    end_date = parse_date(args.end_date)
    start = datetime.combine(start_date, time.min)
    end = datetime.combine(end_date, time.min)
    if start >= end:
        raise SystemExit("--start-date must be earlier than --end-date")

    config = AppConfig()
    root = project_root()
    raw_dir, processed_dir = ensure_output_dirs(root)

    windows = build_windows(start, end, config.chunk_days)
    collected = []
    raw_paths = []

    print_banner(config.station, start_date, end_date)

    for index, window in enumerate(windows, start=1):
        print_window_status(index, len(windows), window.start.date())
        rows, payload = fetch_window(config, window)
        raw_path = save_raw_payload(raw_dir, window, payload)
        raw_paths.append(raw_path)
        collected.extend(rows)
        print(f"    saved raw evidence -> {raw_path}")

    records = dedupe_and_sort(collected)
    processed_name = f"ogletree_{start_date.isoformat()}_to_{end_date.isoformat()}_processed.csv"
    processed_path = write_processed_csv(processed_dir, processed_name, records, config.station)

    print_final_summary(len(records), len(raw_paths), raw_dir, processed_path)
    return 0
