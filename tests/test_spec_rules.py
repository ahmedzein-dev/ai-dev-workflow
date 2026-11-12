"""Specification validation: mandatory rules block, judgment rules need a review, advisory rules only warn."""
from __future__ import annotations

import json
import unittest

from helpers import EXAMPLE_TEMPLATE, FILLED_SPEC, WorkflowTestCase

SPEC = ".ai-dev-workflow/tasks/favorites/spec.md"


class SpecRulesTest(WorkflowTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.init()
        self.new_task()
        self.to_specification()

    def check(self, spec: str | None = None) -> dict:
        if spec is not None:
            self.write(SPEC, spec)
        return json.loads(self.wf("spec-check", "favorites", "--json", expect=None))

    def rules(self, result: dict) -> set:
        return {m["rule"] for m in result["mandatory"]}

    def test_blank_template_fails_on_placeholders_and_missing_content(self) -> None:
        result = self.check()
        self.assertTrue({"M-placeholder", "M-content"} <= self.rules(result))
        self.assertFalse(result["ready"])

    def test_filled_spec_passes_every_mandatory_rule(self) -> None:
        self.assertEqual(self.check(FILLED_SPEC)["mandatory"], [])

    def test_no_numeric_limits_on_requirements_edge_cases_exclusions_or_criteria(self) -> None:
        many = "\n".join(f"- **REQ-{n}:** Behavior number {n} is shown on the screen." for n in range(1, 16))
        spec = FILLED_SPEC.replace(
            "- **REQ-1:** A heart button on each item toggles whether the item is saved.\n"
            "- **REQ-2:** The favorites screen lists saved items, newest first.", many)
        result = self.check(spec)
        self.assertEqual(result["mandatory"], [])
        messages = " ".join(w["message"] for w in result["advisory"]).lower()
        for phrase in ("split", "at least", "more than", "fewer than", "maximum", "minimum"):
            self.assertNotIn(phrase, messages)
        single = FILLED_SPEC.replace("- **REQ-2:** The favorites screen lists saved items, newest first.\n", "")
        self.assertEqual(self.check(single)["mandatory"], [])

    def test_none_with_a_reason_is_allowed_only_where_the_rules_permit_it(self) -> None:
        none_reason = FILLED_SPEC.replace("- Sharing favorites with other users", "- None — nothing is excluded")
        result = self.check(none_reason)
        self.assertEqual(result["mandatory"], [])
        self.assertIn("A2", {w["rule"] for w in result["advisory"]})
        bare = FILLED_SPEC.replace("- Sharing favorites with other users", "- None")
        self.assertIn("without a reason", json.dumps(self.check(bare)["mandatory"]))
        empty = FILLED_SPEC.replace("- Sharing favorites with other users\n", "")
        self.assertIn("has no content", json.dumps(self.check(empty)["mandatory"]))

    def test_requirements_must_describe_real_behavior(self) -> None:
        spec = FILLED_SPEC.replace(
            "- **REQ-1:** A heart button on each item toggles whether the item is saved.\n"
            "- **REQ-2:** The favorites screen lists saved items, newest first.", "- **REQ-1:** None — not needed")
        self.assertIn("cannot be None", json.dumps(self.check(spec)["mandatory"]))

    def test_ids_must_be_unique_and_without_gaps(self) -> None:
        duplicate = FILLED_SPEC.replace("**REQ-2:**", "**REQ-1:**")
        self.assertIn("M-ids", self.rules(self.check(duplicate)))
        gap = FILLED_SPEC.replace("**REQ-2:**", "**REQ-3:**")
        self.assertIn("M-ids", self.rules(self.check(gap)))

    def test_acceptance_criteria_must_be_given_when_then(self) -> None:
        spec = FILLED_SPEC.replace(
            "Given a signed-in user, when they tap an empty heart, then the item appears first in favorites.",
            "The item appears first in favorites.")
        self.assertIn("M-ac-form", self.rules(self.check(spec)))

    def test_edge_case_rows_need_a_specific_behavior(self) -> None:
        spec = FILLED_SPEC.replace('The heart reverts and "No connection" appears with Retry.', " ")
        self.assertIn("M-edge-cases", self.rules(self.check(spec)))

    def test_unresolved_markers_block_but_ordinary_words_do_not(self) -> None:
        self.assertIn("M-unresolved", self.rules(self.check(FILLED_SPEC + "\nTBD: confirm sorting\n")))
        self.assertEqual(self.check(FILLED_SPEC.replace("Sharing favorites", "Sharing a todo list"))["mandatory"], [])

    def test_vague_wording_is_flagged_until_fixed_or_dismissed(self) -> None:
        spec = FILLED_SPEC.replace("newest first.", "newest first and loads fast.")
        result = self.check(spec)
        flag_ids = [f["id"] for f in result["flags"]]
        self.assertIn("J1:REQ-2:fast", flag_ids)
        self.assertIn("still has open flags", self.wf("review", "favorites", "--pass", "J1", expect=1))
        self.wf("review", "favorites", "--dismiss", "J1:REQ-2:fast", "the user defined fast as under 300 ms in REQ-2's test")
        self.wf("review", "favorites", "--pass", "J1")

    def test_coverage_flags_cannot_be_dismissed_only_resolved(self) -> None:
        self.write(SPEC, FILLED_SPEC)
        self.assertIn("cannot be dismissed",
                      self.wf("review", "favorites", "--dismiss", "J4:REQ-1:unmapped", "covered elsewhere", expect=1))
        self.assertIn("not an ID", self.wf("review", "favorites", "--map", "REQ-1=AC-9", expect=1))
        self.wf("review", "favorites", "--map", "REQ-1=AC-1", "--map", "REQ-2=DW-2")
        self.assertNotIn("J4", {f["rule"] for f in self.check()["flags"]})

    def test_structure_proposals_need_a_recorded_basis(self) -> None:
        self.write(SPEC, FILLED_SPEC)
        self.assertIn("explaining the basis", self.wf("review", "favorites", "--pass", "J3", expect=1))
        self.wf("review", "favorites", "--pass", "J3", "--note", "J3=Follows the existing app.py module layout.")

    def test_review_must_be_redone_after_the_spec_changes(self) -> None:
        self.write(SPEC, FILLED_SPEC)
        self.review_spec()
        self.assertTrue(self.check()["ready"])
        result = self.check(FILLED_SPEC.replace("newest first", "most recent first"))
        self.assertFalse(result["ready"])
        self.assertEqual({j["status"] for j in result["judgment"].values()}, {"pending"})

    def test_advisory_questions_warn_but_never_block(self) -> None:
        self.write(SPEC, FILLED_SPEC)
        self.review_spec()
        result = self.check()
        self.assertTrue(result["advisory"])
        self.assertTrue(result["ready"])
        self.wf("review", "favorites", "--question", "offline=EC-1", "--question", "concurrent=n/a:single-user data")
        self.assertIn("--question", self.wf("review", "favorites", "--question", "offline=maybe", expect=1))

    def test_verification_items_cover_criteria_edge_cases_and_checklist(self) -> None:
        self.assertEqual(self.check(FILLED_SPEC)["verification_items"], ["AC-1", "EC-1", "DW-1", "DW-2"])


class StructureOnlyTest(WorkflowTestCase):
    def test_template_without_rules_checks_structure_and_placeholders_only(self) -> None:
        self.wf("init", "--template", str(EXAMPLE_TEMPLATE), "--commit", "all", "--no-rules", "--config",
                str(self._config()))
        self.new_task()
        self.to_specification()
        blank = json.loads(self.wf("spec-check", "favorites", "--json", expect=None))
        self.assertIn("M-placeholder", {m["rule"] for m in blank["mandatory"]})
        self.write(SPEC, FILLED_SPEC)
        result = json.loads(self.wf("spec-check", "favorites", "--json"))
        self.assertEqual((result["mandatory"], result["judgment"], result["ready"]), ([], {}, True))

    def test_missing_template_heading_is_reported(self) -> None:
        self.wf("init", "--template", str(EXAMPLE_TEMPLATE), "--commit", "all", "--no-rules", "--config",
                str(self._config()))
        self.new_task()
        self.to_specification()
        self.write(SPEC, FILLED_SPEC.replace("## Constraints", "## Limits"))
        result = json.loads(self.wf("spec-check", "favorites", "--json", expect=1))
        self.assertIn("'## Constraints' is missing", json.dumps(result["mandatory"]))

    def _config(self):
        path = self.tmp / "empty.json"
        path.write_text(json.dumps({"checks": []}), encoding="utf-8")
        return path


if __name__ == "__main__":
    unittest.main()
