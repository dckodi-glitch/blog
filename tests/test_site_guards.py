import datetime as dt
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from shutil import copyfile


ROOT = Path(__file__).resolve().parents[1]


class PostGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "projects").mkdir()
        (self.root / "posts").mkdir()
        copyfile(ROOT / "site/check-published-posts.py", self.root / "check.py")
        for name in ("index.qmd", "archive.qmd", "methodology.qmd"):
            (self.root / name).write_text("---\ntitle: Page\n---\n", encoding="utf-8")

    def run_guard(self, content):
        (self.root / "posts/post.qmd").write_text(content, encoding="utf-8")
        return subprocess.run([sys.executable, str(self.root / "check.py")],
                              text=True, capture_output=True)

    def post(self, *, day="2023-06-14", publication="2023-06-15", draft="false", extra=""):
        return (
            f"---\ntitle: Example\ndate: {day}\npublication-date: {publication}\n"
            f"draft: {draft}\n---\n{extra}\n"
            "[Code](https://github.com/example/project/blob/"
            "0123456789abcdef0123456789abcdef01234567/analysis.py)\n"
        )

    def test_reviewed_post_passes(self):
        self.assertEqual(self.run_guard(self.post()).returncode, 0)

    def test_future_and_draft_posts_fail_closed(self):
        future = (dt.datetime.now(dt.timezone.utc).date() + dt.timedelta(days=1)).isoformat()
        for post in (self.post(day=future), self.post(publication=future),
                     self.post(draft="true")):
            with self.subTest(post=post):
                self.assertNotEqual(self.run_guard(post).returncode, 0)

    def test_executable_or_included_content_fails(self):
        for extra in ("```{python}\nprint('x')\n```",
                      "{{< include ../../implementation-plan.md >}}"):
            with self.subTest(extra=extra):
                self.assertNotEqual(self.run_guard(self.post(extra=extra)).returncode, 0)

    def test_missing_revision_link_fails(self):
        self.assertNotEqual(self.run_guard(self.post().replace("/blob/", "/tree/")).returncode, 0)


class OutputGuardTests(unittest.TestCase):
    def test_raw_data_and_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text("ok", encoding="utf-8")
            check = ROOT / "site/check-output.py"
            cmd = [sys.executable, str(check), str(root)]
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            (root / "studentInfo.csv").write_text("private", encoding="utf-8")
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            (root / "studentInfo.csv").unlink()
            (root / "linked.html").symlink_to(root / "index.html")
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
