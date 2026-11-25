import csv
import hashlib
import json
import unittest
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "site/drafts/electricity-2024-08-07-assets"


class ElectricityE03Tests(unittest.TestCase):
    def test_hourly_summary_and_coverage(self):
        with (ASSETS / "hourly_active_power.csv").open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        quality = json.loads((ASSETS / "quality_summary.json").read_text())
        self.assertEqual(len(rows), 24)
        self.assertEqual([row["hour_of_day"] for row in rows], [f"{hour:02d}:00" for hour in range(24)])
        self.assertEqual(sum(int(row["valid_power_minutes"]) for row in rows),
                         quality["valid_active_power_minutes"])
        self.assertEqual(sum(int(row["missing_power_minutes"]) for row in rows),
                         quality["missing_active_power_minutes"])
        for row in rows:
            expected = int(row["expected_minutes"])
            valid = int(row["valid_power_minutes"])
            self.assertEqual(row["complete_hour"], "true" if valid * 10 >= expected * 9 else "false")
            self.assertAlmostEqual(float(row["valid_coverage_pct"]), 100 * valid / expected, places=3)
            self.assertEqual(bool(row["mean_active_power_kw"]), row["complete_hour"] == "true")
        low = min(rows, key=lambda row: Decimal(row["mean_active_power_kw"]))
        high = max(rows, key=lambda row: Decimal(row["mean_active_power_kw"]))
        self.assertEqual((low["hour_of_day"], low["mean_active_power_kw"]), ("04:00", "0.443847"))
        self.assertEqual((high["hour_of_day"], high["mean_active_power_kw"]), ("20:00", "1.899064"))

    def test_source_provenance_and_unpublished_draft(self):
        metadata = json.loads((ASSETS / "export_metadata.json").read_text())
        entries = json.loads((ROOT / "weekly-editorial-ledger.json").read_text())["entries"]
        entry = next(entry for entry in entries if entry.get("milestone_id") == "e03")
        source_hash = hashlib.sha256((ASSETS / "household_power.py").read_bytes()).hexdigest()
        self.assertEqual(entry["analysis_source_sha256"], source_hash)
        self.assertEqual(metadata["analysis_revision"]["script_sha256"], source_hash)
        self.assertEqual(entry["actual_execution_date"], metadata["execution_timestamp"])
        self.assertEqual(entry["input_data_revision"], metadata["input"]["input_commit"])
        self.assertEqual(entry["analysis_code_revision"], metadata["analysis_revision"]["git_commit"])
        self.assertEqual(entry["analysis_code_revision"], "2d94f2982173471a49379bcb45e537ebba23f35b")
        self.assertEqual(
            entry["analysis_code_url"],
            f"https://github.com/dckodi-glitch/electricity-changes/blob/{entry['analysis_code_revision']}/analysis/household_power.py",
        )
        self.assertFalse(metadata["analysis_revision"]["working_tree_dirty_at_execution"])
        self.assertIsNone(metadata["publication_date"])
        self.assertIsNone(entry["actual_publication_date"])
        post = (ROOT / entry["prepared_post"]).read_text()
        self.assertIn("draft: true", post)
        self.assertIn("publication-date: null", post)
        self.assertIn(source_hash, post)
        self.assertIn(entry["analysis_code_url"], post)


if __name__ == "__main__":
    unittest.main()
