# Sprint 06: Thiessen Areal Rainfall for Hydrologic Modeling

MMC Watershed Data already collects, validates, processes, maps, and reports
rainfall observations from Auburn and Opelika stations. This sprint converts
those point observations into an area-weighted rainfall time series for the
Moores Mill Creek (MMC) watershed using Thiessen polygons, also known as
Voronoi polygons.

The resulting time series is intended to be a transparent, reproducible input
for a hydrologic model. The implementation must preserve the station data and
add a derived product; it must not change the Auburn or Opelika raw-to-processed
transformations completed in earlier sprints.

## Context

The project already contains the required spatial inputs:

- station coordinates in `assets/geospatial/stations/`;
- the MMC watershed boundary in `assets/geospatial/watershed/`;
- processed station rainfall in `data/processed/auburn/` and
  `data/processed/opelika/`;
- shared typed loading, validation, collection, dashboard, and report logic.

The current geospatial module reads latitude and longitude for presentation on
a map. It does not yet project geometries, create Thiessen polygons, intersect
them with the watershed, calculate areas, or combine rainfall values using
spatial weights.

## Objective

For the most recently collected API period, the project should:

1. identify the stations with sufficient usable observations;
2. generate one Thiessen influence region per eligible station;
3. clip each influence region to the MMC watershed;
4. calculate the watershed area assigned to each station;
5. convert those areas into fixed station weights;
6. apply the weights to the processed rainfall observations; and
7. save and display a watershed-average rainfall time series suitable for
   downstream hydrologic modeling.

The method, eligibility decisions, missing-data status, projection, areas, and
weights must be visible and auditable. The project must not present a derived
value as complete when the required spatial or temporal coverage is missing.

## User Features: What

- A normal `mmc` collection still requires only a start date and end date.
- After station data are processed, the shared workflow can generate Thiessen
  polygons, station weights, and watershed-average rainfall for that period.
- A user can inspect the area and percentage of the watershed assigned to each
  eligible station.
- A user can see which stations were excluded and why.
- A user can inspect the Thiessen polygons on the dashboard map together with
  the station points and watershed boundary.
- A user can view a watershed-average rainfall hyetograph for the selected
  period.
- A user can compare the Thiessen-weighted series with the simple arithmetic
  station mean.
- A user can download the Thiessen weights, polygon geometry, and watershed
  rainfall time series.
- The derived CSV includes temporal coverage and quality fields so a modeler
  can identify incomplete intervals before simulation.
- The README explains the method, formula, outputs, assumptions, limitations,
  and exact commands.

## Hydrologic Method

### Coordinate reference system

The KML/KMZ inputs use longitude and latitude in WGS 84 (`EPSG:4326`). Area
must not be calculated in geographic degrees or Web Mercator.

Before creating or measuring polygons, transform the station points and
watershed boundary into one documented local projected coordinate reference
system with meter units. The initial implementation should use WGS 84 / UTM
Zone 16N (`EPSG:32616`) after verifying that it covers the MMC study area.

Record the CRS identifier in the weight output and documentation. All area
tests and calculations must use the projected geometry. Geometry exported for
web mapping may be transformed back to `EPSG:4326` after area calculations are
complete.

### Eligible station set

Build one eligible station set for the entire requested period. Do not change
the Thiessen polygons or station weights independently at each timestamp.

The initial eligibility policy should be deterministic:

- the station must exist in the configured station catalog and KMZ assets;
- coordinates must be finite, unique, and inside the supported projected CRS;
- the station must have at least one validated processed rainfall record;
- the station should cover at least 90 percent of the expected nominal
  10-minute intervals for the selected whole-day period;
- stations below the threshold remain in the audit table with
  `eligible = false` and a clear `exclusion_reason`;
- at least three eligible, non-collinear station locations are required for a
  valid watershed Thiessen analysis.

The coverage threshold must be a named project constant or typed configuration
value rather than an unexplained number embedded in dashboard code. The README
and dashboard must display the threshold.

### Thiessen construction

Create a Voronoi/Thiessen diagram from all eligible station points in the
projected CRS. The construction extent must cover the watershed and all input
stations so that finite polygons cover the complete watershed boundary.

Associate each uncut Thiessen polygon with its generating station before
clipping. This is necessary because a station can be outside the watershed
while its nearest-neighbor influence region still intersects the watershed.

Intersect each associated Thiessen polygon with the MMC watershed polygon.
Retain an audit row with zero area when an eligible station has no intersection
with the watershed, but do not give that station a positive rainfall weight.

For station `i`, calculate:

```text
station_area_i = area(thiessen_polygon_i intersect watershed)
weight_i = station_area_i / watershed_area
```

The implementation must verify, within a documented numerical tolerance, that:

