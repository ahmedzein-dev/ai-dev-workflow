# Implementation Plan: F1.0.5 State Store Reliability

> Spec: approved v1 · 0bd712e1 (full SHA-256: 0bd712e1bd5e731e7727582a3a806e8ac75717fe4647d710b2c8bf5418e6bcc6)
> Frozen once approved. Progress is recorded with `workflow.py step`, never by editing this plan.

## 1. Goal

Make per-task state and the ACTIVE pointer validate their format, resist lost concurrent writes, and persist each file durably where the OS permits. Add a preview-first, backed-up and reversible migration protocol without defining a production schema-2 converter or migrating this project's records.

## 2. Current Behavior

- `aidw/store/state.py` reads `state.json`, checks five top-level fields plus stage/status, then adds optional defaults in memory. It does not check `schema` or task ID against the directory. It writes state through `save_state`, updates `ACTIVE` through `activate`, and treats unreadable `ACTIVE` as absent.
- `aidw/infra/text.py` writes a PID-named temporary file and calls `os.replace`, without file/directory fsync or orphan cleanup.
- `aidw/api.py` is the record-writing engine. Its new, discover, review, approve, stage, resume, pause, preflight, step, run, decision and close paths read and then update task state; some also touch ACTIVE, snapshots or verification. `run_check` deliberately saves state before regenerating the verification view; `new_task` saves its state before activation and removes only files it owns on failure (TD-25).
- `aidw/agents/claude_hooks.py` reads task state and ACTIVE, and can write ACTIVE when binding a session. `aidw/cli/main.py` and `cli/commands.py` parse/render commands while calling the API. `workflow.py` is the compatible entry and re-export surface.
- `aidw/core/gates.py` checks approval snapshot hashes and evidence freshness. `tests/test_secret_identity.py` pins TD-25 early identity rejection and rollback order; `tests/test_package.py`, `tests/test_api.py`, golden and hook tests pin package layers and behavior. Existing records in this checkout and the v1.0.0 engine use task schema 1.

## 3. Proposed Solution

1. Keep `state.json` as the source of truth. Add a schema-1 validator beside `load_state` in `store/state.py`: check an integer schema exactly equal to 1, required field/container shapes, legal stage/status and ID/path agreement before in-memory defaults. Permit unknown and historically optional fields. Surface a present corrupt ACTIVE pointer instead of returning None; make the hook deny edits in that affected repository until repaired. No read performs a write.
2. Add `store/lock.py` with an exclusive local file lock (`O_CREAT|O_EXCL`), unique owner token, PID, host and creation time. Keep it inside the existing store layer, with timeout and bounded retry. Acquire the ACTIVE lock before task locks, and multiple task locks in stable slug order; release in reverse order and only if the owner token still matches. Wrap complete API read-modify-write sections and the hook's ACTIVE binding. The short lock scope excludes external check command execution: capture a state digest before execution, reacquire and reload afterwards, then revalidate the intended result against current state or refuse a conflict without discarding another agent's write. Do not conflate this with a transaction across multiple files.
3. On a timed-out lock, consider automatic recovery only for a provably dead same-host process and only after comparing the exact lock identity again. A live PID, PID reuse ambiguity, another host, unreadable metadata or unreliable liveness blocks automatic removal. Explain the task, safe inspection and manual recovery in the error without exposing credentials or silently stealing a lock. Keep lock artifacts git-ignored.
4. Strengthen the shared `infra/text.py` writer with a unique same-directory temp name, flush/fsync before replace, and supported directory sync afterwards. Record a pre-replace failure as no committed replacement; a post-replace sync error as indeterminate durability. On Windows use supported file flush and atomic replacement, and disclose unavailable directory sync. Under the appropriate lock, remove only proven orphan temps next to an existing valid target; preserve ambiguous or sole recovery files. Keep the TD-25 task-creation ownership rules intact.
5. Add `store/migrate.py` for explicit versioned converters and migration/rollback coordination. Add a thin `api.migrate_task` and CLI `migrate <task>` with read-only preview by default, `--apply` for a known conversion and `--rollback` for a verified backup. The approved production registry contains no schema-2 converter. For schema 1, preview reports no applicable migration without writing. Use a test-only converter in isolated repositories to prove backup, apply, retry and rollback behavior. Backup exact bytes under `tasks/<task>/.migrate-backup/`, record source/result digests in local backup metadata, ignore that directory in git, and refuse rollback if the current state digest differs from the migrated result. Preserve approval hashes, history, checks, timestamps and unknown fields; never touch other task records or approved snapshots.
6. Integrate with `cli/main.py`, `cli/commands.py`, the Claude hook and compatible `workflow.py` re-exports only where needed. Keep CLI printing out of the API/store, installed skill standard-library-only, and all valid existing command behavior. Add concise migration/recovery guidance. Use targeted tests and explicit fault injection to validate the invariants before the full suite.

