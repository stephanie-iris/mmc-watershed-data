"""Streamlit dashboard for station, event, and watershed rainfall analysis."""

from __future__ import annotations

from datetime import date, timedelta
import logging
from pathlib import Path
from typing import Iterable

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from mmc_watershed_data.analysis import (
    RainfallEvent,
    RainfallRecord,
    detect_events,
    load_rainfall_records,
)
from mmc_watershed_data.config import project_root
from mmc_watershed_data.geospatial import (
    StationPoint,
    load_station_points,
    load_watershed_boundary,
)
from mmc_watershed_data.logging_config import configure_logging
from mmc_watershed_data.spatial import (
    SpatialAnalysis,
    SpatialAnalysisError,
    create_spatial_products,
    spatial_download_bytes,
    spatial_geojson,
)
from mmc_watershed_data.stations import AUBURN_STATIONS, OPELIKA_STATIONS
from mmc_watershed_data.workflow import (
    CollectionRequest,
    CollectionResult,
    collect_rainfall,
)


logger = logging.getLogger(__name__)
ALL_STATIONS = AUBURN_STATIONS + OPELIKA_STATIONS
CITY_COLORS = {"Auburn": "#1f77b4", "Opelika": "#d62728"}


def main() -> None:
    """Render the Streamlit pages using the shared collection and analysis code."""

    st.set_page_config(page_title="MMC Watershed Rainfall Dashboard", layout="wide")
    configure_logging(verbose=True, log_file=None)
    root = project_root()

    st.title("MMC Watershed Rainfall Dashboard")
    st.caption("Moores Mill Creek | Auburn and Opelika rainfall data")

    request, selected_keys, action = _render_controls()
    if action == "collect":
        _collect_for_dashboard(request, root)
    elif action == "load":
        _load_saved_for_dashboard(request, root)

    _show_dashboard_notice()

    page = st.sidebar.radio(
        "Dashboard page",
        ("Rainfall Observation", "Event Analysis", "Watershed Rainfall"),
    )
    records = st.session_state.get("rainfall_records", [])
    selected_records = [
        record for record in records if record.station_key in selected_keys
    ]

    if not records:
        st.info(
            "Select a date range and collect data or load an existing processed period."
        )
        return

    if page == "Rainfall Observation":
        _render_observation(root, selected_keys, selected_records)
    elif page == "Event Analysis":
        _render_event_analysis(selected_records)
    else:
        _render_watershed_rainfall(root)


def _render_controls() -> tuple[CollectionRequest, set[str], str | None]:
    """Render date and station controls and return the current user choices."""

    today = date.today()
    with st.sidebar:
        st.header("Data selection")
        start_date = st.date_input("Start date", value=today - timedelta(days=7))
        end_date = st.date_input("End date", value=today)
        if start_date > end_date:
            st.error("End date must be on or after the start date.")
            end_date = start_date

        options = [station.key for station in ALL_STATIONS]
        labels = {
            station.key: f"{station.city}: {station.name}" for station in ALL_STATIONS
        }
        selected = st.multiselect(
            "Stations to analyze",
            options=options,
            default=options,
            format_func=lambda key: labels[key],
        )
        collect_clicked = st.button(
            "Collect from APIs", type="primary", use_container_width=True
        )
        load_clicked = st.button("Load saved CSVs", use_container_width=True)

    request = CollectionRequest(start_date=start_date, end_date=end_date)
    action = "collect" if collect_clicked else "load" if load_clicked else None
    return request, set(selected), action


def _collect_for_dashboard(request: CollectionRequest, root: Path) -> None:
    """Collect a period, store typed records, and request an immediate refresh."""

    try:
        with st.spinner("Collecting, validating, and saving rainfall data..."):
            result = collect_rainfall(request, root)
            records = _records_from_results(result)
        _store_dashboard_data(
            request,
            records,
            result,
            result.spatial_analysis,
            result.spatial_failure,
        )
        if result.station_failures or result.spatial_failure:
            details = (
                f" Spatial analysis: {result.spatial_failure}"
                if result.spatial_failure
                else ""
            )
            _set_dashboard_notice(
                "warning",
                f"Loaded new station data; {len(result.station_failures)} station(s) "
                f"could not be loaded.{details}",
            )
        else:
            _set_dashboard_notice(
                "success", f"Loaded {len(records)} processed observations."
            )
        st.rerun()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Dashboard collection failed.")
        st.error(f"The selected data could not be collected: {exc}")


