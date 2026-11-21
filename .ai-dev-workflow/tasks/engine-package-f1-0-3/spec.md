# Feature Spec: Split workflow.py into the aidw package, no behaviour change (F1.0.3)

---

## 1. Requirements

**Goal (one sentence):**
The engine's code lives in a structured standard-library package that later phases can extend, while every user, agent, hook, tool and test sees exactly the same behaviour as before.

**User story:**
As a maintainer of AIDevWorkflow, I want the 3,458-line engine split into focused modules so that adapters, records, modes and decisions can be added without growing one file, with proof that nothing changed for users.

**Functional requirements:**
- **FR-1:** The engine's code lives in `skills/ai-dev-workflow/scripts/aidw/`, organised in layers from TARGET_ARCHITECTURE §3 (infra, records, store, core, adapters, agents, cli), using the Python standard library only.
- **FR-2:** `scripts/workflow.py` stays at the same path as a thin entry point: it puts its own folder first on `sys.path`, imports the package, re-exports the public names and runs `main()` when executed as a script.
- **FR-3:** Every public module-level name importable from `workflow` before the split stays importable after it (checked against a list recorded before the split), and `workflow.shutil` and `workflow.locale` still refer to the standard modules.
- **FR-4:** Behaviour is identical: commands, options, help, messages, exit codes, records, hashes and fingerprints; the golden, script-entry and all existing tests pass without regenerating any golden file.
- **FR-5:** Code moves verbatim, except imports and the location-dependent path constants (`SKILL_DIR`, `TEMPLATES_DIR`), which must resolve to the same folders as before.
- **FR-6:** The package's import graph has no cycles: each module imports only from lower layers (infra → records/store → core/adapters → agents/cli).
- **FR-7:** Loading by file path keeps working: `tools/prepublish_check.py` and the SKILL.md hooks work unchanged, and `install.py` copies the package with the skill for user and project installs with `doctor` reporting no drift.
- **FR-8:** ruff and mypy pass with the package included.

**Out of scope (do NOT build):**
- Any logic change, bug fix or rename of a public name (the reproduced bugs TD-03/TD-04 are fixed in E1.1, not here)
- The engine API layer (F1.0.4), schema check/migrate/locking (F1.0.5), single version source (F1.0.6)
- Splitting the installer (`install.py` stays one file)
- Regenerating golden files to make tests pass
- Performance tuning (startup time is measured and reported, not optimised)

---

## 2. Edge Cases

| ID | Scenario | Expected Behavior |
|----|----------|-------------------|
| EC-1 | `workflow.py` run by absolute path from another working directory (as the hooks do) | It finds its bundled `aidw` package through its own folder and behaves as before; covered by the script-entry test run from the fixture repository |
| EC-2 | The engine loaded under another module name through `spec_from_file_location` (`tools/prepublish_check.py`) | `find_secrets` is available and the scan gives the same file count and findings as before |
| EC-3 | Template paths after the move | `TEMPLATES_DIR` equals `skills/ai-dev-workflow/assets/templates`; a test asserts it |
| EC-4 | Copied installs (user canonical copy, project copies, copy mode used on Windows) | `aidw/` is copied, `__pycache__` excluded; the installed copy runs `--version`, and `doctor` reports no problems |
| EC-5 | Another module named `aidw` elsewhere on `sys.path` | The bundled package wins because `workflow.py` inserts its own folder at position 0 |
| EC-6 | Startup time grows with more modules (the Claude hook runs on every edit) | Median time of `workflow.py --version` and of the hook entry measured before and after; a slowdown above 50 ms is reported as an audit finding, never hidden |
| EC-7 | Tests patch `workflow.shutil.which` and `workflow.locale.getpreferredencoding` | The patches still affect engine code, because they patch the shared standard modules |

---

## 3. Constraints (must NOT change)

- **Protected files / modules:** `SKILL.md`, `references/`, `assets/`, `install.py`, `index.html`, `docs/` (except a short code-layout note), every existing test expectation and every golden file.
- **Public contracts:** the CLI (commands, options, help, outputs, exit codes), record formats, the `scripts/workflow.py` path, and the names importable from `workflow`.
- **Allowed packages:** Python standard library only, Python 3.9+. No new packages without approval.
- **Architecture:** layers from TARGET_ARCHITECTURE §3; the skill folder stays self-contained and copyable; no business logic left in `workflow.py`.
- **Scope:** `scripts/workflow.py`, the new `scripts/aidw/` package, `pyproject.toml` if the mypy settings need it, new tests only (no edits to existing tests), a short code-layout note in the README "Development" section.
- **If anything is unclear:** stop and ask. Do not guess.

---

## 4. Acceptance Criteria

- **AC-1:** Given the split engine, when the full suite runs on Python 3.13 and 3.9, then every test passes and no file in `tests/golden/` has changed (byte comparison with the pre-split copy).
- **AC-2:** Given the package, when ruff and mypy run with the project configuration, then both report no issues.
- **AC-3:** Given a user-level install from the working copy into a temporary home folder, when `doctor` and the installed `workflow.py --version` run, then doctor reports no problems and the version matches.
- **AC-4:** Given `tools/prepublish_check.py`, when it runs after the split, then it loads the engine and reports the same scan result as before the split.
- **AC-5:** Given the package modules, when each is imported first in a fresh interpreter, then none raises an import error (no cycles), and the layer rule holds.
- **AC-6:** Given the public-names list recorded before the split, when the names test runs after it, then every recorded name is importable from `workflow`, and `workflow.py` contains no engine logic.
- **AC-7:** Given before/after timing of `workflow.py --version` and the hook entry, when the report is written, then both medians are recorded with the difference.

**Done when:**
- [ ] All requirements implemented
- [ ] All edge cases handled as specified
- [ ] Required tests pass through the engine: `unit` (existing, golden, script-entry, names, layer and install round-trip tests), `unit-py39`, `privacy`, `ruff`, `mypy`
- [ ] The CI test matrix and lint job pass after the owner pushes
- [ ] The README "Development" section describes the package layout in a few lines
