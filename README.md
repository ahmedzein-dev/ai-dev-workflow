# AIDevWorkflow

**Structured AI-Assisted Development — From Requirements to Release.**

AIDevWorkflow is a reusable [Agent Skill](https://agentskills.io) named `ai-dev-workflow` that takes a feature, bug
fix or refactoring from requirements to a verified, audited result — with your approval at the two points that
matter, and with task records any supported coding agent can pick up.

- **You decide when it runs.** It starts only when you invoke it. Outside the skill, your agents behave as usual.
- **One skill, several agents.** The same folder works in Claude Code, Codex, Gemini CLI and Antigravity; each
  agent has its own invocation syntax.
- **Nothing lives only in chat.** Specs, plans, approvals, progress, evidence and audits are files in your
  repository, so you can start in one agent and finish in another.

Open [`index.html`](index.html) in a browser for the visual guide, in English and Arabic.

## How it works

```
Discovery → Dependencies → Specification → Spec approval → Planning → Plan approval
          → Implementation → Testing ⇄ Fixing → Audit → Final report
```

- The agent asks only what your code cannot answer, and drafts ready-to-send questions for the backend team when an
  API contract is missing.
- The spec uses **your project's template**. Mandatory template rules block approval; recommendations only warn.
  There are no limits on how many requirements, edge cases or acceptance criteria a spec has.
- Approvals are your own words, bound to a SHA-256 of the exact spec or plan version. The approved files are frozen;
  any change needs your approval again.
- No feature code is written before the plan is approved, and every session revalidates the task (`preflight`)
  before touching code.
- Checks are run by the engine and recorded with a fingerprint of the code; stale or missing evidence is never
  reported as passing.
- The final status is computed from the evidence. An accepted Critical or Important finding never yields
  "Completed".

## Quick start

Requirements: git, Python 3.9+.

```bash
git clone https://github.com/ahmedzein-dev/ai-dev-workflow.git
cd ai-dev-workflow
python3 skills/ai-dev-workflow/scripts/install.py
python3 skills/ai-dev-workflow/scripts/install.py doctor
```

The installer keeps one copy in `~/.agents/skills/ai-dev-workflow` (read by Codex and Gemini CLI) and links Claude
Code (and Antigravity, if present) to it, falling back to a copy where links are not available. See
[docs/installation.md](docs/installation.md) for project-level installs, Windows and cloud agents.

Then, in a project:

| Agent | Start a task | Resume it |
|---|---|---|
| Claude Code | `/ai-dev-workflow Add saved favorites to the item list` | `/ai-dev-workflow saved-favorites` |
| Codex | `$ai-dev-workflow Add saved favorites to the item list` (or pick it in `/skills`) | `$ai-dev-workflow saved-favorites` |
| Gemini CLI | `/ai-dev-workflow Add saved favorites to the item list` | `/ai-dev-workflow saved-favorites` |
| Antigravity | `/ai-dev-workflow Add saved favorites to the item list` | `/ai-dev-workflow saved-favorites` |

The first time in a project, the agent shows you the instruction files, template candidates and checks it found,
and asks which template to use and whether task records are committed. See [docs/usage.md](docs/usage.md).

## Supported agents

| Agent | Manual-only | Hooks | Evidence |
|---|---|---|---|
| Claude Code | Yes — `disable-model-invocation: true` | Skill-scoped: block code edits for the active task only | Tested (2.1.263): explicit start, no implicit start, hook gate, a full task end to end |
| Codex | Yes — `agents/openai.yaml`: `allow_implicit_invocation: false` | Not used (project-wide only) | Tested (0.166): explicit start, no implicit start, a full task end to end |
| Gemini CLI | No setting exists; every model-initiated activation asks for consent | Not used (project-wide only) | Tested (0.53.1): slash command, by name, no implicit start, handoff; full task not run |
| Antigravity | Not documented | Not used | Vendor docs; manual check described |
| Other Agent Skills clients | Varies | — | Unverified |

Where an agent cannot be made manual-only, the skill's first rule tells it to stop and ask, and the engine refuses
to create task files unless it receives your starting message naming the skill. That reduces, but cannot eliminate,
the chance of an unwanted start. [docs/compatibility.md](docs/compatibility.md) lists exactly what was tested, on
which versions, and what remains unverified.

## Task records

```
.ai-dev-workflow/
├── config.json        project setup: standards files, template, checks
├── PROJECT.md         project notes: instruction conflicts, audit checklist
├── templates/         the project's specification template (+ rules file)
└── tasks/<task>/
    ├── spec.md  dependencies.md  plan.md  approved/
    ├── state.json     stage, approvals, progress, evidence, history
    ├── verification.md  audit.md  report.md
```

Whether task records are committed is your choice per project: `all`, `config-only` or `none`.

## What is enforced

| Rule | Mechanism |
|---|---|
| Stage order, prerequisites, approval–version binding, completion rules | `workflow.py` (every agent) |
| No code edits before an approved plan and a passing preflight | Claude Code: skill hook. Other agents: instructions, plus detection afterwards |
| Evidence freshness, secret-free records | `workflow.py` |
| Good questions, no invented contracts, honest reporting, audit quality | Instructions in the skill |

An agent runs as your user account, so no file-based workflow can make self-approval technically impossible. The
engine records the evidence and catches later changes; the rules forbid the rest.

## Documentation

- [index.html](index.html) — the visual guide (English and Arabic)
- [docs/installation.md](docs/installation.md) — install, update, uninstall; user and project level
- [docs/usage.md](docs/usage.md) — starting, approving, resuming, switching agents, finishing
- [docs/compatibility.md](docs/compatibility.md) — per-agent behavior, evidence and limitations
- [docs/configuration.md](docs/configuration.md) — `config.json`, checks and rule scans
- [docs/templates-and-rules.md](docs/templates-and-rules.md) — using your own spec template
- [docs/validation-report.md](docs/validation-report.md) — what was tested and how
- [examples/](examples/) — an example template with rules, starting configs, a complete sample task

## Development

```bash
cd tests && python3 -m unittest
python3 tools/prepublish_check.py
```

The engine and installer use only the Python standard library.

## License

[MIT](LICENSE)
