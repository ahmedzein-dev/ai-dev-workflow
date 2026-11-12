# Configuration

Each project's setup lives in `.ai-dev-workflow/config.json`, created by `workflow.py init` after you confirm the
choices. You can edit it by hand afterwards (it is not part of any approval).

```json
{
  "schema": 1,
  "project": "example-app",
  "standards": ["AGENTS.md"],
  "spec_template": ".ai-dev-workflow/templates/example-spec-template.md",
  "spec_rules": ".ai-dev-workflow/templates/example-spec-template.rules.json",
  "template_source": "file:example-spec-template.md",
  "records": {"commit": "all"},
  "checks": [ … ],
  "rules": [ … ]
}
```

| Field | Meaning |
|---|---|
| `standards` | Instruction files every agent reads before planning, implementing and auditing (CLAUDE.md, AGENTS.md, …) |
| `spec_template`, `spec_rules` | The project's template and optional rules file, copied by `init` — see [templates-and-rules.md](templates-and-rules.md) |
| `template_source` | Where the template came from (`user:<name>` or `file:<name>`); no absolute paths are stored |
| `records.commit` | `all`, `config-only` or `none` |
| `setup` | What `init` recommended and what you chose (`recommended`, `chosen`), plus later `changes` |
| `checks` | Verification commands (below) |
| `rules` | Patterns for the `rule-scan` check (below) |

Change settings with `workflow.py init --update` and `--commit <mode>`, `--standards <files>`, `--template <template>`
(not while a task is open), `--add-check <id>=<command>` or `--without-check <id>`. A check may also carry `explain`,
the one-line description shown during setup.

## Checks

```json
{"id": "analyze", "name": "flutter analyze", "command": "flutter analyze", "parser": "dart-analyzer",
 "fail_on": ["error", "warning", "new"], "required": true}
```

| Field | Meaning |
|---|---|
| `id`, `name` | How the check is referred to (`workflow.py run <task> <id>`) |
| `command` | Run from the repository root without a shell; the first word is looked up on PATH |
| `required` | Must have a fresh result before the audit and for a Completed status |
| `when` | Makes a required check conditional; the agent may then record it as not applicable, with a reason |
| `accepts_args` | Allows extra arguments: `run <task> test -- path/to/test` |
| `timeout_s` | Default 1800 |
| `parser` | `dart-analyzer`: counts issues by severity (Dart/Flutter analyzer output) instead of trusting the exit code |
| `fail_on` | For the analyzer parser: any of `error`, `warning`, `info`, and `new` (issues not in the baseline) |
| `builtin` | Instead of a command: `json-key-parity` (with `files`), `rule-scan`, `manifest-diff` (with `files`) |

Results are recorded in `state.json` and summarized in `verification.md`, each with a fingerprint of the code. When
the code changes, the result is stale. Commits do not change the fingerprint.

### Built-in checks

- **`json-key-parity`** — the listed JSON files (for example translation files) must have the same keys. Gaps that
  existed before the task are reported as pre-existing.
- **`rule-scan`** — applies `rules` to the files the task changed, and fails only on violations the task introduced.
- **`manifest-diff`** — compares dependency manifests (`pubspec.yaml`, `package.json`, `requirements.txt`) with the
  state before implementation. New dependencies fail the check until the user's approval is recorded with
  `workflow.py decision <task> --text "Approved adding <name>" --evidence "<their words>"`.

### Analyzer baseline

Right after the plan is approved and before the first code edit, the agent captures existing analyzer issues:
`workflow.py run <task> analyze --baseline`. Later runs separate issues the task introduced from issues that were
already there (`preexisting` status, which caps the outcome at Completed with Limitations).

## Rule scans

```json
{"id": "no-print", "pattern": "(?<![\\w.])print\\(", "paths": ["lib/**/*.dart"], "exclude": ["lib/dev/**"],
 "max_per_file": 0, "severity": "error", "message": "Remove debug print() calls from production code."}
```

| Field | Meaning |
|---|---|
| `pattern` | Python regular expression, matched per file (multiline) |
| `paths`, `exclude` | Glob patterns (`**` matches directories) |
| `max_per_file` | Allowed matches per file (default 0) — for example 1 for "one class of this kind per file" |
| `severity` | `error` fails the check; `warning` is listed in the summary |

Rule scans are a safety net for rules that can be expressed as patterns. They do not replace the audit against the
full standards files.

## PROJECT.md

Notes every agent reads with the standards files: instruction conflicts and how they were resolved, the audit
checklist (pointers to the sections of the standards files the audit must check), testing conventions, and anything
the setup could not detect. Pass your own with `init --project-notes <file>`.

## Starting points

[`examples/configs/flutter.json`](../examples/configs/flutter.json) and
[`examples/configs/node.json`](../examples/configs/node.json) can be passed to `init --config`.
