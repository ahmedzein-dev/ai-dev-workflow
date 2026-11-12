# Specification and spec approval

## Writing the spec (stage 3)

`spec.md` starts as a verbatim copy of the project's template (`spec_template` in `config.json`). Fill it in; never
replace or restructure it. Keep every heading and field in the template's order. Where the template allows, capture:
purpose, expected behavior, functional requirements, applicable non-functional requirements, business rules, user
interactions, technical dependencies, error handling, edge cases, constraints, acceptance criteria and explicit
exclusions. Do not add unrelated requirements.

**As detailed as the feature needs, no more and no less.** There are no minimum or maximum counts for requirements,
edge cases, exclusions or acceptance criteria. Never pad a spec to reach a number, and never split a feature only
because it has many requirements. Split only when the user agrees the scope is really several features.

**Identifiers and traceability.** Use the template's IDs (for example FR-1, EC-1, AC-1), unique and in order. They
connect requirement → plan step → test → audit finding. Record coverage with `review --map`: every requirement maps
to the acceptance criteria, edge cases, checklist items or named tests that will verify it.

**Architecture.** Do not ask the user to design the code. Inspect the existing architecture first, then propose the
structures the change needs (classes, use cases, components, layers), each based on the existing code or pattern it
follows, and let the user review them in the spec and the plan. Never propose structures without having read the
relevant code (record what you read with `discover --inspected`).

**Missing information.** Unclear behavior goes back to discovery or becomes a dependency. Never fill a gap with a
guess. `TBD`, `TODO` and `???` block approval.

## Checking the spec

Run `spec-check <task>`. The checks come from the template itself plus the template's rules file
(`spec_rules` in `config.json`), and fall into three groups:

- **Mandatory** (block approval): the template's structure (headings in order, every field present), no template
  placeholder left, IDs unique and in order, required formats (for example acceptance criteria written as
  "Given …, when …, then …"), complete edge-case rows, sections that must have content, and no unresolved dependency
  that blocks the spec. These are checked automatically.
- **Judgment rules** (block approval until reviewed): rules that need judgment, such as "every requirement is
  testable". The engine flags likely problems (vague words, a requirement no test covers, no recorded inspection). Fix
  each flag, or dismiss it with a real reason; then mark each rule reviewed for this version:

  ```
  workflow.py review <task> --map FR-1=AC-1,EC-2 --map FR-2=test:"favorites list test" \
      --pass J1 --pass J2 --pass J3 --note J3="follows the existing <file or pattern>" --pass J4
  workflow.py review <task> --dismiss "J1:FR-3:fast" "FR-3 cites a measured target (300 ms), not a vague claim"
  ```

  The tool proves the review happened, not that it was right; the user's approval confirms it.
- **Advisory** (warnings only): recommendations and questions from the template's guide, such as common edge cases to
  consider. Record your decision on each question (`review --question offline=EC-3` or
  `--question offline=n/a:<reason>`); do not add an edge case only to silence a warning.

Without a rules file, only the structural checks apply.

Before presenting, review the spec yourself for: missing requirements, ambiguity, contradictions, unresolved
blocking dependencies, important unhandled edge cases, acceptance criteria that cannot be verified, and conflicts with
the project's standards.

## Presenting the spec (stage 4)

Move to SPEC_APPROVAL (`stage <task> SPEC_APPROVAL`; it re-runs the checks). Present:

- the version and short hash (for example "spec v2 · 3f9a1c0e");
- the spec itself, or a summary with the full file path if it is long;
- the `spec-check` summary, including advisory warnings and the structures you propose with their basis;
- open decisions the user must make.

Ask for an explicit decision: "Reply 'approve the spec' to approve spec v2 (3f9a1c0e), or tell me what to change."
Only an explicit approval of this version counts. Record it:

```
workflow.py approve <task> spec --evidence "<the user's exact words>"
```

If the user asks for changes, edit `spec.md`, re-run `spec-check` and `review`, and present the new version.

## Conflicting project instructions

If the project's instructions contradict each other on something this task touches: name the conflicting rules,
explain the practical impact, recommend a resolution, and ask the user if it matters for this task. Record the decision
with `decision <task> …` and, if it applies project-wide, in `.ai-dev-workflow/PROJECT.md`. Never silently pick a side
or change a standard. If existing code violates a standard, do not copy the violation. A conflict that does not affect
the task is noted, not raised as a blocker.
