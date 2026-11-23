# Phase 17 — Engineering Analytics & Business Impact (basic: v3.x · full: v5.x)

> Numbering history (2026-11-22): brief-1 Phase 8 → Phase 15 (brief 2 integration, D-020) → Phase 17 (ORE integration, D-031); feature IDs follow the phase number.

**Status:** Planned (outline). Basic task metrics can ship with the dashboard because the data already exists in
task history.

## Goal

Measure the quality and performance of the development process from real execution data, never from estimates
presented as facts.

## Scope

Task metrics (durations per stage, approval waiting time, revisions, failed checks, findings, fixing cycles, scope
changes, reopened tasks, completion status); agent metrics (successes, failures, findings, rework, time; tokens and
cost only when reported by the agent); quality metrics (requirement and AC coverage, test coverage when available,
regressions, churn, trends); dashboard views and export.

## Out of scope

Off-device telemetry without explicit opt-in; invented token counts or costs; rankings of agents by task count alone.

## Existing capabilities to keep

`history` events with timestamps, agents and stages; outcome computation.

## Requirements

1. Every number traces back to recorded events or check results.
2. Missing data is shown as "Unavailable", never estimated silently.
3. Comparisons between agents account for task size and complexity (or are not shown).
4. Export to CSV/JSON; any off-device telemetry is opt-in with clear consent.

## Dependencies

Phase 2 (event log), Phase 11 (dashboard), Phase 14 (agent usage data, where available), Phase 16 (outcome records).
F17.6.1 uses the Phase 1 usability baseline and F17.1.1 event-derived task metrics; basic measures can ship in
v3.x, while richer views follow when their source data exists. Unavailable values remain labelled.

## Implementation tasks

| ID | Feature | Pri | Effort |
|---|---|---|---|
| F17.1.1 | Task metrics computed from events (CLI + dashboard) | P1 | M |
| F17.2.1 | Agent metrics with availability flags | P2 | M |
| F17.3.1 | Engineering quality metrics (coverage from parsers, churn from git) | P2 | M |
| F17.4.1 | Analytics views by task, project, agent, technology, period; report export | P2 | L |
| F17.5.1 | Business impact view from outcome records (baseline, target, actual; expected vs measured; ROI assumptions labelled) | P2 | M |
| F17.6.1 | Product-experience metrics (PRODUCT_EXPERIENCE §6) from events and explicitly labelled study data, with measured / estimated / assumed / unavailable flags and baseline vs current; no fabricated values | P1 | M |

At the detailed specifications, re-evaluate whether F17.6.1's baseline and experience measures remain distinct
from F17.1.1's event-derived task metrics. Keep both IDs until that evidence-based review.

## Acceptance criteria

Results trace to real execution data; reports can be exported; unavailable data is never claimed (brief).

Product-experience metrics show baseline vs current with an availability flag on every value (F17.6.1).

## Testing strategy

Metric calculations tested on synthetic event logs with known answers.

## Risks

Misleading metrics; privacy if telemetry is added.

## Estimated effort

Basic ≈ 1–2 weeks; full ≈ 4–6 weeks.

## Migration requirements

None.

## Documentation changes

`docs/metrics.md` with definitions of every metric.

## Rollback plan

Read-only feature; removable without effect on records.

## Completion evidence

Metric tests, sample reports, phase review approved by the owner.
