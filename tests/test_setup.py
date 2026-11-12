"""First-time project setup: default template, grounded check recommendations, record-saving choices."""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import unittest
from unittest import mock

from helpers import EXAMPLE_TEMPLATE, WorkflowTestCase, git

import install  # noqa: E402
import workflow  # noqa: E402

RULES = EXAMPLE_TEMPLATE.with_name("example-spec-template.rules.json")


class SetupTestCase(WorkflowTestCase):
    def discover(self) -> dict:
        return json.loads(self.wf("init", "--discover", "--json"))

    def add_template(self, name: str, *extra: str) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            install.main(["add-template", name, str(EXAMPLE_TEMPLATE), "--rules", str(RULES), *extra])

    def config(self) -> dict:
        return json.loads((self.repo / ".ai-dev-workflow" / "config.json").read_text(encoding="utf-8"))

    def checks(self) -> dict:
        return {c["id"]: c for c in self.discover()["suggested_checks"]}


class DefaultTemplateTest(SetupTestCase):
    def test_without_a_default_nothing_is_recommended_and_examples_are_not_picked(self) -> None:
        self.write("docs/example-spec-template.md", EXAMPLE_TEMPLATE.read_text(encoding="utf-8"))
        report = self.discover()
        self.assertIsNone(report["template"]["recommended"])
        self.assertIn("No default template is registered", report["template"]["reason"])
        self.assertIn("docs/example-spec-template.md", report["template_candidates"])
        self.assertIn("(example)", self.wf("init", "--discover"))
        self.assertIn("never invent", self.wf("init", "--commit", "all", expect=1))

    def test_the_registered_default_is_recommended_for_every_new_project(self) -> None:
        self.add_template("other")
        self.add_template("mine", "--default")
        report = self.discover()
        self.assertEqual(report["template"]["recommended"], "user:mine")
        self.assertEqual([t["default"] for t in report["user_templates"]], [True, False])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            install.main(["list-templates"])
        self.assertIn("user:mine  (with rules)  [default]", out.getvalue())
        self.wf("init", "--template", "user:mine", "--commit", "all")
        setup = self.config()["setup"]
        self.assertEqual(setup["recommended"]["template"], "user:mine")
        self.assertEqual(setup["chosen"]["template"], "user:mine")
        self.assertNotIn(str(self.home), json.dumps(self.config()))

    def test_a_missing_default_is_explained_and_not_replaced(self) -> None:
        self.add_template("mine", "--default")
        shutil.rmtree(self.home / ".ai-dev-workflow" / "templates" / "mine")
        report = self.discover()
        self.assertFalse(report["default_template"]["available"])
        self.assertIsNone(report["template"]["recommended"])
        self.assertIn("files are missing", report["template"]["reason"])

    def test_the_default_can_be_changed_and_cleared(self) -> None:
        self.add_template("mine")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(install.main(["default-template", "mine"]), 0)
        self.assertEqual(self.discover()["template"]["recommended"], "user:mine")
        with contextlib.redirect_stdout(io.StringIO()):
            install.main(["default-template", "--clear"])
        self.assertIsNone(self.discover()["template"]["recommended"])
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            install.main(["default-template", "missing"])


