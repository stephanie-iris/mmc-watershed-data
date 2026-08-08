# MMC Watershed Data Documentation

The README is the starting point for installing and using MMC Watershed Data.
This page maps the durable project documentation to the question it answers.

| Need | Source |
| --- | --- |
| Install, configure, run, test, or troubleshoot | [`README.md`](../README.md) |
| Understand project guidance and source-of-truth rules | [`AGENTS.md`](../AGENTS.md) |
| Understand station, Thiessen-weight, GeoJSON, and watershed-rainfall fields | [`data-dictionary.md`](data-dictionary.md) |
| Review completed implementation requirements | [`specs/`](specs/) |
| Read or rebuild the rainfall report | [`reports/`](../reports/) |
| Build and verify release artifacts | [`package-checklist.md`](package-checklist.md) |
| Review the automated quality gate | [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) |
| See expected behavior and offline test inputs | [`tests/`](../tests/) and [`tests/fixtures/`](../tests/fixtures/) |
| Review the open-source license | [`LICENSE`](../LICENSE) |

The source modules contain the code-level contracts through their docstrings.
The README is the user source of truth, the data dictionary is the processed
CSV schema source of truth, and `reports/mmc-rainfall-report.qmd` is the report
source of truth.

Files under `data/raw/`, `data/processed/`, and `logs/` are run-specific
evidence or diagnostics. They are not the source of intended behavior and are
ignored by Git.
