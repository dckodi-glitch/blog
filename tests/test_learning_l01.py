import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "site/drafts/learning-2026-02-04-assets"


class LearningL01Tests(unittest.TestCase):
    def test_aggregate_results_and_integrity(self):
        with (ASSETS / "final_results.csv").open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            self.assertEqual(reader.fieldnames, ["final_result", "enrollment_count"])
            results = {row["final_result"]: int(row["enrollment_count"]) for row in reader}
        quality = json.loads((ASSETS / "data_quality.json").read_text())
        self.assertEqual(results, {"Pass": 12361, "Withdrawn": 10156, "Fail": 7052, "Distinction": 3024})
        self.assertEqual(sum(results.values()), quality["input_rows"]["studentInfo"])
        self.assertEqual(quality["input_rows"]["studentAssessment"], 173912)
        self.assertEqual(quality["input_rows"]["courses"], 22)
        self.assertEqual(quality["input_rows"]["assessments"], 206)
        self.assertTrue(all(value == 0 for value in quality["referential_integrity_errors"].values()))
        lengths = [course["length_days"] for course in quality["course_and_assessment_structure"]]
        self.assertEqual((min(lengths), max(lengths)), (234, 269))
        self.assertEqual(quality["registration_result_disagreements"], "suppressed")

    def test_provenance_and_unpublished_draft(self):
        metadata = json.loads((ASSETS / "provenance.json").read_text())
        entries = json.loads((ROOT / "weekly-editorial-ledger.json").read_text())["entries"]
        entry = next(entry for entry in entries if entry.get("milestone_id") == "l01")
        self.assertEqual(entry["actual_execution_date"], metadata["executed_at"])
        self.assertEqual(entry["analysis_source_sha256"], metadata["analysis_revision"]["sha256"])
        self.assertEqual({value["git_commit"] for value in metadata["input_revisions"].values()},
                         {entry["input_data_revision"]})
        self.assertIsNone(metadata["publication_date"])
        self.assertIsNone(entry["actual_publication_date"])
        post = (ROOT / entry["prepared_post"]).read_text()
        self.assertIn("draft: true", post)
        self.assertIn("publication-date: null", post)
        self.assertIn(entry["analysis_code_revision"], post)


if __name__ == "__main__":
    unittest.main()
