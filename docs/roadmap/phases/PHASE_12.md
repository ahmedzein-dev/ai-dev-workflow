# Phase 12 — Git, GitHub Integration & Parallel Development (target v3.x)

> Numbering history (2026-11-22): brief-1 Phase 4 → Phase 10 (brief 2 integration, D-020) → Phase 12 (ORE integration, D-031); feature IDs follow the phase number.

**Status:** Planned (outline; tasks are detailed when the phase starts — rolling-wave planning).

## Goal

Support real development flows: tasks bound to branches, safe parallel tasks in one repository, conflict warnings,
and GitHub issues and pull requests, without ever committing, pushing or merging on its own.

## Scope

Optional branch binding; per-task diff and change ownership; worktree-based parallel tasks; a task registry across
worktrees; file-overlap conflict detection; heuristic migration/API-contract conflict warnings; a git-host provider
interface with a `gh` CLI provider (issues in, PRs out, status checks).

## Out of scope

Automatic commits, pushes, merges or deployments; storing tokens; GitLab/Bitbucket providers (the interface
allows them later); semantic conflict detection claims.

## Existing capabilities to keep

Baselines, change sets, pre-existing work protection, `scope --exclude`, one active task per checkout.

## Requirements

1. No commit, push, merge or deployment without explicit permission (INV-11).
2. Each parallel task has its own workspace, state, scope and evidence; corrupting one cannot affect another.
3. Conflict detection states its method (file overlap, migration naming, contract files) and its limits.
4. Issue text imported from GitHub is quoted as data, never followed as instructions (S-06).
5. Nothing private (specs, records, secrets) is sent to GitHub without explicit permission per action.

## Dependencies

Phase 1 E1.0, Phase 2 F2.4 (locking, event log), Phase 11 F11.1 (CLI) recommended. D-017.

## Implementation tasks

| ID | Feature | Pri | Effort |
|---|---|---|---|
| E12.1 | **Git integration** | | |
| F12.1.1 | Optional branch binding per task (`new --branch`, checks in preflight) | P1 | S |
| F12.1.2 | Per-task diff export and change ownership per step | P1 | M |
| E12.2 | **Parallel tasks** | | |
| F12.2.1 | Worktree management per task (create, list, remove) with a records strategy for each commit mode; study of alternatives recorded first | P0 | L |
| F12.2.2 | Cross-worktree task registry and locking | P0 | M |
| E12.3 | **Conflict detection** | | |
| F12.3.1 | File overlap between active tasks (approved Affected Areas and actual changes) | P0 | S |
| F12.3.2 | Heuristics for migration ordering and API contract files (OpenAPI, protobuf, GraphQL schemas), labelled as heuristics | P2 | M |
| E12.4 | **GitHub** | | |
| F12.4.1 | Provider interface + `gh` CLI provider (auth stays in `gh`) | P1 | M |
| F12.4.2 | Import an issue as task input (quoted, with link) | P1 | S |
| F12.4.3 | Create a pull request after explicit permission, with report summary, acceptance criteria, test results and audit findings chosen by the user | P1 | M |
| F12.4.4 | Optional status check from `check` + `outcome` in CI; guidance for branch protection | P2 | M |

## Acceptance criteria

Two parallel tasks run without corrupting each other's state or losing user changes; overlapping files are reported;
a test task is linked to a test pull request (brief).

## Testing strategy

Integration tests with real git worktrees in temporary repositories; provider tests against a fake `gh`; one manual
run against a test GitHub repository, recorded in the validation report.

## Risks

Worktree records strategy differs per commit mode (R-02); `gh` version differences (R-04); accidental publication
of private records (S-08) — mitigated by explicit per-action consent and previews.

## Estimated effort

About 5–7 weeks.

## Migration requirements

Task state gains optional `branch`, `worktree`, `links` fields (schema bump handled by the Phase 1 migration framework).

## Documentation changes

`docs/parallel-work.md`, `docs/github.md`, usage and compatibility updates.

## Rollback plan

All features opt-in; tasks without branch/worktree bindings behave as in v1.x.

## Completion evidence

Integration test results, recorded manual PR test, phase review approved by the owner.
