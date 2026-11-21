# Phase 14 — Multi-Agent Orchestration (target v4.x)

> Numbering history (2026-11-22): brief-1 Phase 6 → Phase 12 (brief 2 integration, D-020) → Phase 14 (ORE integration, D-031); feature IDs follow the phase number.

**Status:** Planned (outline; automatic mode depends on a research spike, D-011).

## Goal

Make collaboration between coding agents smooth without forcing the user to carry context by hand, building on the
existing manual handoff instead of replacing it.

## Scope

Agent adapters with capability profiles; role assignment (analyst, architect, planner, developer, tester, reviewer,
security reviewer, auditor); execution modes (single, manual multi-agent, custom, and an opt-in automatic mode after
the spike); independent audit packets; reliability controls; privacy and cost consent.

## Out of scope

Agents approving on behalf of the human (INV-01); default-on automation; unofficial or terms-violating integrations.

## Existing capabilities to keep

Records-only handoff, `resume`, audit independence levels, tested invocation per agent.

## Requirements

1. Each agent adapter declares what it actually supports (invocation, session, resume, permissions, structured
   output, streaming, cancellation, usage metrics, errors) with evidence labels.
2. Multiple agents' approvals never replace a human approval.
3. Before running an external agent: show what data it receives, its permissions and the possible cost; get consent.
4. Automatic mode is opt-in, budget-limited, with timeouts, retries, iteration limits and loop prevention.
5. Two agents never work on the same task workspace at the same time.

## Dependencies

Phase 2 (events, locking), Phase 11 F11.1.3 (handoff packet), Phase 12 (worktrees) for parallel agents.

## Implementation tasks

| ID | Feature | Pri | Effort |
|---|---|---|---|
| F14.1.1 | Agent capability profiles (data), `aidev agents` report | P1 | M |
| F14.2.1 | Role assignment per task; policy "auditor must differ from implementer" | P1 | M |
| F14.3.1 | Manual multi-agent mode via handoff packets and role prompts | P1 | S |
| F14.3.2 | Research spike: official headless modes, terms, rate limits, cost reporting per vendor; decision record | P1 | M |
| F14.3.3 | Automatic orchestrator (opt-in): state machine driving agents, budgets, retries, timeouts, iteration limits, cancellation, recovery | P2 | XL |
| F14.4.1 | Independent audit packet (diff, spec, plan, standards, evidence) for a separate agent | P1 | S |
| F14.5.1 | Consent and cost disclosure before external agent runs | P2 | M |
| F14.6.1 | ORE agent and model allocation: per-stage choice, number of agents, parallel split, independent auditor, single vs multi-agent; human gates, privacy and budgets as hard constraints; `INSUFFICIENT_DATA` fallback to manual choice (ORE-G) | P2 | M |
| F14.6.2 | Feedback loop: measured task results update the registry; allocation results go stale when inputs change | P2 | S |

## Acceptance criteria

A full feature runs with one agent planning, another implementing and an independent agent auditing, with human
approvals kept and the ability to resume after any agent fails (brief). The automatic part of this criterion applies
only if the spike approves automatic mode.

## Testing strategy

Fake agent adapters for deterministic tests; recorded live runs per vendor in the validation report with versions.

## Risks

R-04 vendor changes, R-08 cost and terms, reliability of headless modes.

## Estimated effort

Manual and role features ≈ 3 weeks; automatic orchestrator ≈ 6–10 weeks if approved.

## Migration requirements

Task state gains `roles` and `assignments`; backward compatible.

## Documentation changes

`docs/multi-agent.md`, compatibility matrix per agent.

## Rollback plan

Single-agent mode remains the default and unchanged.

## Completion evidence

Recorded multi-agent runs, test results, phase review approved by the owner.
