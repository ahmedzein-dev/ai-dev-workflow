"""The engine API (aidw.api, F1.0.4): separation from the CLI, no hidden state, JSON parity and an API-only lifecycle."""
from __future__ import annotations

import ast
import contextlib
import io
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterator
from unittest import mock

from helpers import (EXAMPLE_TEMPLATE, FILLED_AUDIT, FILLED_PLAN, FILLED_REPORT, FILLED_SPEC, MATRIX_ROWS, PY, SKILL,
                     WorkflowTestCase, git)

from aidw import api

import workflow

PKG = SKILL / "scripts" / "aidw"
# Functions that write records; the CLI may reach them only through aidw.api (spec FR-2, AC-3).
WRITERS = {"save_state", "save_json", "write_text", "activate", "clear_active", "add_history", "add_checkpoint",
           "make_readonly", "apply_commit_mode", "apply_commit_mode_in_clone", "regenerate_check_block",
           "install_template"}
LOWER = ["api.py", "constants.py", "errors.py", "core", "adapters", "store", "records", "infra"]
# Functions defined in aidw/api.py itself (not names it imports from lower layers).
API_FUNCTIONS = {node.name for node in ast.parse((PKG / "api.py").read_text(encoding="utf-8")).body
                 if isinstance(node, ast.FunctionDef)}


def modules(*parts: str) -> Iterator[Path]:
    for part in parts:
        path = PKG / part
        yield from (sorted(path.rglob("*.py")) if path.is_dir() else [path])


def called_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        return f"{func.value.id}.{func.attr}"
    return func.attr if isinstance(func, ast.Attribute) else ""


@contextlib.contextmanager
def no_output(test: Any) -> Iterator[None]:
    """Fail if anything reaches stdout or stderr, at Python level or at file-descriptor level (child processes)."""
    out, err = io.StringIO(), io.StringIO()
    with tempfile.TemporaryFile() as fd_out, tempfile.TemporaryFile() as fd_err:
        saved = [os.dup(1), os.dup(2)]
        os.dup2(fd_out.fileno(), 1)
        os.dup2(fd_err.fileno(), 2)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                yield
        finally:
            os.dup2(saved[0], 1)
            os.dup2(saved[1], 2)
            for fd in saved:
                os.close(fd)
        fd_out.seek(0)
        fd_err.seek(0)
        leaked = (out.getvalue(), err.getvalue(), fd_out.read().decode(errors="replace"), fd_err.read().decode(errors="replace"))
    test.assertEqual(leaked, ("", "", "", ""), "the engine API printed something")


def make_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    git(path, "init", "-q")
    git(path, "config", "user.email", "test@example.com")
    git(path, "config", "user.name", "Test")
    git(path, "config", "commit.gpgsign", "false")
    (path / "app.py").write_text("print('hello')\n", encoding="utf-8")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "init")
    return path


