# MMC Rainfall Data Dictionary

The processed CSV is the stable, validated view used by the dashboard, event
analysis, and reproducible report. Each row represents one observation from one
station during the requested date range.

## Processed Fields

| Field | Type and format | Unit or values | Meaning, source, and transformation |
| --- | --- | --- | --- |
| `city` | string | `Auburn` or `Opelika` | City owning the station. Added by the project from the station catalog. |
| `station_key` | string | Stable project key | Project identifier used to match API results, files, map points, and charts. |
| `station_name` | string | Station display name | Human-readable station name from the project station catalog. |
| `Date_hour` | datetime string, `YYYY-MM-DD HH:MM:SS` | Local fixed UTC-6 representation | Observation timestamp. Auburn epoch milliseconds are converted to UTC and represented at UTC-6; Opelika provider date/time text is parsed and retained in the source's usable timestamp form. |
| `RainIn` | decimal number | Inches per processed interval | Processed interval rainfall. Auburn keeps the source station rain amount. Opelika derives the difference between consecutive cumulative `RainToday` values. |

## Source and Provenance

- Auburn source: [LI-COR timeseries endpoint](https://www.licor.cloud/api/v2/timeseriesdata), selected by the dashboard UUID and station channel identifier.
- Opelika source: [ThorArchive weather packets endpoint](https://360.thormobile.net/thorcloud/api/weatherpacketsbyinterval), selected by station identifier and requested date range.
- Station names, keys, and identifiers are defined in
  `src/mmc_watershed_data/stations.py`.
- The raw JSON response is saved before processed validation and remains the
  evidence of what the provider returned. A raw CSV extract is also saved for
  inspection, but its columns follow each provider's response shape.

## Missing and Invalid Values

The project does not impute missing required station identity, timestamp, or
rainfall values. Pydantic validation stops a source-specific response that
cannot be safely interpreted. A missing or malformed row should be diagnosed
from the corresponding raw JSON evidence.

For Opelika, a negative difference in cumulative `RainToday` is treated as a
counter reset and the current cumulative value becomes the interval amount.
This prevents a reset from creating negative rainfall. Empty source responses
are preserved as raw evidence and produce an empty processed CSV when the
response shape is valid.

## Analysis Conventions

The dashboard and report use `RainIn` in inches. A positive `RainIn` value is a
rainfall observation. Consecutive positive observations are grouped into a
station event, and nearby station events are merged into a regional event using
the documented one-hour tolerance. Event totals are sums of processed interval
values, not cumulative counters.

## Thiessen Weights Fields

The period-level weights file under `data/processed/spatial/` audits every
configured station, including excluded and zero-area stations.

| Field | Type, unit, or values | Meaning and transformation |
| --- | --- | --- |
| `station_key` | string | Stable project station identifier from the station catalog. |
| `station_name` | string | Human-readable configured station name. |
| `city` | `Auburn` or `Opelika` | City associated with the station. |
| `latitude` | decimal degrees, WGS 84 | Latitude read from the tracked station KMZ. Must be finite and unique with longitude. |
| `longitude` | decimal degrees, WGS 84 | Longitude read from the tracked station KMZ. Must be finite and unique with latitude. |
| `eligible` | boolean text | Whether the station met coordinate, observation, and 90% temporal-coverage requirements. |
| `exclusion_reason` | string or empty | Deterministic reason an ineligible station did not participate. Empty when eligible. |
| `temporal_coverage` | fraction, 0 to 1 | Unique aligned station intervals divided by all expected 10-minute intervals in the whole-day period. |
| `watershed_area_m2` | square meters | MMC area measured after projection to `EPSG:32616`. |
| `thiessen_area_m2` | square meters | Station Voronoi region intersected with the projected MMC watershed. Zero is retained. |
| `thiessen_area_km2` | square kilometers | `thiessen_area_m2 / 1,000,000`. |
| `area_percent` | percent | Percentage of projected watershed area assigned to the station. |
| `weight` | fraction, 0 to 1 | `thiessen_area_m2 / watershed_area_m2`; positive weights sum to one within tolerance. |
| `analysis_crs` | `EPSG:32616` | Meter-based CRS used for all authoritative area calculations. |
| `aggregated_observation_count` | nonnegative integer | Additional distinct processed observations summed into an already occupied nominal 10-minute label for this station. |

The matching GeoJSON contains the same identity, eligibility, area, period,
and weight properties. Its clipped polygon geometry is transformed back to
`EPSG:4326` for mapping; areas must not be recalculated from geographic degrees.

## Watershed Rainfall Fields

The model-ready areal rainfall CSV contains every expected 10-minute label in
the selected inclusive whole-day period.

| Field | Type, unit, or values | Meaning and transformation |
| --- | --- | --- |
| `Date_hour` | `YYYY-MM-DD HH:MM:SS`, fixed UTC-6 local representation | Shared nominal label. Source timestamps are rounded to the nearest 10 minutes for this analysis only; exact ties round forward. |
| `RainIn` | decimal inches or empty | Sum of fixed Thiessen weight times station interval rain. Empty unless every positive weight is represented. |
| `simple_mean_RainIn` | decimal inches or empty | Arithmetic mean across the same positive-weight stations and complete timestamp; comparison only. |
| `coverage_fraction` | fraction, 0 to 1 | Sum of positive fixed weights with an observation at the timestamp. |
| `stations_used` | integer | Positive-weight eligible stations represented at the timestamp. |
| `eligible_station_count` | integer | All eligible period stations, including any eligible zero-area station. |
| `quality_flag` | `complete` or `incomplete` | `complete` only when the represented positive weights sum to one within tolerance. |
| `method` | `thiessen` | Stable identifier for the spatial method. |

When distinct Auburn or Opelika timestamps map to one analysis label, their
processed interval values are summed to preserve rainfall volume. Opelika
increments were already derived from successive cumulative `RainToday`
readings. Exact duplicates with an identical timestamp and value are retained
once. Equal timestamps with divergent values exclude that station with
`conflicting duplicate timestamp values` as the reason. Every aggregation is
counted in the weights audit and logged; station CSVs are never overwritten.

Missing station observations are not treated as zero, interpolated, or
reweighted. Incomplete rows are retained as evidence of the model-input gap.
