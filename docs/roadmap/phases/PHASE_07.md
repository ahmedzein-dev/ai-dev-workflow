# Phase 7 — Workflow Modes, System Design & Diagrams (target v2.0.0)

> Numbering history (2026-11-22): Phase 6 (brief 2 integration, D-020) → Phase 7 (ORE integration, D-031).

**Status:** Planned (new, strategic integration 2026-11-22).

## Goal

Support system design as a goal of its own, plus architecture reviews and business discovery, each with its own
deliverables and completion criteria; produce HLD, LLD, capacity estimates, failure analysis and editable diagrams
that stay linked to decisions and requirements.

## Scope

Modes `system-design`, `architecture-review`, `business-discovery`, `full`; components (`CMP`) and HLD documents; LLD
documents (modules, interfaces, domain models, schema, API and event contracts, state machines, algorithms,
validation, error and concurrency handling, transaction boundaries, patterns); capacity estimates recomputed by the
engine; failure analysis with test mapping; distributed-systems analysis with a "justify the complexity" rule;
Mermaid diagrams with states, versions, hashes, linting and staleness; optional renderers.

## Out of scope

The FDE mode and delivery (Phase 16); architecture drift over time (Phase 13); dashboard viewer (Phase 11).

## Existing capabilities to keep

Feature mode unchanged; hash-bound approvals; depth policy.

## Requirements

1. Each mode has its own stages, gates, deliverables and completion criteria; not writing code in system-design mode is
   success, not a gap.
2. HLD and LLD are separate documents; architecture-level decisions are not mixed with internal details.
3. Capacity estimates show inputs (confirmed / assumed / measured), formulas and outputs; the engine recomputes them.
4. Distributed-systems mechanisms (replication, sharding, consensus, sagas, outbox, idempotency, retries, DLQ,
   backpressure, circuit breakers, rate limiting) appear only with the problem they solve and why the complexity is justified.
5. Failure scenarios state handling and how it will be tested.
6. Diagrams: editable text source in git; states as-is / proposed / approved / implemented; no invented components;
   linked to ADRs and requirements; versioned; flagged stale when linked records change; syntax-validated when tooling exists.

## Dependencies

Phase 2 (gate table, approvals), Phase 3 (profiles, depth), Phase 4 (requirements), Phase 5 (ADRs, decision sets).

## Technical decisions (proposed)

D-024 modes, D-027 diagrams (Mermaid first). Details: [ENGINEERING_INTELLIGENCE.md §6, §10](../ENGINEERING_INTELLIGENCE.md).

## Implementation tasks

| ID | Feature | Pri | Effort | Depends on |
|---|---|---|---|---|
| E7.1 | **Modes** | | | |
| F7.1.1 | `system-design` mode: requirements baseline → decision sets → HLD → LLD → diagrams → design approval → design review → report | P0 | L | F2.1.1, E5.1 |
| F7.1.2 | `architecture-review` mode: as-is discovery → analysis → findings → options → review approval → report | P1 | M | F7.1.1 |
| F7.1.3 | `business-discovery` mode: stakeholders → workflows → objectives & metrics → solution options → proposal approval | P1 | M | E4.2 |
| F7.1.4 | `full` development mode: feature mode with discovery and design stages switched on by depth | P1 | M | F7.1.1 |
| E7.2 | **System design artifacts** | | | |
| F7.2.1 | Components (`CMP`) and HLD structure: context, style, components, boundaries, data ownership, communication, data flow, integrations, storage, scalability, availability, security boundaries, deployment, major failures | P0 | M | F2.7.1 |
| F7.2.2 | LLD documents: modules, interfaces, models, schema, API/event contracts, state machines, algorithms, validation, errors, concurrency, transactions, patterns | P0 | M | F7.2.1 |
| F7.2.3 | Capacity estimates (`EST`) with safe engine recomputation and confirmed/assumed/measured inputs | P1 | M | F2.7.1 |
| F7.2.4 | Failure analysis records (database, network, service, duplicates, partial failure, races, timeouts, data loss, external APIs, payments, overload, disaster recovery) mapped to tests | P1 | M | F7.2.1 |
| F7.2.5 | Distributed-systems guidance in the profile with the justify-complexity rule | P1 | S | F3.2.3 |
| E7.3 | **Diagrams** | | | |
| F7.3.1 | Diagram registry (`DGM`), Mermaid source, states, versions, hashes, links to `CMP`/`ADR`/`REQ` | P0 | M | F2.7.1 |
| F7.3.2 | Lint: supported type, referenced components exist, linked decisions current, staleness flags | P0 | M | F7.3.1 |
| F7.3.3 | Optional syntax validation with Mermaid CLI when installed | P2 | S | F7.3.1 |
| F7.3.4 | Diagrams embedded in spec and plan; as-is vs proposed vs approved vs implemented | P1 | S | F7.3.1 |
| F7.3.5 | Optional renderers and exports: PlantUML, Structurizr DSL, SVG/PNG, interactive HTML | P2 | M | F7.3.1 |
| E7.4 | **Validation** | | | |
| F7.4.1 | Eval fixtures: Scenario C (high scale: estimates, consistency trade-offs, no unjustified distribution), D (frontend rendering/SEO/performance), B design part (ERD, sequence diagram, duplicate-booking tests) | P1 | M | E7.1–E7.3 |

## Acceptance criteria

- AC-1: A system-design task finishes with an approved design package and no code, and is reported as complete.
- AC-2: A capacity estimate with an arithmetic error in the document is flagged by recomputation.
- AC-3: A diagram referencing a non-existent component fails lint; a diagram linked to a superseded ADR is flagged stale.
- AC-4: Scenario C does not propose a distributed architecture without a recorded justification.
- AC-5: Existing feature-mode tasks behave exactly as before (golden and scenario tests).

## Testing strategy

Mode transition tests per mode; estimate recomputation tests; diagram lint tests; eval checks for C, D, B (design).

## Risks

Over-design (mitigated by depth and the justify-complexity rule); diagram drift (lint + staleness); record format
changes readable by v1 engines (major version, migration).

## Estimated effort

About 7–9 weeks.

## Migration requirements

Task state gains `mode` (existing tasks → `feature`); records written in new modes need v2 engines (major version).

## Documentation changes

`docs/modes.md`, `docs/system-design.md`, `docs/diagrams.md`, guide sections.

## Rollback plan

New modes are opt-in; feature mode unchanged; v1.x stays installable.

## Completion evidence

Tests, eval results, phase review approved by the owner, v2.0.0 release checklist.
