# Dependencies: TD-25: keep secret-like check ids and agent names out of task records

List every external input this task needs: designs, API contracts, data, platform constraints, decisions.
Ask only for what this task actually needs; inspect the code first.

- **Class:** Blocking (required before its gate), Non-blocking (helpful, not essential), Verified (confirmed
  with reliable evidence) or Not applicable.
- **Gate** (Blocking only): the stage it stops — `spec`, `plan`, `implementation` or `completion`.
- **Type:** ui, backend, data, platform, security, third-party, decision, environment or other.

| ID | Type | Class | Gate | Owner | Summary |
|----|------|-------|------|-------|---------|
| DEP-1 | security | Verified | — | Engine (infra/secrets.py) | Detection uses the existing scanner (`find_secrets`, `assert_no_secrets`) unchanged; no new patterns |
| DEP-2 | environment | Verified | — | This session | The defect reproduces with a synthetic token on the current engine and on the pinned v1.0.0 |
| DEP-3 | decision | Verified | — | Owner | Scope and priority: «open a separate task to investigate and fix TD-25, including both unredacted fields (check ID and agent name) … Do not implement it without approval.» Scope additions found in discovery (the session id) are put to the owner in the spec and decided at SPEC_APPROVAL |

## Details

### DEP-1 — Secret detection

**Why it matters:** FR-1 to FR-4 refuse values the existing scanner flags; the fix must not invent a second
definition of "secret".
**Resolution:** Verified by reading `aidw/infra/secrets.py`; the patterns and the placeholder rule stay as they are.

### DEP-2 — Reproduction

**Why it matters:** The regression tests must fail before the fix.
**Evidence (2026-11-22, synthetic value `ghp_` + 36 × `A`, a scratch repository outside this one):**
- `run t1 <value> -- true`: the value is in the verification.md check block; state.json refused and unchanged.
- `run t1 smoke --agent <value> -- true`: the value is in the check block (Agent column); state.json refused.
- `resume t1 --agent <value>` and `AI_DEV_WORKFLOW_AGENT=<value> resume t1`: the value is in `ACTIVE`; state.json
  refused, so the task stays paused while `ACTIVE` names it.
- `new t2 --agent <value>`: the value is in `ACTIVE`; the folder `tasks/t2/` exists with five record files and no
  state.json, and a later `new t2` refuses with "already exists; resume it", which cannot work.
- `resume t1 --session <value>`: the value is in `ACTIVE` and the command **succeeds** (state.json does not hold the
  session).
- The pinned engine v1.0.0 behaves the same for the check id.

### DEP-3 — Owner's scope decision

**Answer received:** quoted in the table. **Resolution:** the spec lists the session id as a proposed addition for
approval.
