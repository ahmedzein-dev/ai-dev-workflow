# Dependencies: F1.0.3 Split workflow.py into the aidw package (no behaviour change)

List every external input this task needs: designs, API contracts, data, platform constraints, decisions.
Ask only for what this task actually needs; inspect the code first.

- **Class:** Blocking (required before its gate), Non-blocking (helpful, not essential), Verified (confirmed
  with reliable evidence) or Not applicable.
- **Gate** (Blocking only): the stage it stops — `spec`, `plan`, `implementation` or `completion`.
- **Type:** ui, backend, data, platform, security, third-party, decision, environment or other.

| ID | Type | Class | Gate | Owner | Summary |
|----|------|-------|------|-------|---------|
| DEP-1 | decision | Verified | | Project owner | Commit the F1.0.2 work before implementation starts, so this refactor's diff is reviewable on its own (workflow.py already has uncommitted F1.0.2 edits) |
| DEP-2 | decision | Verified | | Project owner | Standing rule: `docs/roadmap/` files are outside every task's scope (approved once for F1.0.2 as DEP-3) |

<!-- One row per dependency, for example:
| DEP-1 | backend | Blocking | spec | Backend developer | Response shape for GET /favorites |
If the task needs nothing external, replace the table with this line:
No dependencies identified — <reason>.
-->

## Details

### DEP-1 — Commit F1.0.2 first

**Why it matters:** The task baseline recorded 46 files with uncommitted changes, including `workflow.py` (F1.0.2 lint
edits). Without a commit, this refactor's changes to `workflow.py` mix with F1.0.2's in `git diff`, which makes the
audit harder. Not blocking: `scope` still separates them by content hash.
**Who provides it:** The project owner (commit permission; the agent never commits on its own).
**Answer received:** «Approved all and you do the commit» (owner, 2026-11-22) — the agent commits F1.0.2 on a new branch, no push.
**Resolution:** Verified; commit made before implementation.

### DEP-2 — Roadmap files outside task scope

**Why it matters:** Roadmap statuses are updated alongside every task; a standing rule avoids asking each time.
**Who provides it:** The project owner.
**Answer received:** «Approved all and you do the commit» (owner, 2026-11-22).
**Resolution:** Verified; standing rule written to `.ai-dev-workflow/PROJECT.md`, applied with `scope --exclude`.

<!-- One section per dependency, for example:

### DEP-1 — Favorites list response

**Why it matters:** Which requirement depends on it.
**Who provides it:** The person or team who must answer.
**Message to send:**
```text
A ready-to-forward message: the feature context, the exact missing information, specific questions,
and a request for example payloads or responses.
```
**Answer received:** Paste the answer, or "Waiting since <date>".
**Resolution:** What changed in the spec, and the dependency's new Class.
-->
