# Final Report: TD-25: keep secret-like check ids and agent names out of task records

## 1. Overall Status

**Status:** Completed with Limitations

Everything in the approved spec v2 (`9cf6cec3`) and plan v2 (`f1c2745d`) is implemented and verified on the
development branch, and the v1.0.1 backport is prepared and tested. The status stays below "Completed" for three
reasons:
- **Installed copies are still vulnerable.** The fix reaches users only through the v1.0.1 release, whose tag,
  publication and installation need the owner's separate approval. TD-25 stays open until then.
- **Windows CI on the release branch** shows two test failures that already exist in v1.0.0 (§4).
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
  - `new` saves the new task before activating it, and on failure removes only the files it wrote (best effort).
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

- **Engine checks on the final code:** `unit` (Python 3.13), `unit-py39` (3.9.6), `privacy`, `ruff`, `mypy`,
  `golden-byte-compare`. Every golden file is byte-identical except the approved FR-13 file. The 27 refusal pins, the
  signature and name pins, the TD-24 pins and the existing hook tests are unchanged and passing.
- **Tests failing on the vulnerable engines:**

  | Engine | Fail | Pass | Skipped |
  |---|---|---|---|
  | `5a7576a` | 25 + 1 error | 4 (legitimate values, valid UUID hook) | 6 (no `aidw.api`) |
  | `fa6a676` | 31 + 1 error | 4 | 0 |
  | `a346300` (before the audit fixes) | 2 (multi-line values, huge session) | 34 | 0 |
  | Final code | 0 | 36 | 0 |
- **Exposure check (counts only):** 45 record files, 0 with secret-like values; this repository's ACTIVE not flagged.
- **CI, development branch:** `a346300` run 45021516859 and `49ba40a` run 45023454467, each 7/7 (lint, plus Linux,
  Windows and macOS × Python 3.9/3.13). The final records commit gets its own run.
- **Backport:**
  - the adapted tests pass 32/32; on pristine v1.0.0, 27 fail, 1 errors, and the 4 legitimate-value tests pass;
  - the full v1.0.0 suite passes locally on 3.13 and 3.9.
  - CI `d8efe25` run 45023456456: Linux and macOS 4/4. On Windows, 2 failures out of 150 tests:
    `test_infos_alone_do_not_fail_when_only_errors_and_warnings_count` and `test_line_endings_do_not_change_the_hash`.
    - Both failures are pre-existing. The CI run on the `v1.0.0` tag itself (43175463889) failed with exactly these
      two.
    - They were fixed on `main` after the release: `ad5bfd3` (analyzer separator regex and a test) and `0bd5a6c`
      (decoding command output with a Windows code-page fallback).
    - They are not ported, because they are outside the TD-25 scope. That is a decision for the release proposal
      (§8).

## 5. Code Audit

An independent, security-focused, read-only subagent reviewed the work in two rounds.

| Round | Verdict | Findings |
|---|---|---|
| 1 | NO-GO | F-1 Important: a line separator inside an agent or check name passed the early check while `state.json` still caught it, so the ordering bug came back. Six Minor: F-2 to F-7 |
| 2 | Code GO; records NO-GO | F-8 Important: verification.md cited this report before it was written. Four Minor: F-9 to F-12 |

All findings are fixed except F-9, which is Deferred and documented (details in audit.md). No existing secret check,
gate, approval rule or refusal was weakened.

## 6. Edge Cases and Regression Risks

- **Detection limits (FR-10):**
  - `assert_no_secrets` is pattern-based: credentials in unknown formats pass. So does a value split by U+0085 or
    U+2028, which the `state.json` check misses too (audit F-9).
  - The session format rule bounds structure, not secrecy.
  - Agent names stay free text.
- **Persistence limits (FR-9, TD-29):**
  - Single files are replaced atomically; multi-file updates are not transactional.
  - `resume`, `preflight` and pausing another task write ACTIVE or the other task's `state.json` first. `pause` and
    `close` delete ACTIVE, and `approve` writes the snapshot, before `save_state`.
  - The check block can lag `state.json` after a failed write, until the next `run`.
  - The new-task clean-up is best effort.
  - Recovery: `status`, then `resume` or `pause`; any `run` rewrites the check block.
- **Trust boundary (FR-14, TD-30):**
  - Direct Python calls to the exported writers (`activate`, `save_state`, `save_json`, `write_text`, `add_history`,
    `regenerate_check_block`) bypass the API checks. No protection is claimed for them.
  - **A centralised persistence check was assessed, not built.** A secret scan of every write under
    `.ai-dev-workflow/` would catch future regressions and most misuse at small cost. But a refusal in the middle of
    a multi-file write could create new partial states, so it should come with the F1.0.5 storage work, as a
    separately approved task, with the API checks staying primary.
- **Hook strictness:** a malformed payload session inside an active task now blocks edits. Claude Code sends UUIDs,
  so this needs a broken or tampered payload. The denial says how to continue.
- **Existing ACTIVE files** written by an unfixed engine are not migrated; `pause <task>` deletes them.

## 7. Pending Dependencies

- **Owner approval of the v1.0.1 release actions (§8).** Until they are done, installed copies, including this
  project's managing engine v1.0.0, remain affected.
- **Owner decision** on porting the two pre-existing Windows fixes into 1.0.1.

## 8. Next Actions

**Release proposal for the owner's separate approval. None of these steps has been taken.**

| Step | Action | Gate |
|---|---|---|
| R0 | Decide whether 1.0.1 also carries the two pre-existing Windows fixes from `main` (`ad5bfd3` regex and test, `0bd5a6c` output decoding). Recommended, so that the release's CI is green on Windows. They are small and already validated on `main` and the development branch, but outside the TD-25 scope | Owner decision |
| R1 | Tag `v1.0.1` on the final tested `release/1.0.x` commit and push the tag | Owner approval |
| R2 | Publish GitHub release notes: affected versions (1.0.0 and development versions before this fix), impact, fix, mitigation, limits; no secret values. A security advisory is optional | Owner approval |
| R3 | Bring the fix to `main` (merge `release/1.0.x`, or port it) | Owner approval |
| R4 | Run `install.py update` from the v1.0.1 checkout on every install (user and project), then `install.py doctor`. Check that `.aidw-install.json` shows 1.0.1, and re-run the CLI and hook regression scenarios against the installed copy | Owner approval |
| R5 | Mark TD-25 **Resolved** only after R4 is verified; then close this task | After R4 |
