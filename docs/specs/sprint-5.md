# Sprint 05: Project Documentation and Reproducible Rainfall Report

MMC Watershed Data is a `uv`-managed Python command-line tool and Streamlit
dashboard for collecting, validating, processing, and exploring rainfall data
from Auburn and Opelika. This sprint prepares the project for Practicum 6 by
making its documentation complete and by adding one authoritative, reproducible
Quarto report.

## Context

The project already has a working CLI, shared collection workflow, Pydantic
validation, raw JSON and CSV evidence, processed CSV outputs, a Streamlit
dashboard, station KMZ files, event analysis, tests, and an `AGENTS.md` file.
The documentation is not yet a complete map of the project, and the project
does not yet provide a data dictionary, standard open-source license, or
reproducible report.

The report must be a consumer of the existing project logic, not a second
implementation of API access, validation, rainfall conversion, event
detection, or CSV loading.

## User Features: What

- A new contributor can understand what MMC means, what the project does, and
  who it is for from the README.
- A stranger can follow the fastest documented path from clone to a working
  collection or dashboard result.
- The README documents installation, configuration, exact run commands, exact
  test commands, realistic examples, inputs, outputs, and common failures.
- The README links to the data dictionary, license, report source, report PDF,
  documentation map, and other detailed documentation that users need.
- The repository includes a standard open-source license, using an established
  license text rather than a custom license.
- `AGENTS.md` provides durable setup, testing, navigation, conventions, and
  source-of-truth guidance. It is not a task list or session transcript.
- `mmc --help` accurately describes the required date arguments, optional
  logging arguments, output behavior, and useful examples or usage guidance.
- The dashboard's visible labels, short instructions, and error messages use
  current MMC terminology and tell users what action to take when possible.
- Every project module, class, and function has a concise docstring. Public
  inputs and outputs use type hints, and docstrings explain important failures
  or transformations where they apply.
- A data dictionary defines the fields in the main processed rainfall output.
- A reader can rebuild the report PDF from its committed `.qmd` source after
  restoring the project environment.
- The report asks one useful question about the rainfall data and answers it
  with generated evidence: a summary, at least one table, at least one figure,
  and a brief interpretation.

## Documentation Deliverables

### README

Update `README.md` as the user-facing source of truth. It should contain, in a
direct and project-specific form:

- the purpose of MMC Watershed Data and its intended users;
- a fastest-path quick start using `uv sync` and a realistic date range;
- Python and `uv` requirements;
- the fact that the Auburn and Opelika endpoints used here do not require an
  API key, so users are not asked to create an unnecessary `.env` file;
- the exact CLI command, dashboard command, test command, and report-render
  command;
- the input date range semantics: whole calendar days selected with
  `--start-date` and `--end-date`;
- the two data sources and links to the Auburn and Opelika dashboards;
- the station scope and the raw/processed output locations;
- a realistic example of a successful collection and a description of the
  files it creates;
- the distinction between raw JSON evidence, raw CSV inspection extracts, and
  processed CSV data used by analysis;
- the Auburn timestamp and rainfall transformation;
- the Opelika cumulative `RainToday` to interval-rainfall transformation;
- the Streamlit pages, date/station controls, street map, station colors,
  watershed boundary, rainfall charts, and event-analysis metrics;
- common failures such as invalid dates, HTTP failures, empty API responses,
  validation failures, missing KMZ assets, missing saved CSVs, and unavailable
  Quarto/PDF tooling, with actionable recovery guidance;
- links to `LICENSE`, `docs/index.md`, `docs/data-dictionary.md`,
  `reports/mmc-rainfall-report.qmd`, and the rendered report PDF.

Do not document an API key or `.env.example` as required configuration because
the current MMC sources are public and do not require credentials. Never place
a real secret in the README, report, fixtures, logs, or repository metadata.

### Documentation map

Add `docs/index.md` as a small navigation page. It should identify the
authoritative purpose of each of these locations:

- `README.md` for user setup, commands, outputs, and troubleshooting;
- `AGENTS.md` for durable contributor and coding guidance;
- `docs/data-dictionary.md` for processed rainfall fields and transformations;
- `docs/specs/` for completed sprint requirements;
- `reports/` for the report source and rendered report artifact;
- `tests/` and `tests/fixtures/` for executable behavior and stable test input;
- `LICENSE` for the project's standard open-source license;
- source docstrings for the code-level API contract.

