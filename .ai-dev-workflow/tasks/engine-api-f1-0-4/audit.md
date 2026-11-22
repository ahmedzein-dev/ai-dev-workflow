# Audit: F1.0.4 Engine API: commands return data, the CLI only prints

**Review independence:** subagent
**Reviewer:** Claude Code read-only general-purpose subagent (Opus 5.5), given the task records, the pre-task commit and the diff, not the implementer's conclusions; three rounds: cea2e9f (full audit), b2f5b8e (re-audit of the fixes), fa6a676 (final delta, verdict GO)
**Reviewed scope:** `git diff 5a7576a fa6a676` — aidw/api.py, aidw/cli/commands.py, aidw/cli/helpers.py, aidw/agents/claude_hooks.py, aidw/core/setup.py, scripts/workflow.py, tests/test_api.py, tests/test_behaviour_pins.py, tests/test_package.py, the five new golden files, README.md; approved spec v1 (303f07fe) and plan v1 (4e4b2a66); verification.md and state.json

## Dimensions

- **A. Specification compliance:**
  - FR-1–FR-12 are met.
  - FR-3 had two deviations at cea2e9f (F-1, F-2). Both are fixed and pinned against 5a7576a.
  - AC-1–AC-12 are Met in the final state (auditor's per-criterion verdicts).
- **B. Architecture compliance:**
  - Layers: `api` is level 4, `agents` and `cli` are level 5; the graph is acyclic.
  - The CLI writes no records; the separation test catches imports, bare calls, attribute calls, aliases and `.open` writes (mutation-tested).
  - Below the front ends there is no `print`.
  - The API keeps no module-level state and reads no working directory, agent variable or argv. Relative paths resolve against the working directory, as documented (F-5).
- **C. Code quality:**
  - Typed keyword-only functions, with docstrings naming the returned keys.
  - Minor leftovers: the `stage`/`step` parameters shadow their own function names, and `notices`/`output_tail` are ad hoc attributes on exceptions (F-13).
- **D. Security and privacy:**
  - No gate or secret check was weakened. These are verbatim at every call site: `assert_no_secrets`, `find_secrets`, `redact`, the sha256 approval binding, the snapshots and `make_readonly`.
  - One pre-existing gap, F-7, is recorded as TD-25 (security-sensitive).
- **E. Edge cases:**
  - EC-1–EC-10 are handled.
  - A refusal after `run` executed (F-1) is fixed and pinned.
  - Two side effects that happen before a refusal are kept as before: `new` (documented) and `init --update --commit` (TD-26).
- **F. Regression risk:**
  - The per-command comparison against 5a7576a for all 19 commands found no difference after the fixes.
  - The 27 refusal pins, the late-refusal pin, both TD-24 pins and the signature pin pass on the old and the new engine with Python 3.13 and 3.9.
- **G. Test adequacy:**
  - The pins were verified independently against an export of 5a7576a.
  - The tests added after the audit fail on cea2e9f and pass at fa6a676.
  - The separation and output-capture tests were mutation-tested.
- **H. Scope compliance:**
  - Only planned files changed, plus this task's records and roadmap files under the standing rule.
  - Wording deviations are documented in F-11.
- **I. Reliability and performance:**
  - The hook entry is +1 to 2 ms (paired runs).
  - There are a few extra read-only state loads (F-12).

## Project standards checklist

No standards files are configured (`standards: []`). Spec constraints:
- Standard library only: yes.
- CLI byte-identical: yes (pre-existing golden files byte-identical, 27 refusal pins, signatures).
- Protected files untouched: yes. This covers `install.py`, `SKILL.md`, `references/`, `assets/`, `docs/` apart from the roadmap, `tools/`, other tasks' records, the existing golden files, and the existing tests apart from the layer table.
- API internal and unversioned: yes.

## Findings

| ID | Severity | Dimension | Finding | Location | Disposition | Notes |
|----|----------|-----------|---------|----------|-------------|-------|
| F-1 | Important | F | `run` lost the command output when a refusal or exception came after the command ran | api.py `run_check`, cli `cmd_run` | Fixed | The output tail is carried on the exception and printed first; pinned from 5a7576a (`LateRefusalTest`), which fails on cea2e9f |
| F-2 | Minor | F | `--repo` of spaces changed the exit code and message | api.py `_root`, cli `repo_arg` | Fixed | The first fix made the API resolve spaces to the cwd on Windows (second CI failure); final: the API refuses empty or space-only paths, the CLI resolves spaces through `find_repo` as before |
| F-3 | Important | G, B | The separation test missed attribute calls; the CLI reached a core writer through `api.` | tests/test_api.py, cli `ensure_commit_mode` | Fixed | The wrapper calls `api.apply_clone_commit_mode`; the test checks attribute calls and API-defined names, and fails on cea2e9f |
| F-4 | Minor | F | `update_setup` wrapper edge cases (missing fields, path handling) | cli `update_setup` | Fixed | Reads the setup from the given path first; getattr for optional fields |
| F-5 | Minor | B | Relative paths given to the API resolve against cwd | api.py module docstring | Fixed | Documented: pass absolute paths |
| F-6 | Minor | C | Docstring overstated "refusal before any write" | api.py module docstring | Fixed | States the exceptions (`new_task`, `update_setup`, `run_check`) |
| F-7 | Important | D | A secret-like extra check id reaches verification.md before the secret check refuses state.json (pre-existing, same on 5a7576a) | `run_check`, `regenerate_check_block` | Accepted | Owner: «TD-25: classify as a security-sensitive issue and prioritize an appropriately scoped, separately approved fix … Do not expand F1.0.4 to fix those historical defects.» Recorded as TD-25 (High, priority); the agent name is a second unredacted field; no secret-like value in this repository's 32 task records |
| F-8 | Minor | G | Refusal golden had gaps | tests/test_behaviour_pins.py | Fixed | 27 scenarios, all recorded from 5a7576a |
| F-9 | Minor | G | JSON parity compared values only | tests/test_api.py | Fixed | Raw-text parity incl. check with errors |
| F-10 | Minor | G | Lifecycle comparison skipped checkpoints and config | tests/test_api.py | Fixed | Checkpoints, config.json and ACTIVE compared |
| F-11 | Minor | H | Wording deviations: `ensure_commit_mode` renamed to `apply_commit_mode_in_clone` in core; `test_behaviour_pins.py` not named in the spec Scope (implied by plan S1) | core/setup.py | Deferred | Documented in report.md; the `workflow.ensure_commit_mode` name and behaviour are kept by the wrapper |
| F-12 | Minor | I | Extra read-only state loads (`task_id` for plan-check/scope text, config read twice in `init --update`); +1–2 ms hook startup | cli/commands.py | Deferred | Documented in report.md; within the 50 ms threshold |
| F-13 | Minor | C | Code nits | api.py, cli/commands.py | Deferred | Blank lines and the `status` local fixed; parameter shadowing and ad hoc exception attributes kept (changing them would touch errors.py, outside the scope) |
| F-14 | Minor | E | `init --update --commit` applies the mode before later refusals (pre-existing) | api.py `update_setup` | Deferred | TD-26; order kept exactly (owner: keep documented as a separate defect) |
| F-15 | Minor | B, E | (re-audit N-1) `apply_clone_commit_mode` skipped root resolution | api.py | Fixed | Refuses empty paths; documents that it takes the root as given (old behaviour) |
| F-16 | Minor | G | (re-audit N-2) Empty-path test name and intent diverged | tests/test_api.py | Fixed | Message asserted |
| F-17 | Minor | H | (re-audit N-3) Stale "17 refusals" text | verification.md | Fixed | Now 27 |
| F-18 | Minor | F | (re-audit N-4) `resolve_template` wrapper tolerates a missing `rules` attribute (old raised AttributeError) | cli `resolve_template` | Deferred | More permissive, harmless; documented in report.md |
| F-19 | Minor | G | (re-audit N-5) Separation test blind spots (aliases, `.open("w")`) | tests/test_api.py | Fixed | Mutation-tested by the auditor |

## Remediation log

- **FIXING round 1** (commit b2f5b8e):
  - First CI failure on Windows (cea2e9f): the test restored the cwd after tearDown (WinError 32); now `try/finally`.
  - Audit fixes: F-1–F-6, F-8–F-10, F-13.
  - New pins generated from 5a7576a.
  - TD-25 and TD-26 recorded.
- **FIXING round 2** (commit fa6a676):
  - Second CI failure on Windows (b2f5b8e): F-2 refined, because space-only paths resolve to the cwd on Windows.
  - The late-refusal pin uses a script file, since quoted extra commands are not portable to Windows (pre-existing).
  - Re-audit fixes: F-15–F-17 and F-19 (re-audit N-1, N-2, N-3, N-5).
- **Re-run on the final code** (fingerprint 23f78e988f at fa6a676, again as b46e1599a2 after a roadmap-only edit): `unit` (173), `unit-py39`, `privacy`, `ruff`, `mypy`, `golden-byte-compare` and `startup-timing` all passed.
- **CI:** run 45005422565 on fa6a676, Linux, Windows and macOS × Python 3.9/3.13, plus lint: 7/7 passed.
- **Final re-audit verdict:** GO.
