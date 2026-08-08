"""Offline tests for wheel and source-archive release contracts."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_backend  # noqa: E402
from scripts.verify_package import _verify_sdist, _verify_wheel  # noqa: E402


class PackagingTests(unittest.TestCase):
    """Build artifacts in temporary directories and inspect their contracts."""

    def test_wheel_contains_metadata_entry_point_license_and_assets(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
            "project"
        ]
        with tempfile.TemporaryDirectory() as tmp:
            filename = build_backend.build_wheel(tmp)
            wheel = Path(tmp) / filename

            _verify_wheel(wheel, project)

    def test_source_archive_is_complete_and_excludes_generated_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            filename = build_backend.build_sdist(tmp)
            sdist = Path(tmp) / filename

            _verify_sdist(sdist, build_backend.VERSION)

    def test_build_backend_derives_runtime_dependencies_from_pyproject(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
            "project"
        ]

        self.assertEqual(
            build_backend.DEPENDENCY_METADATA,
            [f"Requires-Dist: {item}" for item in project["dependencies"]],
        )


if __name__ == "__main__":
    unittest.main()
