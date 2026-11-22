# Implementation Plan: F1.0.4 Engine API: commands return data, the CLI only prints

> Spec: 303f07fe (second draft, after the owner's review; becomes approved version v1)
> Frozen once approved. Progress is recorded with `workflow.py step`, never by editing this plan.

## 1. Goal

Extract the logic of the 19 engine commands in `aidw/cli/commands.py` into 21 functions in the internal module
`aidw/api.py` (`init` has three modes: discover, set up, update). The functions take explicit keyword parameters,
write the records and return data; the CLI only renders. Every printed byte stays the same, today's quirks included.

## 2. Current Behavior

- `aidw/cli/commands.py` (937 lines) holds 19 `cmd_*` functions. Each one does three things together: validate,
  write records (`save_state`, `save_json`, `write_text`, `activate`, `clear_active`, `make_readonly`,
  `apply_commit_mode`, `regenerate_check_block`) and print. Logic helpers live next to them: `resolve_template(args)`,
  `install_template`, `change_checks`, `open_tasks`, `update_setup(repo, args)`, `scan_records`, `validate_task`.
- `aidw/cli/helpers.py` mixes data builders (`status_line`, `task_summary`, `require_task`) with `print_summary`.
- `aidw/agents/claude_hooks.py` imports `status_line` from `aidw.cli.helpers`.
- **Hidden inputs and output below the CLI** (inspected):
  - `infra/text.agent_name(args)` falls back to `AI_DEV_WORKFLOW_AGENT`.
  - `infra/gitutil.find_repo(None)` uses the current directory.
  - `store/config.library_dir()` honours `AI_DEV_WORKFLOW_HOME`.
  - `core/setup.ensure_commit_mode` prints "Applied records.commit=…"; this is the only `print` below the CLI.
- **`cmd_preflight` (`cli/commands.py`, about lines 632–645)** prints the JSON object when `--json` is set. After it,
  outside the `if/elif`, it prints:
  - the "Changes since the last checkpoint…" list when there are unattributed changes;
  - the analyzer baseline hint, when the task is valid, in IMPLEMENTATION, has an analyzer check and no baseline yet.

  So `preflight --json` is not pure JSON in those cases. This is existing behaviour, kept and pinned (spec FR-8).
- **Safety net:** 156 tests, including 8 golden CLI outputs and the script-entry, layer and public-names tests.
  CI is green on 3 operating systems.

## 3. Proposed Solution

One new internal module, `aidw/api.py`, at layer level 4, between `core`/`adapters` (3) and the front ends (`cli`,
`agents`, now 5), following TARGET_ARCHITECTURE §2–3 and the package layout of F1.0.3.

**API contract (all keyword parameters; `repo` and `agent` explicit, never defaulted from the process):**

| API function | Returns (main keys) | CLI renderer keeps |
|---|---|---|
| `discover_setup(repo)` | the discovery report (unchanged) | `print_discovery`, `--json` |
| `init_project(repo, template, commit, rules, no_rules, standards, config, project, project_notes, without_check, add_check, agent)` | `source_label`, `has_rules`, `commit`, `checks`, `exclude` | the set-up lines |
| `update_setup(repo, commit, standards, template, rules, no_rules, without_check, add_check, agent)` | `changed` | "Updated the AIDevWorkflow settings: …" |
| `new_task(repo, task, title, task_type, invocation, agent, session)` | `task`, `commit_mode_message`, `paused`, `preexisting`, `next`, `read` | creation lines, in today's order |
| `status(repo, task=None)` | `{setup: false, message}`, the task summary, or `{setup, active, tasks}` | table, `print_summary`, `--json` |
| `record_discovery(repo, task, inspected, summary, agent)` | `inspected`, `summary_set`, `missing` | two lines |
| `spec_check(repo, task)` / `plan_check(repo, task)` | the check result (unchanged) | `print_spec_check`, plan lines, `--json`, exit 1 |
| `review(repo, task, maps, questions, dismiss, notes, passes, agent)` | `spec_check` (fresh result) | `print_spec_check` |
| `approve(repo, task, document, evidence, by, agent)` | `document`, `version`, `sha256`, `snapshot`, `stage`, `message` | message |
| `stage(repo, task, stage, reason, agent)` | `task`, `stage`, `next`, `read` | three lines |
| `resume(repo, task, agent, session)` | `paused`, `summary`, `code_stage` | paused line, summary, reminder |
| `pause(repo, task, reason, agent)` | `task` | one line |
| `preflight(repo, task, agent, session)` | `valid`, `problems`, `unattributed`, `task`, `stage`, `analyzer_hint` | passed/failed text or `--json` (3 keys), then the trailing lines exactly as today; exit 1 |
| `step(repo, task, step, status, files, note, agent)` | `step`, `status`, `files`, `done`, `total` | one line |
| `run_check(repo, task, check, extra, baseline, force, blocked, not_applicable, agent)` | `entry`, `output_tail`, `recorded_on_purpose` | tail lines, result line, exit code |
| `scope(repo, task, exclude, reason, agent)` | **exactly today's seven keys** (`baseline`, `task_changes`, `unattributed`, `preexisting_modified`, `preexisting_untouched`, `excluded`, `notes`) | scope text (task name from the argument; the "Not attributed" line when `baseline == "implementation"`, equivalent to today's test), `--json` |
| `decision(repo, task, text, evidence, by, agent)` | `count` | one line |
| `check_records(repo, task=None)` | `ok`, `errors`, `warnings` | ERROR/WARNING lines, `--json`, exit 1 |
| `outcome(repo, task)` | the outcome result (unchanged) | three lines, `--json` |
| `close(repo, task, agent)` | `task`, `outcome` | one line |

