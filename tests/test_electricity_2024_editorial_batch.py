import datetime as dt
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "weekly-editorial-ledger.json"


class Electricity2024EditorialBatchTests(unittest.TestCase):
    def setUp(self):
        self.entries = json.loads(LEDGER.read_text(encoding="utf-8"))["entries"]
        self.by_id = {entry.get("milestone_id"): entry for entry in self.entries}

    def test_batch_has_thirteen_electricity_wednesdays(self):
        dates = []
        current = dt.date(2024, 6, 12)
        end = dt.date(2024, 9, 4)
        while current <= end:
            dates.append(current.isoformat())
            current += dt.timedelta(days=7)
        batch = [entry for entry in self.entries if entry.get("coverage_date") in dates]
        self.assertEqual(len(dates), 13)
        self.assertEqual(len(batch), 13)
        self.assertEqual({entry["coverage_date"] for entry in batch}, set(dates))
        self.assertTrue(all(entry["featured_project"] == "electricity" for entry in batch))

    def test_e02_remains_proposed_without_duplicate_work_claim(self):
        e02 = self.by_id["e02"]
        self.assertEqual(e02["coverage_date"], "2024-07-03")
        self.assertEqual(e02["slot_status"], "proposed_milestone")
        self.assertIn("e01 quality exports already report", e02["evidence_status"])
        self.assertIsNone(e02["actual_execution_date"])
        self.assertIsNone(e02["actual_publication_date"])
        self.assertIsNone(e02.get("prepared_post"))
        self.assertEqual(e02["publication_status"], "excluded_draft; no post created")
        self.assertLessEqual(e02["estimated_minutes"]["total"], 120)

        e01_quality_path = ROOT / "site/drafts/electricity-2024-06-05-assets/quality_summary.json"
        e01_quality = json.loads(e01_quality_path.read_text(encoding="utf-8"))
        self.assertEqual(e01_quality["missing_active_power_minutes"], 25979)
        self.assertEqual(e01_quality["duplicate_timestamps"], 0)
        self.assertEqual(e01_quality["complete_days"], 1358)
        self.assertEqual(e01_quality["partial_or_incomplete_days"], 84)

    def test_e03_execution_and_exact_snapshot_provenance(self):
        e03 = self.by_id["e03"]
        self.assertEqual(e03["coverage_date"], "2024-08-07")
        self.assertEqual(e03["slot_status"], "retrospective_executed")
        self.assertEqual(e03["actual_execution_date"], "2026-11-24T13:09:50.542628-08:00")
        self.assertIsNone(e03["actual_publication_date"])
        self.assertEqual(e03["analysis_code_revision"], "2d94f2982173471a49379bcb45e537ebba23f35b")
        self.assertEqual(e03["input_data_revision"], "929ed43064487e09fe69af58f5c43d5971fa14a4")
        self.assertEqual(e03["analysis_source_sha256"], "ac056b355793410ea6a8206844051510a0a56350cb8051d99ebbcb4584c002c3")
        self.assertIn("e02 was not separately executed", e03["evidence_status"])
        self.assertIn("Git permalink available", e03["analysis_revision_availability"])
        self.assertFalse(json.loads((ROOT / "site/drafts/electricity-2024-08-07-assets/export_metadata.json").read_text(encoding="utf-8"))["analysis_revision"]["working_tree_dirty_at_execution"])

        asset_dir = ROOT / "site/drafts/electricity-2024-08-07-assets"
        snapshot = asset_dir / "household_power.py"
        self.assertEqual(hashlib.sha256(snapshot.read_bytes()).hexdigest(), e03["analysis_source_sha256"])
        metadata = json.loads((asset_dir / "export_metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["execution_timestamp"], e03["actual_execution_date"])
        self.assertEqual(metadata["analysis_revision"]["git_commit"], e03["analysis_code_revision"])
        self.assertEqual(metadata["analysis_revision"]["script_sha256"], e03["analysis_source_sha256"])
        self.assertEqual(metadata["input"]["input_commit"], e03["input_data_revision"])
        self.assertIsNone(metadata["publication_date"])

        quality = json.loads((asset_dir / "quality_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(quality["hourly_group_count"], 24)
        self.assertEqual(quality["complete_hour_groups"], 24)
        self.assertEqual(quality["timezone"], "Not specified by the source; timestamps are kept timezone-naive.")

        draft = ROOT / e03["prepared_post"]
        text = draft.read_text(encoding="utf-8")
        self.assertIn("draft: true", text)
        self.assertIn("publication-date: null", text)
        self.assertIn("not the reader's household", text)
        self.assertIn(e03["analysis_code_url"], text)

    def test_e04_is_future_proposed_work_and_other_slots_stay_unassigned(self):
        e04 = self.by_id["e04"]
        self.assertEqual(e04["coverage_date"], "2024-09-04")
        self.assertEqual(e04["slot_status"], "proposed_milestone")
        self.assertEqual(e04["prerequisites"], ["e03"])
        self.assertIsNone(e04["actual_execution_date"])
        self.assertIsNone(e04["actual_publication_date"])
        self.assertIsNone(e04.get("prepared_post"))
        self.assertEqual(e04["publication_status"], "excluded_draft; no post created")

        batch = [entry for entry in self.entries if "2024-06-12" <= entry["coverage_date"] <= "2024-09-04"]
        unassigned = [entry for entry in batch if entry["slot_status"] == "unassigned_undocumented"]
        self.assertEqual(len(unassigned), 10)
        self.assertTrue(all(entry.get("milestone_id") is None for entry in unassigned))
        self.assertTrue(all(entry["estimated_minutes"]["total"] == 0 for entry in unassigned))

    def test_e03_site_assets_are_only_aggregates_and_provenance(self):
        asset_dir = ROOT / "site/drafts/electricity-2024-08-07-assets"
        names = {path.name.lower() for path in asset_dir.iterdir() if path.is_file()}
        self.assertEqual(names, {
            "export_metadata.json", "hourly_active_power.csv",
            "hourly_active_power.svg", "household_power.py", "quality_summary.json",
        })
        self.assertFalse(any("student" in name or "learner" in name for name in names))
        self.assertFalse(any(name.endswith((".zip", ".txt", ".xlsx")) for name in names))


if __name__ == "__main__":
    unittest.main()