def _load_saved_for_dashboard(request: CollectionRequest, root: Path) -> None:
    """Load matching processed CSVs and request an immediate chart refresh."""

    records: list[RainfallRecord] = []
    paths: list[Path] = []
    for station in ALL_STATIONS:
        path = (
            root
            / "data"
            / "processed"
            / station.source
            / f"{station.key}_{request.start_date.isoformat()}_to_"
            f"{request.end_date.isoformat()}_processed.csv"
        )
        if path.exists():
            records.extend(load_rainfall_records(path))
            paths.append(path)
    if not records:
        st.error("No processed CSVs were found for the selected period.")
        return
    spatial: SpatialAnalysis | None = None
    spatial_failure: str | None = None
    try:
        spatial = create_spatial_products(
            root, records, request.start_date, request.end_date
        )
    except (OSError, ValueError, SpatialAnalysisError) as exc:
        spatial_failure = str(exc)
    _store_dashboard_data(request, records, paths, spatial, spatial_failure)
    _set_dashboard_notice(
        "success", f"Loaded {len(records)} saved processed observations."
    )
    st.rerun()


def _records_from_results(result: CollectionResult) -> list[RainfallRecord]:
    """Load typed records from the successful processed station outputs."""

    records: list[RainfallRecord] = []
    for station_result in result.station_results:
        records.extend(load_rainfall_records(station_result.processed_path))
    return records


def _store_dashboard_data(
    request: CollectionRequest,
    records: list[RainfallRecord],
    evidence: CollectionResult | list[Path],
    spatial_analysis: SpatialAnalysis | None,
    spatial_failure: str | None,
) -> None:
    """Store records and evidence paths in Streamlit session state."""

    st.session_state["rainfall_request"] = request
    st.session_state["rainfall_records"] = records
    st.session_state["rainfall_evidence"] = evidence
    st.session_state["spatial_analysis"] = spatial_analysis
    st.session_state["spatial_failure"] = spatial_failure


def _render_observation(
    root: Path,
    selected_keys: set[str],
    records: list[RainfallRecord],
) -> None:
    """Render station selection, map, summaries, and rainfall charts."""

    st.header("Rainfall Observation")
    selected_stations = [
        station for station in ALL_STATIONS if station.key in selected_keys
    ]
    if not selected_stations:
        st.warning("Select at least one station in the sidebar.")
        return

    try:
        station_points = load_station_points(root)
        boundary = load_watershed_boundary(root)
        st_folium(
            _build_map(station_points, boundary), height=500, use_container_width=True
        )
    except (OSError, ValueError, KeyError) as exc:
        logger.exception("Could not render the geospatial layers.")
        st.error(f"The station map could not be loaded: {exc}")

    totals = _station_totals(records)
    metric_columns = st.columns(3)
    metric_columns[0].metric("Selected stations", len(selected_stations))
    metric_columns[1].metric("Observations", len(records))
    metric_columns[2].metric("Rainfall total (in)", f"{sum(totals.values()):.3f}")

    st.subheader("Rainfall by station")
    for station in selected_stations:
        station_records = sorted(
            [record for record in records if record.station_key == station.key],
            key=lambda record: record.timestamp,
        )
        st.markdown(f"**{station.city} | {station.name}**")
        if not station_records:
            st.info("No observations for this station in the selected period.")
            continue
        chart_data = pd.DataFrame(
            {
                "timestamp": [record.timestamp for record in station_records],
                "RainIn": [record.rain_in for record in station_records],
            }
        ).set_index("timestamp")
        st.bar_chart(chart_data, y="RainIn", use_container_width=True)
        st.caption(f"Total: {totals.get(station.key, 0.0):.3f} inches")

    _render_evidence_links()


def _render_event_analysis(records: list[RainfallRecord]) -> None:
    """Render event counts, rankings, durations, totals, and station lists."""

    st.header("Event Analysis")
    st.caption(
        "Positive observations are grouped using a one-hour station and regional tolerance."
    )
    events = detect_events(records)
    if not events:
        st.info(
            "No positive-rainfall events were found for the selected stations and period."
        )
        return

    longest = max(events, key=lambda event: event.duration_minutes)
    total_rain = sum(event.total_rain_in for event in events)
    metrics = st.columns(3)
    metrics[0].metric("Rainfall events", len(events))
    metrics[1].metric("Longest duration", _format_duration(longest))
    metrics[2].metric("Total event rainfall (in)", f"{total_rain:.3f}")

    rows = [_event_row(index, event) for index, event in enumerate(events, start=1)]
    st.subheader("Detected events")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader("Events by total precipitation")
    chart = pd.DataFrame(
        {
            "event": [row["event"] for row in rows],
            "total_rain_in": [row["total_rain_in"] for row in rows],
        }
    ).set_index("event")
    st.bar_chart(chart, y="total_rain_in", use_container_width=True)


