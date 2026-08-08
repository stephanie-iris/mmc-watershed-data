# AGENTS.md

## Project Context

MMC Watershed Data is a `uv`-managed Python project for collecting, validating,
processing, and exploring rainfall observations from Auburn and Opelika. The
CLI command is `mmc`; the browser interface is the Streamlit dashboard.

## Setup and Checks

Restore the environment with:

```bash
uv sync --locked
```

Run the checks before committing:

```bash
uv run coverage run --source=mmc_watershed_data -m pytest
uv run coverage report --show-missing --fail-under=70
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run mkdocs build --strict
uv build --no-sources
uv run python scripts/verify_package.py
quarto render reports/mmc-rainfall-report.qmd --to pdf
```

The test suite is offline and uses fixtures plus mocks. Quarto and a PDF engine
are external tools; `quarto check` diagnoses their installation.
Package verification uses temporary environments and does not call live APIs.

## Navigation and Conventions

- Keep API access in `src/mmc_watershed_data/api.py`, `auburn.py`, and
  `opelika.py`.
- Keep the shared date request and multi-city orchestration in `workflow.py`.
- Keep external response validation in `validation.py` and file output in
  `storage.py`.
- Keep typed rainfall loading and event detection in `analysis.py`.
- Keep map parsing in `geospatial.py` and browser presentation in
  `dashboard.py`.
- Auburn outputs belong in `data/raw/auburn/` and
  `data/processed/auburn/`; Opelika outputs use the corresponding `opelika`
  directories.
- Raw JSON preserves provider evidence. Raw CSV is an inspection extract.
  Processed CSV is the stable schema used by analysis and the dashboard.
- Station KMZ assets belong under `assets/geospatial/`; generated data, logs,
  `.venv/`, `.vscode/`, and notebook checkpoints are not source files.
- Use small fixtures under `tests/fixtures/` and mocked network boundaries in
  tests. Unit tests must not call the live APIs.
- Add concise module, class, and function docstrings with type hints. Comments
  should explain rationale or source-format constraints, not narrate obvious
  statements.

## Source Of Truth

- `README.md` is the user-facing source of truth for installation, commands,
  outputs, dashboard behavior, and troubleshooting.
- `docs/index.md` is the documentation map.
- `docs/data-dictionary.md` is the processed CSV schema source of truth.
- `docs/specs/` records completed sprint requirements; do not rewrite completed
  specifications to describe later implementation details.
- `reports/mmc-rainfall-report.qmd` is the authoritative report source, and its
  PDF is generated output from that source.
- `.github/workflows/ci.yml` is the authoritative automated quality gate.
- `mkdocs.yml` defines the documentation website, and
  `.github/workflows/docs.yml` is its GitHub Pages deployment source.
- `docs/package-checklist.md` is the source of truth for release artifact
  verification.
- Source docstrings and tests define code-level contracts and expected failure
  behavior.

Update the smallest authoritative document when behavior, commands, output
fields, units, transformations, or user-visible labels change. Never put API
keys or other secrets in source, fixtures, reports, metadata, outputs, or logs.
