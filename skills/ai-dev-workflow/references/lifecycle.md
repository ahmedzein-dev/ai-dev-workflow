# Lifecycle, gates and handoff

The workflow has 11 stages. `workflow.py` stores the stage in `state.json` and refuses any move whose
prerequisites are missing. Blockers (unresolved Blocking dependencies) are tracked separately and can hold a task at
any stage.

```
DISCOVERY → DEPENDENCIES → SPECIFICATION → SPEC_APPROVAL → PLANNING → PLAN_APPROVAL
          → IMPLEMENTATION → TESTING ⇄ FIXING → AUDIT → FINAL_REPORT → closed
```

## Moving forward

| Into | Requires |
|---|---|
| DEPENDENCIES | inspected files and a discovery summary recorded (`discover`) |
| SPECIFICATION | every dependency classified in `dependencies.md` (or "No dependencies identified — <reason>"); each Blocking backend dependency has a ready-to-send message |
| SPEC_APPROVAL | `spec-check`: no mandatory violation, no open review flag, every judgment rule reviewed for this spec version; no Blocking dependency with gate `spec` |
| PLANNING | only via `approve <task> spec` after the user's explicit approval |
| PLAN_APPROVAL | valid spec approval; `plan-check` passes; no Blocking dependency with gate `spec` or `plan` |
| IMPLEMENTATION | only via `approve <task> plan`; no Blocking dependency with gate `implementation` |
| TESTING | valid approvals; every approved plan step marked done |
| FIXING | a reason (what failed) |
| AUDIT | every required check ran on the current code and none failed; the acceptance matrix covers every AC, EC and checklist item; no item Failed |
| FINAL_REPORT | from AUDIT: audit complete, no finding Open. From any earlier stage: a reason (the report will be Partially Completed or Blocked) |
| closed | `close`: `report.md` complete and its status no higher than `outcome` allows |

Forward moves are one stage at a time, except TESTING → AUDIT (FIXING is only for failures).

## Moving back

Always allowed with `--reason`. Typical cases:

- **Scope change or wrong assumption found during implementation**: stop coding, explain the discovery and its
  impact, move back to SPECIFICATION or PLANNING, update the document, present it, and get renewed approval.
- **A new dependency appears**: move back to DEPENDENCIES and classify it.
- **Tests fail or an audit finding needs a code change**: TESTING → FIXING, AUDIT → FIXING, then FIXING → TESTING.

Moving back never deletes approvals; they simply stop being valid once the document changes.

## Approvals and versions

- `approve` works only in SPEC_APPROVAL or PLAN_APPROVAL, only when the checks pass, and only with `--evidence`
  quoting the user. It stores the version, a SHA-256 of the document (line endings normalized), the user's words, the
  recording agent and the time, and writes a read-only snapshot `approved/<doc>.v<N>.md`.
- After approval, `spec.md` and `plan.md` must not change. Any change, however small, makes the hash differ from the
  snapshot: the approval is invalid, code edits are blocked, and the user must approve the new version. Show them the
  difference against the snapshot.
- A plan approval is tied to the approved spec's hash. A new spec version invalidates the plan approval as well.
- Progress lives in `state.json` (`step`), never in the plan file, so marking steps done keeps the plan's hash.
- The engine cannot prove a human typed the approval: it records the evidence you give it. Never record an approval
  the user did not give. If you cannot establish that an approval is genuine — for example after switching agents the
  evidence looks wrong — ask the user to confirm again.

## Blockers

A Blocking dependency names the gate it stops (`spec`, `plan`, `implementation`, `completion`). Until it is resolved
(Class changed to Verified, with the evidence in its section), the engine refuses that gate. Drafting can continue
around it: a spec can be written while the backend answer is pending, but not approved. `status` shows
`BLOCKED — Awaiting <summary> (<owner>)`.

## Resuming

When you resume a task (`resume <task>`), act on its stage:

| Stage | What to do |
|---|---|
| DISCOVERY, DEPENDENCIES | Continue discovery; if waiting for answers, check whether the user brought them |
| SPECIFICATION | Continue the spec from where the records stand |
| SPEC_APPROVAL, PLAN_APPROVAL | Present the document again and wait; do not start the next stage |
| IMPLEMENTATION, FIXING | Run `preflight`; inspect what is actually implemented (`scope`, the code, step progress) before continuing |
| TESTING | Re-run checks that are stale or failed; continue the matrix |
| AUDIT | Perform or continue the audit |
| FINAL_REPORT | Finish the report and close |
| closed | Explain the outcome; do not redo work |

Records are not proof that the code still matches them. `preflight`, `status` and `check` compare hashes, evidence
fingerprints and the working tree; investigate every mismatch they report before relying on the records.

## Cross-agent handoff

Before you stop working on a task (end of session, switching agents), make sure the records show the current stage,
what is done (steps), what remains, blockers, pending decisions, verification status and known risks. `status <task>`
must tell the next agent what to do. Use `decision` to record decisions the user made in chat.

The next agent invokes the skill, runs `resume <task>`, reads `spec.md`, `plan.md`, `dependencies.md` and the
latest evidence, checks `git status` and `scope`, and runs `preflight` before any code edit.

## Preflight

Run `preflight <task>` at the start of every session that will edit code, after switching agents, after `resume`, and
after a pause. It checks the state file, both approvals against their snapshots, the stage, blocking dependencies and
secrets in records, and lists changes since the last checkpoint that no recorded step explains. If it fails, do not
edit code. In Claude Code the skill's hook also blocks edits until preflight has passed in the current session; other
agents rely on you following this rule, and later `workflow.py` commands report changes made outside it.

## Several tasks and several people

One task is active per working copy (`ACTIVE`, not committed). Starting or resuming another task pauses the previous
one. For parallel work use separate git worktrees. `scope` separates the task's changes from changes that existed
before it; never overwrite or revert work you did not do. If unexpected changes appear, ask the user before
attributing them (`scope --exclude <files> --reason …` once they confirm a file is unrelated).

## Command reference

| Command | Purpose |
|---|---|
| `init --discover` / `init …` | Inspect and then set up a project (after asking the user) |
| `new <task> --title --type --invocation` | Create a task, only after an explicit invocation |
| `status [<task>]` | List tasks, or show one with its next step |
| `resume <task>` / `pause <task>` | Make a task active for this session / stop its gates |
| `discover <task> --inspected … --summary …` | Record discovery |
| `spec-check <task>` / `review <task> …` | Validate the spec / record the judgment review, coverage and flag dismissals |
| `plan-check <task>` | Validate the plan |
| `approve <task> spec|plan --evidence "…"` | Record the user's explicit approval |
| `stage <task> <STAGE> [--reason]` | Change stage |
| `preflight <task>` | Revalidate before editing code |
| `step <task> S<n> done` | Record progress on an approved step |
| `run <task> <check> [-- args]` | Run a check and record evidence; `--baseline`, `--blocked`, `--not-applicable` |
| `scope <task>` | The task's changes vs. pre-existing work |
| `decision <task> --text --evidence` | Record a user decision |
| `check [<task>]` | Validate all records |
| `outcome <task>` / `close <task>` | Highest allowed status / close the task |
