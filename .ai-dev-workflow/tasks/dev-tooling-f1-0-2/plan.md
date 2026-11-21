# Implementation Plan: F1.0.2 Dev tooling: ruff, mypy and golden CLI outputs

> Spec: v1 · 6415e7ce
> Frozen once approved. Progress is recorded with `workflow.py step`, never by editing this plan.

## 1. Goal

Add dev-only lint and type checks and golden CLI output tests, so the F1.0.3 module split can prove it changed no
behaviour.

## 2. Current Behavior

- No linter or type checker is configured anywhere in the repository (TD-17); `README.md` "Development" lists only
  `python3 -m unittest` and `tools/prepublish_check.py`.
- Tests drive the engine in-process through `workflow.main()` with an isolated `AI_DEV_WORKFLOW_HOME`
  (`tests/helpers.py`, `WorkflowTestCase.wf`), and the helpers already build a full scenario
  (`to_implementation`, `implement_and_test`, `FILLED_SPEC`, `FILLED_PLAN`).
- CI (`.github/workflows/tests.yml`) runs one `test` job over Ubuntu, macOS and Windows × Python 3.9 and 3.13, then
  the privacy scan.
- No test pins CLI output text; a refactor could change messages or help without failing anything.

## 3. Proposed Solution

1. **Golden tests first, on the unchanged engine.** `tests/test_golden.py` subclasses `WorkflowTestCase`, runs a
   fixed scenario with the existing helpers, captures stdout+stderr of the listed commands, normalizes them
   (`<TMP>`, `<TIME>`, `<PY>`, `<TOOL_FOUND>`, LF endings, "optional arguments:" → "options:") with `COLUMNS=100`,
   and compares with `tests/golden/<name>.txt`. `AIDW_UPDATE_GOLDEN=1` rewrites the files. Recording them before
   any lint edit is what makes FR-8 provable.
2. **Tool configuration** in a repo-root `pyproject.toml` (sections `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.mypy]`
   only) and `requirements-dev.txt` with exact pins of the latest stable ruff and mypy at implementation time.
   Locally they run from a git-ignored `.venv/` (`.venv/` is already in `.gitignore`), only if DEP-1 is granted.
3. **Lint-only fixes**, then re-run the golden tests without regeneration (AC-7).
4. **CI `lint` job** next to the existing `test` job, in the same file and style.
5. **Evidence through the engine**: `unit` and `privacy` as configured checks; ruff and mypy as ad-hoc checks
   (`run <task> ruff -- .venv/bin/ruff check .`), so the project setup does not change in this task.

## 4. Affected Areas

- New: `pyproject.toml`, `requirements-dev.txt`, `tests/test_golden.py`, `tests/golden/*.txt`
- Changed: `.github/workflows/tests.yml` (new job), `README.md` (Development section)
- Possibly changed, lint-only: `skills/ai-dev-workflow/scripts/workflow.py`, `skills/ai-dev-workflow/scripts/install.py`,
  `tools/prepublish_check.py`, files under `tests/`

## 5. Implementation Steps

- **S1:** Add `tests/test_golden.py` (scenario, normalization, update switch, missing-file message) and generate
  `tests/golden/` on the unchanged engine; run the golden tests twice without regeneration to prove they are
  stable (FR-5, FR-6, FR-7, EC-1, EC-2, EC-3, EC-4, EC-5).
- **S2:** Add `pyproject.toml` and `requirements-dev.txt`; create `.venv/` and install the pinned tools if DEP-1 is
  granted (FR-1, FR-4, EC-6).
- **S3:** Run ruff and mypy; apply lint-only fixes; add reasoned `# type: ignore[<code>]` only where a fix would
  change behaviour; re-run the full suite and the golden tests without regeneration (FR-2, FR-3, FR-8, EC-7).
- **S4:** Add the `lint` job to `.github/workflows/tests.yml` (FR-4).
- **S5:** Update the README "Development" section with the dev install, ruff, mypy and golden-regeneration commands.

## 6. Important Technical Decisions

- **Golden files before lint edits** (rather than after): otherwise a lint edit that changed output would be baked
  into the baseline.
- **ruff default rules only** (E4, E7, E9, F): catches real defects (undefined names, unused imports, syntax issues)
  without style churn in a 3,458-line file just before it is split. More rules can be added after F1.0.3.
- **mypy non-strict on `scripts/` and `tools/`**, tests excluded for now: strict mode on untyped test code would
  create noise without protecting behaviour.
- **Ad-hoc engine checks for ruff and mypy** instead of editing `config.json`: changing the project's required
  checks is a setup decision for the owner; proposed as a follow-up once the tools are installed everywhere.
- **Normalize rather than skip** version-dependent help text, so help output stays protected on every Python version.

## 7. Edge Cases

- EC-1, EC-2: normalization of the help heading and `COLUMNS=100` in the test environment.
- EC-3: path and line-ending normalization; verified by the Windows CI jobs after the owner pushes.
- EC-4: explicit failure message with the file name and `AIDW_UPDATE_GOLDEN=1` hint; write only in update mode.
- EC-5: `tool_found` values replaced in the `init --discover --json` output.
- EC-6: without DEP-1, `run <task> ruff --blocked "ruff not installed: DEP-1 not granted"`; CI still runs it.
- EC-7: inline ignores with reasons, listed in `report.md`; `warn_unused_ignores = true`.
- If CI shows other Python-version differences in help output, they are normalized explicitly and the change is
  reported, never by deleting a golden case.

## 8. Testing Plan

| Item | Proven by |
|---|---|
| AC-1 | ad-hoc check `ruff` passing (local) and the CI `lint` job |
| AC-2 | ad-hoc check `mypy` passing (local) and the CI `lint` job |
| AC-3 | CI run after the owner pushes (Not Verified until then) |
| AC-4 | `unit` check locally (macOS, Python 3.13) + CI matrix after push |
| AC-5 | a temporary one-word change to a message, golden run fails with diff, change reverted (recorded in verification.md) |
| AC-6 | golden run with and without `AIDW_UPDATE_GOLDEN=1`, checking file modification times |
| AC-7 | golden files unchanged (`git diff --stat tests/golden/` empty) after S3, full `unit` check passing |
| EC-1–EC-7 | as listed in section 7 |
| DW-1–DW-5 | the items above, plus the `privacy` check and the README review |

## 9. Risks and Dependencies

- DEP-1 (local tool install) blocks only local ruff/mypy evidence; without it the outcome is at most Completed
  with Limitations.
- Unknown number of existing mypy findings; if fixing them needs behaviour changes, they are ignored with reasons
  and listed, not fixed (out of scope).
- AC-3 and the Windows/Linux part of AC-4 can only be verified after the owner pushes.

## 10. Expected Result

`ruff check .` and `mypy` pass; golden tests protect help and key command outputs on every OS and Python version
in CI; the engine's behaviour is unchanged; F1.0.3 can start with a safety net.
