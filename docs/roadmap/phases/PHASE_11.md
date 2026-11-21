# Phase 11 — Developer Experience: CLI, Dashboard & Engineering Decision Center (target v3.x)

> Numbering history (2026-11-22): brief-1 Phase 3 → Phase 9 (brief 2 integration, D-020) → Phase 11 (ORE integration, D-031); feature IDs follow the phase number.

**Status:** Planned. Moved after the engineering-intelligence phases (3–8), so the dashboard shows decisions, requirements and designs, not only tasks. Until then, approvals happen in chat and through the user CLI channel from Phase 2 (F2.3.1).

## Goal

Let a developer manage tasks, approvals and evidence without opening JSON or Markdown files, through a human CLI
and an optional local dashboard that both use the same engine.

## Scope

`aidev` human CLI (D-010); handoff packet; local web dashboard (D-009) with tasks, task detail, approval center,
basic metrics; light/dark, responsive, Arabic/English with correct RTL.

## Out of scope

Accounts, cloud hosting, team features (Phase 18); desktop app wrappers (revisit after v3); advanced analytics (Phase 17).

## Existing capabilities to keep

`workflow.py` CLI for agents (unchanged commands and `--json` outputs); the skill-only path without any dashboard.

## Requirements

1. CLI and dashboard call the engine API; no business rule or approval logic in the UI (INV-04).
2. Dashboard approvals go through the engine and are recorded as channel A1 (or higher with signing).
3. Dashboard binds to 127.0.0.1, uses a per-launch token, checks Host/Origin, serves only allow-listed files.
4. Works without installing anything beyond the skill; no network requests to third parties.
5. The skill keeps working if the dashboard is never used.

## Dependencies

Phase 1 E1.0 (API), Phase 2 F2.3.1 and E2.7 (approval channels, record store), Phases 4–9 for the engineering views.

## Technical decisions (proposed)

D-009 dashboard technology; D-010 `aidev` launcher. CLI command map (final design in F11.1.1):

| `aidev` | Engine command(s) |
|---|---|
| `init` | `init --discover` → confirm → `init` |
| `doctor` | `install.py doctor` + project checks (config, tools, trust store) |
| `tasks` / `status <task>` | `status` |
| `resume <task>` / `pause <task>` | `resume` / `pause` |
| `approve <task> spec\|plan` | `approve` via channel A1 with diff and confirmation |
| `check` | `check` |
| `handoff <task>` | new: generated handoff packet |
| `dashboard` | start the local dashboard |
| `agents` / `plugins` | capability report (Phase 14) / plugin list (Phase 15) |

## Implementation tasks

| ID | Feature | Pri | Effort | Depends on |
|---|---|---|---|---|
| E11.1 | **Human CLI** (v3.0) | | | |
| F11.1.1 | CLI design record: command map, output style, exit codes, localisation approach | P0 | S | E1.0 |
| F11.1.2 | `aidev` launcher installed by `install.py`; commands `init`, `doctor`, `tasks`, `status`, `resume`, `pause`, `check`, interactive `approve` | P0 | M | F11.1.1, F2.3.1 |
| F11.1.3 | `handoff <task>`: one generated brief (stage, next step, open items, files to read, last evidence) | P1 | S | E1.0 |
| E11.2 | **Dashboard foundation** (v3.x) | | | |
| F11.2.1 | Technology and security design record | P0 | S | F11.1.1 |
| F11.2.2 | Local server on `http.server`, token, JSON endpoints over the engine API (read first, then approval actions) | P0 | M | F11.2.1 |
| F11.2.3 | Opt-in project registry (`~/.ai-dev-workflow/projects.json`) and derived index (`index.db`) | P1 | M | F11.2.2 |
| E11.3 | **Views** | | | |
| F11.3.1 | Projects and tasks overview; task detail: stage, spec, plan, acceptance criteria, check results, audit findings, history, final report | P0 | L | F11.2.2 |
| F11.3.2 | Approval center: document version, diff against the previous version, hash, warnings, decisions; Approve / Request changes / Reject through the engine | P0 | L | F11.2.2, F2.3.1 |
| E11.4 | **Design** | | | |
| F11.4.1 | Design system reused from `index.html`: tokens, light/dark, responsive, Arabic/English, RTL, accessible contrast | P0 | M | — |
| E11.5 | **Quality** | | | |
| F11.5.1 | Tests: API contract, rendering smoke tests, security tests (token, Origin, path traversal) | P0 | M | E11.2–E11.3 |
| F11.5.2 | Regression test proving the skill-only path works with no dashboard files used | P0 | S | — |
| E11.6 | **Engineering views** (brief 2 §16) | | | |
| F11.6.1 | Business objectives, discovery questions and answers (answer from the UI), requirements explorer, risks and assumptions | P1 | L | Phase 4 |
| F11.6.2 | Engineering decision center: alternatives, trade-off matrix (user-approved criteria only), AI recommendation and reasons, choose a different option, request more information or a spike, approve decision sets, ADR history | P0 | L | Phase 5 |
| F11.6.3 | Architecture explorer and diagram viewer; design version comparison; impact of changing an old decision | P1 | L | Phases 7, 8 |
| F11.6.4 | Traceability explorer, open engineering questions, project health, production readiness, customer delivery status, business outcome metrics | P2 | L | Phases 8, 16, 17 |
| F11.6.5 | ORE views: problem explorer, results with guarantee levels and classifications, trade-off and Pareto charts (complete vs partial), scenarios, decision review through the core | P2 | L | Phases 6, 10 |

## Acceptance criteria

- AC-1: A user can review and manage tasks, approvals and test results from the dashboard (brief).
- AC-2: The system works exactly as before when the dashboard is not used (brief).
- AC-3: Every approval made in the dashboard appears in `state.json` with channel A1 and is accepted by `check`.
- AC-4: Arabic layout is correct right-to-left on desktop and at 375 px; light and dark themes pass contrast checks.

## Testing strategy

API contract tests against the engine; browser smoke tests on the three operating systems in CI where feasible;
security tests for the local server; manual RTL review recorded in the validation report.

## Risks

R-06 drift between UI and engine, S-10 local server exposure, scope creep in UI polish.

## Estimated effort

CLI ≈ 2 weeks; dashboard ≈ 5–8 weeks.

## Migration requirements

None for records; approval channel fields come from Phase 2.

## Documentation changes

`docs/cli.md`, `docs/dashboard.md`, README quick start, guide sections in both languages.

## Rollback plan

The dashboard is an optional command; disabling it leaves the skill and CLI unaffected.

## Completion evidence

Test results, screenshots in both languages and themes, phase review approved by the owner.
