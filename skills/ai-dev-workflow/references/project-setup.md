# Setting up a project

The skill is project-agnostic. Each project gets a small setup in `.ai-dev-workflow/`, created only after the user
explicitly invoked the skill and confirmed the choices.

## First run: guided setup

The goal is a short setup the user can answer without knowing git or the project's toolchain: you propose, explain
and ask once; they accept or change.

1. Run `workflow.py init --discover` (add `--json` for structured output). It changes nothing. If it says the
   project is **already set up**, reuse the settings and skip the questions; only fix the problems it lists, or
   change what the user asks for with `init --update`.
2. Otherwise present its proposal, in the user's language and in plain words, as one short message:
   - **Engineering standards** — the instruction files found; every agent follows them.
   - **Specification template** — if a default template is registered in the user's private library, it is the
     recommendation (`user:<name>`); say which one and that it lives outside every repository. Otherwise say so
     plainly and list what was found (repository files marked "example" are samples, not recommendations) or ask the
     user to provide one. Never pick a template on their behalf.
   - **Checks** — each recommended command with its one-line explanation and what it was found from (for example
     pubspec.yaml, a package.json script, a pytest configuration, the CI workflow). Say they have not been run yet
     and mention any tool "not found on this computer". If nothing was detected, inspect the README, scripts and CI
     and propose commands yourself; never invent ones you have not seen evidence for.
   - **Saving task records in git** — explain the three options with the output's own words (what is committed,
     what a clone contains, whether another computer or agent can resume, what is lost with this computer, privacy),
     then the recommended option, its reason and its trade-off.
3. Ask: accept everything as recommended, or change any item. Wait for the answer. Silence or a question is not
   acceptance.
4. Run `init` with exactly what they confirmed:

```
workflow.py init --template user:my-template --commit all --standards CLAUDE.md,AGENTS.md
workflow.py init --template docs/spec-template.md --commit config-only --without-check codegen --add-check e2e="npm run e2e"
workflow.py init --template <file> --commit all --config <checks-and-rules.json> --project-notes <PROJECT.md>
```

`init` copies the chosen template (and its rules file) into `.ai-dev-workflow/templates/`, so every agent and machine
uses the same version, and records in `config.json` → `setup` both what was recommended and what the user chose.
With `config-only` or `none` it adds rules to the repository's local git exclude file (no tracked file changes); in a
new clone they are re-applied when the next task starts. The settings are reused for every later task.

Change settings only when the user asks: `init --update` with `--commit`, `--standards`, `--template` (refused while
a task is still open, so its spec keeps its template), `--add-check` or `--without-check`. Never change the records
mode of an existing project on your own.

## config.json

| Field | Meaning |
|---|---|
| `standards` | instruction files every agent reads for planning, implementation and audit |
| `spec_template`, `spec_rules` | the project's template and optional rules file (copied by `init`) |
| `template_source` | where the template came from (`user:<name>` or `file:<name>`) |
| `records.commit` | `all`, `config-only` or `none` |
| `setup` | what `init` recommended and what the user chose (`recommended`, `chosen`), and later `changes` |
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
`init --discover` as `user:<name>`. Add `--default` (or run `install.py default-template <name>`) to make one the
recommendation for every new project. Templates are never applied to a project unless the user confirms them.

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
