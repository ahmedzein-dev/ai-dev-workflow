# Phase 4 — Business Discovery, Requirements & Adaptive Questioning (target v1.4.0) · MVP

**Status:** Planned (new, strategic integration 2026-11-22).

## Goal

Understand the real problem before proposing architecture or code: business and technical context, objectives and
success metrics, functional requirements and measurable non-functional requirements, with questions asked only when
the code and records cannot answer them.

## Scope

Question-and-answer ledger with engine commands; `questions next` batching; derived answers with sources; structured
contradiction detection; objectives with success metrics; requirement records (functional and non-functional) with
measurable targets; constraints and assumptions with review triggers; requirement-baseline approval; discovery in
feature mode scaled by depth; the unknown-answer protocol.

## Out of scope

Separate discovery modes (`business-discovery`, `fde`: Phases 7 and 16); dashboard question answering (Phase 11).

## Existing capabilities to keep

Discovery stage (`discover --inspected --summary`), dependency classification with gates, ready-to-send backend
messages, the rule "ask only what the code cannot answer".

## Requirements

1. Derive before asking; derived answers cite file and line and can be corrected by the user.
2. Questions carry type (requirement, preference, constraint, assumption, decision), impact, the gate that needs them,
   and why they matter; asked in related batches ordered by impact on the next decisions.
3. No question is asked twice unless its key's circumstances changed.
4. Unknown answers: explain why it matters, give options with effects and a recommendation; the user picks, assumes or defers.
5. Only high-impact questions needed by the next gate block it; everything else proceeds with recorded assumptions.
6. NFRs become measurable targets (latency, throughput, availability, RPO, RTO, budget) when relevant; proposed values
   show their basis; nothing is invented or treated as approved without the user.
7. The ledger lets any agent continue the discussion.

## Dependencies

Phase 2 (record store, generic approvals), Phase 3 (profiles provide question banks; depth scales discovery).

## Technical decisions (proposed)

D-021 record model (questions JSONL + views), D-022 approval types (requirement baseline).

## Implementation tasks

| ID | Feature | Pri | Effort | Depends on | MVP |
|---|---|---|---|---|---|
| E4.1 | **Question ledger** | | | | |
| F4.1.1 | `questions.jsonl` + commands `ask`, `answer`, `derive`, `assume`, `defer` + generated `questions.md` view | P0 | M | F2.7.1 | ✔ |
| F4.1.2 | `questions next`: open, needed by the next gate, highest impact, grouped, excluding answered/deferred keys | P0 | M | F4.1.1, F3.1.2 | ✔ |
| F4.1.3 | Structured contradiction detection; re-ask triggers when a related record changes | P1 | S | F4.1.1 | |
| E4.2 | **Business context** | | | | |
| F4.2.1 | Objectives (`OBJ`) with stakeholders, success metrics (baseline, target, expected/measured), MVP vs future scope, failure impact | P0 | M | F2.7.1 | ✔ |
| F4.2.2 | Business and technical context topics in the generic profile; instructions for discovery interviews | P0 | M | F3.2.1 | ✔ |
| E4.3 | **Requirements engineering** | | | | |
| F4.3.1 | Requirement records (`REQ`, functional / non-functional, priority, source, verification refs) | P0 | M | F2.7.1 | ✔ |
| F4.3.2 | Measurable NFR targets with proposed values, basis and status (proposed / approved) | P0 | M | F4.3.1 | ✔ |
| F4.3.3 | Constraints (`CON`) and assumptions (`ASM`) with confidence, validation plan and review trigger | P0 | S | F2.7.1 | ✔ |
| F4.3.4 | Requirement-baseline approval (with the spec in feature mode) | P0 | S | F2.7.2 | ✔ |
| E4.4 | **Discovery in the feature workflow** | | | | |
| F4.4.1 | Feature-mode discovery uses the ledger and active profiles, scaled by depth; spec `FR` map to `REQ` | P0 | M | F4.1.2, F3.3.2 | ✔ |
| F4.4.2 | Unknown-answer protocol in instructions and records (options, effects, recommendation, assume/defer) | P0 | S | F4.1.1 | ✔ |
| E4.5 | **Validation** | | | | |
| F4.5.1 | Eval fixture Scenario A (mobile offline/sync): right questions asked, derivable ones not asked, no imposed architecture | P1 | M | F4.4.1 | |

## Acceptance criteria

- AC-1: In a fixture project, facts present in the code are recorded as derived, not asked.
- AC-2: `questions next` returns only open questions needed by the next gate, highest impact first, never answered keys.
- AC-3: A user who does not know an answer can accept an assumption or defer, and the task proceeds unless the question blocks the gate.
- AC-4: An NFR with a proposed target stays "proposed" until the requirement baseline is approved.
- AC-5: A second agent resumes the discussion from the ledger without repeating answered questions.

## Testing strategy

Unit tests for the ledger and batching; scenario tests; deterministic eval checks for Scenario A.

## Risks

Question overload (mitigated by impact/gate filtering and depth); invented numbers (mitigated by proposed/approved
status and basis fields); agents skipping derivation (eval checks).

## Estimated effort

About 5–6 weeks.

## Migration requirements

None for existing tasks; spec `FR` can optionally map to `REQ`.

## Documentation changes

`docs/discovery.md`, references for discovery and specification stages.

## Rollback plan

The ledger is optional per task at L0; feature workflow unchanged when disabled.

## Completion evidence

Tests, Scenario A eval results, phase review approved by the owner.
