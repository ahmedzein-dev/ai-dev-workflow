# Feature Spec: Dev tooling — ruff, mypy and golden CLI outputs (F1.0.2)

---

## 1. Requirements

**Goal (one sentence):**
Maintainers and CI get a lint check, a type check and golden CLI output tests that fail on any unintended change, before the engine is split into modules (F1.0.3).

**User story:**
As a maintainer of AIDevWorkflow, I want automated lint, type and CLI-output checks so that the module split and later refactors cannot change the engine's behaviour unnoticed.

**Functional requirements:**
- **FR-1:** A repository-root `pyproject.toml` configures ruff and mypy only; it declares no package, no build backend and no runtime dependency.
- **FR-2:** `ruff check .` exits 0 on the repository with ruff's default rule set (E4, E7, E9, F).
- **FR-3:** `mypy` exits 0 with the project configuration: target Python 3.9, files under `skills/ai-dev-workflow/scripts/` and `tools/`, default (non-strict) checking, `warn_unused_ignores` on.
- **FR-4:** `requirements-dev.txt` pins exact versions of ruff and mypy; CI gains a `lint` job (Ubuntu, Python 3.13) that installs it and runs both tools; the existing test matrix is unchanged.
- **FR-5:** A new `tests/test_golden.py` compares CLI output with files committed in `tests/golden/`: `workflow.py --help`, every subcommand's `--help`, `install.py --help`, and, for a fixed scenario repository, `status` (list and one task), `spec-check`, `plan-check`, `outcome` and `init --discover --json`.
- **FR-6:** Before comparison, output is normalized: temporary paths become `<TMP>` with forward slashes, line endings become LF, timestamps become `<TIME>`, the Python executable becomes `<PY>`, and machine-specific tool presence (`tool_found`) becomes `<TOOL_FOUND>`.
- **FR-7:** With `AIDW_UPDATE_GOLDEN=1` set, the golden tests rewrite the golden files and pass; without it, a difference fails the test and prints a unified diff.
- **FR-8:** Lint-only source edits (unused imports or variables, similar mechanical findings) change no behaviour: golden outputs recorded before the edits stay identical after them, and the existing tests keep passing.

**Out of scope (do NOT build):**
- Fixing type findings that would need a behaviour change (recorded as follow-ups instead)
- Strict mypy mode, docstring rules, or reformatting the code (no `ruff format`, no black)
- Any change to commands, options, exit codes, messages or record formats of `workflow.py` and `install.py`
- Packaging or publishing the project (no build backend, no PyPI release)
- Coverage reporting (planned for Phase 10)
- Installing anything into the shipped skill folder

---

## 2. Edge Cases

| ID | Scenario | Expected Behavior |
|----|----------|-------------------|
| EC-1 | argparse help differs between Python versions ("optional arguments:" on 3.9, "options:" on 3.10+) | Normalization maps both headings to "options:"; the golden tests pass on 3.9 and 3.13 |
| EC-2 | Terminal width changes argparse line wrapping | The golden tests set `COLUMNS=100` for their run; output is identical whatever the real terminal width |
| EC-3 | Windows paths and CRLF line endings | Temporary paths become `<TMP>` with forward slashes and text is compared with LF endings; Windows CI passes |
| EC-4 | A golden file is missing | The test fails with a message naming the file and the regeneration command; no file is created unless `AIDW_UPDATE_GOLDEN=1` is set |
| EC-5 | A tool suggested by `init --discover` exists on one machine but not on another | `tool_found` is replaced by `<TOOL_FOUND>` before comparison, so the result does not depend on the machine |
| EC-6 | ruff or mypy is not installed locally | The engine records that check as blocked with the reason, never as passed; CI still runs both tools |
| EC-7 | A mypy finding cannot be fixed without changing behaviour | An inline `# type: ignore[<code>]` with a short reason is added and listed in the final report; `warn_unused_ignores` flags any ignore that becomes unnecessary |

---

## 3. Constraints (must NOT change)

- **Protected files / modules:** behaviour of `skills/ai-dev-workflow/scripts/workflow.py` and `install.py` (lint-only edits allowed); `SKILL.md`, `references/`, `assets/`, `index.html` and `docs/` stay untouched, except a short "Development" note in `README.md`.
- **Public contracts:** every `workflow.py` and `install.py` command, option, exit code, output text and record format stays exactly the same.
- **Allowed packages:** Python standard library at runtime. Dev only: ruff and mypy, pinned in `requirements-dev.txt`. No new packages without approval.
- **Architecture:** The skill folder stays standard-library only and self-contained; dev tooling lives at the repository root and in `tests/`, and `install.py` never copies it (it copies only the skill folder).
- **Scope:** Only touch files related to this feature. No refactoring outside it. Roadmap status files under `docs/roadmap/` are outside this task (DEP-3).
- **If anything is unclear:** stop and ask. Do not guess.

---

## 4. Acceptance Criteria

- **AC-1:** Given the repository with the pinned dev tools installed, when `ruff check .` runs, then it exits 0.
- **AC-2:** Given the same environment, when `mypy` runs with the project configuration, then it reports no errors.
- **AC-3:** Given a push or pull request on GitHub, when CI runs, then a `lint` job installs `requirements-dev.txt` and runs ruff and mypy, and the existing six test jobs still run.
- **AC-4:** Given an unchanged engine, when the golden tests run on Ubuntu, macOS and Windows with Python 3.9 and 3.13, then they pass.
- **AC-5:** Given a deliberate one-word change in a status message, when the golden tests run, then they fail and the diff names the changed line.
- **AC-6:** Given `AIDW_UPDATE_GOLDEN=1`, when the golden tests run, then the golden files are rewritten and the run passes; given it is not set, then no golden file is written.
- **AC-7:** Given the lint-only edits, when the full suite runs, then every existing test and every golden test passes, and the golden files recorded before the edits are unchanged.

**Done when:**
- [ ] All requirements implemented
- [ ] All edge cases handled as specified
- [ ] Required tests pass: the `unit` check (existing tests plus the golden tests) and the `privacy` check through the engine; ruff and mypy pass locally, or are recorded as blocked if DEP-1 is not granted
- [ ] The `lint` job and the six test jobs pass on GitHub Actions after the owner pushes
- [ ] The README "Development" section lists the new commands
