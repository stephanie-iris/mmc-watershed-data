# MMC Watershed Data

MMC stands for Moores Mill Creek. This project is a small `uv`-managed Python command-line tool that collects precipitation data from the City of Auburn and the City of Opelika.

Current version: `0.2.0`

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

## What We Will Build

The second sprint expands the first version into a multi-station rainfall downloader for Auburn and Opelika, while keeping the command simple: the user only chooses the time period.

## Setup

1. Create a virtual environment with `uv`.
2. Install dependencies with `uv sync`.

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
