# Package Release Checklist

Use this checklist for every MMC Watershed Data release. Replace `X.Y.Z` with
the version declared in `pyproject.toml`; do not infer a version from an old
file already present in `dist/`.

## Repository Gate

- Confirm `pyproject.toml`, `mmc_watershed_data.__version__`, `uv.lock`, README,
  and CHANGELOG agree on the release version.
- Confirm `.env`, `.coverage`, `data/`, `dist/`, virtual environments, logs,
  and notebook checkpoints are not tracked.
- Confirm the latest GitHub Actions CI run for the release commit succeeds.
- Confirm no test or CI step calls the live Auburn or Opelika APIs.

## Local Quality Gate

Run from a clean checkout:

```bash
uv sync --locked
uv run coverage erase
uv run coverage run --source=mmc_watershed_data -m pytest
uv run coverage report --show-missing --fail-under=70
uv run ruff format --check .
uv run ruff check .
uv run mypy src
quarto render reports/mmc-rainfall-report.qmd --to pdf
```

Inspect the PDF and dashboard manually. Quarto remains a local check because
its PDF engine is intentionally not installed in the Python-only CI runner.

## Build And Verify

Ensure `dist/` does not contain stale files that could be confused with the
current release, then run:

```bash
uv build --no-sources
uv run python scripts/verify_package.py
```

For version `X.Y.Z`, verify that the only intended release attachments are:

```text
dist/mmc_watershed_data-X.Y.Z-py3-none-any.whl
dist/mmc-watershed-data-X.Y.Z.tar.gz
```

The verification script checks metadata, dependencies, console entry point,
license, geospatial assets, and archive contents. It rebuilds the wheel from
the extracted source archive, installs the original wheel into a temporary
virtual environment, and runs `mmc --version`, `mmc --help`, and an import from
outside the repository. It does not call either rainfall API.

## Release Evidence

- Attach the verified `.whl` and `.tar.gz` files to the exact GitHub Release.
- Link that exact release in the project reflection.
- Keep `dist/` ignored; release attachments, not committed binaries, are the
  authoritative package evidence.
- Perform a short manual API collection and inspect raw JSON, raw CSV,
  processed CSV, dashboard behavior, station failures, and spatial outputs.
