# Dependencies: F1.0.4 Engine API: commands return data, the CLI only prints

List every external input this task needs: designs, API contracts, data, platform constraints, decisions.
Ask only for what this task actually needs; inspect the code first.

- **Class:** Blocking (required before its gate), Non-blocking (helpful, not essential), Verified (confirmed
  with reliable evidence) or Not applicable.
- **Gate** (Blocking only): the stage it stops — `spec`, `plan`, `implementation` or `completion`.
- **Type:** ui, backend, data, platform, security, third-party, decision, environment or other.

| ID | Type | Class | Gate | Owner | Summary |
|----|------|-------|------|-------|---------|
| DEP-1 | decision | Verified | — | Project owner | Engine structure and the API layer: D-001 (foundations epic) and D-002 (stdlib `aidw` package, `workflow.py` entry point) accepted on 2026-11-22; TARGET_ARCHITECTURE §2–3 places the API in `aidw/api.py` |
| DEP-2 | platform | Verified | — | Project owner | F1.0.3 (the package split this builds on) is committed and passed CI on Linux, Windows and macOS with Python 3.9 and 3.13 (`tests` runs at `3837bb2`, `6188b29`) |
| DEP-3 | decision | Verified | — | Project owner | Standing rule in PROJECT.md: roadmap files under `docs/roadmap/` are outside every task's scope and are excluded with `scope --exclude` |

## Details

### DEP-1 — Approved structure

**Why it matters:** FR-1 and the layer rule follow the approved architecture instead of a new design.
**Who provides it:** The project owner (DECISIONS.md, «موافق على كله و قالب المواصفات الخاص بيا», 2026-11-22).
**Answer received:** Accepted.
**Resolution:** Verified; no question needed.

### DEP-2 — Base commit verified

**Why it matters:** The refactor starts from code whose behaviour is pinned by golden tests on three operating systems.
**Who provides it:** CI on GitHub Actions.
**Answer received:** All jobs passed.
**Resolution:** Verified.

### DEP-3 — Roadmap files out of scope

**Why it matters:** The roadmap is updated alongside the task without counting as task changes.
**Who provides it:** The project owner («Approved all and you do the commit», 2026-11-22).
**Answer received:** Recorded in PROJECT.md.
**Resolution:** Verified.
