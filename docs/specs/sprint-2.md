# Sprint 02: Multi-Station Auburn and Opelika Rainfall Tool

MMC Watershed Data is a Python command-line tool for collecting precipitation data from the City of Auburn and the City of Opelika, using all available stations from both city feeds.

## Context

Expand the first version from a single Auburn station into a multi-station tool. The user should provide only a period of time, and the tool should collect every available station for Auburn and Opelika for that same date range.

## User Features: What

- A user can run the project as the `mmc` command.
- A user can identify only a start date and an end date for the download.
- A user can collect rainfall data for all available Auburn stations.
- A user can collect rainfall data for all available Opelika stations.
- A user can reuse the same date window for every station in both cities.
- A user can save raw API responses as evidence in `data/raw/`.
- A user can save raw CSV files in `data/raw/` to inspect the unprocessed rows.
- A user can save processed CSV files in `data/processed/`.
- A user can see the station names and station IDs used in the download output.
- A user can get a clear message when a station request fails.
- A user can find enough information in the README to install and run the project without help.
- A developer can run tests without calling the live APIs.
- A developer can run formatting, linting, type checking, and package build checks.

## Implementation Plan: How

- Keep the `src/` package layout.
- Keep `uv` as the project runner and build tool.
- Keep the command name as `mmc`.
- Keep the CLI limited to `--start-date` and `--end-date`.
- Treat the date window as a whole-day range for every station.
- Use the Auburn LI-COR endpoint for the Auburn stations.
- Use the Opelika ThorArchive endpoint for the Opelika stations.
- Encode station metadata in a single source of truth, including station key, station name, and station ID or channel UUID.
- Keep network access isolated in API modules.
- Keep raw-to-processed transformation logic isolated and testable.
- Use dataclasses or typed models for station metadata, raw record sets, and processed outputs.
- Write raw JSON evidence and raw/processed CSV files, keeping the layout close to Sprint 1.
- Keep raw and processed transformations explicit and easy to compare with the source scripts.
- Keep station-specific processing rules explicit in the code and documented in the README.
- Use fixture-based tests for request building, parsing, conversion, and file output behavior.

## Auburn Source Details

- The Auburn feed uses the LI-COR dashboard endpoint seen in:
  - `https://www.licor.cloud/dashboards/52f7495a-bd9c-48ff-a568-20431bc95b60/true`
- The Auburn API endpoint is:
  - `https://www.licor.cloud/api/v2/timeseriesdata`
- Available Auburn stations:
  - `WRM Office`
  - `Lake Ogletree`
  - `Northside WPCF`
  - `NW Auburn Tank`
  - `HC Morgan WPCF`
- Auburn raw data should preserve the endpoint response in JSON and also store a raw CSV extract for visual inspection.
- Auburn processed data should convert epoch milliseconds into a fixed UTC-6 timestamp and keep rainfall values as the station rain amount.

## Opelika Source Details

- The Opelika feed uses the ThorArchive API endpoint:
  - `https://360.thormobile.net/thorcloud/api/weatherpacketsbyinterval`
- Available Opelika stations:
  - `Sportsplex`
  - `Floral Park`
  - `West Ridge Park`
  - `Covington Center`
- Opelika requests should be made per station using the requested date range.
- Opelika raw data should preserve the returned JSON and also store a raw CSV extract for inspection.
- Opelika processed data should convert the cumulative `RainToday` field into interval rainfall values, keeping the data usable for downstream work.

## Tasks

- Update project metadata if needed for the expanded scope.
- Keep the `mmc` console script.
- Implement station metadata for all Auburn and Opelika stations.
- Implement the Auburn data download flow for all Auburn stations.
- Implement the Opelika data download flow for all Opelika stations.
- Accept only `--start-date` and `--end-date` on the CLI.
- Reuse the same date window for every station in both city feeds.
- Save raw JSON responses in `data/raw/`.
- Save raw CSV files in `data/raw/` for visual review.
- Save processed CSV files in `data/processed/`.
- Make the raw JSON easy to inspect as evidence, with one station per file and clear metadata.
- Make the raw CSV easy to inspect, with one station per file and clear column names.
- Make the processed CSV easy to inspect, with one station per file and clear headers.
- Document the station lists, endpoints, and processing rules in `README.md`.
- Document that the user only supplies the time period, not the station list.
- Add or update tests for the Auburn and Opelika transformation rules.
- Add or update tests for CSV creation and naming.
- Verify:
  - `uv build`
  - `uv run python -m unittest discover -s tests`

## Out Of Scope

- Adding new cities beyond Auburn and Opelika.
- Allowing the user to choose individual stations from the command line.
- Charts, dashboards, or web views.
- Scheduled runs.
- Database storage.
- Manual spreadsheet editing outside the generated CSV outputs.
- Changing the station processing rules beyond what the source scripts already define.