class CheckRecommendationTest(SetupTestCase):
    def test_flutter_checks_come_from_the_project_files(self) -> None:
        self.write("pubspec.yaml", "name: app\ndependencies:\n  flutter:\n    sdk: flutter\n"
                                   "dev_dependencies:\n  build_runner: ^2.4.0\n")
        self.write("test/widget_test.dart", "void main() {}\n")
        self.write("assets/translations/en.json", "{}")
        self.write("assets/translations/ar.json", "{}")
        checks = self.checks()
        self.assertEqual(list(checks), ["analyze", "test", "codegen", "dependencies", "translations"])
        self.assertEqual(checks["analyze"]["command"], "flutter analyze")
        self.assertIn("1 test file", checks["test"]["explain"])
        self.assertFalse(checks["codegen"]["required"])
        self.assertEqual(checks["translations"]["files"],
                         ["assets/translations/ar.json", "assets/translations/en.json"])
        for check in checks.values():
            self.assertTrue(check["explain"] and check["evidence"], check["id"])

    def test_no_test_check_without_test_files(self) -> None:
        self.write("pubspec.yaml", "name: app\ndependencies:\n  flutter:\n    sdk: flutter\n")
        self.assertNotIn("test", self.checks())

    def test_node_scripts_are_used_and_the_npm_placeholder_is_ignored(self) -> None:
        self.write("package.json", json.dumps({"scripts": {
            "lint": "eslint .", "test": 'echo "Error: no test specified" && exit 1'}}))
        self.write("pnpm-lock.yaml", "")
        checks = self.checks()
        self.assertEqual(checks["lint"]["command"], "pnpm lint")
        self.assertIn("eslint .", checks["lint"]["explain"])
        self.assertNotIn("test", checks)

    def test_python_test_runner_follows_the_configuration(self) -> None:
        self.write("test_app.py", "import unittest\n")
        self.assertEqual(self.checks()["test"]["command"], f"{workflow.PY_CMD} -m unittest")
        self.write("requirements-dev.txt", "pytest==8.0\nruff\n")
        checks = self.checks()
        self.assertEqual(checks["test"]["command"], f"{workflow.PY_CMD} -m pytest")
        self.assertEqual(checks["lint"]["command"], "ruff check .")

    def test_python_tests_in_a_folder_without_init(self) -> None:
        self.write("tests/test_app.py", "import unittest\n")
        self.assertEqual(self.checks()["test"]["command"], f"{workflow.PY_CMD} -m unittest discover -s tests")

    def test_missing_tools_are_reported_and_ci_commands_are_listed(self) -> None:
        self.write("package.json", json.dumps({"scripts": {"lint": "eslint ."}}))
        self.write(".github/workflows/ci.yml", "jobs:\n  t:\n    steps:\n      - run: npm ci\n      - run: |\n"
                                               "          npm test\n      - run: npm run lint\n")
        with mock.patch.object(workflow.shutil, "which", return_value=None):
            report = self.discover()
            text = self.wf("init", "--discover")
        self.assertFalse(report["suggested_checks"][0]["tool_found"])
        self.assertIn("[tool not found on this computer]", text)
        self.assertEqual(report["ci_commands"], ["npm ci", "npm run lint"])

    def test_init_saves_the_chosen_checks_without_discovery_details(self) -> None:
        self.write("test_app.py", "import unittest\n")
        self.write("pubspec.yaml", "name: app\ndependencies:\n  flutter:\n    sdk: flutter\n")
        self.wf("init", "--template", str(EXAMPLE_TEMPLATE), "--commit", "all", "--without-check", "dependencies",
                "--add-check", "smoke=python3 -m unittest -q")
        cfg = self.config()
        ids = [c["id"] for c in cfg["checks"]]
        self.assertEqual(ids, ["analyze", "test", "smoke"])
        self.assertTrue(all("evidence" not in c and "tool_found" not in c for c in cfg["checks"]))
        self.assertIn("explain", cfg["checks"][0])
        self.assertEqual(cfg["setup"]["recommended"]["checks"], ["analyze", "dependencies", "test"])
        self.assertEqual(cfg["setup"]["chosen"]["checks"], ids)

    def test_bad_check_changes_are_refused(self) -> None:
        self.write("test_app.py", "import unittest\n")
        self.assertIn("no check 'nope'", self.wf("init", "--template", str(EXAMPLE_TEMPLATE), "--commit", "all",
                                                  "--without-check", "nope", expect=1))
        self.assertIn("<id>=<command>", self.wf("init", "--template", str(EXAMPLE_TEMPLATE), "--commit", "all",
                                                 "--add-check", "just-a-name", expect=1))


