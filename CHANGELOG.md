# Changelog

## Unreleased

- Guided first-time setup: `init --discover` now proposes a complete setup with plain-language explanations — your
  default template (`install.py add-template … --default`, `install.py default-template`), checks found from the
  project's own files (with what each does, why it was suggested, and whether its tool is installed), the commands
  the CI already runs, and what each records option really does, with a recommendation and its trade-off.
- An existing setup is reused without asking again; `init --discover` lists only its problems.
- `config.json` → `setup` records what was recommended and what the user chose.
- `init` and `init --update` accept `--without-check` and `--add-check`; `init --update --template` changes the
  template when no task is open.
- The `config-only` and `none` exclusions are re-applied in a new clone when a task starts.

## 1.0.0 — 2026-11-12

First release.

- `ai-dev-workflow` skill (Agent Skills format) with an 11-stage lifecycle: discovery, dependencies, specification,
  spec approval, planning, plan approval, implementation, testing, fixing, audit, final report.
- Explicit activation only: `disable-model-invocation` (Claude Code), `allow_implicit_invocation: false` (Codex),
  and a first-rule guard plus an invocation check for every agent.
- `workflow.py` engine: guarded stage changes, hash-bound approvals with read-only snapshots, preflight
  revalidation, per-project templates with mandatory / judgment / advisory rules (no numeric limits), recorded check
  evidence with code fingerprints, analyzer baselines, built-in checks, secret scanning, outcome caps.
- Claude Code hooks scoped to the skill: block code edits only for the task started in that session.
- `install.py`: one canonical copy, links or copies per agent, project-level installs, `doctor`, private template
  library.
- Standalone `index.html` guide in English and Arabic, docs, examples, tests and a pre-publish privacy scan.
