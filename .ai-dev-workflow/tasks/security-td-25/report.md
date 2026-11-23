# Final Report: TD-25: keep secret-like check ids and agent names out of task records

## 1. Overall Status

**Status:** Completed with Limitations

The approved spec v2 (`9cf6cec3`) and plan v2 (`f1c2745d`) were implemented and verified. The v1.0.1 security
release was published, the missing fix was integrated into `main`, and the accessible user-level installation was
updated from the official tag and verified. The owner explicitly approved closing TD-25 with this outcome.
"Completed with Limitations" records the pattern-based detection boundary (§6), inaccessible installation-inventory
locations, and agent sessions that could not be verified live (§4). No outdated installation is asserted in an
inaccessible location.

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
- **Publication and main integration:** annotated tag `v1.0.1` resolves to `6a7cba0`; the GitHub Release is
  published. PR #1 merged the TD-25 integration into `main` at `a964cadd` without replacing its newer work.
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
- **Main integration:** [PR #1](https://github.com/ahmedzein-dev/ai-dev-workflow/pull/1) merged at
  `a964cadd22347872034bdb82f4e8cecfbea7a111`. Its tree matches the approved integration head `49c1395`;
  the [post-merge CI](https://github.com/ahmedzein-dev/ai-dev-workflow/actions/runs/45068051262) passed 6/6
  (Ubuntu, macOS, Windows × Python 3.9 and 3.13), including unit and privacy steps. No newer `main` functionality
  or existing Windows compatibility fix was removed.
- **Published release:** [v1.0.1](https://github.com/ahmedzein-dev/ai-dev-workflow/releases/tag/v1.0.1) remains
  on `6a7cba0da146421e51988edf386fbfb3adda5f20`; `release/1.0.x` and the tag are unchanged.
- **Installed engine:** the accessible user-level copy under `~/.agents/skills/ai-dev-workflow` was originally an
  unmodified v1.0.0 install. A private backup was made outside the public repository. The installer dry-run named
  only that canonical copy for replacement and kept the existing Claude Code and Antigravity links. After update,
  `doctor` reported no problems; manifest, metadata, engine bytes (SHA-256
  `a251b28c21908b72817a50884de61cdd2d2e4fe6cdccd52cfa45da62792e1ff3`) and all installed files match the
  clean official v1.0.1 tag. The private library and task records were unchanged. The 32 TD-25 release regression
  tests passed against the installed engine on each of Python 3.9 and 3.13 in isolated temporary repositories;
  they covered rejected agent, session and check identities, no persisted values or command execution, hook denial
  and logging, and valid session handling. The initial temporary test harness omitted the example rules file;
  after adding that fixture, all 32 tests passed without changing the installed engine.
- **Agent resolution:** a fresh read-only Codex session explicitly loaded the installed skill and reported 1.0.1;
  a fresh Gemini CLI `skills list --all` showed it enabled at the same canonical path. Claude Code and Antigravity
  symlinks resolve to the 1.0.1 engine, but a fresh Claude Code invocation was blocked by its weekly usage limit,
  existing Claude Desktop sessions were not restarted, and Antigravity is not installed for a live test.
- **Closure gate:** after the TD-25 technical-debt status was updated, the official workflow identified its required
  `unit` and `privacy` checks as stale. They were rerun through `workflow.py run` on code fingerprint `5589c9abc4`:
  209/209 unit tests passed and the privacy scan found no issue in 212 files. `workflow.py check` reports consistent
  records, and `outcome` allows Completed; the owner chose Completed with Limitations.

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
- **Installation-inventory limits:** no project-level installation was found in the accessible locations inspected.
  macOS denied access to `~/Desktop` and the `ZEIN_ORIGINALS` parent, so their contents were
  not inventoried. No claim is made that either contains an installation, outdated or otherwise. Existing Claude
  Desktop sessions were not restarted; their in-memory skill state is unverified. A live Claude Code check was
  blocked by its weekly usage limit. Antigravity is not installed, so only its symlink target was checked. These
  are follow-up verification limits, not failed security tests or evidence of an affected installed copy.

## 7. Pending Dependencies

No approval remains for the verified release and accessible installation scope; the owner explicitly approved
closure as Completed with Limitations. Inspection of the two macOS-restricted directories and live checks of Claude
Code after its usage limit resets may be performed when available. They do not block this owner-approved closure.
The public repository is intentional; the historical path sanitation did not rewrite earlier Git history.

## 8. Next Actions

The official `workflow.py close` set the task to Closed — Completed with Limitations after record-integrity and
privacy checks. When access becomes available, inspect the two restricted directories and verify Claude Code after
a fresh session can run; record any finding as follow-up without silently changing this outcome. F-9 remains
Deferred, and TD-29 and TD-30 remain separate open technical debts. No feature starts as part of this closure.
