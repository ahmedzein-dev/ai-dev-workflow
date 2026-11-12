---
name: ai-dev-workflow
description: "AIDevWorkflow: structured, spec-driven development with approval gates and persistent cross-agent task records (discovery, dependencies, specification, spec approval, planning, plan approval, implementation, testing, fixing, audit, final report). Use only when the user explicitly invokes ai-dev-workflow by name, for example /ai-dev-workflow or $ai-dev-workflow. Never start it on your own for ordinary coding requests."
license: MIT
compatibility: "Requires git and Python 3.9+. Read by Claude Code, Codex, Gemini CLI, Antigravity and other Agent Skills clients; invocation and limits differ per agent (see docs/compatibility.md in the AIDevWorkflow repository)."
metadata:
  project: AIDevWorkflow
  version: "1.0.0"
disable-model-invocation: true
argument-hint: "[feature request | task name | status | pause <task> | audit <task>]"
hooks:
  PreToolUse:
    - matcher: "Edit|Write|MultiEdit|NotebookEdit"
      hooks:
        - type: command
          command: >-
            for d in "${CLAUDE_SKILL_DIR}" "$CLAUDE_PROJECT_DIR/.claude/skills/ai-dev-workflow" "$HOME/.claude/skills/ai-dev-workflow";
            do if [ -f "$d/scripts/workflow.py" ]; then P=$(command -v python3 || command -v python) || exit 0;
            exec "$P" "$d/scripts/workflow.py" hook claude-pre-edit; fi; done; exit 0
  UserPromptSubmit:
    - hooks:
        - type: command
          command: >-
            for d in "${CLAUDE_SKILL_DIR}" "$CLAUDE_PROJECT_DIR/.claude/skills/ai-dev-workflow" "$HOME/.claude/skills/ai-dev-workflow";
            do if [ -f "$d/scripts/workflow.py" ]; then P=$(command -v python3 || command -v python) || exit 0;
            exec "$P" "$d/scripts/workflow.py" hook claude-prompt; fi; done; exit 0
---

# AIDevWorkflow

Structured AI-Assisted Development — From Requirements to Release.

## Hard rules (they apply for the whole task)

1. **Explicit start only.** Run this workflow only when the user explicitly asked for it: they typed
   `/ai-dev-workflow`, `$ai-dev-workflow`, or asked for AIDevWorkflow / ai-dev-workflow by name. If you loaded this
   skill on your own, stop, create no files, and ask: "Do you want to run this through AIDevWorkflow?" Outside this
   skill, work normally under the project's own instructions.
2. **Never bypass a gate on your own.** In an active workflow task, write no feature code until the plan is approved
   and `preflight` passes in your current session; before then, write only task records under `.ai-dev-workflow/`.
   Reading code and running read-only commands is fine. Do not infer permission to skip stages from urgency, a small
   change, or your own judgment. If the user explicitly asks to skip the spec, an approval, or another stage,
   acknowledge exactly what they are overriding and record their request and the skipped stages with
   `pause <task> --reason "User explicitly requested …; skipped …"` before editing code. Then carry out their
   instruction outside the active workflow without asking them to approve the override again. Leave skipped stages
   and approvals uncompleted; never record an approval they did not give or claim skipped work was verified. If the
   request is unclear, ask what they want rather than treating it as an override. On a later resume, address missing
   stages and gates before claiming workflow completion or editing under the workflow.
3. **Approval comes from the user, never from you.** Record an approval only after the user explicitly approves that
   exact version in their own words ("approve the spec", "plan approved, go ahead"). Questions, "looks good but…",
   discussion, silence, or approval of an earlier version are not approval. Never run `approve` on your own initiative.
4. **Approved documents are frozen.** Never edit `approved/`, `state.json` or `ACTIVE` by hand. Any change to an
   approved spec or plan needs renewed approval: move the task back a stage, edit, show the change, approve again.
5. **Revalidate before touching code in an active workflow task.** At every new session, agent switch, resume, or
   continuation after a pause, run `preflight` before editing feature code under the workflow. If it fails, do not
   edit under the workflow; explain what is wrong and ask.
6. **Never invent.** No invented requirements, API contracts, designs, business rules, architecture, approvals or test
   results. Missing information is a dependency: ask the user, or prepare a backend question, and wait at the gate.
7. **Evidence, or it did not happen.** Claim only checks you actually ran with `run` inside the workflow, or that you
   actually ran and identify outside it after an explicit user override. A check that could not run is Blocked or Not
   Verified, never Passed. A skipped stage is not completed or verified. A workflow final status is never higher than
   what `outcome` allows; do not present overridden work as a completed workflow task.
8. **Preserve other work.** Never revert, overwrite or reformat files outside the approved scope. Files that already had
   uncommitted changes when the task started are not yours. No commits, merges, pushes, deployments or other
   irreversible actions without the user's explicit authorization.
9. **No secrets in records.** Never write credentials, tokens, keys, passwords or personal data into task files;
   refer to them by name.
10. **Follow the project's engineering standards** — the files listed under `standards` in
    `.ai-dev-workflow/config.json` (for example CLAUDE.md or AGENTS.md) — when planning, implementing and auditing,
    whichever agent you are.

## The engine

Every state change goes through the engine that ships with this skill:

```
python3 "<SKILL_DIR>/scripts/workflow.py" <command> <task> [options] --agent <your-name>
```

