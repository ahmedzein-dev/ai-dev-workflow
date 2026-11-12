# Usage

## Starting a task

Invoke the skill explicitly with your request:

| Agent | Example |
|---|---|
| Claude Code | `/ai-dev-workflow Add saved favorites to the item list` |
| Codex | `$ai-dev-workflow Add saved favorites to the item list`, or choose `ai-dev-workflow` in `/skills` |
| Codex (non-interactive) | `codex exec '$ai-dev-workflow Add saved favorites to the item list'` — single quotes, so the shell does not expand `$ai` |
| Gemini CLI | `/ai-dev-workflow Add saved favorites to the item list` |
| Antigravity | `/ai-dev-workflow Add saved favorites to the item list` |

[compatibility.md](compatibility.md) lists which of these were tested on which versions, and fallbacks.

An ordinary request such as "add saved favorites" does not start the workflow. If an agent loads the skill on its
own, the skill tells it to stop and ask you first.

## First run in a project

The agent runs `workflow.py init --discover` and shows you:

- the instruction files it found (CLAUDE.md, AGENTS.md, GEMINI.md, …) — confirm which ones are the engineering
  standards every agent must follow;
- specification templates found in the repository and in your private library — choose one, or provide one;
  the agent never invents a template;
- suggested checks based on the project's tooling — confirm or adjust;
- whether task records are committed: `all`, `config-only` or `none`.

Then it runs `workflow.py init`, which creates `.ai-dev-workflow/`. Nothing else in the repository changes.

## What happens next

1. **Discovery** — the agent reads the relevant code and asks only what the code cannot answer.
2. **Dependencies** — it lists what it needs from outside (designs, API contracts, decisions). For a missing
   backend contract it writes a message you can forward, then waits: `BLOCKED — Awaiting backend API contract`.
3. **Specification** — it fills your template, checks it (`spec-check`), and shows you the result.
4. **Spec approval** — it asks, for example: *Reply "approve the spec" to approve spec v1 (3f9a1c0e), or tell me
   what to change.*
5. **Planning** — it inspects the code it will change and writes the plan: goal, current behavior, proposed
   solution, affected areas, steps, decisions, edge cases, testing, risks, expected result.
6. **Plan approval** — the same explicit approval, bound to the plan's hash.
7. **Implementation** — only now does it edit code, after `preflight`, one approved step at a time.
8. **Testing and fixing** — it runs the project's checks through the engine and fills the acceptance matrix; failures
   go to Fixing and back.
9. **Audit** — a review of the real changes against the spec, plan and your standards, independent where possible.
10. **Final report** — a one-minute summary, with a status no higher than the evidence allows.

## Approving

Approve in plain words that refer to the document: "approve the spec", "plan approved, go ahead". These are recorded
verbatim with the version's hash. Questions, "looks good but…", or silence are not approvals. If you change your
mind later, any edit to the approved file requires a new approval.

## Changing scope

If the agent discovers during implementation that the approved spec or plan is wrong or incomplete, it stops,
explains the impact, moves the task back, and asks for your approval of the updated document.

## Pausing and doing something else

Say "pause the task" (or ask for something unrelated — the agent pauses first). A paused task places no limits on
any agent. Resume with the skill and the task name: `/ai-dev-workflow saved-favorites`.

## Switching agents

Start in one agent and continue in another:

1. In the second agent, invoke the skill with the task name (`$ai-dev-workflow saved-favorites`).
2. It runs `resume`, reads the records, checks `git status` and the task's scope, and runs `preflight` before any
   code edit. Approvals are re-validated against the frozen snapshots, so nothing is taken on trust.

For an independent audit, implement in one agent and audit in another: `$ai-dev-workflow audit saved-favorites`.

## Where things are

```
.ai-dev-workflow/tasks/saved-favorites/
├── spec.md            your template, filled in
├── dependencies.md    what was needed from outside, backend messages, answers
├── plan.md            the implementation plan (frozen once approved)
├── approved/          read-only snapshots of every approved version
├── state.json         stage, approvals, progress, evidence, history (only the engine writes it)
├── verification.md    recorded checks and the acceptance matrix
├── audit.md           findings and how each was resolved
└── report.md          the final report
```

[examples/sample-task](../examples/sample-task) contains a complete, finished example.

## Commands

You rarely need to run the engine yourself; the agent does. For reference:

```bash
python3 ~/.agents/skills/ai-dev-workflow/scripts/workflow.py status            # list tasks
python3 ~/.agents/skills/ai-dev-workflow/scripts/workflow.py status <task>     # one task, with the next step
python3 ~/.agents/skills/ai-dev-workflow/scripts/workflow.py check             # validate all records
python3 ~/.agents/skills/ai-dev-workflow/scripts/workflow.py outcome <task>    # highest status the evidence allows
python3 ~/.agents/skills/ai-dev-workflow/scripts/workflow.py --help
```
