# Changelog

## 1.0.1 — Security (unreleased; awaiting the owner's release approval)

Security patch for 1.0.0. It contains only the TD-25 fix: no features or restructuring from later development.

- A secret-like agent name (`--agent` or `AI_DEV_WORKFLOW_AGENT`), session id (`--session`) or check name
  (`run <task> <name>`) is refused before anything runs or is written. In 1.0.0 such a value could reach
  `verification.md` or the local `ACTIVE` pointer before the secret check refused `state.json`, and a secret-like
  session id was stored and accepted. Refusal messages name the field, never the value.
- Session ids must be 1–256 printable characters without spaces (Claude Code's UUIDs pass); `${…}`, `none` and
  `null` still mean "no session".
- The Claude Code hooks treat the payload session id as untrusted. An invalid one is never written to `ACTIVE` or the
  hook log, and inside an active task the edit is denied. Without an active task nothing changes.
- On failure, `new` removes the files it wrote (best effort; a crash or a locked file can still leave them) and never
  removes anything else. `run` saves `state.json` before rewriting the check block. Multi-file updates are still not
  transactional.
- Detection is pattern-based: a credential in a format the scanner does not know is not recognised.
- Affected: 1.0.0, and development versions before this fix. Mitigation until 1.0.1 is installed: never type
  credentials into `--agent`, `--session` or check names.

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
