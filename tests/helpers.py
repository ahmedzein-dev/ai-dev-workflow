"""Shared fixtures for the AIDevWorkflow tests: a throwaway git repository and a CLI runner."""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "ai-dev-workflow"
EXAMPLE_TEMPLATE = ROOT / "examples" / "templates" / "example-spec-template.md"
sys.path.insert(0, str(SKILL / "scripts"))

import workflow  # noqa: E402

PY = sys.executable

FILLED_SPEC = """# Feature Specification: Saved favorites

## Summary

**Problem:** Returning users cannot find items they liked without searching again.
**Outcome:** A signed-in user can save an item to favorites and see the list later.

## Requirements

- **REQ-1:** A heart button on each item toggles whether the item is saved.
- **REQ-2:** The favorites screen lists saved items, newest first.

**Not included:**
- Sharing favorites with other users

## Edge Cases

| ID | Situation | Expected behavior |
|----|-----------|-------------------|
| EC-1 | The network drops while saving | The heart reverts and "No connection" appears with Retry. |

## Constraints

- **Must not change:** The item card layout, apart from the heart slot.
- **Structures:** None — the change stays inside the existing app.py module.
- **New dependencies:** None

## Acceptance Criteria

- **AC-1:** Given a signed-in user, when they tap an empty heart, then the item appears first in favorites.

**Definition of done:**
- [ ] Every requirement and edge case behaves as specified
- [ ] The unit test for favorites passes
"""

FILLED_PLAN = """# Implementation Plan: Saved favorites

> Spec: v1 approved

## 1. Goal

Let signed-in users save items and list them.

## 2. Current Behavior

Items render from `app.py` with no saved state.

## 3. Proposed Solution

Add a favorites set in `app.py`, following the existing module structure.

## 4. Affected Areas

`app.py` only.

## 5. Implementation Steps

- **S1:** Add the favorites toggle and list (REQ-1, REQ-2, EC-1).

## 6. Important Technical Decisions

None — single-module change.

## 7. Edge Cases

EC-1: revert the toggle when saving fails.

## 8. Testing Plan

The unit check covers AC-1 and EC-1.

## 9. Risks and Dependencies

None — no shared code is touched.

## 10. Expected Result

Users can save and list favorites.
"""

MATRIX_ROWS = """| AC-1 | Passed | unit check `unit` |
| EC-1 | Passed | unit check `unit` |
| DW-1 | Passed | inspection of app.py |
| DW-2 | Passed | check `unit` passed |
"""

FILLED_AUDIT = """# Audit: Saved favorites

**Review independence:** second pass
**Reviewer:** test-agent
**Reviewed scope:** app.py and the recorded checks

## Dimensions

- **A. Specification compliance:** Meets REQ-1, REQ-2, EC-1 and AC-1.
- **B. Architecture compliance:** Stays inside the existing module.
- **C. Code quality:** Small and readable.
- **D. Security and privacy:** No sensitive data involved.
- **E. Edge cases:** EC-1 handled by reverting.
- **F. Regression risk:** Low; one module.
- **G. Test adequacy:** Unit check covers the behavior.
- **H. Scope compliance:** Matches the approved plan.
- **I. Reliability and performance:** No async work.

## Project standards checklist

No project checklist items apply.

## Findings

{findings}

## Remediation log

Nothing to fix.
"""

FILLED_REPORT = """# Final Report: Saved favorites

## 1. Overall Status

**Status:** {status}

All acceptance criteria passed with recorded evidence.

## 2. What Was Implemented

Favorites toggle and list in app.py.

## 3. Specification Compliance

Matches the approved spec.

## 4. Testing Results

Check `unit` passed on the current code.

## 5. Code Audit

No issues were identified within the reviewed scope.

## 6. Edge Cases and Regression Risks

EC-1 covered; low regression risk.

## 7. Pending Dependencies

None — nothing is pending.

## 8. Next Actions

None.
"""


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=str(repo), check=True, capture_output=True, text=True).stdout


def _force_remove(func, path, _exc):
    os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
    func(path)


