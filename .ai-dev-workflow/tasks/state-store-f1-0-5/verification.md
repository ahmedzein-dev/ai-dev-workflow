# Verification: F1.0.5 State Store Reliability

## Check runs

Written by `workflow.py run`; do not edit between the markers.

<!-- aidw:checks:start -->
| Check | Status | Summary | Code fingerprint | When | Agent |
|---|---|---|---|---|---|
| privacy | passed | Scanned 225 files: no findings. | `b04a1b47d1` | 2026-11-24T12:08:03Z | codex |
| unit | passed | OK | `b04a1b47d1` | 2026-11-24T06:36:50Z | codex |
<!-- aidw:checks:end -->

## Acceptance matrix

One row for every AC and EC in the approved spec and every "Done when" item, numbered DW-1, DW-2, … in
order. Status is Passed, Failed, Blocked or Not Verified. Evidence names the test, command or inspection;
for Blocked and Not Verified it says why. A check that did not run is never Passed.

| Item | Status | Evidence |
|------|--------|----------|
| AC-1 | Passed | `test_state_store.StateSchemaTest` loads v1.0.0 and optional-field fixtures without rewriting bytes; malformed schema, ID, shape and stage fixtures refuse. Full CI run below. |
| AC-2 | Passed | `MigrationTest.test_schema_one_preview_and_apply_without_converter_are_nonwriting` proves the production schema-1 no-op preview and refusal to apply without a converter. |
| AC-3 | Passed | `MigrationTest.test_test_only_converter_preview_apply_retry_and_rollback` checks dry-run, byte-exact backup, explicit apply, retry and rollback in an isolated repository. |
| AC-4 | Passed | Migration fault tests cover converter, backup, manifest and target-write failures, corrupt backup and rollback conflict; no real task migration was run. |
| AC-5 | Passed | `ConcurrentStoreTest` covers competing task writes, activation, Claude bindings and a delayed check with an intervening state edit. |
| AC-6 | Passed | `LockTest` covers live, dead, ambiguous, reused-owner and cross-process lock cases, stable acquisition order and bounded refusal. |
| AC-7 | Passed | `DurableWriteTest` and task-creation rollback tests cover pre/post replacement failures and conservative temp cleanup. Post-replace directory-sync fault injection is skipped on Windows because the operation is unavailable there; the platform limit is documented below. |
| AC-8 | Passed | `StateSchemaTest` malformed `ACTIVE` cases and Claude hook regression tests cover fail-closed behavior, valid sessions and inactive workflows. FIFO-specific case is skipped on Windows because FIFOs are unavailable there. |
| AC-9 | Passed | The final local 243-test suite includes all 36 development-branch TD-25 `test_secret_identity.py` cases, approval/CLI/hook compatibility and historical late-refusal golden tests. Only the CLI help golden changed from the pre-feature commit, to show `migrate`. |
| AC-10 | Passed | Final code fingerprint `b04a1b47d182d353c27ca0f465f67a54c0837ba341416cc42a87f8b667d413a1` passed local Python 3.9/3.13 243/243, official unit/privacy, Ruff 0.17.6 and Mypy 1.20.2 with zero diagnostics. Exact-source CI run `45390904437` passed six OS/Python jobs plus lint at `dd88e73140828eebffb373aa2492d0eac0acdf64`. The verified pre-feature Ruff/Mypy baseline at `a66a6070f40ecc6c6da6ee9e8303d94f43bbfe78` was zero diagnostics. Windows conditional skips and durability limit are below. |
| EC-1 | Passed | `test_existing_v100_record_loads_without_rewrite`, `test_missing_optional_fields_default_only_in_memory`. |
| EC-2 | Passed | `test_invalid_schema_and_shapes_refuse_without_write`, `test_bad_stage_and_status_do_not_echo_values`. |
| EC-3 | Passed | `test_invalid_schema_and_shapes_refuse_without_write`, `test_malformed_active_directory_and_task_id_fail_closed`. |
| EC-4 | Passed | `test_schema_one_preview_and_apply_without_converter_are_nonwriting`. |
| EC-5 | Passed | `test_conversion_and_backup_failures_preserve_source`, `test_manifest_and_target_write_failures_leave_original_state`. |
| EC-6 | Passed | `test_pre_replace_sync_failure_keeps_old_bytes_and_cleans_owned_temp`, `test_post_replace_sync_failure_reports_indeterminate_result`; latter is inapplicable on Windows because directory sync is unsupported. |
| EC-7 | Passed | `test_rollback_refuses_later_edits`, `test_corrupt_backup_refuses_rollback_without_touching_migrated_state`. |
| EC-8 | Passed | `test_two_process_writers_preserve_both_discoveries`, `test_delayed_check_does_not_overwrite_intervening_state`. |
| EC-9 | Passed | `test_competing_resumes_leave_one_active_task`, `test_competing_claude_bindings_keep_one_complete_session`. |
| EC-10 | Passed | `LockTest` live/crashed/ambiguous and Windows unknown-liveness branches plus `test_reused_pid_metadata_does_not_steal_a_lock` passed locally and in all six CI jobs. The new fixture represents a former owner whose PID now identifies an unrelated live process. |
| EC-11 | Passed | `test_only_known_dead_writer_temps_beside_a_valid_target_are_removed`, `test_next_locked_writes_clean_proven_state_and_active_orphans`. |
| EC-12 | Passed | `StateSchemaTest` malformed `ACTIVE` tests and existing Claude hook fail-closed regression tests. |
| EC-13 | Passed | All 36 development TD-25 `test_secret_identity.py` cases, including CLI/API/hook identity refusals, passed in both local 243-test suites and in all six CI jobs. |
| EC-14 | Passed | Both final Windows jobs passed file-flush/atomic-replace tests; directory-sync fault test was skipped there as unsupported, accurately described in `docs/usage.md`. |
| EC-15 | Passed | `test_test_only_converter_preview_apply_retry_and_rollback` checks no second conversion or backup overwrite on retry. |
| EC-16 | Passed | Same migration retry test checks dry-run inspection after apply rather than blind reapplication. |
| DW-1 | Passed | All S1–S8 plan steps recorded through the stable v1.0.1 engine; only isolated test-fixture migrations occurred. |
| DW-2 | Passed | Edge-case tests use temporary repositories and fixtures; the real project records were not migrated. |
| DW-3 | Passed | Final 243-test snapshot passed both local Python suites, Ruff, Mypy and privacy; exact-commit CI run `45390904437` passed all six matrix jobs plus lint. Windows conditional skips are listed below. |
| DW-4 | Passed | `docs/usage.md` explains preview, backup, rollback and durability limits; TD-29 and TD-30 remain separately tracked. |
| DW-5 | Passed | Independent read-only audit of code and all 31 acceptance rows on `dd88e73140828eebffb373aa2492d0eac0acdf64` issued GO after CI run `45390904437`; F-1 through F-3 were fixed and rechecked. See `audit.md`. |

