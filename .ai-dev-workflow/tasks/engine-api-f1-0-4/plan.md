# Implementation Plan: F1.0.4 Engine API: commands return data, the CLI only prints

> Spec: v1 · f4dd4068
> Frozen once approved. Progress is recorded with `workflow.py step`, never by editing this plan.

## 1. Goal

Extract the logic of the 19 engine commands in `aidw/cli/commands.py` into 21 functions in `aidw/api.py` (`init` has three modes: discover, set up, update), functions that take
keyword parameters, write the records and return data, so that the CLI only renders. Every printed byte stays the same.

## 2. Current Behavior

- `aidw/cli/commands.py` (937 lines) holds 19 `cmd_*` functions. Each one does three things together: validate,
  write records (`save_state`, `save_json`, `write_text`, `activate`, `clear_active`, `make_readonly`,
  `apply_commit_mode`, `regenerate_check_block`) and print. Logic helpers live next to them: `resolve_template`,
  `install_template`, `change_checks`, `open_tasks`, `update_setup`, `scan_records`, `validate_task`.
- `aidw/cli/helpers.py` mixes data builders (`status_line`, `task_summary`, `require_task`) with `print_summary`.
- `aidw/agents/claude_hooks.py` imports `status_line` from `aidw.cli.helpers`, so the hooks depend on the CLI layer.
- `aidw/cli/main.py` parses arguments, calls `args.func(args)` and turns `WorkflowError` into stderr text and an exit
  code. That stays.
- Safety net: 156 tests including 8 golden CLI outputs, script-entry, layer and public-names tests (F1.0.2, F1.0.3).
  CI is green on 3 operating systems.

## 3. Proposed Solution

One new module, `aidw/api.py`, at layer level 4, between `core`/`adapters` (3) and the front ends (`cli`, `agents`,
now 5). It follows TARGET_ARCHITECTURE §2–3 and the package layout of F1.0.3.

| API function (keyword parameters) | Returns (main keys) | CLI renderer keeps |
|---|---|---|
| `discover_setup(repo)` | the discovery report (unchanged) | `print_discovery`, `--json` |
| `init_project(repo, template, commit, rules, no_rules, standards, config, project, project_notes, without_check, add_check, agent)` | `source_label`, `has_rules`, `commit`, `checks`, `exclude` | the three set-up lines |
| `update_setup(repo, commit, standards, template, rules, no_rules, without_check, add_check, agent)` | `changed` | "Updated the AIDevWorkflow settings: …" |
| `new_task(repo, task, title, task_type, invocation, agent, session)` | `task`, `paused`, `preexisting`, `next`, `read` | creation lines |
| `status(repo, task=None)` | `{setup: false, message}`; or the task summary; or `{setup, active, tasks}` | table, `print_summary`, `--json` |
| `record_discovery(repo, task, inspected, summary, agent)` | `inspected`, `summary_set`, `missing` | two lines |
| `spec_check(repo, task)` / `plan_check(repo, task)` | the check result (unchanged) | `print_spec_check`, plan lines, `--json`, exit 1 |
| `review(repo, task, maps, questions, dismiss, notes, passes, agent)` | `spec_check` (fresh result) | `print_spec_check` |
| `approve(repo, task, document, evidence, by, agent)` | `document`, `version`, `sha256`, `snapshot`, `stage`, `message` | message |
| `stage(repo, task, stage, reason, agent)` | `task`, `stage`, `next`, `read` | three lines |
| `resume(repo, task, agent, session)` | `paused`, `summary`, `code_stage` | paused line, summary, reminder |
| `pause(repo, task, reason, agent)` | `task` | one line |
| `preflight(repo, task, agent, session)` | `valid`, `problems`, `unattributed`, `task`, `stage`, `analyzer_hint` | passed/failed text, `--json` (3 keys), exit 1 |
| `step(repo, task, step, status, files, note, agent)` | `step`, `status`, `files`, `done`, `total` | one line |
| `run_check(repo, task, check, extra, baseline, force, blocked, not_applicable, agent)` | `entry`, `output_tail`, `recorded_on_purpose` | tail lines, result line, exit code |
| `scope(repo, task, exclude, reason, agent)` | the scope result (unchanged) plus `task`, `implementation_baseline` | scope text, `--json` |
| `decision(repo, task, text, evidence, by, agent)` | `count` | one line |
| `check_records(repo, task=None)` | `ok`, `errors`, `warnings` | ERROR/WARNING lines, `--json`, exit 1 |
| `outcome(repo, task)` | the outcome result (unchanged) | three lines, `--json` |
| `close(repo, task, agent)` | `task`, `outcome` | one line |

