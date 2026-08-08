"""Verify release artifacts in isolated, temporary environments."""

from __future__ import annotations

from email.parser import BytesParser
from email.policy import default
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile


ROOT = Path(__file__).resolve().parents[1]


class PackageVerificationError(RuntimeError):
    """Report a release artifact that fails the submission contract."""


def main() -> int:
    """Inspect, rebuild, install, and smoke-test current package artifacts."""

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    version = str(project["version"])
    wheel = ROOT / "dist" / f"mmc_watershed_data-{version}-py3-none-any.whl"
    sdist = ROOT / "dist" / f"mmc-watershed-data-{version}.tar.gz"
    for artifact in (wheel, sdist):
        if not artifact.is_file():
            raise PackageVerificationError(
                f"Expected artifact was not found: {artifact}"
            )

    _verify_wheel(wheel, project)
    _verify_sdist(sdist, version)
    with tempfile.TemporaryDirectory(prefix="mmc-package-check-") as temporary:
        temp_root = Path(temporary)
        rebuilt_wheel = _rebuild_sdist(sdist, version, temp_root)
        _verify_wheel(rebuilt_wheel, project)
        _smoke_test_wheel(wheel, version, temp_root)

    print(f"Verified wheel and source archive for MMC {version}.")
    return 0


def _verify_wheel(wheel: Path, project: dict[str, object]) -> None:
    """Check wheel contents, metadata, entry point, dependencies, and license."""

    version = str(project["version"])
    dist_info = f"mmc_watershed_data-{version}.dist-info"
    required_members = {
        "mmc_watershed_data/__init__.py",
        "mmc_watershed_data/cli.py",
        "mmc_watershed_data/dashboard.py",
        "mmc_watershed_data/spatial.py",
        "mmc_watershed_data/assets/geospatial/stations/auburn_stations.kmz",
        "mmc_watershed_data/assets/geospatial/stations/opelika_stations.kmz",
        "mmc_watershed_data/assets/geospatial/watershed/mmc_boundary.kmz",
        f"{dist_info}/METADATA",
        f"{dist_info}/entry_points.txt",
        f"{dist_info}/licenses/LICENSE",
    }
    with zipfile.ZipFile(wheel) as archive:
        members = {name.replace("\\", "/") for name in archive.namelist()}
        missing = required_members - members
        if missing:
            raise PackageVerificationError(
                f"Wheel is missing required members: {sorted(missing)}"
            )
        metadata = BytesParser(policy=default).parsebytes(
            archive.read(f"{dist_info}/METADATA")
        )
        if metadata["Name"] != project["name"] or metadata["Version"] != version:
            raise PackageVerificationError(
                "Wheel name or version metadata is incorrect."
            )
        if metadata["Requires-Python"] != project["requires-python"]:
            raise PackageVerificationError("Wheel Python requirement is incorrect.")
        expected_dependencies = set(project["dependencies"])  # type: ignore[arg-type]
        actual_dependencies = set(metadata.get_all("Requires-Dist", []))
        if actual_dependencies != expected_dependencies:
            raise PackageVerificationError(
                "Wheel runtime dependencies differ from pyproject.toml."
            )
        entry_points = archive.read(f"{dist_info}/entry_points.txt").decode("utf-8")
        if "mmc = mmc_watershed_data.cli:main" not in entry_points:
            raise PackageVerificationError(
                "Wheel does not define the mmc console script."
            )
        if (
            archive.read(f"{dist_info}/licenses/LICENSE")
            != (ROOT / "LICENSE").read_bytes()
        ):
            raise PackageVerificationError("Wheel license text differs from LICENSE.")


def _verify_sdist(sdist: Path, version: str) -> None:
    """Check source archive completeness and absence of generated artifacts."""

    base = f"mmc-watershed-data-{version}"
    required_members = {
        f"{base}/pyproject.toml",
        f"{base}/build_backend.py",
        f"{base}/README.md",
        f"{base}/LICENSE",
        f"{base}/uv.lock",
        f"{base}/src/mmc_watershed_data/cli.py",
        f"{base}/assets/geospatial/watershed/mmc_boundary.kmz",
        f"{base}/tests/test_api.py",
        f"{base}/docs/package-checklist.md",
        f"{base}/reports/mmc-rainfall-report.qmd",
        f"{base}/scripts/verify_package.py",
        f"{base}/.github/workflows/ci.yml",
    }
    forbidden_anywhere = {
        ".coverage",
        ".env",
        ".ipynb_checkpoints",
        ".venv",
        "__pycache__",
    }
    forbidden_top_level = {
        "data",
        "dist",
        "htmlcov",
        "logs",
    }
    with tarfile.open(sdist, "r:gz") as archive:
        members = {member.name.replace("\\", "/") for member in archive.getmembers()}
    missing = required_members - members
    if missing:
        raise PackageVerificationError(
            f"Source archive is missing required members: {sorted(missing)}"
        )
    for member in members:
        relative_parts = Path(member).parts[1:]
        top_level = relative_parts[0] if relative_parts else ""
        if (
            forbidden_anywhere.intersection(relative_parts)
            or top_level in forbidden_top_level
        ):
            raise PackageVerificationError(
                f"Source archive contains generated or secret material: {member}"
            )