## Behavioral checks

Prior pushed source: `b9c39ed74b39b55fe114898afad377e6051929fb` on `phase-1/foundations`; remote branch matched. [GitHub CI run 45340225724](https://github.com/ahmedzein-dev/ai-dev-workflow/actions/runs/45340225724) completed successfully against that SHA: Ubuntu 24.04, macOS and Windows with Python 3.9/3.13 all passed. Each job ran `python -m unittest -v` from `tests/` (242 discovered) and `python tools/prepublish_check.py` (225 files, no findings). Separate Ubuntu/Python 3.13 lint job ran pinned `ruff check .` and `mypy`, both successful. A new explicit PID-reuse regression test was then added; this CI run is not evidence for the modified source. The suite includes migration, locking, concurrency, recovery, TD-25, compatibility and golden tests; CI does not run these as separate named steps.

Local macOS Python 3.9 and 3.13 full suites each passed 242/242 on that prior source. The stable v1.0.1 engine recorded `unit` (242 tests) and `privacy` passed on fingerprint `6efbf531b426082bdfac1707efc7ff8522471d09252db3dfef9e6b9b9119bc8f`. Pinned Ruff 0.17.6 (`ruff check . --no-cache`) reported zero diagnostics and Mypy 1.20.2 (`mypy --no-incremental`) reported zero in 33 source files. The verified pre-feature baseline at `a66a6070f40ecc6c6da6ee9e8303d94f43bbfe78` was also zero with these pinned versions; earlier reports of 2 Ruff/18 Mypy findings were not present in that exact baseline. Record integrity and `git diff --check` passed.

On the final source fingerprint `b04a1b47d182d353c27ca0f465f67a54c0837ba341416cc42a87f8b667d413a1`, local macOS Python 3.9 and 3.13 full suites each passed 243/243. The stable engine recorded `unit` (243 tests) and `privacy` passed; Ruff 0.17.6 and Mypy 1.20.2 again had zero diagnostics, and privacy found none in 225 files. The explicit PID-reuse fixture also passed independently on both Python versions. Commit `dd88e73140828eebffb373aa2492d0eac0acdf64` contains this source. [GitHub CI run 45390904437](https://github.com/ahmedzein-dev/ai-dev-workflow/actions/runs/45390904437) completed successfully against that SHA: Ubuntu 24.04, macOS and Windows with Python 3.9/3.13 all passed. Each of the six matrix jobs discovered 243 tests and passed the privacy scan of 225 files. The separate Ubuntu/Python 3.13 lint job passed Ruff and Mypy; no mandatory CI step was skipped.

The first CI attempt on `f0d469e7fb8c8813e6e84fc006870a38ef2fc389` failed only on macOS/Python 3.9 during test-repository cleanup: Git removed a transient maintenance lock while `shutil.rmtree` was handling it. `tests/helpers.py` now tolerates only a disappearing file (`FileNotFoundError`); other errors still propagate. On the prior successful [CI run 45340225724](https://github.com/ahmedzein-dev/ai-dev-workflow/actions/runs/45340225724), this job passed 242 tests and privacy scan. The earlier failed run remains [available](https://github.com/ahmedzein-dev/ai-dev-workflow/actions/runs/45338246643) and is not described as passing.

## Limitations

In the final successful run 45390904437, Windows/Python 3.9 executed 241/243 tests (2 conditional skips): directory-sync failure injection is unsupported in this design, and FIFO files are unavailable. Windows/Python 3.13 executed 240/243 tests (3 conditional skips): the same two plus a pre-existing repository-path-of-spaces case whose fixture resolves to an existing repository on that runner. All remaining tests and both privacy scans passed. No CI job or mandatory step was skipped. The prior successful run 45340225724 had the same conditional skips in its 242-test suite.

Windows uses supported file flush and atomic replacement but no directory fsync; equivalent power-loss durability is not claimed. Per-file locking and persistence do not provide atomic multi-file transactions (TD-29). Direct internal persistence calls remain outside the API security boundary (TD-30). Secret detection remains pattern-based, with the documented F-9 Unicode edge cases deferred. Concurrent mixed stable/development engines in one checkout are not guaranteed safe. No production schema-2 converter or migration of real project records was attempted.