- **Moved helpers:** `status_line`, `task_summary`, `resolve_template`, `install_template`, `change_checks`,
  `open_tasks`, `scan_records`, `validate_task` move to `api.py`. `resolve_template` takes keyword parameters instead
  of `args`. `require_task(args)` stays in `cli/helpers.py`, read-only, so its public name keeps working.
- **CLI functions keep their names and signatures.** Each `cmd_x(args)` becomes: call `api.x(**fields from args)`,
  print as today, return the same exit code.
- **Hooks:** import `status_line` from `aidw.api`.
- **workflow.py:** re-exports the moved names from their new module, so the recorded public-names list still holds.
- **Moving order:** one command group per step, each followed by the full suite, so any byte difference shows up next
  to the change that caused it.

## 4. Affected Areas

- **New:** `skills/ai-dev-workflow/scripts/aidw/api.py`, `tests/test_api.py`.
- **Changed:**
  - `aidw/cli/commands.py` (renderers only);
  - `aidw/cli/helpers.py` (keeps `require_task`, `print_summary`);
  - `aidw/agents/claude_hooks.py` (one import);
  - `scripts/workflow.py` (import locations);
  - `tests/test_package.py` (layer table: `api` 4, `agents`/`cli` 5);
  - `README.md` (Development note).
- **Unchanged by design:** every other existing test, every golden file, `aidw/cli/main.py` argument definitions,
  `install.py`, `SKILL.md`, `references/`, `assets/`, `tools/`, `docs/`.
- **Outside task scope:** roadmap files, excluded under the standing rule.

## 5. Implementation Steps

- **S1:** Record baselines: copy `tests/golden/` aside for the byte comparison (AC-1); measure the medians of `workflow.py --version` and the hook entry (EC-8, AC-7).
- **S2:** Create `aidw/api.py` with the moved helpers (`status_line`, `task_summary`, `resolve_template`, `install_template`, `change_checks`, `open_tasks`, `scan_records`, `validate_task`). Point `cli/commands.py`, `cli/helpers.py`, the hooks and `workflow.py` at them. Update the layer table in `tests/test_package.py`. Run the full suite (FR-4, FR-5, FR-6, EC-6).
- **S3:** Setup and task-creation commands → API: `discover_setup`, `init_project`, `update_setup`, `new_task`, `status`, `record_discovery`; their `cmd_*` become renderers. Run the full suite (FR-1, FR-2, FR-3, EC-5).
- **S4:** Specification and lifecycle commands → API: `spec_check`, `plan_check`, `review`, `approve`, `stage`, `resume`, `pause`. Run the full suite (FR-1, FR-2, FR-3, EC-1, EC-3, EC-4).
- **S5:** Implementation and evidence commands → API: `preflight`, `step`, `run_check`, `scope`, `decision`, `check_records`, `outcome`, `close`. Run the full suite and the golden byte comparison (FR-1, FR-2, FR-3, FR-7, EC-2, EC-3).
- **S6:** Add `tests/test_api.py`:
  - the separation test (AC-3): source inspection of `aidw/cli/`;
  - the API-only lifecycle test, from setup to close in a temporary repository, with stdout and stderr captured (AC-4, EC-7);
  - JSON parity for the eight `--json` commands (AC-5);
  - the hook module importing nothing from `aidw/cli/` (AC-6).
- **S7:** Finish: docstrings with return keys and type annotations (FR-8); ruff, mypy, privacy and `unit-py39` (AC-2); re-measure timing (AC-7); README "Development" note.