def _render_watershed_rainfall(root: Path) -> None:
    """Render Thiessen geometry, weights, rainfall, quality, and downloads."""

    st.header("Watershed Rainfall")
    st.caption(
        "Thiessen polygons convert eligible station observations into one "
        "area-weighted rainfall series for the Moores Mill Creek watershed."
    )
    analysis = st.session_state.get("spatial_analysis")
    if not isinstance(analysis, SpatialAnalysis):
        request = st.session_state.get("rainfall_request")
        records = st.session_state.get("rainfall_records")
        if isinstance(request, CollectionRequest) and isinstance(records, list):
            try:
                with st.spinner("Building Thiessen polygons for the loaded period..."):
                    analysis = create_spatial_products(
                        root,
                        records,
                        request.start_date,
                        request.end_date,
                    )
                st.session_state["spatial_analysis"] = analysis
                st.session_state["spatial_failure"] = None
            except (OSError, ValueError, SpatialAnalysisError) as exc:
                st.session_state["spatial_failure"] = str(exc)
    if not isinstance(analysis, SpatialAnalysis):
        failure = st.session_state.get("spatial_failure")
        st.error(
            "Watershed rainfall is unavailable for this period. "
            + (str(failure) if failure else "Collect or load a processed period first.")
        )
        return

    complete = sum(row.quality_flag == "complete" for row in analysis.rainfall)
    incomplete = len(analysis.rainfall) - complete
    positive_weight_sum = sum(row.weight for row in analysis.weights if row.weight > 0)
    metrics = st.columns(6)
    metrics[0].metric("Watershed area", f"{analysis.watershed_area_m2 / 1e6:.2f} km2")
    metrics[1].metric("Eligible stations", analysis.eligible_count)
    metrics[2].metric("Excluded stations", analysis.excluded_count)
    metrics[3].metric("Weight sum", f"{positive_weight_sum:.6f}")
    metrics[4].metric("Complete intervals", complete)
    metrics[5].metric("Incomplete intervals", incomplete)
    st.caption(
        f"Period eligibility requires at least {analysis.coverage_threshold:.0%} "
        "of the expected 10-minute observations. "
        f"{sum(row.aggregated_observation_count for row in analysis.weights)} "
        "additional source observation(s) were summed into shared labels."
    )

    try:
        points = load_station_points(root)
        boundary = load_watershed_boundary(root)
        st.subheader("Thiessen polygons and monitoring stations")
        st_folium(
            _build_spatial_map(points, boundary, analysis),
            height=560,
            use_container_width=True,
        )
    except (OSError, ValueError, KeyError) as exc:
        logger.exception("Could not render the Thiessen map.")
        st.error(f"The Thiessen map could not be loaded: {exc}")

    weight_rows = [
        {
            "station": row.station_name,
            "city": row.city,
            "eligible": row.eligible,
            "coverage": round(row.temporal_coverage, 3),
            "area_km2": round(row.thiessen_area_km2, 4),
            "area_percent": round(row.area_percent, 3),
            "weight": round(row.weight, 6),
            "aggregated_observations": row.aggregated_observation_count,
            "exclusion_reason": row.exclusion_reason,
        }
        for row in analysis.weights
    ]
    st.subheader("Station influence and eligibility")
    st.dataframe(pd.DataFrame(weight_rows), use_container_width=True, hide_index=True)

    positive_keys = {
        weight.station_key for weight in analysis.weights if weight.weight > 0
    }
    positive_weights = pd.DataFrame(
        [
            row
            for row, weight in zip(weight_rows, analysis.weights, strict=True)
            if weight.station_key in positive_keys
        ]
    ).set_index("station")
    st.subheader("Thiessen area percentage")
    st.bar_chart(positive_weights, y="area_percent", use_container_width=True)

    rainfall = pd.DataFrame(
        {
            "timestamp": [row.timestamp for row in analysis.rainfall],
            "Thiessen weighted": [row.rain_in for row in analysis.rainfall],
            "quality": [row.quality_flag for row in analysis.rainfall],
        }
    ).set_index("timestamp")
    st.subheader("Watershed rainfall hyetograph")
    st.bar_chart(rainfall, y="Thiessen weighted", use_container_width=True)
    if incomplete:
        st.warning(
            f"{incomplete} interval(s) are incomplete and remain blank; missing "
            "station weight was not redistributed or replaced with zero."
        )

    weights_bytes, geojson_bytes, rainfall_bytes = spatial_download_bytes(analysis)
    period = f"{analysis.start_date.isoformat()}_to_{analysis.end_date.isoformat()}"
    downloads = st.columns(3)
    downloads[0].download_button(
        "Download weights CSV",
        weights_bytes,
        f"mmc_thiessen_weights_{period}.csv",
        "text/csv",
        use_container_width=True,
    )
    downloads[1].download_button(
        "Download polygons GeoJSON",
        geojson_bytes,
        f"mmc_thiessen_polygons_{period}.geojson",
        "application/geo+json",
        use_container_width=True,
    )
    downloads[2].download_button(
        "Download watershed rainfall CSV",
        rainfall_bytes,
        f"mmc_areal_rainfall_{period}.csv",
        "text/csv",
        use_container_width=True,
    )


