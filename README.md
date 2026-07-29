# MMC Watershed Data

MMC stands for Moores Mill Creek. This project is a small `uv`-managed Python command-line tool that collects precipitation data from the City of Auburn and the City of Opelika. The collection workflow validates external responses before processing them and can provide optional diagnostic logs when troubleshooting.

Current version: `0.3.0`

## API

The tool uses two public data sources:

- Auburn LI-COR dashboard page: [https://www.licor.cloud/dashboards/52f7495a-bd9c-48ff-a568-20431bc95b60/true](https://www.licor.cloud/dashboards/52f7495a-bd9c-48ff-a568-20431bc95b60/true)
- Auburn endpoint: `https://www.licor.cloud/api/v2/timeseriesdata`
- Opelika dashboard page: [https://360.thormobile.net/opelika-al/archive/](https://360.thormobile.net/opelika-al/archive/)
- Opelika ThorArchive endpoint: `https://360.thormobile.net/thorcloud/api/weatherpacketsbyinterval`

## Example Request

The command below downloads a date range using whole days only. The tool fetches every available Auburn station and every available Opelika station for that period:

```bash
uv run mmc --start-date 2026-01-01 --end-date 2026-01-08
```

## What the Response Contains

The Auburn feed returns 10-minute rainfall values from the LI-COR dashboard. The Opelika feed returns daily station records with a cumulative `RainToday` field. The tool saves:

- raw JSON evidence files in `data/raw/auburn/` and `data/raw/opelika/`
- raw CSV files in `data/raw/auburn/` and `data/raw/opelika/`
- processed CSV files in `data/processed/auburn/` and `data/processed/opelika/`

Each station gets its own raw JSON, raw CSV, and processed CSV so the output is easy to inspect and compare with the source scripts.

## How The Data Is Handled

### Auburn

- Raw data comes back from the LI-COR API as JSON.
- The tool saves that JSON as the evidence copy in `data/raw/auburn/`.
- The tool also writes a raw CSV extract for easier reading.
- The processed CSV converts epoch milliseconds into a fixed UTC-6 timestamp.
- The rainfall value is kept as the station rain amount for that timestamp.

### Opelika

- Raw data comes back from the ThorArchive API as JSON.
- The tool sends one request per station for the full selected date range.
- The tool saves that JSON as the evidence copy in `data/raw/opelika/`.
- The tool also writes a raw CSV extract for easier reading.
- The processed CSV converts the cumulative `RainToday` field into interval rainfall values.
- The processed output keeps the rainfall usable for later analysis.

## Reliability and Diagnostics

The project keeps external data separate from trusted internal records:

```text
API response -> raw JSON evidence -> Pydantic validation -> processed records
```

- Pydantic validates the Auburn fields used for timestamps and rainfall values.
- Pydantic validates the Opelika `CreatedDT` and `RainToday` fields before the cumulative value is converted into interval rainfall.
- Raw JSON is written before processed-data validation, so an invalid response can still be inspected as evidence.
- Invalid data is reported with a source and field location instead of an internal validation traceback.

The tests are designed to run offline. Files under `tests/fixtures/` are small,
stable examples of valid and invalid API responses. Mocks replace network calls
so tests can control successful responses, HTTP or connection failures, and
retry behavior without contacting Auburn or Opelika.

The CLI is quiet by default. Use `--verbose` for operational messages in the
terminal or `--log-file` for detailed `DEBUG` logs:

```bash
uv run mmc --start-date 2026-01-01 --end-date 2026-01-08 --verbose
uv run mmc --start-date 2026-01-01 --end-date 2026-01-08 --log-file logs/mmc.log
```

Console logs use `INFO` for milestones. File logs also include `DEBUG` details.
The logging configuration does not record API keys or other credentials.

The shared workflow in `src/mmc_watershed_data/workflow.py` owns the common
date request and combines Auburn and Opelika results. This lets the command
line tool and the future Streamlit dashboard reuse the same collection,
validation, storage, and failure behavior.

## What We Will Build

The current implementation is the second-sprint multi-station rainfall downloader plus the Sprint 3 reliability layer. The command remains simple: the user only chooses the time period, while the project handles station selection, validation, storage, and diagnostics.

## Setup

1. Install `uv` if it is not already available.
2. Synchronize the project environment with `uv sync`. This installs Pydantic and the project itself.

## Run

```bash
uv run mmc --start-date 2026-01-01 --end-date 2026-01-08
```

## Stations

### Auburn

- WRM Office
- Lake Ogletree
- Northside WPCF
- NW Auburn Tank
- HC Morgan WPCF

### Opelika

- Sportsplex
- Floral Park
- West Ridge Park
- Covington Center

## Development Checks

Run these when you want to make sure the project is still healthy:

```bash
uv run python -m unittest discover -s tests
uv build
```

Tests use fixtures and mocks, so the development checks do not call the live
rainfall APIs.
