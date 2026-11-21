# Final Report: F1.0.2 Dev tooling: ruff, mypy and golden CLI outputs

## 1. Overall Status

**Status:** Completed with Limitations

Everything was implemented and verified locally on macOS with Python 3.13 and 3.9. It is not Completed because the
CI `lint` job and the Ubuntu and Windows runs (AC-3, AC-4, EC-3, DW-2, DW-4) can only run after the owner pushes;
nothing was pushed or committed.

## 2. What Was Implemented

- `pyproject.toml` (tool configuration only: ruff default rules, mypy targeting Python 3.9) and `requirements-dev.txt`
  (ruff 0.17.6, mypy 1.20.2, exact pins).
- `tests/test_golden.py` with eight golden files in `tests/golden/`: help for every `workflow.py` and `install.py`
  command, plus `status`, `spec-check`, `plan-check`, `outcome` and `init --discover --json` for a fixed scenario,
  with normalization and the `AIDW_UPDATE_GOLDEN=1` regeneration switch; plus a script-entry smoke test.
- Lint-only fixes: 2 unused imports, 18 mypy findings fixed by renames, annotations and `typing.cast`; no
  `type: ignore` needed.
- CI `lint` job; README "Development" section.

## 3. Specification Compliance

Matches spec v1 (6415e7ce) and plan v1 (e0647c97). Not Verified: AC-3, AC-4 (Ubuntu/Windows part), EC-3, DW-2,
DW-4 — all waiting for CI. Deviations: mypy pinned to 1.20.2 instead of the latest because 2.4.1 refused
`python_version = 3.9` locally; usage-line normalization added for Python-version wrapping differences (EC-1).

## 4. Testing Results

On code 1705ed3d78: `unit` 147 tests passed (Python 3.13), `unit-py39` passed (Python 3.9.6), `privacy` passed (113
files), `ruff` passed, `mypy` passed, `golden-ac5-ac6` passed (mutation detected with a diff; update switch writes only
when set), `golden-narrow-terminal` passed. `ec6-missing-tool` was recorded as blocked on purpose to show that a
missing tool is never reported as passed.

## 5. Code Audit

Independent read-only subagent review: no Critical or Important findings; eight Minor findings (evidence wording,
test polish, a script-entry test gap, Windows README paths), all fixed and re-verified. The reviewer confirmed that the
golden files match the unmodified HEAD engine on Python 3.13 and 3.9.

## 6. Edge Cases and Regression Risks

Golden tests cannot detect wrap-only changes inside argparse usage lines, and do not cover every renamed code path
(for example the rule-scan branch); those rely on the existing suite. Argparse patch-level differences on CI's
Python versions could require one more normalization; any such change will be reported, not hidden.

## 7. Pending Dependencies

The owner's push (or a pull request) to run GitHub Actions; until then AC-3, AC-4 (Ubuntu/Windows), EC-3, DW-2 and DW-4
stay Not Verified.

## 8. Next Actions

- After the first push: check the `lint` job and the six test jobs; normalize any new Python-version difference if one
  appears.
- Follow-up proposal: add `ruff` and `mypy` as required checks in `.ai-dev-workflow/config.json` (a setup change for
  the owner to approve).
- Next feature: F1.0.3 (split `workflow.py` into the `aidw/` package), now protected by golden and script-entry tests.
