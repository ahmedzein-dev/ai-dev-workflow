"""F1.0.5 task-state schema and storage reliability regressions."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from unittest import mock

from helpers import ROOT, SKILL, WorkflowTestCase
from aidw.store import lock
from aidw.store import migrate
from aidw import api
from aidw.agents import claude_hooks
from aidw.infra import text as text_module
from workflow import WorkflowError, load_state, read_active


class StateSchemaTest(WorkflowTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.init()
        self.new_task()

    def save_raw(self, value: object) -> None:
        (self.task / "state.json").write_text(json.dumps(value), encoding="utf-8")

    def test_existing_v100_record_loads_without_rewrite(self) -> None:
        source = ROOT / "tests" / "fixtures" / "state-v1.0.0.json"
        legacy = self.repo / ".ai-dev-workflow" / "tasks" / "legacy-fixture" / "state.json"
        legacy.parent.mkdir()
        legacy.write_bytes(source.read_bytes())
        before = legacy.read_bytes()
        state = load_state(self.repo, "legacy-fixture")
        self.assertEqual(state["schema"], 1)
        self.assertEqual(legacy.read_bytes(), before)

    def test_missing_optional_fields_default_only_in_memory(self) -> None:
        state = self.state()
        state.pop("checks")
        state["future_field"] = {"value": 1}
        self.save_raw(state)
        before = (self.task / "state.json").read_bytes()
        loaded = load_state(self.repo, "favorites")
        self.assertEqual(loaded["checks"], [])
        self.assertEqual(loaded["future_field"], {"value": 1})
        self.assertEqual((self.task / "state.json").read_bytes(), before)

    def test_invalid_schema_and_shapes_refuse_without_write(self) -> None:
        good = self.state()
        cases = [
            ({**good, "schema": True}, "schema"),
            ({**good, "schema": 2}, "schema"),
            ({k: v for k, v in good.items() if k != "schema"}, "schema"),
            ({**good, "id": "other-task"}, "'id'"),
            ({**good, "approvals": {"spec": []}}, "approvals"),
            ({**good, "history": ["invalid"]}, "history"),
            ({**good, "checks": ["invalid"]}, "checks"),
            ([], "root"),
        ]
        for value, message in cases:
            with self.subTest(message=message, value=value):
                self.save_raw(value)
                before = (self.task / "state.json").read_bytes()
                with self.assertRaisesRegex(WorkflowError, message):
                    load_state(self.repo, "favorites")
                self.assertEqual((self.task / "state.json").read_bytes(), before)

    def test_present_corrupt_active_is_not_absent(self) -> None:
        pointer = self.repo / ".ai-dev-workflow" / "ACTIVE"
        pointer.write_text("{broken", encoding="utf-8")
        with self.assertRaisesRegex(WorkflowError, "ACTIVE pointer"):
            read_active(self.repo)
        denied = self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py"))
        self.assertIn('"permissionDecision": "deny"', denied)
        pointer.write_text(json.dumps({"task": ""}), encoding="utf-8")
        with self.assertRaisesRegex(WorkflowError, "ACTIVE pointer"):
            read_active(self.repo)

    def test_malformed_active_directory_and_task_id_fail_closed(self) -> None:
        pointer = self.repo / ".ai-dev-workflow" / "ACTIVE"
        pointer.unlink()
        pointer.mkdir()
        self.assertIn('"permissionDecision": "deny"',
                      self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py")))
        pointer.rmdir()
        pointer.write_text(json.dumps({"task": "../outside"}), encoding="utf-8")
        with self.assertRaisesRegex(WorkflowError, "ACTIVE pointer"):
            read_active(self.repo)
        self.assertIn('"permissionDecision": "deny"',
                      self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py")))

    def test_dangling_active_symlink_fails_closed_when_supported(self) -> None:
        pointer = self.repo / ".ai-dev-workflow" / "ACTIVE"
        pointer.unlink()
        try:
            pointer.symlink_to(self.repo / "missing-active-target")
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable on this runner")
        with self.assertRaisesRegex(WorkflowError, "ACTIVE pointer"):
            read_active(self.repo)
        self.assertIn('"permissionDecision": "deny"',
                      self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py")))

    def test_active_fifo_fails_closed_without_blocking_when_supported(self) -> None:
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO files are unavailable on this runner")
        pointer = self.repo / ".ai-dev-workflow" / "ACTIVE"
        pointer.unlink()
        os.mkfifo(pointer)
        with self.assertRaisesRegex(WorkflowError, "ACTIVE pointer"):
            read_active(self.repo)
        self.assertIn('"permissionDecision": "deny"',
                      self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py")))

    def test_bad_stage_and_status_do_not_echo_values(self) -> None:
        state = self.state()
        synthetic = "ghp_" + "A" * 36
        state["stage"] = synthetic
        state["status"] = synthetic
        self.save_raw(state)
        with self.assertRaises(WorkflowError) as caught:
            load_state(self.repo, "favorites")
        self.assertNotIn(synthetic, str(caught.exception))
        self.assertIn("unknown stage", str(caught.exception))

    def test_corrupt_current_task_cannot_be_replaced_by_new_active_task(self) -> None:
        pointer = self.repo / ".ai-dev-workflow" / "ACTIVE"
        original_pointer = pointer.read_bytes()
        state = self.state()
        state["schema"] = 99
        self.save_raw(state)
        refusal = self.wf("new", "second", "--title", "Second", "--invocation",
                          "/ai-dev-workflow second", expect=1)
        self.assertIn("unsupported task schema", refusal)
        self.assertEqual(pointer.read_bytes(), original_pointer)
        self.assertFalse((self.repo / ".ai-dev-workflow" / "tasks" / "second").exists())

    def test_next_locked_writes_clean_proven_state_and_active_orphans(self) -> None:
        state_temp = self.task / ".state.json.999999999.tmp"
        active_temp = self.repo / ".ai-dev-workflow" / ".ACTIVE.999999999.tmp"
        for path in (state_temp, active_temp):
            path.write_text("orphan", encoding="utf-8")
        def status(pid: int, signal: int) -> None:
            if pid == 999999999:
                raise ProcessLookupError()
            self.fail("unexpected liveness probe")

        with mock.patch.object(text_module.os, "kill", side_effect=status):
            api.record_discovery(repo=self.repo, task="favorites", agent="codex", summary="Current state")
            api.resume(repo=self.repo, task="favorites", agent="codex")
        if os.name == "nt":
            self.assertTrue(state_temp.exists())
            self.assertTrue(active_temp.exists())
        else:
            self.assertFalse(state_temp.exists())
            self.assertFalse(active_temp.exists())


class ConcurrentStoreTest(WorkflowTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.init()
        self.new_task()

    def test_two_process_writers_preserve_both_discoveries(self) -> None:
        go = self.tmp / "go"
        markers = [self.tmp / f"ready-{index}" for index in range(2)]
        code = (
            "import sys,time; from pathlib import Path; from aidw import api; "
            "repo=Path(sys.argv[1]); ready=Path(sys.argv[2]); go=Path(sys.argv[3]); "
            "ready.write_text('ready'); deadline=time.monotonic()+10; "
            "\nwhile not go.exists() and time.monotonic()<deadline: time.sleep(0.01)\n"
            "if not go.exists(): raise RuntimeError('start barrier timed out')\n"
            "api.record_discovery(repo=repo, task='favorites', agent='codex', "
            "inspected=[sys.argv[4]], summary='concurrent discovery')"
        )
        children = [subprocess.Popen([sys.executable, "-c", code, str(self.repo), str(markers[index]),
                                      str(go), name], cwd=str(SKILL / "scripts"),
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    for index, name in enumerate(("app.py", "other.py"))]
        try:
            deadline = time.monotonic() + 10
            while not all(marker.exists() for marker in markers) and time.monotonic() < deadline:
                self.assertTrue(all(child.poll() is None for child in children), "writer exited before start")
                time.sleep(0.01)
            self.assertTrue(all(marker.exists() for marker in markers), "writers did not reach start barrier")
            go.write_text("start", encoding="utf-8")
            for child in children:
                output, error = child.communicate(timeout=15)
                self.assertEqual(child.returncode, 0, (output + error).decode(errors="replace"))
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
                    child.wait(timeout=5)
                if child.stdout:
                    child.stdout.close()
                if child.stderr:
                    child.stderr.close()
        state = self.state()
        self.assertEqual(set(state["discovery"]["inspected"]), {"app.py", "other.py"})
        self.assertEqual(sum(item["event"] == "discovery" for item in state["history"]), 2)

    def test_delayed_check_does_not_overwrite_intervening_state(self) -> None:
        started, continue_check = threading.Event(), threading.Event()
        failures = []

        def fake_execute(*_args: object) -> tuple:
            started.set()
            if not continue_check.wait(5):
                raise AssertionError("check was not released")
            return 0, "check output\n", 0.01, None

        def run() -> None:
            try:
                api.run_check(repo=self.repo, task="favorites", check="unit", agent="codex")
            except Exception as exc:  # noqa: BLE001 - inspect the exact concurrent failure
                failures.append(exc)

        with mock.patch.object(api, "execute", side_effect=fake_execute):
            worker = threading.Thread(target=run)
            worker.start()
            try:
                self.assertTrue(started.wait(5), "check did not begin")
                api.record_discovery(repo=self.repo, task="favorites", agent="codex", summary="A newer write")
            finally:
                continue_check.set()
                worker.join(timeout=5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(failures), 1)
        self.assertIsInstance(failures[0], WorkflowError)
        self.assertIn("Task state changed", str(failures[0]))
        self.assertEqual(getattr(failures[0], "output_tail"), ["check output"])
        state = self.state()
        self.assertEqual(state["discovery"]["summary"], "A newer write")
        self.assertEqual(state["checks"], [])

    def test_competing_resumes_leave_one_active_task(self) -> None:
        self.wf("new", "second", "--title", "Second", "--invocation", "Use AIDevWorkflow")
        barrier = threading.Barrier(3)
        failures = []

        def resume(task: str) -> None:
            try:
                barrier.wait(timeout=5)
                api.resume(repo=self.repo, task=task, agent="codex")
            except Exception as exc:  # noqa: BLE001 - report thread failures to the test
                failures.append(exc)

        workers = [threading.Thread(target=resume, args=(task,)) for task in ("favorites", "second")]
        for worker in workers:
            worker.start()
        barrier.wait(timeout=5)
        for worker in workers:
            worker.join(timeout=5)
            self.assertFalse(worker.is_alive())
        self.assertEqual(failures, [])
        active = read_active(self.repo)
        self.assertIsNotNone(active)
        self.assertEqual(load_state(self.repo, active["task"])["status"], "active")
        other = ({"favorites", "second"} - {active["task"]}).pop()
        self.assertEqual(load_state(self.repo, other)["status"], "paused")

    def test_competing_claude_bindings_keep_one_complete_session(self) -> None:
        self.wf("resume", "favorites", "--agent", "claude-code")
        barrier = threading.Barrier(3)
        failures = []

        def bind(session: str) -> None:
            payload = self.edit_payload(self.task / "spec.md", session=session)
            try:
                barrier.wait(timeout=5)
                claude_hooks.hook_claude_pre_edit(json.dumps(payload))
            except Exception as exc:  # noqa: BLE001 - report thread failures to the test
                failures.append(exc)

        workers = [threading.Thread(target=bind, args=(session,)) for session in ("S1", "S2")]
        for worker in workers:
            worker.start()
        barrier.wait(timeout=5)
        for worker in workers:
            worker.join(timeout=5)
            self.assertFalse(worker.is_alive())
        self.assertEqual(failures, [])
        active = read_active(self.repo)
        self.assertIn(active["session"], ("S1", "S2"))
        self.assertEqual(active["agent"], "claude-code")


class LockTest(WorkflowTestCase):
    def test_special_or_oversized_lock_is_ambiguous_and_bounded(self) -> None:
        path = lock._lock_path(self.repo, "favorites")
        path.parent.mkdir(parents=True)
        path.write_bytes(b"x" * 5000)
        self.assertIsNone(lock._owner(path))
        with self.assertRaisesRegex(WorkflowError, "Timed out"):
            with lock.locked_records(self.repo, ("favorites",), timeout=0.1):
                self.fail("oversized lock was stolen")
        path.unlink()
        if not hasattr(os, "mkfifo"):
            return
        os.mkfifo(path)
        self.assertIsNone(lock._owner(path))
        with self.assertRaisesRegex(WorkflowError, "Timed out"):
            with lock.locked_records(self.repo, ("favorites",), timeout=0.1):
                self.fail("FIFO lock was stolen")

    def test_windows_liveness_is_unknown_without_os_kill(self) -> None:
        owner = {"token": "test", "pid": 999999999, "host": lock._HOST}
        with mock.patch.object(lock.os, "name", "nt"):
            with mock.patch.object(lock.os, "kill", side_effect=AssertionError("unsafe Windows probe")):
                self.assertFalse(lock._dead_same_host(owner))
                self.assertEqual(text_module.cleanup_orphan_temps(self.repo / "record.txt"), 0)

    def test_legacy_project_keeps_lock_files_out_of_git(self) -> None:
        self.init()
        ignore = self.repo / ".ai-dev-workflow" / ".gitignore"
        legacy = "ACTIVE\n*.local.json\n.locks/active.lock\n"
        ignore.write_text(legacy, encoding="utf-8")
        with lock.locked_records(self.repo, ("favorites",)):
            path = lock._lock_path(self.repo, "favorites")
            ignored = subprocess.run(["git", "check-ignore", "-q", "--", str(path)],
                                     cwd=self.repo, capture_output=True)
            self.assertEqual(ignored.returncode, 0, ignored.stderr)
        self.assertEqual(ignore.read_text(encoding="utf-8"), legacy)

    def test_crashed_process_lock_is_recovered_only_when_death_is_provable(self) -> None:
        marker = self.tmp / "lock-ready"
        code = ("import sys,time; from pathlib import Path; "
                "from aidw.store.lock import locked_records; "
                "repo=Path(sys.argv[1]); marker=Path(sys.argv[2]); "
                "ctx=locked_records(repo, ('favorites',)); ctx.__enter__(); "
                "marker.write_text('ready'); time.sleep(30)")
        child = subprocess.Popen([sys.executable, "-c", code, str(self.repo), str(marker)],
                                 cwd=str(SKILL / "scripts"), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 5
            while not marker.exists() and child.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(marker.exists(), child.stderr.read().decode() if child.poll() is not None else "lock not acquired")
            child.kill()
            child.wait(timeout=5)
            path = lock._lock_path(self.repo, "favorites")
            self.assertTrue(path.exists())
            if lock._dead_same_host(lock._owner(path)):
                with lock.locked_records(self.repo, ("favorites",), timeout=0.5):
                    self.assertTrue(path.exists())
                self.assertFalse(path.exists())
            else:
                before = path.read_bytes()
                with self.assertRaisesRegex(WorkflowError, "Timed out"):
                    with lock.locked_records(self.repo, ("favorites",), timeout=0.1):
                        self.fail("ambiguous owner was stolen")
                self.assertEqual(path.read_bytes(), before)
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=5)
            child.stdout.close()
            child.stderr.close()

    def test_lock_order_is_active_then_sorted_tasks(self) -> None:
        paths = []
        real_acquire = lock._acquire

        def record(path: Path, timeout: float, label: str):
            paths.append(path.name)
            return real_acquire(path, timeout, label)

        with mock.patch.object(lock, "_acquire", side_effect=record):
            with lock.locked_records(self.repo, ("z", "a", "z"), active=True):
                self.assertEqual(len(paths), 3)
        self.assertEqual(paths[0], "active.lock")
        self.assertEqual(paths[1:], [lock._lock_path(self.repo, name).name for name in ("a", "z")])

    def test_live_lock_times_out_without_theft(self) -> None:
        path = lock._lock_path(self.repo, "favorites")
        with lock.locked_records(self.repo, ("favorites",)):
            before = path.read_bytes()
            with self.assertRaisesRegex(WorkflowError, "Timed out"):
                with lock.locked_records(self.repo, ("favorites",), timeout=0.1):
                    self.fail("live lock was stolen")
            self.assertEqual(path.read_bytes(), before)
        self.assertFalse(path.exists())

    def test_stale_recovery_requires_proof_and_preserves_new_owner(self) -> None:
        path = lock._lock_path(self.repo, "favorites")
        path.parent.mkdir(parents=True)
        stale = {"token": "old", "pid": 999999999, "host": socket.gethostname(), "created": 0}
        path.write_text(json.dumps(stale), encoding="utf-8")
        # A platform may not expose reliable process liveness. Test the recovery state machine
        # with proof restricted to the observed old owner, never to the newly acquired owner.
        with mock.patch.object(lock, "_dead_same_host", side_effect=lambda owner: bool(owner and owner.get("token") == "old")):
            with lock.locked_records(self.repo, ("favorites",), timeout=0.2):
                self.assertNotEqual(json.loads(path.read_text())["token"], "old")
        self.assertFalse(path.exists())

    def test_ambiguous_owner_is_not_removed(self) -> None:
        path = lock._lock_path(self.repo, "favorites")
        path.parent.mkdir(parents=True)
        data = {"token": "old", "pid": os.getpid(), "host": "another-host", "created": 0}
        path.write_text(json.dumps(data), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaisesRegex(WorkflowError, "Timed out"):
            with lock.locked_records(self.repo, ("favorites",), timeout=0.1):
                self.fail("ambiguous lock was stolen")
        self.assertEqual(path.read_bytes(), before)


class DurableWriteTest(WorkflowTestCase):
    def test_pre_replace_sync_failure_keeps_old_bytes_and_cleans_owned_temp(self) -> None:
        target = self.repo / "record.txt"
        target.write_text("old", encoding="utf-8")
        with mock.patch.object(text_module.os, "fsync", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                text_module.write_text(target, "new")
        self.assertEqual(target.read_text(encoding="utf-8"), "old")
        self.assertEqual(list(target.parent.glob(".record.txt.*.tmp")), [])

    def test_post_replace_sync_failure_reports_indeterminate_result(self) -> None:
        if os.name == "nt":
            self.skipTest("Windows has no directory sync in this design")
        target = self.repo / "record.txt"
        target.write_text("old", encoding="utf-8")
        calls = 0
        real_fsync = os.fsync

        def sync(fd: int) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("directory sync failed")
            real_fsync(fd)

        with mock.patch.object(text_module.os, "fsync", side_effect=sync):
            with self.assertRaisesRegex(WorkflowError, "durability is indeterminate"):
                text_module.write_text(target, "new")
        self.assertEqual(target.read_text(encoding="utf-8"), "new")
        self.assertEqual(calls, 2)

    def test_only_known_dead_writer_temps_beside_a_valid_target_are_removed(self) -> None:
        target = self.repo / "record.txt"
        target.write_text("current", encoding="utf-8")
        stale = self.repo / ".record.txt.999999999.tmp"
        live = self.repo / f".record.txt.{os.getpid()}.tmp"
        unknown = self.repo / "user-notes.tmp"
        for path in (stale, live, unknown):
            path.write_text("preserve unless proven orphan", encoding="utf-8")
        def process_status(pid: int, signal: int) -> None:
            if pid == 999999999:
                raise ProcessLookupError()
            if pid != os.getpid():
                self.fail("unexpected liveness probe")

        with lock.locked_records(self.repo, ("favorites",)):
            with mock.patch.object(text_module.os, "kill", side_effect=process_status):
                self.assertEqual(text_module.cleanup_orphan_temps(target), 0 if os.name == "nt" else 1)
        self.assertEqual(stale.exists(), os.name == "nt")
        self.assertTrue(live.exists())
        self.assertTrue(unknown.exists())
        target.unlink()
        sole = self.repo / ".record.txt.999999999.tmp"
        sole.write_text("recovery candidate", encoding="utf-8")
        self.assertEqual(text_module.cleanup_orphan_temps(target), 0)
        self.assertTrue(sole.exists())


class TaskCreationRollbackTest(WorkflowTestCase):
    def test_pre_replacement_active_failure_cleans_only_new_task_files(self) -> None:
        self.init()
        pointer = self.repo / ".ai-dev-workflow" / "ACTIVE"
        with mock.patch("aidw.store.state.save_active", side_effect=OSError("injected pointer failure")):
            with self.assertRaisesRegex(OSError, "injected pointer failure"):
                api.new_task(repo=self.repo, task="new-task", title="New task", task_type="feature",
                             invocation="/ai-dev-workflow new task", agent="codex")
        self.assertFalse(pointer.exists())
        self.assertFalse((self.repo / ".ai-dev-workflow" / "tasks" / "new-task").exists())

    def test_partial_prior_task_update_keeps_new_records_for_recovery(self) -> None:
        self.init()
        self.new_task()
        pointer = self.repo / ".ai-dev-workflow" / "ACTIVE"
        before_pointer = pointer.read_bytes()
        with mock.patch("aidw.store.state.save_active", side_effect=OSError("injected pointer failure")):
            with self.assertRaisesRegex(OSError, "injected pointer failure"):
                api.new_task(repo=self.repo, task="new-task", title="New task", task_type="feature",
                             invocation="/ai-dev-workflow new task", agent="codex")
        self.assertEqual(pointer.read_bytes(), before_pointer)
        self.assertEqual(load_state(self.repo, "favorites")["status"], "paused")
        self.assertTrue((self.repo / ".ai-dev-workflow" / "tasks" / "new-task" / "state.json").exists())


class MigrationTest(WorkflowTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.init()
        self.new_task()

    @staticmethod
    def _fixture_converter(state: dict) -> dict:
        state["schema"] = 2
        state["test_marker"] = "fixture only"
        return state

    def test_schema_one_preview_and_apply_without_converter_are_nonwriting(self) -> None:
        before = (self.task / "state.json").read_bytes()
        preview = json.loads(self.wf("migrate", "favorites", "--json"))
        self.assertFalse(preview["available"])
        self.assertFalse(preview["changed"])
        self.assertEqual(preview["validation"], {"source": "passed", "proposed": "not applicable"})
        self.assertIn("Validation: source passed; proposed not applicable", self.wf("migrate", "favorites"))
        self.assertEqual((self.task / "state.json").read_bytes(), before)
        self.assertFalse((self.task / ".migrate-backup").exists())
        self.assertIn("No production migration", self.wf("migrate", "favorites", "--apply", expect=1))
        self.assertEqual((self.task / "state.json").read_bytes(), before)

    def test_test_only_converter_preview_apply_retry_and_rollback(self) -> None:
        before = (self.task / "state.json").read_bytes()
        with mock.patch.dict(migrate.CONVERTERS, {1: (2, self._fixture_converter)}, clear=True):
            preview = api.migrate_task(repo=self.repo, task="favorites", agent="codex")
            self.assertTrue(preview["available"])
            self.assertEqual(preview["target_schema"], 2)
            self.assertEqual(preview["validation"], {"source": "passed", "proposed": "passed"})
            self.assertEqual((self.task / "state.json").read_bytes(), before)
            self.assertFalse((self.task / ".migrate-backup").exists())
            applied = api.migrate_task(repo=self.repo, task="favorites", agent="codex", apply=True)
            backup = self.repo / applied["backup"]
            self.assertEqual((backup / "state.json").read_bytes(), before)
            self.assertEqual(json.loads((self.task / "state.json").read_text())["schema"], 2)
            ignored = subprocess.run(["git", "check-ignore", "-q", str(backup / "state.json")],
                                     cwd=self.repo, capture_output=True)
            self.assertEqual(ignored.returncode, 0, ignored.stderr)
            retry = api.migrate_task(repo=self.repo, task="favorites", agent="codex")
            self.assertFalse(retry["available"])
            self.assertEqual(len([p for p in (self.task / ".migrate-backup").iterdir() if p.is_dir()]), 1)
            restored = api.migrate_task(repo=self.repo, task="favorites", agent="codex",
                                        rollback=applied["backup_id"])
            self.assertEqual(restored["schema"], 1)
            self.assertEqual((self.task / "state.json").read_bytes(), before)
            self.assertEqual((backup / "state.json").read_bytes(), before)

    def test_rollback_refuses_later_edits(self) -> None:
        with mock.patch.dict(migrate.CONVERTERS, {1: (2, self._fixture_converter)}, clear=True):
            applied = api.migrate_task(repo=self.repo, task="favorites", agent="codex", apply=True)
        path = self.task / "state.json"
        changed = json.loads(path.read_text(encoding="utf-8"))
        changed["later_evidence"] = {"kept": True}
        path.write_text(json.dumps(changed), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaisesRegex(WorkflowError, "erase newer evidence"):
            api.migrate_task(repo=self.repo, task="favorites", agent="codex",
                             rollback=applied["backup_id"])
        self.assertEqual(path.read_bytes(), before)
        self.assertTrue((self.repo / applied["backup"] / "state.json").exists())

    def test_conversion_and_backup_failures_preserve_source(self) -> None:
        path = self.task / "state.json"
        before = path.read_bytes()

        def invalid(state: dict) -> dict:
            state["schema"] = 2
            state["history"] = []
            return state

        with mock.patch.dict(migrate.CONVERTERS, {1: (2, invalid)}, clear=True):
            with self.assertRaisesRegex(WorkflowError, "evidence"):
                api.migrate_task(repo=self.repo, task="favorites", agent="codex", apply=True)
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse((self.task / ".migrate-backup").exists())
        with mock.patch.dict(migrate.CONVERTERS, {1: (2, self._fixture_converter)}, clear=True):
            with mock.patch.object(migrate, "write_bytes", side_effect=OSError("backup failure")):
                with self.assertRaises(OSError):
                    api.migrate_task(repo=self.repo, task="favorites", agent="codex", apply=True)
        self.assertEqual(path.read_bytes(), before)

    def test_manifest_and_target_write_failures_leave_original_state(self) -> None:
        path = self.task / "state.json"
        before = path.read_bytes()
        with mock.patch.dict(migrate.CONVERTERS, {1: (2, self._fixture_converter)}, clear=True):
            with mock.patch.object(migrate, "save_json", side_effect=OSError("manifest failure")):
                with self.assertRaises(OSError):
                    api.migrate_task(repo=self.repo, task="favorites", agent="codex", apply=True)
            self.assertEqual(path.read_bytes(), before)
            real_write = migrate.write_bytes

            def fail_target(destination: Path, data: bytes) -> None:
                if destination.resolve() == path.resolve():
                    raise OSError("target failure before replace")
                real_write(destination, data)

            with mock.patch.object(migrate, "write_bytes", side_effect=fail_target):
                with self.assertRaises(OSError):
                    api.migrate_task(repo=self.repo, task="favorites", agent="codex", apply=True)
        self.assertEqual(path.read_bytes(), before)

    def test_corrupt_backup_refuses_rollback_without_touching_migrated_state(self) -> None:
        with mock.patch.dict(migrate.CONVERTERS, {1: (2, self._fixture_converter)}, clear=True):
            applied = api.migrate_task(repo=self.repo, task="favorites", agent="codex", apply=True)
        path = self.task / "state.json"
        before = path.read_bytes()
        (self.repo / applied["backup"] / "state.json").write_bytes(b"broken")
        with self.assertRaisesRegex(WorkflowError, "integrity check"):
            api.migrate_task(repo=self.repo, task="favorites", agent="codex",
                             rollback=applied["backup_id"])
        self.assertEqual(path.read_bytes(), before)
