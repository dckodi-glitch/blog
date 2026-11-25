import datetime as dt
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "weekly-editorial-ledger.json"


class GroceryEditorialBatchTests(unittest.TestCase):
    def setUp(self):
        self.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        self.entries = [
            entry for entry in self.ledger["entries"]
            if "2023-06-14" <= entry.get("coverage_date", "") <= "2023-09-06"
        ]
        self.by_date = {entry["coverage_date"]: entry for entry in self.entries}

    def test_batch_has_one_entry_for_each_wednesday(self):
        expected = []
        day = dt.date(2023, 6, 14)
        end = dt.date(2023, 9, 6)
        while day <= end:
            expected.append(day.isoformat())
            day += dt.timedelta(days=7)
        self.assertEqual(len(expected), 13)
        self.assertEqual(sorted(self.by_date), expected)
        self.assertEqual(len(self.entries), 13)
        self.assertTrue(all(entry["featured_project"] == "groceries" for entry in self.entries))

    def test_only_supported_retropectives_are_completed(self):
        for date, code_revision in (
            ("2023-06-14", "e555df70bd62f971386674f82b83f5c5f7c183b0"),
            ("2023-07-26", "f092b3a782ecc2da931e0f0576684338511997bb"),
        ):
            entry = self.by_date[date]
            self.assertEqual(entry["slot_status"], "retrospective_executed")
            self.assertEqual(entry["analysis_code_revision"], code_revision)
            self.assertIsNotNone(entry["actual_execution_date"])
            self.assertIsNone(entry["actual_publication_date"])
            post = ROOT / entry["prepared_post"]
            self.assertTrue(post.is_file())
            self.assertIn("draft: true", post.read_text(encoding="utf-8"))

    def test_proposed_and_unassigned_slots_do_not_claim_execution(self):
        for milestone in ("g02", "g03", "g04", "g05", "g06", "g08", "g09"):
            entry = next(item for item in self.entries if item.get("milestone_id") == milestone)
            self.assertEqual(entry["slot_status"], "proposed_milestone")
            self.assertIsNone(entry["actual_execution_date"])
            self.assertIsNone(entry["actual_publication_date"])
            self.assertIn("proposed", entry["evidence_status"])
            self.assertIsNone(entry.get("prepared_post"))
        unassigned = [entry for entry in self.entries if entry["slot_status"] == "unassigned_undocumented"]
        self.assertEqual([entry["coverage_date"] for entry in unassigned],
                         ["2023-08-09", "2023-08-16", "2023-08-23", "2023-08-30"])
        self.assertTrue(all(entry.get("milestone_id") is None for entry in unassigned))

    def test_existing_grocery_draft_assets_are_aggregate_exports(self):
        for draft_dir in (ROOT / "site/drafts/grocery-2023-06-14-assets",
                          ROOT / "site/drafts/grocery-2023-07-26-assets"):
            names = {path.name.lower() for path in draft_dir.iterdir() if path.is_file()}
            self.assertTrue(names)
            self.assertFalse(any(name.endswith((".xlsx", ".xls", ".db")) for name in names))
            self.assertFalse(any("student" in name or "learner" in name for name in names))


if __name__ == "__main__":
    unittest.main()
