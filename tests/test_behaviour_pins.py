"""Behaviour pinned before the F1.0.4 engine-API refactor: signatures, refusals and `preflight --json`.

The golden files these tests read were generated from the engine as it was before F1.0.4 (spec FR-6, FR-8, FR-11).
They are a baseline, not a convenience: never regenerate them to make a refactor pass. A difference is a regression.

- tests/golden/workflow-public-signatures.txt  — the call signature of every public function importable from workflow
- tests/golden/refusals.json                   — refused commands: exit code, stdout, stderr (normalised)
- tests/golden/preflight-json-*.txt            — `preflight --json` output, including today's trailing text (TD-24)

Every refusal test also compares the bytes of every file under .ai-dev-workflow/ before and after the refused
command, inside the test itself, so record integrity is checked exactly and on every platform.
"""
from __future__ import annotations

import contextlib
import inspect
import io
import json
import os
from pathlib import Path
from typing import Callable, Dict, Tuple, Union

from helpers import EXAMPLE_TEMPLATE, FILLED_PLAN, FILLED_SPEC, PY, git
from test_golden import GOLDEN, UPDATE_ENV, GoldenTestCase, normalize

import workflow

NAMES_FILE = GOLDEN / "workflow-public-names.txt"
SIGNATURES_FILE = GOLDEN / "workflow-public-signatures.txt"
REFUSALS_FILE = GOLDEN / "refusals.json"


def describe_signature(func: Callable) -> str:
    """Parameter names, kinds and defaults; annotations are left out (their text differs between Python versions)."""
    parts = []
    seen_kw_only = False
    for param in inspect.signature(func).parameters.values():
        if param.kind is param.KEYWORD_ONLY and not seen_kw_only:
            parts.append("*")
            seen_kw_only = True
        text = {param.VAR_POSITIONAL: "*", param.VAR_KEYWORD: "**"}.get(param.kind, "") + param.name
        if param.default is not param.empty:
            text += "=" + repr(param.default)
        parts.append(text)
    return f"{func.__name__}({', '.join(parts)})"


def public_signatures() -> str:
    names = [n for n in NAMES_FILE.read_text(encoding="utf-8").split() if n]
    lines = []
    for name in names:
        obj = getattr(workflow, name)
        if inspect.isfunction(obj):
            lines.append(f"{name}: {describe_signature(obj)}")
    return "\n".join(lines) + "\n"


class SignaturesTest(GoldenTestCase):
    def test_public_function_signatures_are_unchanged(self) -> None:
        actual = public_signatures()
        if os.environ.get(UPDATE_ENV) == "1" and not SIGNATURES_FILE.exists():
            SIGNATURES_FILE.write_text(actual, encoding="utf-8", newline="\n")
        self.assertEqual(SIGNATURES_FILE.read_text(encoding="utf-8").replace("\r\n", "\n"), actual)


def snapshot(root: Path) -> Dict[str, bytes]:
    records = root / ".ai-dev-workflow"
    if not records.exists():
        return {}
    return {p.relative_to(records).as_posix(): p.read_bytes() for p in sorted(records.rglob("*")) if p.is_file()}


