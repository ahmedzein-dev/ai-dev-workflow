# Final Report: F1.0.4 Engine API: commands return data, the CLI only prints

## 1. Overall Status

**Status:** Completed with Limitations

Everything in the approved spec v1 (303f07fe) and plan v1 (4e4b2a66) is implemented and verified. The tested commit
is **fa6a676**:
- CI run 45005422565 passed: Linux, Windows and macOS × Python 3.9/3.13, plus lint.
- The independent re-audit gave GO.

The limitation is one pre-existing, security-sensitive defect found by the audit, F-7 / TD-25. It was not introduced
by this task and is accepted by the owner for a separate, approved fix. That acceptance caps the status below
"Completed".

## 2. What Was Implemented

- **New internal module `aidw/api.py`:**
  - 21 command functions, plus `apply_clone_commit_mode` and the moved helpers;
  - keyword parameters, with the repository and agent always explicit;
  - JSON-serialisable dict results with documented keys;
  - every refusal raised as `WorkflowError`;
  - no printing, no working-directory use, no environment agent lookup and no module-level state.
- **The 19 `cmd_*` functions are renderers:** `aidw/cli/commands.py` went from 937 to 387 lines and writes no
  records.
- **Other moves:** the hooks import from the API, and the core no longer prints (`apply_commit_mode_in_clone` returns
  its message).
- **Compatibility:** `resolve_template`, `update_setup` and `ensure_commit_mode` keep their old signatures and
  behaviour through thin wrappers in the CLI.
- **Behaviour pinned from the pre-refactor engine (5a7576a):**
  - the signatures of every public function;
  - 27 refusal scenarios, with record bytes compared inside each test;
  - the output of a late `run` refusal;
  - the `preflight --json` trailing text (TD-24, kept).
- **Tests:** layers updated (api=4, agents/cli=5); new `tests/test_api.py` (separation, isolation, JSON parity,
  API-only lifecycle, commit-mode notice); README Development note.

## 3. Specification Compliance

FR-1–FR-12, EC-1–EC-10 and AC-1–AC-12 are Met (verification.md; the auditor's per-criterion verdicts).

Documented deviations, none of which changes behaviour:
- **F-11:** the core function `ensure_commit_mode` was renamed `apply_commit_mode_in_clone`. The `workflow` name and its
  behaviour are kept. `tests/test_behaviour_pins.py` was added under plan S1 but is not named in the spec's Scope list.
- **F-18:** the `resolve_template` wrapper also accepts a Namespace without `rules`.
- **`api.py` size:** 948 lines against an estimate of 650. The owner accepted this.

## 4. Testing Results

- **Code fingerprint 23f78e988f** (fa6a676), re-run as **b46e1599a2** after a roadmap-only edit:
  - `unit` 173 tests (156 pre-existing unchanged, 5 behaviour pins, 12 API tests) and `unit-py39`;
  - `privacy` (199 files), `ruff`, `mypy` (31 files);
  - `golden-byte-compare`: the 9 pre-existing golden files are byte-identical.
- **Timing (paired runs):** `--version` 61.2 → 63.1 ms, hook 60.9 → 62.7 ms.
- **CI on fa6a676:** 7/7 jobs.
- **Earlier CI failures, Windows only:**
  - cea2e9f: a test restored the working directory after tearDown, which fails with WinError 32.
  - b2f5b8e: space-only paths resolve to the working directory on Windows, and quoted extra commands do not parse
    there.

  Both root causes and fixes are documented in verification.md.

## 5. Code Audit

An independent read-only subagent reviewed the work in three rounds:
- **cea2e9f:** 14 findings, three of them Important (F-1, F-3, F-7).
- **b2f5b8e:** the fixes were verified, and 5 new Minor findings were raised (F-15–F-19).
- **fa6a676:** GO, with no new findings.

Dispositions:
- **Fixed:** F-1–F-6, F-8–F-10, F-15–F-17, F-19.
- **Accepted:** F-7, as TD-25 (owner's words quoted in audit.md).
- **Deferred (Minor, documented):** F-11, F-12, F-13 leftovers, F-14 (TD-26), F-18.

Every refusal and every secret check is unchanged against 5a7576a.

## 6. Edge Cases and Regression Risks

- **Regression risk is low.** The per-command comparison of all 19 commands against 5a7576a shows no difference. The
  pins pass on both engines with Python 3.13 and 3.9.
- **Known, kept behaviour:**
  - TD-24: `preflight --json` prints text after the JSON.
  - TD-25: unredacted check id and agent name in verification.md before a refusal. Security-sensitive, high priority.
    The exposure check found no secret-like value in this repository's 32 task records; no values were printed.
  - TD-26: `init --update --commit` applies the mode before later refusals.
- **F-12:** small extra read-only loads.
- **For future hook entry points:** importing the hook module alone now also imports the API (+13 ms import time).

## 7. Pending Dependencies

None — DEP-1 to DEP-3 are Verified.

## 8. Next Actions

- Owner: decide on closing F1.0.4 with this status.
- Then the next feature in the agreed order: F1.0.5 (state schema check, migrate, locking).
- TD-25 should get its own prioritised, separately approved task. TD-24 and TD-26 stay as separate defects.
