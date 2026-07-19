# AGENTS.md

## Project Notes

- This project is a `uv`-managed Python command-line tool.
- The main command is `mmc`.
- Raw API responses belong in `data/raw/`.
- Processed datasets belong in `data/processed/`.
- The example script in `examples/` documents the original request pattern.

## Coding Guidance

- Prefer small, testable functions.
- Keep network access isolated in the API module.
- Keep file writing isolated in the storage module.
- Use the README as the source of truth for setup and run instructions.