**Further rules:**
- **Moved helpers** (same signatures): `status_line`, `task_summary`, `install_template`, `change_checks`,
  `open_tasks`, `scan_records`, `validate_task`. `require_task(args)` stays read-only in `cli/helpers.py`.
- **Compatibility (owner point 5)** for three names whose shape changes inside the package:
  - `api.resolve_template(template, rules, no_rules)` and `api.update_setup(...)` take keyword parameters.
  - `core.setup.ensure_commit_mode(repo, cfg)` returns the message instead of printing it.
  - `workflow` re-exports thin wrappers in `aidw/cli/commands.py` with the old signatures and behaviour: about 3
    lines each, no other machinery.
  - A signatures golden file proves every re-exported callable keeps its signature. API functions are not
    re-exported from `workflow`.
- **CLI defaults stay in the CLI:** `--repo` absent → current directory; agent from `--agent`, then
  `AI_DEV_WORKFLOW_AGENT`. The API receives resolved values.
- **Order of work:** pin today's behaviour first (refusals, `preflight --json`, signatures), then move one command
  group per step, with the full suite after each.

## 4. Affected Areas

- **New:** `skills/ai-dev-workflow/scripts/aidw/api.py`, `tests/test_api.py`, `tests/golden/refusals.json`,
  `tests/golden/workflow-public-signatures.txt`, `tests/golden/preflight-json-*.txt`.
- **Changed:**
  - `aidw/cli/commands.py` (renderers and the three compatibility wrappers);
  - `aidw/cli/helpers.py`;
  - `aidw/agents/claude_hooks.py` (one import);
  - `aidw/core/setup.py` (`ensure_commit_mode` returns its message);
  - `scripts/workflow.py` (import locations);
  - `tests/test_package.py` (layer table);
  - `README.md` (Development note).
- **Unchanged by design:** every other existing test and golden file, the argument definitions in `aidw/cli/main.py`,
  `install.py`, `SKILL.md`, `references/`, `assets/`, `tools/`, `docs/`, and the records of other tasks (the closed
  F1.0.2 and F1.0.3 reports stay as written).
- **Outside task scope (standing rule):** the roadmap files. TD-24 is added to TECHNICAL_DEBT.md there.

## 5. Implementation Steps

