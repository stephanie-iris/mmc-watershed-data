# MMC Watershed Data

MMC Watershed Data collects, validates, and processes rainfall observations
from Auburn and Opelika stations near the **Moores Mill Creek (MMC) watershed**.
It also derives a Thiessen area-weighted watershed rainfall time series for
hydrologic modeling.

## What You Can Produce

- Raw JSON evidence and readable raw CSV extracts for every station.
- Validated, standardized station rainfall CSV files.
- Thiessen station weights and clipped watershed polygons.
- A model-ready watershed rainfall time series.
- Interactive rainfall and event views in a Streamlit dashboard.
- A reproducible PDF report based on the latest saved collection.

## Fastest Path

```bash
git clone https://github.com/stephanie-iris/mmc-watershed-data.git
cd mmc-watershed-data
uv sync --locked
uv run mmc --start-date 2026-01-01 --end-date 2026-01-08
uv run streamlit run src/mmc_watershed_data/dashboard.py
```

The public APIs do not require credentials. Start with the
[installation and command guide](getting-started.md), then use the
[data dictionary](data-dictionary.md) to understand the generated fields.

## Documentation Map

| Need | Documentation |
| --- | --- |
| Install, collect data, and launch the dashboard | [Getting Started](getting-started.md) |
| Understand fields, units, provenance, and transformations | [Data Dictionary](data-dictionary.md) |
| Read or rebuild the analysis artifact | [Reproducible Report](report.md) |
| Reuse loading, validation, and spatial behavior | [Python Reference](reference/collection.md) |

The repository [README](https://github.com/stephanie-iris/mmc-watershed-data#readme)
is the detailed user source of truth. Source docstrings define code-level
contracts, and the report source remains authoritative for report behavior.
