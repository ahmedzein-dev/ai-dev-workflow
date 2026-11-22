# Verification: F1.0.4 Engine API: commands return data, the CLI only prints

## Check runs

Written by `workflow.py run`; do not edit between the markers.

<!-- aidw:checks:start -->
| Check | Status | Summary | Code fingerprint | When | Agent |
|---|---|---|---|---|---|
| golden-byte-compare | passed | pre-existing golden files: 9 differences: [] new: 5 | `23f78e988f` | 2026-11-22T09:00:10Z | claude-code |
| mypy | passed | Success: no issues found in 31 source files | `23f78e988f` | 2026-11-22T09:00:10Z | claude-code |
| privacy | passed | Scanned 199 files: no findings. | `23f78e988f` | 2026-11-22T08:59:23Z | claude-code |
| ruff | passed | All checks passed! | `23f78e988f` | 2026-11-22T09:00:10Z | claude-code |
| startup-timing | passed | after: --version 63.1 ms (before 61.2), hook 62.7 ms (before 60.9) | `23f78e988f` | 2026-11-22T09:00:11Z | claude-code |
| unit | passed | OK | `23f78e988f` | 2026-11-22T08:58:21Z | claude-code |
| unit-py39 | passed | OK | `23f78e988f` | 2026-11-22T08:59:23Z | claude-code |
<!-- aidw:checks:end -->

## Acceptance matrix

One row for every AC and EC in the approved spec and every "Done when" item, numbered DW-1, DW-2, … in
order. Status is Passed, Failed, Blocked or Not Verified. Evidence names the test, command or inspection;
for Blocked and Not Verified it says why. A check that did not run is never Passed.

| Item | Status | Evidence |
|------|--------|----------|
| AC-1 | Passed | check `unit` (173 tests: 156 pre-existing unchanged, 5 behaviour pins, 12 API tests) and `unit-py39` on code 23f78e988f; check `golden-byte-compare`: the 9 pre-existing files in tests/golden/ are byte-identical to the copy taken in S1 |
| AC-2 | Passed | checks `ruff` and `mypy` (31 files) |
| AC-3 | Passed | `test_api.SeparationTest.test_cli_modules_write_no_records`: writer imports, bare and attribute calls (`api.x`), and calls to names `aidw.api` only imports; shown to flag the pre-refactor `cli/commands.py` and, after the audit (F-3), the first implementation's wrapper call |
| AC-4 | Passed | `test_api.ApiLifecycleTest.test_api_only_lifecycle_matches_the_cli`: setup to close through the API only, no output, normalised state.json and the spec, plan, dependencies, audit, report and approved snapshots byte-identical to the CLI-driven repository |
| AC-5 | Passed | `test_api.JsonParityTest`: values and raw text (key order and formatting) for status (list and task), spec-check, plan-check, scope (exactly seven keys), check (with and without errors), outcome, init --discover; preflight: its three keys |
| AC-6 | Passed | `test_package` layer, cycle and public-names tests with api=4, agents/cli=5; `test_api.SeparationTest.test_hooks_import_nothing_from_the_cli` |
| AC-7 | Passed | check `startup-timing` on 23f78e988f: `--version` 61.2 → 63.1 ms, hook 60.9 → 62.7 ms (median of 15) |
| AC-8 | Passed | `test_behaviour_pins.RefusalsTest`: 27 refusal scenarios (17 from S1, 10 added after the audit, F-8), all recorded from the pre-refactor engine 5a7576a and passing there with Python 3.13 and 3.9 (exit code, stdout, stderr, normalised); every file under .ai-dev-workflow/ compared byte for byte before and after inside each run |
| AC-9 | Passed | `test_api.NoHiddenStateTest.test_alternating_repositories_in_one_process`: two repositories, working directory unchanged, nothing on Python streams or file descriptors 1/2 (shown to catch a child-process write), AI_DEV_WORKFLOW_AGENT ignored by the API |
| AC-10 | Passed | `test_behaviour_pins.SignaturesTest` against tests/golden/workflow-public-signatures.txt recorded in S1 (includes the wrappers resolve_template, update_setup, ensure_commit_mode) |
| AC-11 | Passed | `test_behaviour_pins.PreflightJsonTest`: both outputs recorded in S1 are byte-identical after the refactor |
| AC-12 | Passed | `test_api.SeparationTest.test_lower_layers_never_print_exit_change_directory_or_read_argv` (api, core, adapters, store, records, infra, constants, errors); the core print in `ensure_commit_mode` removed |
| EC-1 | Passed | refusal golden test (27 scenarios, including exit-3 paths) and the spaces-path equivalence test (audit F-2) |
| EC-2 | Passed | existing scenario tests of `run` unchanged and passing; `ApiLifecycleTest` asserts `output_tail`; `LateRefusalTest`: the output printed before a refusal that comes after the command ran, pinned from 5a7576a (audit F-1; fails on cea2e9f, passes now) |
| EC-3 | Passed | existing tests for spec-check/plan-check/preflight/check/run exit code 1, all passing |
| EC-4 | Passed | existing review, resume and blocked-plan tests, all passing; spec-check/plan-check golden files unchanged |
| EC-5 | Passed | existing status tests and JSON parity (not set up) |
| EC-6 | Passed | existing hook tests passing; hook import test |
| EC-7 | Passed | two-repository test (AC-9) and the lifecycle test inside `no_output` |
| EC-8 | Passed | check `startup-timing` (AC-7) |
| EC-9 | Passed | `PreflightJsonTest` (AC-11) |
| EC-10 | Passed | `test_api.CommitModeNoticeTest`: notice printed before "Created task …", and kept on stdout when a later check refuses |
| DW-1 | Passed | FR-1–FR-12 covered by AC-1–AC-12 above |
| DW-2 | Passed | EC-1–EC-10 above |
| DW-3 | Passed | checks `unit`, `unit-py39`, `privacy`, `ruff`, `mypy` on code 23f78e988f |
| DW-4 | Not Verified | CI runs after the push; recorded here when it has run |
| DW-5 | Passed | TD-24 in docs/roadmap/TECHNICAL_DEBT.md (committed in 5a7576a) |
| DW-6 | Passed | README "Development" section describes the internal API layer |

