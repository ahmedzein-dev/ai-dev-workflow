# Implementation Plan: TD-25: keep secret-like check ids and agent names out of task records

> Spec: 9cf6cec3 (v2: adds the Claude Code hook, the F-1 pin re-trigger, the trust boundary and the backport
> preparation; becomes approved version v2). Replaces plan v1 (b60cd6f0).
> Frozen once approved. Progress is recorded with `workflow.py step`, never by editing this plan.

## 1. Goal

Refuse a secret-like agent name, session id or check name before any command runs or any file is written, at every
entry point that persists one: the 15 API functions and the two Claude Code hooks. Make the two affected multi-file
writes (`run_check`, `new_task`) unable to leave a refused or half-created record behind. Keep the F-1 output
guarantee pinned with a scenario that no longer depends on the vulnerability. Document the persistence, detection and
trust-boundary limits that remain. Prepare and test the v1.0.1 backport without tagging, publishing or installing it.

## 2. Current Behavior

Inspected in discovery (records: discovery summary, dependencies.md DEP-2) and during S1–S3:
- **Identity values reach the API unchecked** (before S2):
  - `infra/text.py` L71–72: `agent_name(args)` returns `--agent`, or else `AI_DEV_WORKFLOW_AGENT`, or else
    `unknown-agent`.
  - `infra/text.py` L65–68: `clean_session` drops only empty values, `${…}`, `none` and `null`.
  - The only secret check on them was `save_state` (`store/state.py` L45–48), which scans `state.json` just before
    writing it.
- **`run_check`** wrote the check block (`regenerate_check_block`) before `save_state`. **`new_task`** wrote the
  folder, the six records and `ACTIVE` (through `activate`) before `save_state`. **`resume`** and **`preflight`**
  write `ACTIVE` before `save_state`. A secret-like `--session` was stored in `ACTIVE` and `resume` succeeded.
- **Claude Code hooks** (`aidw/agents/claude_hooks.py`):
  - `hook_claude_pre_edit` (L88–137) takes `session_id` from the payload through `clean_session` (L93).
  - When the active task is unbound and owned by `claude-code`, `unknown-agent` or nobody, it stores that session in
    `ACTIVE` (`active["session"]`, and `preflight_session` when a preflight is pending, then `save_json`, L108–115).
  - It writes the session to the hook log through `_hook_log` (L29–37) when `AI_DEV_WORKFLOW_HOOK_LOG` names a file.
  - When `ACTIVE` is bound to a different session, the edit is allowed ("other session", L104–107).
  - Errors before the gate allow the edit (no active task); errors in the gate deny it.
  - `hook_claude_prompt` (L140–157) only reads and prints a reminder.
- **F-1 pin** (`tests/test_behaviour_pins.py` `LateRefusalTest`): a check name made of `"ghp_" + …` is refused by
  the `state.json` secret check after the command ran. After S2 the same name is refused before the command runs, so
  the pin's output cannot occur any more. In the S1–S3 suite, 195 of 196 tests pass; this pin is the one failure.
- **Exported writers:** `workflow` re-exports `activate`, `add_history`, `add_checkpoint`, `save_state`,
  `save_json`, `write_text` and `regenerate_check_block` (golden `workflow-public-names.txt`). A direct Python call
  to them bypasses any API-level check.
- **File writes:** `write_text` (`infra/text.py` L33–38) writes a temporary file and calls `os.replace`, so each
  file is replaced atomically. There is no fsync, a failed write can leave the temporary file, and there is no
  multi-file transaction or lock (F1.0.5).
- **v1.0.0** is the single-file engine `scripts/workflow.py` (2,996 lines) at tag `v1.0.0`:
  - The same paths exist there: `cmd_new` L2006, `cmd_resume` L2308, `cmd_preflight` L2353, `cmd_run` L2440
    (check block at L2522 before `save_state`), `activate` L889, and the hooks at L2766 and L2809.
  - Its CI runs only on `main` pushes and pull requests. `main` is 14 unreleased commits ahead of the tag.

## 3. Proposed Solution

**API (done in S2–S3, kept):** in `aidw/api.py`, at layer 4.
- `_check_agent(agent)`, then `_check_session(session)` for the three functions that take a session, then the
  check-name check in `run_check`, as the first statements of the 15 functions.
- `run_check` saves `state.json` before rewriting the check block.
- `_create_task` saves the new task's `state.json` before `activate`. On any failure before that save, it removes
  only the files it wrote (and their `write_text` temporary names), then the folder only if it is empty
  (`rmdir`, never `rmtree`). A file it did not write is never removed. The original error is re-raised.

**Shared session rule (S4):**
- `session_problem(session) -> Optional[str]` in `aidw/api.py` returns the refusal message, or `None` for a session
  that passes or that `clean_session` drops. It runs the secret check through `assert_no_secrets` and catches its
  `WorkflowError` to reuse the exact message, then applies the format rule.
