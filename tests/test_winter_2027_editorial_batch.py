import datetime as dt
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "weekly-editorial-ledger.json"
ONLINE_REVISION = "2859cb40d9a120a86eb12d7c1407cd2f80c66c01"
OULAD_INPUT_REVISION = "a51ba30520859201319ec9efc40142153fb68fc2"
OULAD_ANALYSIS_BLOB = "40350a025a6f222db6f73e283de13e080463baa0"


class Winter2027EditorialBatchTests(unittest.TestCase):
    def setUp(self):
        self.entries = json.loads(LEDGER.read_text(encoding="utf-8"))["entries"]
        self.by_id = {entry.get("milestone_id"): entry for entry in self.entries}

    def test_batch_has_thirteen_dates_and_only_l12_proposed(self):
        dates = []
        current = dt.date(2026, 12, 9)
        end = dt.date(2027, 3, 3)
        while current <= end:
            dates.append(current.isoformat())
            current += dt.timedelta(days=7)
        batch = [entry for entry in self.entries if entry["coverage_date"] in dates]
        self.assertEqual([entry["coverage_date"] for entry in batch], dates)
        self.assertEqual(len(batch), 13)

        proposed = [entry for entry in batch if entry["slot_status"] == "proposed_milestone"]
        self.assertEqual(
            [(entry["coverage_date"], entry["milestone_id"]) for entry in proposed],
            [("2027-01-06", "l12")],
        )
        self.assertEqual(
            sum(entry["slot_status"] == "unassigned_undocumented" for entry in batch),
            12,
        )
        for entry in batch:
            self.assertEqual(entry["featured_project"], "learning analytics")
            self.assertIsNone(entry["actual_execution_date"])
            self.assertIsNone(entry["actual_publication_date"])
            self.assertEqual(entry["publication_status"], "excluded_draft; no post created")

    def test_l12_is_a_privacy_bounded_future_proposal_with_exact_provenance(self):
        entry = self.by_id["l12"]
        self.assertEqual(entry["coverage_date"], "2027-01-06")
        self.assertEqual(entry["slot_status"], "proposed_milestone")
        self.assertEqual(entry["prerequisites"], ["l04", "l08", "l11"])
        self.assertEqual(entry["publication_status"], "excluded_draft; no post created")
        self.assertIsNone(entry["actual_execution_date"])
        self.assertIsNone(entry["actual_publication_date"])
        self.assertIsNone(entry["analysis_code_revision"])
        self.assertLessEqual(entry["estimated_minutes"]["total"], 120)
        self.assertIn(ONLINE_REVISION, entry["evidence_status"])
        self.assertIn(OULAD_INPUT_REVISION, entry["historical_cutoff"])
        self.assertIn(OULAD_ANALYSIS_BLOB, entry["historical_cutoff"])
        self.assertFalse(
            any(
                "studentInfo.csv" in path or "studentVle.csv" in path
                for path in entry["required_inputs"]
            )
        )
        self.assertIn("aggregate", entry["expected_evidence"].lower())
        self.assertIn("methodology", entry["unavailable_data_or_release_uncertainty"])

    def test_site_and_inventory_keep_future_work_excluded(self):
        page = (ROOT / "site/projects/learning.qmd").read_text(encoding="utf-8")
        inventory = (ROOT / "data-source-evidence-inventory.md").read_text(encoding="utf-8")
        self.assertIn("A future l12 source comparison remains an excluded proposal", page)
        self.assertIn("twelve\nunassigned weeks and one future excluded proposal", inventory)
        self.assertIn(OULAD_INPUT_REVISION, inventory)
        self.assertIn(OULAD_ANALYSIS_BLOB, inventory)
        self.assertIn("No `studentVle.csv` or repository code", inventory)


if __name__ == "__main__":
    unittest.main()
