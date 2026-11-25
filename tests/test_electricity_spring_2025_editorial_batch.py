import datetime as dt
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "weekly-editorial-ledger.json"


class ElectricitySpring2025EditorialBatchTests(unittest.TestCase):
    def setUp(self):
        self.entries = json.loads(LEDGER.read_text(encoding="utf-8"))["entries"]
        self.by_id = {entry.get("milestone_id"): entry for entry in self.entries}

    def test_batch_has_thirteen_electricity_wednesdays(self):
        dates = []
        current = dt.date(2025, 3, 12)
        end = dt.date(2025, 6, 4)
        while current <= end:
            dates.append(current.isoformat())
            current += dt.timedelta(days=7)
        batch = [entry for entry in self.entries if entry.get("coverage_date") in dates]
        self.assertEqual(len(batch), 13)
        self.assertEqual({entry["coverage_date"] for entry in batch}, set(dates))
        self.assertTrue(all(entry["featured_project"] == "electricity" for entry in batch))

    def test_e11_reuses_daily_coverage_evidence_without_claiming_sensitivity_results(self):
        e11 = self.by_id["e11"]
        self.assertEqual(e11["coverage_date"], "2025-04-02")
        self.assertEqual(e11["slot_status"], "proposed_milestone")
        self.assertEqual(e11["prerequisites"], ["e01"])
        self.assertIn("1,440-valid-minute", e11["small_milestone"])
        self.assertIn("1,368 valid minutes", e11["small_milestone"])
        self.assertEqual(
            e11["required_inputs"],
            [
                "blog:site/drafts/electricity-2024-06-05-assets/daily_consumption.csv",
                "blog:site/drafts/electricity-2024-06-05-assets/export_metadata.json",
                "blog:site/drafts/electricity-2024-06-05-assets/quality_summary.json",
            ],
        )
        self.assertIn("no threshold-sensitivity result exists", e11["evidence_status"])
        self.assertIn("ae46f2abe167f4d5d14395829ee3e542c7af04bb84397fbd46cbf45149a5cd37", e11["evidence_status"])
        self.assertIsNone(e11["actual_execution_date"])
        self.assertIsNone(e11["actual_publication_date"])
        self.assertIsNone(e11.get("prepared_post"))
        self.assertEqual(e11["publication_status"], "excluded_draft; no post created")
        self.assertLessEqual(e11["estimated_minutes"]["total"], 120)

        assets = ROOT / "site/drafts/electricity-2024-06-05-assets"
        metadata = json.loads((assets / "export_metadata.json").read_text(encoding="utf-8"))
        quality = json.loads((assets / "quality_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["analysis_revision"]["script_sha256"], "ae46f2abe167f4d5d14395829ee3e542c7af04bb84397fbd46cbf45149a5cd37")
        self.assertEqual(metadata["execution_timestamp"], "2026-11-14T14:30:55.191723-08:00")
        self.assertEqual(quality["day_count"], 1442)
        self.assertEqual(quality["complete_days"], 1358)
        self.assertEqual(quality["partial_or_incomplete_days"], 84)

    def test_e12_waits_for_required_aggregate_outputs_and_makes_no_conclusion(self):
        e12 = self.by_id["e12"]
        self.assertEqual(e12["coverage_date"], "2025-05-07")
        self.assertEqual(e12["slot_status"], "proposed_milestone")
        self.assertEqual(e12["prerequisites"], ["e05", "e08", "e11"])
        self.assertIn("not yet available", e12["required_inputs"][-1])
        self.assertIn("remain proposed without results", e12["evidence_status"])
        self.assertIsNone(e12["actual_execution_date"])
        self.assertIsNone(e12["actual_publication_date"])
        self.assertIsNone(e12.get("prepared_post"))
        self.assertEqual(e12["publication_status"], "excluded_draft; no post created")
        self.assertLessEqual(e12["estimated_minutes"]["total"], 120)

    def test_eleven_other_weeks_remain_unassigned_and_only_aggregate_assets_are_listed(self):
        batch = [
            entry for entry in self.entries
            if "2025-03-12" <= entry["coverage_date"] <= "2025-06-04"
        ]
        unassigned = [entry for entry in batch if entry["slot_status"] == "unassigned_undocumented"]
        self.assertEqual(len(unassigned), 11)
        self.assertTrue(all(entry.get("milestone_id") is None for entry in unassigned))
        self.assertTrue(all(entry["estimated_minutes"]["total"] == 0 for entry in unassigned))

        assets = ROOT / "site/drafts/electricity-2024-06-05-assets"
        names = {path.name.lower() for path in assets.iterdir() if path.is_file()}
        self.assertFalse(any("student" in name or "learner" in name for name in names))
        self.assertFalse(any(name.endswith((".zip", ".txt")) for name in names))

        inventory = " ".join(
            (ROOT / "data-source-evidence-inventory.md").read_text(encoding="utf-8").split()
        )
        self.assertIn("1,358 complete days, 84 partial or incomplete days", inventory)
        self.assertIn("no such sensitivity result", inventory)
        project_status = " ".join(
            (ROOT / "site/projects/electricity.qmd").read_text(encoding="utf-8").split()
        )
        self.assertIn("other eleven coverage dates from March 12 through June 4, 2025", project_status)


if __name__ == "__main__":
    unittest.main()
