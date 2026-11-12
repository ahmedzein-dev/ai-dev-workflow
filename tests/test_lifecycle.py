"""The 11-stage lifecycle end to end, plus the gates between stages."""
from __future__ import annotations

import os
import unittest

from helpers import FILLED_AUDIT, FILLED_PLAN, FILLED_REPORT, FILLED_SPEC, WorkflowTestCase


class HappyPathTest(WorkflowTestCase):
    def test_full_lifecycle_closes_as_completed(self) -> None:
        self.to_implementation()
        self.assertEqual(self.state()["stage"], "IMPLEMENTATION")
        self.implement_and_test()
        self.wf("stage", "favorites", "AUDIT")
        self.write(".ai-dev-workflow/tasks/favorites/audit.md", FILLED_AUDIT.format(findings="No findings."))
        self.wf("stage", "favorites", "FINAL_REPORT")
        self.assertIn("Highest status the evidence allows: Completed", self.wf("outcome", "favorites"))
        self.write(".ai-dev-workflow/tasks/favorites/report.md", FILLED_REPORT.format(status="Completed"))
        self.wf("close", "favorites")
        state = self.state()
        self.assertEqual((state["status"], state["outcome"]), ("closed", "Completed"))
        self.assertFalse((self.repo / ".ai-dev-workflow" / "ACTIVE").exists())
        self.wf("check")

    def test_stages_follow_the_agreed_order(self) -> None:
        from workflow import STAGES
        self.assertEqual(STAGES, [
            "DISCOVERY", "DEPENDENCIES", "SPECIFICATION", "SPEC_APPROVAL", "PLANNING", "PLAN_APPROVAL",
            "IMPLEMENTATION", "TESTING", "FIXING", "AUDIT", "FINAL_REPORT"])


class GateTest(WorkflowTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.init()
        self.new_task()

    def test_discovery_needs_inspected_files_and_summary(self) -> None:
        out = self.wf("stage", "favorites", "DEPENDENCIES", expect=1)
        self.assertIn("inspected", out)
        self.wf("discover", "favorites", "--inspected", "app.py", "--summary", "Scope noted.")
        self.wf("stage", "favorites", "DEPENDENCIES")

    def test_dependencies_must_be_classified(self) -> None:
        self.wf("discover", "favorites", "--inspected", "app.py", "--summary", "Scope noted.")
        self.wf("stage", "favorites", "DEPENDENCIES")
        self.assertIn("Classify dependencies", self.wf("stage", "favorites", "SPECIFICATION", expect=1))

    def test_blocking_backend_dependency_needs_a_message_and_blocks_the_spec(self) -> None:
        self.wf("discover", "favorites", "--inspected", "app.py", "--summary", "Scope noted.")
        self.wf("stage", "favorites", "DEPENDENCIES")
        table = ("| ID | Type | Class | Gate | Owner | Summary |\n|---|---|---|---|---|---|\n"
                 "| DEP-1 | backend | Blocking | spec | Backend developer | Favorites API contract |\n")
        self.write(".ai-dev-workflow/tasks/favorites/dependencies.md", "# Dependencies\n\n" + table)
        self.assertIn("Message to send", self.wf("stage", "favorites", "SPECIFICATION", expect=1))
        details = ("\n### DEP-1 — Favorites API\n\n**Message to send:**\n```text\nHi, which endpoint lists favorites?\n```\n"
                   "**Answer received:** Waiting.\n")
        self.write(".ai-dev-workflow/tasks/favorites/dependencies.md", "# Dependencies\n\n" + table + details)
        self.wf("stage", "favorites", "SPECIFICATION")
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC)
        self.review_spec()
        out = self.wf("stage", "favorites", "SPEC_APPROVAL", expect=1)
        self.assertIn("DEP-1", out)
        self.assertIn("BLOCKED — Awaiting Favorites API contract", self.wf("status", "favorites"))

    def test_approval_requires_the_review_stage_and_real_evidence(self) -> None:
        self.to_specification()
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC)
        self.assertIn("only in SPEC_APPROVAL", self.wf("approve", "favorites", "spec", "--evidence", "ok", expect=1))
        self.review_spec()
        self.wf("stage", "favorites", "SPEC_APPROVAL")
        self.assertIn("own words", self.wf("approve", "favorites", "spec", "--evidence", " ", expect=1))

    def test_planning_and_implementation_start_only_through_approval(self) -> None:
        self.to_specification()
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC)
        self.review_spec()
        self.wf("stage", "favorites", "SPEC_APPROVAL")
        self.assertIn("approve <task> spec", self.wf("stage", "favorites", "PLANNING", expect=1))

    def test_moving_back_needs_a_reason(self) -> None:
        self.to_specification()
        self.assertIn("--reason", self.wf("stage", "favorites", "DISCOVERY", expect=1))
        self.wf("stage", "favorites", "DISCOVERY", "--reason", "scope changed")
        self.assertEqual(self.state()["stage"], "DISCOVERY")

    def test_skipping_stages_is_refused(self) -> None:
        self.assertIn("next stage is DEPENDENCIES", self.wf("stage", "favorites", "SPECIFICATION", expect=1))

    def test_explicit_user_override_is_recorded_without_fabricating_gates(self) -> None:
        request = "skip the spec and plan approval; write the code now"
        reason = f"User explicitly requested: {request}; skipped specification and plan approval"
        self.wf("pause", "favorites", "--reason", reason)
        state = self.state()
        self.assertEqual((state["status"], state["stage"], state["outcome"]),
                         ("paused", "DISCOVERY", None))
        self.assertEqual(state["approvals"], {})
        self.assertEqual(state["history"][-1]["reason"], reason)
        self.assertIn("PAUSED — DISCOVERY", self.wf("status", "favorites"))
        self.assertIn("only in SPEC_APPROVAL", self.wf("approve", "favorites", "spec", "--evidence", request,
                                                       expect=1))
        self.assertIn("DISCOVERY", self.wf("close", "favorites", expect=1))
        self.write("app.py", "print('requested override')\n")
        self.assertIn("before any implementation was approved", self.wf("status", "favorites"))
        self.assertEqual(self.state()["approvals"], {})

    def test_early_final_report_needs_a_reason(self) -> None:
        self.assertIn("--reason", self.wf("stage", "favorites", "FINAL_REPORT", expect=1))
        self.wf("stage", "favorites", "FINAL_REPORT", "--reason", "backend contract will not arrive this sprint")


