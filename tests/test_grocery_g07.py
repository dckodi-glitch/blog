import csv
import hashlib
import json
import unittest
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "site/drafts/grocery-2023-07-26-assets"


class GroceryG07Tests(unittest.TestCase):
    def test_differences_match_exported_prices(self):
        with (ASSETS / "monthly-differences.csv").open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        with (ROOT / "site/drafts/grocery-2023-06-14-assets/monthly-prices.csv").open(
            newline="", encoding="utf-8"
        ) as file:
            prices = list(csv.DictReader(file))
        self.assertEqual(len(rows), 195)
        self.assertEqual(len(prices), len(rows))
        previous = {}
        for row, original in zip(rows, prices):
            self.assertEqual((row["item"], row["observation_month"], row["price"], row["price_unit"]),
                             (original["item"], original["observation_month"], original["price"], original["unit"]))
            value = Decimal(row["price"])
            prior = previous.get(row["item"])
            if prior is None:
                self.assertEqual(row["status"], "first_month")
                self.assertEqual((row["change"], row["absolute_change"], row["percentage_change"]), ("", "", ""))
            else:
                change = value - prior
                self.assertEqual(row["status"], "ok")
                self.assertEqual(Decimal(row["change"]), change)
                self.assertEqual(Decimal(row["absolute_change"]), abs(change))
                self.assertAlmostEqual(float(row["percentage_change"]), float(change / prior * 100), places=5)
            previous[row["item"]] = value
        expected = {"bread": ("2021-09-01", "0.113"), "eggs": ("2023-03-01", "-0.765"),
                    "milk": ("2022-05-01", "0.192")}
        for item, pair in expected.items():
            largest = max((row for row in rows if row["item"] == item and row["status"] == "ok"),
                          key=lambda row: Decimal(row["absolute_change"]))
            self.assertEqual((largest["observation_month"], largest["change"]), pair)

    def test_draft_provenance(self):
        metadata = json.loads((ASSETS / "analysis-metadata.json").read_text())
        entries = json.loads((ROOT / "weekly-editorial-ledger.json").read_text())["entries"]
        entry = next(entry for entry in entries if entry.get("milestone_id") == "g07")
        code_hash = hashlib.sha256((ASSETS / "monthly_differences.py").read_bytes()).hexdigest()
        self.assertEqual(metadata["analysis_revision"]["monthly_differences.py"], f"sha256:{code_hash}")
        self.assertEqual(entry["analysis_source_sha256"], code_hash)
        self.assertEqual(entry["actual_execution_date"], metadata["execution_date"])
        self.assertEqual(entry["source_vintage"], metadata["source_vintage"])
        self.assertIsNone(entry["actual_publication_date"])
        post = (ROOT / entry["prepared_post"]).read_text()
        self.assertIn("draft: true", post)
        self.assertIn("publication-date: null", post)
        self.assertIn(code_hash, post)
        self.assertIn(entry["analysis_code_url"], post)
        self.assertIn(entry["analysis_code_revision"], entry["analysis_code_url"])


if __name__ == "__main__":
    unittest.main()
