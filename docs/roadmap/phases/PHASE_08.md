# Phase 8 — Intelligent Specifications, Planning & End-to-End Traceability (target v2.1.0)

> Numbering history (2026-11-22): Phase 7 (brief 2 integration, D-020) → Phase 8 (ORE integration, D-031).

**Status:** Planned (new, strategic integration 2026-11-22).

## Goal

Make specs architecture-, domain- and business-aware without forcing one template, make plans derive from approved
decisions and designs, and make the whole chain traceable from business objective to delivery outcome.

## Scope

Profile-suggested spec sections and companion documents; spec quality measured by requirement coverage; extended plan
sections scaled by depth; plan consistency checks against decisions, HLD and LLD; the reopen-decision protocol;
`trace` queries (why, impact, coverage); a generated requirements traceability matrix with a gaps report; links from
code changes and delivery outcomes.

## Out of scope

Deep code-level impact analysis (Phase 13); dashboard explorer (Phase 11).

## Existing capabilities to keep

Custom spec templates and rules files (never replaced or silently changed); `review --map` coverage; step-to-file
attribution; acceptance matrix.

## Requirements

1. The user's template stays authoritative; if it lacks a section the task needs, the agent proposes adding it or a
   companion document — never edits the template without approval.
2. Spec quality = coverage of real requirements, not section count or length.
3. Plans state strategy, architecture impact, affected components, API and database changes, data migration,
   dependency order, steps, testing, failure handling, security, performance validation, observability, deployment,
   rollback and documentation — as far as the depth requires.
4. A plan inconsistent with approved decisions or designs cannot be approved; changing an important decision during
   planning or implementation reopens it with impact analysis and approvals.
5. The system can answer: why was X chosen, which requirements led to it, what is affected if it changes, which tests
   prove a requirement, is the implementation consistent with the approved architecture, were all criteria met.

## Dependencies

Phases 4–7.

## Implementation tasks

| ID | Feature | Pri | Effort | Depends on |
|---|---|---|---|---|
| E8.1 | **Specifications** | | | |
| F8.1.1 | Profile-suggested spec sections; companion documents when the template lacks a needed section | P0 | M | F3.1.1 |
| F8.1.2 | Spec quality by requirement coverage (`REQ` ↔ AC / tests / edge cases) | P0 | S | F4.3.1 |
| E8.2 | **Planning** | | | |
| F8.2.1 | Extended plan sections scaled by depth (custom plan templates allowed) | P0 | M | F3.3.2 |
| F8.2.2 | Plan consistency checks against approved decisions, HLD and LLD (cited IDs current and approved) | P0 | M | F5.3.1, F7.2.1 |
| F8.2.3 | Reopen-decision protocol during planning and implementation | P1 | S | F5.3.2 |
| E8.3 | **Traceability** | | | |
| F8.3.1 | `trace why|impact|coverage <ID>` over the reference graph | P0 | M | F2.7.3 |
| F8.3.2 | Generated RTM (`OBJ → REQ → CON → ADR → CMP → spec → plan → code → evidence → finding → outcome`) and gaps report | P0 | M | F8.3.1 |
| F8.3.3 | Links from code changes (steps, commits when available) and delivery outcomes (`MET`) | P1 | S | F8.3.1 |

## Acceptance criteria

- AC-1: `trace why ADR-4` lists the requirements, constraints and objectives behind it; `trace impact REQ-7` lists affected decisions, components, plans and tests.
- AC-2: The RTM for a fixture project has no unexplained gaps; a requirement without verification shows up in the gaps report.
- AC-3: A plan citing a superseded decision is refused.
- AC-4: A template missing a security section gets a proposed companion document, and the template file is unchanged.

## Testing strategy

Graph and RTM tests on fixtures; plan consistency tests; regression tests for custom templates.

## Risks

Traceability overhead (IDs only where useful, as the brief says); false confidence from links (audit checks content).

## Estimated effort

About 5–6 weeks.

## Migration requirements

Plan template gains optional sections; existing plans stay valid.

## Documentation changes

`docs/traceability.md`, specification and planning references.

## Rollback plan

Checks configurable; traceability is additive.

## Completion evidence

Tests, RTM sample, phase review approved by the owner.
