# AGENTS.md

## Project Notes

- This project is a `uv`-managed Python command-line tool.
- The main command is `mmc`.
- Auburn outputs belong in `data/raw/auburn/` and `data/processed/auburn/`.
- Opelika outputs belong in `data/raw/opelika/` and `data/processed/opelika/`.
- CSV is the standard output format for both raw and processed data.
- The example scripts in `examples/` document the Auburn and Opelika request patterns.

## Coding Guidance

- Prefer small, testable functions.
- Keep network access isolated in the API module.
- Keep file writing isolated in the storage module.
- Use the README as the source of truth for setup and run instructions.
