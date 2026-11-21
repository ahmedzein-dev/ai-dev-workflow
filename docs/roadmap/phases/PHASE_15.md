# Phase 15 — Plugin Ecosystem & Extensibility (target v4.x)

> Numbering history (2026-11-22): brief-1 Phase 7 → Phase 13 (brief 2 integration, D-020) → Phase 15 (ORE integration, D-031); feature IDs follow the phase number.

**Status:** Planned (outline). Declarative extension points (adapters, parsers, templates, task types) arrive
earlier in Phase 1; this phase adds executable plugins, management and custom workflow policies.

## Goal

Let others extend the system without changing the core, while keeping every core safety guarantee intact.

## Scope

Plugin manifest with permissions and API version; install, uninstall, enable, disable; trusted sources; dependency
and compatibility validation; custom workflow policies (required/optional checks, roles, extra stages and gates,
audit rules); developer SDK, guide, examples and test utilities.

## Out of scope

Plugins that remove or weaken core gates, record human approvals, or run before the user trusts them; a hosted
marketplace (P11 study).

## Existing capabilities to keep

Declarative adapters, rules files, templates and task types from Phase 1; the trust store from Phase 2.

## Requirements

1. Plugin types: technology adapters, testing providers, quality gates, spec templates, audit rules, security
   scanners, agent adapters, git providers, issue trackers, notification providers, workflow extensions, report
   generators.
2. Any plugin that runs local code is part of the trust surface: shown, confirmed and pinned by hash before running.
3. Policies may add stages and gates; they can never remove the two approval gates or the evidence rules.
4. Incompatible or untrusted plugins are refused with a clear reason; the core keeps working.

## Dependencies

Phase 1 (registries), Phase 2 (trust store, gate table), Phase 11 (CLI for management); Phase 3 (profiles) and Phase 7 (modes) define what custom profiles and policies extend.

## Implementation tasks

| ID | Feature | Pri | Effort |
|---|---|---|---|
| F15.1.1 | Plugin manifest, permission model, API versioning and compatibility contract | P1 | M |
| F15.1.2 | Plugin management: install, uninstall, enable, disable, trusted sources, hash pinning | P1 | L |
| F15.2.1 | Custom workflow policy file (cannot remove core gates) | P1 | L |
| F15.3.1 | SDK: API docs, development guide, example plugins, test utilities | P1 | L |
| F15.4.1 | Additional solver adapters and custom problem types as plugins, including bring-your-own commercial solvers (never required) | P2 | M |

## Acceptance criteria

An independent plugin is created, added and run without core changes; incompatible or untrusted plugins are handled
safely (brief).

## Testing strategy

Example plugins as fixtures; negative tests (bad manifest, wrong API version, changed hash, policy trying to remove
a gate).

## Risks

S-07 untrusted code; maintenance of a public API (versioning discipline).

## Estimated effort

About 6–8 weeks.

## Migration requirements

None for existing projects.

## Documentation changes

`docs/plugins.md`, SDK reference, security model update.

## Rollback plan

Plugins disabled by default; removing them returns to built-in behaviour.

## Completion evidence

Plugin fixture results, phase review approved by the owner.
