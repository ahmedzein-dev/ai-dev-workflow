# Feature Spec: F1.0.5 State Store Reliability

---

## 1. Requirements

**Goal (one sentence):**
Task state is validated, saved durably, and protected from lost concurrent updates; supported migrations can be previewed and reversed explicitly.

**User story:**
As an AIDevWorkflow user, I want reliable task records and clear recovery actions so that approvals, history and verification evidence remain trustworthy across agents and operating systems.

**Functional requirements:**
- **FR-1:** `load_state` checks `schema` before defaulting or returning data. Support existing task schema 1; refuse absent, boolean, malformed or unsupported schemas without writing. Validate required schema-1 field types, legal stage/status, ID matching the task directory, and core approval, history and check container shapes. Preserve unknown and historically optional fields; reading never rewrites a record.
- **FR-2:** Provide a versioned migration registry and an explicit task-state `migrate` CLI/API operation. Default is read-only dry-run: show source/target schema, affected file, validation result, planned backup and whether any change is available. Apply requires an explicit confirmation flag and a registered converter, then validates source, proposed result, and preservation of approvals, hashes, history, timestamps, checks, and unknown fields. No migration occurs on load, status, resume or hooks. F1.0.5 introduces no production schema 2 conversion because its format is not defined; schema-1 records report no available migration. Exercise the protocol with an isolated test converter, never real records during this task.
- **FR-3:** Before an applicable migration write, create a byte-preserving backup under the task's `.migrate-backup/` as in TARGET_ARCHITECTURE M2, excluded from normal git staging. If backup, validation or conversion fails before replacement, leave source bytes unchanged. Keep the backup after success. Explicit rollback verifies the backup and refuses to overwrite subsequent edits. Never change approved snapshots, spec, plan, verification, or another task as a migration side effect.
- **FR-4:** Serialize task read-modify-write operations with a task lock, acquired exclusively with bounded wait. Serialize `ACTIVE` changes with a separate lock in a documented consistent order. Use unique owner token, process and host metadata; only the owner releases a lock. A long-running check must not hold a lock during command execution: detect an intervening state change before recording and revalidate/merge a compatible append or refuse the conflict, never overwrite a newer state. Read-only status remains available while a check runs.
- **FR-5:** Automatically recover a stale lock only after reliably proving the same-host owner process has died and that the lock is still the observed file. Age alone, host mismatch, inaccessible process status or a live process never justify stealing it. Uncertain locks time out with non-sensitive metadata and a safe manual recovery direction. Lock files are local and git-ignored.
- **FR-6:** Use unique same-directory temporary files, flush and `fsync` file data before atomic replacement, then sync the directory where supported. On Windows use supported file flush and replacement primitives and state the directory-sync limitation, without claiming identical power-loss guarantees. A pre-replace failure leaves the old target intact; a post-replace sync failure is reported as indeterminate, never falsely reported as unchanged.
- **FR-7:** Under the relevant lock, clean only proven orphan temp files of the writer's known naming scheme, when the valid target exists. Preserve unknown files, user files, live-owner temps, sole recovery candidates and backups. A failed write cleans its own proven temp. Read-only operations do not clean up.
- **FR-8:** Validate `ACTIVE` structure and surface a present malformed pointer rather than treating it as no active task. Claude Code edit hooks fail closed inside an active workflow if task identity cannot be validated. Preserve TD-25 early validation of agent, check and session identifiers, including raw/JSON representations and pre-execution refusal; do not broaden the pattern-based scanner here.
- **FR-9:** Preserve CLI/API gates, approval snapshots and hashes, task histories, evidence fingerprints, the historical F-1 output ordering, `workflow.py` compatibility exports, schema-1 config, and valid-session behavior. Use Python 3.9+ standard library on Linux, macOS and Windows. Concurrent mixed old/new engines in one checkout are not guaranteed safe; normal schema-1 use needs no migration or new user settings.

**Out of scope (do NOT build):**
- [ ] Multi-file transactions across `ACTIVE`, `state.json`, snapshots and `verification.md` (TD-29). Per-file durability and locking do not make these one atomic transaction.
- [ ] A central security boundary for direct internal writers or removal of public re-exports (TD-30).
- [ ] `config.json` schema 2 (F1.4.1), events/hash chains, SQLite, stable-install replacement, and migration of real project records during this task.
- [ ] Release/tag changes, completed task records, unrelated technical debt, or changed approval policy.

---

## 2. Edge Cases

| ID | Scenario | Expected Behavior |
|----|----------|-------------------|
| EC-1 | Valid old schema-1 record omits a historically optional field | It loads with the same effective in-memory default; stored bytes and evidence stay unchanged. |
| EC-2 | Schema is absent, boolean, unsupported, or JSON/root is corrupt | Refuse before writing; identify file and problem without echoing content. |
| EC-3 | Record ID differs from directory or core container has wrong shape | Refuse rather than repair or misattribute the task. |
| EC-4 | Dry-run on schema 1 with no registered production converter | Report no available/needed migration; no backup or file change. |
| EC-5 | Backup, converter, or target validation fails | Original bytes remain; clean owned temp; explain recovery. |
| EC-6 | I/O failure occurs before or after atomic replace | Before: previous target intact. After: report indeterminate durability; do not claim rollback. |
| EC-7 | Rollback requested after a later state edit | Refuse overwrite; preserve backup for human reconciliation. |
| EC-8 | Two agents update one task while a check command runs | No successful update is silently lost; result append is revalidated or refused after command output. |
| EC-9 | Two agents activate different tasks or hook binds a session during `ACTIVE` update | Pointer remains valid and represents one complete owner; no lost binding reported as success. |
| EC-10 | Lock owner crashes, PID is reused, host differs, or liveness is unknown | Recover only a proven dead same-host owner; otherwise bounded refusal. |
| EC-11 | Crash leaves a matching temp but target is absent or owner may live | Preserve the temp for recovery; cleanup affects only proven orphans beside a valid target. |
| EC-12 | `ACTIVE` is malformed during a Claude edit hook | Deny an edit in the affected repository and give repair direction; do not silently classify as inactive. |
| EC-13 | Recognized secret-like identity is provided with concurrent/migration activity | TD-25 refuses before execution/persistence; absent from state, `ACTIVE`, verification and hook logs. |
| EC-14 | Directory sync is unsupported on Windows or another platform | Record the actual available guarantee; still use atomic replace and supported file flush. |
| EC-15 | A user retries an apply command after it already succeeded | The new schema is recognized and reported; no second conversion or overwrite of the original backup occurs. |
| EC-16 | Migration succeeds but its CLI response is lost | A later dry-run inspects current schema and backup, and reports actual state without assuming the first attempt failed. |

