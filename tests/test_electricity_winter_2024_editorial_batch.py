import datetime as dt
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "weekly-editorial-ledger.json"


class ElectricityWinter2024EditorialBatchTests(unittest.TestCase):
    def setUp(self):
        self.entries = json.loads(LEDGER.read_text(encoding="utf-8"))["entries"]
        self.by_id = {entry.get("milestone_id"): entry for entry in self.entries}

    def test_batch_has_thirteen_electricity_wednesdays(self):
        dates = []
        current = dt.date(2024, 12, 11)
        end = dt.date(2025, 3, 5)
        while current <= end:
            dates.append(current.isoformat())
            current += dt.timedelta(days=7)
        batch = [entry for entry in self.entries if entry.get("coverage_date") in dates]
        self.assertEqual(len(dates), 13)
        self.assertEqual(len(batch), 13)
        self.assertEqual({entry["coverage_date"] for entry in batch}, set(dates))
        self.assertTrue(all(entry["featured_project"] == "electricity" for entry in batch))

    def test_e08_stays_blocked_on_submeter_validation(self):
        e08 = self.by_id["e08"]
        self.assertEqual(e08["coverage_date"], "2025-01-01")
        self.assertEqual(e08["slot_status"], "proposed_milestone")
        self.assertEqual(e08["prerequisites"], ["e07"])
        self.assertIn("all required inputs are valid", e08["small_milestone"])
        self.assertIn("e07 remains proposed", e08["evidence_status"])
        self.assertIsNone(e08["actual_execution_date"])
        self.assertIsNone(e08["actual_publication_date"])
        self.assertIsNone(e08.get("prepared_post"))
        self.assertEqual(e08["publication_status"], "excluded_draft; no post created")
        self.assertLessEqual(e08["estimated_minutes"]["total"], 120)

    def test_e09_reuses_verified_completeness_and_hourly_method_without_claiming_results(self):
        e09 = self.by_id["e09"]
        self.assertEqual(e09["coverage_date"], "2025-02-05")
        self.assertEqual(e09["slot_status"], "proposed_milestone")
        self.assertEqual(e09["prerequisites"], ["e01", "e03"])
        self.assertEqual(
            e09["required_inputs"],
            [
                "electricity-changes:individual+household+electric+power+consumption.zip",
                "blog:site/drafts/electricity-2024-06-05-assets/daily_consumption.csv",
                "blog:site/drafts/electricity-2024-06-05-assets/export_metadata.json",
                "blog:site/drafts/electricity-2024-06-05-assets/quality_summary.json",
            ],
        )
        self.assertIn("explicitly defined seasons", e09["small_milestone"])
        self.assertIn("no seasonal output", e09["evidence_status"])
        self.assertIn("2d94f2982173471a49379bcb45e537ebba23f35b", e09["evidence_status"])
        self.assertIn(
            "ac056b355793410ea6a8206844051510a0a56350cb8051d99ebbcb4584c002c3",
            e09["evidence_status"],
        )
        self.assertIn("source timezone is unspecified", e09["unavailable_data_or_release_uncertainty"])
        self.assertIsNone(e09["actual_execution_date"])
        self.assertIsNone(e09["actual_publication_date"])
        self.assertIsNone(e09.get("prepared_post"))
        self.assertEqual(e09["publication_status"], "excluded_draft; no post created")
        self.assertLessEqual(e09["estimated_minutes"]["total"], 120)

        e03_metadata = json.loads(
            (ROOT / "site/drafts/electricity-2024-08-07-assets/export_metadata.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            e03_metadata["analysis_revision"]["git_commit"],
            "2d94f2982173471a49379bcb45e537ebba23f35b",
        )
        self.assertEqual(
            e03_metadata["analysis_revision"]["script_sha256"],
            "ac056b355793410ea6a8206844051510a0a56350cb8051d99ebbcb4584c002c3",
        )

    def test_e10_has_no_unneeded_dependency_and_remains_unexecuted(self):
        e10 = self.by_id["e10"]
        self.assertEqual(e10["coverage_date"], "2025-03-05")
        self.assertEqual(e10["slot_status"], "proposed_milestone")
        self.assertEqual(e10["prerequisites"], [])
        self.assertEqual(
            e10["required_inputs"],
            ["electricity-changes:individual+household+electric+power+consumption.zip"],
        )
        self.assertIn("valid and missing counts", e10["small_milestone"])
        self.assertIn("no voltage analysis or output", e10["evidence_status"])
        self.assertIsNone(e10["actual_execution_date"])
        self.assertIsNone(e10["actual_publication_date"])
        self.assertIsNone(e10.get("prepared_post"))
        self.assertEqual(e10["publication_status"], "excluded_draft; no post created")
        self.assertLessEqual(e10["estimated_minutes"]["total"], 120)

    def test_other_weeks_stay_unassigned_and_no_raw_assets_are_published(self):
        batch = [
            entry for entry in self.entries
            if "2024-12-11" <= entry["coverage_date"] <= "2025-03-05"
        ]
        unassigned = [entry for entry in batch if entry["slot_status"] == "unassigned_undocumented"]
        self.assertEqual(len(unassigned), 10)
        self.assertTrue(all(entry.get("milestone_id") is None for entry in unassigned))
        self.assertTrue(all(entry["estimated_minutes"]["total"] == 0 for entry in unassigned))

        for relative in (
            "site/drafts/electricity-2024-06-05-assets",
            "site/drafts/electricity-2024-08-07-assets",
        ):
            names = {path.name.lower() for path in (ROOT / relative).iterdir() if path.is_file()}
            self.assertFalse(any("student" in name or "learner" in name for name in names))
            self.assertFalse(any(name.endswith((".zip", ".txt")) for name in names))

        inventory = (ROOT / "data-source-evidence-inventory.md").read_text(encoding="utf-8")
        self.assertIn(
            "no residual, seasonal, voltage, or submeter-channel summaries",
            " ".join(inventory.split()),
        )
        project_status = " ".join(
            (ROOT / "site/projects/electricity.qmd").read_text(encoding="utf-8").split()
        )
        self.assertIn("other ten coverage dates from December 11", project_status)


if __name__ == "__main__":
    unittest.main()
