"""Golden CLI outputs: help texts and key command outputs must not change unnoticed.

The files in tests/golden/ record what the CLI prints today. A refactor that changes any of it fails here with a
diff. After an intended change, regenerate them from the tests folder and review the diff before committing:

    AIDW_UPDATE_GOLDEN=1 python3 -m unittest test_golden
"""
from __future__ import annotations

import contextlib
import difflib
import io
import os
import re
import subprocess
import sys
from pathlib import Path
from unittest import mock

from helpers import FILLED_PLAN, FILLED_SPEC, SKILL, WorkflowTestCase

# helpers puts the skill's scripts folder on sys.path, so these import the working copy's engine and installer.
import install
import workflow

GOLDEN = Path(__file__).resolve().parent / "golden"
UPDATE_ENV = "AIDW_UPDATE_GOLDEN"
TIME_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
TOOL_FOUND_RE = re.compile(r'"tool_found": (?:true|false)')
TMP_PATH_RE = re.compile(r"<TMP>[^\s\"'|)]*")
USAGE_RE = re.compile(r"(?m)^usage:[^\n]*(?:\n[ \t]+[^\n]*)*")


def capture(main, argv, expect_code: int = 0) -> str:
    """Run a CLI main() in-process and return stdout + stderr; --help exits through SystemExit, whose code is checked."""
    out, err = io.StringIO(), io.StringIO()
    code = None
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = main(list(argv))
        except SystemExit as exc:
            code = exc.code
    text = out.getvalue() + err.getvalue()
    if (code or 0) != expect_code:
        raise AssertionError(f"{' '.join(argv)} exited {code}, expected {expect_code}:\n{text}")
    return text


def normalize(text: str, tmp: Path | None = None) -> str:
    """Remove what differs between machines, operating systems and Python versions."""
    text = text.replace("\r\n", "\n")
    if tmp is not None:
        for variant in sorted({str(tmp), str(tmp.resolve()), os.path.realpath(str(tmp))}, key=len, reverse=True):
            text = text.replace(variant.replace("\\", "\\\\"), "<TMP>").replace(variant, "<TMP>")
        text = TMP_PATH_RE.sub(lambda m: m.group(0).replace("\\\\", "/").replace("\\", "/"), text)
    for exe in {sys.executable, os.path.realpath(sys.executable)}:
        text = text.replace(exe.replace("\\", "\\\\"), "<PY>").replace(exe, "<PY>")
    text = TIME_RE.sub("<TIME>", text)
    text = TOOL_FOUND_RE.sub('"tool_found": "<TOOL_FOUND>"', text)
    # Python versions wrap argparse usage lines at different points; compare each usage block as one line.
    text = USAGE_RE.sub(lambda m: " ".join(m.group(0).split()), text)
    return text.replace("optional arguments:", "options:")  # Python 3.9 vs 3.10+


class GoldenTestCase(WorkflowTestCase):
    def setUp(self) -> None:
        super().setUp()
        columns = mock.patch.dict(os.environ, {"COLUMNS": "100"})  # argparse wraps to the terminal width
        columns.start()
        self.addCleanup(columns.stop)

    def assertGolden(self, name: str, text: str) -> None:
        path = GOLDEN / name
        actual = normalize(text, self.tmp)
        if os.environ.get(UPDATE_ENV) == "1":
            GOLDEN.mkdir(exist_ok=True)
            path.write_text(actual, encoding="utf-8", newline="\n")
            return
        if not path.exists():
            self.fail(f"Golden file tests/golden/{name} is missing. Create it from the tests folder with: "
                      f"{UPDATE_ENV}=1 python3 -m unittest test_golden")
        expected = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        if actual != expected:
            diff = "".join(difflib.unified_diff(expected.splitlines(True), actual.splitlines(True),
                                                f"tests/golden/{name}", "current output"))
            self.fail(f"CLI output changed ({name}). If the change is intended, regenerate with "
                      f"{UPDATE_ENV}=1 and review the diff.\n{diff}")


def subcommands(parser) -> list:
    for action in parser._actions:  # argparse keeps subparsers here; no public accessor exists
        if action.__class__.__name__ == "_SubParsersAction":
            return list(action.choices)
    return []


class HelpGoldenTest(GoldenTestCase):
    def test_workflow_help(self) -> None:
        parts = ["=== workflow.py --help ===\n" + capture(workflow.main, ["--help"])]
        for name in subcommands(workflow.build_parser()):
            parts.append(f"=== workflow.py {name} --help ===\n" + capture(workflow.main, [name, "--help"]))
        self.assertGolden("workflow-help.txt", "\n".join(parts))

    def test_install_help(self) -> None:
        parts = ["=== install.py --help ===\n" + capture(install.main, ["--help"])]
        for name in subcommands(install.build_parser()):
            parts.append(f"=== install.py {name} --help ===\n" + capture(install.main, [name, "--help"]))
        self.assertGolden("install-help.txt", "\n".join(parts))


class CommandGoldenTest(GoldenTestCase):
    def test_init_discover_json(self) -> None:
        # A Makefile test target makes discovery suggest `make test`, whose tool_found depends on the machine (EC-5).
        self.write("Makefile", "test:\n\tpython3 -m unittest\n")
        text = self.wf("init", "--discover", "--json")
        self.assertIn('"tool_found":', text)
        self.assertGolden("init-discover.json", text)

    def test_status_spec_check_and_plan_check(self) -> None:
        self.init()
        self.new_task()
        self.to_specification()
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC)
        self.review_spec()
        # subTest: one changed output does not hide differences in the others.
        for name, args in (("spec-check.txt", ("spec-check", "favorites")), ("status-list.txt", ("status",)),
                           ("status-task.txt", ("status", "favorites"))):
            with self.subTest(golden=name):
                self.assertGolden(name, self.wf(*args))
        self.write(".ai-dev-workflow/tasks/favorites/plan.md", FILLED_PLAN)
        with self.subTest(golden="plan-check.txt"):
            self.assertGolden("plan-check.txt", self.wf("plan-check", "favorites"))

    def test_outcome_after_testing(self) -> None:
        self.to_implementation()
        self.implement_and_test()
        self.assertGolden("outcome.txt", self.wf("outcome", "favorites"))


class ScriptEntryTest(GoldenTestCase):
    """Agents and hooks run the engine as a script (`python workflow.py …`), not through main() in-process."""

    def run_script(self, script: str, *args: str) -> str:
        proc = subprocess.run([sys.executable, str(SKILL / "scripts" / script), *args], cwd=str(self.repo),
                              capture_output=True, text=True, encoding="utf-8",
                              env=dict(os.environ, COLUMNS="100", PYTHONIOENCODING="utf-8"))
        self.assertEqual(proc.returncode, 0, f"{script} {' '.join(args)} exited {proc.returncode}:\n{proc.stderr}")
        return proc.stdout + proc.stderr

    def test_scripts_run_and_match_in_process_output(self) -> None:
        self.assertEqual(self.run_script("workflow.py", "--version").strip(), f"AIDevWorkflow {workflow.__version__}")
        for script, main in (("workflow.py", workflow.main), ("install.py", install.main)):
            with self.subTest(script=script):
                self.assertEqual(normalize(self.run_script(script, "--help")), normalize(capture(main, ["--help"])))
        self.init()
        self.assertIn("No AIDevWorkflow tasks yet.", self.run_script("workflow.py", "status"))
