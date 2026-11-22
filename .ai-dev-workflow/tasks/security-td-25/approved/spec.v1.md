# Feature Spec: TD-25 — keep secret-like check names, agent names and session ids out of task records

---

## 1. Requirements

**Goal (one sentence):**
A secret-like value given as a check name, an agent name or a session id is refused before the engine runs anything or writes anything, so it can never reach `state.json`, `ACTIVE`, `verification.md` or any other persistent output, and the fix reaches installed copies through a patch release.

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

  The 27 pinned refusals, the late-refusal pin, the signature pin and every existing golden file pass unchanged.
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
- **FR-11:** Remediation status and patch release:
  - **This task fixes the development branch only.** TD-25 is marked "fixed on the development branch; installed copies still affected", not resolved.
  - A follow-up task delivers **v1.0.1**, a security patch release built from the `v1.0.0` tag with only this fix ported: no unreleased features. It needs its own spec and plan approvals. Tagging, publishing the release and updating installs each need the owner's explicit approval.
  - Its outline is part of this task's plan: port the fix and tests to the v1.0.0 engine, show that v1.0.0 fails and v1.0.1 passes, run CI, tag, publish release notes, then `install.py update` and `install.py doctor` on every install. `main` also gets the fix.
  - TD-25 is resolved only after v1.0.1 is installed and verified.

**Out of scope (do NOT build):**
- [ ] TD-24 (`preflight --json` trailing text), TD-26 (`init --update --commit` order), TD-27 and TD-28 (below) stay separate tracked defects. They change only if a change is strictly necessary to remove the TD-25 vulnerability; none is today.
- [ ] TD-27: `approve` freezes a spec or plan whose content holds a secret into the read-only approved snapshot without scanning it first. The content is written by the author, not by the engine, and `preflight` and `check` flag it later.
- [ ] TD-28: other refusal messages echo user input to the terminal, for example `--add-check … got '<spec>'` or `There is no check '<id>' to remove`, and check names that contain `|` or line breaks break the check table in `verification.md`.
- [ ] TD-29 itself: transactional multi-file updates, fsync, temporary-file cleanup and locking. These belong to F1.0.5.
- [ ] The Claude Code hook storing the session id from Claude Code's own hook payload into `ACTIVE`. This is a generated id, not typed input; the hook must never block an edit on its own errors.
- [ ] New secret patterns, or changes to `find_secrets`, `redact` or the placeholder rule.
- [ ] Rewriting or migrating existing records or an existing `ACTIVE` file. The exposure check found no secret-like value in this repository's records.
- [ ] The v1.0.1 release itself: it is the follow-up task of FR-11.

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

---

## 3. Constraints (must NOT change)

- **Protected files / modules:**
  - `SKILL.md`, `references/`, `assets/`, `install.py`, `index.html`, `tools/`, `docs/` apart from the roadmap files;
  - every existing golden file;
  - every existing test;
  - other tasks' records: historical reports and findings are never rewritten;
  - `aidw/infra/secrets.py`;
  - `aidw/store/` (the write order changes inside `api.py` only).
- **Public contracts:** for legitimate values (FR-7), the CLI (commands, options, help, outputs, exit codes), record formats and approval gates. The only intended changes are the new refusals of FR-1 to FR-3. The names and call signatures importable from `workflow` stay unchanged (signature pin).
- **Allowed packages:** Python standard library only, Python 3.9+. No new packages without approval.
- **Architecture:** TARGET_ARCHITECTURE §2–3 and the F1.0.4 layering: the checks live in the API (level 4); the CLI stays a renderer and gains no logic; the core never prints.
- **Scope:**
  - `scripts/aidw/api.py`: the checks of FR-1 to FR-3 and the write order and cleanup of FR-4 and FR-5;
  - a new `tests/test_secret_identity.py`;
  - a "Security" entry under "Unreleased" in `CHANGELOG.md`;
  - in `docs/roadmap/`: the TD-25 status and new TD-27, TD-28 and TD-29 rows in TECHNICAL_DEBT.md, PROGRESS.md, `roadmap-data.js`.
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
- **AC-7:** Given the full suite, when it runs on Python 3.13 and 3.9, then every test passes and no existing test or golden file changed. This includes the 27 refusal pins, the late-refusal pin and the signature pin.
- **AC-8:** Given the change, when ruff, mypy and the `privacy` check run, then all report no issues, and no file in the repository contains a literal secret-like test value.
- **AC-9:** Given the simulated failure of EC-12, when `new` fails, then no folder for that task exists, `ACTIVE` and the other task's files are byte-identical, and the original exception type reaches the caller.
- **AC-10:** Given the simulated failure of EC-13, when `run` fails, then the error reaches the caller and `state.json` holds the entry. When the next `run` succeeds, then the check block matches `state.json`.
- **AC-11:** Given the report and TECHNICAL_DEBT.md, when the task reaches its final report, then each of these is written down:
  - the detection-control limits of FR-10;
  - the persistence limits of FR-9 (TD-29);
  - TD-25 as "fixed on the development branch; installed copies still affected";
  - TD-27 and TD-28 as separate open items;
  - the v1.0.1 follow-up task of FR-11, proposed with its outline.

**Done when:**
- [ ] All requirements implemented
- [ ] All edge cases handled as specified
- [ ] Required tests pass through the engine: `unit`, `unit-py39`, `privacy`, `ruff`, `mypy`
- [ ] CI (`tests` workflow) passes on Linux, Windows and macOS with Python 3.9 and 3.13 on the pushed commit
- [ ] An independent read-only audit finds no Important issue left open, and specifically verifies that no existing secret check or gate was weakened
- [ ] Exposure check after the fix: the secret scanner over this repository's task records and its `ACTIVE` file reports counts only, never values
- [ ] TD-25 marked "fixed on the development branch; installed copies still affected", and the v1.0.1 follow-up task proposed; F1.0.4's report and findings stay unchanged