- `_check_session` raises `WorkflowError(session_problem(...))`. The messages are unchanged from S2.

**Hooks (S4, FR-12):** in `aidw/agents/claude_hooks.py`, which already imports from `aidw.api`.
- After `clean_session`, `rejected = session_problem(raw) is not None`. A rejected session is replaced by `None` for
  every later use (binding, comparison, log), so it can reach no file.
- **`claude-pre-edit`, rejected session:** find the records and `ACTIVE` as today.
  - No records, no `ACTIVE`, or a task whose `state.json` status is not `active`: allow, as today.
  - An active task: deny with "AIDevWorkflow: this session's id is not valid (it must be 1–256 printable characters
    without spaces and must not look like a credential), so this edit cannot be checked against task '<slug>'.
    Pause the task for unrelated work." The reason never contains the value.
  - The branch never calls `save_json`. If reading the state fails, the edit is denied (fail closed inside an active
    task).
- **Log lines:** for a rejected session, `"session": null, "session_rejected": true`. Lines for valid sessions are
  unchanged: the key is added only when a session was rejected.
- **`claude-prompt`, rejected session:** return without printing.

**F-1 pin re-trigger (S5, FR-13):** `LateRefusalTest` keeps its name and purpose. Its new scenario:
- The script `two_lines.py` prints `line-one`, a synthetic secret-like line (`'token ' + 'ghp_' + 'A' * 36`, built
  when the script runs) and `line-two`, then writes a marker file.
- `aidw.api.save_state` is patched to raise `WorkflowError("Synthetic late refusal after the command ran (test).")`.
- The test asserts the marker file, `token [REDACTED]`, the absence of the token, the line order, exit code 1, and
  equality with the golden file.
- The golden file is replaced by the one generated from an export of `fa6a676` with this exact scenario. Generation
  is already done as evidence: it passes there on Python 3.13 and 3.9. The output is three lines on stdout and the
  refusal on stderr, the same shape as the historical file.
- The docstring explains the change.

**Documentation (S7):**
- CHANGELOG: the Security entry, extended with the hook.
- TECHNICAL_DEBT.md:
  - TD-25 status;
  - TD-27, TD-28, TD-29 (already recorded);
  - a new **TD-30**: the exported internal writers trust boundary, and the centralised persistence check proposed as
    defence in depth.
- report.md: the limits and the assessment (FR-9, FR-10, FR-14).

**Backport preparation (S9, FR-11):** in a separate git worktree on branch `release/1.0.x` from `v1.0.0`.
- Port the same checks into the single-file engine: an agent check and a session check at the top of each recording
  `cmd_*`, the check name in `cmd_run`, the `cmd_run` and `cmd_new` order and clean-up, and the hook rule.
- Add `release/**` to that branch's CI triggers.
- Adapt the TD-25 tests: the CLI and hook classes; the API classes do not apply to v1.0.0.
- Bump to 1.0.1 and add a CHANGELOG section "1.0.1 — Security".
- Show that v1.0.0 fails and the backport passes, and that the full v1.0.0 suite passes.
- Push the branch only, for CI. No tag, release, merge into `main` or install.

## 4. Affected Areas

- **Changed:**
  - `skills/ai-dev-workflow/scripts/aidw/api.py`, `skills/ai-dev-workflow/scripts/aidw/agents/claude_hooks.py`;
  - `tests/test_behaviour_pins.py` (`LateRefusalTest` only), `tests/golden/run-output-before-late-refusal.txt`
    (from `fa6a676`);
  - `CHANGELOG.md`.
- **New:** `tests/test_secret_identity.py` (extended with `HookTest`).
- **Roadmap files (standing rule):** `docs/roadmap/TECHNICAL_DEBT.md`, `PROGRESS.md`, `roadmap-data.js`.
- **Release branch only:** `release/1.0.x` (v1.0.0 files: `scripts/workflow.py`, its tests, CI workflow, CHANGELOG).
- **Unchanged by design:**
  - `aidw/infra/secrets.py`, `aidw/store/`, `aidw/core/`, `aidw/cli/`;
  - every other existing test and golden file;
  - `SKILL.md`, `references/`, `install.py`;
  - the records of other tasks.

## 5. Implementation Steps

- **S1:** Write `tests/test_secret_identity.py` first (FR-8; AC-1 to AC-6, AC-9, AC-10; EC-1 to EC-13). Done:
  - the unfixed engine fails 20 of 23 tests;
  - `5a7576a` fails 14 (API classes skipped), `fa6a676` fails 20;
  - the 3 legitimate-value tests pass everywhere.
