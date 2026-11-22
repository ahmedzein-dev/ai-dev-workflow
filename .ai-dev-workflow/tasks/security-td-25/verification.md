# Verification: TD-25: keep secret-like check ids and agent names out of task records

Tested commit: **a346300** (code fingerprint 4e22081a98) — CI run 45021516859, 7/7. Backport: release/1.0.x 056ac73 + 7f3a2ae (CI runner pin), CI run 45021971350. Approved documents: spec v2 `9cf6cec3`, plan v2
`f1c2745d`.

**Approval history (condition 4 of the v2 approval).**
- S1–S3 were implemented under the approved **spec v1 `2fdbc034` and plan v1 `b60cd6f0`** (approved 2026-11-22,
  frozen as `approved/spec.v1.md` and `approved/plan.v1.md`).
- During S3 the F-1 pin conflict was found. The owner then chose Option A (pin re-trigger) and Option 1 (hook in
  scope).
- The task moved back to SPECIFICATION, and spec v2 and plan v2 were written and approved afterwards (`approved/spec.v2.md`,
  `approved/plan.v2.md`). v2 records S1–S3 as already done under v1.
- S4 onward were implemented under v2. The S1–S3 code was kept unchanged, except that `_check_session` now calls
  the shared `session_problem` (S4) with identical messages.
- No approval evidence was rewritten. The engine's warning "files changed before implementation was approved"
  refers to the S1–S3 files changed while v2 was being specified.

## Check runs

Written by `workflow.py run`; do not edit between the markers.

<!-- aidw:checks:start -->
| Check | Status | Summary | Code fingerprint | When | Agent |
|---|---|---|---|---|---|
| golden-byte-compare | passed | 14 golden files; changed: ['run-output-before-late-refusal.txt']; unexpected: none | `5c340c9124` | 2026-11-22T12:38:10Z | claude-code |
| mypy | passed | Success: no issues found in 31 source files | `5c340c9124` | 2026-11-22T12:38:09Z | claude-code |
| privacy | passed | Scanned 212 files: no findings. | `5c340c9124` | 2026-11-22T12:35:54Z | claude-code |
| ruff | passed | All checks passed! | `5c340c9124` | 2026-11-22T12:38:09Z | claude-code |
| unit | passed | OK | `5c340c9124` | 2026-11-22T12:35:55Z | claude-code |
| unit-py39 | passed | OK | `5c340c9124` | 2026-11-22T12:37:11Z | claude-code |
<!-- aidw:checks:end -->

## Acceptance matrix

One row for every AC and EC in the approved spec and every "Done when" item, numbered DW-1, DW-2, … in
order. Status is Passed, Failed, Blocked or Not Verified. Evidence names the test, command or inspection;
for Blocked and Not Verified it says why. A check that did not run is never Passed.

