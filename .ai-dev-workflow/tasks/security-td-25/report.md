# Final Report: TD-25: keep secret-like check ids and agent names out of task records

## 1. Overall Status

**Status:** Completed with Limitations

Everything in the approved spec v2 (`9cf6cec3`) and plan v2 (`f1c2745d`) is implemented and verified on the
development branch, and the v1.0.1 backport is prepared and tested. The status stays below "Completed" for two
reasons:
- **Installed copies are still vulnerable.** The fix reaches users only through the v1.0.1 release, whose tag,
  publication and installation need the owner's separate approval. TD-25 stays open until then.
- **Detection is pattern-based** (§6).

Approval history:
- S1–S3 were implemented under the approved v1 documents (`2fdbc034`, `b60cd6f0`).
- S4 onward were implemented under v2, which recorded S1–S3 as done (see verification.md).
- The owner's decisions are recorded in state.json: Option A (F-1 pin re-trigger) and Option 1 (hooks in scope).

## 2. What Was Implemented

- **Identity checks before anything runs or is written** (`aidw/api.py`):
  - The 15 recording functions check the agent name first, which covers `--agent` and `AI_DEV_WORKFLOW_AGENT`.
  - `new`, `resume` and `preflight` check the session id: the secret check, then 1–256 printable characters without
    spaces; above 4,096 characters the session is refused before any scanning.
  - `run` checks the check name before the lookup and before executing.
  - Each value is scanned as given and in its JSON form, the form `state.json` is scanned in (audit F-1).
  - Messages name the field, never the value.
- **Claude Code hooks** (`aidw/agents/claude_hooks.py`) treat the payload session id as untrusted:
  - An invalid one (secret-like, malformed or not text) is never written to ACTIVE or the hook log. The log records
    `session: null, session_rejected: true`.
  - Inside an active task the edit is denied whatever the binding.
  - Without an active task, and for valid sessions, nothing changes.
- **Write order:**
  - `run` saves `state.json` before rewriting the check block.
  - `new` saves the task before activating it. The handover audit found a cleanup path that could remove a foreign
    file. Cleanup now reserves temporary names exclusively, tracks successful writes, and preserves foreign or
    changed records. Tests cover both a failed state replacement and files created or changed outside the write.
  - This repairs two orderings. **It is not multi-file atomicity** (TD-29).
- **F-1 regression pin (owner decision Option A):**
  - `LateRefusalTest` keeps its purpose with a synthetic `WorkflowError` raised by `save_state` after the command ran.
  - Its golden file was regenerated from the pre-fix engine `fa6a676`. A regeneration with the final test there is
    byte-identical.
- **Tests:** `tests/test_secret_identity.py` has 36 tests with synthetic values only.
- **Documentation:**
  - CHANGELOG "Unreleased → Security";
  - TECHNICAL_DEBT TD-25 status and limits, TD-27 to TD-29, and the new TD-30.
- **v1.0.1 backport** on `release/1.0.x` (`056ac73`, `7f3a2ae`, `d8efe25`, plus the round-2 commit), built from
  `v1.0.0`:
  - the same security behaviour in the single-file engine, with no later features or restructuring;
  - version 1.0.1, a CHANGELOG section, and CI on `release/**` with the Ubuntu runner pinned to 24.04;
  - 32 adapted tests.
- **Owner-approved Windows compatibility fixes** on release commit `6a7cba0`: the analyzer accepts the Windows
  replacement separator, command output uses the system code page when UTF-8 decoding fails, and the CRLF test
  fixture normalizes its input. Only the relevant hunks and tests from `ad5bfd3` and `0bd5a6c` were ported.

## 3. Specification Compliance

FR-1–FR-14, EC-1–EC-18 and AC-1–AC-14 are met (verification.md). The documented deviations are:
- **Session refusal above 4,096 characters:** the session is refused with the format message before the secret scan
  (audit F-5). FR-2 orders the secret check first. The change applies only to absurd lengths that the format rule
  refuses anyway.
