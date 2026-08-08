# Getting Started

## Requirements

- Python 3.11 or newer.
- [`uv`](https://docs.astral.sh/uv/).
- Internet access when collecting live rainfall data.
- No API key or `.env` file.

## Install

```bash
git clone https://github.com/stephanie-iris/mmc-watershed-data.git
cd mmc-watershed-data
uv sync --locked
```

## Collect A Period

The command accepts inclusive calendar dates in `YYYY-MM-DD` format and
collects every configured Auburn and Opelika station:

```bash
uv run mmc --start-date 2026-01-01 --end-date 2026-01-08
```

Use diagnostic logging when investigating a provider or station failure:

```bash
uv run mmc --start-date 2026-01-01 --end-date 2026-01-08 --verbose --log-file logs/mmc.log
```

## Open The Dashboard

```bash
uv run streamlit run src/mmc_watershed_data/dashboard.py
```

The dashboard can collect a new period or load processed CSVs already saved
under `data/processed/`. Its three pages cover station rainfall, rainfall
events, and Thiessen-weighted watershed rainfall.

## Outputs

```text
data/raw/auburn/         Auburn JSON evidence and raw CSV extracts
data/raw/opelika/        Opelika JSON evidence and raw CSV extracts
data/processed/auburn/   validated Auburn station CSVs
data/processed/opelika/  validated Opelika station CSVs
data/processed/spatial/  weights, polygons, and watershed rainfall
```

Generated root-level `data/` and `logs/` directories are ignored by Git. The
report fallback under `reports/data/` is intentionally tracked so the report
can be rebuilt without a live API request.

## Common Failures

**Invalid date range:** use `YYYY-MM-DD` and ensure the start is not after the
end.

**One station returns HTTP 500:** retry a shorter period and inspect verbose or
file logs. Other stations can still finish successfully.

**No spatial products:** inspect the printed warning. Thiessen analysis needs
valid watershed geometry, distinct station coordinates, and at least three
eligible stations with sufficient temporal coverage.

For complete behavior, report commands, testing, and troubleshooting, read the
[project README](https://github.com/stephanie-iris/mmc-watershed-data#readme).
