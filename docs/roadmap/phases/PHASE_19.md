# Phase 19 — Production Readiness & Public Release (continuous, with a final checkpoint)

> Numbering history (2026-11-22): brief-1 Phase 10 → Phase 17 (brief 2 integration, D-020) → Phase 19 (ORE integration, D-031); feature IDs follow the phase number.

**Status:** Planned. Recommended change (D-019): apply a release checklist to every version from v1.1 on, and keep
this phase for what remains before a broad public launch.

## Goal

A stable, documented product that can be installed, updated, rolled back and trusted, with evidence for every
feature declared ready.

## Scope

Test strategy completion (unit, integration, end-to-end, regression, security, compatibility, concurrency, recovery,
migration, plugin, agent interoperability, dashboard); cross-platform validation; technology and agent validation
matrices; installation, update, uninstall, doctor, migration, packaging, GitHub Releases, rollback; full
documentation set including the bilingual guide; CI/CD with security, packaging, release and consistency checks.

## Out of scope

Choosing a package manager before comparing options (brief).

## Existing capabilities to keep

CI matrix (3 OS × 2 Python versions), privacy scan, doc-consistency tests, evidence-labelled compatibility and
validation reports.

## Requirements

1. No feature is called ready without test evidence, documented limits and no open critical issue (brief).
2. Agent validation matrix per agent: supported, tested, untested, limits, tested versions, evidence.
3. Technology validation matrix with at least: Flutter, native mobile, Node backend, Python backend, Java or .NET
   backend, React frontend, full-stack monorepo, Go or Rust CLI, IaC, custom technology.
4. Distribution options compared (git clone + installer, GitHub Release archive, pipx, Homebrew) before choosing.

## Dependencies

Each release; the final checkpoint after the phases chosen for the public launch.

## Implementation tasks

| ID | Feature | Pri | Effort |
|---|---|---|---|
| F19.1.1 | Release checklist and `tools/release_check.py` (versions, changelog, tests, scan, docs consistency, migration test) — used from v1.1 | P0 | S |
| F19.2.1 | Test strategy completion: concurrency, recovery, migration, interoperability suites | P1 | L |
| F19.3.1 | Technology validation matrix with fixtures in CI | P1 | L |
| F19.3.2 | Agent validation matrix with recorded live runs per release | P1 | M |
| F19.4.1 | Distribution: compare options, release archives on GitHub Releases, update and rollback commands | P1 | M |
| F19.5.1 | Documentation set: architecture, user, configuration, adapters, plugins, security, troubleshooting, FAQ, contributing; bilingual guide refresh | P1 | L |
| F19.6.1 | CI/CD: coverage report, security checks (secret scan, dependency-free audit), packaging and release validation, version consistency | P1 | M |
| F19.7.1 | ORE validation matrix per release: solvers × scenarios × operating systems, guarantee levels re-confirmed | P1 | M |

## Acceptance criteria

No feature is considered ready for publication without clear test evidence, documented known limits and no
unaddressed critical issue (brief).

## Testing strategy

Everything above, run on every release; manual checks recorded with versions.

## Risks

R-05 bandwidth; R-16 platform differences.

## Estimated effort

Checklist ≈ 1 day (early); the rest ≈ 4–6 weeks spread across releases.

## Migration requirements

Migration tests for every record schema change.

## Documentation changes

The whole documentation set.

## Rollback plan

Every release installable from its tag; documented downgrade path per release.

## Completion evidence

Release checklists, CI runs, validation matrices.
