import datetime as dt
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "weekly-editorial-ledger.json"


class Spring2024EditorialBatchTests(unittest.TestCase):
    def setUp(self):
        self.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        self.entries = self.ledger["entries"]
        self.by_id = {entry.get("milestone_id"): entry for entry in self.entries}

    def test_batch_has_thirteen_wednesdays_and_one_project_per_slot(self):
        dates = []
        current = dt.date(2024, 3, 13)
        end = dt.date(2024, 6, 5)
        while current <= end:
            dates.append(current.isoformat())
            current += dt.timedelta(days=7)
        batch = [entry for entry in self.entries if entry.get("coverage_date") in dates]
        self.assertEqual(len(dates), 13)
        self.assertEqual(len(batch), 13)
        self.assertEqual({entry["coverage_date"] for entry in batch}, set(dates))
        self.assertEqual(self.by_id["g12"]["featured_project"], "groceries")
        self.assertEqual(self.by_id["e01"]["featured_project"], "electricity")

    def test_g12_is_planned_but_waits_on_unexecuted_prerequisites(self):
        g12 = self.by_id["g12"]
        self.assertEqual(g12["coverage_date"], "2024-05-01")
        self.assertEqual(g12["slot_status"], "proposed_milestone")
        self.assertEqual(g12["prerequisites"], ["g06", "g07", "g08"])
        self.assertEqual(self.by_id["g06"]["slot_status"], "proposed_milestone")
        self.assertEqual(self.by_id["g08"]["slot_status"], "proposed_milestone")
        self.assertIn("g06 and g08 remain unexecuted", g12["evidence_status"])
        self.assertIsNone(g12["actual_execution_date"])
        self.assertIsNone(g12["actual_publication_date"])
        self.assertIsNone(g12.get("prepared_post"))
        self.assertEqual(g12["publication_status"], "excluded_draft; no post created")
        self.assertEqual(g12["estimated_minutes"]["total"], 120)

    def test_e01_uses_exact_existing_execution_and_source_provenance(self):
        e01 = self.by_id["e01"]
        self.assertEqual(e01["coverage_date"], "2024-06-05")
        self.assertEqual(e01["slot_status"], "retrospective_executed")
        self.assertEqual(e01["actual_execution_date"], "2026-11-14T14:30:55.191723-08:00")
        self.assertIsNone(e01["actual_publication_date"])
        self.assertEqual(e01["analysis_code_revision"], "16e57642f3bb5fc21a62bc84f48550f83cbd9081")
        self.assertEqual(e01["input_data_revision"], "929ed43064487e09fe69af58f5c43d5971fa14a4")
        self.assertEqual(e01["analysis_source_sha256"], "ae46f2abe167f4d5d14395829ee3e542c7af04bb84397fbd46cbf45149a5cd37")

        draft = ROOT / e01["prepared_post"]
        text = draft.read_text(encoding="utf-8")
        self.assertIn("draft: true", text)
        self.assertIn("publication-date: null", text)
        self.assertIn(e01["analysis_code_revision"], text)
        self.assertIn("November 14, 2026", text)

        metadata_path = ROOT / "site/drafts/electricity-2024-06-05-assets/export_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.assertEqual(metadata["execution_timestamp"], e01["actual_execution_date"])
        self.assertEqual(metadata["analysis_revision"]["script_sha256"], e01["analysis_source_sha256"])
        self.assertEqual(metadata["input"]["input_commit"], e01["input_data_revision"])
        self.assertEqual(metadata["input"]["input_blob_sha"], "ae8864521e68b784443e4e9f55c7505812ee6c36")
        self.assertEqual(metadata["input"]["local_sha256"], "9f84b46ade8a2d8e1286ec4b2b6c2987a45a755c59f263be3b3b3d10dfbda3ff")
        self.assertEqual(metadata["publication_date"], e01["actual_publication_date"])

    def test_e01_site_assets_are_curated_aggregates(self):
        asset_dir = ROOT / "site/drafts/electricity-2024-06-05-assets"
        names = {path.name.lower() for path in asset_dir.iterdir() if path.is_file()}
        self.assertEqual(names, {
            "daily_consumption.csv", "daily_consumption.svg",
            "quality_summary.json", "export_metadata.json",
        })
        self.assertFalse(any("student" in name or "learner" in name for name in names))
        self.assertFalse(any(name.endswith((".zip", ".txt", ".xlsx")) for name in names))


if __name__ == "__main__":
    unittest.main()
