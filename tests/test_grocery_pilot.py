import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "site/drafts/grocery-2023-06-14-assets"


class GroceryPilotTests(unittest.TestCase):
    def test_exported_prices_and_quality(self):
        with (ASSETS / "monthly-prices.csv").open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        with (ASSETS / "data-quality.csv").open(newline="", encoding="utf-8") as file:
            quality = list(csv.DictReader(file))
        self.assertEqual(len(rows), 195)
        expected = {"bread": "1.951", "eggs": "2.666", "milk": "4.042"}
        self.assertEqual(
            {row["item"]: row["price"] for row in rows
             if row["observation_month"] == "2023-05-01"},
            expected,
        )
        self.assertEqual(len(quality), 3)
        for row in quality:
            self.assertEqual(row["rows"], "65")
            for key in ("duplicate_dates", "missing_months", "malformed_dates",
                        "missing_values", "invalid_values", "out_of_range_dates"):
                self.assertEqual(row[key], "0", (row["item"], key))

    def test_execution_and_publication_are_separate(self):
        metadata = json.loads((ASSETS / "analysis-metadata.json").read_text())
        ledger = json.loads((ROOT / "weekly-editorial-ledger.json").read_text())
        entry = ledger["entries"][0]
        self.assertEqual(entry["coverage_date"], "2023-06-14")
        self.assertEqual(metadata["source_vintage"], "2023-06-13")
        self.assertEqual(entry["actual_execution_date"], metadata["execution_date"])
        self.assertIsNone(metadata["publication_date"])
        self.assertIsNone(entry["actual_publication_date"])
        post = (ROOT / entry["prepared_post"]).read_text()
        self.assertIn("draft: true", post)
        self.assertIn("publication-date: null", post)
        self.assertIn(entry["analysis_code_revision"], post)


if __name__ == "__main__":
    unittest.main()
