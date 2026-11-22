"""Keep the historical F-1 output guarantee while TD-25 refuses secret-like check IDs early.

The golden was generated on the pre-fix engine at fa6a676; do not regenerate it from this implementation.
"""
from __future__ import annotations

import contextlib
import io
from unittest import mock

from helpers import PY, ROOT, WorkflowTestCase, git

import workflow


class HistoricalLateRefusalTest(WorkflowTestCase):
    SCRIPT = ("from pathlib import Path\n"
              "print('line-one')\n"
              "print('token ' + 'ghp_' + 'A' * 36)\n"
              "print('line-two')\n"
              "Path('ran.marker').write_text('ran')\n")

    def test_run_output_precedes_a_synthetic_late_refusal(self) -> None:
        self.write("two_lines.py", self.SCRIPT)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "fixture")
        self.to_implementation()

        out, err = io.StringIO(), io.StringIO()
        refusal = workflow.WorkflowError("Synthetic late refusal after the command ran (test).")
        with mock.patch.object(workflow, "save_state", side_effect=refusal), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = workflow.main(["run", "--repo", str(self.repo), "favorites", "smoke", "--", PY,
                                  "two_lines.py"])

        self.assertTrue((self.repo / "ran.marker").exists())
        self.assertEqual(code, 1)
        self.assertIn("token [REDACTED]", out.getvalue())
        self.assertNotIn("ghp_" + "A" * 36, out.getvalue() + err.getvalue())
        self.assertLess(out.getvalue().index("line-one"), out.getvalue().index("line-two"))
        self.assertEqual(err.getvalue().strip(), "AIDevWorkflow: Synthetic late refusal after the command ran (test).")

        actual = (f"exit: {code}\n--- stdout ---\n{out.getvalue()}"
                  f"--- stderr ---\n{err.getvalue()}").replace("\r\n", "\n").encode("utf-8")
        golden = (ROOT / "tests" / "golden" / "run-output-before-late-refusal.txt").read_bytes()
        self.assertEqual(actual, golden.replace(b"\r\n", b"\n"))