Explain that `data/raw/`, `data/processed/`, and `logs/` are run-specific
evidence or diagnostics, not the source of truth for intended behavior.

### License

Add a standard open-source license file. The implementation should use the
MIT License unless the course or repository owner has already selected another
standard license. The README must link to it and identify the project as
licensed under that standard license. Do not invent or modify license wording.

### AGENTS.md

Refresh `AGENTS.md` so it remains short and durable. It should include:

- project purpose and source layout;
- `uv sync` setup and exact test/build/report checks;
- where API access, shared workflow, validation, storage, analysis, dashboard,
  and report code belong;
- conventions for fixtures, mocks, raw evidence, processed data, geospatial
  assets, and ignored generated files;
- the rule that the README is the user source of truth, the data dictionary is
  the schema source of truth, and the report `.qmd` is the report source of
  truth;
- the requirement to update documentation when user-visible behavior, output
  fields, transformations, or commands change.

It must not include a chronological record of this sprint or instructions that
only apply to a single temporary task.

## CLI and Dashboard Documentation Quality

- Review `mmc --help` after any CLI help changes. The output must be accurate
  for the current command, including the fact that only dates are selected and
  that all configured stations are collected.
- Keep help text concise but useful to a new user. It should explain the date
  format, the output locations, `--verbose`, and `--log-file`.
- Review dashboard page titles, labels, buttons, empty-state messages, and
  errors. They should say `watershed`, not `basin`, and should explain whether
  the user should collect new data or load saved processed CSVs.
- Preserve the existing user-facing behavior that collecting a new period
  refreshes the dashboard data and charts automatically.
- Add or update tests for important help text and user-facing failure paths
  without requiring a live API or browser.

## Docstrings and Type Hints

Audit every `.py` module under `src/mmc_watershed_data/`:

- every module has a module docstring describing its responsibility;
- every class has a concise docstring describing its role and important
  invariants;
- every function has a concise docstring describing behavior, relevant inputs,
  return value, and important failures or transformations;
- public and internal function inputs and outputs have useful type hints;
- comments are reserved for rationale, source-format constraints, or other
  non-obvious decisions rather than narrating straightforward code.

Docstrings must describe MMC behavior, not repeat generic Python terminology.
They should mention source-specific details such as epoch milliseconds,
cumulative `RainToday`, raw-evidence preservation, validation failures, and KMZ
parsing where those details belong.

## Data Dictionary

Add `docs/data-dictionary.md` for the main processed rainfall CSV schema. At a
minimum, document every field currently written by the Auburn and Opelika
processed outputs, including fields such as station identity, city, local
timestamp, rainfall amount, and source-specific identifiers where present.

For each field, specify:

- field name;
- Python/storage type and expected format;
- units or allowable values;
- meaning;
- source field or source endpoint;
- provenance and station context;
- missing-value rules;
- important transformations or derivations.

Document the different source rules explicitly:

- Auburn timestamps are converted from epoch milliseconds to the project's
  fixed UTC-6 timestamp representation, and the station rain amount is kept as
  the interval rainfall value.
- Opelika timestamps are parsed from the provider date/time representation, and
  cumulative `RainToday` is converted into interval rainfall values.
- The documented policy for counter resets, negative differences, malformed
  values, and missing observations must match the implemented code.

Explain that raw JSON and raw CSV have broader provider-specific shapes and are
evidence artifacts, while the processed CSV is the stable schema intended for
downstream analysis and the dashboard.

## Reproducible Quarto Report

Create one authoritative source at:

```text
reports/mmc-rainfall-report.qmd
```

Create and commit one rendered PDF produced from that source at a clearly named
path such as:

```text
reports/mmc-rainfall-report.pdf
```

The PDF must not be edited by hand. If the rendered result is wrong, update the
`.qmd`, project code, or report input and render again.

### Report question and evidence

The report should ask one useful question that can be answered with the
available processed rainfall data. A suitable example is:

> During the selected reporting period, which station recorded the greatest
> total interval rainfall, and how did rainfall vary across the stations?

