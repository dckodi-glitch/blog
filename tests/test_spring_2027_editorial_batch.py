import datetime as dt
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "weekly-editorial-ledger.json"


class Spring2027EditorialBatchTests(unittest.TestCase):
    def setUp(self):
        self.entries = json.loads(LEDGER.read_text(encoding="utf-8"))["entries"]

    def test_batch_has_thirteen_unassigned_wednesdays(self):
        dates = []
        current = dt.date(2027, 3, 10)
        end = dt.date(2027, 6, 2)
        while current <= end:
            dates.append(current.isoformat())
            current += dt.timedelta(days=7)

        batch = [entry for entry in self.entries if entry["coverage_date"] in dates]
        self.assertEqual([entry["coverage_date"] for entry in batch], dates)
        self.assertEqual(len(batch), 13)
        for entry in batch:
            self.assertEqual(entry["featured_project"], "learning analytics")
            self.assertEqual(entry["slot_status"], "unassigned_undocumented")
            self.assertIsNone(entry["milestone_id"])
            self.assertIsNone(entry["proposed_question"])
            self.assertIsNone(entry["actual_execution_date"])
            self.assertIsNone(entry["actual_publication_date"])
            self.assertEqual(entry["required_inputs"], [])
            self.assertEqual(entry["estimated_minutes"]["total"], 0)
            self.assertEqual(entry["publication_status"], "excluded_draft; no post created")

    def test_site_and_inventory_do_not_recast_prior_work_as_2027_activity(self):
        page = (ROOT / "site/projects/learning.qmd").read_text(encoding="utf-8")
        inventory = (ROOT / "data-source-evidence-inventory.md").read_text(encoding="utf-8")
        self.assertIn("No learning milestone is assigned to the March 10 through June 2, 2027", page)
        self.assertIn("not work on the 2027 coverage labels", inventory)
        self.assertIn("The l03 proposal is dated 2026-04-01, outside this batch", inventory)
        self.assertIn("l04 and l05 proposals are dated 2026-05-06 and 2026-06-03", inventory)
        self.assertIn("No `studentVle.csv`, learner-level output, or repository code", inventory)


if __name__ == "__main__":
    unittest.main()
