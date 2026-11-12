"""Verification evidence (freshness, analyzer baselines) and the final-status caps."""
from __future__ import annotations

import json
import unittest
from unittest import mock

from helpers import FILLED_AUDIT, FILLED_REPORT, PY, WorkflowTestCase, git
from workflow import decode_command_output, parse_analyzer

FINDINGS_HEADER = ("| ID | Severity | Dimension | Finding | Location | Disposition | Notes |\n"
                   "|----|----------|-----------|---------|----------|-------------|-------|\n")


class EvidenceTest(WorkflowTestCase):
    def test_analyzer_accepts_windows_replacement_separators(self) -> None:
        issues, counts = parse_analyzer("   info ? Style hint ? lib/a.dart:3:3 ? style\n")
        self.assertEqual(counts, {"error": 0, "warning": 0, "info": 1})
        self.assertEqual(issues[0]["code"], "style")

    def test_analyzer_decodes_windows_code_page_output(self) -> None:
        output = "   info • Style hint • lib/a.dart:3:3 • style\n"
        with mock.patch("workflow.locale.getpreferredencoding", return_value="cp1252"):
            decoded = decode_command_output(output.encode("cp1252"))
        issues, counts = parse_analyzer(decoded)
        self.assertEqual(counts, {"error": 0, "warning": 0, "info": 1})
        self.assertEqual(issues[0]["code"], "style")

    def test_evidence_goes_stale_when_code_changes_but_not_when_it_is_committed(self) -> None:
        self.to_implementation()
        self.implement_and_test()
        git(self.repo, "add", "app.py")
        git(self.repo, "commit", "-q", "-m", "favorites")
        self.wf("stage", "favorites", "AUDIT")
        self.write("app.py", "FAVORITES = set()\nprint('changed after testing')\n")
        self.assertIn("ran on older code", self.wf("outcome", "favorites"))

    def test_a_failed_required_check_blocks_the_audit(self) -> None:
        self.init(checks=[{"id": "unit", "command": f'"{PY}" -c "import sys; sys.exit(3)"', "required": True}])
        self._advance_to_testing()
        self.wf("run", "favorites", "unit", expect=1)
        self.assertIn("failed; move to FIXING", self.wf("stage", "favorites", "AUDIT", expect=1))

    def test_blocked_and_not_applicable_checks(self) -> None:
        self.init(checks=[
            {"id": "unit", "command": f'"{PY}" -c "print(1)"', "required": True},
            {"id": "device", "command": "device-test", "required": True},
            {"id": "codegen", "command": "codegen", "required": True, "when": "models change"}])
        self._advance_to_testing()
        self.assertIn("always required", self.wf("run", "favorites", "device", "--not-applicable", "x", expect=1))
        self.wf("run", "favorites", "device", "--blocked", "no physical device here")
        self.wf("run", "favorites", "codegen", "--not-applicable", "no models changed")
        self.wf("run", "favorites", "unit")
        out = json.loads(self.wf("outcome", "favorites", "--json"))
        self.assertIn("could not run: no physical device here", " ".join(out["reasons"]))

    def test_missing_command_is_recorded_as_blocked(self) -> None:
        self.init(checks=[{"id": "unit", "command": "definitely-not-a-real-command-xyz", "required": True}])
        self._advance_to_testing()
        self.assertIn("blocked", self.wf("run", "favorites", "unit", expect=1))

    def test_analyzer_counts_by_severity_and_separates_preexisting_issues(self) -> None:
        self.write("analyzer.py", "import sys\nprint(open('issues.txt').read())\nsys.exit(1 if open('issues.txt').read().strip() else 0)\n")
        self.write("issues.txt", "warning • Old problem • lib/a.dart:1:1 • old_code\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "analyzer fixture")
        self.init(checks=[{"id": "analyze", "command": f'"{PY}" analyzer.py', "parser": "dart-analyzer",
                           "fail_on": ["error", "warning", "new"], "required": True}])
        self._advance_to_implementation()
        self.wf("run", "favorites", "analyze", "--baseline")
        self.write("issues.txt", "warning • Old problem • lib/a.dart:1:1 • old_code\n"
                                 "warning • New problem • lib/b.dart:2:2 • new_code\n")
        self.assertIn("failed", self.wf("run", "favorites", "analyze", expect=1))
        self.write("issues.txt", "warning • Old problem • lib/a.dart:1:1 • old_code\n")
        self.assertIn("preexisting", self.wf("run", "favorites", "analyze"))
        self.write("issues.txt", "   info • Style hint • lib/a.dart:3:3 • style\n"
                                 "warning • Old problem • lib/a.dart:1:1 • old_code\n")
        self.assertIn("failed", self.wf("run", "favorites", "analyze", expect=1))

    def test_infos_alone_do_not_fail_when_only_errors_and_warnings_count(self) -> None:
        self.write("analyzer.py", "import sys\nprint('   info • Style hint • lib/a.dart:3:3 • style')\nsys.exit(1)\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "fixture")
        self.init(checks=[{"id": "analyze", "command": f'"{PY}" analyzer.py', "parser": "dart-analyzer",
                           "fail_on": ["error", "warning"], "required": True}])
        self._advance_to_testing()
        self.assertIn("passed", self.wf("run", "favorites", "analyze"))

    def test_baseline_refused_after_code_changed(self) -> None:
        self.init(checks=[{"id": "analyze", "command": f'"{PY}" -c "print(1)"', "parser": "dart-analyzer", "required": True}])
        self._advance_to_implementation()
        self.write("app.py", "changed\n")
        self.assertIn("would hide new", self.wf("run", "favorites", "analyze", "--baseline", expect=1))

    def test_output_is_redacted_before_it_is_stored(self) -> None:
        self.write("leak.py", "print('api_key=' + 'abcdef0123456789xyz')\n")
        git(self.repo, "add", "leak.py")
        git(self.repo, "commit", "-q", "-m", "fixture")
        self.init(checks=[{"id": "unit", "required": True, "command": f'"{PY}" leak.py'}])
        self._advance_to_testing()
        self.wf("run", "favorites", "unit")
        summary = self.state()["checks"][-1]["summary"]
        self.assertIn("[REDACTED]", summary)
        self.assertNotIn("abcdef0123456789xyz", (self.task / "state.json").read_text(encoding="utf-8"))

    def _advance_to_implementation(self) -> None:
        from helpers import FILLED_PLAN, FILLED_SPEC
        self.new_task()
        self.to_specification()
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC)
        self.review_spec()
        self.wf("stage", "favorites", "SPEC_APPROVAL")
        self.wf("approve", "favorites", "spec", "--evidence", "approve the spec")
        self.write(".ai-dev-workflow/tasks/favorites/plan.md", FILLED_PLAN)
        self.wf("stage", "favorites", "PLAN_APPROVAL")
        self.wf("approve", "favorites", "plan", "--evidence", "approve the plan")

    def _advance_to_testing(self) -> None:
        self._advance_to_implementation()
        self.wf("preflight", "favorites")
        self.write("app.py", "FAVORITES = set()\n")
        self.wf("step", "favorites", "S1", "done")
        self.wf("stage", "favorites", "TESTING")


class OutcomeTest(WorkflowTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.to_implementation()
        self.implement_and_test()
        self.wf("stage", "favorites", "AUDIT")

    def audit(self, rows: str) -> None:
        self.write(".ai-dev-workflow/tasks/favorites/audit.md", FILLED_AUDIT.format(findings=FINDINGS_HEADER + rows))

    def report(self, status: str) -> None:
        self.write(".ai-dev-workflow/tasks/favorites/report.md", FILLED_REPORT.format(status=status))

    def outcome(self) -> dict:
        return json.loads(self.wf("outcome", "favorites", "--json"))

    def test_open_findings_block_the_final_report(self) -> None:
        self.audit("| F-1 | Minor | C | Naming | app.py | Open | |\n")
        self.assertIn("still Open", self.wf("stage", "favorites", "FINAL_REPORT", expect=1))

    def test_only_minor_findings_can_be_deferred(self) -> None:
        self.audit("| F-1 | Important | B | Layer leak | app.py | Deferred | later |\n")
        self.assertIn("only Minor", self.wf("stage", "favorites", "FINAL_REPORT", expect=1))

    def test_accepted_findings_need_the_users_words(self) -> None:
        self.audit("| F-1 | Important | B | Layer leak | app.py | Accepted | |\n")
        self.assertIn("user's words", self.wf("stage", "favorites", "FINAL_REPORT", expect=1))

    def test_accepted_critical_finding_never_yields_completed(self) -> None:
        self.audit('| F-1 | Critical | D | Token logged | app.py | Accepted | "ship it, we fix it next sprint" |\n')
        self.wf("stage", "favorites", "FINAL_REPORT")
        result = self.outcome()
        self.assertEqual(result["max"], "Partially Completed")
        self.report("Completed")
        self.assertIn("allows at most 'Partially Completed'", self.wf("close", "favorites", expect=1))
        self.report("Completed with Limitations")
        self.wf("close", "favorites", expect=1)
        self.report("Partially Completed")
        self.wf("close", "favorites")

    def test_accepted_important_finding_caps_at_limitations(self) -> None:
        self.audit('| F-1 | Important | C | Duplicate helper | app.py | Accepted | "fine for now" |\n')
        self.wf("stage", "favorites", "FINAL_REPORT")
        self.assertEqual(self.outcome()["max"], "Completed with Limitations")
        self.report("Completed")
        self.wf("close", "favorites", expect=1)
        self.report("Completed with Limitations")
        self.wf("close", "favorites")

    def test_fixed_findings_and_minor_deferrals_allow_completed(self) -> None:
        self.audit("| F-1 | Critical | D | Token logged | app.py | Fixed | re-ran unit |\n"
                   "| F-2 | Minor | C | Naming | app.py | Deferred | cosmetic |\n")
        self.wf("stage", "favorites", "FINAL_REPORT")
        self.assertEqual(self.outcome()["max"], "Completed")

    def test_unverified_items_cap_at_limitations(self) -> None:
        path = self.task / "verification.md"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "| EC-1 | Passed | unit check `unit` |", "| EC-1 | Not Verified | needs a real network drop; no device |"),
            encoding="utf-8")
        self.audit("")
        self.write(".ai-dev-workflow/tasks/favorites/audit.md", FILLED_AUDIT.format(findings="No findings."))
        self.wf("stage", "favorites", "FINAL_REPORT")
        result = self.outcome()
        self.assertEqual(result["max"], "Completed with Limitations")
        self.assertIn("EC-1 is Not Verified", " ".join(result["reasons"]))

    def test_open_blocking_dependency_allows_blocked(self) -> None:
        self.write(".ai-dev-workflow/tasks/favorites/dependencies.md",
                   "| ID | Type | Class | Gate | Owner | Summary |\n|---|---|---|---|---|---|\n"
                   "| DEP-1 | environment | Blocking | completion | DevOps | Production feature flag |\n")
        self.write(".ai-dev-workflow/tasks/favorites/audit.md", FILLED_AUDIT.format(findings="No findings."))
        self.wf("stage", "favorites", "FINAL_REPORT")
        result = self.outcome()
        self.assertTrue(result["blocked"])
        self.assertIn("Blocked", result["allowed"])
        self.assertNotIn("Completed", result["allowed"])


if __name__ == "__main__":
    unittest.main()
