# Changelog

## Unreleased

- **Security (TD-25):** a secret-like agent name (`--agent` or `AI_DEV_WORKFLOW_AGENT`), session id (`--session`)
  or check name (`run <task> <name>`) is now refused before anything runs or is written. Before, such a value could
  reach `verification.md` or the local `ACTIVE` pointer before the secret check refused `state.json`, and a
  secret-like session id was stored and accepted. Refusal messages name the field, never the value. Values are checked
  as given and in their JSON form, as `state.json` is. Detection is pattern-based: a credential in a format the scanner
  does not know is not recognised, nor a value split by U+0085 or U+2028.
- **Claude Code hooks:** the session id in a hook payload is treated as untrusted input. An invalid one (secret-like,
  malformed or not text) is never written to `ACTIVE` or the hook log, and inside an active task the edit is denied
  so it cannot bypass the gates. Without an active task the hooks behave as before.
- **Session ids** must be 1–256 printable characters without spaces (Claude Code's UUIDs pass); other values are
  refused with an explicit message. `${…}`, `none` and `null` are still treated as "no session".
- On failure, `new` removes the files it wrote (best effort: a crash or a locked file can still leave them) and never
  removes anything else. `run` now saves `state.json` before rewriting the check block in `verification.md`. Updates
  that touch several files are still not transactional (TD-29).
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