class ImmutabilityTest(WorkflowTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.to_implementation()

    def test_snapshots_are_written_and_read_only(self) -> None:
        state = self.state()
        for doc in ("spec", "plan"):
            snapshot = self.task / state["approvals"][doc]["snapshot"]
            self.assertTrue(snapshot.exists())
            self.assertFalse(os.access(snapshot, os.W_OK) and os.name != "nt")
        self.assertEqual(state["approvals"]["plan"]["spec_sha256"], state["approvals"]["spec"]["sha256"])
        self.assertEqual(state["approvals"]["spec"]["evidence"], "Approve spec v1")

    def test_progress_does_not_touch_the_plan_or_its_approval(self) -> None:
        before = (self.task / "plan.md").read_text(encoding="utf-8")
        self.wf("preflight", "favorites")
        self.write("app.py", "FAVORITES = set()\n")
        self.wf("step", "favorites", "S1", "done")
        self.assertEqual((self.task / "plan.md").read_text(encoding="utf-8"), before)
        self.assertEqual(self.state()["progress"]["S1"]["files"], ["app.py"])
        self.wf("preflight", "favorites")

    def test_any_plan_change_invalidates_the_approval(self) -> None:
        self.write(".ai-dev-workflow/tasks/favorites/plan.md", FILLED_PLAN.replace("Users can", "People can"))
        out = self.wf("preflight", "favorites", expect=1)
        self.assertIn("plan.md changed after v1 was approved", out)
        self.assertIn("ERROR", self.wf("check", expect=1))
        self.write(".ai-dev-workflow/tasks/favorites/plan.md", FILLED_PLAN)
        self.wf("preflight", "favorites")

    def test_a_new_spec_version_invalidates_the_plan_approval_too(self) -> None:
        self.wf("stage", "favorites", "SPECIFICATION", "--reason", "user asked for sorting options")
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC.replace("newest first", "newest first by default"))
        self.review_spec()
        self.wf("stage", "favorites", "SPEC_APPROVAL")
        self.wf("approve", "favorites", "spec", "--evidence", "approve spec v2")
        state = self.state()
        self.assertEqual(state["approvals"]["spec"]["version"], 2)
        self.assertEqual(state["stage"], "PLANNING")
        ok, message = __import__("workflow").approval_status(self.repo, state, "plan")
        self.assertFalse(ok)
        self.assertIn("older spec version", message)

    def test_line_endings_do_not_change_the_hash(self) -> None:
        path = self.task / "plan.md"
        path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        self.wf("preflight", "favorites")


if __name__ == "__main__":
    unittest.main()