class WorkflowTestCase(unittest.TestCase):
    """Each test gets a fresh git repository and an isolated AIDevWorkflow home."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aidw-test-"))
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")
        (self.repo / "app.py").write_text("print('hello')\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "init")
        self.home = self.tmp / "home"
        self.home.mkdir()
        self._env = mock.patch.dict(os.environ, {
            "AI_DEV_WORKFLOW_HOME": str(self.home / ".ai-dev-workflow"),
            "AI_DEV_WORKFLOW_AGENT": "test-agent",
        })
        self._env.start()

    def tearDown(self) -> None:
        self._env.stop()
        if sys.version_info >= (3, 12):
            shutil.rmtree(self.tmp, onexc=_force_remove)
        else:
            shutil.rmtree(self.tmp, onerror=_force_remove)

    # -- runners ------------------------------------------------------------------
    def wf(self, command: str, *args: str, expect: int | None = 0) -> str:
        out, err = io.StringIO(), io.StringIO()
        argv = [command, "--repo", str(self.repo), *args]
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = workflow.main(argv)
        text = out.getvalue() + err.getvalue()
        if expect is not None:
            self.assertEqual(code, expect, f"workflow.py {' '.join(argv)} exited {code}:\n{text}")
        return text

    def hook(self, name: str, payload: dict | None = None, raw: str | None = None) -> str:
        out = io.StringIO()
        stdin = io.StringIO(raw if raw is not None else json.dumps(payload or {}))
        with contextlib.redirect_stdout(out), mock.patch("sys.stdin", stdin):
            code = workflow.main(["hook", name])
        self.assertEqual(code, 0)
        return out.getvalue()

    def edit_payload(self, path: Path, session: str = "S1") -> dict:
        return {"session_id": session, "cwd": str(self.repo), "hook_event_name": "PreToolUse",
                "tool_name": "Edit", "tool_input": {"file_path": str(path)}}

    # -- fixtures -----------------------------------------------------------------
    @property
    def task(self) -> Path:
        return self.repo / ".ai-dev-workflow" / "tasks" / "favorites"

    def write(self, rel: str, text: str) -> None:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def state(self) -> dict:
        return json.loads((self.task / "state.json").read_text(encoding="utf-8"))

    def init(self, checks: list | None = None, commit: str = "all") -> None:
        config = self.tmp / "config.json"
        config.write_text(json.dumps({"checks": checks if checks is not None else [
            {"id": "unit", "name": "unit check", "command": f'"{PY}" -c "print(1)"', "required": True}]}),
            encoding="utf-8")
        self.wf("init", "--template", str(EXAMPLE_TEMPLATE), "--commit", commit, "--config", str(config))

    def new_task(self, *extra: str) -> None:
        self.wf("new", "favorites", "--title", "Saved favorites", "--invocation", "/ai-dev-workflow add saved favorites",
                *extra)

    def to_specification(self) -> None:
        self.wf("discover", "favorites", "--inspected", "app.py", "--summary", "Add favorites to app.py; no sharing.")
        self.wf("stage", "favorites", "DEPENDENCIES")
        self.write(".ai-dev-workflow/tasks/favorites/dependencies.md",
                   "# Dependencies: Saved favorites\n\nNo dependencies identified — the change is local to app.py.\n")
        self.wf("stage", "favorites", "SPECIFICATION")

    def review_spec(self) -> None:
        self.wf("review", "favorites", "--map", "REQ-1=AC-1", "--map", "REQ-2=test:favorites list test",
                "--pass", "J1", "--pass", "J2", "--pass", "J3", "--pass", "J4",
                "--note", "J3=No new structures; extends the existing app.py module.")

    def to_implementation(self) -> None:
        self.init()
        self.new_task()
        self.to_specification()
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC)
        self.review_spec()
        self.wf("stage", "favorites", "SPEC_APPROVAL")
        self.wf("approve", "favorites", "spec", "--evidence", "Approve spec v1")
        self.write(".ai-dev-workflow/tasks/favorites/plan.md", FILLED_PLAN)
        self.wf("stage", "favorites", "PLAN_APPROVAL")
        self.wf("approve", "favorites", "plan", "--evidence", "Plan approved, go ahead")

    def implement_and_test(self) -> None:
        self.wf("preflight", "favorites")
        self.write("app.py", "FAVORITES = set()\nprint('hello')\n")
        self.wf("step", "favorites", "S1", "done")
        self.wf("stage", "favorites", "TESTING")
        self.wf("run", "favorites", "unit")
        text = (self.task / "verification.md").read_text(encoding="utf-8")
        text = text.replace("|------|--------|----------|\n", "|------|--------|----------|\n" + MATRIX_ROWS)
        self.write(".ai-dev-workflow/tasks/favorites/verification.md", text)