- **Session secret check:** it scans the JSON form as well as the value (audit F-1), and is stricter than written in
  FR-2.
- **Hook, non-text session:** a non-text payload session is treated as invalid and denied inside an active task.
  Before, the exception path let the edit through.

## 4. Testing Results

- **Development `c0f5800519e0934e30184142e7f92cbcabbb45f4`:** local engine fingerprint `fd10d4edf94522f066af80d764f0aeb5d3929edfcc8c8a9fc9085a61c364379d`. 209/209 passed on
  each of Python 3.13 and 3.9.6, including 36 TD-25 tests and the existing legacy compatibility suite.
  Ruff, Mypy, the privacy scan and the golden comparison passed. The F-1 test also matched the approved golden
  on a separate export of `fa6a676` with both interpreters. [Development CI 45036934864](https://github.com/ahmedzein-dev/ai-dev-workflow/actions/runs/45036934864) passed 7/7.
- **Release `6a7cba0da146421e51988edf386fbfb3adda5f20`:** 152/152 passed locally on each of Python 3.13 and 3.9.6, including 32 TD-25 tests. The privacy scan found no issues in 65 files and the release golden files remain byte-identical to v1.0.0. [Release CI 45038409846](https://github.com/ahmedzein-dev/ai-dev-workflow/actions/runs/45038409846) passed 6/6 on Linux, macOS and Windows with both Python versions. Each Windows job passed 152 tests, including the two formerly failing tests and the new decoding regression, plus its privacy scan.
- **Windows baseline:** the same two tests failed on both Python versions in
  [the original CI at the v1.0.0 commit](https://github.com/ahmedzein-dev/ai-dev-workflow/actions/runs/43175463889). The analyzer test's output separators were misinterpreted
  on Windows. The other test converted a file that already had CRLF by blindly adding a carriage return to each
  LF. `ad5bfd3` corrected the CRLF test and broadened separator parsing. The analyzer test still failed in that
  run. `0bd5a6c` added locale-aware fallback decoding, and [the later run passed 6/6](https://github.com/ahmedzein-dev/ai-dev-workflow/actions/runs/43179376215).
  The owner approved both narrow ports; the final release CI confirms their Windows tests now pass.
- **Original v1.0.0 suite:** Codex reran the 118 original tests on macOS with both Python versions. Both passed.
- **Historical security reproduction:** Claude Code's pre-fix results on `5a7576a`, `fa6a676`, `a346300`
  and pristine v1.0.0 are retained in verification.md and the task history. Codex confirmed the patched regression
  suites and did not repeat the old secret persistence scenario.
- **Exposure check (counts only):** 38 task record files; 0 flagged; ACTIVE present=True, flagged=False.
- **Installed engine:** the local installed engine identifies as v1.0.0. Its engine file has the same Git blob
  hash as the engine at the original v1.0.0 tag.

## 5. Code Audit

The initial independent reviewer audited the implementation in two rounds. A separate read-only reviewer audited the Codex handover.

| Round | Verdict | Findings |
|---|---|---|
| 1 | NO-GO | F-1 Important: a line separator inside an agent or check name passed the early check while `state.json` still caught it, so the ordering bug came back. Six Minor: F-2 to F-7 |
| 2 | Code GO; records NO-GO | F-8 Important: verification.md cited this report before it was written. Four Minor: F-9 to F-12 |
| Handover | Initial NO-GO, then GO for the rollback correction | F-13 Important: rollback ownership, fixed in both branches. F-14 Minor: evidence and wording, fixed. |
| Final release code | GO for code and tests | Separate read-only audit of `6a7cba0` found no new defect; the required Windows hunks and tests were ported without later architecture or CI changes. Exact CI and record evidence were reconciled afterward. |

All findings are fixed except F-9, which is Deferred and documented (details in audit.md). No existing secret check,
gate, approval rule or refusal was weakened.

## 6. Edge Cases and Regression Risks

- **Detection limits (FR-10):**
  - `assert_no_secrets` uses patterns. Unknown credential formats and the documented U+0085 and U+2028 cases can
    escape the secret scan, including in `state.json` (audit F-9).
  - The independent session format check rejects those separators and bounds the session ID structure.
  - Agent names stay free text.
- **Persistence limits (FR-9, TD-29):**
  - The writer replaces each file atomically with `os.replace`. It does not use fsync. A failure can still
    leave a temporary file (for example if cleanup is interrupted or refused by the file system).
  - Updates that span several files have no transaction or lock (TD-29).
  - `resume`, `preflight` and pausing another task write ACTIVE or the other task's `state.json` first. `pause` and
    `close` delete ACTIVE, and `approve` writes the snapshot, before `save_state`.
  - The check block can lag `state.json` after a failed write, until the next `run`.
  - The new-task clean-up is best effort.
  - Recovery: `status`, then `resume` or `pause`; any `run` rewrites the check block.
- **Trust boundary (FR-14, TD-30):**
  - Direct Python calls to the exported writers (`activate`, `save_state`, `save_json`, `write_text`, `add_history`,
    `regenerate_check_block`) bypass the API checks. No protection is claimed for them.
  - **A centralised persistence check was assessed, not built.** A secret scan of every write under
    `.ai-dev-workflow/` could catch future regressions and misuse at small scanning cost. A legitimate record that matches a secret
    pattern could be rejected. Refusal in the middle of a multi-file write could also create new partial states, so it should come with the F1.0.5 storage work, as a
    separately approved task, with the API checks staying primary.
- **Hook strictness:** a malformed payload session inside an active task now blocks edits. Claude Code sends UUIDs,
  so this needs a broken or tampered payload. The denial says how to continue.
- **Existing ACTIVE files** written by an unfixed engine are not migrated; `pause <task>` deletes them.
- **Public-record sanitation:** the owner approved replacing the machine-specific directory in exactly three
  historical `golden-byte-compare` command fields with `[REDACTED_LOCAL_TMP]/`. The original bytes were backed up
  privately outside the repository. A parsed-JSON comparison showed no other field changed. The published command
  strings are redacted records and cannot be run verbatim; the check results, timestamps, fingerprints and approval
  evidence remain intact. The original path remains visible in earlier public Git commits; history was not rewritten.
  Verification details and hashes are in verification.md.

## 7. Pending Dependencies

- **Owner approval of the v1.0.1 release actions (§8).** Until they are done, installed copies, including this
  project's managing engine v1.0.0, remain affected.
- **Repository visibility:** the owner confirmed the public repository is intentional. The three historical
  machine-specific command paths in the current task record were sanitized with the owner's explicit approval;
  earlier public Git history still contains them.

## 8. Next Actions

**Release proposal for the owner's separate approval. R0 is complete; R1–R5 have not been taken.**

| Step | Action | Gate |
|---|---|---|
| R0 | Port the two approved Windows fixes and tests; verify the final release branch on all six CI jobs | Done on `6a7cba0`; CI 45038409846 passed 6/6 |
| R1 | Tag `v1.0.1` on the final tested `release/1.0.x` commit and push the tag | Owner approval |
| R2 | Publish GitHub release notes: affected versions (1.0.0 and development versions before this fix), impact, fix, mitigation, limits; no secret values. A security advisory is optional | Owner approval |
| R3 | Bring the fix to `main` (merge `release/1.0.x`, or port it) | Owner approval |
| R4 | Run `install.py update` from the v1.0.1 checkout on every install (user and project), then `install.py doctor`. Check that `.aidw-install.json` shows 1.0.1, and re-run the CLI and hook regression scenarios against the installed copy | Owner approval |
| R5 | Mark TD-25 **Resolved** only after R4 is verified; then close this task | After R4 |
