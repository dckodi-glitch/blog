import datetime as dt
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "weekly-editorial-ledger.json"


class ElectricitySummer2025UnassignedBatchTests(unittest.TestCase):
    def setUp(self):
        self.entries = json.loads(LEDGER.read_text(encoding="utf-8"))["entries"]

    def test_batch_has_thirteen_electricity_wednesdays(self):
        dates = []
        current = dt.date(2025, 6, 11)
        end = dt.date(2025, 9, 3)
        while current <= end:
            dates.append(current.isoformat())
            current += dt.timedelta(days=7)
        batch = [entry for entry in self.entries if entry.get("coverage_date") in dates]
        self.assertEqual(len(batch), 13)
        self.assertEqual({entry["coverage_date"] for entry in batch}, set(dates))
        self.assertTrue(all(entry["featured_project"] == "electricity" for entry in batch))

    def test_unsupported_weeks_remain_unassigned_without_claimed_work(self):
        batch = [
            entry for entry in self.entries
            if "2025-06-11" <= entry["coverage_date"] <= "2025-09-03"
        ]
        self.assertEqual(len(batch), 13)
        self.assertTrue(all(entry["slot_status"] == "unassigned_undocumented" for entry in batch))
        self.assertTrue(all(entry.get("milestone_id") is None for entry in batch))
        self.assertTrue(all(entry.get("proposed_question") is None for entry in batch))
        self.assertTrue(all(entry["estimated_minutes"]["total"] == 0 for entry in batch))
        self.assertTrue(all(entry["actual_execution_date"] is None for entry in batch))
        self.assertTrue(all(entry["actual_publication_date"] is None for entry in batch))
        self.assertTrue(
            all(entry["publication_status"] == "excluded_draft; no post created" for entry in batch)
        )

    def test_site_and_inventory_report_evidence_gap_without_claiming_no_work(self):
        project_status = " ".join(
            (ROOT / "site/projects/electricity.qmd").read_text(encoding="utf-8").split()
        )
        self.assertIn("all 13 coverage dates remain unassigned", project_status)
        self.assertIn("not proof that no work occurred outside GitHub", project_status)

        inventory = " ".join(
            (ROOT / "data-source-evidence-inventory.md").read_text(encoding="utf-8").split()
        )
        self.assertIn("same six files in `outputs/`", inventory)
        self.assertIn("evidence gap, not proof that no off-platform work occurred", inventory)

    def test_preserved_electricity_assets_are_aggregate_only(self):
        for relative in (
            "site/drafts/electricity-2024-06-05-assets",
            "site/drafts/electricity-2024-08-07-assets",
        ):
            names = {path.name.lower() for path in (ROOT / relative).iterdir() if path.is_file()}
            self.assertFalse(any("student" in name or "learner" in name for name in names))
            self.assertFalse(any(name.endswith((".zip", ".txt")) for name in names))


if __name__ == "__main__":
    unittest.main()