- `<SKILL_DIR>` is the folder that contains this SKILL.md. In Claude Code it is `${CLAUDE_SKILL_DIR}`.
- Use `python` if `python3` is not available. Run it from inside the project's git repository.
- `--agent` is your name: `claude-code`, `codex`, `gemini-cli`, `antigravity` or `other`.
- In Claude Code, also pass `--session ${CLAUDE_SESSION_ID}` to `new`, `resume` and `preflight`.
- `workflow.py --help` lists the commands. A refusal always says what is missing; fix the cause, never edit records
  to get around it.

## Starting or resuming

The user's request after the invocation is in `$ARGUMENTS` or in their message.

1. Run `status`. If the project has no `.ai-dev-workflow/` folder yet, set it up first with the guided setup in
   [references/project-setup.md](references/project-setup.md): run `init --discover`, present its recommendations
   (template, checks, how task records are saved in git) in plain language with their trade-offs, and let the user
   accept them or change any item; then run `init` with what they confirmed. A recommendation is not a choice: never
   run `init` before the user confirms, never pick a template on their behalf, and never invent one. If the project
   is already set up, reuse its settings and ask nothing, unless `init --discover` reports a problem or the user asks
   for a change (`init --update`).
2. If the request names an existing task, or the user wants to continue one, run `resume <task>` and continue from its
   stage. If several tasks could match, ask which.
3. Otherwise create a task: choose a short kebab-case name and a type (`feature`, `bugfix`, `enhancement`,
   `refactor`), then run
   `new <task> --title "…" --type <type> --invocation "<the user's starting message, verbatim>"`.
4. Read the project's standards files and `.ai-dev-workflow/PROJECT.md` before planning, implementing or auditing.
5. Work through the stages below. After every stage change, `status <task>` prints the next step and the reference
   file for that stage; read it, because long sessions lose earlier context.

## Stages

| # | Stage | What you do | It ends when |
|---|---|---|---|
| 1 | DISCOVERY | Understand the request; inspect the code, related features and standards; ask only what the code cannot answer; `discover --inspected … --summary …` | inspected files and a summary are recorded |
| 2 | DEPENDENCIES | Classify every external input in `dependencies.md`; ask for designs; prepare ready-to-send backend messages | every dependency is classified |
| 3 | SPECIFICATION | Fill `spec.md` from the project's template; `spec-check`; fix; record the review with `review` | no mandatory violation, no open flag, review recorded |
| 4 | SPEC_APPROVAL | Present the spec and wait; then `approve <task> spec --evidence "<their words>"` | the user's approval is recorded (moves to PLANNING) |
| 5 | PLANNING | Inspect the code to change; write `plan.md`; `plan-check` | the plan is complete |
| 6 | PLAN_APPROVAL | Present the plan and wait; then `approve <task> plan --evidence "<their words>"` | the user's approval is recorded (moves to IMPLEMENTATION) |
| 7 | IMPLEMENTATION | `preflight`; implement the approved steps in order; `step <task> S<n> done` after each | every step is done |
| 8 | TESTING | `run` each required check; fill the acceptance matrix in `verification.md` | checks ran on the current code and nothing failed |
| 9 | FIXING | `preflight`; fix root causes; return to TESTING and re-run | re-tested |
| 10 | AUDIT | Review the real changes and evidence, independently where possible; record findings in `audit.md` | every finding is Fixed, Accepted by the user, or Deferred (Minor) |
| 11 | FINAL_REPORT | `outcome`; write `report.md`; `close` | report complete, status allowed |

Move between stages with `stage <task> <STAGE>`; the engine refuses a move whose prerequisites are missing. Going back
is always allowed with `--reason`. Stage details:
[discovery-and-dependencies](references/discovery-and-dependencies.md) ·
[specification](references/specification.md) ·
[planning-and-implementation](references/planning-and-implementation.md) ·
[testing-and-fixing](references/testing-and-fixing.md) ·
[audit-and-report](references/audit-and-report.md) ·
gates, resuming and handoff: [lifecycle](references/lifecycle.md).

Scale the depth to the task: a small fix gets a short spec and plan, a large feature gets as much detail as it needs.
The gates are the same for every active workflow task; an explicit user override is recorded by pausing, not by
advancing stages or inventing approvals.

## Presenting for approval

Show the version and the first 8 characters of its hash (from `status` or `spec-check`), a short summary, the
`spec-check` or `plan-check` result including advisory warnings, and any decisions or questions that need the user.
Then ask plainly, for example: "Reply 'approve the spec' to approve spec v2 (3f9a1c0e), or tell me what to change."
Record the approval with their words as `--evidence`. If the user approves with conditions or asks for changes, edit,
re-check and present again.

**Fast path for small changes.** You may draft `plan.md` while the spec awaits approval and present both together. If
the user explicitly approves both in one message, record the spec approval, move to PLAN_APPROVAL after `plan-check`,
and record the plan approval with the same words. Both approvals are still required; nothing else is skipped.

## Pausing and unrelated requests

If the user asks for something unrelated while a task is active, pause the task first (`pause <task>`) and tell
them; then work normally. Resume later with the skill and `resume <task>`, followed by `preflight` before code edits.
A closed or paused task places no limits on your edits.

## Switching agents

All state lives in `.ai-dev-workflow/tasks/<task>/`. A different agent invokes the skill, runs `resume <task>`, reads the
records, checks `git status` and `scope`, and runs `preflight` before touching code. Never rely on chat history from
another session; the records and the code are the source of truth.

## Reporting

Keep the user informed without noise: report when a gate needs them (a question, a backend message, a spec or plan
to approve, a scope change, a blocker) and at the end. Blocked work starts with a status line such as
`BLOCKED — Awaiting backend API contract`, followed by what is missing, why it matters, who must provide it, and
what happens next. The final message is a one-minute summary of `report.md`; distinguish what was verified from
what was not.
