# Phase 13 — Project Intelligence & Architecture Evolution (target v3.x)

> Numbering history (2026-11-22): brief-1 Phase 5 → Phase 11 (brief 2 integration, D-020) → Phase 13 (ORE integration, D-031); feature IDs follow the phase number.

**Status:** Planned (outline; detailed at phase start).

> Scope change (2026-11-22): ADRs moved to Phase 5 and the record store to Phase 2; this phase builds the
> cumulative project knowledge and architecture evolution on top of them.

## Goal

Let the system understand a project cumulatively, so each new task starts from verified knowledge instead of
rediscovering everything, and produce reviewable impact reports before plan approval.

## Scope

Project knowledge store with sources; deterministic architecture map from components and dependency graphs; ADRs
linked to tasks and files; impact report at PLANNING; post-task knowledge update with staleness detection; task
context packs.

## Out of scope

Vector databases or embeddings unless a measured need appears (brief); treating AI-generated statements as facts
without evidence.

## Existing capabilities to keep

`PROJECT.md`, standards files, `discover --inspected`, per-task decisions, components from Phase 1.

## Requirements

1. Every knowledge entry cites its sources (files with content hashes, docs, decisions) and its status
   (verified / proposed / stale).
2. ADRs proposed by an agent stay Proposed until the user approves them where approval is needed.
3. Impact reports separate confirmed, likely and unknown impact.
4. Knowledge becomes stale automatically when its source files change.

## Dependencies

Phase 1 (components, adapters), Phase 2 (events, record store), Phase 5 (ADRs), Phase 7 (components, diagrams), Phase 11 (views, optional).

## Implementation tasks

| ID | Feature | Pri | Effort |
|---|---|---|---|
| F13.1.1 | Knowledge entries on top of the engineering record store (Phase 2 E2.7): architecture overview, modules, APIs, schema, auth, shared components, conventions, limitations, business rules — each with source hashes | P1 | M |
| F13.1.2 | Architecture map: components, internal dependency graph from manifests and imports (adapter-provided extractors) | P1 | L |
| F13.2.1 | Architecture evolution timeline: ADR and diagram history, as-is / approved / implemented over time, drift between approved and implemented architecture (ADRs themselves moved to Phase 5) | P1 | M |
| F13.3.1 | Deep, code-level impact report at PLANNING (basic record-level impact queries arrive in Phase 8): modules, shared components, API consumers, schema/migrations, auth, permissions, performance, compatibility, security, tests, infrastructure | P1 | L |
| F13.4.1 | Post-task update: changed knowledge, new ADRs, stale entries flagged by hash | P2 | M |
| F13.5.1 | Task context pack: relevant files and knowledge for the agent, from metadata and the dependency graph | P2 | M |

## Acceptance criteria

A new task reuses knowledge from an earlier task; knowledge is flagged stale after the code changes; an impact
report can be reviewed and is attached to the plan (brief).

## Testing strategy

Fixture projects with known dependency graphs; staleness tests by editing source files; review of report quality
recorded in the validation report.

## Risks

Low-quality or outdated knowledge misleading agents (mitigated by sources + staleness); scope growth toward
"code intelligence" products.

## Estimated effort

About 6–8 weeks.

## Migration requirements

New optional folder; no change to existing records.

## Documentation changes

`docs/project-knowledge.md`, `docs/adr.md`, references for the PLANNING stage.

## Rollback plan

Feature folder can be ignored; tasks work without it.

## Completion evidence

Fixture results, sample impact reports, phase review approved by the owner.