| Item | Status | Evidence |
|------|--------|----------|
| AC-1 | Passed | tests/test_secret_identity.py CliRefusalTest (13 tests: EC-1–EC-7, EC-11; byte snapshot of .ai-dev-workflow/ and .git/info/exclude, value absent from stdout/stderr and from every repository file); checks `unit`, `unit-py39` at 4e22081a98 |
| AC-2 | Passed | CliRefusalTest run tests: marker file from `make_marker.py` absent after each refusal |
| AC-3 | Passed | test_new_with_a_secret_like_agent_name_while_another_task_is_active: no folder, other task and ACTIVE byte-identical, later `new` succeeds |
| AC-4 | Passed | ApiRefusalTest: all 15 functions with a secret-like agent; new_task/resume/preflight with 2 secret-like and 5 malformed sessions; AI_DEV_WORKFLOW_AGENT via CLI and a subprocess |
| AC-5 | Passed | LegitimateValuesTest (UUID, `${CLAUDE_SESSION_ID}`, 256-character id, placeholder-like agent, `smoke test` check name, existing refusal order); the 3 value tests also pass on 5a7576a and fa6a676 |
| AC-6 | Passed | Old engines with the final test file: 5a7576a 22 fail / 4 pass (legitimate values, valid UUID hook) / 6 skip (no aidw.api); fa6a676 28 fail / 4 pass; fixed engine 32/32 |
| AC-7 | Passed | `unit` (Python 3.13) and `unit-py39` (3.9.6) at 4e22081a98; `golden-byte-compare`: 14 golden files, only run-output-before-late-refusal.txt changed (the approved FR-13 file); 27 refusal pins and signature pin unchanged and passing |
| AC-8 | Passed | checks `ruff`, `mypy` (31 files), `privacy` (212 files); token-pattern grep over the repository: 0 literal values (synthetic values are concatenated at run time) |
| AC-9 | Passed | RecoveryTest.test_failed_new_removes_only_its_own_folder_and_leaves_the_active_task; test_failed_new_never_deletes_a_file_it_did_not_write (a foreign file in the new folder survives) |
| AC-10 | Passed | RecoveryTest.test_failed_check_block_write_keeps_state_and_the_next_run_repairs_it (OSError propagates with output_tail; state.json has the entry; next run rewrites the block) |
| AC-11 | Passed | report.md Limitations (FR-9 persistence, FR-10 detection); TECHNICAL_DEBT TD-25 status "fixed on the development branch; installed copies still affected", TD-27, TD-28, TD-29 rows; release proposal in report.md |
| AC-12 | Passed | HookTest (9 tests: active task bound/unbound/other agent/records path, non-text session, no records, paused/closed with ACTIVE, prompt hook, valid UUID with hook log enabled); 7 of the 8 invalid-session tests failed before the fix and on fa6a676; existing test_preflight_and_hooks unchanged and passing |
| AC-13 | Passed | LateRefusalTest passes on fa6a676 and the fixed engine, Python 3.13 and 3.9; golden regenerated in an export of fa6a676 with the final test is byte-identical (`cmp`); asserts marker, `token [REDACTED]`, order, stderr, exit code 1 |
| AC-14 | Passed | TECHNICAL_DEBT TD-30 (exported writers trust boundary, centralised check assessed, not built); report.md section on the trust boundary |
| EC-1 | Passed | test_run_with_a_secret_like_check_name_and_an_extra_command |
| EC-2 | Passed | test_run_with_a_secret_like_unknown_check_name |
| EC-3 | Passed | test_run_with_a_secret_like_agent_name |
| EC-4 | Passed | test_agent_name_from_the_environment (+ separate process) |
| EC-5 | Passed | test_resume/preflight_with_a_secret_like_agent_name |
| EC-6 | Passed | test_new_with_a_secret_like_agent_name_while_another_task_is_active; test_new_without_setup_commit_mode_is_not_applied_before_the_refusal |
| EC-7 | Passed | test_secret_like_session_ids; test_preflight_with_a_secret_like_session_id |
| EC-8 | Passed | LegitimateValuesTest.test_accepted_session_ids; test_placeholder_like_agent_name_is_accepted |
| EC-9 | Passed | test_existing_refusal_order_with_a_legitimate_agent |
| EC-10 | Passed | Not migrated by design; exposure check: this repository's ACTIVE not flagged (45 record files, 0 flagged); report gives `pause <task>` as clean-up |
| EC-11 | Passed | test_malformed_session_ids_are_refused_explicitly; ApiRefusalTest sessions |
| EC-12 | Passed | RecoveryTest new-task tests |
| EC-13 | Passed | RecoveryTest check-block test |
| EC-14 | Passed | HookTest.test_valid_uuid_session_behaves_as_before; existing hook tests |
| EC-15 | Passed | HookTest active-task tests (bound, unbound, other agent, records path, non-text) |
| EC-16 | Passed | HookTest.test_without_an_active_task…; test_paused_or_closed_task_with_an_active_pointer… |
| EC-17 | Passed | HookTest.test_prompt_hook_is_silent_for_an_invalid_session |
| EC-18 | Passed | LateRefusalTest (AC-13) |
| DW-1 | Passed | All FR-1–FR-14 implemented (S1–S7 recorded with `step`) |
| DW-2 | Passed | EC-1–EC-18 rows above |
| DW-3 | Passed | checks `unit`, `unit-py39`, `privacy`, `ruff`, `mypy` (and `golden-byte-compare`) at 4e22081a98 |
| DW-4 | Passed | CI run 45021516859 on a346300: lint + Linux, Windows, macOS × Python 3.9/3.13, 7/7 success |
| DW-5 | Not Verified | Independent security audit running; updated when its report is in |
| DW-6 | Passed | Exposure check (counts only): 45 record files, 0 with secret-like values; ACTIVE present, not flagged; no value printed |
| DW-7 | Passed | release/1.0.x (056ac73 port, 7f3a2ae CI runner pin) in a separate worktree: adapted tests 28/28 pass, 24 of 28 fail on pristine v1.0.0 (4 legitimate-value tests pass); full v1.0.0 suite passes locally on 3.13 and 3.9; CI run 45021971350: Linux and macOS 4/4; Windows 2 failures, both pre-existing in v1.0.0 (identical failures in CI run 43175463889 on the v1.0.0 tag itself), all TD-25 tests pass on Windows; no tag, release or install |
| DW-8 | Not Verified | Pending the audit report (must cover the hook path and the FR-13 pin) |
| DW-9 | Passed | TECHNICAL_DEBT TD-25 marked "fixed on the development branch; installed copies still affected"; release proposal in report.md for the owner's separate approval; F1.0.4 records untouched |

## Behavioral checks

- Reproduction before the fix (DEP-2) with a synthetic token in a scratch repository: check name and agent name in the verification.md check block, ACTIVE written by resume/new/preflight, orphan task folder after `new`, secret-like `--session` stored and accepted.
- After the fix, the same commands are refused with the field named and nothing written (CliRefusalTest asserts this per command).
- Existing features exercised unchanged: the full suite (all pre-existing tests, 27 refusal pins, signature pin, TD-24 pins, hook tests, API separation tests).

## Limitations

- **Detection is pattern-based (FR-10):** a credential in a format the scanner does not know is not refused. The session format rule bounds structure, not secrecy. Agent names keep free text.
- **Persistence (FR-9, TD-29):** single files are replaced atomically; multi-file updates are not transactional. `resume`, `preflight` and pausing another task still write ACTIVE or another task's state.json before the task's own. The check block can lag state.json until the next `run` after a failed write (tested, EC-13).
- **Trust boundary (TD-30):** direct Python calls to the exported writers (`activate`, `save_state`, …) bypass the API checks; no protection is claimed for them.
- **Installed copies:** the installed v1.0.0 engine is still affected until v1.0.1 is approved, released and installed.
- **Backport on Windows:** two pre-existing v1.0.0 test failures (analyzer output decoding on the Windows code page; a line-ending test). They are identical on the v1.0.0 tag's own CI, fixed on `main` after the release (ad5bfd3, 0bd5a6c), and not ported (outside the TD-25 scope; owner decision pending).
