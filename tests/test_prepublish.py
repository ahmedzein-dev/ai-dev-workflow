"""tools/prepublish_check.py finds secrets, private details and copies of private files."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("prepublish_check", ROOT / "tools" / "prepublish_check.py")
prepublish = importlib.util.module_from_spec(spec)
EMAIL = "alice" + "@" + "corp-internal.io"
HOME_PATH = "/Us" + "ers/alice"
spec.loader.exec_module(prepublish)


class PrepublishTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aidw-pre-"))
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=str(self.repo), check=True)
        (self.repo / "README.md").write_text("# Clean project\n\nNothing private here; contact dev@example.com.\n",
                                             encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_check(self, *args: str) -> tuple:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = prepublish.main(["--root", str(self.repo), *args])
        return code, out.getvalue()

    def test_clean_repository_passes(self) -> None:
        self.assertEqual(self.run_check()[0], 0)

    def test_finds_secrets_emails_home_paths_and_private_terms(self) -> None:
        (self.repo / "notes.md").write_text(
            "key " + "AKIA" + "ABCDEFGHIJKLMNOP" + "\nmail " + EMAIL + "\npath " + HOME_PATH + "/work\nclient Acme Rockets\n",
            encoding="utf-8")
        terms = self.tmp / "private-terms.txt"
        terms.write_text("acme rockets\n", encoding="utf-8")
        code, out = self.run_check("--private-terms", str(terms))
        self.assertEqual(code, 1)
        for expected in ("AWS access key", EMAIL, HOME_PATH, "private term"):
            self.assertIn(expected, out)

    def test_detects_copies_of_private_files(self) -> None:
        private = self.tmp / "private"
        private.mkdir()
        lines = [f"This is a distinctive private template line number {n} with enough length." for n in range(5)]
        (private / "template.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        (self.repo / "copy.md").write_text("\n".join(lines[:3]) + "\n", encoding="utf-8")
        code, out = self.run_check("--fingerprints", str(private))
        self.assertEqual(code, 1)
        self.assertIn("shares 3 lines with private file template.md", out)

    def test_private_terms_file_must_live_outside_the_repository(self) -> None:
        inside = self.repo / "terms.txt"
        inside.write_text("x\n", encoding="utf-8")
        self.assertEqual(self.run_check("--private-terms", str(inside))[0], 2)


if __name__ == "__main__":
    unittest.main()
