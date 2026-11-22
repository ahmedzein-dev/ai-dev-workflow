# Verification: F1.0.3 Split workflow.py into the aidw package (no behaviour change)

## Check runs

Written by `workflow.py run`; do not edit between the markers.

<!-- aidw:checks:start -->
| Check | Status | Summary | Code fingerprint | When | Agent |
|---|---|---|---|---|---|
| golden-byte-compare | passed |  | `9b5f860b53` | 2026-11-21T23:52:35Z | claude-code |
| mypy | passed | Success: no issues found in 30 source files | `9b5f860b53` | 2026-11-21T23:51:59Z | claude-code |
| prepublish-loads-engine | passed | Scanned 167 files: no findings. | `9b5f860b53` | 2026-11-21T23:52:35Z | claude-code |
| privacy | passed | Scanned 167 files: no findings. | `9b5f860b53` | 2026-11-21T23:51:58Z | claude-code |
| ruff | passed | All checks passed! | `9b5f860b53` | 2026-11-21T23:51:59Z | claude-code |
| startup-timing | passed | version 61.5 ms \| hook 62.8 ms | `9b5f860b53` | 2026-11-21T23:52:35Z | claude-code |
| unit | passed | OK | `9b5f860b53` | 2026-11-21T23:51:11Z | claude-code |
| unit-py39 | passed | OK | `9b5f860b53` | 2026-11-21T23:51:59Z | claude-code |
<!-- aidw:checks:end -->

## Acceptance matrix

One row for every AC and EC in the approved spec and every "Done when" item, numbered DW-1, DW-2, … in
order. Status is Passed, Failed, Blocked or Not Verified. Evidence names the test, command or inspection;
for Blocked and Not Verified it says why. A check that did not run is never Passed.

| Item | Status | Evidence |
|------|--------|----------|
| AC-1 | Passed | checks `unit` (156 tests: 147 existing + 9 new, Python 3.13) and `unit-py39` (Python 3.9.6) passed on code 9b5f860b53; check `golden-byte-compare`: every pre-split golden file byte-identical |
| AC-2 | Passed | checks `ruff` (all passed) and `mypy` (no issues in 30 source files) |
| AC-3 | Passed | `InstalledCopyTest`: user install into a temporary home copies `aidw/`, the installed `workflow.py --version` matches, `doctor` prints "No problems found"; `ProjectInstallTest` does the same for project copies |
| AC-4 | Passed | check `prepublish-loads-engine`: tools/prepublish_check.py loads workflow.py by path and scans 167 files with no findings (140 before + 27 new files) |
| AC-5 | Passed | `PackageStructureTest`: each of the 27 import units (19 modules, 8 packages) imports first in a fresh interpreter; imports stay within their own layer or lower (5 layer levels across 7 subpackages); no cycles |
| AC-6 | Passed | `PublicNamesTest`: all 198 names recorded before the split importable; `test_entry_point_holds_no_engine_logic`: workflow.py has no function or class definitions |
| AC-7 | Passed | check `startup-timing` (bytecode writing allowed by the environment, disabled by the engine) and the S1 baseline: `--version` 58.3 → 61.5 ms, hook 57.6 → 62.8 ms (median of 15 runs, macOS) |
| EC-1 | Passed | `ScriptEntryTest` runs workflow.py by absolute path from the fixture repository; `InstalledCopyTest` runs the installed copy from the temporary home |
| EC-2 | Passed | check `prepublish-loads-engine` (spec_from_file_location under the name aidw_workflow) |
| EC-3 | Passed | `test_template_folder_still_resolves_to_the_skill_assets`; every `new` in the existing tests copies record templates |
| EC-4 | Passed | `InstalledCopyTest` (user canonical copy) and `ProjectInstallTest` (both project copies): `aidw/` copied, `__pycache__` excluded, the copies run, and after running them no bytecode appears in the copies or in `git status` (audit F-1 fixed with `sys.dont_write_bytecode`) |
| EC-5 | Passed | `ShadowingTest`: with a fake `aidw` package first on `PYTHONPATH`, `workflow.py --version` still reports the bundled version |
| EC-6 | Passed | startup grew by 3.2 ms and 5.2 ms, below the 50 ms finding threshold |
| EC-7 | Passed | the existing tests patching `workflow.locale.getpreferredencoding` and `workflow.shutil.which` pass unchanged; `test_patched_standard_modules_are_the_real_ones` |
| DW-1 | Passed | FR-1–FR-8 implemented (19 modules in 7 subpackages, 5 layer levels; entry point without engine logic) |
| DW-2 | Passed | EC-1–EC-7 handled as above |
| DW-3 | Passed | checks `unit`, `unit-py39`, `privacy`, `ruff`, `mypy` passed on the current code |
| DW-4 | Not Verified | CI (three operating systems, lint job) runs only after the owner pushes the branch |
| DW-5 | Passed | README "Development" describes the package layers |

## Behavioral checks

- The 147 existing tests (incl. golden and script-entry tests) plus 9 new package tests pass on Python 3.13 and 3.9.
- Code moved verbatim by a deterministic script (contiguous source lines per top-level statement); only module headers, imports and the `SKILL_DIR` expression changed. The managing engine (v1.0.0 install) was not touched.

## Limitations

- Windows and Ubuntu runs and the CI lint job: only after the owner pushes the branch (DW-4).
- Startup timing measured on macOS only.
