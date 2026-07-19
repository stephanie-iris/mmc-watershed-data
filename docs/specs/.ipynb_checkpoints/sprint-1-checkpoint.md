# Sprint 01: First Auburn Rainfall Data Tool

MMC Watershed Data is a small Python command-line tool for collecting precipitation data for the City of Auburn, using the Ogletree station as the data source.

## Context

Build the first useful version of the project. Keep the scope narrow: one data source, one collection flow, one terminal summary, and enough structure to support later changes.

## User Features: What

- A user can run the project from the command line.
- A user can collect precipitation data for the City of Auburn from the Ogletree station.
- A user can obtain the data the same way it is accessed in `examples/CityofAuburnData_LakeOgeltree_Self_Copy_R03.py`.
- A user can define a date range for the download.
- A user can see clear progress messages while data is being fetched.
- A user can get a clear message when the request fails or no data is returned.
- A user can save the collected data to a local file.
- A developer can run tests without calling the live data source.
- A developer can run formatting, linting, type checking, and package build checks.

## Implementation Plan: How

- Use a `src/` package layout for the application code.
- Use `uv` for environment management, command execution, locking, and building.
- Use `uv_build` as the build backend.
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
- Add local environment and secrets handling if needed.
- Add `.gitignore` entries for environments, caches, generated data, and output files.
- Implement the Auburn Ogletree data download client.
- Implement CLI arguments for the relevant date range and output settings.
- Reuse the request pattern shown in `examples/CityofAuburnData_LakeOgeltree_Self_Copy_R03.py`.
- Handle retries, time windows, and request failures clearly.
- Normalize and sort the collected records before saving.
- Write the collected rainfall data to a local file.
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
