# Phase 1 — Universal Development Support (target release v1.1.0)

**Status:** In progress — started 2026-11-22. F1.0.1 done; F1.0.2 closed as Completed with Limitations (CI not run until the owner pushes). Scope unchanged by the strategic integration, except that detection results now also feed profile activation (Phase 3).

## Goal

Make AIDevWorkflow genuinely technology-agnostic: detect any project's components from evidence, recommend the
right checks per component, let users add technologies without touching Python, and support specs for any kind of
task, all on an engine structure that can hold the later phases.

## Scope

- E1.0 Engine foundations (pulled from Phase 2, D-001): package split, engine API, state schema + migration +
  locking, dev tooling, single version source.
- E1.1 Project detection engine with components, evidence and confidence.
- E1.2 Declarative technology adapters, built-in and project-local (the generic custom adapter).
- E1.3 Output parsers (JUnit XML, SARIF, regex) and baselines for any structured parser.
- E1.4 Multi-technology projects: config schema 2 with components and per-check `cwd`.
- E1.5 Universal specification system: configurable task types and templates per type.
- E1.6 Validation fixtures, the "new adapter without core change" proof, documentation.

## Out of scope

Approval gates and their rules (unchanged, as the brief requires); executable plugins (P8); git hooks, approval
channels, evidence v2 (P2); any UI (P3).

## Existing capabilities to keep

`init --discover` flow and wording (recommendations, explanations, tool presence, user confirmation), every existing
check type and field, rules files, private template library, all 141 tests. For a single-technology repository at
the root, detection output must stay equivalent to v1.0.0 (same checks, same commands).

## Requirements

1. Detection uses file evidence only, records evidence and confidence for each finding, and never applies a
   recommendation without user confirmation.
2. Monorepos: components anywhere in the tracked tree (bounded depth, ignored paths respected).
3. Adding a technology = adding a JSON adapter (built-in or in `.ai-dev-workflow/adapters/`); no core change.
4. Adapters suggest checks; they never run commands automatically.
5. Projects with an unknown technology can declare commands, success conditions and output formats in config.
6. Any project can use its own spec template; a template can be chosen per task type, with fallback.
7. `config.json` schema 1 projects keep working without changes; moving to schema 2 is an explicit, reversible step.
8. Python 3.9 compatible, standard library only.

## Dependencies

Owner decisions listed in the status line. F1.0.1 needs the owner's go-ahead to install the pinned release on their
machine and to run `init` in this repository.

## Technical decisions (proposed)

D-002 package structure, D-003 declarative adapters, D-004 standard output formats, D-012 Python 3.9 floor with a
minimal TOML reader. New decisions taken during the phase go to DECISIONS.md before implementation.

## Proposed architecture

See [TARGET_ARCHITECTURE.md §3–4.3](../TARGET_ARCHITECTURE.md). Detection pipeline:

```
git ls-files ─▶ candidate manifests ─▶ adapters (detect rules) ─▶ components {path, techs, frameworks, pm, evidence, confidence}
                                                                      │
config (schema 2) ◀── user confirms ◀── recommended checks per component (cwd, format, explain, tool_found)
```

## Implementation tasks

Priority: P0 must · P1 should · P2 could. Effort (one developer with an AI agent, rough): S ≤ 1 day · M 2–4 days ·
L 1–2 weeks · XL > 2 weeks. Each feature is one AIDevWorkflow task (D-016).

### E1.0 — Engine foundations

| ID | Feature | Pri | Effort | Depends on |
|---|---|---|---|---|
| F1.0.1 | Self-hosting setup: install the pinned `v1.0.0` release as the managing engine; `init` this repository with the owner's choices (D-005–D-007) | P0 | S | Owner decisions |
| F1.0.2 | Dev tooling: ruff + mypy configuration (dev only), CI job; golden CLI output tests for `status`, `spec-check`, `outcome`, `init --discover` | P0 | S | F1.0.1 |
| F1.0.3 | Mechanical split of `workflow.py` into the `aidw/` package; `workflow.py` becomes the entry point; no behaviour change | P0 | L | F1.0.2 |
| F1.0.4 | Engine API (`aidw/api.py`): commands return data; CLI only prints | P0 | M | F1.0.3 |
| F1.0.5 | State store: `schema` check on load, `migrate` (dry run, backup, rollback), lock file with stale detection, fsync, temp-file cleanup | P0 | M | F1.0.3 |
| F1.0.6 | Single version source + consistency test (`__version__`, SKILL.md metadata, changelog) | P1 | S | F1.0.3 |

Tasks for F1.0.3 (example of the task level used for every feature at its start):
1. Record golden outputs and the test baseline.
2. Create `aidw/` with `infra/` (fsutil, git, secrets, process), move code without edits.
3. Move `records/`, then `core/`, then `adapters/` (detection as-is), then `cli/`, re-running tests after each move.
4. Keep `workflow.py` importable as `workflow` for tests and hooks (re-export public names).
5. Verify installs: user-level copy, project-level copy, Windows CI.

### E1.1 — Project detection engine

| ID | Feature | Pri | Effort | Depends on |
|---|---|---|---|---|
| F1.1.1 | Component discovery over `git ls-files` (manifests at any depth, bounded, ignored paths respected) with evidence and confidence | P0 | M | F1.0.4 |
| F1.1.2 | Detection report: languages, frameworks, package managers, build and test tools, databases, IaC, Docker, CI (including multi-line `run:` blocks), instruction files, tools available on PATH | P0 | M | F1.1.1 |
| F1.1.3 | Component-scoped check IDs (`web:test`), fixing the silent de-duplication (TD-03) | P0 | S | F1.1.1 |

### E1.2 — Declarative technology adapters

