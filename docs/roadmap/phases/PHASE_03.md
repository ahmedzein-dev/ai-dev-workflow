# Phase 3 — Engineering Domain Profiles & Adaptive Depth (target v1.3.0) · MVP

**Status:** Planned (new, strategic integration 2026-11-22).

## Goal

Give agents curated, extensible engineering knowledge per domain, separate from technology adapters and from the
core, and scale the depth of the process to the task so small changes stay light and critical ones get real analysis.

## Scope

Profile format and registry (built-in and project-local); profile activation from detection plus user confirmation;
built-in profiles (generic, backend, mobile, frontend first; cloud-devops, AI, distributed systems, data, security and
the discovery part of forward-deployed next); decision guides, trade-off guides and failure-pattern references;
adaptive depth levels L0–L3 with a recorded classification, user override and a depth policy that sets required
artifacts per mode.

## Out of scope

Running any profile code (profiles are data); semantic grading of answers; modes other than `feature` (Phases 5–7).

## Existing capabilities to keep

Template rules (mandatory / judgment / advisory) and the "record a decision on each advisory question" pattern —
profiles reuse it for topic applicability.

## Requirements

1. Technology adapters, domain profiles and the workflow core stay separate; a project can activate several profiles.
2. Adding or customising a profile needs no core change (`.ai-dev-workflow/profiles/`).
3. Each profile defines discovery topics, questions, decision triggers, considerations, trade-offs, spec sections,
   planning needs, recommended diagrams, verification needs, risks and failure cases.
4. Profiles are references: the agent records which topics applied and why others did not.
5. Depth is proposed with reasons, shown at the first gate, can be changed by the user, and never removes core gates.
6. Unknown domains work through the generic profile plus custom rules.

## Dependencies

Phase 1 (detection, registries), Phase 2 (gate table, record store).

## Technical decisions (proposed)

D-021 record model, D-025 depth levels, D-026 profile format. Details: [ENGINEERING_INTELLIGENCE.md §7, §9](../ENGINEERING_INTELLIGENCE.md).

## Implementation tasks

| ID | Feature | Pri | Effort | Depends on | MVP |
|---|---|---|---|---|---|
| E3.1 | **Profile system** | | | | |
| F3.1.1 | Profile format (`profile.json` + Markdown guides), JSON Schema, registry, project-local overrides | P0 | M | F1.2.1 | ✔ |
| F3.1.2 | Profile activation from detected components and the user's confirmation; several profiles per project | P0 | S | F3.1.1, F1.1.1 | ✔ |
| F3.1.3 | Topic applicability records (applied / not applicable with reason) | P1 | S | F3.1.1 | ✔ |
| E3.2 | **Built-in profiles and knowledge** | | | | |
| F3.2.1 | `generic` profile (fallback for any domain): business, technical, functional and non-functional topics | P0 | M | F3.1.1 | ✔ |
| F3.2.2 | backend, mobile, frontend profiles (brief 2 §7 contents) | P0 | L | F3.2.1 | ✔ |
| F3.2.3 | cloud-devops, ai-engineering, distributed-systems, data-engineering, security, fde-discovery profiles | P1 | L | F3.2.1 | |
| F3.2.4 | Decision guides, trade-off guides, architecture patterns, failure-pattern references (Markdown, sourced) | P1 | L | F3.1.1 | |
| E3.3 | **Adaptive depth** | | | | |
| F3.3.1 | Depth levels L0–L3: proposal with signals and reasons, user override, shown at the first gate, recorded | P0 | M | F2.1.1 | ✔ |
| F3.3.2 | Depth policy: required artifacts per depth and mode, enforced by the gate table | P0 | M | F3.3.1 | ✔ |
| F3.3.3 | Profile minimum-depth rules (paths, topics) and under-depth warnings | P1 | S | F3.3.2 | |
| E3.4 | **Validation and docs** | | | | |
| F3.4.1 | Eval fixtures: Scenario F (small bug fix stays L0/L1, no HLD or ADR) and Scenario I (unknown domain via generic profile) | P0 | M | F3.3.2 | ✔ |
| F3.4.2 | Docs: profiles guide, depth guide, writing a custom profile | P0 | M | all | ✔ |

## Acceptance criteria

- AC-1: A project activates backend + distributed-systems + AI profiles together; topics from each appear, with no core change.
- AC-2: A custom profile in `.ai-dev-workflow/profiles/` is picked up without editing engine code.
- AC-3: Scenario F: a typo fix is classified L0, requires no HLD/LLD/ADR, and keeps both approval gates.
- AC-4: Scenario I: an unsupported domain gets generic topics and custom rules end to end.
- AC-5: A depth lower than the signals suggest is shown as a warning at the gate.

## Testing strategy

Schema tests for profiles; registry tests (built-in vs project override); depth policy tests per level; deterministic
eval checks on recorded scenario runs.

## Risks

Profiles turning into bureaucratic checklists (mitigated by applicability records and depth); profile maintenance
(R-07); agents gaming depth downward (mitigated by signals, warnings and the user seeing the level).

## Estimated effort

About 5–7 weeks (most of it profile content).

## Migration requirements

Existing tasks get depth `unclassified` and behave as today; new tasks classify depth.

## Documentation changes

`docs/profiles.md`, `docs/depth.md`, SKILL.md and references (how to use profiles and depth).

## Rollback plan

Disable profiles and depth policy per project; the feature workflow continues as in v1.2.

## Completion evidence

Test results, eval results for Scenarios F and I, phase review approved by the owner.