- **S1:** Pin today's behaviour with the current engine, before any refactor (FR-6, FR-8, FR-11):
  - generate `tests/golden/workflow-public-signatures.txt`;
  - generate `tests/golden/refusals.json` from the EC-1 scenarios: exit code, stdout, stderr, and a hash of every file under `.ai-dev-workflow/` before and after;
  - generate the `preflight --json` regression outputs for EC-9 (unattributed changes; analyzer hint);
  - add the tests that compare against these files;
  - copy `tests/golden/` aside for the byte comparison (AC-1);
  - measure the medians of `workflow.py --version` and the hook entry (EC-8, AC-7);
  - run the full suite: everything must pass on the unchanged engine.
- **S2:** Create `aidw/api.py` with the moved helpers and the keyword-parameter `resolve_template`. Make `ensure_commit_mode` return its message. Add the three compatibility wrappers. Point `cli/commands.py`, `cli/helpers.py`, the hooks and `workflow.py` at the new locations. Update the layer table. Run the full suite (FR-4, FR-5, FR-6, FR-10, EC-6).
- **S3:** Setup and task-creation commands → API: `discover_setup`, `init_project`, `update_setup`, `new_task`, `status`, `record_discovery`. Their `cmd_*` become renderers. Run the full suite (FR-1, FR-2, FR-3, FR-9, EC-5, EC-10).
- **S4:** Specification and lifecycle commands → API: `spec_check`, `plan_check`, `review`, `approve`, `stage`, `resume`, `pause`. Run the full suite (FR-1, FR-2, FR-3, FR-11, EC-1, EC-3, EC-4).
- **S5:** Implementation and evidence commands → API: `preflight`, `step`, `run_check`, `scope`, `decision`, `check_records`, `outcome`, `close`. Run the full suite and the golden byte comparison (FR-1, FR-2, FR-3, FR-7, FR-8, EC-2, EC-3, EC-9).
- **S6:** Add `tests/test_api.py`:
  - separation tests: CLI modules write nothing (AC-3); lower layers never `print`, `sys.exit`, `os.chdir` or read `sys.argv`, and the API never reads `AI_DEV_WORKFLOW_AGENT` (AC-12);
  - the API-only lifecycle test (AC-4);
  - the two-repository test, with the working directory checked and file descriptors 1 and 2 captured (AC-9, EC-7);
  - JSON parity for the eight `--json` commands (AC-5);
  - the hook module importing nothing from `aidw/cli/` (AC-6).
- **S7:** Finish:
  - docstrings with return keys, type annotations, and the "internal, unversioned" note (FR-12);
  - ruff, mypy, privacy and `unit-py39` (AC-2);
  - re-measure the timing (AC-7);
  - the README "Development" note.

## 6. Important Technical Decisions

Approved in principle by the owner on 2026-11-22: a single module, keyword parameters, plain dictionaries.
- **One module `aidw/api.py`** (about 650 lines), as TARGET_ARCHITECTURE names it. It can be split later into a
  package without changing callers, because they import from `aidw.api`.
- **Keyword parameters, not `argparse.Namespace`**, with `repo` and `agent` always explicit. The API has no implicit
  dependency on the process (working directory, `AI_DEV_WORKFLOW_AGENT`, `sys.argv`).
- **Plain JSON-serialisable `dict` results** with return keys documented in docstrings and type annotations. They
  match today's `--json` outputs; there are no typed result classes or versioning in this phase (internal API).
- **Pin before moving.** The refusal, signature and `preflight --json` behaviours are recorded from the current engine
  in S1. Any difference after the refactor is a regression, not a new baseline.
- **Thin wrappers only where a signature changes** (three names). Nothing else gets a compatibility layer, because
  the other moved names keep their signatures.
- **Exit codes stay in the CLI**, and the `cmd_*` names stay as renderers.
- **Existing defects are recorded, not fixed:** TD-24 for the `preflight --json` trailing text.

## 7. Edge Cases

- **EC-1, FR-11:**
  - Refusal checks move with their code, in the same order and before any write. `main()` still formats
    `WorkflowError`.
  - The S1 refusal golden file compares messages, exit codes, stdout and record hashes.
  - Where today's code mutates the in-memory state before refusing (for example `review`), it saves nothing; the
    hashes prove this stays so.
