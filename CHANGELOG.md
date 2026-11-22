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

## 1.0.1 — 2026-11-22

Security release for TD-25, based on v1.0.0. Main retains its separate unreleased changes above.

- Secret-like agent names (`--agent` or `AI_DEV_WORKFLOW_AGENT`), session ids and check ids are rejected before
  affected records are written or check commands run. Refusals name the field without echoing its value.
- Session ids have a separate 1–256 printable-character format rule. Claude Code hooks reject invalid session ids
  without logging them and deny edits inside an active task when the session identity cannot be validated.
- Task-creation rollback preserves files the operation did not write; `run` saves state before regenerating the
  verification check block. Multi-file updates remain non-transactional.
- Detection is pattern-based and can miss unknown credential formats, including the documented U+0085 and U+2028
  cases. The session format rule independently rejects those separators.
- Windows compatibility: command output falls back to the system code page if UTF-8 decoding fails, analyzer
  output accepts the replacement separator, and the CRLF regression fixture normalizes existing line endings.

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
