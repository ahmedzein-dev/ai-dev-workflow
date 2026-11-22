"""Technology detection and check recommendations (replaced by declarative adapters in E1.2)."""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from aidw.infra.gitutil import run_git
from aidw.infra.text import read_text


PY_CMD = "python" if os.name == "nt" else "python3"


TRANSLATION_DIRS = ("assets/translations", "assets/lang", "assets/langs", "assets/l10n", "assets/i18n", "assets/locales",
                    "lib/l10n", "locales", "i18n", "src/locales", "src/i18n", "translations")


def _read(repo: Path, rel: str) -> str:
    path = repo / rel
    try:
        return read_text(path) if path.is_file() else ""
    except (OSError, UnicodeDecodeError):
        return ""


def _tool_found(repo: Path, command: str) -> bool:
    first = command.split()[0]
    if first.startswith(("./", ".\\")):
        return (repo / first[2:]).is_file()
    return shutil.which(first) is not None


def _check(cid: str, name: str, command: str, explain: str, evidence: str, required: bool = True,
           **extra: Any) -> Dict[str, Any]:
    check = {"id": cid, "name": name, "command": command, "required": required, "explain": explain,
             "evidence": evidence}
    check.update(extra)
    return check


def _builtin(cid: str, name: str, kind: str, files: List[str], explain: str, evidence: str) -> Dict[str, Any]:
    return {"id": cid, "name": name, "builtin": kind, "files": files, "required": True, "explain": explain,
            "evidence": evidence}


def project_files(repo: Path) -> List[str]:
    return [f for f in run_git(repo, ["ls-files", "-co", "--exclude-standard", "-z"]).split("\0") if f]


def _dart_checks(repo: Path, pubspec: str) -> List[Dict[str, Any]]:
    tool = "flutter" if re.search(r"sdk:\s*flutter", pubspec) else "dart"
    evidence = "pubspec.yaml" + (", analysis_options.yaml" if (repo / "analysis_options.yaml").exists() else "")
    checks = [_check("analyze", f"{tool} analyze", f"{tool} analyze",
                     "Reads the Dart code and reports errors and warnings, without running the app.", evidence,
                     parser="dart-analyzer", fail_on=["error", "warning", "new"])]
    tests = sorted((repo / "test").rglob("*_test.dart")) if (repo / "test").is_dir() else []
    if tests:
        checks.append(_check("test", f"{tool} test", f"{tool} test",
                             f"Runs the project's automated tests ({len(tests)} test file(s) in test/).",
                             "test/*_test.dart", accepts_args=True))
    if re.search(r"^\s+build_runner\s*:", pubspec, re.M):
        checks.append(_check("codegen", "build_runner", "dart run build_runner build --delete-conflicting-outputs",
                             "Regenerates generated code (models, serializers); needed only when that code changes.",
                             "build_runner in pubspec.yaml", required=False,
                             when="Run when code-generated sources (models, serializers) change."))
    checks.append(_builtin("dependencies", "New dependencies", "manifest-diff", ["pubspec.yaml"],
                           "Lists packages added to pubspec.yaml, so every new dependency gets reviewed.",
                           "pubspec.yaml"))
    return checks


def _node_checks(repo: Path, text: str) -> List[Dict[str, Any]]:
    try:
        pkg = json.loads(text)
    except ValueError:
        pkg = {}
    scripts = pkg.get("scripts") or {}
    if (repo / "pnpm-lock.yaml").exists():
        runner = "pnpm"
    elif (repo / "yarn.lock").exists():
        runner = "yarn"
    elif (repo / "bun.lockb").exists() or (repo / "bun.lock").exists():
        runner = "bun run"
    else:
        runner = "npm run"
    meaning = {"lint": "Checks code style and common mistakes", "typecheck": "Checks the types",
               "type-check": "Checks the types", "check": "Runs the project's combined checks",
               "test": "Runs the automated tests", "build": "Builds the project to make sure it compiles"}
    checks: List[Dict[str, Any]] = []
    for name in ("lint", "typecheck", "type-check", "check", "test", "build"):
        body = scripts.get(name)
        if not isinstance(body, str) or not body.strip():
            continue
        if name == "test" and "no test specified" in body:
            continue
        cid = "typecheck" if name == "type-check" else name
        if any(c["id"] == cid for c in checks):
            continue
        checks.append(_check(cid, f"{runner} {name}", f"{runner} {name}",
                             f"{meaning[name]} (package.json script: {body.strip()[:80]}).",
                             f"package.json scripts.{name}", required=name != "build", accepts_args=name == "test"))
    deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
    if not any(c["id"] == "typecheck" for c in checks) and (repo / "tsconfig.json").exists() and "typescript" in deps:
        checks.append(_check("typecheck", "TypeScript types", "npx tsc --noEmit",
                             "Checks the TypeScript types without building.", "tsconfig.json, typescript in package.json"))
    checks.append(_builtin("dependencies", "New dependencies", "manifest-diff", ["package.json"],
                           "Lists packages added to package.json, so every new dependency gets reviewed.",
                           "package.json"))
    return checks