## Behavioral checks

- Full lifecycle through the CLI (existing tests) and through the API only (new test), compared record by record.
- 27 refusals and the output of a late `run` refusal pinned from the pre-refactor engine (5a7576a); preflight --json quirk (TD-24) pinned in two scenarios.
- Records commit-mode notice in a fresh clone, including a refusal after it was applied.
- Hooks (existing tests), install round trips and project-copy cleanliness (test_package) unchanged.

## CI failure on Windows (first run) and root cause

- **Run:** `tests` workflow on cea2e9f: Linux and macOS passed (Python 3.9, 3.13), lint passed; **Windows failed on both
  Python versions** with one error in `test_api.NoHiddenStateTest.test_alternating_repositories_in_one_process`:
  `PermissionError: [WinError 32] The process cannot access the file because it is being used by another process:
  '…\aidw-test-…\elsewhere'`.
- **Root cause:** a test defect, not an engine defect. The test changed the working directory into a temporary folder
  and restored it with `addCleanup`. unittest runs cleanups after `tearDown`, and `tearDown` deletes the temporary
  folder first; Windows cannot delete the current directory.
- **Fix (test only):** the working directory is restored in `try/finally` inside the test, before `tearDown`, also
  when an assertion or exception occurs. No production code and no assertion changed; the repository-isolation and
  file-descriptor checks are kept.
- **Also found in FIXING:** the new late-refusal pin passed `--repo` after the positionals, which Python 3.9's argparse
  reads as part of the extra command. Fixed by putting `--repo` first. The pinned output is unchanged; verified on the
  pre-refactor engine with Python 3.13 and 3.9.

## CI failure on Windows (second run) and root cause

- **Run:** `tests` workflow on b2f5b8e: Linux, macOS and lint passed; Windows failed on both Python versions with two
  failures.
- **`test_an_empty_repository_path_is_refused`:** the first F-2 fix made the API pass a path of spaces to `find_repo`.
  On Windows, `pathlib` turns a path of spaces into the current directory, so the API silently used the working
  directory (against FR-9) and the test's refusal did not happen. **Fix (production, audit F-2 refined):** the API
  refuses an empty path or a path of spaces again; the CLI resolves a `--repo` of spaces itself through `find_repo`,
  exactly as before F1.0.4 on every platform. The test's assertions are unchanged; a message check was added (re-audit
  N-2).
- **`LateRefusalTest`:** the extra command `python -c "print('…')"` cannot be parsed on Windows (quoting of extra
  commands there is a pre-existing limitation of the engine, the same before and after F1.0.4). **Fix (test only):** the
  command runs a script file instead; the pinned output was regenerated from the pre-refactor engine and is byte-
  identical to the earlier golden.

## Limitations

- CI on Linux, Windows and macOS (DW-4) runs after the push.
- Signature compatibility covers parameter names, kinds and defaults; annotations are not compared (their text differs between Python versions).
