# Phase 16 — Forward Deployed Engineering & Production Delivery (target v4.x)

> Renumbered again on 2026-11-22 (D-031, ORE integration): Phase 14 → Phase 16 (feature IDs F14.x → F16.x).

**Status:** Planned (new, strategic integration 2026-11-22). FDE **discovery** starts early: the fde-discovery
profile (Phase 3), business discovery and requirements (Phase 4), and the business-discovery mode (Phase 7). This
phase adds the full FDE mode, PoC discipline, customer delivery and measured business impact.

## Goal

Support the forward deployed engineer's loop: understand the customer's real problem, design for the customer's
environment, prove the idea with the smallest sufficient PoC, integrate, deliver, hand over, and measure whether the
solution achieved its engineering and business goals.

## Scope

`fde` mode (composite of business discovery, scaled system design, PoC, integration, UAT, pilot, delivery, handover,
impact); solution-design extras (build vs buy, legacy and API integration, data sources, quality, mapping, ETL/ELT,
sync, permissions, multi-tenancy, customer configuration vs reusable product capability); PoC records (hypotheses,
success criteria, PoC vs prototype vs MVP vs production-ready); delivery records (environment, integration validation,
UAT, onboarding, pilot, demo, handover, runbooks, incident response, training, ownership); business impact records
(baseline, target, actual, expected vs measured, ROI assumptions, adoption, time saved, cost, feedback).

## Out of scope

Invented ROI or business results; treating a successful demo as production readiness.

## Requirements

1. Expected and measured outcomes are always separated; missing data is shown as unavailable.
2. A PoC states its hypotheses and success criteria before it is built; its result never upgrades a solution to production-ready by itself.
3. Delivery completion needs evidence (UAT results, handover records), not statements.

## Dependencies

Phases 4–8 (discovery, decisions, design, traceability), Phase 9 (audit dimensions incl. customer acceptance), Phase 12 (git/delivery integrations).

## Implementation tasks

| ID | Feature | Pri | Effort | Depends on |
|---|---|---|---|---|
| F16.1.1 | `fde` mode composed from business-discovery, system-design (scaled), PoC, integration, UAT, pilot, delivery, handover, impact stages | P1 | L | F7.1.1, F7.1.3 |
| F16.2.1 | Solution-design extras in the fde profile and records: build vs buy, legacy/API integration, data mapping and quality, ETL/ELT, sync, multi-tenancy, customer configuration vs product capability | P1 | M | F3.2.3 |
| F16.3.1 | PoC records: hypotheses, success criteria, scope, result; PoC / prototype / MVP / production-ready distinction | P1 | M | F2.7.1 |
| F16.4.1 | Delivery records: environment, integration validation, UAT, onboarding, pilot, demo, handover, runbooks, incident response, training, ownership. Include a stakeholder walkthrough showing the proposal is readable and the handover usable; record effort and outcomes as expected vs measured | P1 | L | F16.1.1, F16.5.1 |
| F16.5.1 | Business impact records (`MET`): baseline, target, actual, expected vs measured, ROI assumptions labelled | P1 | M | F2.7.1 |
| F16.6.1 | Eval fixture Scenario E: service-operations AI copilot (discovery, data integration, RAG, tools, human approval, security, tenant isolation, evals, monitoring, deployment, demo, handover, impact) | P1 | M | F9.2.1 |
| F16.7.1 | ORE for forward deployed work: build vs buy with measurable terms, rollout and implementation scheduling, logistics template (ORE-E) | P2 | M | F10.4.3 |

## Acceptance criteria

- AC-1: Scenario E runs end to end in `fde` mode with every stage's evidence recorded.
- AC-2: An outcome without measured data is reported as expected, never as achieved.
- AC-3: A PoC without success criteria cannot be approved.
- AC-4: A stakeholder walkthrough of the proposal and handover is recorded, with customer effort and outcomes as expected vs measured (F16.4.1).

## Testing strategy

Mode tests; record tests; Scenario E eval.

## Risks

Scope breadth; customer data privacy (records must never hold customer secrets — existing secret scanning applies).

## Estimated effort

About 6–8 weeks.

## Migration requirements

None.

## Documentation changes

`docs/fde.md`.

## Rollback plan

Optional mode.

## Completion evidence

Scenario E results, tests, phase review approved by the owner.