## 4. Affected Areas

- `skills/ai-dev-workflow/scripts/aidw/store/state.py`: schema/ACTIVE validation and task-state access; new `store/lock.py` and `store/migrate.py` for locks and registered conversions.
- `skills/ai-dev-workflow/scripts/aidw/infra/text.py`: durable atomic writer and owned temp cleanup.
- `skills/ai-dev-workflow/scripts/aidw/api.py`: serialized read-modify-write operations, conflict handling and migration API. `agents/claude_hooks.py`: serialized session binding and fail-closed corrupt-pointer handling.
- `skills/ai-dev-workflow/scripts/aidw/cli/main.py`, `cli/commands.py` and `scripts/workflow.py`: new command and compatibility surface, with no gate logic in CLI.
- `.ai-dev-workflow/.gitignore`: local lock and migration-backup artifacts. Focused new tests, existing TD-25/hook/API/golden tests, and migration/recovery user documentation. Existing closed task records and the installed stable skill are excluded.

## 5. Implementation Steps

- **S1:** Freeze test fixtures and baseline evidence before source edits: copy schema-1/v1.0.0 records into temporary test repositories, pin existing CLI/help/golden and TD-25 behavior, and retain the verified Ruff/Mypy baseline below. Do not mutate original task records. (FR-9; EC-1, EC-13; AC-1, AC-9, AC-10)
- **S2:** Implement state schema/shape and ACTIVE validation with focused refusal/compatibility tests; preserve optional defaults and unknown fields, no write on read. (FR-1, FR-8; EC-1–EC-3, EC-12; AC-1, AC-8)
- **S3:** Implement task and ACTIVE lock primitives, deterministic ordering, owner-checked release, bounded wait and conservative stale recovery; test live/dead/ambiguous owners and cross-process contention on each OS. (FR-4, FR-5; EC-8–EC-10; AC-5, AC-6)
- **S4:** Apply locks to API and Claude hook read-modify-write paths. Keep long checks outside the lock, compare/revalidate on commit, and report conflicting result writes after showing command output. Test competing activations, session binding, approvals and check append. (FR-4, FR-8, FR-9; EC-8, EC-9, EC-13; AC-5, AC-8, AC-9)
- **S5:** Strengthen the shared atomic writer, fsync and ownership-aware temp cleanup; inject failures before/after replacement and test Windows sync limits. Preserve TD-25 new-task cleanup and run-check ordering. (FR-6, FR-7, FR-9; EC-5, EC-6, EC-11, EC-14; AC-7, AC-9)
- **S6:** Add migration registry, preview-first CLI/API, ignored byte-exact backups, explicit apply/rollback and conflict detection. Keep production schema-2 conversion absent; test with a test-only converter and fixture repositories. (FR-2, FR-3; EC-4, EC-5, EC-7, EC-15, EC-16; AC-2–AC-4)
- **S7:** Add concise migration/recovery documentation and compatibility/golden updates required solely by the new command; verify no new settings or ordinary-use prompts. (FR-2, FR-5, FR-9; EC-4, EC-10, EC-14; AC-2, AC-6, AC-9)
- **S8:** Run targeted then full validation on the exact final code, compare Ruff/Mypy with the documented pre-feature baseline, run privacy checks and all CI jobs, and record honest platform limits and TD-29/TD-30 residuals. Independent audit follows the official TESTING stage. (FR-1–FR-9; EC-1–EC-16; AC-1–AC-10)

