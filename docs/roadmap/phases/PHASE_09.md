# Phase 9 — Engineering Audit, Verification & Evals (target v2.2.0)

> Numbering history (2026-11-22): Phase 8 (brief 2 integration, D-020) → Phase 9 (ORE integration, D-031).

**Status:** Planned (new, strategic integration 2026-11-22). Eval fixtures start earlier (Phases 3–7); this phase
builds the harness and the extended audit.

## Goal

Verify more than code: business alignment, requirement coverage, architecture and decision compliance, data and
transaction safety, failure recovery, diagram accuracy, operational readiness and customer acceptance — and measure
the quality of the system's questions, recommendations and decisions with scenario evals.

## Scope

Audit dimensions as data selected by mode, depth and profile; separating documentation completeness, design
correctness, implementation correctness and measured results; architecture drift checks (implemented vs approved);
the eval harness with scenarios A–I, deterministic checks, a human rubric and an optional model-graded rubric.

## Out of scope

Claiming automatic proof of semantic engineering quality (the engine never claims it).

## Existing capabilities to keep

Audit independence levels, severity × disposition rules, outcome caps.

## Requirements

1. The existence of a diagram, ADR or test file is never treated as evidence of quality.
2. Audit reports separate: documentation complete, design sound, implementation correct, results measured.
3. Evals record agent, model and version; results labelled like the compatibility report (tested / not run).
4. Model-graded evals are optional and need explicit consent for their cost.

## Dependencies

Phases 3–8 (records to audit); Phase 2 (evidence v2).

## Implementation tasks

| ID | Feature | Pri | Effort | Depends on |
|---|---|---|---|---|
| E9.1 | **Engineering audit** | | | |
| F9.1.1 | Audit dimensions as data by mode, depth and profile (business alignment, requirement coverage, architecture and decision compliance, data correctness, transaction safety, security, performance, scalability, failure recovery, API contracts, integration, maintainability, test quality, diagram accuracy, deployment and operational readiness, customer acceptance) | P0 | M | F3.1.1 |
| F9.1.2 | Audit and outcome distinguish documentation completeness, design correctness, implementation correctness and measured results | P0 | M | F9.1.1 |
| F9.1.3 | Architecture drift check: implemented code paths vs approved components and diagrams | P1 | M | F7.2.1 |
| E9.2 | **Evals** | | | |
| F9.2.1 | Eval harness: scenario fixtures A–I, deterministic record checks, results registry with agent/model/version | P0 | L | F3.4.1, F5.6.1 |
| F9.2.2 | Human rubric workflow (relevance, missing considerations, trade-off quality, sycophancy) | P1 | S | F9.2.1 |
| F9.2.3 | Optional model-graded rubric with cost consent | P2 | M | F9.2.1 |
| E9.3 | **Agent and model performance registry** (ORE integration) | | | |
| F9.3.1 | Registry per agent, model, version and task category: success, coverage, test success, findings, rework, time; tokens and cost only when reported; context, tools, privacy and rate limits; every value labelled measured / expected / unavailable; normalised by task category and size | P1 | M | F2.4.1, F9.2.1 |
| F9.3.2 | Task-specific model eval sets built from the user's own samples, with versions, dates and sample sizes | P1 | M | F9.2.1 |

## Acceptance criteria

- AC-1: All nine scenarios (A–I) run through the harness with deterministic checks; results are recorded per agent and model.
- AC-2: An audit of a fixture with a diagram that contradicts an approved ADR reports it.
- AC-3: A task with complete documents but failing measured targets cannot report "Completed".

## Testing strategy

Harness self-tests with recorded runs; audit dimension tests.

## Risks

Eval cost and flakiness (deterministic checks first; model grading optional); overfitting instructions to scenarios.

## Estimated effort

About 5–6 weeks.

## Migration requirements

Audit template gains optional dimensions; existing audits stay valid.

## Documentation changes

`docs/evals.md`, audit reference, validation report sections.

## Rollback plan

Dimensions configurable; evals are a separate tool.

## Completion evidence

Eval results table, tests, phase review approved by the owner.
