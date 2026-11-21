# Phase 18 — Team Collaboration & Commercial Product (study only)

> Numbering history (2026-11-22): brief-1 Phase 9 → Phase 16 (brief 2 integration, D-020) → Phase 18 (ORE integration, D-031); feature IDs follow the phase number.

**Status:** Future. Starts only after the local system and multi-agent architecture are stable (brief): after v4. No code
in this phase without a separate approval.

## Goal

Prepare an architecture and a product/licensing strategy for teams and organisations without affecting individual
users or forcing paid services on anyone.

## Scope

Studies: team workspaces, shared projects and knowledge, assignments, team policies, approval responsibilities,
RBAC, multiple approvers, activity history, central audit logs, organisation policies, SSO, self-hosted deployment,
optional sync, privacy controls; product editions (Community / Pro / Enterprise as a proposal); licensing (open
core, separation of MIT core and commercial components, contribution policy).

## Out of scope

Building commercial features, subscriptions or hosted services in this phase.

## Requirements

1. The MIT core remains MIT; nothing is re-licensed implicitly (INV-16).
2. Individual local use never requires an account or a paid service (INV-13, INV-14).
3. The study states technical, product and licensing trade-offs before any commercial build.

## Dependencies

Stable v4 (local system + multi-agent, Phase 14). Contribution policy (DCO, D-013) can be adopted earlier.

## Implementation tasks

| ID | Feature | Pri | Effort |
|---|---|---|---|
| F18.1.1 | Technical study: team model, RBAC, multiple approvers, sync options (git-based first), self-hosted design | P2 | M |
| F18.2.1 | Product study: editions, pricing hypotheses, what stays Community | P2 | M |
| F18.3.1 | Licensing study: open-core separation, repository layout, DCO vs CLA, trademark | P2 | S |

## Acceptance criteria

A clear architecture for teams and organisations exists that does not affect the individual user or force paid
services (brief).

## Risks

R-09 licensing ambiguity; premature commercial work diverting effort from the core.

## Estimated effort

About 2–3 weeks of study.

## Migration requirements

None.

## Documentation changes

Study documents under `docs/roadmap/studies/`.

## Rollback plan

Not applicable (no code).

## Completion evidence

Approved study documents.
