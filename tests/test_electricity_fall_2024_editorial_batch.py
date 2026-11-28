import csv
import datetime as dt
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "weekly-editorial-ledger.json"


class ElectricityFall2024EditorialBatchTests(unittest.TestCase):
    def setUp(self):
        self.entries = json.loads(LEDGER.read_text(encoding="utf-8"))["entries"]
        self.by_id = {entry.get("milestone_id"): entry for entry in self.entries}

    def test_batch_has_thirteen_electricity_wednesdays(self):
        dates = []
        current = dt.date(2024, 9, 11)
        end = dt.date(2024, 12, 4)
        while current <= end:
            dates.append(current.isoformat())
            current += dt.timedelta(days=7)
        batch = [entry for entry in self.entries if entry.get("coverage_date") in dates]
        self.assertEqual(len(dates), 13)
        self.assertEqual(len(batch), 13)
        self.assertEqual({entry["coverage_date"] for entry in batch}, set(dates))
        self.assertTrue(all(entry["featured_project"] == "electricity" for entry in batch))

    def test_e05_and_e06_are_distinct_proposals_using_e01_aggregates(self):
        e05 = self.by_id["e05"]
        e06 = self.by_id["e06"]
        for entry in (e05, e06):
            self.assertEqual(entry["slot_status"], "proposed_milestone")
            self.assertEqual(entry["prerequisites"], ["e01"])
            self.assertEqual(
                entry["required_inputs"],
                [
                    "blog:site/drafts/electricity-2024-06-05-assets/daily_consumption.csv",
                    "blog:site/drafts/electricity-2024-06-05-assets/export_metadata.json",
                    "blog:site/drafts/electricity-2024-06-05-assets/quality_summary.json",
                ],
            )
            self.assertIsNone(entry["actual_execution_date"])
            self.assertIsNone(entry["actual_publication_date"])
            self.assertIsNone(entry.get("prepared_post"))
            self.assertEqual(entry["publication_status"], "excluded_draft; no post created")
            self.assertLessEqual(entry["estimated_minutes"]["total"], 120)
        self.assertIn("calendar month", e05["small_milestone"])
        self.assertIn("complete-day", e06["small_milestone"])
        self.assertIn("no e05 execution or result", e05["evidence_status"])
        self.assertIn("no separate e06 distribution", e06["evidence_status"])
        self.assertIn(
            "ae46f2abe167f4d5d14395829ee3e542c7af04bb84397fbd46cbf45149a5cd37",
            e06["evidence_status"],
        )
        self.assertIn("16e57642f3bb5fc21a62bc84f48550f83cbd9081", e06["evidence_status"])
        self.assertIn(
            "dirty tree based at 929ed43064487e09fe69af58f5c43d5971fa14a4",
            e06["evidence_status"],
        )

    def test_e01_exports_support_planning_and_are_aggregate_only(self):
        assets = ROOT / "site/drafts/electricity-2024-06-05-assets"
        with (assets / "daily_consumption.csv").open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            self.assertEqual(
                reader.fieldnames,
                [
                    "date",
                    "daily_energy_kwh",
                    "expected_minutes",
                    "observed_minutes",
                    "valid_power_minutes",
                    "missing_power_minutes",
                    "observed_coverage_pct",
                    "valid_coverage_pct",
                    "complete_day",
                ],
            )
            self.assertEqual(next(reader)["date"], "2006-12-16")
        daily_path = assets / "daily_consumption.csv"
        self.assertEqual(
            hashlib.sha256(daily_path.read_bytes()).hexdigest(),
            "df297bdc4431035e9fc3cac371bb2ab355799db2b3d4cf482500b79bff60cde2",
        )
        metadata = json.loads((assets / "export_metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["input"]["input_commit"], "929ed43064487e09fe69af58f5c43d5971fa14a4")
        self.assertEqual(metadata["input"]["input_blob_sha"], "ae8864521e68b784443e4e9f55c7505812ee6c36")
        self.assertEqual(metadata["execution_timestamp"], "2026-11-14T14:30:55.191723-08:00")
        self.assertIsNone(metadata["publication_date"])

        names = {path.name.lower() for path in assets.iterdir() if path.is_file()}
        self.assertFalse(any("student" in name or "learner" in name for name in names))
        self.assertFalse(any(name.endswith((".zip", ".txt")) for name in names))

    def test_e07_remains_proposed_and_other_slots_stay_unassigned(self):
        e07 = self.by_id["e07"]
        self.assertEqual(e07["slot_status"], "proposed_milestone")
        self.assertEqual(e07["prerequisites"], ["e01"])
        self.assertEqual(
            e07["required_inputs"],
            ["electricity-changes:individual+household+electric+power+consumption.zip"],
        )
        self.assertIn("units and missingness", e07["small_milestone"])
        self.assertIn("no submeter-channel analysis or results", e07["evidence_status"])
        self.assertIn("do not infer appliance use", e07["unavailable_data_or_release_uncertainty"])
        self.assertIsNone(e07["actual_execution_date"])
        self.assertIsNone(e07["actual_publication_date"])
        self.assertIsNone(e07.get("prepared_post"))
        self.assertEqual(e07["publication_status"], "excluded_draft; no post created")
        self.assertLessEqual(e07["estimated_minutes"]["total"], 120)

        batch = [
            entry for entry in self.entries
            if "2024-09-11" <= entry["coverage_date"] <= "2024-12-04"
        ]
        unassigned = [entry for entry in batch if entry["slot_status"] == "unassigned_undocumented"]
        self.assertEqual(len(unassigned), 10)
        self.assertTrue(all(entry.get("milestone_id") is None for entry in unassigned))
        self.assertTrue(all(entry["estimated_minutes"]["total"] == 0 for entry in unassigned))

        inventory = (ROOT / "data-source-evidence-inventory.md").read_text(encoding="utf-8")
        self.assertIn("e69fadb3089e96e8dd9ea812559d840dddf13d6c", inventory)
        self.assertIn("b7f16bf4efd5e927cea47c97c40a27b8a8fd195f", inventory)
        self.assertIn("No repository code was run", inventory)
        project_status = (ROOT / "site/projects/electricity.qmd").read_text(encoding="utf-8")
        self.assertIn("other ten coverage dates", project_status)
        self.assertIn("their posts remain excluded", project_status)


if __name__ == "__main__":
    unittest.main()
