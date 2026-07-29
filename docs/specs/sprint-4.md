# Sprint 04: Streamlit Rainfall Dashboard

MMC Watershed Data is a `uv`-managed Python command-line tool for collecting
rainfall data from Auburn and Opelika. This sprint adds a Streamlit dashboard
that reuses the collection, validation, storage, and analysis guarantees built
for the command-line tool.

## Context

The dashboard should not become a second implementation of the data pipeline.
It should call the shared workflow from Sprint 3, use the same Pydantic
validation, preserve the same raw and processed evidence, and display trusted
processed records. The project already contains the geographic KMZ assets:

- `assets/geospatial/stations/auburn_stations.kmz`;
- `assets/geospatial/stations/opelika_stations.kmz`;
- `assets/geospatial/basin/mmc_boundary.kmz`.

## User Features: What

- A user can open a Streamlit dashboard locally.
- A user can select a start date and end date for the rainfall data.
- A user can collect or load data for all Auburn and Opelika stations for that period.
- A user can see Auburn and Opelika stations on the same map with different colors.
- The station map uses a standard street-map base layer, not satellite imagery.
- A user can see the Moores Mill Creek basin boundary on the map.
- A user can select which stations should appear in rainfall charts.
- A user can see one rainfall bar chart per selected station.
- A user can inspect a station's rainfall values over the selected period.
- A user can open a separate event-analysis page.
- A user can see the number of detected rainfall events.
- A user can see the event with the longest duration.
- A user can see total precipitation for each event.
- A user can see which stations recorded each regional event.
- A user can download or locate the raw JSON, raw CSV, and processed CSV evidence created for the selected period.
- A user receives a clear message when an API request or validation step fails.
- The README explains how to start the dashboard and describes its new features.

## Pages

### Rainfall Observation

This page should contain:

- start-date and end-date controls;
- a button to load or collect the selected period;
- a station map;
- a station selector grouped by city;
- one rainfall bar chart for every selected station;
- a compact summary showing selected stations, record counts, and total rainfall.

Auburn stations should use one consistent map color and Opelika stations a
second color. The map should use a readable street-map tile layer such as
OpenStreetMap. The basin boundary should be rendered as a separate line or
polygon layer with a clear legend.

### Event Analysis

This page should use the same selected period and processed data as the rainfall
page. It should contain:

- total number of detected events;
- event start and end times;
- event duration;
- total precipitation summed across the event;
- stations that recorded positive rainfall during the event;
- a ranking of events by duration and total precipitation;
- an optional event timeline or bar chart for comparison.

## Event Definition

The first implementation should use a documented, deterministic rule:

- A positive processed `RainIn` value indicates rainfall at a station.
- Consecutive positive observations form a station event.
- A zero or missing observation closes the station event.
- Regional events are formed by merging station events that overlap or are separated by no more than a documented tolerance.
- The initial tolerance should be one expected observation interval, with the value made explicit because Auburn and Opelika may report at different frequencies.
- Event precipitation is the sum of interval rainfall values, not the final cumulative counter value.
- A station is listed for an event when it contributes at least one positive interval.

If the source frequencies make this rule unreliable for a selected period, the
dashboard should show the source interval information and state the limitation
instead of silently pretending the stations have identical sampling rates.

## Implementation Plan: How

- Add Streamlit and a lightweight map component such as Folium with `streamlit-folium`.
- Use a street-map tile layer such as OpenStreetMap as the default map base.
- Keep the dashboard entry point separate from the CLI entry point.
- Reuse the Sprint 3 shared workflow for date validation, collection, and processing.
- Save raw JSON, raw CSV, and processed CSV when the dashboard performs a collection.
- Allow the dashboard to read already-generated processed CSV files when appropriate.
- Keep network access out of page-rendering helpers.
- Parse KMZ files by reading their embedded `doc.kml` content.
- Extract station points and the basin geometry into map-ready structures.
- Add a small geospatial module so KMZ parsing can be unit tested without opening the browser.
- Keep map colors and labels centralized rather than embedding them throughout the page.
- Use the processed `RainIn` field for rainfall charts and event analysis.
- Keep event detection as pure functions that accept records and return typed event records.
- Test the dashboard's analysis functions with fixtures and mocks rather than live APIs.
- Configure dashboard logging through the same logging module used by `mmc`.
- Show user-friendly errors in the page while retaining technical details in logs.
- Update `README.md` with dashboard installation and launch instructions, page
  descriptions, map layers, station selection, chart behavior, and event definitions.

## Suggested Additional Metrics

The first dashboard release could also include:

- total rainfall by station for the selected period;
- maximum interval rainfall by station;
- date and time of each station's maximum interval;
- station coverage or missing-record count;
- a map tooltip containing city, station name, station ID, and total rainfall.

These metrics should remain derived from processed records and should not change
the raw-to-processed rules.

## Tests

Add or update tests for:

- KMZ extraction of station points;
- KMZ extraction of the basin boundary;
- city-specific map colors and station labels;
- date-range and station-selection behavior;
- loading valid processed fixtures;
- rainfall event detection and event merging;
- event duration and precipitation totals;
- station participation in regional events;
- mocked collection calls from the dashboard workflow;
- user-facing handling of API and validation failures.

## Verification

```bash
uv run python -m unittest discover -s tests
uv run streamlit run src/mmc_watershed_data/dashboard.py
uv build
```

## Documentation

Update `README.md` to document:

- the Streamlit dependency and dashboard launch command;
- the Rainfall Observation and Event Analysis pages;
- the date-range and station-selection controls;
- the street-map base layer, city colors, KMZ assets, and basin boundary;
- the rainfall charts and additional summary metrics;
- the definition of a station event and a regional event;
- how dashboard collection reuses the CLI workflow and saves evidence files.

## Out Of Scope

- Real-time streaming updates.
- Scheduled or background downloads.
- Database storage.
- Editing KMZ files from the dashboard.
- Predictive rainfall modeling.
- Changing station metadata through the browser.
