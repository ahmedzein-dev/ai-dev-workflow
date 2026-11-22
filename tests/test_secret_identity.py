"""TD-25: secret-like agent names, session ids and check names are refused before anything runs or is written.

Every value that looks like a credential is synthetic and built at run time, so this file holds no literal token
(the repository's privacy scan must stay clean). The tests check the persisted files and the printed output, not
only exit codes:

- the refusal names the field and never contains the value (stdout and stderr);
- every file under .ai-dev-workflow/ and .git/info/exclude keeps its bytes;
- no file in the repository (outside .git/objects) contains the value;
- an extra command given to `run` was not executed.

Write failures are simulated to show what the write order and the task-creation clean-up guarantee, and what they
do not (TD-29): there is no multi-file transaction.
"""
from __future__ import annotations

import contextlib
import importlib
import io
import json
import tempfile
import os
import subprocess
import unittest
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from unittest import mock

from helpers import EXAMPLE_TEMPLATE, PY, SKILL, WorkflowTestCase, git

import workflow

try:
    api = importlib.import_module("aidw.api")
except ImportError:  # engines before F1.0.4 (used to show that the tests fail on the vulnerable engine)
    api = None

needs_api = unittest.skipIf(api is None, "this engine has no aidw.api (before F1.0.4)")


def token(kind: str = "github") -> str:
    """A synthetic value the secret scanner flags. Built here so that no literal token is stored in the file."""
    if kind == "github":
        return "ghp_" + "A" * 36
    return "sk-ant-" + "b" * 24


TOKENS = (token("github"), token("anthropic"))


def workflow_session_problem(value: str):  # the shared session rule (aidw.api), or the single-file engine's copy
    return getattr(api, "session_problem", None)(value) if api is not None and hasattr(api, "session_problem") \
        else workflow.session_problem(value)
SESSION_FORMAT = "The session id must be 1–256 printable characters without spaces."
# A value split by a line separator is not flagged line by line, but the JSON form that state.json is scanned in is
# (audit F-1): "password=" + separator + 12 characters.
MULTI_LINE = {name: "password=" + sep + "q7" * 6 for name, sep in
              (("LF", "\n"), ("CR", "\r"), ("VT", "\x0b"), ("FF", "\x0c"), ("FS", "\x1c"))}
MALFORMED_SESSIONS = {
    "line break": "abc\ndef",
    "tab": "abc\tdef",
    "space": "abc def",
    "zero-width space": "abc​def",
    "257 characters": "s" * 257,
}


def snapshot(root: Path) -> Dict[str, bytes]:
    """Bytes of every file under .ai-dev-workflow/ and of .git/info/exclude."""
    files: Dict[str, bytes] = {}
    records = root / ".ai-dev-workflow"
    if records.exists():
        for path in sorted(records.rglob("*")):
            if path.is_file():
                files[path.relative_to(root).as_posix()] = path.read_bytes()
    exclude = root / ".git" / "info" / "exclude"
    if exclude.exists():
        files[".git/info/exclude"] = exclude.read_bytes()
    return files


