"""The engine package: public names stay importable from `workflow`, modules import cleanly in layer order, paths
resolve to the skill folder, and installed copies work.

tests/golden/workflow-public-names.txt was recorded from the single-file engine before the F1.0.3 split: every
non-underscore name defined in workflow.py (functions, classes, constants), excluding imported modules and typing names.
"""
from __future__ import annotations

import ast
import locale
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, SKILL

import workflow

GOLDEN = Path(__file__).resolve().parent / "golden"


class PublicNamesTest(unittest.TestCase):
    def test_every_name_recorded_before_the_split_is_still_importable(self) -> None:
        names = [n for n in (GOLDEN / "workflow-public-names.txt").read_text(encoding="utf-8").split() if n]
        self.assertGreater(len(names), 150)
        missing = [n for n in names if not hasattr(workflow, n)]
        self.assertEqual(missing, [], f"names no longer importable from workflow: {missing}")

    def test_patched_standard_modules_are_the_real_ones(self) -> None:
        self.assertIs(workflow.shutil, shutil)
        self.assertIs(workflow.locale, locale)

    def test_template_folder_still_resolves_to_the_skill_assets(self) -> None:
        self.assertEqual(Path(workflow.TEMPLATES_DIR), SKILL / "assets" / "templates")
        self.assertEqual(Path(workflow.SKILL_DIR), SKILL)
        self.assertTrue((Path(workflow.TEMPLATES_DIR) / "plan.md").is_file())
        self.assertEqual(ROOT / "skills" / "ai-dev-workflow", SKILL)


SCRIPTS = SKILL / "scripts"
PKG = SCRIPTS / "aidw"
# Layer of each top-level part of the package; a module may import only from its own layer or lower ones.
LAYER = {"__init__": 0, "errors": 0, "constants": 0, "infra": 1, "records": 2, "store": 2, "core": 3, "adapters": 3,
         "api": 4, "agents": 5, "cli": 5}


def module_names() -> list:
    names = []
    for path in sorted(PKG.rglob("*.py")):
        rel = path.relative_to(SCRIPTS).with_suffix("")
        parts = list(rel.parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        names.append(".".join(parts))
    return names


def layer_of(module: str) -> int:
    parts = module.split(".")
    return LAYER["__init__"] if len(parts) == 1 else LAYER[parts[1]]


class PackageStructureTest(unittest.TestCase):
    def test_every_module_imports_first_in_a_fresh_interpreter(self) -> None:
        for name in module_names():
            with self.subTest(module=name):
                proc = subprocess.run([sys.executable, "-c", f"import {name}"], cwd=str(SCRIPTS),
                                      capture_output=True, text=True)
                self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_imports_follow_the_layers_and_have_no_cycles(self) -> None:
        graph = {}
        for name in module_names():
            path = PKG.joinpath(*name.split(".")[1:]) if name != "aidw" else PKG
            path = path / "__init__.py" if path.is_dir() else path.with_suffix(".py")
            tree = ast.parse(path.read_text(encoding="utf-8"))
            targets = {node.module for node in ast.walk(tree)
                       if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == "aidw"}
            graph[name] = targets
            for target in targets:
                with self.subTest(module=name, imports=target):
                    self.assertLessEqual(layer_of(target), layer_of(name), f"{name} imports higher layer {target}")
        visiting, done = set(), set()

        def visit(node: str, trail: list) -> None:
            self.assertNotIn(node, visiting, "import cycle: " + " -> ".join(trail + [node]))
            if node in done:
                return
            visiting.add(node)
            for nxt in graph.get(node, ()):
                visit(nxt, trail + [node])
            visiting.discard(node)
            done.add(node)

        for name in graph:
            visit(name, [])

    def test_entry_point_holds_no_engine_logic(self) -> None:
        tree = ast.parse((SCRIPTS / "workflow.py").read_text(encoding="utf-8"))
        definitions = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
        self.assertEqual(definitions, [])


class InstalledCopyTest(unittest.TestCase):
    def test_user_install_copies_the_package_and_runs(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            env = dict(os.environ, HOME=home, USERPROFILE=home, AI_DEV_WORKFLOW_HOME=str(Path(home) / ".aidw"))
            installer = SCRIPTS / "install.py"
            proc = subprocess.run([sys.executable, str(installer), "--agents", "codex"], env=env,
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            installed = Path(home) / ".agents" / "skills" / "ai-dev-workflow" / "scripts"
            self.assertTrue((installed / "aidw" / "core" / "gates.py").is_file())
            self.assertFalse(any(installed.rglob("__pycache__")))
            version = subprocess.run([sys.executable, str(installed / "workflow.py"), "--version"], env=env,
                                     capture_output=True, text=True, cwd=home)
            self.assertEqual(version.stdout.strip(), f"AIDevWorkflow {workflow.__version__}")
            doctor = subprocess.run([sys.executable, str(installer), "doctor"], env=env, capture_output=True, text=True)
            self.assertIn("canonical copy", doctor.stdout)
            self.assertIn("No problems found", doctor.stdout)
            self.assertNotIn("drift", doctor.stdout.lower())


def run_engine(script: Path, *args: str, env: dict, cwd: str, stdin: str = "") -> "subprocess.CompletedProcess[str]":
    return subprocess.run([sys.executable, str(script), *args], env=env, cwd=cwd, input=stdin,
                          capture_output=True, text=True)


class ProjectInstallTest(unittest.TestCase):
    """Project-level copies live in users' repositories: running the engine must leave them clean (no bytecode)."""

    def test_project_copy_runs_without_writing_bytecode_into_the_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=str(repo), check=True)
            env = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}
            env.update(HOME=tmp, USERPROFILE=tmp)
            installer = SCRIPTS / "install.py"
            proc = subprocess.run([sys.executable, str(installer), "install", "--project", str(repo)], env=env,
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            for copy in (repo / ".agents" / "skills" / "ai-dev-workflow", repo / ".claude" / "skills" / "ai-dev-workflow"):
                with self.subTest(copy=copy.parts[-3]):
                    engine = copy / "scripts" / "workflow.py"
                    self.assertTrue((copy / "scripts" / "aidw" / "core" / "gates.py").is_file())
                    version = run_engine(engine, "--version", env=env, cwd=str(repo))
                    self.assertEqual(version.stdout.strip(), f"AIDevWorkflow {workflow.__version__}")
                    hook = run_engine(engine, "hook", "claude-pre-edit", env=env, cwd=str(repo), stdin="{}")
                    self.assertEqual((hook.returncode, hook.stdout), (0, ""))
                    self.assertEqual(sorted(p.relative_to(copy).as_posix() for p in copy.rglob("__pycache__")), [])
            status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=str(repo),
                                    capture_output=True, text=True).stdout
            self.assertNotIn("__pycache__", status)
            self.assertNotIn(".pyc", status)
            doctor = subprocess.run([sys.executable, str(installer), "doctor", "--project", str(repo)], env=env,
                                    capture_output=True, text=True)
            self.assertIn("No problems found", doctor.stdout)


class ShadowingTest(unittest.TestCase):
    def test_bundled_package_wins_over_another_aidw_on_the_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "aidw"
            fake.mkdir()
            (fake / "__init__.py").write_text('__version__ = "fake"\n', encoding="utf-8")
            env = dict(os.environ, PYTHONPATH=tmp)
            version = run_engine(SCRIPTS / "workflow.py", "--version", env=env, cwd=tmp)
            self.assertEqual(version.stdout.strip(), f"AIDevWorkflow {workflow.__version__}")
