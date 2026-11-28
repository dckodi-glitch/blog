import datetime as dt
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "weekly-editorial-ledger.json"
FANTASY_REVISION = "8ca3bba8504b00649b8d3dcc6bfde30cdb7f17eb"


class FantasyFall2025EditorialBatchTests(unittest.TestCase):
    def setUp(self):
        self.entries = json.loads(LEDGER.read_text(encoding="utf-8"))["entries"]
        self.by_id = {entry.get("milestone_id"): entry for entry in self.entries}

    def test_batch_has_thirteen_wednesdays_and_only_supported_fantasy_assignments(self):
        dates = []
        current = dt.date(2025, 9, 10)
        end = dt.date(2025, 12, 3)
        while current <= end:
            dates.append(current.isoformat())
            current += dt.timedelta(days=7)

        batch = [entry for entry in self.entries if entry["coverage_date"] in dates]
        self.assertEqual(len(batch), 13)
        self.assertEqual({entry["coverage_date"] for entry in batch}, set(dates))

        assigned = {
            entry["coverage_date"]: entry["milestone_id"]
            for entry in batch
            if entry["milestone_id"] is not None
        }
        self.assertEqual(
            assigned,
            {
                "2025-10-01": "f01",
                "2025-10-15": "f02",
                "2025-10-29": "f03",
                "2025-11-12": "f04",
                "2025-11-26": "f05",
            },
        )
        self.assertTrue(
            all(
                entry["featured_project"] == "fantasy football"
                for entry in batch
                if entry["milestone_id"] is not None
            )
        )

    def test_f02_records_only_the_verified_source_inspection(self):
        f02 = self.by_id["f02"]
        self.assertEqual(f02["slot_status"], "retrospective_executed")
        self.assertEqual(f02["actual_execution_date"], "2026-11-24T13:11:48-08:00")
        self.assertIsNone(f02["actual_publication_date"])
        self.assertIsNone(f02["analysis_code_revision"])
        self.assertEqual(f02["evidence_repository_revision"], FANTASY_REVISION)
        self.assertEqual(f02["prerequisites"], [])
        self.assertEqual(f02["publication_status"], "excluded_draft; prepared locally, not published")

        draft = (ROOT / f02["prepared_post"]).read_text(encoding="utf-8")
        self.assertIn("publication-date: null", draft)
        self.assertIn("draft: true", draft)
        self.assertIn("No cells were run during this inspection", draft)
        self.assertIn("do not establish an execution date", draft)

    def test_proposed_milestones_remain_excluded_within_budget(self):
        for milestone_id in ("f01", "f03", "f04", "f05"):
            entry = self.by_id[milestone_id]
            self.assertEqual(entry["slot_status"], "proposed_milestone")
            self.assertIsNone(entry["actual_execution_date"])
            self.assertIsNone(entry["actual_publication_date"])
            self.assertIsNone(entry["analysis_code_revision"])
            self.assertEqual(entry["publication_status"], "excluded_draft; no post created")
            self.assertIsNone(entry.get("prepared_post"))
            self.assertLessEqual(entry["estimated_minutes"]["total"], 120)

        self.assertEqual(self.by_id["f03"]["prerequisites"], ["f01", "f02"])
        self.assertEqual(self.by_id["f04"]["prerequisites"], ["f03"])
        self.assertEqual(self.by_id["f05"]["prerequisites"], ["f03"])
        self.assertIn("no join validation or comparison was executed", self.by_id["f03"]["evidence_status"])
        self.assertIn("no comparison was executed", self.by_id["f04"]["evidence_status"])
        self.assertIn("no join validation or comparison was executed", self.by_id["f05"]["evidence_status"])

    def test_eight_unsupported_dates_stay_unassigned_and_source_provenance_is_visible(self):
        expected = {
            "2025-09-10",
            "2025-09-17",
            "2025-09-24",
            "2025-10-08",
            "2025-10-22",
            "2025-11-05",
            "2025-11-19",
            "2025-12-03",
        }
        unassigned = {
            entry["coverage_date"]: entry
            for entry in self.entries
            if entry["coverage_date"] in expected
        }
        self.assertEqual(set(unassigned), expected)
        for entry in unassigned.values():
            self.assertEqual(entry["slot_status"], "unassigned_undocumented")
            self.assertEqual(entry["estimated_minutes"]["total"], 0)
            self.assertIsNone(entry["actual_execution_date"])
            self.assertIsNone(entry["actual_publication_date"])

        inventory = (ROOT / "data-source-evidence-inventory.md").read_text(encoding="utf-8")
        self.assertIn(FANTASY_REVISION, inventory)
        self.assertIn("7351372877f6d3ec57aee08c7282fa019899ebd1", inventory)
        self.assertIn("No notebook cells were run during this inspection", inventory)
        self.assertIn("b066fef0b5d017ae3686d5f5447bae0a83229f46", inventory)

        project = (ROOT / "site/projects/fantasy.qmd").read_text(encoding="utf-8")
        self.assertIn(FANTASY_REVISION, project)
        self.assertIn("performed no new joins or matchup comparisons", project)


if __name__ == "__main__":
    unittest.main()
