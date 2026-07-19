# MMC Watershed Data

This project is a small `uv`-managed Python command-line tool that collects precipitation data for the City of Auburn from the Ogletree station.

## API

The tool uses the LI-COR cloud timeseries endpoint shown in the example script and on this dashboard page:

- Example source in this repo: [examples/CityofAuburnData_LakeOgeltree_Self_Copy_R03.py](/C:/Users/fanei/insy7970/mmc-watershed-data/examples/CityofAuburnData_LakeOgeltree_Self_Copy_R03.py)
- LI-COR dashboard page: [https://www.licor.cloud/dashboards/52f7495a-bd9c-48ff-a568-20431bc95b60/true](https://www.licor.cloud/dashboards/52f7495a-bd9c-48ff-a568-20431bc95b60/true)
- Endpoint: `https://www.licor.cloud/api/v2/timeseriesdata`

## Example Request

The command below downloads a short range:

```bash
uv run mmc-watershed-data --start 2026-01-01T00:00:00 --end 2026-01-08T00:00:00
```

## What the Response Contains

The API response contains time-series records for the Ogletree station. The tool extracts timestamped rainfall values, saves the raw JSON response as evidence in `data/raw/`, and writes a processed CSV for later use in `data/processed/`.

## What We Will Build

The first version focuses on one command, one data source, raw evidence capture, and a cleaned processed dataset that someone else can reproduce from the README alone.

## Setup

1. Create a virtual environment with `uv`.
2. Copy `.env.example` to `.env` and add `LICOR_API_KEY` if needed.
3. Install dependencies with `uv sync`.

## Run

```bash
uv run mmc-watershed-data --start 2026-01-01T00:00:00 --end 2026-01-08T00:00:00
```

## Development Checks

Run these when you want to make sure the project is still healthy:

```bash
uv run python -m pytest
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv build
```