def _rebuild_sdist(sdist: Path, version: str, temp_root: Path) -> Path:
    """Extract the sdist safely and independently rebuild its wheel."""

    extract_root = temp_root / "source"
    extract_root.mkdir()
    with tarfile.open(sdist, "r:gz") as archive:
        _safe_extract(archive, extract_root)
    source_root = extract_root / f"mmc-watershed-data-{version}"
    output = temp_root / "rebuilt-dist"
    _run(
        ["uv", "build", "--no-sources", "--out-dir", str(output)],
        cwd=source_root,
    )
    rebuilt = output / f"mmc_watershed_data-{version}-py3-none-any.whl"
    if not rebuilt.is_file():
        raise PackageVerificationError("The source archive did not rebuild its wheel.")
    return rebuilt


def _safe_extract(archive: tarfile.TarFile, destination: Path) -> None:
    """Extract regular archive paths without allowing traversal or links."""

    destination_resolved = destination.resolve()
    for member in archive.getmembers():
        target = (destination / member.name).resolve()
        if (
            destination_resolved not in target.parents
            and target != destination_resolved
        ):
            raise PackageVerificationError(f"Unsafe source archive path: {member.name}")
        if member.issym() or member.islnk():
            raise PackageVerificationError(
                f"Source archive contains a link: {member.name}"
            )
    archive.extractall(destination, filter="data")


def _smoke_test_wheel(wheel: Path, version: str, temp_root: Path) -> None:
    """Install the wheel in a clean venv and run its public command contract."""

    environment = temp_root / "wheel-venv"
    _run(["uv", "venv", "--python", sys.executable, str(environment)])
    python = _venv_executable(environment, "python")
    mmc = _venv_executable(environment, "mmc")
    _run(["uv", "pip", "install", "--python", str(python), str(wheel)])
    smoke_root = temp_root / "outside-repository"
    smoke_root.mkdir()
    version_output = _run([str(mmc), "--version"], cwd=smoke_root)
    if version_output.strip() != f"mmc {version}":
        raise PackageVerificationError("Installed mmc --version output is incorrect.")
    help_output = _run([str(mmc), "--help"], cwd=smoke_root)
    for expected in ("--start-date", "--end-date", "--log-file", "spatial products"):
        if expected not in help_output:
            raise PackageVerificationError(f"Installed mmc --help omits {expected}.")
    import_output = _run(
        [
            str(python),
            "-c",
            "import mmc_watershed_data; print(mmc_watershed_data.__version__)",
        ],
        cwd=smoke_root,
    )
    if import_output.strip() != version:
        raise PackageVerificationError(
            "Installed package import reports wrong version."
        )
    asset_output = _run(
        [
            str(python),
            "-c",
            (
                "from pathlib import Path; "
                "from mmc_watershed_data.geospatial import "
                "load_station_points, load_watershed_boundary; "
                "stations = load_station_points(Path.cwd()); "
                "boundary = load_watershed_boundary(Path.cwd()); "
                "print(len(stations), len(boundary))"
            ),
        ],
        cwd=smoke_root,
    )
    station_count, boundary_count = map(int, asset_output.split())
    if station_count != 9 or boundary_count < 4:
        raise PackageVerificationError(
            "Installed package could not load its bundled geospatial assets."
        )


def _venv_executable(environment: Path, name: str) -> Path:
    """Return a cross-platform executable path inside a virtual environment."""

    if sys.platform == "win32":
        suffix = ".exe"
        return environment / "Scripts" / f"{name}{suffix}"
    return environment / "bin" / name


def _run(command: list[str], *, cwd: Path | None = None) -> str:
    """Run a package check command and return captured output on success."""

    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        details = completed.stderr.strip() or completed.stdout.strip()
        raise PackageVerificationError(
            f"Command failed ({' '.join(command)}): {details}"
        )
    return completed.stdout


if __name__ == "__main__":
    raise SystemExit(main())
