# Verification: F1.0.2 Dev tooling: ruff, mypy and golden CLI outputs

## Check runs

Written by `workflow.py run`; do not edit between the markers.

<!-- aidw:checks:start -->
| Check | Status | Summary | Code fingerprint | When | Agent |
|---|---|---|---|---|---|
| ec6-missing-tool | blocked | Could not run: 'aidw-tool-that-does-not-exist' was not found on PATH. | `1705ed3d78` | 2026-11-21T22:37:50Z | claude-code |
| golden-ac5-ac6 | passed | OK | `1705ed3d78` | 2026-11-21T22:37:41Z | claude-code |
| golden-narrow-terminal | passed | OK | `1705ed3d78` | 2026-11-21T22:37:47Z | claude-code |
| mypy | passed | Success: no issues found in 3 source files | `1705ed3d78` | 2026-11-21T22:37:07Z | claude-code |
| privacy | passed | Scanned 113 files: no findings. | `1705ed3d78` | 2026-11-21T22:37:06Z | claude-code |
| ruff | passed | All checks passed! | `1705ed3d78` | 2026-11-21T22:37:07Z | claude-code |
| unit | passed | OK | `1705ed3d78` | 2026-11-21T22:36:20Z | claude-code |
| unit-py39 | passed | OK | `1705ed3d78` | 2026-11-21T22:37:07Z | claude-code |
<!-- aidw:checks:end -->

## Acceptance matrix

One row for every AC and EC in the approved spec and every "Done when" item, numbered DW-1, DW-2, … in
order. Status is Passed, Failed, Blocked or Not Verified. Evidence names the test, command or inspection;
for Blocked and Not Verified it says why. A check that did not run is never Passed.

| Item | Status | Evidence |
|------|--------|----------|
| AC-1 | Passed | check `ruff` passed on code 1705ed3d78 (ruff 0.17.6, macOS) |
| AC-2 | Passed | check `mypy` passed on code 1705ed3d78 (mypy 1.20.2, target 3.9) |
| AC-3 | Not Verified | the `lint` job is added and the workflow file parses (jobs: test, lint), but CI runs only after the owner pushes |
| AC-4 | Not Verified | macOS passes with Python 3.13 (check `unit`) and 3.9 (check `unit-py39`); Ubuntu and Windows run only in CI after the owner pushes |
| AC-5 | Passed | check `golden-ac5-ac6`: a one-word change to the outcome message failed the golden tests with a diff showing the old and new line (run on a temporary copy) |
| AC-6 | Passed | check `golden-ac5-ac6`: update mode rewrote every golden file and passed; normal and failing runs wrote nothing |
| AC-7 | Passed | golden files were first recorded in S1 on the unchanged engine and passed without regeneration after the S3 lint edits; they were regenerated once in FIXING (EC-5), so the proof of no output change is the independent audit: the current golden files pass against a `git archive HEAD` copy of the pre-edit engine on Python 3.13 and 3.9; `unit` passes (147 tests) |
| EC-1 | Passed | check `unit-py39` (Python 3.9.6): golden help tests pass with the options-heading and usage-wrapping normalization |
| EC-2 | Passed | check `golden-narrow-terminal` (COLUMNS=40) passed; the tests force COLUMNS=100 |
| EC-3 | Not Verified | path and line-ending normalization is in place, but no Windows run is possible here; verified by the Windows CI jobs after the owner pushes |
| EC-4 | Passed | manual run with tests/golden/outcome.txt removed: failed with "Golden file tests/golden/outcome.txt is missing. Create it … AIDW_UPDATE_GOLDEN=1 …"; no file was written |
| EC-5 | Passed | fixed in FIXING: the discovery scenario has a Makefile test target; tests/golden/init-discover.json holds "tool_found": "<TOOL_FOUND>" and the test asserts the field exists |
| EC-6 | Passed | check `ec6-missing-tool`: a missing executable is recorded as blocked ("was not found on PATH"), not passed |
| EC-7 | Passed | all 18 mypy findings fixed without behaviour change; no `type: ignore` in scripts/ or tools/ (grep: 0); `warn_unused_ignores = true` in pyproject.toml |
| DW-1 | Passed | FR-1–FR-8 implemented: pyproject.toml, requirements-dev.txt, lint job, tests/test_golden.py with tests/golden/, lint-only edits |
| DW-2 | Not Verified | every edge case's handling is implemented, but EC-3 (Windows) can be verified only by CI after the owner pushes |
| DW-3 | Passed | checks `unit` (147 tests incl. the script-entry smoke test), `privacy`, `ruff`, `mypy` passed on the current code; DEP-1 was granted, so nothing was blocked |
| DW-4 | Not Verified | needs a push by the owner; GitHub Actions has not run this change |
| DW-5 | Passed | README "Development" lists the dev install, ruff, mypy and the golden regeneration command |

## Behavioral checks

- Full existing suite (141 tests) plus 6 new tests (5 golden, 1 script-entry smoke test) pass on Python 3.13 and 3.9.
- `workflow.py` behaviour unchanged: renames and annotations only (`git diff` on workflow.py: digest→hasher, line→lineno, result→spec_result, list annotations, `typing.cast`), reviewed hunk by hunk in the independent audit and covered by the existing suite; the golden outputs cover the help and key command outputs but not every renamed path (for example the rule-scan branch).
- The managing engine (v1.0.0 install) was not touched; the edits are in the working copy only.

## Limitations

- GitHub Actions (AC-3, DW-4) and Ubuntu/Windows runs (AC-4, EC-3) need the owner to push; nothing is pushed or committed by the agent.
- Deviation from the plan: mypy is pinned to 1.20.2, not the latest (2.4.1), because 2.4.1 refused `python_version = 3.9` locally ("must be 3.10 or higher"), which FR-3 requires.
- Normalization added beyond FR-6's list: each argparse `usage:` block is compared as one line, because Python 3.9 and 3.13 wrap usage lines at different points (EC-1). Wrap-only changes inside usage lines are therefore not detected.
- The `<TMP>` and `<PY>` normalizations are in place but no current golden output contains those values.