- **S2:** Identity checks first in the 15 API functions and the check-name check (FR-1, FR-2, FR-3, FR-6). Done.
- **S3:** `run_check` order, `_create_task` order and own-files clean-up (FR-4, FR-5). Done: 23 of 23 pass, and the
  full suite passes apart from the F-1 pin (S5).
- **S4:** Hooks (FR-12; AC-12; EC-14 to EC-17).
  - Add `HookTest` first and show it fails on the current hook and on `fa6a676`.
  - Then add `session_problem` and the hook changes, and run all hook tests, including the existing
    `test_preflight_and_hooks.py`, unchanged.
- **S5:** F-1 pin (FR-13; AC-13; EC-18). Replace the `LateRefusalTest` scenario and its golden with the `fa6a676`
  output, generated with `AIDW_UPDATE_GOLDEN=1` only in the export. Run it on `fa6a676` and the fixed engine with
  Python 3.13 and 3.9.
- **S6:** Verification through the engine (AC-7, AC-8, DW-3, DW-6):
  - `unit`, `unit-py39`, `privacy`, `ruff`, `mypy`;
  - the byte comparison of every other golden file;
  - the token-pattern grep (expect 0);
  - the exposure check over this repository's records and `ACTIVE`, counts only.
- **S7:** Documentation (FR-9, FR-10, FR-11, FR-14; AC-11, AC-14): CHANGELOG, TECHNICAL_DEBT (TD-25 status, TD-30),
  PROGRESS, `roadmap-data.js`, and the centralised-check assessment for the report.
- **S8:** Publish and review (DW-4, DW-5, DW-8):
  - Commit and push the development branch.
  - CI on Linux, Windows and macOS × Python 3.9/3.13.
  - An independent, security-focused, read-only audit, given the spec, the plan and the diff, not my conclusions.
    It covers every FR and AC, the hook path and the pin change, and verifies that no secret check, gate or refusal
    was weakened.
  - FIXING for anything found.
- **S9:** Backport preparation (FR-11; DW-7). As in §3:
  - a worktree on `release/1.0.x` from `v1.0.0`;
  - port, tests, version 1.0.1, CHANGELOG;
  - v1.0.0 fails, the backport passes;
  - the full v1.0.0 suite passes;
  - push the branch for CI, with no tag.
- **S10:** Final report.
  - Status no higher than `outcome` allows.
  - TD-25 marked "fixed on the development branch; installed copies still affected".
  - The release proposal (tag `v1.0.1`, release notes, optional advisory, merge into `main`, `install.py update` and
    `doctor` on every install) presented for separate approval (DW-9).

## 6. Important Technical Decisions

- **Refuse, not redact.** Every other free-text input is already refused by `assert_no_secrets`. Redacting an
  identity would silently change attribution, and the user would not learn that a credential was typed.
- **Check in the API and in the hooks.** These are the two places where an identity value enters and is persisted.
  The CLI stays a renderer.
- **Check first.** It is simple to verify, and it changes nothing for legitimate values (EC-9).
- **Session format: a bounded structure, not a charset** ("1–256 printable characters, no whitespace"). UUID-only or
  `[A-Za-z0-9._-]` could break other agents' ids. It refuses explicitly. It is not secret detection (FR-10).
- **Agent names: no format rule.** "other" is free text.
- **Hook: one shared rule, fail closed only where gates apply.**
  - Reusing `session_problem` keeps one definition for the CLI and the hooks.
  - Denying inside an active task closes the bypass: today a different session id is allowed as "other session", so
    an invalid id treated as "different" would pass.
  - Allowing outside an active task keeps the hook harmless where there is nothing to gate.
  - The rejected alternative, ignoring the invalid id and continuing as if there were no session, would bind
    nothing. It would then compare `None` with the pending preflight session in ways that depend on earlier state.
- **New task recovery: save before activating, remove only own files.** A journal or transaction would be the
  storage rewrite that was excluded (F1.0.5).
- **`run_check`: save first, then derive the block.** This repairs one ordering. It is not multi-file atomicity:
  if the block write fails, `state.json` is ahead until the next `run` (TD-29, EC-13).
- **F-1 pin: a synthetic trigger and an old-engine golden.** It keeps the regression meaning without relying on a
  defect, and the expected output comes from code that predates the fix.
- **Backport in the single-file engine, no architecture.** The patch release must not carry the F1.0.3/F1.0.4
  refactors or unreleased features.

## 7. Edge Cases

- **EC-1 to EC-13:** as implemented in S1–S3 (refusal before `_task`, the lookup, `execute`, `activate` and
  `mkdir`; the patched failures for EC-12 and EC-13).
- **EC-14:** the existing hook tests, which use sessions such as `S1`, plus a UUID, run unchanged.
- **EC-15:** a rejected session with `ACTIVE` bound to this, another or no session, and owned by another agent. Each
  case is denied while the task is active. `ACTIVE` keeps its bytes, and the log line holds no value.
