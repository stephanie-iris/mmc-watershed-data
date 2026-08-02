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
