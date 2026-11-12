# Setting up a project

The skill is project-agnostic. Each project gets a small setup in `.ai-dev-workflow/`, created only after the user
explicitly invoked the skill and confirmed the choices.

## First run

1. `workflow.py init --discover` lists the instruction files found (CLAUDE.md, AGENTS.md, GEMINI.md, …), files that
   look like specification templates, templates in the user's private library, and suggested checks based on the
   project's tooling (pubspec.yaml, package.json, pyproject.toml, go.mod, Cargo.toml, …).
2. Show the user what was found and ask them to confirm:
   - **engineering standards** — the instruction files every agent must follow for this project;
   - **specification template** — a template file in the repository, a template from their private library
     (`user:<name>`), or one they provide now. Never choose for them and never invent one; if there is none, ask
     for it and stop;
   - **checks** — the commands that verify the project (adjust the suggestions with them);
   - **commit mode** for task records: `all` (shared with teammates, other machines and cloud agents),
     `config-only` (setup shared, task records local) or `none` (everything local).
3. Run `init` with those choices, for example:

```
workflow.py init --template user:my-template --commit all --standards CLAUDE.md
workflow.py init --template docs/spec-template.md --rules docs/spec-template.rules.json --commit config-only
workflow.py init --template <file> --commit all --config <checks-and-rules.json> --project-notes <PROJECT.md>
```

`init` copies the chosen template (and its rules file) into `.ai-dev-workflow/templates/`, so every agent and machine
uses the same version. With `config-only` or `none` it adds rules to the repository's local git exclude file; no
tracked file changes. Change these later with `init --update --commit <mode>` or `--standards <files>`.

## config.json

| Field | Meaning |
|---|---|
| `standards` | instruction files every agent reads for planning, implementation and audit |
| `spec_template`, `spec_rules` | the project's template and optional rules file (copied by `init`) |
| `template_source` | where the template came from (`user:<name>` or `file:<name>`) |
| `records.commit` | `all`, `config-only` or `none` |
| `checks` | verification commands: `id`, `name`, `command`, `required`, optional `when` (conditional), `accepts_args`, `timeout_s`, `parser` (`dart-analyzer`, with `fail_on`), or `builtin` (`json-key-parity` with `files`, `rule-scan`, `manifest-diff` with `files`) |
| `rules` | patterns for `rule-scan`: `id`, `pattern` (regex), `paths`, `exclude`, `max_per_file`, `severity` (`error` or `warning`), `message` |

## Template rules files

A rules file sits next to its template (`<template>.rules.json`) and classifies the template's requirements. Without
one, only the structure derived from the template applies (headings, fields, placeholders). With one:

- `id_prefixes` — ID families checked for uniqueness and order (for example `["FR", "EC", "AC"]`);
- `patterns` — mandatory formats (`target`, `regex`, `message`);
- `tables` — table rows that must be complete;
- `content_required` — fields that need real content (`allow_none: true` permits "None — <reason>");
- `verification` — which IDs and which checklist the acceptance matrix must cover;
- `judgment` — rules that need judgment, with detectors (`vague-words`, `inspected-files`, `coverage-map`);
- `advisory` — warnings (`questions`, `label-mentions`, `none-entry`, `prompts`).

Classify by the template's own language: what the template or its guide defines as mandatory blocks approval;
recommendations become warnings. Do not add numeric limits on how many requirements, edge cases, exclusions or
criteria a spec has.

A rules file uses these targets: `label:<field name>`, `section:<heading start>`, `ids:<PREFIX>` and
`table:<PREFIX>:<column>`.

## Private template library

A user can keep personal templates outside any repository and offer them to projects:

```
python3 <SKILL_DIR>/scripts/install.py add-template my-template /path/to/spec-template.md --rules /path/to/rules.json
```

They are stored in `~/.ai-dev-workflow/templates/<name>/` (or `$AI_DEV_WORKFLOW_HOME`) and appear in
`init --discover` as `user:<name>`. They are never applied to a project unless the user picks them.

## PROJECT.md

Project notes every agent reads with the standards files: conflicts between instructions and how they were
resolved, the audit checklist (pointers to the sections of the standards files the audit must check), testing
conventions, and anything the setup could not detect. Update it when the user resolves a project-wide question.

## Agent notes

- **Claude Code** — pass `--session ${CLAUDE_SESSION_ID}` to `new`, `resume` and `preflight`. The skill's hooks block
  code edits while the task you started in this session is not in IMPLEMENTATION or FIXING with valid approvals and a
  passing preflight. They stay silent once the task is paused or closed, in other sessions, and in other repositories.
- **Codex** — the skill is invoked explicitly with `$ai-dev-workflow`. In the `workspace-write` sandbox, commands
  that write outside the repository (for example a package cache) may need approval; record a check as blocked if it
  cannot run.
- **Gemini CLI** — activating a skill asks for consent; project-level skills load only in trusted folders.
- **All agents** — gates that are not enforced by a hook depend on following these instructions; `workflow.py`
  detects most deviations afterwards (changed approved documents, stale evidence, unexplained changes).