class SecretIdentityCase(WorkflowTestCase):
    def setUp(self) -> None:
        super().setUp()
        # A script file, not `python -c "…"`: quoted extra commands are not portable to Windows.
        self.write("make_marker.py", "from pathlib import Path\nPath('ran.marker').write_text('ran')\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "fixture")

    @property
    def marker(self) -> Path:
        return self.repo / "ran.marker"

    def cli(self, *args: str) -> Tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = workflow.main([args[0], "--repo", str(self.repo), *args[1:]])
        return code, out.getvalue(), err.getvalue()

    def assert_not_persisted(self, value: str) -> None:
        needles = {value.encode("utf-8"), json.dumps(value)[1:-1].encode("utf-8"),
                   json.dumps(value, ensure_ascii=False)[1:-1].encode("utf-8")}  # raw and JSON-escaped forms
        for path in self.repo.rglob("*"):
            rel = path.relative_to(self.repo).as_posix()
            if path.is_file() and not rel.startswith(".git/objects/"):
                data = path.read_bytes()
                for needle in needles:
                    self.assertNotIn(needle, data, f"{rel} contains the refused value")

    def assert_refused(self, args: List[str], value: str, message: str, env: Optional[Dict[str, str]] = None) -> str:
        before = snapshot(self.repo)
        with mock.patch.dict(os.environ, env or {}):
            code, out, err = self.cli(*args)
        after = snapshot(self.repo)
        self.assertNotEqual(code, 0, f"{args[0]} was not refused:\n{out}{err}")
        self.assertIn(message, err)
        self.assertNotIn(value, out + err, "the refused value was printed")
        self.assertEqual(sorted(before), sorted(after), "files were added or removed although the command was refused")
        for rel, data in before.items():
            self.assertEqual(data, after[rel], f"{rel} changed although the command was refused")
        self.assert_not_persisted(value)
        self.assertFalse(self.marker.exists(), "the extra command ran although the command was refused")
        return err


class CliRefusalTest(SecretIdentityCase):
    """EC-1 to EC-7 and EC-11 through the CLI (AC-1, AC-2, AC-3)."""

    def test_run_with_a_secret_like_check_name_and_an_extra_command(self) -> None:  # EC-1, DEP-2
        self.to_implementation()
        self.wf("preflight", "favorites")
        for value in TOKENS:
            self.assert_refused(["run", "favorites", value, "--", PY, "make_marker.py"], value,
                                "Refusing to save the check name")

    def test_run_with_a_secret_like_unknown_check_name(self) -> None:  # EC-2
        self.to_implementation()
        value = token()
        err = self.assert_refused(["run", "favorites", value], value, "Refusing to save the check name")
        self.assertNotIn("Unknown check", err)

    def test_run_with_a_secret_like_agent_name(self) -> None:  # EC-3, DEP-2
        self.to_implementation()
        value = token()
        self.assert_refused(["run", "--agent", value, "favorites", "smoke", "--", PY, "make_marker.py"], value,
                            "Refusing to save the agent name")
        self.assert_refused(["run", "--agent", value, "favorites", "unit"], value, "Refusing to save the agent name")

    def test_agent_name_from_the_environment(self) -> None:  # EC-4, DEP-2
        self.to_implementation()
        value = token("anthropic")
        env = {"AI_DEV_WORKFLOW_AGENT": value}
        self.assert_refused(["run", "favorites", "smoke", "--", PY, "make_marker.py"], value,
                            "Refusing to save the agent name", env)
        self.assert_refused(["step", "favorites", "S1", "done"], value, "Refusing to save the agent name", env)

    def test_agent_name_from_the_environment_in_a_separate_process(self) -> None:  # EC-4
        self.to_implementation()
        value = token()
        before = snapshot(self.repo)
        env = dict(os.environ, AI_DEV_WORKFLOW_AGENT=value)
        proc = subprocess.run([PY, str(SKILL / "scripts" / "workflow.py"), "run", "--repo", str(self.repo), "favorites",
                               "smoke", "--", PY, "make_marker.py"], env=env, capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Refusing to save the agent name", proc.stderr)
        self.assertNotIn(value, proc.stdout + proc.stderr)
        self.assertEqual(before, snapshot(self.repo))
        self.assertFalse(self.marker.exists())
        self.assert_not_persisted(value)

    def test_resume_with_a_secret_like_agent_name(self) -> None:  # EC-5, DEP-2
        self.init()
        self.new_task()
        self.wf("pause", "favorites")
        value = token()
        self.assert_refused(["resume", "--agent", value, "favorites"], value, "Refusing to save the agent name")
        self.assertEqual(self.state()["status"], "paused")
        self.assertFalse((self.repo / ".ai-dev-workflow" / "ACTIVE").exists())

    def test_preflight_with_a_secret_like_agent_name(self) -> None:  # EC-5
        self.to_implementation()
        value = token()
        self.assert_refused(["preflight", "--agent", value, "favorites"], value, "Refusing to save the agent name")

    def test_new_with_a_secret_like_agent_name_while_another_task_is_active(self) -> None:  # EC-6, DEP-2, AC-3
        self.init()
        self.new_task()
        value = token()
        self.assert_refused(["new", "--agent", value, "second", "--title", "Second", "--invocation",
                             "/ai-dev-workflow second"], value, "Refusing to save the agent name")
        self.assertFalse((self.repo / ".ai-dev-workflow" / "tasks" / "second").exists())
        self.assertEqual(self.state()["status"], "active")
        self.wf("new", "second", "--title", "Second", "--invocation", "/ai-dev-workflow second")
        self.assertTrue((self.repo / ".ai-dev-workflow" / "tasks" / "second" / "state.json").exists())

    def test_new_without_setup_commit_mode_is_not_applied_before_the_refusal(self) -> None:  # EC-6
        self.init(commit="none")
        exclude = self.repo / ".git" / "info" / "exclude"
        exclude.write_text("", encoding="utf-8")  # a fresh clone: the commit mode is not applied yet
        value = token()
        self.assert_refused(["new", "--agent", value, "second", "--title", "Second", "--invocation",
                             "/ai-dev-workflow second"], value, "Refusing to save the agent name")

    def test_secret_like_session_ids(self) -> None:  # EC-7, DEP-2 (resume used to succeed)
        self.init()
        self.new_task()
        value = token()
        self.wf("pause", "favorites")
        self.assert_refused(["resume", "favorites", "--session", value], value, "Refusing to save the session id")
        self.wf("resume", "favorites")
        self.assert_refused(["new", "second", "--title", "Second", "--invocation", "/ai-dev-workflow second",
                             "--session", value], value, "Refusing to save the session id")

    def test_preflight_with_a_secret_like_session_id(self) -> None:  # EC-7
        self.to_implementation()
        value = token("anthropic")
        self.assert_refused(["preflight", "favorites", "--session", value], value, "Refusing to save the session id")

    def test_malformed_session_ids_are_refused_explicitly(self) -> None:  # EC-11
        self.init()
        self.new_task()
        self.wf("pause", "favorites")
        for label, value in MALFORMED_SESSIONS.items():
            with self.subTest(label):
                self.assert_refused(["resume", "favorites", "--session", value], value, SESSION_FORMAT)

    def test_multi_line_secret_like_values_are_refused_before_anything_runs(self) -> None:  # audit F-1
        self.to_implementation()
        self.wf("pause", "favorites")
        for label, value in MULTI_LINE.items():
            with self.subTest(label):
                self.assert_refused(["resume", "--agent", value, "favorites"], value, "Refusing to save the agent name")
        self.wf("resume", "favorites")
        for label, value in MULTI_LINE.items():
            with self.subTest(label):
                self.assert_refused(["preflight", "--agent", value, "favorites"], value, "Refusing to save the agent name")
                self.assert_refused(["run", "favorites", value, "--", PY, "make_marker.py"], value,
                                    "Refusing to save the check name")
                err = self.assert_refused(["run", "favorites", value], value, "Refusing to save the check name")
                self.assertNotIn("Unknown check", err)

    def test_every_recording_command_refuses_a_secret_like_agent(self) -> None:  # audit F-4 (CLI sweep)
        self.to_implementation()
        value = token()
        commands = {
            "discover": ["discover", "--agent", value, "favorites", "--summary", "Summary."],
            "review": ["review", "--agent", value, "favorites", "--pass", "J1"],
            "approve": ["approve", "--agent", value, "favorites", "spec", "--evidence", "Approved"],
            "stage": ["stage", "--agent", value, "favorites", "TESTING"],
            "step": ["step", "--agent", value, "favorites", "S1", "done"],
            "scope": ["scope", "--agent", value, "favorites"],
            "decision": ["decision", "--agent", value, "favorites", "--text", "Use X", "--evidence", "Owner: use X"],
            "close": ["close", "--agent", value, "favorites"],
            "pause": ["pause", "--agent", value, "favorites"],
        }
        for name, args in commands.items():
            with self.subTest(name):
                self.assert_refused(args, value, "Refusing to save the agent name")

    def test_init_and_update_with_a_secret_like_agent_name(self) -> None:  # FR-1 (init, init --update)
        value = token()
        self.assert_refused(["init", "--agent", value, "--template", str(EXAMPLE_TEMPLATE), "--commit", "all"], value,
                            "Refusing to save the agent name")
        self.assertFalse((self.repo / ".ai-dev-workflow").exists())
        self.init()
        self.assert_refused(["init", "--update", "--agent", value, "--commit", "none"], value,
                            "Refusing to save the agent name")


@needs_api
class ApiRefusalTest(SecretIdentityCase):
    """AC-4: each of the 15 functions that take `agent` refuses a secret-like one first; the three that take
    `session` refuse a secret-like or malformed one."""

    def call_refused(self, func_name: str, message: str, **kwargs: object) -> None:
        before = snapshot(self.repo)
        with self.assertRaises(workflow.WorkflowError) as caught:
            getattr(api, func_name)(repo=str(self.repo), **kwargs)
        self.assertIn(message, str(caught.exception))
        for value in kwargs.values():
            if isinstance(value, str) and value not in ("favorites", "second"):
                self.assertNotIn(value, str(caught.exception))
        self.assertEqual(before, snapshot(self.repo), f"{func_name} changed records although it refused")
        self.assertFalse(self.marker.exists())

    def test_every_function_that_takes_an_agent(self) -> None:
        self.to_implementation()
        value = token()
        task = {"task": "favorites"}
        calls = {
            "init_project": {"template": str(EXAMPLE_TEMPLATE), "commit": "all"},
            "update_setup": {"commit": "none"},
            "new_task": {"task": "second", "title": "Second", "task_type": "feature",
                         "invocation": "/ai-dev-workflow second"},
            "record_discovery": dict(task, summary="Summary."),
            "review": dict(task, passes=["J1"]),
            "approve": dict(task, document="spec", evidence="Approved"),
            "stage": dict(task, stage="TESTING"),
            "resume": task,
            "pause": task,
            "preflight": task,
            "step": dict(task, step="S1", status="done"),
            "run_check": dict(task, check="smoke", extra=[PY, "make_marker.py"]),
            "scope": task,
            "decision": dict(task, text="Use X", evidence="Owner: use X"),
            "close": task,
        }
        self.assertEqual(len(calls), 15)
        for name, kwargs in calls.items():
            with self.subTest(name):
                self.call_refused(name, "Refusing to save the agent name", agent=value, **kwargs)

    def test_every_function_that_takes_a_session(self) -> None:
        self.to_implementation()
        calls = {
            "new_task": {"task": "second", "title": "Second", "task_type": "feature",
                         "invocation": "/ai-dev-workflow second"},
            "resume": {"task": "favorites"},
            "preflight": {"task": "favorites"},
        }
        for name, kwargs in calls.items():
            for value in TOKENS:
                with self.subTest(name, kind=value[:4]):
                    self.call_refused(name, "Refusing to save the session id", agent="claude-code", session=value,
                                      **kwargs)
            for label, value in MALFORMED_SESSIONS.items():
                with self.subTest(name, malformed=label):
                    self.call_refused(name, SESSION_FORMAT, agent="claude-code", session=value, **kwargs)

    def test_check_name_is_checked_after_the_agent_and_before_anything_else(self) -> None:
        self.to_implementation()
        self.call_refused("run_check", "Refusing to save the check name", agent="claude-code", task="favorites",
                          check=token(), extra=[PY, "make_marker.py"])
        self.call_refused("run_check", "Refusing to save the agent name", agent=token(), task="favorites",
                          check=token("anthropic"))
        self.call_refused("run_check", "Refusing to save the check name", agent="claude-code", task="no-such-task",
                          check=token())


class LegitimateValuesTest(SecretIdentityCase):
    """AC-5, EC-8, EC-9: values the checks accept behave as before."""

    def active(self) -> dict:
        import json
        return json.loads((self.repo / ".ai-dev-workflow" / "ACTIVE").read_text(encoding="utf-8"))

    def test_accepted_session_ids(self) -> None:
        self.init()
        session = str(uuid.uuid4())
        self.new_task("--session", session)
        self.assertEqual(self.active()["session"], session)
        self.wf("pause", "favorites")
        self.wf("resume", "favorites", "--session", "${CLAUDE_SESSION_ID}")
        self.assertIsNone(self.active()["session"])
        self.wf("pause", "favorites")
        long_token = "a1" * 128
        self.wf("resume", "favorites", "--session", long_token)
        self.assertEqual(self.active()["session"], long_token)

    def test_placeholder_like_agent_name_is_accepted(self) -> None:
        self.init()
        self.wf("new", "favorites", "--title", "Saved favorites", "--invocation", "/ai-dev-workflow x",
                "--agent", "api_key=changeme")
        self.assertEqual(self.state()["created_by"], "api_key=changeme")

    def test_ordinary_check_names_still_run(self) -> None:
        self.to_implementation()
        self.wf("preflight", "favorites")
        out = self.wf("run", "favorites", "smoke test", "--", PY, "make_marker.py")
        self.assertIn("Check 'smoke test': passed", out)
        self.assertTrue(self.marker.exists())
        verification = (self.task / "verification.md").read_text(encoding="utf-8")
        self.assertIn("| smoke test | passed |", verification)

    def test_existing_refusal_order_with_a_legitimate_agent(self) -> None:  # EC-9
        self.init()
        code, _, err = self.cli("new", "Bad_Name", "--title", "x", "--invocation", "/ai-dev-workflow x")
        self.assertNotEqual(code, 0)
        self.assertIn("Task names use lowercase letters", err)
        code, _, err = self.cli("new", "--agent", token(), "Bad_Name", "--title", "x", "--invocation",
                                "/ai-dev-workflow x")
        self.assertNotEqual(code, 0)
        self.assertIn("Refusing to save the agent name", err)


@needs_api
class RecoveryTest(SecretIdentityCase):
    """EC-12 and EC-13 (AC-9, AC-10). These show the two repaired write paths; they are not a multi-file transaction
    (TD-29)."""

    def test_failed_new_removes_only_its_own_folder_and_leaves_the_active_task(self) -> None:  # EC-12
        self.init()
        self.new_task()
        before = snapshot(self.repo)
        with mock.patch.object(api, "save_state", side_effect=OSError("simulated disk failure")):
            with self.assertRaises(OSError):
                api.new_task(repo=str(self.repo), task="second", title="Second", task_type="feature",
                             invocation="/ai-dev-workflow second", agent="claude-code")
        self.assertFalse((self.repo / ".ai-dev-workflow" / "tasks" / "second").exists())
        self.assertEqual(before, snapshot(self.repo))

    def test_failed_new_never_deletes_a_file_it_did_not_write(self) -> None:  # requirement: no pre-existing data lost
        self.init()
        self.new_task()
        folder = self.repo / ".ai-dev-workflow" / "tasks" / "second"
        foreign = folder / "notes-from-the-user.txt"
        real_write = api.write_text

        def write_then_fail(path: Path, text: str) -> None:
            if path.name == "plan.md":
                foreign.write_text("not written by the engine", encoding="utf-8")
                raise OSError("simulated disk failure")
            real_write(path, text)

        with mock.patch.object(api, "write_text", side_effect=write_then_fail):
            with self.assertRaises(OSError):
                api.new_task(repo=str(self.repo), task="second", title="Second", task_type="feature",
                             invocation="/ai-dev-workflow second", agent="claude-code")
        self.assertTrue(foreign.exists(), "a file the engine did not write was deleted")
        self.assertEqual(sorted(p.name for p in folder.iterdir()), ["notes-from-the-user.txt"])
        self.assertEqual(self.state()["status"], "active")

    def test_failed_check_block_write_keeps_state_and_the_next_run_repairs_it(self) -> None:  # EC-13
        self.to_implementation()
        self.wf("preflight", "favorites")
        with mock.patch.object(api, "regenerate_check_block", side_effect=OSError("simulated disk failure")):
            with self.assertRaises(OSError) as caught:
                api.run_check(repo=str(self.repo), task="favorites", check="unit", agent="claude-code")
        self.assertIn("unit", [e["id"] for e in self.state()["checks"]], "state.json lost the recorded result")
        self.assertTrue(hasattr(caught.exception, "output_tail"))
        block = (self.task / "verification.md").read_text(encoding="utf-8")
        self.assertNotIn("| unit |", block)  # the block is behind state.json until the next run (TD-29)
        api.run_check(repo=str(self.repo), task="favorites", check="smoke", agent="claude-code",
                      extra=[PY, "make_marker.py"])
        block = (self.task / "verification.md").read_text(encoding="utf-8")
        self.assertIn("| unit | passed |", block)
        self.assertIn("| smoke | passed |", block)


class HookTest(SecretIdentityCase):
    """FR-12 (AC-12, EC-14 to EC-17): the Claude Code hooks treat the payload session id as untrusted input.

    An invalid session (secret-like or malformed) is never written to ACTIVE or the hook log and never printed.
    Inside an active task it can never bypass the gates: the edit is denied whatever the binding. Without an active
    task the hook stays harmless, as before."""

    INVALID = dict({"github token": token(), "anthropic key": token("anthropic")}, **MALFORMED_SESSIONS)

    def setUp(self) -> None:
        super().setUp()
        self.log = self.tmp / "hook.log"
        self._log_env = mock.patch.dict(os.environ, {"AI_DEV_WORKFLOW_HOOK_LOG": str(self.log)})
        self._log_env.start()

    def tearDown(self) -> None:
        self._log_env.stop()
        super().tearDown()

    @property
    def active_file(self) -> Path:
        return self.repo / ".ai-dev-workflow" / "ACTIVE"

    def log_lines(self) -> List[dict]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines() if line.strip()]

    def assert_invalid_session_handled(self, value: str, *, expect_deny: bool, path: Optional[Path] = None,
                                       expect_log: bool = True) -> None:
        before = snapshot(self.repo)
        log_before = len(self.log_lines())
        out = self.hook("claude-pre-edit", self.edit_payload(path or self.repo / "app.py", session=value))
        self.assertEqual('"permissionDecision": "deny"' in out, expect_deny, out)
        if expect_deny:
            self.assertIn("this session's id is not valid", out)
        self.assertNotIn(value, out)
        self.assertEqual(before, snapshot(self.repo), "records or ACTIVE changed for an invalid session")
        self.assert_not_persisted(value)
        if self.log.exists():
            self.assertNotIn(value.encode("utf-8"), self.log.read_bytes(), "the hook log holds the invalid session")
        new_lines = self.log_lines()[log_before:]
        if expect_log:
            self.assertTrue(new_lines, "the hook decision was not logged")
        for line in new_lines:
            self.assertIsNone(line.get("session"))
            self.assertTrue(line.get("session_rejected"))

    def implementation_task(self) -> None:
        self.to_implementation()
        self.wf("pause", "favorites")

    def test_active_task_bound_to_another_session_denies_an_invalid_session(self) -> None:  # EC-15
        self.implementation_task()
        self.wf("resume", "favorites", "--agent", "claude-code", "--session", "S1")
        self.wf("preflight", "favorites", "--agent", "claude-code", "--session", "S1")
        for label, value in self.INVALID.items():
            with self.subTest(label):
                self.assert_invalid_session_handled(value, expect_deny=True)

    def test_active_unbound_claude_task_never_binds_an_invalid_session(self) -> None:  # EC-15
        self.implementation_task()
        self.wf("resume", "favorites", "--agent", "claude-code")
        for label, value in self.INVALID.items():
            with self.subTest(label):
                self.assert_invalid_session_handled(value, expect_deny=True)
        self.assertIsNone(json.loads(self.active_file.read_text(encoding="utf-8"))["session"])

    def test_active_task_of_another_agent_denies_an_invalid_session(self) -> None:  # EC-15
        self.implementation_task()
        self.wf("resume", "favorites", "--agent", "codex")
        for label, value in self.INVALID.items():
            with self.subTest(label):
                self.assert_invalid_session_handled(value, expect_deny=True)

    def test_records_paths_are_denied_too_inside_an_active_task(self) -> None:  # EC-15
        self.init()
        self.new_task("--agent", "claude-code", "--session", "S1")
        self.assert_invalid_session_handled(token(), expect_deny=True, path=self.task / "spec.md")

    def test_without_an_active_task_an_invalid_session_is_allowed_and_not_logged(self) -> None:  # EC-16
        with tempfile.TemporaryDirectory() as other:
            self.assert_invalid_session_handled(token(), expect_deny=False, path=Path(other) / "x.py")
        self.assert_invalid_session_handled(token(), expect_deny=False)  # repository without records
        self.implementation_task()  # paused: ACTIVE removed; the decision is still logged, without the value
        self.assert_invalid_session_handled(token(), expect_deny=False)

    def test_paused_or_closed_task_with_an_active_pointer_allows_an_invalid_session(self) -> None:  # EC-16
        self.init()
        self.new_task("--agent", "claude-code")
        pointer = self.active_file.read_bytes()
        self.wf("pause", "favorites")
        self.active_file.write_bytes(pointer)  # ACTIVE left behind for a paused task
        self.assert_invalid_session_handled(token(), expect_deny=False)
        state = self.state()
        state["status"] = "closed"
        (self.task / "state.json").write_text(json.dumps(state), encoding="utf-8")
        self.assert_invalid_session_handled(token("anthropic"), expect_deny=False)

    def test_prompt_hook_is_silent_for_an_invalid_session(self) -> None:  # EC-17
        self.init()
        self.new_task("--agent", "claude-code")
        for label, value in self.INVALID.items():
            with self.subTest(label):
                before = snapshot(self.repo)
                out = self.hook("claude-prompt", {"session_id": value, "cwd": str(self.repo)})
                self.assertEqual(out, "")
                self.assertEqual(before, snapshot(self.repo))

    def test_unverifiable_non_text_session_is_denied_inside_an_active_task(self) -> None:  # condition 1
        self.implementation_task()
        self.wf("resume", "favorites", "--agent", "claude-code", "--session", "S1")
        before = snapshot(self.repo)
        payload = dict(self.edit_payload(self.repo / "app.py"), session_id=12345)
        out = self.hook("claude-pre-edit", payload)
        self.assertIn('"permissionDecision": "deny"', out)
        self.assertEqual(before, snapshot(self.repo))
        line = self.log_lines()[-1]
        self.assertIsNone(line["session"])
        self.assertTrue(line["session_rejected"])

    def test_multi_line_secret_like_session_is_rejected(self) -> None:  # audit F-1 for the hook path
        self.implementation_task()
        self.wf("resume", "favorites", "--agent", "claude-code")
        for label, value in MULTI_LINE.items():
            with self.subTest(label):
                self.assert_invalid_session_handled(value, expect_deny=True)

    def test_huge_session_is_refused_quickly(self) -> None:  # audit F-5
        import time
        started = time.monotonic()
        self.assertIsNotNone(workflow_session_problem("a." * 200000))
        self.assertLess(time.monotonic() - started, 2.0)

    def test_valid_uuid_session_behaves_as_before(self) -> None:  # EC-14
        self.implementation_task()
        self.wf("resume", "favorites", "--agent", "claude-code")
        session = str(uuid.uuid4())
        out = self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py", session=session))
        self.assertIn("preflight", out)  # binds the session, then asks for a preflight in it
        self.assertEqual(json.loads(self.active_file.read_text(encoding="utf-8"))["session"], session)
        line = self.log_lines()[-1]
        self.assertEqual(line["session"], session)
        self.assertNotIn("session_rejected", line)
        self.wf("preflight", "favorites", "--agent", "claude-code", "--session", session)
        self.assertEqual(self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py", session=session)), "")
        reminder = self.hook("claude-prompt", {"session_id": session, "cwd": str(self.repo)})
        self.assertIn("[AIDevWorkflow] Active task 'favorites'", reminder)


if __name__ == "__main__":
    unittest.main()
