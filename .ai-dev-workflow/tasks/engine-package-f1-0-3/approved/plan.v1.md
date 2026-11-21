# Implementation Plan: F1.0.3 Split workflow.py into the aidw package (no behaviour change)

> Spec: v1 · e4243a94
> Frozen once approved. Progress is recorded with `workflow.py step`, never by editing this plan.

## 1. Goal

Move the engine from one 3,458-line file into the `aidw/` package along its existing section boundaries, with
`workflow.py` as a thin entry point, and prove that nothing observable changed.

## 2. Current Behavior

- `skills/ai-dev-workflow/scripts/workflow.py` holds 157 top-level definitions in 16 sections (basics L124, secrets
  L187, git L247, markdown L410, project config L739, task state L807, specification checks L911, other records L1106,
  approvals and gates L1255, checks L1425, outcome L1666, discovery for init L1732, command helpers L2163, commands
  L2246, agent hooks L3161, CLI L3300).
- `SKILL_DIR = Path(__file__).resolve().parent.parent` and `TEMPLATES_DIR` depend on the file's location.
- Users of the module: tests (`import workflow`; `from workflow import STAGES, find_secrets, decode_command_output,
  parse_analyzer`; `workflow.main/build_parser/PY_CMD/REFERENCE/COMMIT_MODES/__version__`; patches on
  `workflow.shutil.which` and `workflow.locale.getpreferredencoding`), `tools/prepublish_check.py` (loads the file by
  path, uses `find_secrets`), the SKILL.md hooks (run the file by path), `install.py` (copies the whole skill folder,
  ignoring `__pycache__`).
- Safety net from F1.0.2: 8 golden files, a script-entry test, 147 tests, ruff and mypy.

## 3. Proposed Solution

Section → module map (pure moves; only imports and two path constants change):

| Module | Sections | Notes |
|---|---|---|
| `aidw/__init__.py` | `__version__` | |
| `aidw/errors.py` | `WorkflowError` | |
| `aidw/constants.py` | names, stages, tables, `REFERENCE`, `NEXT`, `SKILL_DIR`, `TEMPLATES_DIR` | paths recomputed: `Path(__file__).resolve().parents[2]` → same skill folder |
| `aidw/infra/text.py` | basics | |
| `aidw/infra/secrets.py` | secrets | |
| `aidw/infra/gitutil.py` | git | |
| `aidw/records/markdown.py` | markdown model and structure checks | |
| `aidw/store/config.py` | project config | |
| `aidw/store/state.py` | task state, `ACTIVE` | |
| `aidw/records/parsers.py` | other records (dependencies, matrix, audit, report) | |
| `aidw/core/spec.py` | specification checks, `plan_check` | |
| `aidw/core/gates.py` | approvals and gates | |
| `aidw/core/checks.py` | checks, analyzer, built-ins | |
| `aidw/core/outcome.py` | outcome | |
| `aidw/adapters/detect.py` | technology detection (`_dart_checks` … `detect_checks`, `ci_commands`) | becomes the adapter registry's home in E1.2 |
| `aidw/core/setup.py` | rest of "discovery for init": template proposal, records options, commit modes | |
| `aidw/cli/helpers.py` | command helpers (`status_line`, `task_summary`, …) | |
| `aidw/agents/claude_hooks.py` | agent hooks | imports `cli.helpers.status_line` |
| `aidw/cli/commands.py` | `cmd_*`, printers, init helpers | |
| `aidw/cli/main.py` | `build_parser`, `main` | |
| `scripts/workflow.py` | entry point | `sys.path` insert, imports, re-exports, `import shutil, locale`, `__main__` |

Moving incrementally (lowest layer first) keeps the suite runnable after every step: `workflow.py` imports moved
names from the package until nothing is left in it.

## 4. Affected Areas

- New: `skills/ai-dev-workflow/scripts/aidw/` (about 20 modules), `tests/test_package.py`, `tests/golden/workflow-public-names.txt`
- Changed: `skills/ai-dev-workflow/scripts/workflow.py`, `README.md` (layout note), `pyproject.toml` only if mypy needs a setting
- Unchanged by design: every existing test, every existing golden file, `install.py`, `SKILL.md`, `tools/prepublish_check.py`

