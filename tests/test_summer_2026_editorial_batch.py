import csv
import datetime as dt
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "weekly-editorial-ledger.json"
ASSETS = ROOT / "site/drafts/learning-2026-02-04-assets"
L07_ASSETS = ROOT / "site/drafts/learning-2026-08-05-assets"
L01_INPUT_REVISION = "a51ba30520859201319ec9efc40142153fb68fc2"
L01_ANALYSIS_REVISION = "2859cb40d9a120a86eb12d7c1407cd2f80c66c01"
L07_INPUT_REVISION = "9f2ff2d60ef4ffa09f3fa763ac000b7c9a512ab0"
L07_ANALYSIS_SHA256 = "fc44d12f3632706f3a5eb0b4b7ca05484567d461c86d85e62bc8fe2850aaa448"


class Summer2026EditorialBatchTests(unittest.TestCase):
    def setUp(self):
        self.entries = json.loads(LEDGER.read_text(encoding="utf-8"))["entries"]
        self.by_id = {entry.get("milestone_id"): entry for entry in self.entries}

    def test_batch_has_thirteen_dates_and_preserves_unassigned_weeks(self):
        dates = []
        current = dt.date(2026, 6, 10)
        end = dt.date(2026, 9, 2)
        while current <= end:
            dates.append(current.isoformat())
            current += dt.timedelta(days=7)
        batch = [entry for entry in self.entries if entry["coverage_date"] in dates]
        self.assertEqual([entry["coverage_date"] for entry in batch], dates)
        self.assertEqual(len(batch), 13)

        expected = {
            "2026-06-10": ("learning analytics", None, "unassigned_undocumented"),
            "2026-06-17": ("learning analytics", None, "unassigned_undocumented"),
            "2026-06-24": ("learning analytics", None, "unassigned_undocumented"),
            "2026-07-01": ("learning analytics", "l06", "proposed_milestone"),
            "2026-07-08": ("learning analytics", None, "unassigned_undocumented"),
            "2026-07-15": ("learning analytics", None, "unassigned_undocumented"),
            "2026-07-22": ("learning analytics", None, "unassigned_undocumented"),
            "2026-07-29": ("learning analytics", None, "unassigned_undocumented"),
            "2026-08-05": ("learning analytics", "l07", "retrospective_executed"),
            "2026-08-12": ("learning analytics", None, "unassigned_undocumented"),
            "2026-08-19": ("learning analytics", None, "unassigned_undocumented"),
            "2026-08-26": ("learning analytics", None, "unassigned_undocumented"),
            "2026-09-02": ("learning analytics", "l08", "proposed_milestone"),
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
            elif entry["slot_status"] == "proposed_milestone":
                self.assertEqual(entry["publication_status"], "excluded_draft; no post created")
                self.assertIsNone(entry["actual_execution_date"])
                self.assertIsNone(entry["analysis_code_revision"])
                self.assertLessEqual(entry["estimated_minutes"]["total"], 120)

    def test_l06_overlaps_verified_l01_and_l07_outputs_without_a_new_claim(self):
        l06 = self.by_id["l06"]
        quality = json.loads((ASSETS / "data_quality.json").read_text(encoding="utf-8"))
        l01_provenance = json.loads((ASSETS / "provenance.json").read_text(encoding="utf-8"))
        l07_provenance = json.loads((L07_ASSETS / "provenance.json").read_text(encoding="utf-8"))
        with (L07_ASSETS / "submission_timing.csv").open(encoding="utf-8") as file:
            timing_rows = list(csv.DictReader(file))
        timing = {row["submission_category"]: int(row["submission_records"]) for row in timing_rows}

        self.assertEqual(l06["slot_status"], "proposed_milestone")
        self.assertIn(L01_INPUT_REVISION, l06["evidence_status"])
        self.assertIn(L01_ANALYSIS_REVISION, l06["evidence_status"])
        self.assertIn(L07_INPUT_REVISION, l06["evidence_status"])
        self.assertIn(L07_ANALYSIS_SHA256, l06["evidence_status"])
        self.assertIn("No distinct l06 analysis or result exists", l06["evidence_status"])
        self.assertIsNone(l06["actual_execution_date"])
        self.assertIsNone(l06["analysis_code_revision"])
        self.assertEqual(quality["input_rows"]["studentAssessment"], 173912)
        self.assertEqual(quality["candidate_key_duplicate_counts"]["studentAssessment"], 0)
        self.assertEqual(quality["join_cardinality"]["submissions_to_assessment_inner_rows"], 173912)
        self.assertEqual(quality["join_cardinality"]["submissions_to_assessment_and_enrollment_inner_rows"], 173912)
        self.assertEqual(quality["referential_integrity_errors"]["submission_missing_assessment"], 0)
        self.assertEqual(quality["referential_integrity_errors"]["submission_missing_enrollment"], 0)
        self.assertEqual(quality["missing_values_by_column"]["studentAssessment"]["score"], 173)
        self.assertEqual(quality["missing_values_by_column"]["studentAssessment"]["date_submitted"], 0)
        self.assertEqual(l01_provenance["analysis_revision"]["git_base_commit"], L01_INPUT_REVISION)
        self.assertEqual(l07_provenance["input_revisions"]["diff_data/studentAssessment.csv"]["git_commit"], L07_INPUT_REVISION)
        self.assertEqual(l07_provenance["analysis_code_revisions"]["oulad/timing.py"]["sha256"], L07_ANALYSIS_SHA256)
        self.assertEqual(self.by_id["l07"]["prerequisites"], [])
        self.assertEqual(timing["Banked (excluded)"], 1909)
        self.assertEqual(timing["Missing deadline (excluded)"], 2865)
        self.assertEqual(timing["Missing submission day (excluded)"], 0)
        self.assertIsNone(l07_provenance["publication_date"])
        self.assertNotIn("studentVle.csv", l06["required_inputs"])

        page = (ROOT / "site/projects/learning.qmd").read_text(encoding="utf-8")
        inventory = (ROOT / "data-source-evidence-inventory.md").read_text(encoding="utf-8")
        self.assertIn("l06 analysis or publication is claimed", page)
        self.assertIn("no distinct l06 analysis", inventory.lower())
        self.assertIn("studentVle.csv", inventory)


if __name__ == "__main__":
    unittest.main()
