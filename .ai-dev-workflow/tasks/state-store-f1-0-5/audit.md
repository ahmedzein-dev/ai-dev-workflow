# Audit: F1.0.5 State Store Reliability

**Review independence:** subagent
**Reviewer:** Codex (`/root/f105_audit`).
**Reviewed scope:** Approved specification `0bd712e1…` and plan `a8f95a26…`; `workflow.py scope` (15 implementation, documentation and test files); code diff from pre-feature commit `a66a6070…` through exact source commit `dd88e73140828eebffb373aa2492d0eac0acdf64`; task records; current verification matrix; GitHub CI [run 45390904437](https://github.com/ahmedzein-dev/ai-dev-workflow/actions/runs/45390904437), job logs and platform skips; local test, lint, privacy and record-integrity evidence.

**Final verdict:** **GO** for the reviewed code and evidence on source fingerprint `b04a1b47d182d353c27ca0f465f67a54c0837ba341416cc42a87f8b667d413a1`. All six OS/Python jobs and the separate lint job passed on the exact source commit. No new Critical, Important or Minor finding remained after the fixes below. This is an audit verdict, not task closure or release approval.

## Dimensions

- **A. Specification compliance:** Schema-1 validation, explicit test-only migration protocol, task/ACTIVE locks, conservative stale recovery, durable per-file writes, temp cleanup and backward compatibility match the approved scope. AC/EC/DW matrix has 31 distinct entries; the final independent audit supports DW-5.
- **B. Architecture compliance:** The existing `aidw/` package, CLI/API boundary and shared writer were extended. No parallel store or production schema-2 converter was added.
- **C. Code quality:** No new duplication or dead path requiring action was found. The last code change is a focused regression test; the macOS cleanup correction catches only a disappeared file.
- **D. Security and privacy:** TD-25 early identity refusal and hook fail-closed behavior remain covered by 36 development-branch security tests. Privacy scan found no issue in 225 files. Pattern-based secret detection and the direct-writer trust boundary remain documented limitations.
- **E. Edge cases:** Migration failure/retry/rollback, concurrent writers, stale/ambiguous/reused-PID lock ownership, interrupted writes, malformed `ACTIVE` and orphan temp handling have focused coverage. Windows conditional skips are explicitly classified.
- **F. Regression risk:** Full local Python 3.9/3.13 suites and all six CI matrix jobs passed 243 discovered tests. Historical F-1/golden behavior remained valid; only the CLI help golden changed for `migrate`.
- **G. Test adequacy:** The reviewer identified the missing explicit PID-reuse fixture, which was added and passed locally and in all CI jobs. The final matrix does not claim unrun platform cases as executed.
- **H. Scope compliance:** Approved specification/plan snapshots and hashes are unchanged; no real records were migrated, stable v1.0.1 was not replaced, and TD-29/TD-30 work was not folded into this feature.
- **I. Reliability and performance:** Short mutations are locked; long checks do not hold task locks and revalidate before writing. File data is synced before replacement, directory sync is used where available, and Windows durability limits are stated. No multi-file atomicity is claimed.

## Project standards checklist

- Configured required checks (`unit`, `privacy`) passed on the final code fingerprint; six CI test/privacy jobs and the Ruff/Mypy lint job passed on `dd88e731…`.
- Python 3.9 and 3.13, standard-library-only implementation, API/CLI compatibility, approved snapshots, TD-25 regression protection and D-045 proportional interaction review were checked against the approved spec and plan.
- Normal use adds no settings or prompts; migration alone requires an explicit apply decision after a read-only preview, with backup and risk information available.
- `.ai-dev-workflow/config.json` declares no additional project standards. A root `PROJECT.md` is absent from this checkout; no checklist from such a file is claimed as checked.

## Findings

| ID | Severity | Dimension | Finding | Location | Disposition | Notes |
|----|----------|-----------|---------|----------|-------------|-------|
| F-1 | Minor | G/E | The initial matrix said PID reuse was tested, but no explicit unrelated-live-process PID fixture existed. | `tests/test_state_store.py`, `verification.md` | Fixed | Added `test_reused_pid_metadata_does_not_steal_a_lock`; local Python 3.9/3.13 suites passed 243/243 and CI run 45390904437 passed all six matrix jobs. The lock is not stolen on either OS path. |
| F-2 | Important | A/G | The initial matrix said 32 TD-25 tests, carrying the release-backport count into the development branch; the current module has 36. | `verification.md` AC-9/EC-13 | Fixed | Corrected to 36 and independently counted the tests; all are included in the final full suites. |
| F-3 | Minor | A | Intermediate verification prose called a prior CI result final and did not distinguish its 242-test Windows counts from the current 243-test source. | `verification.md` | Fixed | Final text links each run to its SHA and gives current Windows 241/243 and 240/243 executed counts with 2/3 conditional skips. |

## Remediation log

The first CI attempt on `f0d469e7…` had a macOS/Python 3.9 test-cleanup race; `tests/helpers.py` was changed to ignore only `FileNotFoundError` for a disappearing Git maintenance lock. Local full suites and CI run 45340225724 then passed. The independent evidence audit found F-1 and F-2; a focused PID-reuse test and record corrections were added on `dd88e731…`. Local Python 3.9 and 3.13 full suites each passed 243/243; stable-engine `unit` and `privacy` passed on the final fingerprint; pinned Ruff 0.17.6 and Mypy 1.20.2 returned zero diagnostics; privacy scanned 225 files with no findings. Exact-source CI run 45390904437 passed six matrix jobs plus lint. The reviewer then rechecked the final code and all 31 acceptance rows and issued GO with no new findings.

F-9 remains Deferred from TD-25; TD-29 multi-file transactions and TD-30 direct-writer trust boundary remain separate technical debts. Windows lacks directory fsync in this design. None is described as fixed by F1.0.5.