def _build_spatial_map(
    station_points: Iterable[StationPoint],
    boundary: tuple[tuple[float, float], ...],
    analysis: SpatialAnalysis,
) -> folium.Map:
    """Build the street map with audited Thiessen polygons and station status."""

    points = list(station_points)
    center = (
        sum(latitude for latitude, _longitude in boundary) / len(boundary),
        sum(longitude for _latitude, longitude in boundary) / len(boundary),
    )
    station_map = folium.Map(location=center, zoom_start=12, tiles="OpenStreetMap")
    polygon_layer = folium.FeatureGroup(name="Clipped Thiessen polygons", show=True)
    palette = [
        "#e9c46a",
        "#f4a261",
        "#2a9d8f",
        "#8ab17d",
        "#457b9d",
        "#e76f51",
        "#a8dadc",
        "#bc6c25",
        "#6d597a",
    ]
    colors = {
        weight.station_key: palette[index % len(palette)]
        for index, weight in enumerate(analysis.weights)
    }
    for feature in spatial_geojson(analysis)["features"]:
        properties = feature["properties"]
        station_key = str(properties["station_key"])
        folium.GeoJson(
            feature,
            style_function=lambda _feature, color=colors[station_key]: {
                "color": color,
                "fillColor": color,
                "weight": 2,
                "fillOpacity": 0.28,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=[
                    "station_name",
                    "city",
                    "eligible",
                    "thiessen_area_km2",
                    "area_percent",
                    "temporal_coverage",
                    "weight",
                    "aggregated_observation_count",
                ],
                aliases=[
                    "Station",
                    "City",
                    "Eligible",
                    "Area (km2)",
                    "Watershed (%)",
                    "Temporal coverage",
                    "Weight",
                    "Aggregated observations",
                ],
            ),
        ).add_to(polygon_layer)
    polygon_layer.add_to(station_map)

    watershed_layer = folium.FeatureGroup(name="MMC watershed boundary", show=True)
    folium.Polygon(
        locations=boundary,
        color="#2f6b3b",
        weight=4,
        fill=False,
        tooltip="Moores Mill Creek watershed boundary",
    ).add_to(watershed_layer)
    watershed_layer.add_to(station_map)

    status_by_key = {weight.station_key: weight for weight in analysis.weights}
    status_layer = folium.FeatureGroup(name="Station eligibility", show=True)
    for point in points:
        weight = status_by_key[point.station_key]
        color = CITY_COLORS[point.city] if weight.eligible else "#777777"
        reason = weight.exclusion_reason or "eligible"
        folium.CircleMarker(
            location=(point.latitude, point.longitude),
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            tooltip=(
                f"{point.city} | {point.station_name} | {reason} | "
                f"coverage {weight.temporal_coverage:.1%} | "
                f"weight {weight.weight:.4f}"
            ),
        ).add_to(status_layer)
    status_layer.add_to(station_map)
    map_latitudes = [latitude for latitude, _longitude in boundary] + [
        point.latitude for point in points
    ]
    map_longitudes = [longitude for _latitude, longitude in boundary] + [
        point.longitude for point in points
    ]
    station_map.fit_bounds(
        [
            [
                min(map_latitudes),
                min(map_longitudes),
            ],
            [
                max(map_latitudes),
                max(map_longitudes),
            ],
        ]
    )
    folium.LayerControl().add_to(station_map)
    legend = """
    <div style="position: fixed; bottom: 24px; left: 24px; z-index: 9999;
         background: white; padding: 10px 12px; border: 1px solid #999;
         border-radius: 4px; font-size: 13px;">
      <b>Watershed rainfall map</b><br>
      <span style="color: #1f77b4;">&#9679;</span> Eligible Auburn station<br>
      <span style="color: #d62728;">&#9679;</span> Eligible Opelika station<br>
      <span style="color: #777777;">&#9679;</span> Excluded station<br>
      <span style="color: #2f6b3b;">&#9644;</span> MMC watershed boundary<br>
      <span style="color: #c8953d;">&#9632;</span> Clipped Thiessen area
    </div>
    """
    station_map.get_root().html.add_child(folium.Element(legend))  # type: ignore[attr-defined]
    return station_map