- every clipped geometry is valid;
- clipped polygons do not overlap by a meaningful area;
- the union of clipped polygons covers the watershed;
- the sum of clipped areas equals the watershed area; and
- the sum of positive station weights equals `1.0`.

Raise or report an actionable spatial-analysis error when these invariants do
not hold. Do not silently normalize incorrect geometry to hide a gap or
overlap.

### Time alignment

The processed station CSV remains the source of rainfall values. Do not modify
or overwrite those files.

The sources report at a nominal 10-minute cadence, but their saved timestamps
can differ by seconds. For the spatial calculation only, map observations to a
shared 10-minute timestamp label using one documented rounding rule. This is
time alignment, not a new raw-to-processed rainfall transformation.

- Preserve the original processed timestamp in the station CSV.
- Assign each station observation to the nearest 10-minute analysis timestamp.
- Do not sum or average multiple values silently when one station maps more
  than once to the same timestamp; treat that condition as a data-quality
  conflict and report it.
- Create the expected 10-minute timeline from the requested whole-day start and
  end dates.
- Keep all calculations in the project's documented fixed UTC-6 local-time
  representation.

### Areal rainfall calculation

For each aligned timestamp `t`, calculate:

```text
watershed_rainfall_t = sum(weight_i * station_rainfall_i_t)
```

Use the fixed period-level weights. Do not dynamically redistribute a missing
station's weight to the remaining stations without an explicit future method
and documentation change.

For every timestamp, also calculate:

```text
coverage_fraction_t = sum(weight_i for stations with an observation at t)
station_count_t = number of eligible stations with an observation at t
```

The strict initial policy should be:

- when `coverage_fraction` is effectively `1.0`, write the weighted rainfall
  and mark the row `complete`;
- when one or more positive-weight stations are missing, leave the derived
  rainfall empty and mark the row `incomplete`;
- never replace a missing rainfall observation with zero;
- never interpolate rainfall in this sprint; and
- retain the incomplete row so the missing interval is visible to the modeler.

The dashboard may show incomplete intervals, but it must distinguish them from
zero-rainfall intervals. A future explicit gap-filling method may be added only
with its own assumptions, flags, tests, and documentation.

For comparison and quality review, also calculate a simple arithmetic mean
using the same complete timestamps and eligible station set. Label it clearly
as a comparison rather than the recommended areal estimate.

## Spatial Output Files

Write derived products under a separate processed namespace:

```text
data/processed/spatial/
```

Use the selected period in each filename, following the existing project
convention.

### Thiessen weights CSV

Example path:

```text
data/processed/spatial/mmc_thiessen_weights_2026-06-01_to_2026-07-01.csv
```

At minimum, include:

| Field | Meaning |
| --- | --- |
| `station_key` | Stable project station identifier. |
| `station_name` | Human-readable station name. |
| `city` | Auburn or Opelika. |
| `latitude` | Source station latitude in WGS 84. |
| `longitude` | Source station longitude in WGS 84. |
| `eligible` | Whether the station participated in the period-level analysis. |
| `exclusion_reason` | Empty for eligible stations; otherwise the deterministic reason. |
| `temporal_coverage` | Fraction of expected 10-minute intervals represented. |
| `watershed_area_m2` | Total projected MMC watershed area. |
| `thiessen_area_m2` | Watershed area assigned to the station. |
| `thiessen_area_km2` | Assigned area converted to square kilometers. |
| `area_percent` | Percentage of the watershed assigned to the station. |
| `weight` | Fraction used in the areal rainfall calculation. |
| `analysis_crs` | Projected CRS identifier used for area calculations. |

### Thiessen polygons GeoJSON

Example path:

```text
data/processed/spatial/mmc_thiessen_polygons_2026-06-01_to_2026-07-01.geojson
```

Export clipped polygons in `EPSG:4326` for interoperability with the Streamlit
map and common GIS software. Include station identity, eligibility, projected
area, percentage, weight, period, and analysis CRS as feature properties.

The GeoJSON geometry is a derived visualization and exchange artifact. The
projected calculation, not the longitude/latitude GeoJSON area, remains the
source of truth for weights.

### Watershed rainfall CSV

Example path:

```text
data/processed/spatial/mmc_areal_rainfall_2026-06-01_to_2026-07-01.csv
```

At minimum, include:

| Field | Meaning |
| --- | --- |
| `Date_hour` | Shared nominal 10-minute analysis timestamp in fixed UTC-6 local time. |
| `RainIn` | Thiessen-weighted watershed rainfall in inches; empty when incomplete. |
| `simple_mean_RainIn` | Arithmetic station mean in inches for comparison. |
| `coverage_fraction` | Sum of fixed positive weights represented at the timestamp. |
| `stations_used` | Number of eligible stations with observations at the timestamp. |
| `eligible_station_count` | Fixed number of eligible stations for the period. |
| `quality_flag` | `complete` or `incomplete`. |
| `method` | Stable value such as `thiessen`. |

