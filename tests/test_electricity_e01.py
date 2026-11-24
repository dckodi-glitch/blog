import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "site/drafts/electricity-2024-06-05-assets"


class ElectricityE01Tests(unittest.TestCase):
    def test_daily_coverage_and_missing_readings(self):
        with (ASSETS / "daily_consumption.csv").open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        quality = json.loads((ASSETS / "quality_summary.json").read_text())
        self.assertEqual(len(rows), quality["day_count"])
        self.assertEqual(sum(int(row["missing_power_minutes"]) for row in rows),
                         quality["missing_active_power_minutes"])
        self.assertEqual(sum(row["complete_day"] == "true" for row in rows), quality["complete_days"])
        by_date = {row["date"]: row for row in rows}
        self.assertEqual((by_date["2006-12-16"]["expected_minutes"],
                          by_date["2010-11-26"]["expected_minutes"]), ("396", "1263"))
        missing_day = by_date["2007-04-29"]
        self.assertEqual((missing_day["daily_energy_kwh"], missing_day["valid_power_minutes"],
                          missing_day["complete_day"]), ("0.000000", "0", "false"))
        self.assertEqual(by_date["2006-12-17"]["daily_energy_kwh"], "56.507667")

    def test_metadata_and_draft_provenance(self):
        metadata = json.loads((ASSETS / "export_metadata.json").read_text())
        entries = json.loads((ROOT / "weekly-editorial-ledger.json").read_text())["entries"]
        entry = next(entry for entry in entries if entry.get("milestone_id") == "e01")
        self.assertEqual(entry["actual_execution_date"], metadata["execution_timestamp"])
        self.assertEqual(entry["analysis_source_sha256"], metadata["analysis_revision"]["script_sha256"])
        self.assertEqual(entry["input_data_revision"], metadata["input"]["input_commit"])
        self.assertIsNone(metadata["publication_date"])
        self.assertIsNone(entry["actual_publication_date"])
        post = (ROOT / entry["prepared_post"]).read_text()
        self.assertIn("draft: true", post)
        self.assertIn("publication-date: null", post)
        self.assertIn(entry["analysis_code_revision"], post)
        self.assertIn("not evidence of", post)


if __name__ == "__main__":
    unittest.main()
