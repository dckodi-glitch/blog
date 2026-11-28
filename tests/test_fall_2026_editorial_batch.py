import datetime as dt
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "weekly-editorial-ledger.json"
ONLINE_REVISION = "2859cb40d9a120a86eb12d7c1407cd2f80c66c01"
PLATFORM_CSV_BLOB = "e322129ca2435c886e7eb86cf4e2bd8174796b63"
PLATFORM_NOTEBOOK_BLOB = "87a3080ae78f69b7d61fbb9aec35d80c1cb8a2a1"
OULAD_INPUT_REVISION = "a51ba30520859201319ec9efc40142153fb68fc2"


class Fall2026EditorialBatchTests(unittest.TestCase):
    def setUp(self):
        self.entries = json.loads(LEDGER.read_text(encoding="utf-8"))["entries"]
        self.by_id = {entry.get("milestone_id"): entry for entry in self.entries}

    def test_batch_has_thirteen_dates_and_preserves_unassigned_weeks(self):
        dates = []
        current = dt.date(2026, 9, 9)
        end = dt.date(2026, 12, 2)
        while current <= end:
            dates.append(current.isoformat())
            current += dt.timedelta(days=7)
        batch = [entry for entry in self.entries if entry["coverage_date"] in dates]
        self.assertEqual([entry["coverage_date"] for entry in batch], dates)
        self.assertEqual(len(batch), 13)

        expected = {
            "2026-09-09": ("learning analytics", None, "unassigned_undocumented"),
            "2026-09-16": ("learning analytics", None, "unassigned_undocumented"),
            "2026-09-23": ("learning analytics", None, "unassigned_undocumented"),
            "2026-09-30": ("learning analytics", None, "unassigned_undocumented"),
            "2026-10-07": ("learning analytics", "l09", "proposed_milestone"),
            "2026-10-14": ("learning analytics", None, "unassigned_undocumented"),
            "2026-10-21": ("learning analytics", None, "unassigned_undocumented"),
            "2026-10-28": ("learning analytics", None, "unassigned_undocumented"),
            "2026-11-04": ("learning analytics", "l10", "proposed_milestone"),
            "2026-11-11": ("learning analytics", None, "unassigned_undocumented"),
            "2026-11-18": ("learning analytics", None, "unassigned_undocumented"),
            "2026-11-25": ("learning analytics", None, "unassigned_undocumented"),
            "2026-12-02": ("learning analytics", "l11", "proposed_milestone"),
        }
        for entry in batch:
            self.assertEqual(
                (entry["featured_project"], entry["milestone_id"], entry["slot_status"]),
                expected[entry["coverage_date"]],
            )
            self.assertIsNone(entry["actual_publication_date"])
            if entry["slot_status"] == "unassigned_undocumented":
                self.assertEqual(entry["estimated_minutes"]["total"], 0)
                self.assertIsNone(entry["actual_execution_date"])
            else:
                self.assertEqual(entry["publication_status"], "excluded_draft; no post created")
                self.assertIsNone(entry["actual_execution_date"])
                self.assertIsNone(entry["analysis_code_revision"])
                self.assertLessEqual(entry["estimated_minutes"]["total"], 120)

    def test_l09_and_l10_are_proposals_without_prediction_evidence(self):
        for milestone_id in ("l09", "l10"):
            entry = self.by_id[milestone_id]
            self.assertEqual(entry["slot_status"], "proposed_milestone")
            self.assertEqual(entry["publication_status"], "excluded_draft; no post created")
            self.assertIsNone(entry["actual_execution_date"])
            self.assertIsNone(entry["actual_publication_date"])
            self.assertIsNone(entry["analysis_code_revision"])
            self.assertIn(ONLINE_REVISION, entry["evidence_status"])
            self.assertIn("no baseline", entry["evidence_status"].lower())
            self.assertIn(OULAD_INPUT_REVISION, entry["historical_cutoff"])
            self.assertFalse(any("studentVle.csv" in path for path in entry["required_inputs"]))

    def test_l11_source_provenance_remains_unverified_and_unpublished(self):
        entry = self.by_id["l11"]
        self.assertEqual(entry["slot_status"], "proposed_milestone")
        self.assertIn(ONLINE_REVISION, entry["evidence_status"])
        self.assertIn(PLATFORM_CSV_BLOB, entry["evidence_status"])
        self.assertIn(PLATFORM_NOTEBOOK_BLOB, entry["evidence_status"])
        self.assertIn("exact dataset identity", entry["evidence_status"])
        self.assertIsNone(entry["actual_execution_date"])
        self.assertIsNone(entry["actual_publication_date"])
        self.assertIsNone(entry["analysis_code_revision"])
        self.assertNotIn("studentVle.csv", entry["required_inputs"])

        page = (ROOT / "site/projects/learning.qmd").read_text(encoding="utf-8")
        inventory = (ROOT / "data-source-evidence-inventory.md").read_text(encoding="utf-8")
        self.assertIn("No predictive model, evaluation result, or platform", page)
        self.assertIn(PLATFORM_CSV_BLOB, inventory)
        self.assertIn("collection methodology", inventory)
        self.assertIn("No `studentVle.csv` or repository code", inventory)


if __name__ == "__main__":
    unittest.main()
