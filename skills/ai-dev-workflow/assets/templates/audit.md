# Audit: [Task title]

**Review independence:** [independent agent | subagent | separate session | second pass]
**Reviewer:** [agent and version, e.g. codex 0.166]
**Reviewed scope:** [the files from `workflow.py scope`, the recorded evidence, and the approved spec and plan]

## Dimensions

- **A. Specification compliance:** [Does the change meet every FR, EC and AC?]
- **B. Architecture compliance:** [Layer boundaries, dependency rules, project patterns.]
- **C. Code quality:** [Complexity, duplication, dead code, fragile assumptions.]
- **D. Security and privacy:** [Authentication, authorization, input validation, logging, sensitive data.]
- **E. Edge cases:** [Missing or mishandled cases.]
- **F. Regression risk:** [Existing behavior that could break.]
- **G. Test adequacy:** [Do tests cover the important behavior and failure paths?]
- **H. Scope compliance:** [Unapproved additions or omitted requirements.]
- **I. Reliability and performance:** [Async behavior, network handling, lifecycle, resources, retries.]

## Project standards checklist

[The result for each applicable item in the project's standards files and the PROJECT.md audit checklist.]

## Findings

Severity is Critical, Important or Minor. Disposition is Open, Fixed (and re-verified), Accepted (quote the
user's words in Notes) or Deferred (Minor only). If the review found nothing, write the line
"No findings." instead of table rows.

| ID | Severity | Dimension | Finding | Location | Disposition | Notes |
|----|----------|-----------|---------|----------|-------------|-------|

## Remediation log

[What was fixed, which checks were re-run, and their results.]