## 5. Implementation Steps

- **S1:** Record pre-split baselines: generate `tests/golden/workflow-public-names.txt` from the current module and add `tests/test_package.py` with the names test (FR-3, AC-6); copy `tests/golden/` aside for the byte comparison (AC-1); measure startup medians of `workflow.py --version` and the hook entry (EC-6, AC-7); record the privacy scan result (AC-4).
- **S2:** Create the package with `__init__`, `errors`, `constants` (with recomputed paths) and `infra/` (text, secrets, git); `workflow.py` imports them; full suite (FR-1, FR-5, EC-3).
- **S3:** Move `records/markdown`, `store/config`, `store/state`, `records/parsers`; full suite (FR-1, FR-6).
- **S4:** Move `core/spec`, `core/gates`, `core/checks`, `core/outcome`, `adapters/detect`, `core/setup`; full suite (FR-1, FR-6).
- **S5:** Move `cli/helpers`, `agents/claude_hooks`, `cli/commands`, `cli/main`; reduce `workflow.py` to the entry point; full suite on 3.13 and 3.9, golden byte comparison (FR-2, FR-4, EC-1, EC-5, EC-7).
- **S6:** Add the remaining tests in `tests/test_package.py`: each module imports cleanly in a fresh interpreter and only from lower layers (AC-5), `TEMPLATES_DIR` value (EC-3), install round trip into a temporary home with `doctor` and `--version` (AC-3, EC-4); run ruff, mypy, privacy scan (AC-2, AC-4); re-measure startup (AC-7); README layout note.

## 6. Important Technical Decisions

- **Pure moves along existing sections** rather than redesigning modules now: behaviour preservation is provable
  section by section, and design improvements (API, gate table) are separate approved features.
- **Re-export everything public from `workflow.py`** (instead of only the names tests use today): external scripts
  may import engine names; the recorded names list makes the contract explicit and testable.
- **`sys.path` insertion in `workflow.py`** rather than relative imports: the file is run as a script and loaded by
  path; a package-relative import would fail in both cases.
- **Detection goes to `adapters/detect.py`** now, so E1.2 replaces it in place instead of moving it twice.

## 7. Edge Cases

- EC-1: the existing script-entry test runs `workflow.py` by absolute path from the fixture repository.
- EC-2: `tools/prepublish_check.py` runs unchanged; result compared with the S1 baseline.
- EC-3: `TEMPLATES_DIR` test; `new` copies record templates in many existing tests (a wrong path fails them).
- EC-4: install round-trip test with `AI_DEV_WORKFLOW_HOME` and a temporary `HOME`.
- EC-5: `sys.path.insert(0, …)` in `workflow.py`; checked by the layer test running from another directory.
- EC-6: medians of 10 runs before and after; >50 ms slower → audit finding.
- EC-7: the two patching tests stay unchanged and must pass.

## 8. Testing Plan

| Item | Proven by |
|---|---|
| AC-1 | `unit` and `unit-py39` checks; byte comparison of `tests/golden/` with the S1 copy |
| AC-2 | ad-hoc `ruff` and `mypy` checks |
| AC-3 | install round-trip test in `tests/test_package.py` |
| AC-4 | `privacy` check result equal to the S1 baseline (same file count, no findings) |
| AC-5 | layer/cycle test in `tests/test_package.py` |
| AC-6 | names test against `workflow-public-names.txt`; inspection that `workflow.py` has no engine logic |
| AC-7 | timing measurements recorded in verification.md |
| EC-1–EC-7 | as listed in section 7 |
| DW-1–DW-5 | the items above; CI after the owner pushes; README review |

## 9. Risks and Dependencies

- Hidden cross-section references could create an import cycle; mitigated by moving lowest layers first and the
  layer test; if a function must move to break a cycle, it is a pure move recorded in the report.
- Large diff to review; DEP-1 (commit F1.0.2 first) keeps it readable.
- Ubuntu/Windows verification only after the owner pushes (Not Verified until then).

## 10. Expected Result

`workflow.py` is a short entry point; the engine lives in about 20 focused modules; all tests, golden outputs, tools,
hooks and installs behave exactly as before; E1.1–E1.3 can add detection, adapters and parsers in their own modules.
