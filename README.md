# MMC Watershed Data

MMC means **Moores Mill Creek**. This project is for students, watershed
analysts, and developers who need a repeatable way to collect and inspect
rainfall observations from stations in Auburn and Opelika, Alabama.

The project provides a `uv` command-line tool named `mmc`, a Streamlit
dashboard, validated raw-to-processed outputs, and a reproducible Quarto report.

Current version: `0.7.0`

## Fastest Working Result

Requirements: Python 3.11 or newer, `uv`, and an internet connection for API
collection. The public Auburn and Opelika endpoints used by this project do not
require an API key or a `.env` file.

```bash
git clone https://github.com/stephanie-iris/mmc-watershed-data.git
cd mmc-watershed-data
uv sync
uv run mmc --start-date 2026-01-01 --end-date 2026-01-08
```

The command accepts whole calendar days only. It requests every configured
Auburn and Opelika station and writes one set of raw and processed files per
station.

## Data Sources

- Auburn dashboard: [LI-COR dashboard](https://www.licor.cloud/dashboards/52f7495a-bd9c-48ff-a568-20431bc95b60/true)
- Auburn endpoint: `https://www.licor.cloud/api/v2/timeseriesdata`
- Opelika dashboard: [ThorArchive](https://360.thormobile.net/opelika-al/archive/)
- Opelika endpoint: `https://360.thormobile.net/thorcloud/api/weatherpacketsbyinterval`

## Inputs and Outputs

The input is a required start and end date in `YYYY-MM-DD` format:

```bash
uv run mmc --start-date 2026-01-01 --end-date 2026-01-08
```

The command creates these run-specific artifacts:

```text
data/raw/auburn/         raw JSON evidence and readable raw CSV extracts
data/raw/opelika/        raw JSON evidence and readable raw CSV extracts
data/processed/auburn/  processed CSV files used by analysis
data/processed/opelika/  processed CSV files used by analysis
data/processed/spatial/ Thiessen weights, polygons, and watershed rainfall
```

Generated root-level `data/` and `logs/` files are ignored by Git because they
can be recreated from the documented request. The small CSV under
`reports/data/` is intentionally committed so a fresh clone can rebuild the
report without calling the live APIs. See the
[data dictionary](docs/data-dictionary.md) for the processed CSV schema, units,
provenance, missing-value rules, and transformations.

### Processing Rules

The pipeline follows this boundary:

```text
API response -> raw JSON evidence -> Pydantic validation -> processed CSV
```

Auburn returns epoch-millisecond timestamps and station rainfall values. MMC
saves the response, converts timestamps to the project's fixed UTC-6 display
representation, and keeps the rainfall value as `RainIn`.

Opelika returns date/time records with cumulative `RainToday`. MMC saves the
response, validates the fields, and converts consecutive cumulative values into
interval `RainIn` values. A negative difference is treated as a counter reset
and the current cumulative value is used for that interval.

After station processing, MMC creates Thiessen polygons from stations with at
least 90% of the expected nominal 10-minute observations. Station and watershed
coordinates begin in WGS 84 and are projected to WGS 84 / UTM Zone 16N
(`EPSG:32616`) before clipping and measuring area. For station `i`:

```text
weight_i = clipped_thiessen_area_i / watershed_area
watershed_rainfall_t = sum(weight_i * station_rainfall_i_t)
```

For this derived calculation only, observations are assigned to the nearest
10-minute label; an exact five-minute tie rounds forward. The period-level
weights remain fixed. If any positive-weight station lacks an observation,
MMC leaves `RainIn` blank, marks the interval `incomplete`, and does not replace
the missing value with zero, interpolate it, or redistribute its weight.

When observations from distinct timestamps align to the same nominal 10-minute
label, MMC sums their interval `RainIn` values for both Auburn and Opelika so
the recorded rainfall is preserved. This is especially explicit for Opelika,
whose increments were derived from the cumulative `RainToday` counter. Exact
duplicates with the same timestamp and value are counted once; equal timestamps
with divergent values exclude the station as a data-quality conflict. Original
processed rows and timestamps remain unchanged, and aggregation counts are
written to the weights audit.

The spatial outputs are:

```text
mmc_thiessen_weights_START_to_END.csv       eligibility, area, and weights
mmc_thiessen_polygons_START_to_END.geojson  clipped polygons in EPSG:4326
mmc_areal_rainfall_START_to_END.csv         model-ready watershed time series
```

Thiessen rainfall is a transparent nearest-station spatial estimate. It is not
radar rainfall and does not establish uniform rainfall within each polygon.

## CLI

Show the current command reference:

```bash
uv run mmc --help
```

Print the installed version:

```bash
uv run mmc --version
```

Enable operational terminal messages:

```bash
uv run mmc --start-date 2026-01-01 --end-date 2026-01-08 --verbose
```

Write detailed diagnostic logs to a file:

```bash
uv run mmc --start-date 2026-01-01 --end-date 2026-01-08 --log-file logs/mmc.log
```

## Dashboard

Start the local dashboard:

```bash
uv run streamlit run src/mmc_watershed_data/dashboard.py
```

The **Rainfall Observation** page lets a user select a date range and stations,
collect new API data or load saved processed CSVs, view Auburn and Opelika
stations on an OpenStreetMap street map, and inspect one rainfall bar chart per
selected station. Auburn and Opelika use different map colors, and the Moores
Mill Creek watershed boundary is loaded from the tracked KMZ assets.

The **Event Analysis** page reports the number of rainfall events, event
duration, total interval precipitation, and participating stations. A positive
`RainIn` observation indicates rainfall; nearby observations are grouped using
the one-hour event tolerance documented in the analysis module.

The **Watershed Rainfall** page displays clipped Thiessen polygons, eligible and
excluded stations, projected watershed area, temporal coverage, fixed weights,
complete and incomplete interval counts, a watershed hyetograph, and a
station influence table. It also downloads the weights CSV, polygon GeoJSON,
and watershed rainfall CSV. New API results update this page immediately;
loading matching saved station CSVs rebuilds the same products.

## Reproducible Report

The authoritative report source is
[`reports/mmc-rainfall-report.qmd`](reports/mmc-rainfall-report.qmd), and the
rendered artifact is
[`reports/mmc-rainfall-report.pdf`](reports/mmc-rainfall-report.pdf). The report
calls the project's reporting, loading, and geospatial modules instead of
recreating data logic in notebook cells.

The normal workflow requires entering the dates only once:

```bash
uv run mmc --start-date 2026-01-01 --end-date 2026-01-08
quarto render reports/mmc-rainfall-report.qmd --to pdf
```

The first command creates one processed CSV per station. The report groups
those files by the date range encoded in their filenames and automatically
selects the collection written most recently. Its reporting dates, summary,
station table, Thiessen map and weights, watershed rainfall hyetograph, station
charts in the sources' nominal 10-minute cadence, interpretation, and
provenance are all generated from that collection. If a clone has no generated
data, the bundled dataset under `reports/data/` allows the repository PDF to be
rebuilt offline. When that dataset does not satisfy the 90% spatial eligibility
policy, the report explains why no watershed estimate is shown rather than
presenting an unsupported value.

The report does not accept a separate reporting period. To change its dates,
run `mmc` for the desired API period and render again. This prevents an old
report setting from overriding the latest downloaded collection.

Quarto and a PDF engine such as TinyTeX are external tools. The Quarto Python
kernel must use the environment created by `uv`; otherwise Quarto may use a
Conda/base Python that does not contain Jupyter, PyYAML, or the MMC package.

For Git Bash on Windows, restore and select the project Python environment:

```bash
uv sync
source .venv/Scripts/activate
export QUARTO_PYTHON="$PWD/.venv/Scripts/python.exe"
quarto check
```

For macOS/Linux, including a professor using the default macOS shell, run:

```bash
uv sync
source .venv/bin/activate
export QUARTO_PYTHON="$PWD/.venv/bin/python"
quarto check
```

The `QUARTO_PYTHON` variable tells Quarto exactly which Python installation to
use. It only applies to the current terminal session. After this setup, collect
the desired period with `mmc` and run the same `quarto render` command shown
above.

## Tests and Development Checks

Install the locked environment:

```bash
uv sync --locked
```

Run the offline test suite with the same coverage gate used by CI:

```bash
uv run coverage erase
uv run coverage run --source=mmc_watershed_data -m pytest
uv run coverage report --show-missing --fail-under=70
```

Run formatting, linting, type checking, and package build checks:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv build --no-sources
```

Tests use stable fixtures and mocks, so they do not call the live rainfall APIs.
The 70% project threshold includes the command, API clients, validation,
storage, workflow, analysis, and dashboard modules rather than omitting
presentation glue to inflate the result.

## Continuous Integration

The [GitHub Actions CI workflow](.github/workflows/ci.yml) runs on every push,
on pull requests targeting `main`, and by manual dispatch. It restores
`uv.lock` with `uv sync --locked`, runs the offline coverage suite, formatting,
linting, strict type checks, `uv build --no-sources`, and isolated package
verification. CI has read-only repository permissions and never calls the live
Auburn or Opelika APIs.

Quarto rendering remains a documented local check because a PDF engine is an
external system dependency. The committed report PDF must still be rendered
and visually inspected before a release.

## Package Evidence

Build the exact wheel and source archive required for a release:

```bash
uv build --no-sources
```

For the version currently declared in `pyproject.toml`, the command creates:

```text
dist/mmc_watershed_data-0.7.0-py3-none-any.whl
dist/mmc-watershed-data-0.7.0.tar.gz
```

Verify both artifacts outside the development environment:

```bash
uv run python scripts/verify_package.py
```

The verifier inspects wheel metadata, dependencies, license, console entry
point, and bundled KMZ assets. It independently rebuilds the wheel from the
source archive, installs the original wheel into a temporary virtual
environment, and runs `mmc --version`, `mmc --help`, and a package import from
outside the repository. It does not call the rainfall APIs.

`dist/` is generated and ignored by Git. Attach only the two verified files for
the exact release version to the GitHub Release. Follow the reusable
[package release checklist](docs/package-checklist.md) before submission.

## Troubleshooting

**`start date must be earlier than or equal to end date`**

Use dates in `YYYY-MM-DD` format and make sure the start date is not after the
end date.

**A station reports an HTTP error or has no usable data**

Retry with a shorter date range. Use `--verbose` or `--log-file logs/mmc.log`
for diagnostics. The other stations can still succeed; inspect the station
failure printed by the command and its raw evidence when available.

**The dashboard has no saved data**

Click the collection action for the selected period first, or run the CLI. Then
use **Load saved CSVs** and select a period with processed files.

**The map cannot find a station or watershed boundary**

Confirm that the tracked files remain under
`assets/geospatial/stations/` and `assets/geospatial/watershed/`. The dashboard
does not create or edit KMZ files.

**Spatial products were not created**

Read the warning printed by `mmc` or shown in the dashboard. Common causes are
fewer than three stations remaining after exclusions for low coverage,
duplicate coordinates, conflicting values at an identical timestamp, collinear
locations, or an unrepairable watershed geometry. Distinct interval values
sharing an aligned label are summed and reported in the weights audit and
operational log. Station raw and processed files remain available even when the
derived spatial step cannot run.

**Quarto cannot render the PDF**

Run `uv sync`, activate the project environment, set `QUARTO_PYTHON` as shown
above, verify `quarto check`, and confirm that a PDF engine such as TinyTeX is
installed. If the message mentions the `(base)` environment or says that
Jupyter/PyYAML is unavailable, Quarto is using the wrong Python interpreter.

## Documentation and License

- [Documentation map](docs/index.md)
- [Processed data dictionary](docs/data-dictionary.md)
- [Package release checklist](docs/package-checklist.md)
- [GitHub Actions CI workflow](.github/workflows/ci.yml)
- [Sprint specifications](docs/specs/)
- [Project guidance](AGENTS.md)
- [MIT License](LICENSE)

The project does not require credentials. Never add secrets to the source,
report, fixtures, outputs, or logs.
