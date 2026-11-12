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

The agent inspects the project (`workflow.py init --discover`) and proposes a setup in one short message:

- **Instruction files** it found (CLAUDE.md, AGENTS.md, …) — the standards every agent follows.
- **Specification template** — your default template, if you registered one (`install.py add-template … --default`).
  Without a default it tells you so and lists what it found, or asks you for one; it never picks an example for you.
- **Checks** — commands found from your project's own files (for example `flutter analyze` and `flutter test` from
  pubspec.yaml and test/, scripts from package.json, pytest or ruff from their configuration), each with a one-line
  explanation, plus the commands your CI already runs. You don't need to know them in advance.
- **Saving task records in git** — what `all`, `config-only` and `none` actually do: what is committed, whether a
  clone or another computer can resume a task, what is lost if your computer is, and who can read the records. It
  recommends one, with the reason and the trade-off.

Accept everything, or change any item. Then it runs `workflow.py init`, which creates `.ai-dev-workflow/` and records
both the recommendations and your choices. Nothing else in the repository changes, and later tasks reuse these
settings without asking again. To change one later, ask the agent (`init --update`).

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
any agent. Resume with the skill and the task name: `/ai-dev-workflow saved-favorites`. In Claude Code, do this
also after resuming a session (`claude --resume`): the skill's edit gate is active only once the skill is invoked in
that session.

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
