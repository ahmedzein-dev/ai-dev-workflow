# Verification: TD-25: keep secret-like check ids and agent names out of task records

Tested commit: **pending** (filled in after the commit and CI). Approved documents: spec v2 `9cf6cec3`, plan v2
`f1c2745d`.

**Approval history (condition 4 of the v2 approval).**
- S1–S3 were implemented under the approved **spec v1 `2fdbc034` and plan v1 `b60cd6f0`** (approved 2026-11-22,
  frozen as `approved/spec.v1.md` and `approved/plan.v1.md`).
- During S3 the F-1 pin conflict was found. The owner then chose Option A (pin re-trigger) and Option 1 (hook in
  scope).
- The task moved back to SPECIFICATION, and spec v2 and plan v2 were written and approved afterwards (`approved/spec.v2.md`,
  `approved/plan.v2.md`). v2 records S1–S3 as already done under v1.
- S4 onward were implemented under v2. The S1–S3 code was kept unchanged, except that `_check_session` now calls
  the shared `session_problem` (S4) with identical messages.
- No approval evidence was rewritten. The engine's warning "files changed before implementation was approved"
  refers to the S1–S3 files changed while v2 was being specified.

## Check runs

Written by `workflow.py run`; do not edit between the markers.

<!-- aidw:checks:start -->
| Check | Status | Summary | Code fingerprint | When | Agent |
|---|---|---|---|---|---|
| golden-byte-compare | passed | 14 golden files; changed: ['run-output-before-late-refusal.txt']; unexpected: none | `4e22081a98` | 2026-11-22T12:17:06Z | claude-code |
| mypy | passed | Success: no issues found in 31 source files | `4e22081a98` | 2026-11-22T12:17:06Z | claude-code |
| privacy | passed | Scanned 212 files: no findings. | `4e22081a98` | 2026-11-22T12:14:49Z | claude-code |
| ruff | passed | All checks passed! | `4e22081a98` | 2026-11-22T12:17:06Z | claude-code |
| unit | passed | OK | `4e22081a98` | 2026-11-22T12:14:50Z | claude-code |
| unit-py39 | passed | OK | `4e22081a98` | 2026-11-22T12:16:09Z | claude-code |
<!-- aidw:checks:end -->

## Acceptance matrix

One row for every AC and EC in the approved spec and every "Done when" item, numbered DW-1, DW-2, … in
order. Status is Passed, Failed, Blocked or Not Verified. Evidence names the test, command or inspection;
for Blocked and Not Verified it says why. A check that did not run is never Passed.

| Item | Status | Evidence |
|------|--------|----------|

## Behavioral checks

[Happy paths, error scenarios and affected existing features you exercised, and how.]

## Limitations

[What could not be run or verified (device, service, credential, backend), and why. Write "None — <reason>" if there are none.]
