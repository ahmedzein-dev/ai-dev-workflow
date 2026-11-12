# Compatibility

What works in each agent, how we know, and what is still unverified. Results come from the vendors' documentation,
from inspecting the installed agents, and from live runs in a throwaway repository
([validation-report.md](validation-report.md)).

**Evidence labels**

| Label | Meaning |
|---|---|
| **Tested** | We ran it ourselves on the version shown |
| **Checked in installed version** | Found in the installed agent's code or CLI, not run end to end |
| **Vendor docs** | Documented by the vendor; not run by us |
| **Unverified** | Neither |

Only **Tested** items are described as confirmed.

## Summary

| | Claude Code | Codex | Gemini CLI | Antigravity (app / IDE) | Antigravity CLI |
|---|---|---|---|---|---|
| Version examined | 2.1.263 | 0.166.0-alpha.6 (bundled with the ChatGPT app) | 0.53.1 | app 2.2.1, IDE 2.1.1 | not installed |
| User-level folder | `~/.claude/skills/` | `~/.agents/skills/` | `~/.agents/skills/` (alias of `~/.gemini/skills/`) | `~/.gemini/config/skills/` | `~/.gemini/config/skills/` (also `~/.gemini/antigravity-cli/skills/`, `~/.gemini/skills/`) |
| Project folder | `.claude/skills/` | `.agents/skills/` | `.agents/skills/` or `.gemini/skills/` (trusted folders only) | `.agents/skills/` | `.agents/skills/` |
| Start it | `/ai-dev-workflow …` | `$ai-dev-workflow …`, or pick it in `/skills` | `/ai-dev-workflow …`, or "Use the ai-dev-workflow skill to …" | `/ai-dev-workflow …` (app) | `/ai-dev-workflow …` |
| Stops self-activation | `disable-model-invocation: true` | `allow_implicit_invocation: false` | no setting; consent prompt per activation | not documented | not documented |
| Gates | skill hooks + engine | instructions + engine | instructions + engine | instructions + engine | instructions + engine |

## Claude Code

