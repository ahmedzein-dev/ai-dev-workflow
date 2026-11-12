# Specification templates and rules

AIDevWorkflow does not ship a mandatory template. Every project uses its own, chosen during setup:

- a template file in the repository,
- a template from your private library (`install.py add-template`),
- or the generic [example template](../examples/templates/example-spec-template.md), only if you pick it.

`init` copies the chosen template into `.ai-dev-workflow/templates/`, so every agent and machine uses the same
version, and each task records the template's hash. `spec.md` starts as a verbatim copy of the template; the agent
fills it in without restructuring it.

## Three kinds of rules

| Kind | Effect | Examples |
|---|---|---|
| **Mandatory** | Blocks approval; checked automatically | template headings in order, every field present, no placeholder left, IDs unique and in order, "Given … when … then …" acceptance criteria, complete edge-case rows, fields that need content, no unresolved blocking dependency |
| **Judgment** | Blocks approval until the agent records a review for this spec version; the user's approval confirms it | "every requirement is testable", "every edge case has a specific behavior", "proposed structures are based on the inspected code" |
| **Advisory** | Warning only | common edge cases to consider, "name the required tests", "Out of scope says None" |

Without a rules file, only the structure derived from the template applies (headings, fields, placeholders, open
`TBD`/`TODO` markers). A rules file adds the rest.

**No numeric limits.** Do not encode minimums or maximums for requirements, edge cases, exclusions or acceptance
criteria. A spec is as detailed as the feature needs; the agent never pads it to reach a number and never splits a
feature because of its size.

**Classify by the template's own language.** What your template or its guide defines as mandatory becomes a
mandatory or judgment rule; recommendations, questions and tips become advisory warnings.

## Rules file format

Put the rules next to the template as `<template>.rules.json` (or pass `--rules` to `init`). The full schema is in
[`skills/ai-dev-workflow/assets/rules.schema.json`](../skills/ai-dev-workflow/assets/rules.schema.json); the example
template's rules are a complete, working example:
[`examples/templates/example-spec-template.rules.json`](../examples/templates/example-spec-template.rules.json).

```json
{
  "schema": 1,
  "id_prefixes": ["REQ", "EC", "AC"],
  "patterns": [
    {"id": "M-ac-form", "target": "ids:AC", "regex": "^Given .+?, when .+?, then .+",
     "message": "write acceptance criteria as: Given …, when …, then …."}
  ],
  "tables": [{"id": "M-edge-cases", "id_prefix": "EC", "message": "every edge case needs a specific behavior."}],
  "content_required": [{"target": "ids:REQ"}, {"target": "label:Not included", "allow_none": true}],
  "verification": {"ids": ["AC", "EC"], "checklist_label": "Definition of done", "checklist_prefix": "DW"},
  "judgment": [
    {"id": "J1", "rule": "Every requirement is specific and testable",
     "detectors": [{"type": "vague-words", "target": "ids:REQ"}]},
    {"id": "J3", "rule": "Proposed structures are based on the inspected project", "requires_note": true,
     "detectors": [{"type": "inspected-files"}]},
    {"id": "J4", "rule": "Every requirement is verifiable", "detectors": [{"type": "coverage-map", "of": "REQ"}]}
  ],
  "advisory": [
    {"id": "A1", "type": "questions", "questions": {"offline": "No network connection"}},
    {"id": "A2", "type": "none-entry", "target": "label:Not included", "message": "List what readers might assume."}
  ]
}
```

### Targets

| Target | Means |
|---|---|
| `label:<field>` | The block after a bold field such as `**Goal:**` (matched by its start, case-insensitive) |
| `section:<heading>` | The section under a heading that starts with this text |
| `ids:<PREFIX>` | Every bold list item `**PREFIX-n:**` (or table row whose first cell is `PREFIX-n`) |
| `table:<PREFIX>:<column>` | One column (0-based) of the table rows whose first cell is `PREFIX-n` |

### Judgment detectors

| Detector | Flags | Resolve by |
|---|---|---|
| `vague-words` | items containing words such as "fast", "properly", "handles the error" (configurable with `words` or top-level `vague_words`) | rewording, or dismissing with a reason |
| `inspected-files` | no inspected files recorded for the task | `workflow.py discover <task> --inspected …` |
| `coverage-map` | requirements not mapped to acceptance criteria, edge cases, checklist items or named tests | `workflow.py review <task> --map REQ-1=AC-1` |

`requires_note: true` makes the agent state the basis when it marks the rule reviewed (for structures: the existing
code each proposal follows).

### Advisory types

`questions` (the agent records each as covered by an EC or not relevant), `label-mentions` (warn when a field lacks
certain words), `none-entry` (warn when a field says None), `prompts` (reminders shown with the check).

## Writing rules for your own template

1. Start from the example rules file.
2. Set `id_prefixes` to your template's ID families.
3. Turn every requirement your template or its guide states as mandatory into a `patterns`, `tables` or
   `content_required` entry, or a judgment rule if it needs judgment.
4. Turn recommendations into `advisory` entries.
5. Check it against a filled-in example spec: `workflow.py spec-check <task>`.

## Architecture in specs

The agent inspects the existing architecture and proposes the structures a change needs, citing the code each one
follows. You review them in the spec and plan; you are never asked to write class or use-case names yourself.
