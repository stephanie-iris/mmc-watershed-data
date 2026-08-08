# Changelog

## 0.7.0 - 2026-08-07

Added the Sprint 7 final-delivery safeguards and reproducible package evidence.

- Added read-only GitHub Actions CI for locked installation, offline coverage, formatting, linting, type checking, package builds, and isolated artifact verification.
- Made the wheel independently usable by bundling the license and geospatial KMZ assets, and made the source archive self-contained for rebuilding.
- Added a release checklist, package verification script, 70% coverage gate, and repository-hygiene tests; removed the tracked notebook checkpoint.
- Updated the README, project guidance, documentation map, and package metadata for the final release workflow.
- Added a searchable MkDocs website, docstring-generated Python reference, and automatic GitHub Pages deployment on pushes to `main`.

## 0.6.0 - 2026-08-07

Added the Sprint 6 Thiessen watershed-rainfall release for hydrologic modeling.

- Added projected Voronoi construction and watershed clipping in `EPSG:32616`, with explicit geometry, area, overlap, coverage, and weight validation.
- Added deterministic 90% station eligibility, nearest 10-minute alignment, rainfall-preserving interval summation for both cities, exact-duplicate safeguards, aggregation auditing, and strict missing-data handling without interpolation or weight redistribution.
- Added auditable weights CSV, clipped-polygon GeoJSON, and model-ready watershed rainfall CSV outputs.
- Integrated the shared spatial workflow into the `mmc` command, saved-data loading, dashboard session, and automatic Quarto report.
- Added the Watershed Rainfall dashboard page with Thiessen map, metrics, tables, charts, quality status, and downloads.
- Expanded the report, README, data dictionary, package metadata, and offline tests for the spatial method.

## 0.5.0 - 2026-08-02

Added the Sprint 5 documentation and reproducible-report release.

- Reworked the README around project purpose, installation, exact commands, inputs, outputs, troubleshooting, and the fastest path to a result.
- Added a standard open-source license and durable `AGENTS.md` project guidance.
- Added project documentation and a data dictionary covering field meaning, types, units, provenance, missing values, and transformations.
- Added an authoritative Quarto report source and its rendered PDF.
- Made the report automatically follow the most recently collected API period.
- Added a watershed and station location map, station statistics, total-rainfall comparisons, and direct rainfall charts at the processed data's nominal 10-minute cadence.
- Added automated checks for the required documentation and report behavior.

## 0.4.0 - 2026-07-29

Added the Sprint 4 Streamlit dashboard and refined its user-facing behavior.

- Added the MMC Watershed Rainfall Dashboard with rainfall observation and event analysis pages.
- Added street-map visualization with Auburn and Opelika station colors.
- Added the Moores Mill Creek watershed boundary and station KMZ integration.
- Added station selection, rainfall bar charts, event summaries, and event station participation.
- Added automatic dashboard refresh after collecting a new API period.
- Renamed dashboard and project-facing geographic terminology from basin to watershed.

## 0.3.0 - 2026-07-28

Added the Sprint 3 reliability layer to make collection behavior easier to
validate, test offline, diagnose, and reuse in the future dashboard.

- Added Pydantic validation for the Auburn and Opelika response fields used by the project.
- Added valid and invalid fixtures for controlled success and failure tests.
- Added mocked network tests for successful requests, failures, and retries without live API calls.
- Added a shared collection workflow for the CLI and future Streamlit dashboard.
- Added optional `--verbose` console logging and `--log-file` diagnostic logging.
- Preserved raw JSON evidence before processed-data validation failures whenever possible.
- Documented the new validation, fixture, mock, workflow, and logging behavior in the README.

## 0.2.0 - 2026-07-27

Expanded the tool from a single Auburn station in `0.1.0` to a multi-station downloader for Auburn and Opelika.

- Added all available Auburn stations, not just Lake Ogletree.
- Added all available Opelika stations.
- Kept raw JSON evidence in `data/raw/` for every station.
- Added raw CSV extracts alongside the JSON so the unprocessed rows are easier to read.
- Kept processed CSV outputs in `data/processed/` for every station.
- Documented the Opelika dashboard and both processing rules in the README.
- Kept the CLI simple so the user only chooses the date range.

## 0.1.0 - 2026-07-19

Initial release for Practicum 4, implemented through Sprint 1.

- Added the `mmc` command-line tool.
- Collected Auburn Ogletree rainfall data from the LI-COR dashboard endpoint.
- Saved raw responses in `data/raw/`.
- Saved processed outputs in `data/processed/`.
- Documented setup, usage, and the API source in the README.
