# Feature Spec: Engine API — commands return data, the CLI only prints (F1.0.4)

---

## 1. Requirements

**Goal (one sentence):**
Every engine command is available as an internal Python function that returns data and writes the records, so the CLI (and later the dashboard and orchestrator) only renders results and never re-implements a gate, with no change visible to users or agents.

**User story:**
As a maintainer of AIDevWorkflow, I want the business logic separated from printing (TD-15) so that new front ends and features (component discovery, adapters, the dashboard) call one engine API instead of parsing text or duplicating rules.

**Functional requirements:**
- **FR-1:** A new internal module `skills/ai-dev-workflow/scripts/aidw/api.py` provides one function per command mode: `discover_setup`, `init_project`, `update_setup`, `new_task`, `status`, `record_discovery`, `spec_check`, `plan_check`, `review`, `approve`, `stage`, `resume`, `pause`, `preflight`, `step`, `run_check`, `scope`, `decision`, `check_records`, `outcome`, `close`.
  - Each takes explicit keyword parameters (the repository path, task, agent name, session and the command's options), never an `argparse.Namespace`.
  - Each returns a JSON-serialisable `dict` and raises `WorkflowError` for every refusal.
- **FR-2:** Every record write happens in the API or the layers below it: `state.json`, `ACTIVE`, `config.json`, templates, approved snapshots, `PROJECT.md`, `README.md` in the records folder, the check block in `verification.md`, git exclude rules. Modules in `aidw/cli/` only parse arguments, resolve CLI defaults, call the API, print, and choose the exit code.
- **FR-3:** CLI behaviour stays byte-identical:
  - commands, options and help;
  - every printed line and its order, including today's known quirks (FR-8);
  - `--json` outputs, the stdout/stderr split and exit codes.

  All existing tests and golden files pass unchanged. For `run`, the last 120 lines of the command's output are still printed, redacted, before the result line.
- **FR-4:** The data builders and logic helpers now in the CLI layer move to the API: `status_line`, `task_summary`, `resolve_template`, `install_template`, `change_checks`, `open_tasks`, `scan_records`, `validate_task` and the setup update. Printing helpers (`print_discovery`, `print_spec_check`, `print_summary`) stay in `aidw/cli/`. The Claude Code hooks import from the API, not from the CLI.
- **FR-5:** Layers:
  - `api` is level 4 and imports only from levels 0–3;
  - `agents` and `cli` become level 5 and may import `api`;
  - `tests/test_package.py` enforces the new table, and the import graph has no cycles.
- **FR-6:** Compatibility of names re-exported from `workflow`:
  - Every name in `tests/golden/workflow-public-names.txt` stays importable, with the same call signature. The signatures are recorded before the change in a new `tests/golden/workflow-public-signatures.txt`.
  - Three names change shape inside the package: `resolve_template(args)`, `update_setup(repo, args)` and `ensure_commit_mode(repo, cfg)`. `workflow` re-exports thin CLI-layer wrappers that keep their old signature and behaviour. The API and core versions use keyword parameters or return values.
  - The API functions are not re-exported from `workflow`; front ends import `aidw.api`.
- **FR-7:** JSON outputs (`status`, `spec-check`, `plan-check`, `preflight`, `scope`, `check`, `outcome`, `init --discover`):
  - The CLI builds them only from the API's return value, with no second engine call.
  - For all except `preflight`, the JSON printed equals the API's return value, with the same keys and values as today; in particular `scope` returns exactly today's seven keys.
  - `preflight` also returns `task`, `stage` and `analyzer_hint`, which its text output needs; its `--json` object keeps today's three keys (`valid`, `problems`, `unattributed`).
- **FR-8:** Known behaviour is preserved, not fixed:
  - `preflight --json` today prints, after the JSON object, the "Changes since the last checkpoint…" lines when there are unattributed changes, and the analyzer baseline hint when it applies. That output is not pure JSON.
  - This stays as it is and is pinned by regression tests written against the current engine before the refactor. The defect is recorded separately as TD-24 for a future approved fix.
- **FR-9:** No hidden state in the API:
  - API functions take the repository and the agent name explicitly. They never read `AI_DEV_WORKFLOW_AGENT`, never use or change the current working directory, keep no module-level state between calls, and never print, read `sys.argv` or exit.
  - The CLI keeps resolving its defaults: the current directory when `--repo` is absent, and the agent from `--agent` or `AI_DEV_WORKFLOW_AGENT`.
  - The only environment input the API honours is `AI_DEV_WORKFLOW_HOME` (the user template library), exactly as today, besides git's own environment.
- **FR-10:** The core and lower layers do not print: the one `print` in `core/setup.py` (`ensure_commit_mode`) becomes a returned message. The CLI prints it in the same place as today, before "Created task …".
- **FR-11:** Refusals keep the existing validation order, messages, exit codes and record integrity: a refused command leaves every file under `.ai-dev-workflow/` byte-identical. This is checked against a golden file of refusal scenarios recorded from the current engine before the refactor.
- **FR-12:** ruff and mypy pass. Every API function is type-annotated and has a docstring naming the keys it returns. The module docstring states that the API is internal and unversioned.

**Out of scope (do NOT build):**
- New commands, options or `--json` outputs; any change to messages, record formats or gate rules
- Fixing existing behaviour, including the `preflight --json` trailing text (FR-8, TD-24); defects found are recorded, not fixed
- A public or versioned API, documentation for third parties, frameworks, new dependencies, HTTP servers, databases or background services
- The gate table refactor, state schema check, migration and locking (F1.0.5), single version source (F1.0.6)
- Changes to `install.py`, `SKILL.md`, `references/`, `assets/`, the hooks' behaviour or output
- Rewriting records of other tasks (the closed F1.0.2 and F1.0.3 reports stay as written)
- Performance tuning (startup time is measured and reported, not optimised)

---

## 2. Edge Cases

| ID | Scenario | Expected Behavior |
|----|----------|-------------------|
| EC-1 | A command is refused (invocation without the skill name, bad task name, existing task, short evidence, wrong stage, spec not ready, unknown check, `--baseline` on a non-analyzer check, exclusion without reason, decision without evidence, closing outside FINAL_REPORT, secret in a reason) | The API raises `WorkflowError` at the same point as today. The CLI prints the same `AIDevWorkflow: <message>` on stderr with the same exit code, nothing on stdout, and every file under `.ai-dev-workflow/` stays byte-identical (refusal golden file) |
| EC-2 | `run` executes a command with a long output or a failing exit code | The API returns the redacted last 120 lines and the entry; the CLI prints them before `Check '<id>': …`, as today, and returns 1 for a failure |
| EC-3 | Commands that finish but signal a problem (`spec-check` with mandatory violations, `plan-check` not ready, `preflight` failed, `check` with errors, `run` failed) | The API returns the result without raising; the CLI keeps today's exit code 1 |
| EC-4 | `review` records the review and prints the fresh spec check; `resume` prints the summary and a preflight reminder; `approve` of the plan with a blocking dependency | The API returns the data each output needs (spec-check result, summary, paused task, message); the printed text is unchanged |
| EC-5 | `status` in a repository without AIDevWorkflow set up, with and without `--json` | Same message and same JSON (`setup: false`) as today |
| EC-6 | The Claude Code hooks (`claude-pre-edit`, `claude-prompt`) after the move | Same decisions and output; existing hook tests pass; the hook module imports nothing from `aidw/cli/` |
| EC-7 | API calls in one process, alternating between two repositories, as a dashboard would | Each call reads and writes only its own repository. The working directory is unchanged after every call. Nothing reaches stdout or stderr, including from child processes (captured at file-descriptor level) |
| EC-8 | Startup time of the hook path (it runs on every edit in Claude Code) | Median of `workflow.py --version` and of the hook entry measured before and after; a slowdown above 50 ms is reported as an audit finding, never hidden |
| EC-9 | `preflight --json` with unattributed changes, and with the analyzer baseline hint | Output is identical to today's: the JSON object followed by the same text lines (FR-8), pinned by regression tests recorded before the refactor |
| EC-10 | `new` in a clone where the records commit mode is not yet applied (`config-only` or `none`) | The exclude rules are written by the API; the CLI prints "Applied records.commit=… in this clone (local git exclude only)." before "Created task …", as today |

---

## 3. Constraints (must NOT change)

- **Protected files / modules:**
  - `SKILL.md`, `references/`, `assets/`, `install.py`, `index.html`, `docs/`, `tools/`, every existing golden file;
  - the records of other tasks under `.ai-dev-workflow/tasks/`: historical reports are never rewritten;
  - every existing test except the layer table in `tests/test_package.py` (FR-5).
- **Public contracts:** the CLI (commands, options, help, outputs, exit codes), record formats, the `scripts/workflow.py` path, and the names and call signatures importable from `workflow`.
- **Allowed packages:** Python standard library only, Python 3.9+. No new packages without approval.
- **Architecture:** TARGET_ARCHITECTURE §2–3: front ends call the engine API and never write records; the core never imports a front end and never prints; the skill folder stays self-contained; no logic in `workflow.py`; the API stays internal.
- **Scope:**
  - `scripts/aidw/api.py` (new), `scripts/aidw/cli/`;
  - `scripts/aidw/agents/claude_hooks.py` (imports only), `scripts/aidw/core/setup.py` (`ensure_commit_mode` only), `scripts/workflow.py` (re-exports);
  - `tests/test_package.py` (layer table), a new `tests/test_api.py`;
  - new golden files `tests/golden/refusals.json`, `tests/golden/workflow-public-signatures.txt` and the `preflight --json` regression outputs;
  - a few lines in the README "Development" section.
- **If anything is unclear:** stop and ask. Do not guess.

---

## 4. Acceptance Criteria

- **AC-1:** Given the refactored engine, when the full suite runs on Python 3.13 and 3.9, then every test passes and no pre-existing file in `tests/golden/` changed.
- **AC-2:** Given the change, when ruff and mypy run with the project configuration, then both report no issues.
- **AC-3:** Given the modules in `aidw/cli/`, when the separation test inspects their source, then none imports or calls a record-writing function and none opens a file for writing. The functions checked are `save_state`, `save_json`, `write_text`, `activate`, `clear_active`, `add_history`, `add_checkpoint`, `make_readonly`, `apply_commit_mode` and `regenerate_check_block`.
- **AC-4:** Given a temporary repository, when a test drives a task from setup to close using only API functions, then each call returns the documented data, the records match what the CLI produces, and nothing is printed during the calls.
- **AC-5:** Given the commands with `--json` output, when the CLI runs with `--json`, then its output equals the JSON encoding of the API's return value for the same state. For `preflight`, it equals the encoding of the `valid`, `problems` and `unattributed` keys, followed by the trailing lines of FR-8 when they apply.
- **AC-6:** Given the package, when the layer, cycle and public-names tests run, then they pass with `api` at level 4 and `agents`/`cli` at level 5, and the hook module imports nothing from `aidw/cli/`.
- **AC-7:** Given before/after timing of `workflow.py --version` and the hook entry, when the report is written, then both medians are recorded with the difference.
- **AC-8:** Given the refusal scenarios of EC-1 recorded from the current engine in `tests/golden/refusals.json` (exit code, stdout, stderr, and a hash of every file under `.ai-dev-workflow/` before and after), when they run against the refactored engine, then every value is identical.
- **AC-9:** Given two temporary repositories, when a test calls API functions alternately on each in one process, then each repository's records reflect only its own calls, the working directory is unchanged, and nothing is written to file descriptors 1 or 2.
- **AC-10:** Given `tests/golden/workflow-public-signatures.txt` recorded before the change, when the signatures test runs, then every public callable in `workflow` has the same signature, including the wrappers for `resolve_template`, `update_setup` and `ensure_commit_mode`.
- **AC-11:** Given the `preflight --json` outputs recorded from the current engine for EC-9, when the same scenarios run after the refactor, then the outputs are byte-identical.
- **AC-12:** Given the modules below the front ends (`api`, `core`, `adapters`, `store`, `records`, `infra`, `constants`, `errors`), when the separation test inspects them, then none calls `print`, `sys.exit`, `os.chdir` or reads `sys.argv`. The API also never reads `AI_DEV_WORKFLOW_AGENT`.

**Done when:**
- [ ] All requirements implemented
- [ ] All edge cases handled as specified
- [ ] Required tests pass through the engine: `unit`, `unit-py39`, `privacy`, `ruff`, `mypy`
- [ ] CI (`tests` workflow) passes on Linux, Windows and macOS with Python 3.9 and 3.13 on the pushed commit
- [ ] TD-24 (`preflight --json` trailing text) is recorded in TECHNICAL_DEBT.md for a future approved fix
- [ ] The README "Development" section mentions the internal API layer in a few lines