class RefusalsTest(GoldenTestCase):
    """Each scenario prepares a state, then runs one command the engine must refuse."""

    def refuse(self, command: str, *args: str) -> Tuple[int, str, str]:
        before = snapshot(self.repo)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = workflow.main([command, "--repo", str(self.repo), *args])
        after = snapshot(self.repo)
        self.assertEqual(sorted(before), sorted(after), f"{command}: files under .ai-dev-workflow/ were added or removed")
        for rel, data in before.items():
            self.assertEqual(data, after[rel], f"{command}: .ai-dev-workflow/{rel} changed although the command was refused")
        return code, out.getvalue(), err.getvalue()

    def to_spec_approval(self) -> None:
        self.init()
        self.new_task()
        self.to_specification()
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC)
        self.review_spec()
        self.wf("stage", "favorites", "SPEC_APPROVAL")

    def to_plan_approval_then_change_spec(self) -> None:
        self.to_spec_approval()
        self.wf("approve", "favorites", "spec", "--evidence", "Approve spec v1")
        self.write(".ai-dev-workflow/tasks/favorites/plan.md", FILLED_PLAN)
        self.wf("stage", "favorites", "PLAN_APPROVAL")
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC + "\nChanged after approval.\n")

    def scenarios(self) -> Dict[str, Tuple[Callable[[], None], Union[Tuple[str, ...], Callable[[], Tuple[str, ...]]]]]:
        secret = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"
        return {
            "init-twice": (self.init, ("init", "--template", "x.md", "--commit", "all")),
            "new-without-skill-name": (self.init, ("new", "favorites", "--title", "Saved favorites",
                                                    "--invocation", "add saved favorites please")),
            "new-bad-task-name": (self.init, ("new", "Bad_Name", "--title", "T", "--invocation", "/ai-dev-workflow x")),
            "new-existing-task": (lambda: (self.init(), self.new_task()),
                                  ("new", "favorites", "--title", "Again", "--invocation", "/ai-dev-workflow again")),
            "stage-gate-template-spec": (lambda: (self.init(), self.new_task(), self.to_specification()),
                                         ("stage", "favorites", "SPEC_APPROVAL")),
            "approve-spec-wrong-stage": (lambda: (self.init(), self.new_task(), self.to_specification()),
                                         ("approve", "favorites", "spec", "--evidence", "Approve spec v1")),
            "approve-short-evidence": (self.to_spec_approval, ("approve", "favorites", "spec", "--evidence", "x")),
            "approve-secret-in-evidence": (self.to_spec_approval,
                                           ("approve", "favorites", "spec", "--evidence", f"approved {secret}")),
            "approve-plan-wrong-stage": (self.to_spec_approval,
                                         ("approve", "favorites", "plan", "--evidence", "Plan approved")),
            "review-unknown-map-target": (lambda: (self.init(), self.new_task(), self.to_specification(),
                                                   self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC)),
                                          ("review", "favorites", "--map", "REQ-1=AC-9")),
            "step-outside-code-stage": (self.to_spec_approval, ("step", "favorites", "S1", "done")),
            "run-unknown-check": (self.to_implementation, ("run", "favorites", "nosuch")),
            "run-baseline-non-analyzer": (self.to_implementation, ("run", "favorites", "unit", "--baseline")),
            "scope-exclude-without-reason": (self.to_implementation, ("scope", "favorites", "--exclude", "app.py")),
            "decision-without-evidence": (self.to_implementation, ("decision", "favorites", "--text", "Use a set", "--evidence", "   ")),
            "close-outside-final-report": (self.to_implementation, ("close", "favorites")),
            "stage-secret-in-reason": (self.to_implementation,
                                       ("stage", "favorites", "PLANNING", "--reason", "pass" + "word: hunter2hunter2")),
            # Added after the independent audit (F-8); recorded, like the others, from the pre-refactor engine.
            "unknown-task": (self.init, ("status", "nosuch")),
            "new-before-setup": (lambda: None, ("new", "favorites", "--title", "T", "--invocation", "/ai-dev-workflow x")),
            "init-without-commit": (lambda: None, ("init", "--template", str(EXAMPLE_TEMPLATE))),
            "init-without-template": (lambda: None, ("init", "--commit", "all")),
            "init-update-nothing-to-change": (self.init, ("init", "--update")),
            "approve-spec-not-ready": (lambda: (self.to_spec_approval(), self.write(
                ".ai-dev-workflow/tasks/favorites/spec.md", EXAMPLE_TEMPLATE.read_text(encoding="utf-8"))),
                                       ("approve", "favorites", "spec", "--evidence", "Approve spec v1")),
            "approve-plan-after-spec-changed": (self.to_plan_approval_then_change_spec,
                                                ("approve", "favorites", "plan", "--evidence", "Plan approved")),
            "review-dismiss-unknown-flag": (lambda: (self.init(), self.new_task(), self.to_specification()),
                                            ("review", "favorites", "--dismiss", "NOFLAG", "a real reason")),
            "not-a-git-repository": (lambda: (self.tmp / "plain").mkdir(),
                                     lambda: ("status", "--repo", str(self.tmp / "plain"))),
            "missing-path": (lambda: None, lambda: ("status", "--repo", str(self.tmp / "missing"))),
        }

    def test_refusals_match_the_pre_refactor_engine(self) -> None:
        recorded: Dict[str, Dict[str, object]] = {}
        for name, (prepare, argv) in self.scenarios().items():
            with self.subTest(scenario=name):
                self.tearDown()
                self.setUp()
                prepare()
                code, out, err = self.refuse(*(argv() if callable(argv) else argv))
                recorded[name] = {"exit_code": code, "stdout": normalize(out, self.tmp),
                                  "stderr": normalize(err, self.tmp), "records_identical": True}
                self.assertNotEqual(code, 0, f"{name} was not refused")
        if os.environ.get(UPDATE_ENV) == "1" and not REFUSALS_FILE.exists():
            REFUSALS_FILE.write_text(json.dumps(recorded, indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
                                     newline="\n")
        expected = json.loads(REFUSALS_FILE.read_text(encoding="utf-8"))
        self.assertEqual(sorted(expected), sorted(recorded))
        for name in expected:
            with self.subTest(scenario=name):
                self.assertEqual(expected[name], recorded[name])


class LateRefusalTest(GoldenTestCase):
    """`run` prints the command's output before a refusal that comes after the command ran (audit F-1).

    The scenario also writes the check id into verification.md before the refusal (pre-existing, TD-25), so record
    integrity is not asserted here; only the output is pinned.
    """

    def test_run_output_is_printed_before_a_late_refusal(self) -> None:
        self.to_implementation()
        name = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            # --repo before the positionals: Python 3.9's argparse would treat it as part of the extra command.
            code = workflow.main(["run", "--repo", str(self.repo), "favorites", name, "--", PY, "-c",
                                  "print('line-one'); print('line-two')"])
        self.assertNotEqual(code, 0)
        self.assertIn("line-one", out.getvalue())
        text = f"exit: {code}\n--- stdout ---\n{out.getvalue()}--- stderr ---\n{err.getvalue()}"
        path = GOLDEN / "run-output-before-late-refusal.txt"
        actual = normalize(text, self.tmp)
        if os.environ.get(UPDATE_ENV) == "1" and not path.exists():
            path.write_text(actual, encoding="utf-8", newline="\n")
        self.assertEqual(path.read_text(encoding="utf-8").replace("\r\n", "\n"), actual)


class PreflightJsonTest(GoldenTestCase):
    """`preflight --json` prints text after the JSON object in two cases (TD-24). Pinned, not fixed, in F1.0.4."""

    def pinned(self, name: str, text: str) -> None:
        path = GOLDEN / name
        actual = normalize(text, self.tmp)
        if os.environ.get(UPDATE_ENV) == "1" and not path.exists():
            path.write_text(actual, encoding="utf-8", newline="\n")
        self.assertEqual(path.read_text(encoding="utf-8").replace("\r\n", "\n"), actual)

    def test_json_followed_by_unattributed_changes(self) -> None:
        self.to_implementation()
        self.wf("preflight", "favorites")
        self.write("app.py", "FAVORITES = set()\nprint('hello')\n")
        text = self.wf("preflight", "favorites", "--json")
        self.assertIn("Changes since the last checkpoint", text)
        self.pinned("preflight-json-unattributed.txt", text)

    def test_json_followed_by_the_analyzer_baseline_hint(self) -> None:
        self.write("analyzer.py", "print('No issues found!')\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "analyzer fixture")
        self.init(checks=[{"id": "analyze", "command": f'"{PY}" analyzer.py', "parser": "dart-analyzer",
                           "required": True}])
        self.new_task()
        self.to_specification()
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC)
        self.review_spec()
        self.wf("stage", "favorites", "SPEC_APPROVAL")
        self.wf("approve", "favorites", "spec", "--evidence", "Approve spec v1")
        self.write(".ai-dev-workflow/tasks/favorites/plan.md", FILLED_PLAN)
        self.wf("stage", "favorites", "PLAN_APPROVAL")
        self.wf("approve", "favorites", "plan", "--evidence", "Plan approved, go ahead")
        text = self.wf("preflight", "favorites", "--json")
        self.assertIn("Capture the analyzer baseline", text)
        self.pinned("preflight-json-analyzer-hint.txt", text)

