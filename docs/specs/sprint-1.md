# Sprint 01: First Auburn Rainfall Data Tool

MMC Watershed Data is a small Python command-line tool for collecting precipitation data for the City of Auburn, using the Ogletree station as the data source.

## Context

Build the first useful version of the project. Keep the scope narrow: one API, one collection flow, one command, and enough structure to support later changes.

## User Features: What

- A user can run the project as a `uv`-managed command named `mmc`.
- A user can collect precipitation data for the City of Auburn from the Ogletree station.
- A user can obtain the data the same way it is accessed in `examples/CityofAuburnData_LakeOgeltree_Self_Copy_R03.py`.
- A user can define a date range using whole days only.
- A user can save the raw API response as evidence in `data/raw/`.
- A user can save a processed version for later use in `data/processed/`.
- A user can see clear progress messages while data is being fetched.
- A user can get a clear message when the request fails or no data is returned.
- A user can save the collected data to a local file.
- A user can find enough information in the README to install and run the project without help.
- A developer can run tests without calling the live data source.
- A developer can run formatting, linting, type checking, and package build checks.

## Implementation Plan: How

- Use a `src/` package layout for the application code.
- Use `uv` for environment management, command execution, locking, and building.
- Use `uv_build` as the build backend.
- Keep the project runnable as a command installed or invoked through `uv`.
- Use `requests` for the remote data request.
- Keep the source-specific request logic in a dedicated module.
- Keep command-line parsing and orchestration in a CLI module.
- Keep data transformation, cleanup, and output preparation in separate functions where practical.
- Represent download settings and output metadata with dataclasses or simple typed models.
- Keep pure logic isolated so it is easy to test.
- Use fixture-based tests for request building, parsing, and output behavior.
- Use Ruff for formatting and linting.
- Use mypy for static type checks.

## Tasks

- Create project metadata in `pyproject.toml`.
- Configure the console script for the tool.
- Add `.gitignore` entries for `data/`, `.venv/`, caches, and output files.
- Implement the Auburn Ogletree data download client.
- Implement CLI arguments for the relevant date range using whole days only.
- Reuse the request pattern shown in `examples/CityofAuburnData_LakeOgeltree_Self_Copy_R03.py`.
- Save the raw API response under `data/raw/` before any processing.
- Save the processed, reusable dataset under `data/processed/`.
- Handle retries, time windows, and request failures clearly.
- Normalize and sort the collected records before saving.
- Write the collected rainfall data to a local file.
- Add a short README write-up covering the API and docs link, one example request, what the response contains, and one line describing what will be built.
- Make sure the README is enough for a stranger to install and run the project.
- Add tests for window building, request payload generation, record parsing, and error handling.
- Document setup, usage, and development checks in `README.md`.
- Add `AGENTS.md` with project guidance for coding agents.
- Verify:
  - `uv build`
  - `uv run python -m pytest`
  - `uv run ruff format --check .`
  - `uv run ruff check .`
  - `uv run mypy src`

## Out Of Scope

- Multiple stations.
- Charts, dashboards, or web views.
- Scheduled runs.
- Database storage.
- Manual spreadsheet editing.
- Broader watershed analysis beyond Auburn Ogletree rainfall collection.
- The `examples/` folder content itself is out of scope for the deliverable and can remain ignored in Git.
