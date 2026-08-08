"""Offline checks for the durable Practicum 6 documentation artifacts."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    """Protect the required documentation and report source contract."""

    def test_required_documentation_artifacts_exist(self) -> None:
        """The repository contains the linked documentation deliverables."""

        for relative_path in (
            "LICENSE",
            "AGENTS.md",
            "docs/index.md",
            "docs/data-dictionary.md",
            "docs/package-checklist.md",
            ".github/workflows/ci.yml",
            "reports/mmc-rainfall-report.qmd",
            "reports/mmc-rainfall-report.pdf",
            "reports/data/mmc_report_2026-07-01_to_2026-08-01_processed.csv",
        ):
            self.assertTrue((ROOT / relative_path).is_file(), relative_path)

    def test_root_data_ignore_does_not_hide_report_fallback(self) -> None:
        """Generated root data is ignored without excluding report fixtures."""

        patterns = {
            line.strip()
            for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

        self.assertIn("/data/", patterns)
        self.assertNotIn("data/", patterns)

    def test_report_uses_shared_loader_and_documents_rebuild_command(self) -> None:
        """The report source points to shared code and its rebuild command."""

        source = (ROOT / "reports" / "mmc-rainfall-report.qmd").read_text(
            encoding="utf-8"
        )

        self.assertIn("load_rainfall_records", source)
        self.assertIn("quarto render reports/mmc-rainfall-report.qmd --to pdf", source)
        self.assertNotIn("MMC_REPORT_INPUT", source)
        self.assertNotIn("MMC_REPORT_START_DATE", source)
        self.assertNotIn("MMC_REPORT_END_DATE", source)
        self.assertIn("Rainfall totals", source)
        self.assertIn("fig-station-map", source)

    def test_readme_links_to_documentation_and_license(self) -> None:
        """The README links users to the main detailed documentation."""

        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        for link in (
            "docs/index.md",
            "docs/data-dictionary.md",
            "reports/mmc-rainfall-report.qmd",
            "reports/mmc-rainfall-report.pdf",
            "LICENSE",
            "docs/package-checklist.md",
            ".github/workflows/ci.yml",
        ):
            self.assertIn(link, readme)

    def test_report_documents_runtime_period_selection(self) -> None:
        """The report follows the most recently saved API collection."""

        source = (ROOT / "reports" / "mmc-rainfall-report.qmd").read_text(
            encoding="utf-8"
        )

        self.assertIn("load_report_dataset", source)
        self.assertIn("analyze_spatial_rainfall", source)
        self.assertIn("recently written", source)

    def test_readme_and_dashboard_document_spatial_products(self) -> None:
        """User-facing documentation exposes the Sprint 6 workflow."""

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        dashboard = (ROOT / "src" / "mmc_watershed_data" / "dashboard.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("Watershed Rainfall", readme)
        self.assertIn("mmc_areal_rainfall_START_to_END.csv", readme)
        self.assertIn('"Watershed Rainfall"', dashboard)


if __name__ == "__main__":
    unittest.main()