---

## 3. Constraints (must NOT change)

- **Protected files / modules:** Completed task records and approved snapshots; stable v1.0.1 installation; published release/tag; unrelated roadmap and feature files. Discovery/review changes only this task's new records.
- **Public contracts:** `workflow.py` remains the entry point and existing valid-path commands, options, output, exit behavior and compatibility exports remain. A new migration command may be added. Schema-1 config and mandatory gates remain.
- **Allowed packages:** Python standard library only, compatible with Python 3.9 and 3.13 on Linux, macOS and Windows.
- **Architecture:** Extend inspected `aidw/store/state.py`, `aidw/infra/text.py`, `aidw/api.py`, CLI and Claude hook paths. Small `store/migrate.py` and `store/lock.py` follow TARGET_ARCHITECTURE §4.4. CLI calls the API; no parallel store, events or SQLite.
- **Scope:** Task-state schema validation, task and `ACTIVE` locks, durable file writes, orphan temp handling, explicit task-state migration protocol, focused tests and recovery guidance. TD-29 and TD-30 remain separate.
- **Product experience / D-045:** Normal use adds zero prompts/settings. Optional migration shows preview then requires one explicit apply decision because it changes evidence; rollback is exceptional. Lead with the recommendation; make affected files, backup, risks and details visible. This architectural change has a small interaction surface. Silent upgrades violate explicit control, and a database adds unnecessary distribution and maintenance cost.
- **If anything is unclear:** stop and ask. Do not guess. The proposed absence of a production schema bump needs owner review with this specification before planning.

---

## 4. Acceptance Criteria

- **AC-1:** Given copies of existing schema-1 records and v1.0.0 fixtures, when loaded, then bytes and historical effective behavior remain; invalid schema/shape fixtures refuse without write.
- **AC-2:** Given schema 1 without a production converter, when `migrate` runs its default dry-run, then it states no applicable migration and creates no backup or state change.
- **AC-3:** Given a registered test converter and temporary repository, when dry-run, explicit apply and rollback run, then preview is read-only, backup matches source bytes, result validates, and rollback restores those bytes only if no later edit occurred.
- **AC-4:** Given injected backup, conversion, validation, write and rollback-conflict failures, when migration runs, then no approval, evidence or unrelated task file is overwritten, and error/recovery are explicit.
- **AC-5:** Given concurrent writers and a delayed check, when task and `ACTIVE` updates overlap, then all successful writes remain and no stale snapshot replaces newer state.
- **AC-6:** Given live, dead, ambiguous and reused-owner lock fixtures, when a writer waits, then it recovers only proven stale locks and otherwise times out without stealing.
- **AC-7:** Given write fault injection and orphan temps, when writer/cleanup run, then pre-replace target survives, post-replace uncertainty is reported, owned temps are removed and ambiguous files preserved.
- **AC-8:** Given malformed `ACTIVE` and valid active-task fixtures, when status/hooks inspect them, then corruption is surfaced and protection fails closed; valid-session and inactive behavior remain compatible.
- **AC-9:** Given TD-25 security and F-1/golden regressions, when run on final code, then early refusal, no sensitive persistence, output ordering, approvals and compatibility remain valid.
- **AC-10:** Given a documented pre-feature repository-wide Ruff and Mypy baseline from commit `a66a6070f40ecc6c6da6ee9e8303d94f43bbfe78` (including exact diagnostics and tool configuration) and the exact final code, when unit/security/migration checks, Ruff, Mypy and privacy scan run on Python 3.9/3.13 locally and CI runs on Ubuntu/macOS/Windows, then exact results and platform durability limits are reported. Compare repository-wide lint/type results with that baseline: changed code introduces no new diagnostics, every existing diagnostic remains visible and classified as pre-existing only when the baseline proves it, and neither tool is called passing if it still reports findings. If existing findings prevent reliable validation of changed code, report a blocker rather than success; do not fix or suppress unrelated debt under this feature.

**Done when:**
- [ ] Requirements implemented within an approved plan; no real project-record migration during this feature.
- [ ] Edge cases tested in isolated temporary repositories.
- [ ] Unit, TD-25, compatibility, golden, migration, concurrency and privacy checks pass on the exact final code; CI evidence covers both Python versions on all three OSes. Run Ruff and Mypy, report their exact results, and compare each diagnostic against the documented pre-feature baseline (the previously reported 2 Ruff and 18 Mypy findings require verification). Changed code has no new diagnostics; pre-existing findings are not reported as passing, new findings are never labelled pre-existing, and unrelated debt is neither silently fixed nor suppressed. Report a blocker if baseline findings prevent reliable validation of changed code.
- [ ] User guidance explains preview, backup, rollback and platform durability limits; TD-29 and TD-30 remain open.
- [ ] Independent audit reviews evidence preservation, security and the D-045 interaction assessment.
