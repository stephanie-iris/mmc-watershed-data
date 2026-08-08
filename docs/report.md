# Reproducible Report

The authoritative report source is
[`reports/mmc-rainfall-report.qmd`](https://github.com/stephanie-iris/mmc-watershed-data/blob/main/reports/mmc-rainfall-report.qmd).
It automatically selects the most recently written complete collection under
`data/processed/`. When generated data are unavailable, it uses the tracked
fallback under `reports/data/`.

## Rebuild The PDF

After restoring the project environment and installing Quarto with a PDF
engine, run:

```bash
quarto render reports/mmc-rainfall-report.qmd --to pdf
```

The committed PDF is available from the
<a href="reports/mmc-rainfall-report.pdf">GitHub Pages report download</a> or
directly in the
[`reports/` directory](https://github.com/stephanie-iris/mmc-watershed-data/tree/main/reports).

The report records the selected period, observation count, represented
stations, rainfall units, spatial method, CRS, project version, Python version,
and UTC render time. It calls the project's shared loading and spatial logic
rather than recreating transformations in notebook cells.
