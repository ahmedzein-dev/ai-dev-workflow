"""The 14 required workflow scenarios. Each test checks what the engine enforces; the instruction-level part
of each scenario (what the agent says or asks) is covered by SKILL.md and the references and was exercised in the
live agent tests recorded in docs/validation-report.md."""
from __future__ import annotations

import json
import unittest

from helpers import FILLED_AUDIT, FILLED_PLAN, FILLED_REPORT, FILLED_SPEC, PY, WorkflowTestCase

DEPS_HEADER = "| ID | Type | Class | Gate | Owner | Summary |\n|---|---|---|---|---|---|\n"


class Scenarios(WorkflowTestCase):
    def test_01_missing_specification_template(self) -> None:
        self.assertIn("never invent", self.wf("init", "--commit", "all", expect=1))
        self.init()
        (self.repo / ".ai-dev-workflow" / "templates" / "example-spec-template.md").unlink()
        self.assertIn("never invent",
                      self.wf("new", "favorites", "--title", "x", "--invocation", "/ai-dev-workflow x", expect=1))

    def test_02_new_feature_without_a_specification(self) -> None:
        self.init()
        self.new_task()
        self.assertEqual(self.state()["stage"], "DISCOVERY")
        self.assertIn("only in SPEC_APPROVAL", self.wf("approve", "favorites", "spec", "--evidence", "yes", expect=1))
        self.assertIn("code may change only", self.wf("preflight", "favorites", expect=1))

    def test_03_missing_ui_design(self) -> None:
        self.init()
        self.new_task()
        self.to_specification()
        self.write(".ai-dev-workflow/tasks/favorites/dependencies.md",
                   DEPS_HEADER + "| DEP-1 | ui | Blocking | spec | Design | Favorites screen design |\n")
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC)
        self.review_spec()
        self.assertIn("DEP-1", self.wf("stage", "favorites", "SPEC_APPROVAL", expect=1))
        self.assertIn("BLOCKED — Awaiting Favorites screen design", self.wf("status", "favorites"))

    def test_04_missing_backend_contract(self) -> None:
        self.init()
        self.new_task()
        self.wf("discover", "favorites", "--inspected", "app.py", "--summary", "needs an API")
        self.wf("stage", "favorites", "DEPENDENCIES")
        row = "| DEP-1 | backend | Blocking | spec | Backend developer | Favorites API contract |\n"
        self.write(".ai-dev-workflow/tasks/favorites/dependencies.md", DEPS_HEADER + row)
        self.assertIn("Message to send", self.wf("stage", "favorites", "SPECIFICATION", expect=1))
        message = "\n### DEP-1 — Favorites API\n\n**Message to send:**\n```text\nWhich endpoint lists favorites?\n```\n"
        self.write(".ai-dev-workflow/tasks/favorites/dependencies.md", DEPS_HEADER + row + message)
        self.wf("stage", "favorites", "SPECIFICATION")
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC)
        self.review_spec()
        self.assertIn("still blocks the spec", self.wf("stage", "favorites", "SPEC_APPROVAL", expect=1))
        resolved = row.replace("Blocking | spec", "Verified | -")
        self.write(".ai-dev-workflow/tasks/favorites/dependencies.md", DEPS_HEADER + resolved + message)
        self.wf("stage", "favorites", "SPEC_APPROVAL")

    def test_05_ambiguous_requirements(self) -> None:
        self.init()
        self.new_task()
        self.to_specification()
        self.write(".ai-dev-workflow/tasks/favorites/spec.md",
                   FILLED_SPEC.replace("newest first.", "newest first and works correctly. TBD: sorting"))
        self.review_spec_expecting_failure()
        result = json.loads(self.wf("spec-check", "favorites", "--json", expect=1))
        self.assertIn("M-unresolved", {m["rule"] for m in result["mandatory"]})
        self.assertIn("J1:REQ-2:works correctly", [f["id"] for f in result["flags"]])

    def test_06_specification_not_approved(self) -> None:
        self.init()
        self.new_task("--agent", "claude-code", "--session", "S1")
        self.to_specification()
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC)
        self.review_spec()
        self.wf("stage", "favorites", "SPEC_APPROVAL")
        self.assertIn("approve <task> spec", self.wf("stage", "favorites", "PLANNING", expect=1))
        self.assertIn('"deny"', self.hook("claude-pre-edit", self.edit_payload(self.repo / "app.py")))

    def test_07_plan_not_approved(self) -> None:
        self.init()
        self.new_task()
        self.to_specification()
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC)
        self.review_spec()
        self.wf("stage", "favorites", "SPEC_APPROVAL")
        self.wf("approve", "favorites", "spec", "--evidence", "approve the spec")
        self.write(".ai-dev-workflow/tasks/favorites/plan.md", FILLED_PLAN)
        self.wf("stage", "favorites", "PLAN_APPROVAL")
        self.assertIn("approve <task> plan", self.wf("stage", "favorites", "IMPLEMENTATION", expect=1))
        self.assertIn("code may change only", self.wf("preflight", "favorites", expect=1))

    def test_08_approved_plan_allows_controlled_implementation(self) -> None:
        self.to_implementation()
        self.wf("preflight", "favorites")
        self.write("app.py", "FAVORITES = set()\n")
        self.assertIn("1/1 steps done", self.wf("step", "favorites", "S1", "done"))

    def test_09_failing_tests(self) -> None:
        self.init(checks=[{"id": "unit", "command": f'"{PY}" -c "import sys; sys.exit(1)"', "required": True}])
        self.new_task()
        self._through_approvals()
        self.wf("preflight", "favorites")
        self.write("app.py", "FAVORITES = set()\n")
        self.wf("step", "favorites", "S1", "done")
        self.wf("stage", "favorites", "TESTING")
        self.wf("run", "favorites", "unit", expect=1)
        self.assertIn("move to FIXING", self.wf("stage", "favorites", "AUDIT", expect=1))
        self.assertEqual(json.loads(self.wf("outcome", "favorites", "--json"))["max"], "Partially Completed")

    def test_10_audit_findings(self) -> None:
        self.to_implementation()
        self.implement_and_test()
        self.wf("stage", "favorites", "AUDIT")
        header = ("| ID | Severity | Dimension | Finding | Location | Disposition | Notes |\n"
                  "|---|---|---|---|---|---|---|\n")
        self.write(".ai-dev-workflow/tasks/favorites/audit.md",
                   FILLED_AUDIT.format(findings=header + "| F-1 | Important | C | Duplicated logic | app.py | Open | |\n"))
        self.assertIn("still Open", self.wf("stage", "favorites", "FINAL_REPORT", expect=1))
        self.wf("stage", "favorites", "FIXING", "--reason", "F-1 duplicated logic")
        self.wf("preflight", "favorites")
        self.write("app.py", "FAVORITES = set()  # deduplicated\n")
        self.wf("step", "favorites", "S1", "done")
        self.wf("stage", "favorites", "TESTING", "--reason", "re-test after fixing F-1")
        self.wf("run", "favorites", "unit")
        self.wf("stage", "favorites", "AUDIT")
        self.write(".ai-dev-workflow/tasks/favorites/audit.md",
                   FILLED_AUDIT.format(findings=header + "| F-1 | Important | C | Duplicated logic | app.py | Fixed | re-ran unit |\n"))
        self.wf("stage", "favorites", "FINAL_REPORT")
        self.assertEqual(json.loads(self.wf("outcome", "favorites", "--json"))["max"], "Completed")

    def test_11_a_different_agent_resumes_the_task(self) -> None:
        self.to_implementation()
        out = self.wf("resume", "favorites", "--agent", "codex")
        self.assertIn("IMPLEMENTATION", out)
        self.assertIn("run `workflow.py preflight`", out)
        self.wf("preflight", "favorites", "--agent", "codex")
        agents = {h["agent"] for h in self.state()["history"]}
        self.assertTrue({"test-agent", "codex"} <= agents)

    def test_12_changed_specification_after_approval(self) -> None:
        self.to_implementation()
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC.replace("newest first", "oldest first"))
        self.assertIn("spec.md changed after v1 was approved", self.wf("preflight", "favorites", expect=1))
        self.assertIn("renewed approval", self.wf("check", expect=1))

    def test_13_conflicting_project_instructions(self) -> None:
        self.init()
        self.assertTrue((self.repo / ".ai-dev-workflow" / "PROJECT.md").exists())
        self.new_task()
        self.wf("decision", "favorites", "--text", "Navigation: use the router helper, not the raw API",
                "--evidence", "user: go with the router helper")
        self.assertEqual(len(self.state()["decisions"]), 1)

    def test_14_existing_unrelated_git_changes(self) -> None:
        self.write("notes.txt", "someone's unfinished work\n")
        self.to_implementation()
        scope = json.loads(self.wf("scope", "favorites", "--json"))
        self.assertNotIn("notes.txt", scope["task_changes"])
        self.assertIn("notes.txt", scope["preexisting_untouched"])

    # helpers -----------------------------------------------------------------------
    def review_spec_expecting_failure(self) -> None:
        self.wf("review", "favorites", "--map", "REQ-1=AC-1", "--map", "REQ-2=DW-2")
        self.assertIn("still has open flags", self.wf("review", "favorites", "--pass", "J1", expect=1))

    def _through_approvals(self) -> None:
        self.to_specification()
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC)
        self.review_spec()
        self.wf("stage", "favorites", "SPEC_APPROVAL")
        self.wf("approve", "favorites", "spec", "--evidence", "approve the spec")
        self.write(".ai-dev-workflow/tasks/favorites/plan.md", FILLED_PLAN)
        self.wf("stage", "favorites", "PLAN_APPROVAL")
        self.wf("approve", "favorites", "plan", "--evidence", "approve the plan")


if __name__ == "__main__":
    unittest.main()
