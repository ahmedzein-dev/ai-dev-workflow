# Phase 2 — Core Engine: Records, Modes, Approvals, Security & Recovery (target release v1.2.0)

**Status:** Planned. Part of the original Phase 2 (module split, migration, locking) moved to Phase 1 · E1.0 (D-001).
Strategic integration (2026-11-22, D-020): this phase also builds the core the engineering-intelligence phases need —
the project-level engineering record store, approvals for any document type including decision sets, and a gate
table with per-mode stage sets. It stays before Phases 3–9 because decisions and designs need the same integrity as
specs and plans.

## Goal

Strengthen the guarantees and reduce reliance on the agent following text instructions, while staying honest about
what can be prevented and what can only be detected.

## Scope

Declarative gate table; additional enforcement layers (git hook, CI recipe, more agent hooks where vendors support
scoped hooks); approval channels and trust levels A0/A1 (A2/A3 optional); tamper-evident event log; corruption
recovery; evidence v2; a safe process runner; threat model; local trust store for check commands; security tests.

## Out of scope

Sandboxing or isolated execution environments (documented guidance only); the dashboard approval UI (P3); signed
approvals as a default.

## Existing capabilities to keep

Claude hook behaviour (scoped, fail-open outside, fail-closed inside), preflight, `scope`, unattributed-change
detection, secret refusal, fingerprints, outcome caps, the override-by-pause rule.

## Requirements

1. No new restriction affects agents outside an active workflow task (INV-03).
2. Every mechanism is labelled as prevention or detection in the docs.
3. Existing approvals (A0) stay valid; new levels are opt-in per project.
4. Check commands run by the engine must match a block the user confirmed on this machine.
5. Evidence records enough context to tell when and where it was produced.

## Dependencies

Phase 1 E1.0 (package, API, state store). D-008 approval trust levels.

## Technical decisions (proposed)

D-008. New: event-log format (JSON Lines, SHA-256 chain); trust store location (`~/.ai-dev-workflow/trust.json`,
keyed by repository root and remote URL); signature tool (`ssh-keygen -Y sign/verify`, as used by git).

## Proposed architecture

See [TARGET_ARCHITECTURE.md §4.4–4.6](../TARGET_ARCHITECTURE.md).

## Implementation tasks

| ID | Feature | Pri | Effort | Depends on |
|---|---|---|---|---|
| E2.1 | **Core structure** | | | |
| F2.1.1 | Declarative gate table with per-mode stage sets (only `feature` defined here), replacing the `forward_problems` chain; identical behaviour proven by the scenario and golden tests | P0 | M | E1.0 |
| F2.1.2 | In-process event system (emit on stage, approval, check, step) feeding the event log and later analytics | P1 | S | F2.1.1 |
| E2.2 | **Enforcement layers** | | | |
| F2.2.1 | Optional git pre-commit hook: `install-hook` / `uninstall-hook`; no-op without an active task; blocks commits of code changes made outside IMPLEMENTATION/FIXING | P1 | M | E1.0 |
| F2.2.2 | CI recipe: GitHub Actions workflow running `check` and `outcome` on task records, failing on inconsistencies | P1 | S | F2.4.1 |
| F2.2.3 | Agent hooks review: native Windows Claude hook (TD-18); scoped hooks for other agents only where the vendor offers them, otherwise documented as not available | P1 | M | — |
| F2.2.4 | Scope warning: changed files outside the plan's Affected Areas are listed for the audit | P2 | M | E1.4 |
| E2.3 | **Approval channels** | | | |
| F2.3.1 | Approval `channel` and identity fields; A1 user CLI approval with version, hash and diff against the previous snapshot | P0 | M | E1.0 |
| F2.3.2 | A2/A3 signed approval receipts and verification in `check` and CI | P2 | M | F2.3.1 |
| F2.3.3 | Minimum trust level per gate in project policy | P2 | S | F2.3.1 |
| E2.4 | **Checkpoint and recovery** | | | |
| F2.4.1 | `events.jsonl` append-only log with a hash chain; `check` verifies it; history migrated on next write | P0 | M | F2.1.2 |
| F2.4.2 | Corruption detection and guided recovery (from git history or migration backups) | P1 | M | F2.4.1 |
| E2.5 | **Evidence integrity** | | | |
| F2.5.1 | Evidence v2: HEAD commit, OS, tool versions (from adapters), output SHA-256, optional redacted log file | P0 | M | E1.2 |
| F2.5.2 | Process runner: new process group/session, kill the group on timeout, stream output to a temp file (TD-11, TD-12) | P0 | M | E1.0 |
| F2.5.3 | Documented staleness rules; optional component-scoped staleness | P2 | S | F2.5.1 |
| E2.6 | **Security** | | | |
| F2.6.1 | Threat model document (assets, actors, entry points, prevented vs detected) | P0 | M | — |
| F2.6.2 | Local trust store for check commands (confirm on first use and after any change) | P0 | M | E1.0 |
| F2.6.3 | Security test suite: forged approval, edited state, broken chain, stale-evidence replay, unconfirmed command, path traversal, ReDoS limits | P0 | M | E2.3–E2.6 |
| E2.7 | **Engineering record store** (strategic integration) | | | |
| F2.7.1 | Project-level record store in `.ai-dev-workflow/engineering/`: typed records with IDs (`OBJ`, `REQ`, `CON`, `ASM`, `Q`, `ADR`, `CMP`, `DGM`, `EST`, `RES`, `MET`), `refs` links, schema, migration | P0 | M | E1.0 |
| F2.7.2 | Generic hash-bound approvals for any approvable document (decisions, requirement baselines, design packages) and **decision-set** approvals (one user approval covering a listed set, each item hashed) | P0 | M | F2.7.1, F2.3.1 |
| F2.7.3 | Reference index and trace-graph core (who references what), consistency checks for dangling IDs in `check` | P0 | S | F2.7.1 |

## Acceptance criteria

- AC-1: Attempts to skip stages, forge approvals, edit state, run unconfirmed commands or reuse stale evidence are
  refused or detected, with tests for each (the brief's Phase 2 criterion).
- AC-2: All v1.x records and tests keep working; new mechanisms default off where they add friction.
- AC-3: A timed-out check with child processes leaves no running processes and returns within the timeout plus a
  small margin.
- AC-4: The threat model states, for each threat, whether it is prevented, detected or only reduced.

## Testing strategy

Unit tests per mechanism; adversarial scenario tests; process-runner tests on all three operating systems; migration
tests from v1.1 records.

## Risks

R-12, R-14, R-16; S-01 to S-12 in the risk register. Main residual risk: an agent with the user's permissions can
still do anything the user can (documented, not hidden).

## Estimated effort

About 5–7 weeks.

## Migration requirements

M4 (evidence v2, event log) — automatic on the next write of an active task, with backup; closed tasks untouched.

## Documentation changes

New `docs/security.md` (threat model), updates to `README.md` ("What is enforced"), `docs/usage.md` (approval
channels), `docs/configuration.md` (trust store, hooks), compatibility report.

## Rollback plan

Each mechanism behind configuration; downgrade keeps working with v1.1 records via backups.

## Completion evidence

Security test results, CI runs, phase review approved by the owner, v1.2.0 release checklist.
