from __future__ import annotations

import base64
import csv
import hashlib
import io
import tarfile
import zipfile
from pathlib import Path

NAME = "mmc-watershed-data"
VERSION = "0.1.0"
DIST_INFO = f"mmc_watershed_data-{VERSION}.dist-info"
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src" / "mmc_watershed_data"


def _wheel_name() -> str:
    return f"mmc_watershed_data-{VERSION}-py3-none-any.whl"


def _sdist_name() -> str:
    return f"mmc-watershed-data-{VERSION}.tar.gz"


def get_requires_for_build_wheel(config_settings=None):  # noqa: D401
    return []


def get_requires_for_build_sdist(config_settings=None):  # noqa: D401
    return []


def get_requires_for_build_editable(config_settings=None):  # noqa: D401
    return []


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    metadata_dir = Path(metadata_directory) / DIST_INFO
    metadata_dir.mkdir(parents=True, exist_ok=True)
    (metadata_dir / "METADATA").write_text(
        "\n".join(
            [
                "Metadata-Version: 2.1",
                f"Name: {NAME}",
                f"Version: {VERSION}",
                "Summary: Collect Auburn Ogletree rainfall data",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (metadata_dir / "WHEEL").write_text(
        "\n".join(
            [
                "Wheel-Version: 1.0",
                "Generator: build_backend",
                "Root-Is-Purelib: true",
                "Tag: py3-none-any",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return DIST_INFO


def prepare_metadata_for_build_editable(metadata_directory, config_settings=None):
    return prepare_metadata_for_build_wheel(metadata_directory, config_settings)


def _iter_package_files():
    for path in SRC.rglob("*"):
        if path.is_file():
            yield path, Path("mmc_watershed_data") / path.relative_to(SRC)


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    wheel_path = Path(wheel_directory) / _wheel_name()
    records: list[tuple[str, str, str]] = []

    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for source, dest in _iter_package_files():
            data = source.read_bytes()
            zf.writestr(str(dest), data)
            digest = hashlib.sha256(data).digest()
            encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
            records.append((str(dest), f"sha256={encoded}", str(len(data))))

        metadata = "\n".join(
            [
                "Metadata-Version: 2.1",
                f"Name: {NAME}",
                f"Version: {VERSION}",
                "Summary: Collect Auburn Ogletree rainfall data",
                "",
            ]
        ).encode("utf-8")
        wheel = "\n".join(
            [
                "Wheel-Version: 1.0",
                "Generator: build_backend",
                "Root-Is-Purelib: true",
                "Tag: py3-none-any",
                "",
            ]
        ).encode("utf-8")
        entry_points = "\n".join(
            [
                "[console_scripts]",
                "mmc = mmc_watershed_data.cli:main",
                "",
            ]
        ).encode("utf-8")

        dist_info_files = {
            f"{DIST_INFO}/METADATA": metadata,
            f"{DIST_INFO}/WHEEL": wheel,
            f"{DIST_INFO}/entry_points.txt": entry_points,
        }
        for filename, data in dist_info_files.items():
            zf.writestr(filename, data)
            digest = hashlib.sha256(data).digest()
            encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
            records.append((filename, f"sha256={encoded}", str(len(data))))

        record_name = f"{DIST_INFO}/RECORD"
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        for row in records:
            writer.writerow(row)
        writer.writerow((record_name, "", ""))
        zf.writestr(record_name, buffer.getvalue().encode("utf-8"))

    return wheel_path.name


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    wheel_path = Path(wheel_directory) / _wheel_name()
    records: list[tuple[str, str, str]] = []
    editable_path = str((ROOT / "src").resolve()).replace("\\", "/")

    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        pth_name = "mmc_watershed_data.pth"
        pth_data = f"{editable_path}\n".encode("utf-8")
        zf.writestr(pth_name, pth_data)
        digest = hashlib.sha256(pth_data).digest()
        encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        records.append((pth_name, f"sha256={encoded}", str(len(pth_data))))

        metadata = "\n".join(
            [
                "Metadata-Version: 2.1",
                f"Name: {NAME}",
                f"Version: {VERSION}",
                "Summary: Collect Auburn Ogletree rainfall data",
                "",
            ]
        ).encode("utf-8")
        wheel = "\n".join(
            [
                "Wheel-Version: 1.0",
                "Generator: build_backend",
                "Root-Is-Purelib: true",
                "Tag: py3-none-any",
                "",
            ]
        ).encode("utf-8")
        entry_points = "\n".join(
            [
                "[console_scripts]",
                "mmc = mmc_watershed_data.cli:main",
                "",
            ]
        ).encode("utf-8")
        dist_info_files = {
            f"{DIST_INFO}/METADATA": metadata,
            f"{DIST_INFO}/WHEEL": wheel,
            f"{DIST_INFO}/entry_points.txt": entry_points,
        }
        for filename, data in dist_info_files.items():
            zf.writestr(filename, data)
            digest = hashlib.sha256(data).digest()
            encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
            records.append((filename, f"sha256={encoded}", str(len(data))))

        record_name = f"{DIST_INFO}/RECORD"
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        for row in records:
            writer.writerow(row)
        writer.writerow((record_name, "", ""))
        zf.writestr(record_name, buffer.getvalue().encode("utf-8"))

    return wheel_path.name


def build_sdist(sdist_directory, config_settings=None):
    sdist_path = Path(sdist_directory) / _sdist_name()
    with tarfile.open(sdist_path, "w:gz") as tf:
        base = Path(f"mmc-watershed-data-{VERSION}")
        for relative in [
            Path("pyproject.toml"),
            Path("README.md"),
            Path("AGENTS.md"),
            Path("sitecustomize.py"),
            Path("build_backend.py"),
        ]:
            path = ROOT / relative
            if path.exists():
                tf.add(path, arcname=str(base / relative))
        for source, dest in _iter_package_files():
            tf.add(source, arcname=str(base / Path("src") / dest))
    return sdist_path.name
