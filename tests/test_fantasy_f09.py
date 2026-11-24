import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "site/drafts/fantasy-2026-01-21-assets"


class FantasyF09Tests(unittest.TestCase):
    def test_held_out_summary(self):
        with (ASSETS / "summary.csv").open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        held_out = next(row for row in rows if row["split"] == "test" and row["week"] == "all")
        self.assertEqual((held_out["candidate_rows"], held_out["scored_rows"],
                          held_out["evaluated"], held_out["missing_prior_history"]),
                         ("696", "696", "686", "10"))
        self.assertEqual(f'{float(held_out["coverage"]) * 100:.2f}%', "98.56%")
        self.assertEqual(f'{float(held_out["mae"]):.2f}', "4.43")
        self.assertEqual(f'{float(held_out["rmse"]):.2f}', "6.48")

    def test_provenance_and_unpublished_draft(self):
        metadata = json.loads((ASSETS / "provenance.json").read_text())
        entries = json.loads((ROOT / "weekly-editorial-ledger.json").read_text())["entries"]
        entry = next(entry for entry in entries if entry.get("milestone_id") == "f09")
        self.assertEqual(entry["actual_execution_date"], metadata["execution_timestamp_utc"])
        self.assertEqual(entry["analysis_source_sha256"], metadata["analysis_script_sha256"])
        self.assertEqual(entry["input_data_revision"], metadata["repository_import_commit"])
        self.assertIsNone(metadata["publication_date"])
        self.assertIsNone(entry["actual_publication_date"])
        post = (ROOT / entry["prepared_post"]).read_text()
        self.assertIn("draft: true", post)
        self.assertIn("publication-date: null", post)
        self.assertIn(entry["analysis_code_revision"], post)
        self.assertIn(entry["input_data_revision"], post)


if __name__ == "__main__":
    unittest.main()