| ID | Feature | Pri | Effort | Depends on |
|---|---|---|---|---|
| F1.2.1 | Adapter format, JSON Schema, small condition language (`file`, `glob`, `contains`, `json_has`, `toml_has`), registry and loader | P0 | M | F1.0.4 |
| F1.2.2 | Port the 11 existing ecosystems to built-in adapters with v1.0.0-equivalent output for root-level single-tech repos | P0 | M | F1.2.1, F1.1.1 |
| F1.2.3 | New built-in adapters: PHP/Composer/Laravel, Docker, Terraform, GitHub Actions, Xcode projects, React Native/Expo and Next.js/Angular/Vue/Svelte framework detection | P1 | M | F1.2.2 |
| F1.2.4 | Manifest readers declared by adapters, so `manifest-diff` covers Go, Rust, Maven, Gradle, .NET, Composer, Gemfile, pyproject | P1 | M | F1.2.1 |
| F1.2.5 | Project-local adapters in `.ai-dev-workflow/adapters/*.json` (the generic custom adapter), validated, never executing code | P0 | S | F1.2.1 |

### E1.3 — Output parsers and quality gates

| ID | Feature | Pri | Effort | Depends on |
|---|---|---|---|---|
| F1.3.1 | Parser interface + JUnit XML parser (counts, failures, test names in the summary) | P0 | M | F1.0.3 |
| F1.3.2 | SARIF parser; baselines (new vs existing issues) for any structured parser | P1 | M | F1.3.1 |
| F1.3.3 | Declared regex parser and explicit success/failure conditions per check | P1 | S | F1.3.1 |

### E1.4 — Multi-technology projects

| ID | Feature | Pri | Effort | Depends on |
|---|---|---|---|---|
| F1.4.1 | `config.json` schema 2 (components, `cwd`, adapter references, task types); `migrate` from schema 1; schema 1 still read | P0 | M | F1.0.5, F1.1.1 |
| F1.4.2 | Changed files → affected components → suggested checks in `status`/`scope` (advisory; required checks unchanged) | P1 | M | F1.4.1 |

### E1.5 — Universal specification system

| ID | Feature | Pri | Effort | Depends on |
|---|---|---|---|---|
| F1.5.1 | Configurable task types (defaults stay `feature, bugfix, enhancement, refactor`) | P1 | S | F1.4.1 |
| F1.5.2 | Spec template per task type with fallback to the project default; library entries per type | P1 | M | F1.5.1 |
| F1.5.3 | Example template pack (feature, bugfix, refactor, research, infrastructure, documentation) with rules files; never applied without confirmation | P2 | M | F1.5.2 |

### E1.6 — Validation and documentation

| ID | Feature | Pri | Effort | Depends on |
|---|---|---|---|---|
| F1.6.1 | Fixture repositories: Flutter, Node/React, Python/FastAPI, Go CLI, Terraform, full-stack monorepo (Flutter + React + Node + Postgres + Docker), unsupported technology with a project-local adapter | P0 | L | E1.1–E1.4 |
| F1.6.2 | Proof test: a new adapter added as data changes detection without any core file change | P0 | S | F1.2.5 |
| F1.6.3 | Docs: adapters guide, configuration and templates updates, migration notes, compatibility and validation reports, both languages of the guide where user-facing | P0 | M | all |

## Acceptance criteria

- AC-1: Detection on each fixture lists the right components with evidence and confidence; nothing is applied
  without confirmation.
- AC-2: For root-level single-technology repositories, recommended checks equal v1.0.0 output (golden tests).
- AC-3: The polyglot repository from the TD-03 reproduction gets Node, Python and Flutter checks, each scoped to its
  component.
- AC-4: A new adapter (JSON) added in a test changes detection with zero core code changes (F1.6.2).
- AC-5: An unsupported technology works end to end through a project-local adapter and custom checks.
- AC-6: JUnit XML and SARIF outputs are parsed; baselines separate new and existing issues.
- AC-7: A schema 1 project keeps working unchanged; `migrate` to schema 2 has a dry run, a backup and a rollback.
- AC-8: Approval gates behave exactly as in v1.0.0 (all existing scenario tests pass unchanged).
- AC-9: Tests pass on Ubuntu, macOS and Windows with Python 3.9 and 3.13; privacy scan clean.

## Testing strategy

Golden outputs before the split; unit tests per module; fixture-based detection tests; migration tests on copies of
real v1.0.0 records (the sample task); regression run of all existing tests after every feature; CI matrix.

## Risks

R-02 backward compatibility, R-07 adapter maintenance, R-11 split regressions, R-13 false positives. Mitigations
in [RISK_REGISTER.md](../RISK_REGISTER.md).

## Estimated effort

About 6–9 weeks of focused work in total (E1.0 ≈ 2–3 weeks, E1.1–E1.3 ≈ 2–3 weeks, E1.4–E1.6 ≈ 2–3 weeks).
Re-estimated at each feature's spec.

## Migration requirements

M1 and M2 from [TARGET_ARCHITECTURE.md §5](../TARGET_ARCHITECTURE.md#5-migration-and-backward-compatibility-plan);
config schema 2 (M3) is introduced here as opt-in.

## Documentation changes

`docs/configuration.md`, `docs/templates-and-rules.md`, new `docs/adapters.md`, `docs/installation.md` (update
notes), `docs/compatibility.md`, `docs/validation-report.md`, `README.md`, `index.html` (user-facing setup changes
only), `CHANGELOG.md`.

## Rollback plan

Every feature is a separate change; v1.0.0 stays installable from its tag; `migrate --rollback` restores schema 1
config from the backup.

## Completion evidence

Per feature: the AIDevWorkflow task report (closed status and outcome), test results, CI run link. For the phase: a
phase review in PROGRESS.md approved by the owner, and the v1.1.0 release checklist.
