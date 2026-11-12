# Audit and final report

## The audit is its own stage (stage 10)

Passing tests do not prove the change is complete or architecturally sound. Review the final code against the
approved spec, the approved plan, the project's standards files and the `PROJECT.md` checklist, established patterns,
engineering practice and the recorded evidence.

**Independence.** Prefer a reviewer that did not write the code:

- Claude Code: a read-only subagent (for example a general-purpose agent instructed to only read files, run
  `git diff` and run checks), given the task folder and `scope` output, not your summary.
- Any agent: a separate session of the same or a different agent, invoked with the skill
  (for example `$ai-dev-workflow audit <task>` in Codex after implementing in Claude Code).
- If neither is possible, do an explicit second pass yourself and record `second pass`.

The reviewer inspects the actual changes (`scope`, `git diff`) and evidence, not the implementer's description. Never
claim an independent review that did not happen.

## Dimensions

| | Question |
|---|---|
| A. Specification compliance | Does the change satisfy every requirement, edge case and acceptance criterion? |
| B. Architecture compliance | Are layer boundaries, dependency rules and project patterns respected? |
| C. Code quality | Unnecessary complexity, duplication, fragile assumptions, dead code? |
| D. Security and privacy | Authentication, authorization, input validation, logging, sensitive data? |
| E. Edge cases | Cases missing, mishandled or untested? |
| F. Regression risk | Could existing behavior break? |
| G. Test adequacy | Do tests cover the important behavior and failure paths? |
| H. Scope compliance | Unapproved additions, omitted requirements? |
| I. Reliability and performance | Async behavior, network handling, lifecycle, resources, retries, recovery? |

Then go through the project's own standards (only the rules relevant to this change) and record the result in
"Project standards checklist".

## Findings

| Severity | Meaning |
|---|---|
| Critical | Wrong or unsafe behavior: a mandatory requirement not met, a security or data-loss risk, a crash in a main path |
| Important | A real defect or standards violation that should be fixed before release |
| Minor | Polish or a small improvement that does not affect correctness |

For each confirmed issue, record the problem, the affected code, its impact and its severity. Then:

- **Fixed**: fix in-scope defects (FIXING → TESTING, re-run the affected checks), then re-evaluate.
- **Accepted**: only when the user explicitly accepts leaving it; quote their words in Notes.
- **Deferred**: Minor findings only.

If a fix would change the approved scope or needs a new architectural decision, ask the user first. Never hide an
unresolved finding.

## Final status

Run `outcome <task>`. It computes the highest status the evidence supports; you may report a lower one, never a
higher one, and the report must explain why it is not higher.

| Status | Requires |
|---|---|
| Completed | every plan step done; every AC, EC and checklist item Passed with evidence; every required check passed on the current code; every Critical and Important finding Fixed and re-verified; nothing Not Verified or Blocked; Minor findings only if listed |
| Completed with Limitations | nothing Failed; every Not Verified or Blocked item has a stated reason; pre-existing problems listed; Important findings may be Accepted by the user; no Critical finding open or accepted |
| Partially Completed | anything weaker: a Failed item, an open or accepted Critical finding, an open Important finding, unfinished steps |
| Blocked | work cannot continue; name the blocker and who must act |

Accepting a known Critical or Important finding never yields Completed.

## Final report (stage 11)

Write `report.md` (keep it readable in about a minute, without hiding problems):

1. **Overall Status** — `**Status:**` followed by exactly one status, and why.
2. **What Was Implemented** — the functionality and the main components changed.
3. **Specification Compliance** — matches the approved spec? Failed, blocked or unverified items.
4. **Testing Results** — what ran, passed, failed, could not run; coverage limits.
5. **Code Audit** — Critical, Important and Minor findings and how each ended; unresolved violations. If none:
   "No issues were identified within the reviewed scope."
6. **Edge Cases and Regression Risks**.
7. **Pending Dependencies** — anything waiting on the user, backend, design, API changes, configuration or more
   testing; otherwise say nothing is pending.
8. **Next Actions** — only what is necessary.

Then `close <task>`. In chat, give a short summary of the report; the stored files are the record. Every claim must be
backed by the recorded evidence; separate what was verified from what was assumed or not checked.