def _build_map(
    station_points: Iterable[StationPoint],
    boundary: tuple[tuple[float, float], ...],
) -> folium.Map:
    """Build an OpenStreetMap view with city-colored stations and boundary."""

    points = list(station_points)
    center = (
        sum(point.latitude for point in points) / len(points),
        sum(point.longitude for point in points) / len(points),
    )
    station_map = folium.Map(location=center, zoom_start=11, tiles="OpenStreetMap")
    watershed_layer = folium.FeatureGroup(name="MMC watershed boundary", show=True)
    auburn_layer = folium.FeatureGroup(name="Auburn stations", show=True)
    opelika_layer = folium.FeatureGroup(name="Opelika stations", show=True)
    folium.Polygon(
        locations=boundary,
        color="#2ca02c",
        weight=3,
        fill=False,
        tooltip="Moores Mill Creek watershed boundary",
    ).add_to(watershed_layer)
    watershed_layer.add_to(station_map)
    for point in points:
        folium.CircleMarker(
            location=(point.latitude, point.longitude),
            radius=7,
            color=CITY_COLORS[point.city],
            fill=True,
            fill_color=CITY_COLORS[point.city],
            fill_opacity=0.85,
            tooltip=f"{point.city} | {point.station_name}",
        ).add_to(auburn_layer if point.city == "Auburn" else opelika_layer)
    auburn_layer.add_to(station_map)
    opelika_layer.add_to(station_map)
    folium.LayerControl().add_to(station_map)
    legend = """
    <div style="position: fixed; bottom: 24px; left: 24px; z-index: 9999;
         background: white; padding: 10px 12px; border: 1px solid #999;
         border-radius: 4px; font-size: 13px;">
      <b>MMC Map</b><br>
      <span style="color: #1f77b4;">&#9679;</span> Auburn stations<br>
      <span style="color: #d62728;">&#9679;</span> Opelika stations<br>
      <span style="color: #2ca02c;">&#9644;</span> Watershed boundary
    </div>
    """
    station_map.get_root().html.add_child(folium.Element(legend))  # type: ignore[attr-defined]
    return station_map


def _station_totals(records: Iterable[RainfallRecord]) -> dict[str, float]:
    """Sum processed interval rainfall by station key."""

    totals: dict[str, float] = {}
    for record in records:
        totals[record.station_key] = (
            totals.get(record.station_key, 0.0) + record.rain_in
        )
    return totals


def _event_row(index: int, event: RainfallEvent) -> dict[str, object]:
    """Convert one typed event into a dashboard table row."""

    return {
        "event": index,
        "start": event.start.strftime("%Y-%m-%d %H:%M"),
        "end": event.end.strftime("%Y-%m-%d %H:%M"),
        "duration_hours": round(event.duration_minutes / 60, 2),
        "total_rain_in": round(event.total_rain_in, 3),
        "stations": ", ".join(event.station_names),
    }


def _format_duration(event: RainfallEvent) -> str:
    """Format an event duration in hours for a compact metric display."""

    return f"{event.duration_minutes / 60:.2f} h"


def _render_evidence_links() -> None:
    """Display the raw and processed paths associated with the current data."""

    evidence = st.session_state.get("rainfall_evidence")
    if isinstance(evidence, CollectionResult):
        with st.expander("Saved evidence files"):
            for result in evidence.station_results:
                st.write(str(result.raw_json_path))
                st.write(str(result.raw_csv_path))
                st.write(str(result.processed_path))
    elif isinstance(evidence, list):
        with st.expander("Loaded processed files"):
            for path in evidence:
                st.write(str(path))


def _set_dashboard_notice(level: str, message: str) -> None:
    """Queue a success or warning message for the next Streamlit render."""

    st.session_state["dashboard_notice"] = (level, message)


def _show_dashboard_notice() -> None:
    """Render and clear the queued dashboard notice, if one exists."""

    notice = st.session_state.pop("dashboard_notice", None)
    if notice is None:
        return
    level, message = notice
    if level == "warning":
        st.warning(message)
    else:
        st.success(message)


if __name__ == "__main__":
    main()
