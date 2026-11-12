"""Explicit start, secrets, commit modes, templates and pre-existing work."""
from __future__ import annotations

import io
import json
import contextlib
import unittest

from helpers import EXAMPLE_TEMPLATE, FILLED_SPEC, WorkflowTestCase, git

import install  # noqa: E402  (scripts folder is on sys.path via helpers)


class ExplicitStartTest(WorkflowTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.init()

    def test_an_ordinary_request_creates_nothing(self) -> None:
        out = self.wf("new", "login", "--title", "Login", "--invocation", "please implement a login screen", expect=1)
        self.assertIn("explicitly starts AIDevWorkflow", out)
        self.assertFalse((self.repo / ".ai-dev-workflow" / "tasks").exists())

    def test_invocations_that_name_the_skill_are_accepted(self) -> None:
        for slug, text in (("one", "/ai-dev-workflow add login"), ("two", "$ai-dev-workflow add login"),
                           ("three", "Use AIDevWorkflow for the login screen")):
            self.wf("new", slug, "--title", slug, "--invocation", text)
        self.assertEqual(sorted(p.name for p in (self.repo / ".ai-dev-workflow" / "tasks").iterdir()),
                         ["one", "three", "two"])

    def test_starting_another_task_pauses_the_previous_one(self) -> None:
        self.new_task()
        self.wf("new", "second", "--title", "Second", "--invocation", "/ai-dev-workflow second")
        self.assertEqual(self.state()["status"], "paused")
        active = json.loads((self.repo / ".ai-dev-workflow" / "ACTIVE").read_text(encoding="utf-8"))
        self.assertEqual(active["task"], "second")


class SecretsTest(WorkflowTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.init()
        self.new_task()
        self.to_specification()

    def test_secrets_are_refused_in_evidence_and_decisions(self) -> None:
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC)
        self.review_spec()
        self.wf("stage", "favorites", "SPEC_APPROVAL")
        token = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"
        self.assertIn("secret", self.wf("approve", "favorites", "spec", "--evidence", f"approved {token}", expect=1))
        self.assertIn("secret", self.wf("decision", "favorites", "--text", "use pass" + "word: hunter2hunter2",
                                        "--evidence", "ok", expect=1))

    def test_secrets_written_into_records_are_detected(self) -> None:
        self.write(".ai-dev-workflow/tasks/favorites/spec.md", FILLED_SPEC + "\nAWS key " + "AKIA" + "ABCDEFGHIJKLMNOP" + "\n")
        self.assertIn("AWS access key", self.wf("check", expect=1))

    def test_placeholders_are_not_mistaken_for_secrets(self) -> None:
        from workflow import find_secrets
        self.assertEqual(find_secrets("api_key: <your key>\npassword=${DB_PASSWORD}\ntoken: xxxxxxxx"), [])


class CommitModeTest(WorkflowTestCase):
    def exclude(self) -> str:
        path = self.repo / ".git" / "info" / "exclude"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def test_modes_use_the_local_exclude_file_only(self) -> None:
        self.init(commit="config-only")
        self.assertIn("/.ai-dev-workflow/tasks/", self.exclude())
        self.new_task()
        status = git(self.repo, "status", "--porcelain", "--untracked-files=all")
        self.assertIn(".ai-dev-workflow/config.json", status)
        self.assertNotIn("tasks/favorites", status)
        self.wf("init", "--update", "--commit", "none")
        self.assertIn("/.ai-dev-workflow/\n", self.exclude())
        self.wf("init", "--update", "--commit", "all")
        self.assertNotIn("ai-dev-workflow", self.exclude())
        self.assertIn("ACTIVE", (self.repo / ".ai-dev-workflow" / ".gitignore").read_text(encoding="utf-8"))


class TemplateTest(WorkflowTestCase):
    def test_a_template_must_be_chosen_and_is_never_invented(self) -> None:
        self.assertIn("never invent", self.wf("init", "--commit", "all", expect=1))
        self.init()
        (self.repo / ".ai-dev-workflow" / "templates" / "example-spec-template.md").unlink()
        out = self.wf("new", "favorites", "--title", "x", "--invocation", "/ai-dev-workflow x", expect=1)
        self.assertIn("never invent", out)

    def test_private_library_templates_are_offered_but_never_applied_silently(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            install.main(["add-template", "mine", str(EXAMPLE_TEMPLATE), "--rules",
                          str(EXAMPLE_TEMPLATE.with_name("example-spec-template.rules.json"))])
        discover = json.loads(self.wf("init", "--discover", "--json"))
        self.assertEqual(discover["user_templates"], [{"name": "user:mine", "has_rules": True, "default": False}])
        self.assertFalse((self.repo / ".ai-dev-workflow").exists())
        self.wf("init", "--template", "user:mine", "--commit", "all")
        config = (self.repo / ".ai-dev-workflow" / "config.json").read_text(encoding="utf-8")
        self.assertIn('"template_source": "user:mine"', config)
        self.assertNotIn(str(self.home), config)

    def test_each_project_keeps_its_own_copy_of_the_template(self) -> None:
        self.init()
        copied = self.repo / ".ai-dev-workflow" / "templates" / "example-spec-template.md"
        self.assertEqual(copied.read_text(encoding="utf-8"), EXAMPLE_TEMPLATE.read_text(encoding="utf-8"))
        self.new_task()
        self.assertEqual((self.task / "spec.md").read_text(encoding="utf-8"), EXAMPLE_TEMPLATE.read_text(encoding="utf-8"))


class PreexistingWorkTest(WorkflowTestCase):
    def test_uncommitted_work_from_before_the_task_is_kept_apart(self) -> None:
        self.write("notes.txt", "my unfinished work\n")
        self.init()
        out = self.wf("new", "favorites", "--title", "Saved favorites", "--invocation", "/ai-dev-workflow favorites")
        self.assertIn("already had uncommitted changes", out)
        scope = json.loads(self.wf("scope", "favorites", "--json"))
        self.assertNotIn("notes.txt", scope["task_changes"])
        self.assertIn("notes.txt", scope["preexisting_untouched"])
        self.write("notes.txt", "my unfinished work\nplus an edit\n")
        scope = json.loads(self.wf("scope", "favorites", "--json"))
        self.assertIn("notes.txt", scope["preexisting_modified"])

    def test_project_level_skill_copies_are_not_task_changes(self) -> None:
        self.init()
        self.new_task()
        self.write(".agents/skills/ai-dev-workflow/SKILL.md", "updated skill copy\n")
        self.write(".claude/skills/ai-dev-workflow/SKILL.md", "updated skill copy\n")
        self.assertEqual(json.loads(self.wf("scope", "favorites", "--json"))["task_changes"], [])

    def test_unrelated_changes_can_be_excluded_with_a_reason(self) -> None:
        self.init()
        self.new_task()
        self.write("other.txt", "unrelated\n")
        self.assertIn("--reason", self.wf("scope", "favorites", "--exclude", "other.txt", expect=1))
        self.wf("scope", "favorites", "--exclude", "other.txt", "--reason", "user said it is theirs")
        scope = json.loads(self.wf("scope", "favorites", "--json"))
        self.assertEqual((scope["task_changes"], scope["excluded"]), ([], ["other.txt"]))


if __name__ == "__main__":
    unittest.main()
