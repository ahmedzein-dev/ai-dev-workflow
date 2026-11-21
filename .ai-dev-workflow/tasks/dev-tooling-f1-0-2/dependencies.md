# Dependencies: F1.0.2 Dev tooling: ruff, mypy and golden CLI outputs

List every external input this task needs: designs, API contracts, data, platform constraints, decisions.
Ask only for what this task actually needs; inspect the code first.

- **Class:** Blocking (required before its gate), Non-blocking (helpful, not essential), Verified (confirmed
  with reliable evidence) or Not applicable.
- **Gate** (Blocking only): the stage it stops — `spec`, `plan`, `implementation` or `completion`.
- **Type:** ui, backend, data, platform, security, third-party, decision, environment or other.

| ID | Type | Class | Gate | Owner | Summary |
|----|------|-------|------|-------|---------|
| DEP-1 | environment | Verified | | Project owner | Permission to download pinned ruff and mypy from PyPI into a local, git-ignored `.venv/` on the owner's Mac |
| DEP-2 | third-party | Non-blocking | | Project owner | CI installs the same pinned versions from PyPI on GitHub Actions (free for public repositories) |
| DEP-3 | decision | Verified | | Project owner | Roadmap status files (`docs/roadmap/`) are excluded from this task's scope, since they are project-management records updated alongside every task |

## Details

### DEP-1 — Local install of the dev tools

**Why it matters:** FR-2 and FR-3 need ruff and mypy to run locally; neither is installed on this machine
(`ruff`: not found; no `ruff` module for Python 3.13).
**Who provides it:** The project owner (approval to download).
**Answer received:** «موافق على كله ومش فارقه تتنشر» (owner, 2026-11-22) — approves the download.
**Resolution:** Verified; the tools are installed into `.venv/` in S2.

### DEP-2 — Tools in CI

**Why it matters:** FR-4: the lint job installs the pinned tools from PyPI. Nothing is added to the shipped skill.
**Who provides it:** Covered by the spec approval.
**Answer received:** —
**Resolution:** Decided by approving the spec.

### DEP-3 — Roadmap files outside the task scope

**Why it matters:** The roadmap and setup files were uncommitted when the task started, so the engine records them
as pre-existing work. Updating roadmap statuses during the task would otherwise appear as unexplained changes.
**Who provides it:** The project owner (confirmation).
**Answer received:** «موافق على كله ومش فارقه تتنشر» (owner, 2026-11-22) — confirms the exclusion.
**Resolution:** Verified; recorded with `scope --exclude` for the files under `docs/roadmap/`.
