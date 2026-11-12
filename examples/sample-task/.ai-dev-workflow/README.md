# AIDevWorkflow records

This folder is managed by the `ai-dev-workflow` skill (AIDevWorkflow — Structured AI-Assisted
Development, From Requirements to Release).

- `config.json` — this project's setup: instruction files, specification template, checks.
- `templates/` — the specification template this project uses (and its rules file, if any).
- `tasks/<task>/` — one folder per task: spec, dependencies, plan, approved snapshots, state,
  verification, audit and final report.

To continue a task, invoke the skill explicitly (for example `/ai-dev-workflow <task>` in
Claude Code or Gemini CLI, `$ai-dev-workflow <task>` in Codex). Outside the skill these files are
just records; agents are not bound by them. `state.json` and `approved/` are written by
`workflow.py` only — do not edit them by hand.