- **EC-16:** a rejected session without records, without `ACTIVE`, and with a paused task. The edit is allowed, and
  the log has no value.
- **EC-17:** `claude-prompt` with a rejected session prints nothing.
- **EC-18:** the F-1 pin scenario as in §3.
- **Windows:** extra commands are script files; working directories are restored with `try/finally`.

## 8. Testing Plan

`tests/test_secret_identity.py` (synthetic values built at run time; no literal token stored):

| Class | Covers | How |
|---|---|---|
| `CliRefusalTest` | AC-1 to AC-3; EC-1 to EC-7, EC-11 | CLI and a subprocess for `AI_DEV_WORKFLOW_AGENT`; a byte snapshot of `.ai-dev-workflow/` and `.git/info/exclude`; the value absent from output and from every file; the marker absent |
| `ApiRefusalTest` | AC-4 | The 15 functions with a secret-like agent; the 3 session functions with secret-like and malformed sessions |
| `LegitimateValuesTest` | AC-5; EC-8, EC-9 | Placeholder, UUID and 256-character sessions; a placeholder-like agent; ordinary check names; the existing refusal order |
| `RecoveryTest` | AC-9, AC-10; EC-12, EC-13 | Patched failures; a foreign file in the new folder survives |
| `HookTest` (new in S4) | AC-12; EC-14 to EC-17 | `claude-pre-edit` and `claude-prompt` with the hook log enabled. Valid UUID: the same decisions and log as before. Rejected sessions: denial or silence as specified, `ACTIVE` bytes unchanged, a log line with `session_rejected`, the value in no file and no output |

- **Old-engine proof (AC-6, AC-12):** the file is copied into exports of `5a7576a` and `fa6a676`, and the failing
  and passing lists are recorded in verification.md.
- **F-1 pin (AC-13):** `LateRefusalTest` on `fa6a676` and on the fixed engine, with Python 3.13 and 3.9.
- **Existing safety net (AC-7):** the full suite on Python 3.13 and 3.9, the 27 refusal pins, the signature pin, and
  a byte comparison of every golden file except the FR-13 one against the copy taken before S2.
- **Static and privacy (AC-8):** ruff, mypy, `tools/prepublish_check.py`, the token-pattern grep.
- **CI:** the `tests` workflow, 7 jobs, on the development branch, and the same matrix on `release/1.0.x`.
- **Backport (DW-7):** the adapted tests fail on `v1.0.0` and pass on the backport. The full v1.0.0 suite passes in
  the worktree.

## 9. Risks and Dependencies

- **Installed copies stay vulnerable until v1.0.1 is approved, released and installed.** The mitigation until then
  is operational: fixed agent names, and no credentials typed into identity fields.
- **Hook strictness:** a malformed payload session inside an active task now blocks edits. Claude Code sends UUIDs,
  so this happens only with a tampered or broken payload. The denial reason says how to continue (pause the task).
- **False positives:** a legitimate value that looks like a credential is refused, with a reason.
- **Detection limits:** formats unknown to the scanner pass (FR-10).
- **Trust boundary:** direct calls to the exported writers bypass the checks (TD-30). This is documented, not fixed.
- **Backport divergence:** the single-file engine differs structurally. The adapted tests and the full v1.0.0 suite
  are the guard, plus CI on the branch.
- **Dependencies:** DEP-1 to DEP-3 are Verified. The release actions (tag, publish, `main`, installs) wait for the
  owner's separate approval.

**Release proposal (presented in S10, not executed):**
- **R1:** Tag `v1.0.1` on the tested `release/1.0.x` commit and push the tag.
- **R2:** Publish the GitHub release notes: affected versions (≤ 1.0.0, and `main` before the fix), impact, the fix,
  mitigation, and no secret values. Whether to publish a security advisory is the owner's choice.
- **R3:** Merge or port the fix into `main`.
- **R4:** `install.py update` from the v1.0.1 checkout on every install (user and project), then `install.py
  doctor`. Check that `.aidw-install.json` shows 1.0.1, and repeat the CLI and hook regression scenarios against the
  installed copy.
- **R5:** Mark TD-25 **Resolved** only after R4 is verified.

## 10. Expected Result

- Secret-like agent names (from `--agent` or `AI_DEV_WORKFLOW_AGENT`), session ids (from `--session` or a hook
  payload) and check names are refused before anything runs or is written, without being echoed.
- An invalid hook session can neither be persisted nor bypass an active task's gates.
- `new` leaves no partial folder and never removes a file it did not write.
- `verification.md` is written after `state.json`.
- Legitimate use is unchanged.
- The F-1 guarantee stays pinned against old-engine output.
- The remaining persistence, detection and trust-boundary limits are written down.
- The v1.0.1 backport is ready and tested, awaiting the owner's release approval, with TD-25 open until it is
  installed.
