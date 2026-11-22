# Verification: F1.0.4 Engine API: commands return data, the CLI only prints

## Check runs

Written by `workflow.py run`; do not edit between the markers.

<!-- aidw:checks:start -->
| Check | Status | Summary | Code fingerprint | When | Agent |
|---|---|---|---|---|---|
| golden-byte-compare | passed | pre-existing golden files: 9 differences: [] new: ['preflight-json-analyzer-hint.txt', 'preflight-json-unattributed.txt', 'refusals.json', 'workflow-public-signatures.txt'] | `fd8d5e06a3` | 2026-11-22T08:26:36Z | claude-code |
| mypy | passed | Success: no issues found in 31 source files | `fd8d5e06a3` | 2026-11-22T08:26:36Z | claude-code |
| privacy | passed | Scanned 198 files: no findings. | `fd8d5e06a3` | 2026-11-22T08:25:51Z | claude-code |
| ruff | passed | All checks passed! | `fd8d5e06a3` | 2026-11-22T08:26:35Z | claude-code |
| startup-timing | passed | after: --version 62.7 ms (before 61.2), hook 61.8 ms (before 60.9) | `fd8d5e06a3` | 2026-11-22T08:26:45Z | claude-code |
| unit | passed | OK | `fd8d5e06a3` | 2026-11-22T08:24:52Z | claude-code |
| unit-py39 | passed | OK | `fd8d5e06a3` | 2026-11-22T08:25:51Z | claude-code |
<!-- aidw:checks:end -->

## Acceptance matrix

One row for every AC and EC in the approved spec and every "Done when" item, numbered DW-1, DW-2, … in
order. Status is Passed, Failed, Blocked or Not Verified. Evidence names the test, command or inspection;
for Blocked and Not Verified it says why. A check that did not run is never Passed.

| Item | Status | Evidence |
|------|--------|----------|
| AC-1 | Passed | check `unit` (170 tests: 156 pre-existing unchanged, 4 behaviour pins, 10 API tests) and `unit-py39`; check `golden-byte-compare`: the 9 pre-existing files in tests/golden/ are byte-identical to the copy taken in S1 |
| AC-2 | Passed | checks `ruff` and `mypy` (31 files) |
| AC-3 | Passed | `test_api.SeparationTest.test_cli_modules_write_no_records`; shown to flag 10 writer imports in the pre-refactor `cli/commands.py` |
| AC-4 | Passed | `test_api.ApiLifecycleTest.test_api_only_lifecycle_matches_the_cli`: setup to close through the API only, no output, normalised state.json and the spec, plan, dependencies, audit, report and approved snapshots byte-identical to the CLI-driven repository |
| AC-5 | Passed | `test_api.JsonParityTest` for status (list and task), spec-check, plan-check, scope (exactly seven keys), check, outcome, init --discover; preflight: its three keys |
| AC-6 | Passed | `test_package` layer, cycle and public-names tests with api=4, agents/cli=5; `test_api.SeparationTest.test_hooks_import_nothing_from_the_cli` |
| AC-7 | Passed | check `startup-timing`: `--version` 61.2 → 62.7 ms, hook 60.9 → 61.8 ms (median of 15; also 63.0/62.2 ms in an earlier run) |
| AC-8 | Passed | `test_behaviour_pins.RefusalsTest`: 17 refusal scenarios recorded from the unchanged engine in S1 (exit code, stdout, stderr, normalised); every file under .ai-dev-workflow/ compared byte for byte before and after inside each run |
| AC-9 | Passed | `test_api.NoHiddenStateTest.test_alternating_repositories_in_one_process`: two repositories, working directory unchanged, nothing on Python streams or file descriptors 1/2 (shown to catch a child-process write), AI_DEV_WORKFLOW_AGENT ignored by the API |
| AC-10 | Passed | `test_behaviour_pins.SignaturesTest` against tests/golden/workflow-public-signatures.txt recorded in S1 (includes the wrappers resolve_template, update_setup, ensure_commit_mode) |
| AC-11 | Passed | `test_behaviour_pins.PreflightJsonTest`: both outputs recorded in S1 are byte-identical after the refactor |
| AC-12 | Passed | `test_api.SeparationTest.test_lower_layers_never_print_exit_change_directory_or_read_argv` (api, core, adapters, store, records, infra, constants, errors); the core print in `ensure_commit_mode` removed |
| EC-1 | Passed | refusal golden test (17 scenarios) |
| EC-2 | Passed | existing scenario tests of `run` (output tail, failures, redaction) unchanged and passing; `ApiLifecycleTest` asserts `output_tail` |
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
| DW-3 | Passed | checks `unit`, `unit-py39`, `privacy`, `ruff`, `mypy` on code fd8d5e06a3 |
| DW-4 | Not Verified | CI runs after the push; recorded here when it has run |
| DW-5 | Passed | TD-24 in docs/roadmap/TECHNICAL_DEBT.md (committed in 5a7576a) |
| DW-6 | Passed | README "Development" section describes the internal API layer |

## Behavioral checks

- Full lifecycle through the CLI (existing tests) and through the API only (new test), compared record by record.
- 17 refusals pinned from the pre-refactor engine; preflight --json quirk (TD-24) pinned in two scenarios.
- Records commit-mode notice in a fresh clone, including a refusal after it was applied.
- Hooks (existing tests), install round trips and project-copy cleanliness (test_package) unchanged.

## Limitations

- CI on Linux, Windows and macOS (DW-4) runs after the push.
- Signature compatibility covers parameter names, kinds and defaults; annotations are not compared (their text differs between Python versions).