class RecordOptionsTest(SetupTestCase):
    def test_every_option_is_explained(self) -> None:
        records = self.discover()["records"]
        self.assertEqual([o["mode"] for o in records["options"]], list(workflow.COMMIT_MODES))
        for option in records["options"]:
            for field in ("label", "what", "after_clone", "other_machine", "if_lost", "privacy"):
                self.assertTrue(option[field], (option["mode"], field))
        text = self.wf("init", "--discover")
        self.assertIn("If this computer is lost", text)
        self.assertIn("never commits by itself", text)

    def test_recommendation_follows_the_project(self) -> None:
        self.assertEqual(self.discover()["records"]["recommended"]["mode"], "all")
        git(self.repo, "remote", "add", "origin", "https://example.com/team/app.git")
        self.assertIn("remote", self.discover()["records"]["recommended"]["reason"])
        self.write("LICENSE", "MIT License\n\nPermission is hereby granted, free of charge...\n")
        recommended = self.discover()["records"]["recommended"]
        self.assertEqual(recommended["mode"], "config-only")
        self.assertIn("open-source", recommended["reason"])

    def test_the_user_choice_is_kept_apart_from_the_recommendation(self) -> None:
        self.wf("init", "--template", str(EXAMPLE_TEMPLATE), "--commit", "none")
        setup = self.config()["setup"]
        self.assertEqual(setup["recommended"]["commit"], "all")
        self.assertEqual(setup["chosen"]["commit"], "none")
        self.assertEqual(self.config()["records"]["commit"], "none")

    def test_a_new_clone_gets_the_exclusion_when_a_task_starts(self) -> None:
        self.init(commit="config-only")
        exclude = self.repo / ".git" / "info" / "exclude"
        exclude.write_text("", encoding="utf-8")  # what a fresh clone of the repository has
        self.assertIn("is not yet applied in this clone", self.wf("init", "--discover"))
        self.assertIn("Applied records.commit=config-only", self.wf(
            "new", "favorites", "--title", "x", "--invocation", "/ai-dev-workflow x"))
        self.assertIn("/.ai-dev-workflow/tasks/", exclude.read_text(encoding="utf-8"))


class ExistingSetupTest(SetupTestCase):
    def test_an_existing_setup_is_reused_not_asked_again(self) -> None:
        self.init()
        report = self.discover()
        self.assertTrue(report["existing"]["valid"])
        text = self.wf("init", "--discover")
        self.assertIn("already set up", text)
        self.assertNotIn("Setup proposal", text)
        self.assertIn("already set up", self.wf("init", "--template", str(EXAMPLE_TEMPLATE), "--commit", "all",
                                                 expect=1))

    def test_problems_in_an_existing_setup_are_listed(self) -> None:
        self.init()
        (self.repo / ".ai-dev-workflow" / "templates" / "example-spec-template.md").unlink()
        report = self.discover()["existing"]
        self.assertFalse(report["valid"])
        self.assertTrue(any("template" in p for p in report["problems"]))
        self.assertIn("PROBLEM:", self.wf("init", "--discover"))

    def test_update_changes_only_what_the_user_asked(self) -> None:
        self.init()
        self.assertIn("Nothing to change", self.wf("init", "--update", expect=1))
        self.add_template("mine")
        self.wf("init", "--update", "--template", "user:mine", "--add-check", "lint=ruff check .")
        cfg = self.config()
        self.assertEqual(cfg["template_source"], "user:mine")
        self.assertEqual(cfg["records"]["commit"], "all")
        self.assertEqual([c["id"] for c in cfg["checks"]], ["unit", "lint"])
        self.assertEqual(cfg["setup"]["chosen"]["template"], "user:mine")
        self.assertEqual(cfg["setup"]["changes"][-1]["changed"], ["template=user:mine", "checks"])

    def test_the_template_cannot_change_under_an_open_task(self) -> None:
        self.init()
        self.new_task()
        self.add_template("mine")
        self.assertIn("favorites", self.wf("init", "--update", "--template", "user:mine", expect=1))


if __name__ == "__main__":
    unittest.main()