- **EC-2:** `run_check` returns `output_tail` (redacted, at most 120 lines). `cmd_run` prints it first, then the
  result line. A refusal after a command has run cannot happen today (the secret check on `reason` applies only when
  no command ran), so no output is lost.
- **EC-3:** API results carry `ready`, `valid` or `ok`, or the entry status. The CLI returns 1 exactly where it does
  today.
- **EC-4:** `review` returns the fresh spec check. `resume` returns the paused task and the summary. `approve` returns
  the message it builds today.
- **EC-5:** `status` returns `{setup: false, message}`.
- **EC-6:** the hooks change one import; the existing hook tests cover their output.
- **EC-7:** the two-repository test checks that records land only in their own repository, that the working
  directory is unchanged, and that file descriptors 1 and 2 stay empty.
- **EC-8:** timing before (S1) and after (S7).
- **EC-9:** `cmd_preflight` prints the JSON object or the text, then the trailing lines with today's conditions. The
  S1 golden outputs pin both scenarios.
- **EC-10:** `new_task` returns `commit_mode_message`, and `cmd_new` prints it before "Created task …".

## 8. Testing Plan

| Item | Proof |
|---|---|
| AC-1, FR-3 | `unit` (all 156 existing tests unchanged, plus the new ones) on 3.13 and `unit-py39`; byte comparison of the pre-existing `tests/golden/` files with the S1 copy |
| AC-2, FR-12 | `ruff`, `mypy` (ad hoc checks through `run`) |
| AC-3, FR-2 | CLI separation test |
| AC-4, FR-1 | API-only lifecycle test |
| AC-5, FR-7 | JSON parity test for the eight `--json` commands (`scope` compared on all seven keys) |
| AC-6, FR-4, FR-5, EC-6 | layer, cycle and public-names tests; hook import check |
| AC-7, EC-8 | timing medians of 15 runs before and after, in verification.md |
| AC-8, FR-11, EC-1 | refusal golden test (recorded in S1 from the current engine) |
| AC-9, FR-9, EC-7 | two-repository test with working-directory and file-descriptor checks |
| AC-10, FR-6 | signatures golden test (recorded in S1) |
| AC-11, FR-8, EC-9 | `preflight --json` regression outputs (recorded in S1) |
| AC-12, FR-9, FR-10 | lower-layer separation test |
| EC-2–EC-5, EC-10 | existing scenario and golden tests, plus a records-mode test for EC-10 |
| Done when: CI | `tests` workflow on the pushed commit, 3 OSes × Python 3.9/3.13 |
| Done when: TD-24 | entry in TECHNICAL_DEBT.md |
| Privacy | `privacy` check |

## 9. Risks and Dependencies

- **Hidden output-order change** (risk: medium):
  - mitigated by pinning first (S1);
  - mitigated by one command group per step, with golden, refusal and scenario tests after each.
- **Platform differences in the new golden files** (risk: medium):
  - paths, line endings and hashes can differ on Windows;
  - the S1 tests normalise them as `tests/test_golden.py` does (`<TMP>`, `<PY>`, newline normalisation);
  - hashes are taken over normalised content;
  - CI on three operating systems proves it.
- **Wrapper drift** (risk: low): the signatures test catches any change.
- **Startup time** (risk: low): one more module import on the hook path. Measured; above 50 ms it becomes an audit
  finding.
- **Dependencies:** none open (dependencies.md: DEP-1–DEP-3 Verified).

## 10. Expected Result

- `aidw.api` (internal) exposes 21 functions that run every engine command without printing, without process-level
  hidden inputs, and without changing the working directory.
- The CLI only renders their results and keeps every byte of its output, including the pinned `preflight --json`
  quirk (TD-24).
- Refusals, signatures and records behave exactly as before.
- The hooks no longer depend on the CLI.
- Component discovery (F1.1.1) and adapters (F1.2.1) can build on the API.
