# MMC Watershed Data

MMC means **Moores Mill Creek**. This project is for students, watershed
analysts, and developers who need a repeatable way to collect and inspect
rainfall observations from stations in Auburn and Opelika, Alabama.

The project provides a `uv` command-line tool named `mmc`, a Streamlit
dashboard, validated raw-to-processed outputs, and a reproducible Quarto report.

Current version: `0.5.0`

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
station table, watershed location map, total-rainfall chart, station charts in
the sources' nominal 10-minute cadence, interpretation, and provenance are all
generated from that collection. If a clone has no generated data, the bundled
dataset under `reports/data/` allows the repository PDF to be rebuilt offline.

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
uv sync
```

Run the offline test suite:

```bash
uv run python -m pytest
```

Run formatting, linting, type checking, and package build checks:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv build
```

Tests use stable fixtures and mocks, so they do not call the live rainfall APIs.

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

**Quarto cannot render the PDF**

Run `uv sync`, activate the project environment, set `QUARTO_PYTHON` as shown
above, verify `quarto check`, and confirm that a PDF engine such as TinyTeX is
installed. If the message mentions the `(base)` environment or says that
Jupyter/PyYAML is unavailable, Quarto is using the wrong Python interpreter.

## Documentation and License

- [Documentation map](docs/index.md)
- [Processed data dictionary](docs/data-dictionary.md)
- [Sprint specifications](docs/specs/)
- [Project guidance](AGENTS.md)
- [MIT License](LICENSE)

The project does not require credentials. Never add secrets to the source,
report, fixtures, outputs, or logs.
