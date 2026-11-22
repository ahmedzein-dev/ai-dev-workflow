# Audit: TD-25: keep secret-like check ids and agent names out of task records

**Review independence:** subagent
**Reviewer:** Claude Code read-only general-purpose subagent (Opus 5.5), security-focused. It was given the task
records, the approved spec v2 and plan v2, the diff against `deba846` and the backport worktree, but not the
implementer's conclusions.
**Rounds:**
- Round 1 on the working tree, byte-identical to commit `a346300`, plus the backport `056ac73`/`7f3a2ae`. Verdict
  NO-GO, one Important finding.
- Round 2 on the fixes: see the remediation log.

**Reviewed scope:**
- `aidw/api.py`, `aidw/agents/claude_hooks.py`, `tests/test_secret_identity.py`;
- `tests/test_behaviour_pins.py` (`LateRefusalTest`) and its golden file;
- `CHANGELOG.md`, `docs/roadmap/TECHNICAL_DEBT.md` (TD-25–TD-30);
- the `release/1.0.x` backport (`git diff v1.0.0`);
- approved spec v2 (`9cf6cec3`) and plan v2 (`f1c2745d`).

## Dimensions

- **A. Specification compliance:**
  - FR-2, FR-4, FR-5, FR-7, FR-11, FR-12 and FR-13 are met.
  - FR-1, FR-3 and FR-6 were met as written, but not the spec's goal for values containing a line separator (F-1, fixed).
  - FR-9, FR-10 and FR-14 were incomplete in the report and the debt register (F-2, F-7, fixed).
- **B. Architecture compliance:**
  - The checks live in the API (layer 4). The hooks (layer 5) reuse `aidw.api.session_problem`.
  - The CLI still writes nothing, and `store/` and `infra/` are untouched.
- **C. Code quality:** small private helpers; one shared session rule; no duplication across front ends.
- **D. Security and privacy:**
  - Refusal messages and hook denial reasons never contain the value.
  - Invalid hook sessions are neither written nor logged, and inside an active task they are denied whatever the binding.
  - Round 1 found the line-separator gap (F-1) and a slow regex path on huge session ids (F-5); both fixed.
- **E. Edge cases:**
  - EC-1–EC-18 are covered.
  - A non-text hook session is now denied inside an active task; before, it bypassed the gates through the exception path.
- **F. Regression risk:**
  - Every golden file is byte-identical to `deba846`, except the approved FR-13 file.
  - The 27 refusal pins, the signature and name pins, and the existing hook tests are unchanged and passing.
- **G. Test adequacy:**
  - The tests fail on `5a7576a` and `fa6a676` and pass on the fix.
  - Gaps were found in the log assertions, in the 1.0.1 CLI sweep and in the JSON-escaped persistence check (F-3, F-4); fixed.
- **H. Scope compliance:**
  - TD-24 and TD-26–TD-30 are not fixed here.
  - The backport holds only the TD-25 fix, the version, the CHANGELOG and CI changes.
- **I. Reliability and performance:**
  - The regex scan was quadratic on huge session ids (F-5); fixed with a 4,096-character bound.
  - The rollback is best effort (F-6); the wording was corrected.

## Project standards checklist

No standards files are configured (`standards: []`). Spec constraints:
- Standard library only: yes.
- Protected files untouched: yes. Every existing test is unchanged apart from `LateRefusalTest` (one module-docstring
  line and two imports in that file); `aidw/infra/secrets.py`, `aidw/store/`, `SKILL.md` and `references/` are untouched.
- Synthetic values only, no literal token: yes. The privacy scan is clean.

## Findings

| ID | Severity | Dimension | Finding | Location | Disposition | Notes |
|----|----------|-----------|---------|----------|-------------|-------|
| F-1 | Important | D, A | The early checks scanned the raw value line by line, while the later `state.json` check scans the JSON form, where a line separator becomes an escape. An agent or check name like `password=` + line separator + 8 characters passed early: `resume` wrote it to ACTIVE, `run` executed the command, and "Unknown check" echoed it. The backport had the same gap | `api.py` `_check_agent`, the `run_check` check name; backport `check_identity`, `cmd_run` | Fixed | `_assert_clean_value` / `assert_clean_value` scan the value and its JSON form, as `state.json` is scanned; session ids use the same check. Test `test_multi_line_secret_like_values_are_refused_before_anything_runs` (LF, CR, VT, FF, FS) fails on `a346300` and on backport `056ac73`, and passes after the fix. U+2028 and U+0085 are flagged in neither form, nor in `state.json`: a detection limit, not an ordering gap (documented) |
| F-2 | Minor | A | The TD-25 row lacked the FR-10 limits; report.md and the verification matrix were still empty when audited | TECHNICAL_DEBT TD-25; report.md; verification.md | Fixed | Limits added to TD-25; verification matrix and report completed |
| F-3 | Minor | G | The hook-log assertions could pass with no log line; the non-text session test did not check the log; `assert_not_persisted` looked only for raw bytes | `tests/test_secret_identity.py` | Fixed | At least one new line is required where the hook logs; the non-text test checks `session: null` and `session_rejected`; raw and JSON-escaped forms are both searched |
| F-4 | Minor | G | The backport dropped the API classes, so the 1.0.1 CLI refusal of discover, review, approve, stage, pause, scope, decision and close was untested | backport tests | Fixed | `test_every_recording_command_refuses_a_secret_like_agent` (CLI sweep) in both branches |
| F-5 | Minor | I | The secret regex ran before the 256-character bound and is quadratic on inputs such as `"a." * n` (about 0.9 s at 40,000 characters), a possible hook timeout | `session_problem` (both branches) | Fixed | Values over 4,096 characters are refused with the format message before scanning. `test_huge_session_is_refused_quickly` (400,000 characters, under 2 s) fails on `a346300` and passes after the fix |
| F-6 | Minor | I | The CHANGELOG said `new` "no longer leaves a half-created task folder", which is absolute. A crash, a locked file or a foreign file can still leave it, and an empty `tasks/` folder can remain after a failed first `new` | CHANGELOG (both branches) | Fixed | Reworded to best effort; the residual cases are under TD-29 |
| F-7 | Minor | A | TD-29 omitted that `pause` and `close` delete ACTIVE, and `approve` writes the snapshot, before `save_state` | TECHNICAL_DEBT TD-29 | Fixed | Added to TD-29 (pre-existing, no value leak; not fixed here) |

## Remediation log

- **Round 1 fixes:**
  - F-1 and F-5 in code (development branch and backport);
  - F-3 and F-4 in the tests;
  - F-2, F-6 and F-7 in the documentation.
- **New tests on pre-fix code:** they fail on `a346300` (2 tests: multi-line values, huge session) and on backport
  `056ac73` (the same 2), and pass after the fix.
- **Test counts after the fixes:**
  - development branch: 36 of 36 TD-25 tests;
  - backport: 32 of 32 adapted tests;
  - pristine v1.0.0: 27 failures and 1 error out of 32 adapted tests, with 4 legitimate-value tests passing.
- **Re-run checks and CI:** recorded in verification.md after this round.