| Item | Evidence |
|---|---|
| Reads `~/.claude/skills` and `.claude/skills`; follows a symlinked skill folder | Vendor docs; `.claude/skills` **Checked in installed version** (2.1.263) |
| Does not read `~/.agents/skills` (hence the installer's link or copy) | Not in the docs and not referenced by the 2.1.263 binary |
| `disable-model-invocation: true`: the description never enters Claude's context; only `/ai-dev-workflow` starts it | Vendor docs; key **Checked in installed version** |
| `${CLAUDE_SKILL_DIR}` and `${CLAUDE_SESSION_ID}` substitution in SKILL.md | Vendor docs; `CLAUDE_SKILL_DIR` **Checked in installed version** |
| `/ai-dev-workflow …` starts it; `.ai-dev-workflow/ACTIVE` holds the real session id | **Tested** (2.1.263) |
| A plain request did not start it and created no task files | **Tested** (one run) |
| Skill-scoped hooks register on invocation; with the skill invoked, an edit to `app.py` before approval was denied with the AIDevWorkflow reason, and edits went through after approval and `preflight` | **Tested** (2.1.263) |
| Hooks do not carry over to a resumed session (`claude --resume`, a new process): an edit there went through until `/ai-dev-workflow <task>` was typed again | **Tested** (2.1.263) |
| A full task end to end: approvals recorded in the user's words, implementation, `unit` check, independent subagent review, report, closed as Completed | **Tested** (2.1.263) |

Limits: hooks see Claude's edit tools, not shell commands that write files. Hooks live only in the Claude process
where the skill was invoked: after resuming a session, type `/ai-dev-workflow <task>` again before continuing.

## Codex

| Item | Evidence |
|---|---|
| Discovers the skill in the repository's `.agents/skills/` | **Tested** (0.166.0-alpha.6) |
| `$ai-dev-workflow …` starts it, including non-interactively: `codex exec '$ai-dev-workflow …'` (single quotes so the shell does not expand `$ai`) | **Tested** |
| With `allow_implicit_invocation: false`, a plain request did not start it and created no task files | **Tested** (one run) |
| Followed the gates on its own: discovery, dependencies, spec, review, then stopped at SPEC_APPROVAL asking "Reply 'approve the spec'" | **Tested** |
| Refused approvals it could not establish as genuine (asked the user to reconfirm) | **Tested** |
| When explicitly asked to skip gates, it wrote code in all three runs without fabricating approvals. One run paused the task first; acknowledgment and a recorded reason were not established in every run. `status` and `check` flagged changes before approval. See the [validation report](validation-report.md) for the override criteria. | **Tested** |
| With the updated skill in Codex 0.167.0-alpha.4.1, one live code-edit run acknowledged an explicit override, recorded `pause --reason` before editing, and reported skipped stages as incomplete. The state remained PAUSED at DISCOVERY with no approvals or outcome. | **Tested** (one edit run; see [validation report](validation-report.md)) |
| Picking it in the `/skills` list | Vendor docs; setting **Checked in installed version**; the TUI could not be scripted — manual check below |

Limits: no skill-scoped hooks exist in Codex and project-wide hooks are deliberately not used, so the gates depend on
the instructions, with `workflow.py` detecting deviations afterwards. In the `workspace-write` sandbox, commands that
write outside the repository (package caches, SDKs) may need approval; such checks are recorded as blocked.

## Gemini CLI

| Item | Evidence |
|---|---|
| Discovers the skill in `~/.agents/skills/` and in a trusted project's `.agents/skills/`; accepts the Claude-only frontmatter keys | **Tested** (0.53.1) |
| `/ai-dev-workflow …` — the slash command Gemini creates for each skill — starts it, also non-interactively (`gemini -p`) | **Tested**: the skill created the task; the run then stopped on the account's free-tier quota |
| "Use the ai-dev-workflow skill to …" starts it | **Tested** (same quota note) |
| A plain request did not start it | **Tested** (one run) |
| Resumed a task created by Codex | **Tested**: the resume was recorded, then the quota ran out |
| A consent prompt appears when the model activates a skill on its own | Vendor docs; not exercised (headless runs allowed activation explicitly) |
| Fallback: "Read `<skill folder>/SKILL.md` and follow it for …" (add `--include-directories <skill folder>` when it is outside the project) | **Unverified** |
| A complete task in Gemini CLI | **Not run**: the free-tier daily quota (20 requests) ran out mid-run |

Limits: no manual-only setting exists; project-level skills load only in trusted folders (`--skip-trust` trusts the
folder for one session); non-interactive runs must allow the tools they need. Our runs used
`--approval-mode auto_edit --allowed-tools activate_skill --allowed-tools "run_shell_command(python3)"` (plus `git`
and `ls`), not `yolo`.

Account note: since 2026-06-18 Gemini CLI serves only paid Gemini API keys and Gemini Code Assist Standard/Enterprise
licences; Google AI Pro/Ultra and free individual accounts moved to Antigravity CLI.

## Antigravity

| Item | Evidence |
|---|---|
| Workspace skills in `.agents/skills/`, global skills in `~/.gemini/config/skills/` | Vendor docs |
| App: each skill becomes a `/<skill-name>` command; IDE: no explicit syntax documented | Vendor docs |
| Manual-only: not documented. The installed app's skill loader reads a `disable-model-invocation` key (found in app 2.2.1), but its effect is unknown | **Unverified** |
| Symlinked skill folders | **Unverified** (the installer falls back to a copy if a link fails) |
| Antigravity CLI | Vendor docs only; not installed here |

## Other Agent Skills clients

Cursor, GitHub Copilot / VS Code, OpenCode, Amp, Goose and other clients that implement the
[Agent Skills](https://agentskills.io) format should load the skill from their skills folder or the project's
`.agents/skills/`. **Unverified.** Where an agent cannot be made manual-only, the skill's first rule tells it to stop
and ask, and `workflow.py new` refuses to create a task without the user's invoking message.

## Manual checks

These need a person at the keyboard (or a login we did not have). Each takes a few minutes in a scratch repository
with the skill installed.

**Claude Code** (all five steps were run on 2.1.263; repeat them on a new version)
1. `/ai-dev-workflow Add a whisper(text) function to app.py` → a task appears in `.ai-dev-workflow/tasks/`, and
   `.ai-dev-workflow/ACTIVE` contains a real session id (not `${CLAUDE_SESSION_ID}`).
2. Ask it to edit `app.py` before the plan is approved → the edit is blocked with an AIDevWorkflow reason.
3. Approve spec and plan, let it run `preflight` → code edits now go through.
4. `pause` the task, then ask for an unrelated edit → it goes through.
5. A plain "add a whisper function" in a new session → no task files.

**Codex `/skills` list**: open `codex`, type `/skills`, check that `ai-dev-workflow` is listed, select it with a
request → a task is created.

**Gemini CLI consent prompt** (interactive, default approval mode): start Gemini, ask it to "use the
ai-dev-workflow skill" → a consent prompt names the skill and its folder.

**Antigravity app**: install with `install.py --agents antigravity`, open a project, type `/ai-dev-workflow …` → it
starts. Then ask an ordinary coding question → note whether it ever starts the skill on its own (this tells you whether
`disable-model-invocation` is honored).

## Platforms

Linux and macOS: symlinks work; the installer uses them for Claude Code and Antigravity. Windows: symlinks need
Developer Mode or administrator rights; the installer falls back to copies and `doctor` watches them for drift. Cloud
agents only see the repository: use the project-level install (real copies). The CI workflow runs the test suite on
macOS, Linux and Windows once the repository is published; until then only macOS was tested.
