# Feature Spec: Engine API — commands return data, the CLI only prints (F1.0.4)

---

## 1. Requirements

**Goal (one sentence):**
Every engine command is available as a Python function that returns data and writes the records, so the CLI (and later the dashboard and orchestrator) only renders results and never re-implements a gate, with no change visible to users or agents.

**User story:**
As a maintainer of AIDevWorkflow, I want the business logic separated from printing (TD-15) so that new front ends and features (component discovery, adapters, the dashboard) call one engine API instead of parsing text or duplicating rules.

**Functional requirements:**
- **FR-1:** A new module `skills/ai-dev-workflow/scripts/aidw/api.py` provides one public function per engine command: `discover_setup`, `init_project`, `update_setup`, `new_task`, `status`, `record_discovery`, `spec_check`, `plan_check`, `review`, `approve`, `stage`, `resume`, `pause`, `preflight`, `step`, `run_check`, `scope`, `decision`, `check_records`, `outcome`, `close`. Each takes keyword parameters (repository path, task, agent name, session and the command's options; never an `argparse.Namespace`), returns a JSON-serialisable `dict`, and raises `WorkflowError` for every refusal.
- **FR-2:** Every record write (`state.json`, `ACTIVE`, `config.json`, templates, approved snapshots, `PROJECT.md`, `README.md` in the records folder, the check block in `verification.md`, git exclude rules) happens in the API or the layers below it. Modules in `aidw/cli/` only parse arguments, call the API, print, and choose the exit code.
- **FR-3:** CLI behaviour stays byte-identical: commands, options, help, every printed line and its order, `--json` outputs, stdout/stderr split and exit codes. All existing tests and golden files pass unchanged. For `run`, the last 120 lines of the command's output are still printed, redacted, before the result line.
- **FR-4:** The data builders and logic helpers now in the CLI layer move to the API: `status_line`, `task_summary`, `resolve_template`, `install_template`, `change_checks`, `open_tasks`, `scan_records`, `validate_task` and the setup update. Printing helpers (`print_discovery`, `print_spec_check`, `print_summary`) stay in `aidw/cli/`. The Claude Code hooks import from the API, not from the CLI.
- **FR-5:** Layers: `api` is level 4 and imports only from levels 0–3; `agents` and `cli` become level 5 and may import `api`. `tests/test_package.py` enforces the new table, and the import graph has no cycles.
- **FR-6:** Every name in `tests/golden/workflow-public-names.txt` stays importable from `workflow`. The `cmd_*` functions keep their signature (`args` → exit code). Helpers that move to the API may take keyword parameters instead of `args`; no test or tool calls them with the old signature.
- **FR-7:** The API works without the CLI: no API function prints, reads `sys.argv` or exits the process. Where a command has `--json` output today (`status`, `spec-check`, `plan-check`, `preflight`, `scope`, `check`, `outcome`, `init --discover`), the CLI builds it only from the API's return value, with no second engine call and the same keys and values as today (for `preflight`, the API also returns the task, stage and analyzer hint the text output needs; `--json` keeps its three keys).
- **FR-8:** ruff and mypy pass. Every API function is type-annotated and has a docstring naming the keys it returns.

**Out of scope (do NOT build):**
- New commands, options or `--json` outputs; any change to messages, record formats or gate rules
- A stable versioned public API promise for third parties (the API is internal until a later phase documents it)
- The gate table refactor, state schema check, migration and locking (F1.0.5), single version source (F1.0.6)
- Changes to `install.py`, `SKILL.md`, `references/`, `assets/`, the hooks' behaviour or output
- Performance tuning (startup time is measured and reported, not optimised)

---

## 2. Edge Cases

| ID | Scenario | Expected Behavior |
|----|----------|-------------------|
| EC-1 | A command is refused (wrong stage, missing evidence, secret in a reason, unknown check) | The API raises `WorkflowError` before writing anything, exactly where the command refuses today; the CLI prints `AIDevWorkflow: <message>` on stderr with the same exit code |
| EC-2 | `run` executes a command with a long output or a failing exit code | The API returns the redacted last 120 lines and the entry; the CLI prints them before `Check '<id>': …`, as today, and returns 1 for a failure |
| EC-3 | Commands that finish but signal a problem (`spec-check` with mandatory violations, `plan-check` not ready, `preflight` failed, `check` with errors, `run` failed) | The API returns the result without raising; the CLI keeps today's exit code 1 |
| EC-4 | `review` records the review and prints the fresh spec check; `resume` prints the summary and a preflight reminder; `approve` of the plan with a blocking dependency | The API returns the data each output needs (spec-check result, summary, paused task, message); the printed text is unchanged |
| EC-5 | `status` in a repository without AIDevWorkflow set up, with and without `--json` | Same message and same JSON (`setup: false`) as today |
| EC-6 | The Claude Code hooks (`claude-pre-edit`, `claude-prompt`) after the move | Same decisions and output; existing hook tests pass; the hook module imports nothing from `aidw/cli/` |
| EC-7 | The API is called several times in one process, as a dashboard would | No output on stdout or stderr during API calls (a test captures both); results depend only on the repository and arguments |
| EC-8 | Startup time of the hook path (it runs on every edit in Claude Code) | Median of `workflow.py --version` and of the hook entry measured before and after; a slowdown above 50 ms is reported as an audit finding, never hidden |

---

## 3. Constraints (must NOT change)

- **Protected files / modules:** `SKILL.md`, `references/`, `assets/`, `install.py`, `index.html`, `docs/`, `tools/`, every golden file, and every existing test except the layer table in `tests/test_package.py` (FR-5).
- **Public contracts:** the CLI (commands, options, help, outputs, exit codes), record formats, the `scripts/workflow.py` path, and the names importable from `workflow`.
- **Allowed packages:** Python standard library only, Python 3.9+. No new packages without approval.
- **Architecture:** TARGET_ARCHITECTURE §2–3: front ends call the engine API and never write records; the core never imports a front end; the skill folder stays self-contained; no logic in `workflow.py`.
- **Scope:** `scripts/aidw/api.py` (new), `scripts/aidw/cli/`, `scripts/aidw/agents/claude_hooks.py` (imports only), `scripts/workflow.py` (re-exports), `tests/test_package.py` (layer table), a new `tests/test_api.py`, and a few lines in the README "Development" section.
- **If anything is unclear:** stop and ask. Do not guess.

---

## 4. Acceptance Criteria

- **AC-1:** Given the refactored engine, when the full suite runs on Python 3.13 and 3.9, then every test passes and no file in `tests/golden/` changed.
- **AC-2:** Given the change, when ruff and mypy run with the project configuration, then both report no issues.
- **AC-3:** Given the modules in `aidw/cli/`, when the separation test inspects their source, then none imports or calls a record-writing function (`save_state`, `save_json`, `write_text`, `activate`, `clear_active`, `add_history`, `add_checkpoint`, `make_readonly`, `apply_commit_mode`, `regenerate_check_block`) and none opens a file for writing.
- **AC-4:** Given a temporary repository, when a test drives a task from setup to close using only API functions, then each call returns the documented data, the records match what the CLI produces, and nothing is printed during the calls.
- **AC-5:** Given the commands with `--json` output, when the CLI runs with `--json`, then its output equals the JSON encoding of the API's return value for the same state (for `preflight`, of its `valid`, `problems` and `unattributed` keys).
- **AC-6:** Given the package, when the layer, cycle and public-names tests run, then they pass with `api` at level 4 and `agents`/`cli` at level 5, and the hook module imports nothing from `aidw/cli/`.
- **AC-7:** Given before/after timing of `workflow.py --version` and the hook entry, when the report is written, then both medians are recorded with the difference.

**Done when:**
- [ ] All requirements implemented
- [ ] All edge cases handled as specified
- [ ] Required tests pass through the engine: `unit`, `unit-py39`, `privacy`, `ruff`, `mypy`
- [ ] CI (`tests` workflow) passes on Linux, Windows and macOS with Python 3.9 and 3.13 on the pushed commit
- [ ] The README "Development" section mentions the API layer in a few lines