## 6. Important Technical Decisions

- **Migration format:** Keep production schema 1 and deliver an explicit converter protocol; no schema-2 format or real migration is authorized (approved spec decision). Creating schema 2 merely to exercise the command would add churn and let v1.0.1 misread a newer record; an implicit upgrade would violate the roadmap's explicit-migration rule. The test-only converter proves mechanics without claiming a production conversion.
- **Locks:** Prefer local exclusive lock files as TARGET_ARCHITECTURE §4.4 specifies. A single repository lock is simpler but delays unrelated tasks and hooks; OS-specific advisory locks differ across platforms. A task lock plus one ACTIVE lock gives narrow, documented ordering. Protect the entire state read-modify-write section, but never hold a lock over a long external check; detect conflicts at commit.
- **Stale recovery:** A timeout-only deletion is unsafe because a long-running writer can be alive. Recover only with reliable same-host death evidence and an identity recheck; ambiguous cases need human inspection. This favors evidence safety over automatic progress.
- **Durability:** Per-file temp + replace + fsync is the scoped improvement. It is not a multi-file transaction (TD-29), and Windows directory sync cannot be assumed equivalent to POSIX. A post-replace sync error has an uncertain result, so callers must report it honestly.
- **Security boundary:** Preserve TD-25 API identity checks and unchanged secret scanner. Do not add central validation to direct exported writers or remove re-exports under F1.0.5 (TD-30).
- **Interaction cost / D-045:** Ordinary tasks gain no prompt or configuration. A user sees one preview and one explicit apply decision only for a real supported migration; backup, affected file and rollback risk remain visible. More automatic migration would hide consequential changes; a database rewrite adds maintenance without solving the stated scope.

## 7. Edge Cases

- **EC-1–EC-3:** Version/shape validation precedes defaults and all writes; existing optional fields still default only in memory; unknown fields survive. Invalid ID, schema, JSON or containers produce field-specific refusal without content echo.
- **EC-4, EC-15, EC-16:** With no production converter, schema-1 preview is read-only no-op. A test conversion's retry inspects current schema and retained backup before any further action; a lost CLI response never triggers blind reapplication.
- **EC-5–EC-7:** Exclusive backup creation and digest checks precede replacement. Failures before replace preserve source bytes; after replace, report uncertainty. Rollback compares the current digest to the recorded migrated digest and refuses on later edits.
- **EC-8–EC-10:** Task and ACTIVE locks serialize short mutations; delayed checks use conflict detection. Recovery refuses live/ambiguous locks and uses owner token and file identity to avoid deleting another holder's lock.
- **EC-11–EC-12:** Cleanup requires a valid target and proven orphan. Malformed ACTIVE is an error and edit hooks fail closed within its repository.
- **EC-13–EC-14:** TD-25 early identity checks remain before persistence/command execution; sync tests and docs state the actual OS guarantee.

## 8. Testing Plan

