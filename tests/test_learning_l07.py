import csv
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "site/drafts/learning-2026-08-05-assets"


class LearningL07Tests(unittest.TestCase):
    def test_aggregate_table_matches_figure(self):
        with (ASSETS / "submission_timing.csv").open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            self.assertEqual(reader.fieldnames, ["submission_category", "submission_records"])
            rows = list(reader)
        expected = [("More than 7 days early", 38599), ("1-7 days early", 51752),
                    ("On due day", 29469), ("1-7 days late", 43416),
                    ("More than 7 days late", 5902), ("Banked (excluded)", 1909),
                    ("Missing deadline (excluded)", 2865), ("Missing submission day (excluded)", 0)]
        self.assertEqual([(row["submission_category"], int(row["submission_records"])) for row in rows], expected)
        text = [node.text for node in ET.parse(ASSETS / "submission_timing.svg").getroot().iter()
                if node.tag.endswith("text")]
        for label, count in expected:
            index = text.index(label)
            self.assertEqual(text[index + 1], f"{count:,}")
        self.assertEqual(sum(count for _, count in expected[:5]), 169138)
        self.assertTrue(all(count == 0 or count >= 10 for _, count in expected))

    def test_provenance_and_unpublished_draft(self):
        metadata = json.loads((ASSETS / "provenance.json").read_text())
        entries = json.loads((ROOT / "weekly-editorial-ledger.json").read_text())["entries"]
        entry = next(entry for entry in entries if entry.get("milestone_id") == "l07")
        code = metadata["analysis_code_revisions"]["oulad/timing.py"]
        self.assertEqual(entry["actual_execution_date"], metadata["executed_at"])
        self.assertEqual(entry["analysis_source_sha256"], code["sha256"])
        self.assertEqual(entry["analysis_source_git_blob"], code["working_file_git_blob"])
        self.assertEqual({value["git_commit"] for value in metadata["input_revisions"].values()},
                         {entry["input_data_revision"]})
        self.assertIsNone(metadata["publication_date"])
        self.assertIsNone(entry["actual_publication_date"])
        self.assertIsNone(entry["analysis_code_revision"])
        post = (ROOT / entry["prepared_post"]).read_text()
        self.assertIn("draft: true", post)
        self.assertIn("publication-date: null", post)
        self.assertIn(code["sha256"], post)


if __name__ == "__main__":
    unittest.main()
