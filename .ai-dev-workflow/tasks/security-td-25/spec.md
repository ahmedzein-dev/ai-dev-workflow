# Feature Spec: TD-25 — keep secret-like check names, agent names and session ids out of task records (v2)

---

## 1. Requirements

**Goal (one sentence):**
A secret-like value given as a check name, an agent name or a session id is refused before the engine runs anything or writes anything, so it can never reach `state.json`, `ACTIVE`, `verification.md`, the hook log or any other persistent output, whether it comes from the command line or from a Claude Code hook payload, and the fix reaches installed copies through a patch release.

**User story:**
As an owner whose task records may be committed to git (`records.commit=all`), I want the engine to refuse a credential typed into an identity field before any record is written, so that a slip of the hand never persists a secret in the repository or on disk.

**Functional requirements:**
- **FR-1:** Every API function that takes `agent` checks it with the existing secret check (`assert_no_secrets` from `aidw/infra/secrets.py`) as its **first** step, before any other check, any record write and any command execution. These are the 15 functions `init_project`, `update_setup`, `new_task`, `record_discovery`, `review`, `approve`, `stage`, `resume`, `pause`, `preflight`, `step`, `run_check`, `scope`, `decision` and `close`. The refusal is a `WorkflowError` with the existing wording: "Refusing to save the agent name: it looks like it contains a secret — <kind> (line <n>). …". This covers both `--agent` and `AI_DEV_WORKFLOW_AGENT`, because the CLI resolves both into the `agent` parameter, and both are tested.
- **FR-2:** `new_task`, `resume` and `preflight` check `session` in the same first step, after the agent check. The value checked is the one `clean_session` keeps; a missing session and the placeholders it already drops (`${…}`, `none`, `null`) behave as today. Two checks apply, in this order, and neither message contains the value:
  - the secret check, naming "the session id";
  - a bounded format check: 1 to 256 characters, every character printable, none of them whitespace. The refusal is "The session id must be 1–256 printable characters without spaces." UUIDs (Claude Code's `${CLAUDE_SESSION_ID}`) and other single-token ids pass. Values that cannot be a session id are refused explicitly, never dropped silently: line breaks, tabs, control or invisible format characters, or more than 256 characters.
- **FR-3:** `run_check` checks the `check` name with the same secret check, with "the check name" as the place named in the message. This happens right after the agent check, before the configured-check lookup and before the "Unknown check '<name>'" message, so the refusal never echoes the value. It applies to configured and extra (`-- <command>`) checks alike, and the extra command is not executed.
- **FR-4:** In `run_check`, `verification.md` is written only after `state.json` has been saved. A refusal by the secret check of `state.json`, for any reason, therefore changes no task record. If writing `verification.md` fails after `state.json` was saved, the error reaches the caller; it is never swallowed. The check block is derived from `state.json`, and the next `run` of any check rewrites it completely.
- **FR-5:** `new_task` cannot leave a partial task:
  - A refusal under FR-1 or FR-2 happens before anything is written. That means no task folder, no `ACTIVE` change, no change to the task it would have paused, and no git exclude change.
  - The new task's `state.json` is saved before the task is activated: before `ACTIVE` is written and before another active task is paused.
  - If anything fails after the task folder is created and before its `state.json` is saved, the folder created by this call is removed before the error is raised.
  - A later `new_task` with the same name and safe values succeeds.
- **FR-6:** When a value is refused under FR-1 to FR-3, it is written to no persistent output. That covers `state.json`, `ACTIVE`, `verification.md`, the other task records and approved snapshots, `config.json`, `PROJECT.md`, the records `.gitignore` and the git exclude rules. It also appears in neither stdout nor stderr: the refusal names only the field and, for the secret check, the kind of secret and the line.
- **FR-7:** For legitimate values, behaviour is unchanged. Legitimate values are the values both checks accept: for example `claude-code`, `unknown-agent`, UUID session ids, and check names like `unit`, `unit-py39` or `smoke test`. Unchanged covers:
  - outputs, exit codes and record formats;
  - the order of every existing refusal and every approval gate;
  - the files written on success, with the same content. Only the order of the writes inside `new_task` (FR-5) and `run_check` (FR-4) changes.

  The 27 pinned refusals, the signature pin and every existing golden file pass unchanged, with one approved exception (FR-13): the late-refusal pin, whose historical scenario depended on this vulnerability.
- **FR-8:** Regression tests cover the whole write path, not only `save_state`:
  - **Paths:** task creation (alone and while another task is active), activation, `resume`, `pause`, `preflight`, check execution (configured check, extra command, unknown name without `--`), `init` and `init --update`, and every other API function of FR-1.
  - **Values:** synthetic secret-like values built at run time. The agent name is tested through `--agent` and through `AI_DEV_WORKFLOW_AGENT`.
  - **Assertions:** every test checks the refusal and its field. It also checks that the value is absent from stdout and stderr, and takes a byte snapshot of every file under `.ai-dev-workflow/` plus `.git/info/exclude`, which must be unchanged. For `run`, it checks that the extra command did not run (a marker file is absent). Exit codes alone are never enough.
  - **Old engine:** the tests fail on the current engine, shown by running them against exports of `5a7576a` (CLI paths) and `fa6a676` (CLI and API paths), and pass on the fixed engine.
- **FR-9:** The persistence limits that remain are documented in the report and in TECHNICAL_DEBT.md (TD-29, linked to F1.0.5). These are not fixed here; this task is not a storage rewrite.
  - Each file is replaced atomically (temporary file, then `os.replace`), but without fsync, and a failed write can leave a temporary file.
  - Updates to several files are not transactional. `resume`, `preflight` and the pausing of another task write `ACTIVE` or another task's `state.json` before the task's own `state.json`. An I/O failure between those writes leaves them disagreeing.
  - The documented recovery is `status`, then `resume <task>` or `pause <task>`, which rewrite `ACTIVE`, and any `run`, which rewrites the check block.
- **FR-10:** The report and the TD-25 entry state the limits of this control:
  - `assert_no_secrets` is a pattern-based detection control. It is not a guarantee that every secret is recognised: a credential in a format the scanner does not know still passes.
  - The session format check bounds structure, not secrecy.
  - Agent names keep free text (documented values include "other"), so they get no format restriction.
- **FR-11:** Remediation status and the v1.0.1 security backport:
  - **This task fixes the development branch and prepares the backport; it does not remediate installed copies.** TD-25 is marked "fixed on the development branch; installed copies still affected", not resolved.
  - **Backport preparation (in this task):**
    - Branch `release/1.0.x` from the tag `v1.0.0`.
    - Port only the TD-25 fix (FR-1 to FR-6 and the hook fix of FR-12) into the v1.0.0 engine (the single `scripts/workflow.py`), without later architectural changes: no package split, no API layer, no features from `main` or Phase 1.
    - Adapt the TD-25 regression tests to v1.0.0. Show that they fail on `v1.0.0` and pass on the backport, and that the full v1.0.0 suite passes.
    - Prepare version 1.0.1 and a CHANGELOG section "1.0.1 — Security".
    - Test the branch independently of the development branch: a separate checkout (git worktree), plus CI on the pushed release branch. This is a branch push only, with no tag.
  - **Not authorised by this task, each needing the owner's separate explicit approval:** creating or pushing the tag `v1.0.1`, publishing a GitHub release or security advisory, merging the fix into `main`, and updating any installed environment (`install.py update`, then `install.py doctor`). They are presented as a release proposal with the evidence.
  - TD-25 is resolved only after the approved v1.0.1 release is installed and verified.
- **FR-12:** The Claude Code hooks treat the session id in their payload as untrusted input. Both `claude-pre-edit` and `claude-prompt` apply the session rules of FR-2 (secret check, then the format rule) through the same function the API uses, after `clean_session`. A payload session that fails them is an **invalid session**:
  - It is never written to `ACTIVE`, to the hook log (`AI_DEV_WORKFLOW_HOOK_LOG`) or to any other file. The log line records `"session": null` and `"session_rejected": true` instead.
  - It is never printed. A denial reason names only the rule ("this session's id is not valid…"), never the value.
  - `claude-pre-edit` fails closed: when the repository has an `ACTIVE` task whose `state.json` status is `active`, the edit is denied. This holds whatever the binding (bound to another session, unbound, another agent), so an invalid session can never bypass the gates. Without an active task, or with a paused or closed one, the edit is allowed as today, because no gates apply.
  - `claude-prompt` prints no reminder for an invalid session and writes nothing.
  - Valid sessions keep today's hook behaviour exactly; all existing hook tests pass unchanged. The skill stays manual-only: the hooks still act only inside the task started in that session.
- **FR-13:** The F-1 regression pin (`LateRefusalTest` in `tests/test_behaviour_pins.py`) keeps its purpose: when `run` is refused after the command ran, the command's redacted output is still printed first. Its historical trigger, a secret-like check name refused by the `state.json` secret check after the command ran, is exactly the TD-25 path, which now refuses before the command runs. The scenario changes as follows:
  - The trigger becomes a controlled synthetic `WorkflowError` raised by `save_state` (patched in `aidw.api`) after the command ran.
  - The command is a script file that prints `line-one`, a synthetic secret-like line and `line-two`, then creates a marker file. The test asserts that the marker exists (the command ran), that the secret-like line is printed redacted, the stdout/stderr split, the order of the lines and the exit code.
  - The golden file `run-output-before-late-refusal.txt` is **regenerated from the pre-fix engine `fa6a676`**, never from the fixed implementation, and the fixed engine must match it. The test docstring explains why the historical scenario changed.
  - The rejection of secret-like check names before execution stays covered by the separate TD-25 tests (FR-3, EC-1, EC-2).
- **FR-14:** Trust boundary and defence in depth, documented and assessed only:
  - The engine re-exports internal writing functions from `workflow` for compatibility, for example `activate`, `save_state`, `save_json`, `write_text`, `add_history` and `regenerate_check_block`. A direct Python call to them bypasses the API-level validation of FR-1 to FR-3. The report and TECHNICAL_DEBT.md (**TD-30**) state this; no claim is made that every direct Python invocation is protected.
  - The report assesses a centralised persistence check (for example a secret scan of every write under `.ai-dev-workflow/`) as a separate defence-in-depth improvement: benefits, costs, false-positive risk and the approach. It is not implemented in TD-25 and is not a storage redesign.

**Out of scope (do NOT build):**
- [ ] TD-24 (`preflight --json` trailing text), TD-26 (`init --update --commit` order), TD-27 and TD-28 (below) stay separate tracked defects. They change only if a change is strictly necessary to remove the TD-25 vulnerability; none is today.
- [ ] TD-27: `approve` freezes a spec or plan whose content holds a secret into the read-only approved snapshot without scanning it first. The content is written by the author, not by the engine, and `preflight` and `check` flag it later.
- [ ] TD-28: other refusal messages echo user input to the terminal, for example `--add-check … got '<spec>'` or `There is no check '<id>' to remove`, and check names that contain `|` or line breaks break the check table in `verification.md`.
- [ ] TD-29 itself: transactional multi-file updates, fsync, temporary-file cleanup and locking. These belong to F1.0.5.
- [ ] A centralised persistence check or any change to the exported internal writers (FR-14: documented and assessed only, TD-30).
- [ ] New secret patterns, or changes to `find_secrets`, `redact` or the placeholder rule.
- [ ] Rewriting or migrating existing records or an existing `ACTIVE` file. The exposure check found no secret-like value in this repository's records.
- [ ] Tagging, publishing and installing v1.0.1, and merging into `main` (FR-11): separate approvals.

---

## 2. Edge Cases

| ID | Scenario | Expected Behavior |
|----|----------|-------------------|
| EC-1 | `run <task> <secret-like name> -- <command>` | Refused with "Refusing to save the check name: …"; the command is not executed; every file under `.ai-dev-workflow/` stays byte-identical; the value is not in stdout or stderr; same exit code as other refusals |
| EC-2 | `run <task> <secret-like name>` without `--` (not a configured check) | The secret refusal of EC-1 comes instead of "Unknown check '<name>'", so the value is not echoed |
| EC-3 | `run <task> smoke --agent <secret-like value> -- <command>` | Refused with "Refusing to save the agent name: …" before the command runs; `verification.md` and `state.json` unchanged |
| EC-4 | `AI_DEV_WORKFLOW_AGENT=<secret-like value>` and no `--agent`, for any recording command | The same refusal as EC-3, from the value the CLI resolves |
| EC-5 | `resume`, `preflight` or `new` with a secret-like agent name | Refused before `ACTIVE` is written; `ACTIVE` keeps its bytes (or stays absent) and the task's status is unchanged |
| EC-6 | `new <task> --agent <secret-like value>` while another task is active | Refused before anything is written: no task folder, the other task stays active and unchanged, `ACTIVE` and the git exclude rules are unchanged |
| EC-7 | `new`, `resume` or `preflight` with `--session <secret-like value>` | Refused with "Refusing to save the session id: …" (today `resume` succeeds); `ACTIVE` and `state.json` unchanged |
| EC-8 | Placeholder-like and legitimate values: `--session '${CLAUDE_SESSION_ID}'`, a UUID session, `--agent 'api_key=changeme'` | Not refused: the placeholder is dropped by `clean_session` as today, the UUID passes both session checks, and the agent passes the placeholder rule as today |
| EC-9 | Both a secret-like agent and another refusal condition (for example a bad task name in `new`) | The agent refusal comes first (FR-1); with a legitimate agent, the other refusal is unchanged (FR-7) |
| EC-10 | An `ACTIVE` file written earlier by an unfixed engine that holds a secret-like agent or session | Not read for secrets and not migrated. The report explains that `pause <task>` deletes `ACTIVE`, and the exposure check reports whether this repository's `ACTIVE` is affected (counts only) |
| EC-11 | `--session` with a line break, a tab, a space, a zero-width character, or 257 characters | Refused with "The session id must be 1–256 printable characters without spaces."; nothing written; the value not echoed. A 256-character single-token id passes |
| EC-12 | An I/O error in `new` after the task folder is created and before its `state.json` is saved (simulated in a test) | The folder created by this call is removed, `ACTIVE` and any other task are unchanged, and the original error reaches the caller |
| EC-13 | An I/O error writing `verification.md` in `run` after `state.json` was saved (simulated in a test) | The error reaches the caller (not swallowed, output tail kept as today); `state.json` holds the new entry; the next `run` of any check rewrites the check block from `state.json` |
| EC-14 | `claude-pre-edit` and `claude-prompt` with a valid UUID session (and the existing `S1`-style test sessions) | Exactly today's behaviour: binding, gate decisions, reminders and log lines unchanged |
| EC-15 | `claude-pre-edit` with a secret-like or malformed payload session while an active task's gates apply (bound to this, another or no session; another agent) | The edit is denied with a reason that does not contain the value; `ACTIVE` keeps its bytes; the hook log line has `"session": null` and `"session_rejected": true`; the value is in no file |
| EC-16 | `claude-pre-edit` with an invalid payload session and no active task, or a paused or closed task | Allowed as today; nothing is written except a log line without the value (when the log is enabled) |
| EC-17 | `claude-prompt` with an invalid payload session | No reminder is printed and nothing is written |
| EC-18 | The F-1 pin: `run` whose command prints output and then `save_state` raises a synthetic `WorkflowError` | stdout holds the command's lines in order, with the secret-like line redacted; stderr holds the refusal; exit code 1; the marker file exists; the output equals the golden recorded from `fa6a676` |

---

## 3. Constraints (must NOT change)

- **Protected files / modules:**
  - `SKILL.md`, `references/`, `assets/`, `install.py`, `index.html`, `tools/`, `docs/` apart from the roadmap files;
  - every existing golden file;
  - every existing test, except the `LateRefusalTest` scenario and its golden file (FR-13);
  - other tasks' records: historical reports and findings are never rewritten;
  - `aidw/infra/secrets.py`;
  - `aidw/store/` (the write order changes inside `api.py` only);
  - `aidw/agents/` apart from the session handling in `claude_hooks.py` (FR-12).
- **Public contracts:** for legitimate values (FR-7), the CLI (commands, options, help, outputs, exit codes), record formats and approval gates. The only intended changes are the new refusals of FR-1 to FR-3. The names and call signatures importable from `workflow` stay unchanged (signature pin).
- **Allowed packages:** Python standard library only, Python 3.9+. No new packages without approval.
- **Architecture:** TARGET_ARCHITECTURE §2–3 and the F1.0.4 layering: the checks live in the API (level 4); the CLI stays a renderer and gains no logic; the core never prints.
- **Scope:**
  - `scripts/aidw/api.py`: the checks of FR-1 to FR-3, a shared session-rule function, and the write order and cleanup of FR-4 and FR-5;
  - `scripts/aidw/agents/claude_hooks.py`: the session handling of FR-12;
  - a new `tests/test_secret_identity.py`;
  - `tests/test_behaviour_pins.py` (`LateRefusalTest` only) and `tests/golden/run-output-before-late-refusal.txt` (regenerated from `fa6a676`), FR-13;
  - a "Security" entry under "Unreleased" in `CHANGELOG.md`;
  - in `docs/roadmap/`: the TD-25 status and the TD-27 to TD-30 rows in TECHNICAL_DEBT.md, PROGRESS.md, `roadmap-data.js`.
- **Secrets during the work:** no real secret is inspected, printed or written. Tests and checks use only synthetic values built at run time, and exposure checks report counts, never values.
- **If anything is unclear:** stop and ask. Do not guess.

---

## 4. Acceptance Criteria

- **AC-1:** Given a temporary repository, when each command of EC-1 to EC-7 and EC-11 runs with the synthetic value in the stated field, then three things hold:
  - it is refused with a message that names the field;
  - neither stdout nor stderr contains the value;
  - every file under `.ai-dev-workflow/` and `.git/info/exclude` is byte-identical before and after.
- **AC-2:** Given `run` with a secret-like check name or agent name and an extra command that creates a marker file, when it is refused, then the marker file does not exist.
- **AC-3:** Given a secret-like agent name for `new` while another task is active, when it is refused, then no task folder exists and the other task's `state.json`, `ACTIVE` and the git exclude rules are byte-identical. A later `new` with the same name and a legitimate agent succeeds.
- **AC-4:** Given the 15 API functions of FR-1, when a test calls each one with the secret-like value as `agent` on a repository prepared for that call, then each raises `WorkflowError` naming the agent name, and nothing under `.ai-dev-workflow/` changes. The same holds for the three functions of FR-2 with a secret-like or malformed `session`. The `AI_DEV_WORKFLOW_AGENT` path is covered through the CLI.
- **AC-5:** Given the legitimate values of EC-8, when the commands run, then they behave exactly as on the current engine.
- **AC-6:** Given the new regression tests, when they run against exports of `5a7576a` and `fa6a676`, then every test that covers a DEP-2 scenario fails. When they run against the fixed engine, all pass. The failing and passing lists are recorded in verification.md.
- **AC-7:** Given the full suite, when it runs on Python 3.13 and 3.9, then every test passes and no existing test or golden file changed. This includes the 27 refusal pins and the signature pin; the late-refusal pin is the FR-13 exception.
- **AC-8:** Given the change, when ruff, mypy and the `privacy` check run, then all report no issues, and no file in the repository contains a literal secret-like test value.
- **AC-9:** Given the simulated failure of EC-12, when `new` fails, then no folder for that task exists, `ACTIVE` and the other task's files are byte-identical, and the original exception type reaches the caller.
- **AC-10:** Given the simulated failure of EC-13, when `run` fails, then the error reaches the caller and `state.json` holds the entry. When the next `run` succeeds, then the check block matches `state.json`.
- **AC-11:** Given the report and TECHNICAL_DEBT.md, when the task reaches its final report, then each of these is written down:
  - the detection-control limits of FR-10;
  - the persistence limits of FR-9 (TD-29);
  - TD-25 as "fixed on the development branch; installed copies still affected";
  - TD-27 and TD-28 as separate open items;
  - the v1.0.1 follow-up task of FR-11, proposed with its outline.

- **AC-12:** Given the hook tests, when `claude-pre-edit` and `claude-prompt` run with a valid UUID, with each malformed session of EC-11 and with both synthetic secret-like sessions, in the situations of EC-14 to EC-17 and with the hook log enabled, then valid sessions behave as before and invalid ones are denied or silent as specified. For invalid ones, `ACTIVE` and every record keep their bytes, the hook log holds no value and records `session_rejected`, and the value is in no output. These tests fail on `fa6a676`.
- **AC-13:** Given `tests/golden/run-output-before-late-refusal.txt` regenerated from `fa6a676` with the FR-13 scenario, when `LateRefusalTest` runs on `fa6a676` and on the fixed engine, with Python 3.13 and 3.9, then both match it. The marker file proves that the command ran, and the redacted line, the order, the stream split and the exit code are asserted.
- **AC-14:** Given the report and TECHNICAL_DEBT.md, when the task reaches its final report, then the exported-writer trust boundary (TD-30) and the assessment of a centralised persistence check are written down, without claiming protection for direct Python calls.

**Done when:**
- [ ] All requirements implemented
- [ ] All edge cases handled as specified
- [ ] Required tests pass through the engine: `unit`, `unit-py39`, `privacy`, `ruff`, `mypy`
- [ ] CI (`tests` workflow) passes on Linux, Windows and macOS with Python 3.9 and 3.13 on the pushed commit
- [ ] An independent read-only audit finds no Important issue left open, and specifically verifies that no existing secret check or gate was weakened
- [ ] Exposure check after the fix: the secret scanner over this repository's task records and its `ACTIVE` file reports counts only, never values
- [ ] The v1.0.1 backport branch is prepared and tested independently (v1.0.0 fails the adapted tests, the backport passes them and the full v1.0.0 suite, CI on the release branch), with no tag, release or install
- [ ] The independent audit is security-focused and covers the hook path and the FR-13 pin change
- [ ] TD-25 marked "fixed on the development branch; installed copies still affected", and the release proposal (tag, release, `main`, installs) presented for separate approval; F1.0.4's report and findings stay unchanged
