# Phase 5 — Engineering Decisions, Trade-offs & ADRs (target v1.5.0) · completes the MVP

**Status:** Planned (new, strategic integration 2026-11-22).

## Goal

Make every consequential engineering decision explicit: framed, compared against realistic alternatives with
honest trade-offs, recommended with reasons tied to this project, decided by the engineer, recorded as an ADR with
history, and linked to the requirements, plans and tests it affects.

## Scope

ADR records and lifecycle; alternatives, criteria (only user-approved weights), trade-offs, claim types; consequential
vs delegated decisions under a written policy; decision-set approvals; the conflict rule (decision vs must
requirement); plan approval requires current approved decisions; staleness and re-evaluation; reconsideration
triggers and supersede chains; `decision` mode; spike/PoC evidence; partner behaviour and the mentor overlay.

## Out of scope

Full system-design mode, HLD/LLD and diagrams (Phase 7); dashboard decision center (Phase 11).

## Existing capabilities to keep

`decision` command (user decisions with evidence) — it becomes the lightweight delegated/recorded decision; manifest
approvals for new dependencies keep working.

## Requirements

1. Every consequential decision has: problem, requirements and constraints, at least two realistic alternatives (or a
   recorded reason why only one exists), advantages, disadvantages, trade-offs, cost/complexity/risk, impact,
   reversibility, a recommendation with project-specific reasons, the human decision with evidence, consequences.
2. No arbitrary scoring: weights only if the user approved them; numbers state their source and assumptions; claims
   needing measurement trigger a spike or PoC proposal.
3. The engineer decides; the agent challenges choices that conflict with requirements and never agrees just to please.
4. Consequential decisions need explicit approval; related ones can be approved as a set; small ones may be delegated
   only under the approved policy and are listed at the next gate.
5. A decision recorded as conflicting with a must requirement cannot be approved until the conflict is resolved.
6. Superseded decisions stay; a changed requirement or constraint flags dependent decisions for re-evaluation.
7. Approved decisions affecting implementation are versioned and hash-bound like specs and plans.

## Dependencies

Phase 2 (record store, generic and decision-set approvals, gate table), Phase 3 (decision triggers), Phase 4 (requirements, constraints, assumptions).

## Technical decisions (proposed)

D-022 approval types, D-023 delegation policy, D-024 modes (decision mode first). Details: [ENGINEERING_INTELLIGENCE.md §3–6](../ENGINEERING_INTELLIGENCE.md).

## Implementation tasks

| ID | Feature | Pri | Effort | Depends on | MVP |
|---|---|---|---|---|---|
| E5.1 | **ADR records** | | | | |
| F5.1.1 | ADR format and lifecycle: proposed, under discussion, approved, rejected, deferred, superseded, needs re-evaluation | P0 | M | F2.7.1 | ✔ |
| F5.1.2 | Alternatives table, criteria (approved weights only), trade-offs, claim types (fact / assumption / estimate / recommendation / unknown), number sources | P0 | M | F5.1.1 | ✔ |
| E5.2 | **Decision approvals** | | | | |
| F5.2.1 | Consequential vs delegated classification and the project's delegation policy | P0 | M | F5.1.1 | ✔ |
| F5.2.2 | Decision-set approval for related ADRs | P0 | S | F2.7.2 | ✔ |
| F5.2.3 | Conflict rule: recorded conflict with a must requirement blocks approval until resolved | P0 | M | F4.3.1 | ✔ |
| E5.3 | **Integration with the workflow** | | | | |
| F5.3.1 | Plan approval requires every cited decision to be approved and current | P0 | S | F5.1.1 | ✔ |
| F5.3.2 | Staleness: requirement/constraint change → decisions need re-evaluation → dependent plans lose validity | P0 | M | F2.7.3 | ✔ |
| F5.3.3 | Reconsider-when triggers and supersede chains | P1 | S | F5.1.1 | |
| E5.4 | **Technical decision mode** | | | | |
| F5.4.1 | `decision` mode: frame → options → evaluate → decision approval → record | P0 | M | F2.1.1 | ✔ |
| F5.4.2 | Spike / PoC results recorded as decision validation evidence | P1 | S | F5.1.1 | |
| E5.5 | **Partner behaviour** | | | | |
| F5.5.1 | Instructions: challenge, expose risks, offer better alternatives, explain future impact, no sycophancy; mentor overlay (brief / standard / deep) | P0 | S | — | ✔ |
| F5.5.2 | Decision presentation, one screen first: recommendation, why, risks and limits, what approving means, what happens next; details on demand; approval interactions counted | P0 | S | F5.2.2 | ✔ |
| E5.6 | **Validation** | | | | |
| F5.6.1 | Eval fixtures: Scenario B (booking concurrency — decision part), G (changed business requirement), H (decision conflict) | P0 | M | E5.1–E5.3 | ✔ |
| F5.6.2 | **Validation Gate A** (before the v1.5 release): compare only capabilities actually shipped by v1.5—existing short spec/plan and approvals, plus Phase 3–5 profiles, discovery, requirements and decisions—against selected alternatives on equivalent UX-A–UX-C tasks. Fix a consistent evaluation method before interpreting results. Record decision quality, observed rework, user effort, alternative version/configuration, evidence source and unavailable values. Phase 8 expanded specs, planning and traceability are outside this gate. Gate report, limitations and owner decision (proceed / adjust / simplify / redesign) | P0 | M | F5.6.1, F1.7.4 | ✔ |

## Acceptance criteria

- AC-1: Scenario B: race conditions are identified; concurrency-control alternatives are compared; the decision is recorded as an approved ADR linked to requirements and tests.
- AC-2: Scenario G: changing a requirement flags the affected ADRs and plans; re-approval keeps the full history.
- AC-3: Scenario H: an engineer's choice conflicting with a must requirement is blocked until the requirement or the decision changes.
- AC-4: Three related decisions are approved with one user message; each is hashed and recorded.
- AC-5: A plan citing a decision that changed after approval cannot be approved.
- AC-6: Gate A report compares only shipped v1.5 capabilities on equivalent tasks using a method fixed before interpretation; it records decision quality, observed rework, user effort, alternative version/configuration, evidence source and limitations, explicitly excludes Phase 8 capabilities, and carries the owner's decision before v1.5 ships. Missing essential evidence is insufficient or blocked, not a silent pass (F5.6.2).

## Testing strategy

Unit tests for ADR parsing, approvals, conflict and staleness rules; scenario tests; deterministic eval checks for B, G, H.

## Risks

Approval fatigue (mitigated by decision sets, delegation policy, depth); shallow alternatives (eval checks, audit);
sycophancy (Scenario H, human rubric).

## Estimated effort

About 5–7 weeks.

## Migration requirements

Existing `decisions` entries in tasks stay valid and are shown as recorded (delegated) decisions.

## Documentation changes

`docs/decisions.md` (ADR guide, approval types, delegation policy), references for planning.

## Rollback plan

ADRs optional below L2; existing decision recording continues to work.

## Completion evidence

Tests, eval results for B, G, H; MVP review approved by the owner (v1.5.0).
Validation Gate A report and the owner's decision.
