# Phase 10 — ORE Advanced: Multi-objective, Scenarios, Certificates & Applications (target v2.3.0)

**Status:** Planned (new, ORE integration 2026-11-22, D-031). Covers brief 3's ORE phases 6–8 and the model-selection
part of phase 9. Design: [ore/ORE_DESIGN.md](../ore/ORE_DESIGN.md), [ore/STRICT_OPTIMALITY_POLICY.md](../ore/STRICT_OPTIMALITY_POLICY.md).

## Goal

Extend ORE to the trade-offs and what-if questions engineers and businesses actually ask, add problem classes only
together with matching proofs, and apply ORE to system design, planning, booking, pricing and AI model selection —
always conditional on documented data.

## Scope

Pareto analysis (exact epsilon-constraint, frontier completeness labels), approved weighted sums; scenarios,
sensitivity, thresholds, break-even, robustness with approved ranges, reconsideration triggers; continuous LP with an
exact dual-certificate check; an optional second exact solver for cross-checks; model calibration against
measurements; application templates and scenarios ORE-B, C, D, F, H.

## Out of scope

Nonlinear global optimization and stochastic optimization as proven results (research only); agent allocation
(Phase 14); logistics in production FDE settings (Phase 16).

## Requirements

1. A frontier is called complete only when proven; partial frontiers say so.
2. No weights unless the user approved them.
3. Scenario results each carry their own classification and the inputs they depend on.
4. New problem classes ship only with a verifier that can meet the stated guarantee level.
5. AI model selection uses task-specific eval results with sample size; optimality is relative to candidates and sample.
6. Calibration flags decisions for re-evaluation when measured values deviate beyond the stated threshold.
7. ORE advanced features stay context-sensitive: offered only when the fit gate holds, and explained in plain language before the mathematical detail (PRODUCT_EXPERIENCE §3).

## Dependencies

Phase 6 (ORE foundations), Phase 7 (design artifacts, capacity estimates), Phase 8 (traceability), Phase 9 (evals,
performance registry).

## Implementation tasks

| ID | Feature | Pri | Effort | Depends on |
|---|---|---|---|---|
| E10.1 | **Multi-objective** | | | |
| F10.1.1 | Pareto via exact epsilon-constraint; complete vs partial frontier labels; approved weighted sums; trade-off reporting | P1 | L | F6.3.2 |
| E10.2 | **Scenarios and sensitivity** | | | |
| F10.2.1 | What-if scenarios, thresholds, break-even, robustness with approved ranges, reconsideration triggers | P1 | L | F6.5.1 |
| E10.3 | **Problem classes and certificates** | | | |
| F10.3.1 | Continuous LP through an optional float solver, verified by an exact dual certificate (G3) | P1 | L | F6.2.1 |
| F10.3.2 | Optional second exact solver cross-check for small and medium integer models | P2 | M | F6.2.1 |
| F10.3.3 | Model calibration: measured values vs model parameters, re-evaluation flags | P1 | M | F6.5.1, F8.3.3 |
| E10.4 | **Applications (templates and scenarios)** | | | |
| F10.4.1 | System design, cloud and database capacity templates (ORE-B, ORE-C) | P1 | M | F7.2.3 |
| F10.4.2 | Booking allocation template (ORE-D) | P1 | M | F6.1.5 |
| F10.4.3 | MVP planning, resource allocation and project scheduling templates | P1 | M | F6.1.5 |
| F10.4.4 | Pricing and business templates with demand-model provenance rules | P2 | M | F6.1.5 |
| F10.4.5 | AI model selection template from task-specific evals (ORE-F) | P1 | M | F9.3.2 |
| F10.4.6 | Cost vs performance Pareto scenario (ORE-H) | P1 | S | F10.1.1 |

## Acceptance criteria

- AC-1: ORE-H returns a frontier marked complete only when every epsilon step was proven.
- AC-2: ORE-F reports the chosen model or routing with sample sizes, versions and dates; changing a price makes it stale.
- AC-3: A continuous LP result is `PROVEN_OPTIMAL` only after the exact dual certificate passes; otherwise `FEASIBLE_NOT_PROVEN`.
- AC-4: A calibration deviation flags the linked ADR for re-evaluation.

## Testing strategy

Frontiers checked against enumerated frontiers on small problems; certificate checker tests with constructed
primal–dual pairs (valid and invalid); scenario tests B, C, D, F, H.

## Risks

R-22, R-23, R-26 (data quality for applications).

## Estimated effort

About 8–10 weeks.

## Migration requirements

New optional template files; no change to existing records.

## Documentation changes

`docs/ore/` multi-objective, scenarios, applications, model selection.

## Rollback plan

Each capability optional per model.

## Completion evidence

Scenario results, tests, phase review approved by the owner.