def _python_checks(repo: Path, files: List[str]) -> List[Dict[str, Any]]:
    py_files = [f for f in files if f.endswith(".py")]
    markers = [f for f in ("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "tox.ini") if (repo / f).exists()]
    if not py_files and not markers:
        return []
    pyproject, setup_cfg, tox = _read(repo, "pyproject.toml"), _read(repo, "setup.cfg"), _read(repo, "tox.ini")
    requirements = " ".join(_read(repo, f) for f in files if re.match(r"requirements[^/]*\.txt$", f))
    deps = (pyproject + "\n" + requirements + "\n" + setup_cfg).lower()
    tests = [f for f in py_files if re.search(r"(?:^|/)(?:test_[^/]*|[^/]*_test)\.py$", f)]
    checks: List[Dict[str, Any]] = []
    uses_pytest = ((repo / "pytest.ini").exists() or "[tool.pytest" in pyproject or "[tool:pytest]" in setup_cfg
                   or "[pytest]" in tox or any(f.endswith("conftest.py") for f in py_files)
                   or re.search(r"\bpytest\b", deps) is not None)
    if tests and uses_pytest:
        checks.append(_check("test", "pytest", f"{PY_CMD} -m pytest", "Runs the automated tests with pytest.",
                             f"{len(tests)} test file(s), pytest configured", accepts_args=True))
    elif tests:
        top = sorted({f.split("/")[0] for f in tests if "/" in f})
        if not top:
            command = f"{PY_CMD} -m unittest"
        elif len(top) == 1 and not (repo / top[0] / "__init__.py").exists():
            command = f"{PY_CMD} -m unittest discover -s {top[0]}"
        else:
            command = f"{PY_CMD} -m unittest discover"
        checks.append(_check("test", "unittest", command,
                             "Runs the automated tests with Python's built-in unittest.",
                             f"{len(tests)} test file(s), no pytest configuration"))
    if "[tool.ruff" in pyproject or (repo / "ruff.toml").exists() or (repo / ".ruff.toml").exists() \
            or re.search(r"\bruff\b", deps):
        checks.append(_check("lint", "ruff", "ruff check .", "Checks code style and common mistakes.",
                             "ruff configuration"))
    elif (repo / ".flake8").exists() or "[flake8]" in setup_cfg or "[flake8]" in tox:
        checks.append(_check("lint", "flake8", "flake8", "Checks code style and common mistakes.",
                             "flake8 configuration"))
    if (repo / "mypy.ini").exists() or "[tool.mypy]" in pyproject or "[mypy]" in setup_cfg:
        checks.append(_check("typecheck", "mypy", "mypy .", "Checks the type annotations.", "mypy configuration"))
    return checks


def _other_checks(repo: Path, files: List[str]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    if (repo / "go.mod").exists():
        checks.append(_check("vet", "go vet", "go vet ./...", "Reports suspicious Go code.", "go.mod"))
        checks.append(_check("test", "go test", "go test ./...", "Runs the Go tests.", "go.mod"))
    if (repo / "Cargo.toml").exists():
        if shutil.which("cargo-clippy"):
            checks.append(_check("clippy", "cargo clippy", "cargo clippy", "Reports common Rust mistakes.",
                                 "Cargo.toml, clippy installed"))
        checks.append(_check("test", "cargo test", "cargo test", "Builds and runs the Rust tests.", "Cargo.toml"))
    gradlew = "gradlew.bat" if os.name == "nt" else "./gradlew"
    if (repo / "gradlew").exists() or (repo / "gradlew.bat").exists():
        checks.append(_check("test", "Gradle tests", f"{gradlew} test", "Builds the project and runs its tests.",
                             "gradlew"))
        if any(re.search(r"com\.android\.application", _read(repo, f)) for f in files
               if re.search(r"(?:^|/)build\.gradle(?:\.kts)?$", f)):
            checks.append(_check("lint", "Android lint", f"{gradlew} lint", "Checks the Android code and resources.",
                                 "Android Gradle plugin"))
    elif (repo / "pom.xml").exists():
        checks.append(_check("test", "Maven tests", "mvn -q test", "Builds the project and runs its tests.", "pom.xml"))
    if any(re.match(r"[^/]+\.(?:sln|csproj)$", f) for f in files):
        checks.append(_check("build", "dotnet build", "dotnet build", "Builds the project to make sure it compiles.",
                             ".sln/.csproj"))
        checks.append(_check("test", "dotnet test", "dotnet test", "Runs the .NET tests.", ".sln/.csproj"))
    if (repo / "Gemfile").exists():
        if (repo / "spec").is_dir():
            checks.append(_check("test", "RSpec", "bundle exec rspec", "Runs the Ruby specs.", "Gemfile, spec/"))
        if (repo / ".rubocop.yml").exists():
            checks.append(_check("lint", "RuboCop", "bundle exec rubocop", "Checks Ruby code style.", ".rubocop.yml"))
    if (repo / "Package.swift").exists():
        checks.append(_check("build", "swift build", "swift build", "Builds the Swift package.", "Package.swift"))
        if (repo / "Tests").is_dir():
            checks.append(_check("test", "swift test", "swift test", "Runs the Swift tests.", "Package.swift, Tests/"))
    return checks


def _translation_check(repo: Path) -> Optional[Dict[str, Any]]:
    for folder in TRANSLATION_DIRS:
        path = repo / folder
        if path.is_dir():
            files = sorted(f"{folder}/{p.name}" for p in path.iterdir() if p.suffix in (".json", ".arb"))
            if len(files) >= 2:
                return _builtin("translations", "Translation keys match", "json-key-parity", files,
                                "Checks that every translation file has the same keys, so no text is missing "
                                "in one language.", folder)
    return None


def detect_checks(repo: Path, files: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Recommend checks from the project's own files; each says why it was suggested and whether its tool exists."""
    files = project_files(repo) if files is None else files
    checks: List[Dict[str, Any]] = []
    pubspec = _read(repo, "pubspec.yaml")
    if pubspec:
        checks += _dart_checks(repo, pubspec)
    package = _read(repo, "package.json")
    if package:
        checks += _node_checks(repo, package)
    checks += _python_checks(repo, files)
    checks += _other_checks(repo, files)
    translations = _translation_check(repo)
    if translations:
        checks.append(translations)
    makefile = _read(repo, "Makefile")
    if not any(c["id"] == "test" for c in checks) and re.search(r"^test\s*:", makefile, re.M):
        checks.append(_check("test", "make test", "make test", "Runs the project's test target.", "Makefile"))
    unique: Dict[str, Dict[str, Any]] = {}
    for check in checks:
        unique.setdefault(check["id"], check)
    for check in unique.values():
        if check.get("command"):
            check["tool_found"] = _tool_found(repo, check["command"])
    return list(unique.values())


def ci_commands(repo: Path, files: List[str]) -> List[str]:
    """Single-line commands the project's CI already runs (GitHub Actions `run:` lines)."""
    found: List[str] = []
    for rel in files:
        if not re.match(r"\.github/workflows/[^/]+\.ya?ml$", rel):
            continue
        for line in _read(repo, rel).splitlines():
            match = re.match(r"\s*(?:-\s*)?run:\s*(.+?)\s*$", line)
            if not match:
                continue
            command = match.group(1).strip().strip("'\"")
            if command and command[0] not in "|>" and not command.startswith(("echo ", "git config")) \
                    and command not in found:
                found.append(command)
    return found[:12]
