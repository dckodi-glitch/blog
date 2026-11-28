import datetime as dt
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "weekly-editorial-ledger.json"
FANTASY_REVISION = "8ca3bba8504b00649b8d3dcc6bfde30cdb7f17eb"
OULAD_INPUT_REVISION = "a51ba30520859201319ec9efc40142153fb68fc2"
OULAD_ANALYSIS_REVISION = "2859cb40d9a120a86eb12d7c1407cd2f80c66c01"


class Winter2026EditorialBatchTests(unittest.TestCase):
    def setUp(self):
        self.entries = json.loads(LEDGER.read_text(encoding="utf-8"))["entries"]
        self.by_id = {entry.get("milestone_id"): entry for entry in self.entries}

    def test_batch_has_thirteen_dates_and_preserves_unsupported_slots(self):
        dates = []
        current = dt.date(2025, 12, 10)
        end = dt.date(2026, 3, 4)
        while current <= end:
            dates.append(current.isoformat())
            current += dt.timedelta(days=7)
        batch = [entry for entry in self.entries if entry["coverage_date"] in dates]
        self.assertEqual(len(batch), 13)
        self.assertEqual({entry["coverage_date"] for entry in batch}, set(dates))

        expected = {
            "2025-12-10": ("fantasy football", "f06", "proposed_milestone"),
            "2025-12-17": ("fantasy football", None, "unassigned_undocumented"),
            "2025-12-24": ("fantasy football", "f07", "proposed_milestone"),
            "2025-12-31": ("fantasy football", None, "unassigned_undocumented"),
            "2026-01-07": ("fantasy football", "f08", "proposed_milestone"),
            "2026-01-14": ("fantasy football", None, "unassigned_undocumented"),
            "2026-01-21": ("fantasy football", "f09", "retrospective_executed"),
            "2026-01-28": ("fantasy football", None, "unassigned_undocumented"),
            "2026-02-04": ("learning analytics", "l01", "retrospective_executed"),
            "2026-02-11": ("learning analytics", None, "unassigned_undocumented"),
            "2026-02-18": ("learning analytics", None, "unassigned_undocumented"),
            "2026-02-25": ("learning analytics", None, "unassigned_undocumented"),
            "2026-03-04": ("learning analytics", "l02", "proposed_milestone"),
        }
        for entry in batch:
            self.assertEqual(
                (entry["featured_project"], entry["milestone_id"], entry["slot_status"]),
                expected[entry["coverage_date"]],
            )
            if entry["slot_status"] == "unassigned_undocumented":
                self.assertEqual(entry["estimated_minutes"]["total"], 0)
                self.assertIsNone(entry["actual_execution_date"])
                self.assertIsNone(entry["actual_publication_date"])

    def test_proposed_milestones_use_verified_availability_but_claim_no_analysis(self):
        for milestone_id in ("f06", "f07", "f08", "l02"):
            entry = self.by_id[milestone_id]
            self.assertEqual(entry["slot_status"], "proposed_milestone")
            self.assertEqual(entry["publication_status"], "excluded_draft; no post created")
            self.assertIsNone(entry["actual_execution_date"])
            self.assertIsNone(entry["actual_publication_date"])
            self.assertIsNone(entry["analysis_code_revision"])
            self.assertLessEqual(entry["estimated_minutes"]["total"], 120)

        self.assertIn(FANTASY_REVISION, self.by_id["f06"]["evidence_status"])
        self.assertIn("99 rows labeled WK=10", self.by_id["f06"]["evidence_status"])
        self.assertIn("100 rows labeled WK=11", self.by_id["f07"]["evidence_status"])
        self.assertIn("WR11.csv, Defense11.csv and WR12Results.csv are absent",
                      self.by_id["f08"]["evidence_status"])
        self.assertIn(OULAD_INPUT_REVISION, self.by_id["l02"]["evidence_status"])
        self.assertIn("22 course-presentation rows", self.by_id["l02"]["evidence_status"])
        self.assertFalse(any("studentVle.csv" in path for path in self.by_id["l02"]["required_inputs"]))

    def test_existing_retrospectives_have_exact_provenance_and_unpublished_drafts(self):
        cases = (
            (
                "f09",
                "site/drafts/fantasy-2026-01-21-assets/provenance.json",
                "execution_timestamp_utc",
                "analysis_script_sha256",
                "repository_import_commit",
            ),
            (
                "l01",
                "site/drafts/learning-2026-02-04-assets/provenance.json",
                "executed_at",
                "analysis_revision.sha256",
                "input_commit",
            ),
        )
        for milestone_id, provenance_path, time_key, code_hash_key, input_commit_key in cases:
            entry = self.by_id[milestone_id]
            metadata = json.loads((ROOT / provenance_path).read_text(encoding="utf-8"))
            self.assertEqual(entry["actual_execution_date"], metadata[time_key])
            self.assertIsNone(entry["actual_publication_date"])
            self.assertIsNone(metadata["publication_date"])
            post = (ROOT / entry["prepared_post"]).read_text(encoding="utf-8")
            self.assertIn("draft: true", post)
            self.assertIn("publication-date: null", post)
            if milestone_id == "f09":
                self.assertEqual(entry["analysis_source_sha256"], metadata[code_hash_key])
                self.assertEqual(entry["input_data_revision"], metadata[input_commit_key])
                self.assertEqual(entry["analysis_code_revision"], FANTASY_REVISION)
            else:
                self.assertEqual(entry["analysis_source_sha256"], metadata["analysis_revision"]["sha256"])
                self.assertEqual(entry["input_data_revision"], OULAD_INPUT_REVISION)
                self.assertEqual(entry["analysis_code_revision"], OULAD_ANALYSIS_REVISION)
                self.assertFalse(any("studentVle.csv" in path for path in entry["required_inputs"]))

        learning_assets = ROOT / "site/drafts/learning-2026-02-04-assets"
        self.assertFalse(any("studentvle" in path.name.lower() for path in learning_assets.iterdir()))
        with (learning_assets / "final_results.csv").open(encoding="utf-8") as file:
            self.assertEqual(file.readline().strip(), "final_result,enrollment_count")

        inventory = (ROOT / "data-source-evidence-inventory.md").read_text(encoding="utf-8")
        self.assertIn(FANTASY_REVISION, inventory)
        self.assertIn(OULAD_INPUT_REVISION, inventory)
        self.assertIn(OULAD_ANALYSIS_REVISION, inventory)
        fantasy_page = (ROOT / "site/projects/fantasy.qmd").read_text(encoding="utf-8")
        learning_page = (ROOT / "site/projects/learning.qmd").read_text(encoding="utf-8")
        self.assertIn("/blob/8ca3bba8504b00649b8d3dcc6bfde30cdb7f17eb/retrospective_2024.py", fantasy_page)
        self.assertIn("/blob/2859cb40d9a120a86eb12d7c1407cd2f80c66c01/oulad/analyze.py", learning_page)


if __name__ == "__main__":
    unittest.main()
