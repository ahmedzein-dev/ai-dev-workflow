"""install.py: one canonical copy, links or copies per agent, drift detection, project installs, private templates."""
from __future__ import annotations

import contextlib
import io
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import EXAMPLE_TEMPLATE

import install  # noqa: E402


def run(*argv: str) -> tuple:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        try:
            code = install.main(list(argv))
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else 1
            out.write(str(exc))
    return code, out.getvalue()


def symlinks_supported(base: Path) -> bool:
    try:
        os.symlink(str(base), str(base / "probe-link"), target_is_directory=True)
        os.unlink(str(base / "probe-link"))
        return True
    except (OSError, NotImplementedError):
        return False


class InstallTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aidw-install-"))
        self.home = self.tmp / "home"
        self.home.mkdir()
        self._env = mock.patch.dict(os.environ, {"HOME": str(self.home), "USERPROFILE": str(self.home),
                                                 "AI_DEV_WORKFLOW_HOME": str(self.home / ".ai-dev-workflow")})
        self._env.start()

    def tearDown(self) -> None:
        self._env.stop()

        def force(func, path, _exc):
            os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
            func(path)

        if sys.version_info >= (3, 12):
            shutil.rmtree(self.tmp, onexc=force)
        else:
            shutil.rmtree(self.tmp, onerror=force)

    @property
    def canonical(self) -> Path:
        return self.home / ".agents" / "skills" / "ai-dev-workflow"

    @property
    def claude(self) -> Path:
        return self.home / ".claude" / "skills" / "ai-dev-workflow"

    def test_user_install_creates_one_canonical_copy_and_links_claude(self) -> None:
        code, out = run("install", "--agents", "claude,codex")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.canonical / "SKILL.md").exists())
        self.assertTrue((self.canonical / ".aidw-install.json").exists())
        if symlinks_supported(self.tmp):
            self.assertTrue(self.claude.is_symlink())
            self.assertEqual(self.claude.resolve(), self.canonical.resolve())
        else:
            self.assertIn("symlink not available", out)
        self.assertEqual(run("doctor")[0], 0)

    def test_copy_mode_and_drift_detection(self) -> None:
        self.assertEqual(run("install", "--agents", "claude", "--copy")[0], 0)
        self.assertFalse(self.claude.is_symlink())
        self.assertEqual(run("doctor")[0], 0)
        (self.claude / "references" / "lifecycle.md").write_text("changed\n", encoding="utf-8")
        code, out = run("doctor")
        self.assertEqual(code, 1)
        self.assertIn("DRIFT", out)
        self.assertEqual(run("update", "--copy")[0], 0)
        self.assertEqual(run("doctor")[0], 0)

    def test_refuses_to_replace_a_different_skill(self) -> None:
        self.claude.mkdir(parents=True)
        (self.claude / "SKILL.md").write_text("---\nname: something-else\ndescription: x\n---\n", encoding="utf-8")
        code, out = run("install", "--agents", "claude")
        self.assertEqual(code, 1)
        self.assertIn("Refusing to replace", out)

    def test_project_install_uses_real_copies(self) -> None:
        repo = self.tmp / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=str(repo), check=True)
        self.assertEqual(run("install", "--project", str(repo))[0], 0)
        agents_copy = repo / ".agents" / "skills" / "ai-dev-workflow"
        claude_copy = repo / ".claude" / "skills" / "ai-dev-workflow"
        self.assertTrue(agents_copy.is_dir() and not agents_copy.is_symlink())
        self.assertTrue(claude_copy.is_dir() and not claude_copy.is_symlink())
        self.assertEqual(run("doctor", "--project", str(repo))[0], 0)

    def test_uninstall_needs_confirmation(self) -> None:
        run("install", "--agents", "claude")
        self.assertEqual(run("uninstall")[0], 1)
        self.assertTrue(self.canonical.exists())
        self.assertEqual(run("uninstall", "--yes")[0], 0)
        self.assertFalse(self.canonical.exists() or self.claude.exists() or self.claude.is_symlink())

    def test_private_templates_live_outside_any_repository(self) -> None:
        rules = EXAMPLE_TEMPLATE.with_name("example-spec-template.rules.json")
        self.assertEqual(run("add-template", "mine", str(EXAMPLE_TEMPLATE), "--rules", str(rules))[0], 0)
        stored = self.home / ".ai-dev-workflow" / "templates" / "mine"
        self.assertTrue((stored / "template.md").exists() and (stored / "rules.json").exists())
        self.assertIn("user:mine", run("list-templates")[1])
        self.assertEqual(run("add-template", "mine", str(EXAMPLE_TEMPLATE))[0], 1)

    def test_warns_when_gemini_would_see_two_copies(self) -> None:
        run("install", "--agents", "codex")
        duplicate = self.home / ".gemini" / "skills" / "ai-dev-workflow"
        duplicate.mkdir(parents=True)
        self.assertIn("two copies", run("doctor")[1])


if __name__ == "__main__":
    unittest.main()
