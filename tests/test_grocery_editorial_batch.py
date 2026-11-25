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

    def test_second_batch_keeps_only_g10_proposed(self):
        batch_dates = [
            "2023-09-13", "2023-09-20", "2023-09-27",
            "2023-10-04", "2023-10-11", "2023-10-18", "2023-10-25",
            "2023-11-01", "2023-11-08", "2023-11-15", "2023-11-22",
            "2023-11-29", "2023-12-06",
        ]
        batch = [entry for entry in self.ledger["entries"]
                 if entry.get("coverage_date") in batch_dates]
        self.assertEqual(len(batch), 13)
        self.assertEqual({entry["coverage_date"] for entry in batch}, set(batch_dates))
        g10 = next(entry for entry in batch if entry.get("milestone_id") == "g10")
        self.assertEqual(g10["coverage_date"], "2023-11-01")
        self.assertEqual(g10["slot_status"], "proposed_milestone")
        self.assertIn("proposed future retrospective", g10["evidence_status"])
        self.assertIn("ae661351a4906997e914f600adaa449dedef9a5c", g10["evidence_status"])
        self.assertIsNone(g10["actual_execution_date"])
        self.assertIsNone(g10["actual_publication_date"])
        self.assertIsNone(g10.get("prepared_post"))
        self.assertEqual(g10["publication_status"], "excluded_draft; no post created")
        self.assertLessEqual(g10["estimated_minutes"]["total"], 120)

        unassigned = [entry for entry in batch if entry["slot_status"] == "unassigned_undocumented"]
        self.assertEqual(len(unassigned), 12)
        self.assertTrue(all(entry.get("milestone_id") is None for entry in unassigned))
        self.assertTrue(all(entry["estimated_minutes"]["total"] == 0 for entry in unassigned))

    def test_third_batch_keeps_only_g11_proposed(self):
        batch_dates = [
            "2023-12-13", "2023-12-20", "2023-12-27",
            "2024-01-03", "2024-01-10", "2024-01-17", "2024-01-24",
            "2024-01-31", "2024-02-07", "2024-02-14", "2024-02-21",
            "2024-02-28", "2024-03-06",
        ]
        batch = [entry for entry in self.ledger["entries"]
                 if entry.get("coverage_date") in batch_dates]
        self.assertEqual(len(batch), 13)
        self.assertEqual({entry["coverage_date"] for entry in batch}, set(batch_dates))
        g11 = next(entry for entry in batch if entry.get("milestone_id") == "g11")
        self.assertEqual(g11["coverage_date"], "2024-02-07")
        self.assertEqual(g11["slot_status"], "proposed_milestone")
        self.assertIn("proposed future retrospective", g11["evidence_status"])
        self.assertIn("ae661351a4906997e914f600adaa449dedef9a5c", g11["evidence_status"])
        self.assertIsNone(g11["actual_execution_date"])
        self.assertIsNone(g11["actual_publication_date"])
        self.assertIsNone(g11.get("prepared_post"))
        self.assertEqual(g11["publication_status"], "excluded_draft; no post created")
        self.assertLessEqual(g11["estimated_minutes"]["total"], 120)

        unassigned = [entry for entry in batch if entry["slot_status"] == "unassigned_undocumented"]
        self.assertEqual(len(unassigned), 12)
        self.assertTrue(all(entry.get("milestone_id") is None for entry in unassigned))
        self.assertTrue(all(entry["estimated_minutes"]["total"] == 0 for entry in unassigned))


if __name__ == "__main__":
    unittest.main()