class SeparationTest(WorkflowTestCase):
    def test_cli_modules_write_no_records(self) -> None:
        for path in modules("cli"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imported = {alias.name for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
                        for alias in node.names}
            calls = {called_name(node) for node in ast.walk(tree) if isinstance(node, ast.Call)}
            attrs = {c.rsplit(".", 1)[-1] for c in calls}
            api_calls = {c.split(".", 1)[1] for c in calls if c.startswith("api.")}
            with self.subTest(module=path.name):
                self.assertFalse(imported & WRITERS, f"imports record writers: {imported & WRITERS}")
                self.assertFalse(attrs & WRITERS, f"calls record writers: {attrs & WRITERS}")
                self.assertFalse(api_calls - API_FUNCTIONS, f"calls names that aidw.api only imports: {api_calls - API_FUNCTIONS}")
                aliases = [a for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names
                           if a.asname and (a.name in ("api", "aidw.api") or a.name.startswith("aidw.api"))]
                self.assertFalse(aliases, "aidw.api imported under another name")
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and called_name(node).rsplit(".", 1)[-1] == "open":
                        first = 0 if isinstance(node.func, ast.Attribute) else 1  # path.open(mode) vs open(path, mode)
                        modes = [a.value for a in node.args[first:first + 1] if isinstance(a, ast.Constant)]
                        modes += [k.value.value for k in node.keywords if k.arg == "mode" and isinstance(k.value, ast.Constant)]
                        self.assertFalse(any(set(str(m)) & set("wax+") for m in modes), "opens a file for writing")
                    if isinstance(node, ast.Attribute) and node.attr in ("write_text", "write_bytes"):
                        self.fail("writes a file directly")

    def test_lower_layers_never_print_exit_change_directory_or_read_argv(self) -> None:
        for path in modules(*LOWER):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            calls = {called_name(node) for node in ast.walk(tree) if isinstance(node, ast.Call)}
            argv = [n for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr == "argv"]
            with self.subTest(module=str(path.relative_to(PKG))):
                self.assertFalse(calls & {"print", "sys.exit", "exit", "os.chdir"}, calls & {"print", "sys.exit", "exit", "os.chdir"})
                self.assertFalse(argv, "reads sys.argv")
        tree = ast.parse((PKG / "api.py").read_text(encoding="utf-8"))
        docstrings = {id(node.body[0].value) for node in ast.walk(tree)
                      if isinstance(node, (ast.Module, ast.FunctionDef)) and node.body
                      and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)}
        strings = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
                   and id(n) not in docstrings}
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | \
            {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        self.assertFalse({s for s in strings if "AI_DEV_WORKFLOW_AGENT" in s}, "the API reads the agent from the environment")
        self.assertFalse(names & {"agent_name", "getcwd", "cwd", "environ", "getenv"}, names & {"agent_name", "getcwd", "cwd", "environ", "getenv"})

    def test_hooks_import_nothing_from_the_cli(self) -> None:
        tree = ast.parse((PKG / "agents" / "claude_hooks.py").read_text(encoding="utf-8"))
        targets = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        self.assertFalse({t for t in targets if t.startswith("aidw.cli")})

    def test_api_functions_are_not_reexported_from_workflow(self) -> None:
        self.assertFalse(hasattr(workflow, "api"))
        for name in ("discover_setup", "init_project", "new_task", "record_discovery", "run_check", "check_records"):
            self.assertFalse(hasattr(workflow, name), name)


class NoHiddenStateTest(WorkflowTestCase):
    def config_file(self) -> str:
        config = self.tmp / "config.json"
        config.write_text(json.dumps({"checks": [
            {"id": "unit", "name": "unit check", "command": f'"{PY}" -c "print(1)"', "required": True}]}), encoding="utf-8")
        return str(config)

    def test_alternating_repositories_in_one_process(self) -> None:
        repo_a, repo_b = make_repo(self.tmp / "a"), make_repo(self.tmp / "b")
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        before = os.getcwd()
        os.chdir(elsewhere)
        # Restore the working directory here, before tearDown removes the temporary folder: Windows cannot delete
        # the current directory (the first CI run failed with WinError 32 when this used addCleanup).
        try:
            with mock.patch.dict(os.environ, {"AI_DEV_WORKFLOW_AGENT": "env-agent"}), no_output(self):
                for repo in (repo_a, repo_b):
                    api.init_project(repo=repo, template=str(EXAMPLE_TEMPLATE), commit="all", agent="api-agent",
                                     config=self.config_file())
                api.new_task(repo=repo_a, task="alpha", title="Alpha", task_type="feature",
                             invocation="/ai-dev-workflow alpha", agent="api-agent")
                api.new_task(repo=repo_b, task="beta", title="Beta", task_type="bugfix",
                             invocation="/ai-dev-workflow beta", agent="api-agent")
                api.record_discovery(repo=repo_a, task="alpha", agent="api-agent", inspected=["app.py"], summary="A")
                api.record_discovery(repo=repo_b, task="beta", agent="api-agent", summary="B")
                status_a, status_b = api.status(repo=repo_a), api.status(repo=repo_b)
                self.assertEqual(Path(os.getcwd()).resolve(), elsewhere.resolve())
            self.assertEqual([t["task"] for t in status_a["tasks"]], ["alpha"])
            self.assertEqual([t["task"] for t in status_b["tasks"]], ["beta"])
            self.assertEqual((status_a["active"], status_b["active"]), ("alpha", "beta"))
            state_a = json.loads((repo_a / ".ai-dev-workflow/tasks/alpha/state.json").read_text(encoding="utf-8"))
            state_b = json.loads((repo_b / ".ai-dev-workflow/tasks/beta/state.json").read_text(encoding="utf-8"))
            self.assertEqual((state_a["discovery"]["summary"], state_b["discovery"]["summary"]), ("A", "B"))
            self.assertEqual((state_a["created_by"], state_b["created_by"]), ("api-agent", "api-agent"))
            self.assertEqual(state_b["type"], "bugfix")
            self.assertFalse((repo_a / ".ai-dev-workflow/tasks/beta").exists())
            self.assertFalse((repo_b / ".ai-dev-workflow/tasks/alpha").exists())
            self.assertFalse((elsewhere / ".ai-dev-workflow").exists())
            self.assertEqual(Path(os.getcwd()).resolve(), elsewhere.resolve())
        finally:
            os.chdir(before)

    def test_a_repository_path_of_spaces_is_reported_as_before(self) -> None:
        try:
            workflow.find_repo(" ")
        except workflow.WorkflowError as exc:
            expected_code, expected_message = exc.code, f"AIDevWorkflow: {exc}\n"
        else:
            self.skipTest("on this platform a path of spaces resolves to an existing repository")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = workflow.main(["status", "--repo", " "])
        self.assertEqual((code, out.getvalue(), err.getvalue()), (expected_code, "", expected_message))

    def test_an_empty_repository_path_is_refused(self) -> None:
        for call in (lambda: api.status(repo=""), lambda: api.discover_setup(repo="  "),
                     lambda: api.apply_clone_commit_mode(repo="", cfg={})):
            with self.assertRaises(workflow.WorkflowError) as caught:
                call()
            self.assertIn("explicit repository path", str(caught.exception))


class JsonParityTest(WorkflowTestCase):
    def cli_json(self, *argv: str, expect: int = 0) -> Any:
        text = self.wf(*argv, expect=expect)
        value, end = json.JSONDecoder().raw_decode(text)
        return value, text[end:]

    def assert_raw_parity(self, repo: str) -> None:
        """Byte-level parity (key order and formatting included) for the read-only --json commands."""
        cases = (
            (("init", "--discover", "--json"), lambda: json.dumps(api.discover_setup(repo=repo), indent=2), 0),
            (("status", "--json"), lambda: json.dumps(api.status(repo=repo), indent=2), 0),
            (("status", "favorites", "--json"),
             lambda: json.dumps(api.status(repo=repo, task="favorites"), indent=2, ensure_ascii=False), 0),
            (("spec-check", "favorites", "--json"),
             lambda: json.dumps(api.spec_check(repo=repo, task="favorites"), indent=2, ensure_ascii=False), 0),
            (("plan-check", "favorites", "--json"),
             lambda: json.dumps(api.plan_check(repo=repo, task="favorites"), indent=2, ensure_ascii=False), 0),
            (("scope", "favorites", "--json"),
             lambda: json.dumps(api.scope(repo=repo, task="favorites", agent="test-agent"), indent=2), 0),
            (("outcome", "favorites", "--json"),
             lambda: json.dumps(api.outcome(repo=repo, task="favorites"), indent=2, ensure_ascii=False), 0),
            (("check", "--json"), lambda: json.dumps(api.check_records(repo=repo), indent=2), 0),
        )
        for argv, render, code in cases:
            with self.subTest(raw=argv[0]):
                self.assertEqual(self.wf(*argv, expect=code), render() + "\n")

    def test_check_json_with_errors_matches_the_api(self) -> None:
        self.to_implementation()
        (self.task / "audit.md").unlink()
        text = self.wf("check", "--json", expect=1)
        result = api.check_records(repo=str(self.repo))
        self.assertFalse(result["ok"])
        self.assertIn("favorites: audit.md is missing.", result["errors"])
        self.assertEqual(text, json.dumps(result, indent=2) + "\n")

    def test_cli_json_equals_the_api_result(self) -> None:
        repo = str(self.repo)
        self.assertEqual(self.cli_json("init", "--discover", "--json")[0], api.discover_setup(repo=repo))
        self.assertEqual(self.cli_json("status", "--json")[0], api.status(repo=repo))
        self.to_implementation()
        self.wf("preflight", "favorites")
        for argv, call in (
                (("status", "--json"), lambda: api.status(repo=repo)),
                (("status", "favorites", "--json"), lambda: api.status(repo=repo, task="favorites")),
                (("spec-check", "favorites", "--json"), lambda: api.spec_check(repo=repo, task="favorites")),
                (("plan-check", "favorites", "--json"), lambda: api.plan_check(repo=repo, task="favorites")),
                (("scope", "favorites", "--json"), lambda: api.scope(repo=repo, task="favorites", agent="test-agent")),
                (("check", "--json"), lambda: api.check_records(repo=repo)),
                (("outcome", "favorites", "--json"), lambda: api.outcome(repo=repo, task="favorites"))):
            with self.subTest(command=argv[0]):
                printed, rest = self.cli_json(*argv)
                self.assertEqual(rest.strip(), "")
                self.assertEqual(printed, call())
        self.assert_raw_parity(repo)
        scope = api.scope(repo=repo, task="favorites", agent="test-agent")
        self.assertEqual(sorted(scope), sorted(["baseline", "task_changes", "unattributed", "preexisting_modified",
                                                "preexisting_untouched", "excluded", "notes"]))
        printed, rest = self.cli_json("preflight", "favorites", "--json")
        result = api.preflight(repo=repo, task="favorites", agent="test-agent")
        self.assertEqual(printed, {k: result[k] for k in ("valid", "problems", "unattributed")})
        self.assertEqual((rest.strip(), result["task"], result["stage"]), ("", "favorites", "IMPLEMENTATION"))


class ApiLifecycleTest(WorkflowTestCase):
    """The same task driven through the CLI (self.repo) and through the API only (a second repository)."""

    # Only times, code fingerprints, git baselines (commit ids differ between the two repositories) and durations;
    # checkpoints themselves (session, changes, unattributed, validity) are compared.
    VOLATILE = {"at", "created_at", "updated_at", "closed_at", "recorded_at", "confirmed_at", "fingerprint", "baseline",
                "duration_s", "preflight_at"}

    def normalized(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {k: self.normalized(v) for k, v in value.items() if k not in self.VOLATILE}
        if isinstance(value, list):
            return [self.normalized(v) for v in value]
        return value

    def drive_api(self, repo: Path) -> Dict[str, Any]:
        r, a, task = str(repo), "test-agent", "favorites"
        tdir = repo / ".ai-dev-workflow" / "tasks" / task
        config = self.tmp / "api-config.json"
        config.write_text(json.dumps({"checks": [
            {"id": "unit", "name": "unit check", "command": f'"{PY}" -c "print(1)"', "required": True}]}), encoding="utf-8")
        results: Dict[str, Any] = {}
        with no_output(self):
            results["init"] = api.init_project(repo=r, template=str(EXAMPLE_TEMPLATE), commit="all", agent=a,
                                               config=str(config))
            results["new"] = api.new_task(repo=r, task=task, title="Saved favorites", task_type="feature",
                                          invocation="/ai-dev-workflow add saved favorites", agent=a)
            api.record_discovery(repo=r, task=task, agent=a, inspected=["app.py"],
                                 summary="Add favorites to app.py; no sharing.")
            api.stage(repo=r, task=task, stage="DEPENDENCIES", agent=a)
            (tdir / "dependencies.md").write_text(
                "# Dependencies: Saved favorites\n\nNo dependencies identified — the change is local to app.py.\n",
                encoding="utf-8")
            api.stage(repo=r, task=task, stage="SPECIFICATION", agent=a)
            (tdir / "spec.md").write_text(FILLED_SPEC, encoding="utf-8")
            results["review"] = api.review(repo=r, task=task, agent=a,
                                           maps=["REQ-1=AC-1", "REQ-2=test:favorites list test"],
                                           passes=["J1", "J2", "J3", "J4"],
                                           notes=["J3=No new structures; extends the existing app.py module."])
            api.stage(repo=r, task=task, stage="SPEC_APPROVAL", agent=a)
            results["approve_spec"] = api.approve(repo=r, task=task, document="spec", evidence="Approve spec v1", agent=a)
            (tdir / "plan.md").write_text(FILLED_PLAN, encoding="utf-8")
            api.stage(repo=r, task=task, stage="PLAN_APPROVAL", agent=a)
            results["approve_plan"] = api.approve(repo=r, task=task, document="plan", evidence="Plan approved, go ahead",
                                                  agent=a)
            results["preflight"] = api.preflight(repo=r, task=task, agent=a)
            (repo / "app.py").write_text("FAVORITES = set()\nprint('hello')\n", encoding="utf-8")
            results["step"] = api.step(repo=r, task=task, step="S1", status="done", agent=a)
            api.stage(repo=r, task=task, stage="TESTING", agent=a)
            results["run"] = api.run_check(repo=r, task=task, check="unit", agent=a)
            text = (tdir / "verification.md").read_text(encoding="utf-8")
            (tdir / "verification.md").write_text(
                text.replace("|------|--------|----------|\n", "|------|--------|----------|\n" + MATRIX_ROWS),
                encoding="utf-8")
            api.stage(repo=r, task=task, stage="AUDIT", agent=a)
            (tdir / "audit.md").write_text(FILLED_AUDIT.format(findings="No findings."), encoding="utf-8")
            api.stage(repo=r, task=task, stage="FINAL_REPORT", agent=a)
            results["outcome"] = api.outcome(repo=r, task=task)
            (tdir / "report.md").write_text(FILLED_REPORT.format(status="Completed"), encoding="utf-8")
            results["close"] = api.close(repo=r, task=task, agent=a)
            results["check"] = api.check_records(repo=r)
        return results

    def test_api_only_lifecycle_matches_the_cli(self) -> None:
        self.to_implementation()
        self.implement_and_test()
        self.wf("stage", "favorites", "AUDIT")
        self.write(".ai-dev-workflow/tasks/favorites/audit.md", FILLED_AUDIT.format(findings="No findings."))
        self.wf("stage", "favorites", "FINAL_REPORT")
        self.write(".ai-dev-workflow/tasks/favorites/report.md", FILLED_REPORT.format(status="Completed"))
        self.wf("close", "favorites")

        other = make_repo(self.tmp / "api" / "repo")  # same folder name: the project name comes from it
        results = self.drive_api(other)
        self.assertEqual(results["init"]["checks"], ["unit"])
        self.assertEqual((results["new"]["task"], results["new"]["paused"], results["new"]["commit_mode_message"]),
                         ("favorites", None, None))
        self.assertTrue(results["review"]["spec_check"]["ready"])
        self.assertEqual((results["approve_spec"]["version"], results["approve_spec"]["stage"]), (1, "PLANNING"))
        self.assertEqual(results["approve_plan"]["stage"], "IMPLEMENTATION")
        self.assertTrue(results["preflight"]["valid"])
        self.assertEqual((results["step"]["done"], results["step"]["total"], results["step"]["files"]), (1, 1, ["app.py"]))
        self.assertEqual((results["run"]["entry"]["status"], results["run"]["output_tail"]), ("passed", ["1"]))
        self.assertEqual(results["outcome"]["max"], "Completed")
        self.assertEqual(results["close"], {"task": "favorites", "outcome": "Completed"})
        self.assertTrue(results["check"]["ok"])

        rel = Path(".ai-dev-workflow") / "tasks" / "favorites"
        cli_state = json.loads((self.repo / rel / "state.json").read_text(encoding="utf-8"))
        api_state = json.loads((other / rel / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(self.normalized(api_state), self.normalized(cli_state))
        for name in ("spec.md", "plan.md", "dependencies.md", "audit.md", "report.md", "approved/spec.v1.md",
                     "approved/plan.v1.md"):
            with self.subTest(record=name):
                self.assertEqual((other / rel / name).read_bytes(), (self.repo / rel / name).read_bytes())
        configs = [json.loads((root / ".ai-dev-workflow" / "config.json").read_text(encoding="utf-8"))
                   for root in (self.repo, other)]
        self.assertEqual(self.normalized(configs[1]), self.normalized(configs[0]))
        self.assertEqual([(root / ".ai-dev-workflow" / "ACTIVE").exists() for root in (self.repo, other)], [False, False])


class CommitModeNoticeTest(WorkflowTestCase):
    """EC-10: the records commit mode is applied in a fresh clone by `new`, and its notice is printed first."""

    def forget_exclude(self) -> None:
        exclude = self.repo / ".git" / "info" / "exclude"
        exclude.write_text("", encoding="utf-8")

    def test_notice_before_created_task(self) -> None:
        self.init(commit="config-only")
        self.forget_exclude()
        text = self.wf("new", "favorites", "--title", "Saved favorites", "--invocation", "/ai-dev-workflow favorites")
        lines = text.splitlines()
        self.assertEqual(lines[0], "Applied records.commit=config-only in this clone (local git exclude only).")
        self.assertTrue(lines[1].startswith("Created task 'favorites'"))

    def test_notice_kept_when_a_later_check_refuses(self) -> None:
        self.init(commit="config-only")
        self.forget_exclude()
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = workflow.main(["new", "Bad_Name", "--repo", str(self.repo), "--title", "T",
                                  "--invocation", "/ai-dev-workflow x"])
        self.assertEqual(code, 1)
        self.assertEqual(out.getvalue(), "Applied records.commit=config-only in this clone (local git exclude only).\n")
        self.assertIn("Task names use lowercase letters", err.getvalue())
