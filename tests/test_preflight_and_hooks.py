"""Preflight revalidation and the Claude Code hooks: enforce inside an active task, stay silent everywhere else."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from helpers import FILLED_PLAN, WorkflowTestCase


def denied(output: str) -> bool:
    return '"permissionDecision": "deny"' in output


class PreflightTest(WorkflowTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.to_implementation()

    def test_passes_with_valid_approvals_and_records_a_checkpoint(self) -> None:
        self.assertIn("PREFLIGHT PASSED", self.wf("preflight", "favorites"))
        kinds = [c["kind"] for c in self.state()["checkpoints"]]
        self.assertEqual(kinds[-1], "preflight")

    def test_refuses_outside_code_stages(self) -> None:
        self.wf("stage", "favorites", "PLANNING", "--reason", "plan needs another step")
        self.assertIn("code may change only", self.wf("preflight", "favorites", expect=1))

    def test_refuses_while_paused(self) -> None:
        self.wf("pause", "favorites")
        self.assertIn("paused", self.wf("preflight", "favorites", expect=1))
        self.wf("resume", "favorites")
        self.wf("preflight", "favorites")

    def test_reports_changes_no_step_explains(self) -> None:
        self.wf("preflight", "favorites")
        self.write("app.py", "changed outside any step\n")
        out = self.wf("preflight", "favorites")
        self.assertIn("no recorded step explains", out)
        self.assertIn("app.py", out)

    def test_refuses_when_records_contain_a_secret(self) -> None:
        path = self.task / "verification.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nkey: " + "AKIA" + "ABCDEFGHIJKLMNOP" + "\n", encoding="utf-8")
        self.assertIn("AWS access key", self.wf("preflight", "favorites", expect=1))


class ClaudeHookTest(WorkflowTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.init()

    def bind(self, session: str = "S1") -> None:
        self.wf("resume", "favorites", "--agent", "claude-code", "--session", session)

    def test_no_task_and_no_records_never_interfere(self) -> None:
        self.assertEqual(self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py")), "")
        with tempfile.TemporaryDirectory() as other:
            self.assertEqual(self.hook("claude-pre-edit", self.edit_payload(Path(other) / "x.py")), "")
        self.assertEqual(self.hook("claude-pre-edit", raw="not json"), "")
        self.assertEqual(self.hook("claude-pre-edit", raw=""), "")

    def test_blocks_code_before_plan_approval_but_allows_records(self) -> None:
        self.new_task("--agent", "claude-code", "--session", "S1")
        self.assertTrue(denied(self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py"))))
        self.assertFalse(denied(self.hook("claude-pre-edit", self.edit_payload(self.task / "spec.md"))))
        reason = json.loads(self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py")))
        self.assertIn("pause the task", reason["hookSpecificOutput"]["permissionDecisionReason"])

    def test_other_sessions_other_repositories_and_paused_tasks_are_unaffected(self) -> None:
        self.new_task("--agent", "claude-code", "--session", "S1")
        self.assertEqual(self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py", session="S2")), "")
        with tempfile.TemporaryDirectory() as other:
            self.assertEqual(self.hook("claude-pre-edit", self.edit_payload(Path(other) / "x.py")), "")
        self.wf("pause", "favorites")
        self.assertEqual(self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py")), "")

    def test_closed_task_does_not_interfere(self) -> None:
        self.new_task("--agent", "claude-code", "--session", "S1")
        self.wf("stage", "favorites", "FINAL_REPORT", "--reason", "user cancelled the feature")
        state = self.state()
        state["status"] = "closed"
        (self.task / "state.json").write_text(json.dumps(state), encoding="utf-8")
        self.assertEqual(self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py")), "")

    def test_requires_preflight_in_this_session_then_allows_code(self) -> None:
        self.to_implementation_without_init()
        self.bind("S1")
        out = self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py"))
        self.assertTrue(denied(out))
        self.assertIn("preflight", out)
        self.wf("preflight", "favorites", "--agent", "claude-code", "--session", "S1")
        self.assertEqual(self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py")), "")

    def test_protects_snapshots_state_and_approved_documents(self) -> None:
        self.to_implementation_without_init()
        self.bind("S1")
        self.wf("preflight", "favorites", "--agent", "claude-code", "--session", "S1")
        for rel in ("approved/plan.v1.md", "state.json", "plan.md", "spec.md"):
            self.assertTrue(denied(self.hook("claude-pre-edit", self.edit_payload(self.task / rel))), rel)
        self.assertFalse(denied(self.hook("claude-pre-edit", self.edit_payload(self.task / "verification.md"))))

    def test_an_invalid_approval_blocks_code(self) -> None:
        self.to_implementation_without_init()
        self.bind("S1")
        self.wf("preflight", "favorites", "--agent", "claude-code", "--session", "S1")
        self.write(".ai-dev-workflow/tasks/favorites/plan.md", FILLED_PLAN + "\nExtra line.\n")
        out = self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py"))
        self.assertTrue(denied(out))
        self.assertIn("changed after", out)

    def test_an_unbound_task_is_claimed_by_the_claude_session(self) -> None:
        self.new_task("--agent", "claude-code")
        self.assertTrue(denied(self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py", session="S9"))))
        active = json.loads((self.repo / ".ai-dev-workflow" / "ACTIVE").read_text(encoding="utf-8"))
        self.assertEqual(active["session"], "S9")

    def test_a_task_started_by_another_agent_is_ignored(self) -> None:
        self.new_task("--agent", "codex")
        self.assertEqual(self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py")), "")

    def test_broken_records_fail_closed_inside_an_active_task(self) -> None:
        self.new_task("--agent", "claude-code", "--session", "S1")
        (self.task / "state.json").write_text("{broken", encoding="utf-8")
        out = self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py"))
        self.assertTrue(denied(out))
        self.assertIn("could not validate", out)

    def test_optional_hook_log_records_decisions(self) -> None:
        import os
        from unittest import mock
        self.new_task("--agent", "claude-code", "--session", "S1")
        log = self.tmp / "hook.log"
        with mock.patch.dict(os.environ, {"AI_DEV_WORKFLOW_HOOK_LOG": str(log)}):
            self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py"))
            self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py", session="S2"))
        entries = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([e["decision"] for e in entries], ["deny", "allow"])
        self.assertEqual(entries[1]["why"], "other session")

    def test_prompt_hook_speaks_only_for_the_active_session(self) -> None:
        self.new_task("--agent", "claude-code", "--session", "S1")
        payload = {"session_id": "S1", "cwd": str(self.repo), "prompt": "hi"}
        self.assertIn("[AIDevWorkflow]", self.hook("claude-prompt", payload))
        self.assertEqual(self.hook("claude-prompt", dict(payload, session_id="S2")), "")
        self.wf("pause", "favorites")
        self.assertEqual(self.hook("claude-prompt", payload), "")

    def to_implementation_without_init(self) -> None:
        from helpers import FILLED_PLAN as plan, FILLED_SPEC as spec
        self.new_task()
        self.to_specification()
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", spec)
        self.review_spec()
        self.wf("stage", "favorites", "SPEC_APPROVAL")
        self.wf("approve", "favorites", "spec", "--evidence", "approve the spec")
        self.write(".ai-dev-workflow/tasks/favorites/plan.md", plan)
        self.wf("stage", "favorites", "PLAN_APPROVAL")
        self.wf("approve", "favorites", "plan", "--evidence", "approve the plan")


if __name__ == "__main__":
    unittest.main()
