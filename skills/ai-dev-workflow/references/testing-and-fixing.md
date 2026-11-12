# Testing and fixing

## What to verify (stage 8)

Never claim completion because code was generated. Verify what applies to this change, using the project's
infrastructure:

- **Static checks**: formatting, linting, static analysis, type checking, compilation or build.
- **Automated tests**: unit, widget or component, integration, regression, platform-specific.
- **Behavior**: every acceptance criterion, the happy paths, error scenarios, important edge cases, and existing
  features the change could affect.

The project's checks are listed in `.ai-dev-workflow/config.json` (`checks`). Also apply the verification
requirements in the project's standards files; the configured checks are a baseline, not the whole list.

## Running checks and recording evidence

```
workflow.py run <task> <check-id>                       # a configured check
workflow.py run <task> test -- <path/to/test>           # extra arguments, if the check accepts them
workflow.py run <task> widget-tests -- <command …>      # an extra, unconfigured check
workflow.py run <task> <check-id> --blocked "no Android device available"
workflow.py run <task> codegen --not-applicable "no generated models changed"
```

- `run` executes the command and records the result, a short redacted summary and a fingerprint of the current code.
  If the code changes afterwards, that evidence is stale and must be re-run; `outcome` and the AUDIT gate reject stale
  evidence.
- Statuses: `passed`, `failed`, `preexisting` (only problems that existed before the task remain), `blocked` (could not
  run here, with the reason), `not-applicable` (a conditional check that does not apply, with the reason; not allowed
  for always-required checks).
- Analyzer checks count issues by severity instead of trusting the exit code, and with a baseline they separate
  new issues from old ones.
- Built-in checks: `json-key-parity` (translation files have the same keys), `rule-scan` (project rules on the
  files the task changed, new violations only), `manifest-diff` (new dependencies need a recorded user decision).

## When a check fails

1. Investigate the failure.
2. Find the root cause.
3. Decide whether the task caused it or it existed before (the baseline and `preexisting` status help).
4. Fix what the task caused: move to FIXING (`stage <task> FIXING --reason …`), run `preflight`, fix, mark the step.
5. Return to TESTING and re-run the affected checks.
6. Repeat until it passes or is genuinely blocked.

Never disable or skip tests to get a pass, never hide a failing check, never invent results, never claim a check
passed without running it, and never change unrelated code to hide a pre-existing failure without the user's
approval.

## Environment limits

If a check needs a device, service, backend, credential or resource that is not available, record it as blocked with
the reason (`run … --blocked "…"`). Mark affected acceptance items Blocked or Not Verified. A test that could not run
is never Passed; the final status will be at most Completed with Limitations.

## Acceptance matrix

In `verification.md`, add one row per AC and EC of the approved spec and per checklist item ("Done when"), numbered
DW-1, DW-2, … in order:

```
| Item | Status | Evidence |
|------|--------|----------|
| AC-1 | Passed | widget test "saves favorite on tap" (check test) |
| EC-3 | Blocked | needs a real device in airplane mode; not available here |
| DW-4 | Passed | check analyze passed on the current code |
```

Status is Passed, Failed, Blocked or Not Verified; evidence names the test, command or inspection, or the reason.
Then move to AUDIT, or to FIXING if anything failed.
