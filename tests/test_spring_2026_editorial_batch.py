import datetime as dt
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "weekly-editorial-ledger.json"
ASSETS = ROOT / "site/drafts/learning-2026-02-04-assets"
INPUT_REVISION = "a51ba30520859201319ec9efc40142153fb68fc2"
ANALYSIS_REVISION = "2859cb40d9a120a86eb12d7c1407cd2f80c66c01"


class Spring2026EditorialBatchTests(unittest.TestCase):
    def setUp(self):
        self.entries = json.loads(LEDGER.read_text(encoding="utf-8"))["entries"]
        self.by_id = {entry.get("milestone_id"): entry for entry in self.entries}

    def test_batch_keeps_only_documented_milestones_assigned(self):
        dates = []
        current = dt.date(2026, 3, 11)
        end = dt.date(2026, 6, 3)
        while current <= end:
            dates.append(current.isoformat())
            current += dt.timedelta(days=7)
        batch = [entry for entry in self.entries if entry["coverage_date"] in dates]
        self.assertEqual([entry["coverage_date"] for entry in batch], dates)
        self.assertEqual(len(batch), 13)

        expected = {
            "2026-03-11": ("learning analytics", None, "unassigned_undocumented"),
            "2026-03-18": ("learning analytics", None, "unassigned_undocumented"),
            "2026-03-25": ("learning analytics", None, "unassigned_undocumented"),
            "2026-04-01": ("learning analytics", "l03", "proposed_milestone"),
            "2026-04-08": ("learning analytics", None, "unassigned_undocumented"),
            "2026-04-15": ("learning analytics", None, "unassigned_undocumented"),
            "2026-04-22": ("learning analytics", None, "unassigned_undocumented"),
            "2026-04-29": ("learning analytics", None, "unassigned_undocumented"),
            "2026-05-06": ("learning analytics", "l04", "proposed_milestone"),
            "2026-05-13": ("learning analytics", None, "unassigned_undocumented"),
            "2026-05-20": ("learning analytics", None, "unassigned_undocumented"),
            "2026-05-27": ("learning analytics", None, "unassigned_undocumented"),
            "2026-06-03": ("learning analytics", "l05", "proposed_milestone"),
        }
        for entry in batch:
            self.assertEqual(
                (entry["featured_project"], entry["milestone_id"], entry["slot_status"]),
                expected[entry["coverage_date"]],
            )
            self.assertEqual(entry["publication_status"], "excluded_draft; no post created")
            self.assertIsNone(entry["actual_publication_date"])
            if entry["slot_status"] == "unassigned_undocumented":
                self.assertEqual(entry["estimated_minutes"]["total"], 0)
                self.assertIsNone(entry["actual_execution_date"])
            else:
                self.assertLessEqual(entry["estimated_minutes"]["total"], 120)
                self.assertEqual(
                    entry["estimated_minutes"]["analysis"]
                    + entry["estimated_minutes"]["validation"]
                    + entry["estimated_minutes"]["writing"],
                    entry["estimated_minutes"]["total"],
                )
                self.assertIsNone(entry["actual_execution_date"])
                self.assertIsNone(entry["analysis_code_revision"])

    def test_l03_overlap_is_provenanced_without_claiming_a_second_run(self):
        entry = self.by_id["l03"]
        quality = json.loads((ASSETS / "data_quality.json").read_text(encoding="utf-8"))
        provenance = json.loads((ASSETS / "provenance.json").read_text(encoding="utf-8"))

        self.assertEqual(entry["slot_status"], "proposed_milestone")
        self.assertIn(INPUT_REVISION, entry["historical_cutoff"])
        self.assertIn(INPUT_REVISION, entry["evidence_status"])
        self.assertIn(ANALYSIS_REVISION, entry["evidence_status"])
        self.assertIn("No separate l03 analysis or result exists", entry["evidence_status"])
        self.assertIsNone(entry["actual_execution_date"])
        self.assertIsNone(entry["analysis_code_revision"])
        self.assertEqual(quality["candidate_key_duplicate_counts"]["studentRegistration"], 0)
        self.assertEqual(quality["join_cardinality"]["info_registration_inner_rows"], 32593)
        self.assertEqual(quality["referential_integrity_errors"]["info_missing_registration"], 0)
        self.assertEqual(quality["missing_values_by_column"]["studentRegistration"]["date_registration"], 45)
        self.assertEqual(quality["missing_values_by_column"]["studentRegistration"]["date_unregistration"], 22521)
        self.assertEqual(provenance["executed_at"], "2026-11-23T06:33:35.647869+00:00")
        self.assertEqual(provenance["input_revisions"]["diff_data/studentRegistration.csv"]["git_commit"], INPUT_REVISION)
        self.assertEqual(provenance["analysis_revision"]["git_base_commit"], INPUT_REVISION)
        self.assertIsNone(provenance["publication_date"])
        self.assertNotIn("studentVle.csv", entry["evidence_status"])
        self.assertNotIn("studentVle.csv", entry["required_inputs"])

        page = (ROOT / "site/projects/learning.qmd").read_text(encoding="utf-8")
        inventory = (ROOT / "data-source-evidence-inventory.md").read_text(encoding="utf-8")
        self.assertIn("No second result or publication is claimed", page)
        self.assertIn("No distinct l03 run or result was found", inventory)
        self.assertIn("studentVle.csv` was not accessed", inventory)


if __name__ == "__main__":
    unittest.main()
