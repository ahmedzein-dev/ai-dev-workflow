# Audit: F1.0.2 Dev tooling: ruff, mypy and golden CLI outputs

**Review independence:** subagent
**Reviewer:** Claude Code read-only general-purpose subagent (Opus 5.5), given the task folder and the list of changed files, not the implementer's summary
**Reviewed scope:** `git diff` of workflow.py, prepublish_check.py, test_scenarios.py, tests.yml, README.md; new pyproject.toml, requirements-dev.txt, tests/test_golden.py, tests/golden/*; approved spec v1 and plan v1; verification.md; state.json

## Dimensions

- **A. Specification compliance:** FR-1..FR-8 and EC-1..EC-7 implemented. AC-3, DW-4, EC-3 and the Ubuntu/Windows part of AC-4 are honestly Not Verified (need a push). Evidence wording issues F-1 and F-2 fixed.
- **B. Architecture compliance:** Nothing added to the skill folder; dev tooling stays at the repository root and in tests/, as the spec's constraints require.
- **C. Code quality:** Every edit to workflow.py and prepublish_check.py reviewed hunk by hunk: renames, annotations and `typing.cast` only (identity at runtime). Test polish items F-4..F-6 fixed.
- **D. Security and privacy:** No secrets; the privacy scan passes (113 files). Dev tools are pinned exactly and installed only in a git-ignored virtual environment.
- **E. Edge cases:** EC-5 initially not exercised; fixed during testing (Makefile fixture). All other cases covered by checks.
- **F. Regression risk:** The reviewer confirmed that the current golden files match the unmodified HEAD engine on Python 3.13 and 3.9. Gap F-7 (script entry point untested) closed with a smoke test before F1.0.3.
- **G. Test adequacy:** Golden tests cover help texts and key outputs; subTests now report every differing output; exit codes of `--help` are checked; the script entry point is tested.
- **H. Scope compliance:** All changed and new files are inside the approved plan's affected areas.
- **I. Reliability and performance:** Not affected (tests add about 2 seconds).

## Project standards checklist

No project standards files are configured. Spec constraints checked: standard library at runtime (yes), no change to commands, options, exit codes, messages or records (yes, golden-verified against HEAD), skill folder untouched except lint-only edits (yes).

## Findings

| ID | Severity | Dimension | Finding | Location | Disposition | Notes |
|----|----------|-----------|---------|----------|-------------|-------|
| F-1 | Minor | A | AC-7 evidence said the golden files were unchanged since S1, but they were regenerated once during FIXING | verification.md AC-7 | Fixed | Evidence now cites the reviewer's HEAD-engine comparison |
| F-2 | Minor | A | DW-2 marked Passed although EC-3 is only verifiable in CI; behaviour-neutrality was attributed to golden outputs that do not cover every renamed path | verification.md DW-2, Behavioral checks | Fixed | DW-2 now Not Verified; wording corrected |
| F-3 | Minor | C | Usage-line normalization not listed among deviations; hides wrap-only changes in usage lines | tests/test_golden.py USAGE_RE | Fixed | Listed under Limitations in verification.md and in the report |
| F-4 | Minor | C | Unnecessary and misleading `# noqa: E402` comments | tests/test_golden.py imports | Fixed | Replaced with an explanatory comment |
| F-5 | Minor | C | Four golden assertions in one test: the first mismatch hides the others | tests/test_golden.py | Fixed | subTest per golden output |
| F-6 | Minor | C | `capture()` ignored the exit code of `--help` | tests/test_golden.py capture | Fixed | Exit code checked (expected 0) |
| F-7 | Minor | F | No test runs workflow.py or install.py as a script, which the F1.0.3 split could break | tests/ | Fixed | New ScriptEntryTest: `--version`, `--help` equality with in-process output, `status` |
| F-8 | Minor | D | README dev commands showed POSIX venv paths only | README.md Development | Fixed | Windows path added |

## Remediation log

FIXING after the audit (reason recorded in state.json): test_golden.py (F-4..F-7), README.md (F-8), verification.md wording (F-1..F-3). Golden files compared before and after: unchanged. Re-run on code 1705ed3d78: `unit` (147 tests) passed, `unit-py39` passed, `privacy` passed (113 files), `ruff` passed, `mypy` passed, `golden-ac5-ac6` passed, `golden-narrow-terminal` passed, `ec6-missing-tool` blocked as expected.
