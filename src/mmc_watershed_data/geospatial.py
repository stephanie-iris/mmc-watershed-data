"""Small KMZ/KML readers for the dashboard map."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree


KML_NAMESPACE = "{http://www.opengis.net/kml/2.2}"


@dataclass(frozen=True)
class StationPoint:
    """Map-ready station location with its city and project identity."""

    city: str
    station_key: str
    station_name: str
    latitude: float
    longitude: float


def load_station_points(root: Path) -> tuple[StationPoint, ...]:
    """Read the known station placemarks from the two station KMZ files."""

    from .stations import AUBURN_STATIONS, OPELIKA_STATIONS

    points: list[StationPoint] = []
    for city, filename, stations in (
        ("Auburn", "auburn_stations.kmz", AUBURN_STATIONS),
        ("Opelika", "opelika_stations.kmz", OPELIKA_STATIONS),
    ):
        placemarks = _placemarks(_read_kml(_asset_path(root, "stations", filename)))
        by_name = {
            name: coordinates
            for name, coordinates in placemarks
            if coordinates is not None
        }
        for station in stations:
            if station.name not in by_name:
                raise ValueError(
                    f"Station {station.name!r} was not found in {filename}."
                )
            latitude, longitude = by_name[station.name]
            points.append(
                StationPoint(
                    city=city,
                    station_key=station.key,
                    station_name=station.name,
                    latitude=latitude,
                    longitude=longitude,
                )
            )
    return tuple(points)


def load_watershed_boundary(root: Path) -> tuple[tuple[float, float], ...]:
    """Read the watershed polygon as ``(latitude, longitude)`` pairs."""

    kml_root = ElementTree.fromstring(
        _read_kml(_asset_path(root, "watershed", "mmc_boundary.kmz"))
    )
    for polygon in kml_root.iter():
        if _local_name(polygon.tag) != "Polygon":
            continue
        for element in polygon.iter():
            if _local_name(element.tag) == "coordinates" and element.text:
                return tuple(_parse_coordinate_pairs(element.text))
    raise ValueError("The MMC watershed KMZ does not contain a polygon boundary.")


def _read_kml(path: Path) -> bytes:
    """Read ``doc.kml`` from a KMZ archive or propagate an asset error."""

    with ZipFile(path) as archive:
        return archive.read("doc.kml")


def _asset_path(root: Path, category: str, filename: str) -> Path:
    """Resolve repository assets first, then wheel-bundled geospatial assets."""

    repository_path = root / "assets" / "geospatial" / category / filename
    if repository_path.is_file():
        return repository_path
    return Path(__file__).parent / "assets" / "geospatial" / category / filename


def _placemarks(kml: bytes) -> list[tuple[str, tuple[float, float] | None]]:
    """Extract named point placemarks as latitude/longitude pairs."""

    root = ElementTree.fromstring(kml)
    result: list[tuple[str, tuple[float, float] | None]] = []
    for placemark in root.findall(f".//{KML_NAMESPACE}Placemark"):
        name_element = placemark.find(f"{KML_NAMESPACE}name")
        coordinate_element = placemark.find(
            f".//{KML_NAMESPACE}Point//{KML_NAMESPACE}coordinates"
        )
        if name_element is None or not name_element.text:
            continue
        coordinates = None
        if coordinate_element is not None and coordinate_element.text:
            parsed = _parse_coordinate_pairs(coordinate_element.text)
            coordinates = parsed[0] if parsed else None
        result.append((name_element.text.strip(), coordinates))
    return result


def _parse_coordinate_pairs(text: str) -> list[tuple[float, float]]:
    """Parse KML longitude,latitude[,altitude] tokens into map coordinates."""

    pairs: list[tuple[float, float]] = []
    for coordinate in text.split():
        values = coordinate.split(",")
        if len(values) < 2:
            continue
        longitude, latitude = float(values[0]), float(values[1])
        pairs.append((latitude, longitude))
    return pairs


def _local_name(tag: str) -> str:
    """Return an XML tag name without its optional namespace."""

    return tag.rsplit("}", 1)[-1]
