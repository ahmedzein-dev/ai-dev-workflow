# Phase 6 — ORE Foundations: Modeling, Exact Solving & Strict Optimality (target v1.6.0)

**Status:** Planned (new, ORE integration 2026-11-22, D-031). Covers brief 3's ORE phases 0–5 for the problem
classes that can be proven in version 1. Design: [ore/ORE_DESIGN.md](../ore/ORE_DESIGN.md).

## Goal

Add an optional engine that turns approved, modelable decisions into mathematical models, solves them within resource
limits, verifies results independently and classifies them strictly, so that **no result is called optimal without
proof** — and that refuses to model what cannot be modelled honestly.

## Scope

Research spike on candidate solvers; the `ore/1` model schema with exact numbers, units and provenance; validation and
plain-language rendering; model approval; problem templates (data); solver adapter contract and registry; a built-in
exact enumerator (standard library); one optional solver adapter chosen by the spike; the four-dimension status model
and engine-computed classification; exact verification and guarantee levels; resource-limited execution; run evidence,
staleness and ADR integration; lexicographic objectives; scenario tests.

## Out of scope

Continuous, nonlinear and stochastic models; Pareto frontiers; sensitivity and scenarios; domain application templates
beyond feature selection (all Phase 10); agent/model allocation (Phase 14); dashboard views (Phase 11).

## Existing capabilities to keep

The skill stays standard-library only and usable without ORE; engine gates, approvals, record store, trust store,
process runner and event log (Phase 2) are reused, not duplicated.

## Requirements

1. ORE is an optional module; the skill never imports it unless a task uses it.
2. Models are declarative data; nothing in a model is executed.
3. Unknown data blocks solving; estimates are allowed only when labelled, and results built on them say so.
4. Hard constraints are never relaxed; soft constraints need approved weights or become objectives.
5. Resource limits apply from the first solver run.
6. Only the verifier sets classifications; strict mode is the default; `PROVEN_OPTIMAL` requires the policy's guarantee level.
7. A model must be approved by the engineer (hash-bound) before its result can support a decision.
8. Adding a domain is a template, never an ORE code change.

## Dependencies

Phase 2 (record store, approvals, trust store, process runner, event log), Phase 4 (questions, requirements,
constraints), Phase 5 (ADRs, decision sets). D-032–D-038.

## Implementation tasks

| ID | Feature | Pri | Effort | Depends on |
|---|---|---|---|---|
| E6.0 | **Research and feasibility** | | | |
| F6.0.1 | Desk study: solver comparison from official sources (SOLVER_COMPARISON.md; done in Phase 0 as F0.4.2) | P0 | S | — |
| F6.0.2 | Hands-on spike: candidate solvers in a throwaway virtual environment, run scenarios ORE-A/I/J/K/L, confirm guarantees, status mapping and resource controls; decision record | P0 | M | F6.0.1 |
| E6.1 | **Mathematical model foundation** | | | |
| F6.1.1 | `ore/1` JSON Schema, allow-listed expression AST, safe parser | P0 | M | F2.7.1 |
| F6.1.2 | Exact numbers (fractions), units algebra, data provenance classes | P0 | M | F6.1.1 |
| F6.1.3 | Validation pipeline and model statuses (invalid, insufficient data, unsupported, not modelable, numerical uncertainty) | P0 | M | F6.1.2 |
| F6.1.4 | Plain-language rendering and hash-bound model approval | P0 | M | F6.1.3, F2.7.2 |
| F6.1.5 | Problem templates as data; first template: feature selection | P0 | S | F6.1.1 |
| E6.2 | **Solver foundation** | | | |
| F6.2.1 | Adapter contract (capability declarations) and registry with policy matching | P0 | M | F6.1.3 |
| F6.2.2 | Built-in exact enumerator (standard library) with exact search-space pre-check | P0 | M | F6.2.1 |
| F6.2.3 | First optional adapter chosen by the spike, opt-in install recorded in the trust store | P1 | M | F6.0.2, F2.6.2 |
| E6.3 | **Strict optimality and verification** | | | |
| F6.3.1 | Status model (model, termination, solution, verification) and verifier-computed classification | P0 | M | F6.2.1 |
| F6.3.2 | Exact re-verification of feasibility and objective; guarantee levels G0–G3; default policy | P0 | M | F6.3.1 |
| F6.3.3 | Infeasibility explanations where the adapter provides them | P1 | S | F6.3.1 |
| E6.4 | **Resource safety** | | | |
| F6.4.1 | Execution controller: separate process, time, memory and thread limits, cancellation, termination reasons | P0 | M | F2.5.2 |
| E6.5 | **Evidence and decisions** | | | |
| F6.5.1 | Run evidence records, fingerprints (model, data, solver), staleness | P0 | M | F6.3.2, F2.4.1 |
| F6.5.2 | ADR integration (ORE result as decision evidence) and optimization topics in profiles and discovery | P0 | M | E5.1, F3.2.1 |
| F6.5.3 | Lexicographic objectives | P1 | S | F6.3.2 |
| E6.6 | **Validation and documentation** | | | |
| F6.6.1 | Scenarios ORE-A, I, J, K (tolerance stub), L, M; property tests (enumerator vs optional adapter); security tests O-01–O-10 | P0 | M | E6.1–E6.5 |
| F6.6.2 | User documentation `docs/ore/` (overview, schema, strict policy, limits, known limitations) | P0 | M | all |

## Acceptance criteria

- AC-1: ORE-A: a feature-selection model is approved, solved by the enumerator, verified and classified `PROVEN_OPTIMAL` (G3), with estimated inputs labelled.
- AC-2: ORE-I: contradictory constraints → `PROVEN_INFEASIBLE`; no constraint ignored.
- AC-3: ORE-J: a problem beyond the limits stops safely; no optimality claim; the termination reason is kept.
- AC-4: ORE-K: a tolerance-only (G1) answer is never classified `PROVEN_OPTIMAL` in strict mode.
- AC-5: ORE-L: missing data → `INSUFFICIENT_DATA`; no invented values.
- AC-6: ORE-M: a new domain template works without ORE code changes.
- AC-7: An agent cannot record a classification; a fake solver result fails verification.
- AC-8: The skill and all existing tests work with ORE not installed.

## Testing strategy

Unit tests per module; enumerator cross-checks; property tests; failure and security suites; scenario tests; CI on
three operating systems (optional-solver jobs separate from the standard-library jobs).

## Risks

R-22 optimization theatre, R-23 solver guarantee misunderstanding, R-24 dependency weight, R-25 hard instances.

## Estimated effort

About 7–9 weeks (spike included).

## Migration requirements

New record family (`OPT`) in the record store; no change to existing records.

## Documentation changes

`docs/ore/*`, profile optimization topics, decisions reference.

## Rollback plan

ORE is optional and isolated; uninstalling it leaves the workflow unchanged.

## Completion evidence

Scenario and security test results, spike decision record, phase review approved by the owner.
