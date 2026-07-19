# MMC Watershed Data

MMC stands for Moores Mill Creek. This project is a small `uv`-managed Python command-line tool that collects precipitation data for the City of Auburn from the Ogletree station.

## API

The tool uses the LI-COR cloud timeseries endpoint shown on this dashboard page:

- LI-COR dashboard page: [https://www.licor.cloud/dashboards/52f7495a-bd9c-48ff-a568-20431bc95b60/true](https://www.licor.cloud/dashboards/52f7495a-bd9c-48ff-a568-20431bc95b60/true)
- Endpoint: `https://www.licor.cloud/api/v2/timeseriesdata`

## Example Request

The command below downloads a date range using whole days only:

```bash
uv run mmc --start-date 2026-01-01 --end-date 2026-01-08
```

## What the Response Contains

The API response contains time-series records for the Ogletree station. The tool extracts timestamped rainfall values, saves the raw JSON response as evidence in `data/raw/`, and writes a processed CSV for later use in `data/processed/`.

## What We Will Build

The first version focuses on one command, one data source, raw evidence capture, and a cleaned processed dataset that someone else can reproduce from the README alone.

## Setup

1. Create a virtual environment with `uv`.
2. Install dependencies with `uv sync`.

## Run

```bash
uv run mmc --start-date 2026-01-01 --end-date 2026-01-08
```

## Development Checks

Run these when you want to make sure the project is still healthy:

```bash
uv run python -m unittest discover -s tests
uv build
```