- **Pre-feature Ruff/Mypy baseline, independently verified before any source edit:** HEAD `a66a6070f40ecc6c6da6ee9e8303d94f43bbfe78`; working tree had only this new untracked task-record folder. In a temporary virtual environment on macOS/Python 3.13, installed `requirements-dev.txt` pins `ruff 0.17.6` and `mypy 1.20.2`. `python -m ruff check . --no-cache` exited 0 with “All checks passed!” (0 diagnostics). `python -m mypy --no-incremental` exited 0 with “Success: no issues found in 31 source files” (0 diagnostics); mypy cache was outside the repo. The earlier reported 2 Ruff/18 Mypy diagnostics do **not** describe this exact baseline; keep the historical report visible but do not classify nonexistent findings as current debt. Re-run the same pinned configuration on final code; any new diagnostic fails the changed-code criterion. If a future baseline ambiguity prevents reliable comparison, report a blocker, never silently suppress or fix unrelated findings. CI's lint job is also required.
- **AC-1 / EC-1–EC-3:** Schema-1 copies from the current tasks and v1.0.0 fixtures, including omitted optional fields and unknown fields; malformed/wrong-ID/type/unsupported-schema negative tests; byte comparisons before/after read.
- **AC-2–AC-4 / EC-4, EC-5, EC-7, EC-15, EC-16:** No-converter production preview test; injected test converter in temporary repositories; backup-byte/digest assertions; apply/rollback/retry and fault injection at each boundary; verify no other task or approved snapshot changes.
- **AC-5–AC-6 / EC-8–EC-10:** Multiprocess interleavings for task updates, ACTIVE activation and Claude hook binding; delayed `run`; live/dead/ambiguous/PID-reuse lock fixtures and bounded-time assertions. Avoid sleeps as the sole proof; coordinate with synchronization primitives.
- **AC-7–AC-8 / EC-6, EC-11, EC-12, EC-14:** Inject write/fsync/replace/cleanup failures and test same-directory orphan rules; malformed ACTIVE and valid/inactive hook behavior; verify cross-platform expected branches on the actual OS runners.
- **AC-9 / EC-13:** Full TD-25 `test_secret_identity.py`, historical F-1/golden, package/API/lifecycle/hook compatibility, approval/hash/evidence-freshness tests. Golden changes need an explicit explanation limited to new `migrate` help; never regenerate existing expectations merely to pass.
- **AC-10 / all Done-when items:** Full `python -m unittest -v` in `tests/` on Python 3.9 and 3.13; configured privacy scan; pinned Ruff/Mypy with exact diagnostics and baseline comparison; GitHub CI on Ubuntu 24.04, macOS and Windows for both Python versions plus lint. Record exact commit/run links and platform durability limits. Obtain an independent read-only audit before claiming completion.

## 9. Risks and Dependencies

- Shared `write_text` affects every record path; regressions could change output, permissions or approved snapshot handling. Mitigate with fault-injection, current tests and golden comparisons. A mixed v1.0.1/new engine writing the same checkout at once is outside the lock guarantee; tell users to stop old sessions before later installation updates.
- Process liveness is not equally observable on every OS or filesystem. Conservative timeout and manual recovery take precedence over unsafe stale-lock stealing. Lock metadata and backups stay local and git-ignored; privacy checks inspect staged files before any future commit.
- File fsync and atomic replacement do not make ACTIVE, state, snapshots and verification one transaction. Preserve TD-29 and the existing repair guidance; do not report it fixed. Internal exported writers remain outside TD-25 API validation (TD-30). The pattern-based scanner's F-9 limitation remains deferred.
- Existing `new_task` owner-safe rollback and `run_check` late-refusal ordering are security-critical. Any design that changes their guarantees returns to SPECIFICATION for renewed owner approval. No external dependency is open in `dependencies.md`; plan approval and later implementation authorization are separate gates.

## 10. Expected Result

Schema-1 projects continue without migration, with validated state and a more durable per-file write path. Concurrent current-engine commands cannot silently overwrite another successful task/ACTIVE update; uncertain stale locks and post-replace durability are reported honestly. An operator can preview a future registered task-state migration, approve it explicitly, keep a local backup and roll back only when no newer evidence would be lost. TD-25 protections and historical compatibility remain verified; TD-29 and TD-30 remain separately tracked.