The final question may be refined during implementation, but it must be
specific, answerable from the available data, and relevant to Moores Mill Creek
watershed monitoring. The report must include:

- a concise summary answering the question;
- at least one generated table, such as station totals, record counts, or event
  summaries;
- at least one generated figure, such as rainfall totals by station or a time
  series/bar chart;
- a brief interpretation that distinguishes observed data from conclusions the
  data cannot support;
- the source endpoint(s), station scope, reporting dates, filters/parameters,
  rainfall units, and report render date.

### Shared project logic

The report must import and call existing MMC code for reusable behavior:

- load processed CSV records through the project's loading boundary;
- use the existing typed records and/or validation behavior;
- use existing event detection or aggregation functions where applicable;
- use project-defined transformations rather than reimplementing raw API
  parsing or cumulative-rain conversion in report cells.

Report-specific code may select a question, arrange a table, format text, and
create a publication figure, but it must not become a replacement for
`api.py`, `validation.py`, `storage.py`, `workflow.py`, or `analysis.py`.

### Reproducibility and inputs

Choose and document a reproducible input strategy. The preferred approach is to
use a committed, small, sanitized fixture or report input derived from the
project's processed schema, so the committed PDF can be rebuilt without relying
on a live API. If the report acquires data, it must preserve raw evidence and
record the exact period, stations, endpoint parameters, acquisition mode, and
render timestamp without writing secrets.

The report source, input data, output PDF, metadata, and logs must not contain
API keys or other secrets. Generated full-run `data/` artifacts remain governed
by the project's existing Git policy; the report's committed input must be
small, intentional, and clearly documented.

### Exact rebuild command

Document one exact command in both the README and report for rebuilding the PDF
after the environment has been restored. The command should be:

```bash
uv sync
uv run quarto render reports/mmc-rainfall-report.qmd --to pdf
```

If the environment does not expose Quarto through `uv run`, document the exact
supported Windows PowerShell and Git Bash command instead, and list Quarto and
the PDF engine as external prerequisites. The command must be tested in a
restored environment.

## Tests and Verification

Add or update offline tests for:

- README, documentation-map, data-dictionary, license, and report-source
  presence and links where practical;
- accurate `--help` text and `--version` behavior;
- docstring coverage for project modules, classes, and functions;
- report loading through shared project code rather than duplicated parsing;
- report summary calculations, table data, and figure input using a stable
  fixture;
- missing, malformed, or empty report input with a clear failure;
- report behavior that does not expose secrets in generated text or logs.

Run the complete verification set:

```bash
uv run python -m pytest
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv build
uv run quarto render reports/mmc-rainfall-report.qmd --to pdf
```

Inspect the rendered PDF visually before considering the sprint complete. Check
that the title, summary, table, figure, interpretation, provenance, units, and
page layout are readable and that no traceback, secret, or placeholder remains.

## Documentation Acceptance Criteria

- README is current, linked, direct, and sufficient for a stranger to install,
  run, test, and troubleshoot MMC.
- `LICENSE` is a standard open-source license and is linked by the README.
- `AGENTS.md` contains durable project guidance rather than a task transcript.
- `docs/index.md` and `docs/data-dictionary.md` exist and are linked.
- CLI help and dashboard text match the implemented behavior.
- All project modules, classes, and functions have concise docstrings and type
  hints where applicable.
- `reports/mmc-rainfall-report.qmd` is the single authoritative report source.
- `reports/mmc-rainfall-report.pdf` is generated from that source and committed.
- The report contains a question, summary, table, figure, interpretation,
  provenance, exact dates/parameters, units, and render date.
- The report calls shared MMC code for loading, validation, and analysis.
- The exact PDF rebuild command succeeds after `uv sync`.
- The rendered PDF was inspected and corrected through source changes, never by
  editing the PDF directly.
- No real secrets are present in source, output, metadata, logs, fixtures, or
  committed report inputs.

## Out Of Scope

- Changing Auburn or Opelika API endpoints, station IDs, or rainfall
  transformation rules without a separate data-behavior change.
- Adding a new city or data source.
- Replacing the CLI or Streamlit dashboard with a report-only workflow.
- Building a Quarto website, deployment pipeline, journal template, or multiple
  report formats.
- Adding generic documentation that does not explain MMC behavior.
- Editing existing completed sprint specifications.