Keep this CSV generic and model-ready. A simulator-specific text format, such
as an EPA SWMM time-series block, should be added only after its exact input
contract is confirmed. The generic CSV is the authoritative derived output for
this sprint.

## Shared Project Logic

Do not implement the method inside Streamlit callbacks or Quarto cells.

- Extend the geospatial boundary with small, typed, testable functions for
  projected geometry, Thiessen construction, clipping, area calculation, and
  invariant checks.
- Add a separate spatial-rainfall analysis module if needed to keep geometry
  operations distinct from timestamp alignment and weighted rainfall.
- Reuse `load_station_points`, `load_watershed_boundary`, station metadata, and
  typed processed rainfall loading.
- Keep output writing at the storage boundary.
- Let the CLI workflow, dashboard, and report call the same spatial-analysis
  functions.
- Keep API access isolated from spatial calculations so unit tests remain
  offline.

Add GeoPandas, Shapely, and required projection support through normal `uv`
project dependencies. Update `pyproject.toml`, `uv.lock`, build metadata, and
the README consistently so a clean clone receives every required runtime
dependency.

## Collection Workflow

Preserve the current CLI input contract:

```bash
uv run mmc --start-date YYYY-MM-DD --end-date YYYY-MM-DD
```

After the station collection and processed CSV writing steps finish, call the
shared spatial workflow for the same requested period.

- Do not ask the CLI user to enter the dates a second time.
- Generate the spatial products from successful, validated processed outputs.
- Report eligible and excluded station counts and the three derived output
  paths in the terminal summary.
- If spatial products cannot be created, retain all station raw and processed
  evidence and show an actionable warning or failure without deleting it.
- Log projection, eligibility, area validation, weight validation, alignment,
  and output decisions without logging secrets or excessive row-level data.

The report must continue to select the most recently collected API period.
Spatial outputs from an older period must not override a newer station
collection when the newer collection cannot produce a valid Thiessen result.

## Dashboard: Watershed Rainfall Page

Add a third page named **Watershed Rainfall** alongside Rainfall Observation
and Event Analysis. It must use the same selected period and saved/collected
records as the other pages.

### Map

Display:

- the OpenStreetMap street base layer;
- the MMC watershed boundary;
- Auburn and Opelika station points using the existing city colors;
- clipped Thiessen polygons with distinct fills and visible boundaries;
- a legend explaining station city, watershed boundary, and Thiessen area;
- tooltips containing station name, city, eligibility, area in square
  kilometers, watershed percentage, temporal coverage, and weight.

Stations excluded for insufficient coverage should remain visible but use a
distinct muted marker and an explanatory tooltip. A zero-area eligible station
should also remain visible and show a zero weight.

### Metrics and tables

Show:

- watershed area in square kilometers;
- eligible and excluded station counts;
- the sum of positive Thiessen weights;
- the period-level coverage threshold;
- complete and incomplete timestamp counts;
- a station table with area, percentage, weight, coverage, eligibility, and
  exclusion reason.

### Charts

Show:

- a bar chart of station Thiessen weights or watershed area percentages;
- a 10-minute hyetograph of Thiessen-weighted watershed rainfall;
- a comparison between Thiessen-weighted rainfall and the simple arithmetic
  mean over the same complete timestamps;
- a clear visual treatment for incomplete intervals rather than displaying
  them as zero rainfall.

### Downloads and errors

Provide download controls for:

- the weights CSV;
- the clipped-polygon GeoJSON; and
- the watershed rainfall CSV.

Use current session data immediately after an API collection; do not require a
second "load saved CSV" action. Errors should identify whether the problem is
missing KMZ geometry, insufficient eligible stations, invalid coordinates,
projection failure, incomplete temporal coverage, polygon coverage, or output
writing.

## Reproducible Report

Update the authoritative Quarto report to consume the shared Thiessen outputs
or spatial-analysis functions for the most recently collected API period.
Do not recreate Voronoi, clipping, weighting, or timestamp-alignment logic in
the `.qmd`.

Expand the report question to compare point-station and watershed-scale
rainfall, for example:

> How does Thiessen weighting change the rainfall time series representing the
> MMC watershed compared with a simple mean of the eligible stations?

The updated report should include:

- the selected period and eligible-station policy;
- a Thiessen map with station labels and watershed boundary;
- a table of station area percentages and weights;
- a watershed rainfall hyetograph;
- a comparison with the arithmetic mean;
- complete and incomplete interval counts;
- a concise hydrologic interpretation and limitations; and
- provenance including the source files, CRS, method, threshold, units,
  project version, and render date.

