# Verification: TD-25: keep secret-like check ids and agent names out of task records

Development code commit: `c0f5800519e0934e30184142e7f92cbcabbb45f4`, [CI 45036934864](https://github.com/ahmedzein-dev/ai-dev-workflow/actions/runs/45036934864), 7/7. Local tests used the same TD-25 files. The local engine fingerprint `fd10d4edf94522f066af80d764f0aeb5d3929edfcc8c8a9fc9085a61c364379d` includes the pre-existing uncommitted roadmap edits. The committed code fingerprint is `bafffcdf17229af827e11c1f2f7a9019abe59833aaa376ab562c427dead61dee` (git tree checked using the installed engine's fingerprint rules).

Release code commit: `6a7cba0da146421e51988edf386fbfb3adda5f20`, [CI 45038409846](https://github.com/ahmedzein-dev/ai-dev-workflow/actions/runs/45038409846), 6/6. The release code fingerprint is `fc9a168e7ab37d45271025f603fe9ff3c63c18a5815bb45b6b03519d820cc4d2`. This commit includes the security backport at `095c511` and the owner-approved Windows compatibility fixes from `ad5bfd3` and `0bd5a6c` (only relevant code and tests).

Historical development runs: `c072342` 45024827167, `49ba40a` 45023454467 and `a346300` 45021516859 all passed 7/7. Historical release runs: `0951ed0` 45024829613, `d8efe25` 45023456456 and `095c511` 45036741638 each passed 4/6 with the same pre-existing Windows failures. The original v1.0.0 run 43175463889 failed the same two Windows tests on both Python versions.
Approved documents: spec v2 `9cf6cec3`, plan v2 `f1c2745d`.

**Public-record sanitation (owner-approved, after the checks ran):** The installed v1.0.0 engine has no supported
command for editing an existing check entry. A byte-identical backup of state.json was saved outside the repository
in private local Codex data (file mode `0600`, backup SHA-256 `e296237b36dbca2990814f966a3063ae3e88eea1b5146ae1251480a87a8c0d73`). The three historical
`golden-byte-compare` entries at `checks[7].command` (12:17:06Z), `checks[13].command` (12:38:10Z), and
`checks[19].command` (12:54:11Z) each contained the same machine-specific temporary directory twice. Only that
directory prefix was replaced with `[REDACTED_LOCAL_TMP]/` (six substitutions). A parsed-JSON comparison confirmed
every other field was unchanged; the sanitized state SHA-256 is
`0fc01e24a64cddbbd358673fa3d69ad62557c4525e61f5cef1e6784d74a179f6`. These command strings are
privacy-redacted descriptions of historical checks, **not the original executable command lines**. Their results,
timestamps, fingerprints, and approval records remain intact. The original paths remain in previously published Git
history; no history rewrite was performed. `workflow.py check` reports consistent records; `status` reports valid
spec/plan approvals and active `FINAL_REPORT`; `outcome` still permits Completed with Limitations. The privacy scan
found no issues in 212 files, and a separate machine-path search found none in the four records being committed.

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
| golden-byte-compare | passed | Only the approved late-refusal golden differs from deba846. | `fd10d4edf9` | 2026-11-22T15:13:41Z | codex |
| mypy | passed | Success: no issues found in 31 source files | `fd10d4edf9` | 2026-11-22T15:13:40Z | codex |
| privacy | passed | Scanned 212 files: no findings. | `fd10d4edf9` | 2026-11-22T15:13:40Z | codex |
| records-exposure | passed | 38 task record files; 0 flagged; ACTIVE present=True, flagged=False. | `fd10d4edf9` | 2026-11-22T15:13:41Z | codex |
| ruff | passed | All checks passed! | `fd10d4edf9` | 2026-11-22T15:13:40Z | codex |
| td25-regression | passed | OK | `fd10d4edf9` | 2026-11-22T15:10:55Z | codex |
| unit | passed | OK | `fd10d4edf9` | 2026-11-22T15:11:13Z | codex |
| unit-py39 | passed | OK | `fd10d4edf9` | 2026-11-22T15:12:38Z | codex |
<!-- aidw:checks:end -->

## Acceptance matrix

One row for every AC and EC in the approved spec and every "Done when" item, numbered DW-1, DW-2, … in
order. Status is Passed, Failed, Blocked or Not Verified. Evidence names the test, command or inspection;
for Blocked and Not Verified it says why. A check that did not run is never Passed.

| Item | Status | Evidence |
|------|--------|----------|
| AC-1 | Passed | tests/test_secret_identity.py CliRefusalTest (15 tests: EC-1–EC-7, EC-11, multi-line values (audit F-1), CLI sweep of every recording command (F-4); byte snapshot of .ai-dev-workflow/ and .git/info/exclude; value absent from stdout/stderr and, raw or JSON-escaped, from every repository file); checks `unit`, `unit-py39` on the final code |
| AC-2 | Passed | CliRefusalTest run tests: marker file from `make_marker.py` absent after each refusal |
| AC-3 | Passed | test_new_with_a_secret_like_agent_name_while_another_task_is_active: no folder, other task and ACTIVE byte-identical, later `new` succeeds |
| AC-4 | Passed | ApiRefusalTest: all 15 functions with a secret-like agent; new_task/resume/preflight with 2 secret-like and 5 malformed sessions; AI_DEV_WORKFLOW_AGENT via CLI and a subprocess |
| AC-5 | Passed | LegitimateValuesTest (UUID, `${CLAUDE_SESSION_ID}`, 256-character id, placeholder-like agent, `smoke test` check name, existing refusal order); the 3 value tests also pass on 5a7576a and fa6a676 |
| AC-6 | Passed | Claude Code pre-fix evidence from the then-current regression suite: 5a7576a 25 failures and 1 error / 4 passes / 6 skips; fa6a676 31 failures and 1 error / 4 passes; a346300 2 failures. Codex reran the final 36 tests on the fixed development code. The earlier evidence was retained and the old secret persistence scenario was not repeated. |
| AC-7 | Passed | 209/209 under each of Python 3.13 and 3.9.6 (local fingerprint `fd10d4edf9`). The existing 27 refusal pins, signature pin and TD-24 pins passed. 14 goldens checked against `deba846`; only the FR-13 golden differs. |
| AC-8 | Passed | checks `ruff`, `mypy` (31 files), `privacy` (212 files); token-pattern grep over the repository: 0 literal values (synthetic values are concatenated at run time) |
| AC-9 | Passed | RecoveryTest injects state replacement failure after the temporary state is written. The task folder is removed, the original error is raised and prior records are byte-identical. The separate foreign-file case preserves files at a failed destination and a changed earlier record, with matching release tests. |
| AC-10 | Passed | RecoveryTest.test_failed_check_block_write_keeps_state_and_the_next_run_repairs_it (OSError propagates with output_tail; state.json has the entry; next run rewrites the block) |
| AC-11 | Passed | report.md Limitations (FR-9 persistence, FR-10 detection); TECHNICAL_DEBT TD-25 status "fixed on the development branch; installed copies still affected", TD-27, TD-28, TD-29 rows; release proposal in report.md |
| AC-12 | Passed | HookTest (11 tests, hook log enabled): active task bound/unbound/other agent/records path, non-text and multi-line sessions, huge session, no records, paused, paused/closed with ACTIVE, prompt hook, valid UUID; all 10 invalid-session tests fail on 5a7576a and fa6a676 (the huge-session test errors there), the valid-UUID test passes everywhere; existing test_preflight_and_hooks unchanged and passing |
| AC-13 | Passed | Codex checked LateRefusalTest in a temporary export of fa6a676 and on the fixed engine, under Python 3.13 and 3.9. The test ran the command and checked marker, redaction, stdout and stderr, order, and exit code 1 against the unchanged approved golden. |
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
| DW-1 | Passed | FR-1–FR-14 implemented. S1–S9 recorded in state.json. S10 records the owner review and keeps the task open for release decisions. |
| DW-2 | Passed | EC-1–EC-18 rows above |
| DW-3 | Passed | Engine checks unit (209/209), unit-py39 (209/209), privacy, ruff, mypy and golden-byte-compare passed at `fd10d4edf9`. TD-25 targeted suite 36/36. |
| DW-4 | Passed | [CI 45036934864](https://github.com/ahmedzein-dev/ai-dev-workflow/actions/runs/45036934864) on `c0f5800`: lint and all six Linux/macOS/Windows jobs for Python 3.9 and 3.13 passed. |
| DW-5 | Passed | Independent audit rounds and Codex handover review in audit.md. The handover reviewer confirmed the correction for F-13. F-9 remains Deferred. No known Important finding remains open and no existing check or gate was weakened. |
| DW-6 | Passed | 38 task record files; 0 flagged; ACTIVE present=True, flagged=False. |
| DW-7 | Passed | Release `6a7cba0`: 152/152 locally under Python 3.13 and 3.9.6, including 32 TD-25 tests; privacy scan 65 files with no findings; golden files unchanged from v1.0.0. [Final release CI](https://github.com/ahmedzein-dev/ai-dev-workflow/actions/runs/45038409846) passed all six Linux/macOS/Windows × Python 3.9/3.13 jobs. Both Windows jobs ran 152/152, passed the two previously failing tests and the new decoding regression, and passed the privacy scan. The same two failures were verified in [original v1.0.0 CI](https://github.com/ahmedzein-dev/ai-dev-workflow/actions/runs/43175463889) and `095c511` CI. The 118 original v1.0.0 tests passed locally on each Python version. Pre-fix TD-25 reproduction is inherited from Claude Code. No tag, release, merge, installation or closure. |
| DW-8 | Passed | Both audit rounds covered the hook path (invalid, non-text, multi-line sessions; logging; fail-closed inside an active task) and the FR-13 pin (golden regenerated by the auditor from fa6a676, byte-identical) |
| DW-9 | Passed | TECHNICAL_DEBT TD-25 marked "fixed on the development branch; installed copies still affected"; release proposal in report.md for the owner's separate approval; F1.0.4 records untouched |

## Behavioral checks

- Claude Code’s recorded reproduction before the fix (DEP-2) used a synthetic token in a scratch repository: check name and agent name in the verification.md check block, ACTIVE written by resume/new/preflight, orphan task folder after `new`, secret-like `--session` stored and accepted.
- After the fix, the same commands are refused with the field named and nothing written (CliRefusalTest asserts this per command).
- Existing features exercised unchanged: the full suite (all pre-existing tests, 27 refusal pins, signature pin, TD-24 pins, hook tests, API separation tests).

## Limitations

- **Detection is pattern-based (FR-10):** unknown credential formats and the documented U+0085 and U+2028 cases can escape the secret scan, including the scan of `state.json` (audit F-9). The independent session format rejects those separators and bounds structure. Agent names keep free text.
- **Persistence (FR-9, TD-29):** single files are replaced atomically; multi-file updates are not transactional. `resume`, `preflight` and pausing another task still write ACTIVE or another task's state.json before the task's own. The check block can lag state.json until the next `run` after a failed write (tested, EC-13).
- **Trust boundary (TD-30):** direct Python calls to the exported writers (`activate`, `save_state`, …) bypass the API checks; no protection is claimed for them.
- **Installed copies:** the installed v1.0.0 engine is still affected until v1.0.1 is approved, released and installed.
- **Windows baseline:** the two pre-existing v1.0.0 test failures were corrected on the release branch with the owner's approval. This is compatibility work, not a claim of broader Windows coverage beyond the 6/6 CI matrix.
