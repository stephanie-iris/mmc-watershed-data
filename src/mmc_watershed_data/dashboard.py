"""Streamlit dashboard for rainfall observation and event analysis."""

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
    """Render the dashboard and keep all collection logic in the shared workflow."""

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

    page = st.sidebar.radio("Dashboard page", ("Rainfall Observation", "Event Analysis"))
    records = st.session_state.get("rainfall_records", [])
    selected_records = [record for record in records if record.station_key in selected_keys]

    if not records:
        st.info("Select a date range and collect data or load an existing processed period.")
        return

    if page == "Rainfall Observation":
        _render_observation(root, selected_keys, selected_records)
    else:
        _render_event_analysis(selected_records)


def _render_controls() -> tuple[CollectionRequest, set[str], str | None]:
    today = date.today()
    with st.sidebar:
        st.header("Data selection")
        start_date = st.date_input("Start date", value=today - timedelta(days=7))
        end_date = st.date_input("End date", value=today)
        if start_date > end_date:
            st.error("End date must be on or after the start date.")
            end_date = start_date

        options = [station.key for station in ALL_STATIONS]
        labels = {station.key: f"{station.city}: {station.name}" for station in ALL_STATIONS}
        selected = st.multiselect(
            "Stations to analyze",
            options=options,
            default=options,
            format_func=lambda key: labels[key],
        )
        collect_clicked = st.button("Collect from APIs", type="primary", use_container_width=True)
        load_clicked = st.button("Load saved CSVs", use_container_width=True)

    request = CollectionRequest(start_date=start_date, end_date=end_date)
    action = "collect" if collect_clicked else "load" if load_clicked else None
    return request, set(selected), action


def _collect_for_dashboard(request: CollectionRequest, root: Path) -> None:
    try:
        with st.spinner("Collecting, validating, and saving rainfall data..."):
            result = collect_rainfall(request, root)
            records = _records_from_results(result)
        _store_dashboard_data(request, records, result)
        if result.station_failures:
            _set_dashboard_notice(
                "warning",
                f"Loaded new data, but {len(result.station_failures)} station(s) could not be loaded.",
            )
        else:
            _set_dashboard_notice("success", f"Loaded {len(records)} processed observations.")
        st.rerun()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Dashboard collection failed.")
        st.error(f"The selected data could not be collected: {exc}")


def _load_saved_for_dashboard(request: CollectionRequest, root: Path) -> None:
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
    _store_dashboard_data(request, records, paths)
    _set_dashboard_notice("success", f"Loaded {len(records)} saved processed observations.")
    st.rerun()


def _records_from_results(result: CollectionResult) -> list[RainfallRecord]:
    records: list[RainfallRecord] = []
    for station_result in result.station_results:
        records.extend(load_rainfall_records(station_result.processed_path))
    return records


def _store_dashboard_data(
    request: CollectionRequest,
    records: list[RainfallRecord],
    evidence: CollectionResult | list[Path],
) -> None:
    st.session_state["rainfall_request"] = request
    st.session_state["rainfall_records"] = records
    st.session_state["rainfall_evidence"] = evidence


def _render_observation(
    root: Path,
    selected_keys: set[str],
    records: list[RainfallRecord],
) -> None:
    st.header("Rainfall Observation")
    selected_stations = [station for station in ALL_STATIONS if station.key in selected_keys]
    if not selected_stations:
        st.warning("Select at least one station in the sidebar.")
        return

    try:
        station_points = load_station_points(root)
        boundary = load_watershed_boundary(root)
        st_folium(_build_map(station_points, boundary), height=500, use_container_width=True)
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
    st.header("Event Analysis")
    st.caption("Positive observations are grouped using a one-hour station and regional tolerance.")
    events = detect_events(records)
    if not events:
        st.info("No positive-rainfall events were found for the selected stations and period.")
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


def _build_map(
    station_points: Iterable[StationPoint],
    boundary: tuple[tuple[float, float], ...],
) -> folium.Map:
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
    station_map.get_root().html.add_child(folium.Element(legend))
    return station_map


def _station_totals(records: Iterable[RainfallRecord]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for record in records:
        totals[record.station_key] = totals.get(record.station_key, 0.0) + record.rain_in
    return totals


def _event_row(index: int, event: RainfallEvent) -> dict[str, object]:
    return {
        "event": index,
        "start": event.start.strftime("%Y-%m-%d %H:%M"),
        "end": event.end.strftime("%Y-%m-%d %H:%M"),
        "duration_hours": round(event.duration_minutes / 60, 2),
        "total_rain_in": round(event.total_rain_in, 3),
        "stations": ", ".join(event.station_names),
    }


def _format_duration(event: RainfallEvent) -> str:
    return f"{event.duration_minutes / 60:.2f} h"


def _render_evidence_links() -> None:
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
    st.session_state["dashboard_notice"] = (level, message)


def _show_dashboard_notice() -> None:
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
