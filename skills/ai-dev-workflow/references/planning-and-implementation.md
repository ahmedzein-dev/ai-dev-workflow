# Planning and implementation

## Planning (stage 5)

Start only after the spec approval is recorded and nothing blocks the plan. Inspect the code the change will touch;
the plan must describe this repository, not generic assumptions.

Write `plan.md` from its template:

1. **Goal** — what is being implemented.
2. **Current Behavior** — how the relevant functionality works today, citing the files you read.
3. **Proposed Solution** — the recommended approach and why; each proposed structure with the existing code or
   pattern it follows.
4. **Affected Areas** — modules, screens, services, repositories, models and other components, with paths.
5. **Implementation Steps** — an ordered list `- **S1:** …`, `- **S2:** …`, each naming the FR and EC IDs it
   implements.
6. **Important Technical Decisions** — alternatives, trade-offs, the recommendation.
7. **Edge Cases** — how failures and variations are handled.
8. **Testing Plan** — which tests and checks prove each AC, EC and checklist item.
9. **Risks and Dependencies** — security, compatibility, shared code, delivery.
10. **Expected Result** — what works afterwards.

The plan must be easy to read, specific to this codebase, consistent with the approved spec and the project's
standards, technically realistic, focused on the agreed scope, and detailed enough to catch mistakes before coding.
Skip theory. When several approaches are valid, explain the meaningful trade-offs and recommend one.

For a small change, the plan may be drafted while the spec awaits approval and presented together with it (the fast
path in SKILL.md); each approval is still recorded separately.

Run `plan-check <task>`, move to PLAN_APPROVAL, and present the plan with its version and short hash. Silence,
discussion or clarifying questions are not approval. Record the explicit approval with
`approve <task> plan --evidence "<their words>"`; the task moves to IMPLEMENTATION and the plan is frozen. If the
user changes the plan, edit it, re-check, and ask again.

## Implementation (stage 7)

1. Run `preflight <task>` (in Claude Code with `--session ${CLAUDE_SESSION_ID}`). Do not edit code until it passes.
2. If the project has an analyzer check, capture its baseline before the first edit:
   `run <task> <analyzer-check> --baseline`. Issues that already exist are then reported separately from new ones.
3. Implement the approved steps in order. After each, run `step <task> S<n> done`; files changed since the last
   checkpoint are attributed to that step automatically.

Follow, in this order of authority: the approved spec, the approved plan, the project's engineering standards, and the
established architecture and conventions. Existing code is the truth about current behavior, but not automatically
correct architecture; do not copy violations.

- **Reuse before creating.** Search for existing classes, widgets, components, utilities, services and repositories
  before adding new ones.
- **Preserve behavior** the spec does not change. No unrelated refactoring.
- **No new dependencies** unless the plan includes them and the user approved them; record that approval with
  `decision`. Check the template's constraints as well (for example "no new packages without approval").
- **Impact analysis before changing shared code**: other features, application flows, shared state and services,
  authentication, navigation, data models, platform behavior. One file does not mean an isolated change. When the
  task spans several repositories or apps, check those dependencies too.
- **Verify incrementally**: run targeted checks as you go; do not wait until the end to find integration errors.

### When reality differs from the plan

If you find a significant missing requirement, a wrong assumption, or a necessary architectural change:

1. stop the affected work;
2. explain what you found;
3. say what has to change;
4. explain the impact on the spec and the plan;
5. move back (`stage <task> SPECIFICATION|PLANNING --reason …`) and get renewed approval.

Never expand the approved scope silently.

### Repository safety

Preserve unrelated local changes; never overwrite another person's work; never silently revert files. Check `scope`:
files that had uncommitted changes before the task are listed separately and must survive intact. Never commit, merge,
push, deploy, publish or run other irreversible operations unless the user explicitly asks.

### Project tools and other skills

Use the project's own commands and tools (code generators, formatters, linters) as the plan and standards require.
Other skills that write code may be used only during IMPLEMENTATION or FIXING and only for approved steps;
review-only skills may help during AUDIT.
