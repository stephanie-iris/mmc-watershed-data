"""Offline contract tests for GitHub Actions and repository hygiene."""

from __future__ import annotations

from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ContinuousIntegrationTests(unittest.TestCase):
    """Protect the final automated quality and hygiene gates."""

    def test_ci_runs_locked_offline_checks_on_push(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )

        self.assertRegex(workflow, r"(?m)^  push:\s*$")
        self.assertRegex(workflow, r"(?m)^  pull_request:\s*$")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("contents: read", workflow)
        for command in (
            "uv sync --locked",
            "coverage run --source=mmc_watershed_data -m pytest",
            "coverage report --show-missing --fail-under=70",
            "ruff format --check .",
            "ruff check .",
            "mypy src",
            "uv build --no-sources",
            "scripts/verify_package.py",
        ):
            self.assertIn(command, workflow)
        self.assertNotIn("mmc --start-date", workflow)

    def test_generated_and_secret_paths_are_ignored_and_untracked(self) -> None:
        patterns = {
            line.strip()
            for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        for pattern in (
            ".coverage",
            ".env",
            ".venv/",
            "/data/",
            "dist/",
            "logs/",
            ".ipynb_checkpoints/",
            ".vscode/",
        ):
            self.assertIn(pattern, patterns)

        tracked_output = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        existing_tracked = [
            path.replace("\\", "/")
            for path in tracked_output.splitlines()
            if (ROOT / path).exists()
        ]
        forbidden_anywhere = {
            ".coverage",
            ".env",
            ".venv",
            ".ipynb_checkpoints",
        }
        forbidden_top_level = {"data", "dist", "logs"}
        offenders = []
        for path in existing_tracked:
            parts = Path(path).parts
            if forbidden_anywhere.intersection(parts) or (
                parts and parts[0] in forbidden_top_level
            ):
                offenders.append(path)
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
