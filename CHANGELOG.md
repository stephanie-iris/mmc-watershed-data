# Changelog

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