## 6. Important Technical Decisions

- **One module `aidw/api.py`** (about 650 lines), as the approved TARGET_ARCHITECTURE names it.
  - The alternative was an `aidw/api/` package split by command group. It would add a second layout decision now.
  - It can be split later without changing callers, because callers import from `aidw.api`.
- **Keyword parameters, not `argparse.Namespace`.** A dashboard or orchestrator can call the API without building
  CLI arguments.
  - Cost: each `cmd_*` maps its arguments once.
- **Plain `dict` results, not dataclasses.**
  - They match today's `--json` outputs and `state.json`.
  - They need no schema code yet; typed result classes can come with the documented public API in a later phase.
- **Exit codes stay in the CLI.** They are a property of the command line, not of the engine.
- **`cmd_*` names kept** as thin renderers, so the recorded public names and any script that imports them keep working.

## 7. Edge Cases

- **EC-1:** refusal checks move with their code in the same order, before any write. `main()` still formats
  `WorkflowError`.
- **EC-2:** `run_check` returns `output_tail` (redacted, at most 120 lines); `cmd_run` prints it first, then the
  result line.
  - Today the tail is printed before the state is saved. A later refusal (the secret check on `reason`) can only
    happen when no command ran, so no output is lost.
- **EC-3:** API results carry `ready`, `valid` or `ok`, or the entry status. The CLI returns 1 exactly where it does
  today.
- **EC-4:** `review` returns the fresh spec check. `resume` returns the paused task and the summary. `approve` returns
  the message it builds today.
- **EC-5:** `status` returns `{setup: false, message}`, and the CLI prints the message or the JSON as today.
- **EC-6:** the hooks change only one import; the existing hook tests cover their output.
- **EC-7:** the API has no `print`, `sys.exit` or `sys.argv`. The lifecycle test captures both streams.
- **EC-8:** timing before (S1) and after (S7).
- **Shared-code risk:** `workflow.locale` and `workflow.shutil` patches still apply, because they patch the standard
  modules.

## 8. Testing Plan

| Item | Proof |
|---|---|
| AC-1, FR-3, FR-6 | `unit` (all 156 existing tests unchanged, plus the new ones) on 3.13 and `unit-py39`; byte comparison of `tests/golden/` with the S1 copy |
| AC-2, FR-8 | `ruff`, `mypy` (ad hoc checks through `run`) |
| AC-3, FR-2 | separation test in `tests/test_api.py` |
| AC-4, FR-1, EC-7 | API-only lifecycle test with captured stdout and stderr |
| AC-5, FR-7 | JSON parity test for `status`, `spec-check`, `plan-check`, `preflight`, `scope`, `check`, `outcome`, `init --discover` |
| AC-6, FR-4, FR-5, EC-6 | layer, cycle and public-names tests in `tests/test_package.py`; hook import check in `tests/test_api.py` |
| EC-1–EC-5 | existing scenario and golden tests (they exercise refusals, failing checks, review, resume, status without setup) |
| AC-7, EC-8 | timing medians of 15 runs before and after, recorded in verification.md |
| Done when: CI | `tests` workflow on the pushed commit, 3 OSes × Python 3.9/3.13 |
| Privacy | `privacy` check |

## 9. Risks and Dependencies

- **Hidden output-order change** (risk: medium):
  - mitigated by moving one group per step, with golden and scenario tests after each step;
  - mitigated by the byte comparison.
- **Signature change of moved helpers** (risk: low): no test or tool calls them (checked: tests use only `main`,
  `build_parser` and constants). Recorded in the report.
- **Startup time** (risk: low): one more module import on the hook path. Measured; above 50 ms it becomes an audit
  finding.
- **Dependencies:** none open (dependencies.md: DEP-1–DEP-3 Verified).

## 10. Expected Result

- `aidw.api` exposes 21 functions that run every engine command without printing.
- The CLI only renders their results.
- The hooks no longer depend on the CLI.
- Users and agents see exactly the same commands, outputs and records.
- The next Phase 1 features (component discovery F1.1.1, adapters F1.2.1) build on the API.