The report remains automatic: after a new `mmc` API collection, rendering must
use that latest period without a second date setting. Preserve the direct
station charts already approved unless page length requires a clearly
documented layout refinement.

## Documentation

Update the smallest authoritative documents required by the new behavior:

- `README.md` for dependencies, normal workflow, generated files, dashboard
  page, method summary, outputs, and troubleshooting;
- `docs/data-dictionary.md` for every field in the weights and watershed
  rainfall CSVs;
- `docs/index.md` for links to any new detailed spatial-method documentation;
- CLI help if the collection summary or output description changes;
- module and function docstrings for projection, eligibility, polygon,
  weighting, alignment, and failure contracts;
- `CHANGELOG.md` and project version when the sprint is released.

Document clearly that Thiessen rainfall is a spatial estimate based on nearest
station influence, not a radar product and not proof that rainfall was uniform
inside each polygon.

## Tests

All automated tests must remain offline. Add small synthetic geometry and
rainfall fixtures rather than depending on the full live API outputs.

Test at minimum:

- WGS 84 station and watershed inputs are transformed to the configured
  projected CRS;
- projected area is calculated in square meters, not degrees;
- a synthetic station arrangement produces expected Thiessen ownership;
- stations outside a synthetic watershed can still receive clipped area;
- polygons are associated with the correct station before clipping;
- clipped polygons have no meaningful overlaps or gaps;
- clipped areas sum to watershed area within tolerance;
- positive weights sum to `1.0` within tolerance;
- zero-area stations receive zero weight;
- duplicate coordinates, invalid geometry, and fewer than three eligible
  stations fail clearly;
- temporal coverage and station eligibility are calculated correctly;
- timestamp labels align according to the documented 10-minute rule;
- duplicate aligned station timestamps produce a data-quality failure;
- known station values and weights produce the expected areal rainfall;
- a missing positive-weight station produces an incomplete row rather than
  zero rainfall or silent reweighting;
- weights CSV, GeoJSON, and areal rainfall CSV use stable schemas and names;
- dashboard helpers expose map properties, metrics, chart data, and downloads;
- CLI and dashboard call shared spatial logic rather than duplicate it; and
- the Quarto report imports shared spatial behavior.

## Verification

Run the complete project checks:

```bash
uv sync
uv run python -m pytest
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv build
quarto render reports/mmc-rainfall-report.qmd --to pdf
```

Also perform a manual dashboard check:

```bash
uv run streamlit run src/mmc_watershed_data/dashboard.py
```

Verify one realistic saved period end to end:

- station collection completes or clearly reports source failures;
- the spatial workflow lists eligible and excluded stations;
- the polygons cover the MMC watershed without visible gaps or overlaps;
- table areas and percentages agree with map tooltips;
- positive weights sum to one;
- complete timestamps produce reproducible weighted rainfall;
- incomplete timestamps are not displayed as zero;
- all three download artifacts open correctly; and
- the rendered PDF is inspected visually and corrected through source changes.

## Acceptance Criteria

- The existing `mmc` date-range workflow remains intact.
- The most recently collected period controls the spatial analysis, dashboard,
  and report.
- Thiessen geometry uses a documented projected CRS suitable for area.
- Every polygon is traceable to one configured station.
- Clipped areas cover the watershed and weights sum to one within tolerance.
- Station eligibility and exclusions are deterministic and visible.
- Missing station observations are not replaced with zero or silently
  reweighted.
- Weights CSV, polygon GeoJSON, and areal rainfall CSV are generated with
  documented schemas.
- The Watershed Rainfall dashboard page includes the map, weights, metrics,
  hyetograph, mean comparison, quality status, and downloads.
- The Quarto report uses shared spatial logic and remains automatic for the
  latest API period.
- README, data dictionary, docstrings, tests, changelog, and version are current
  for the released behavior.
- A clean clone can restore dependencies and reproduce the tested spatial
  outputs without a live API by using fixtures.
- No source, fixture, output, report, metadata, or log contains a secret.

## Out Of Scope

- Radar rainfall, satellite precipitation, or gridded weather products.
- Kriging, inverse-distance weighting, spline interpolation, or calibrated
  bias correction.
- Dynamic per-timestamp Thiessen polygons or silent redistribution of missing
  station weights.
- Automatic rainfall interpolation or gap filling.
- Editing station coordinates or the watershed boundary from the dashboard.
- Changing Auburn or Opelika source endpoints and processing rules.
- Real-time streaming, scheduled collection, cloud deployment, or database
  storage.
- Automatic hydrologic-model calibration or simulation execution.
- A simulator-specific rainfall format before its exact required schema is
  confirmed.
- Rewriting completed sprint specifications.
