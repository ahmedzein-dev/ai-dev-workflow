# Discovery and dependencies

## Discovery (stage 1)

Do not write code. First understand what the user wants to achieve.

Inspect, as far as the task needs:

- the user's request and anything they attached;
- the project's specification template and engineering standards (`standards` in `config.json`, `PROJECT.md`);
- the relevant existing code, related features and their patterns;
- existing business rules, API clients, data models and tests;
- `git status`: which files already have uncommitted changes (they are not yours).

Answer for yourself:

1. What problem are we solving?
2. What outcome does the user expect?
3. What should the end user experience?
4. What existing behavior must stay unchanged?
5. What is in scope?
6. What is explicitly excluded?
7. Which modules or systems may be affected?
8. What important information is missing?

**Questions.** Ask only what materially affects the spec or the implementation and cannot be answered by reading the
code. Keep questions short, group related ones, never repeat a question the user already answered. Never silently
invent requirements, business rules, UI behavior or backend behavior; if something is unclear, clarify it before
relying on it.

Record the result:

```
workflow.py discover <task> --inspected <path> <path> … --summary "<goal, scope, exclusions, affected areas>"
```

## Dependencies (stage 2)

Work out exactly which external information, resources or decisions this task needs. This is not a fixed
questionnaire: request only what this task actually needs, and nothing the code already answers.

Record each one in `dependencies.md`:

| Field | Values |
|---|---|
| Type | ui, backend, data, platform, security, third-party, decision, environment, other |
| Class | **Blocking** (required before its gate), **Non-blocking** (helpful, not essential), **Verified** (confirmed with reliable evidence), **Not applicable** |
| Gate | for Blocking items, the stage it stops: `spec`, `plan`, `implementation` or `completion` |
| Owner | who must provide it: the user, the backend developer, design, … |

If nothing external is needed, write `No dependencies identified — <reason>.` instead of the table.

### UI and UX

If the change touches UI, decide whether it needs Figma designs, screenshots, existing design references, images or
other assets, interaction specifications, responsive layout rules, or platform-specific behavior. Also identify the
loading, empty, error, success, disabled and selection states, navigation behavior, accessibility requirements, and
localization or right-to-left needs that apply.

If required design information is missing, ask for it. If you cannot open a supplied Figma file, ask for screenshots
or exports. Never present your own design decisions as approved. If existing components and established patterns
already cover the need, reuse them without asking for a new design.

### Backend and API

Inspect the existing API code and documentation first. Then decide which of these are actually unclear for this
task: endpoint paths, HTTP methods, authentication, authorization, request parameters, request payloads, response
models, error codes, validation, pagination, sorting and filtering, WebSocket or realtime events, realtime
synchronization, file uploads, state transitions, idempotency, retry behavior, backward compatibility.

Never fabricate endpoints, fields, response shapes or backend behavior, and never substitute guessed contracts or mock
responses for real requirements. A prototype using clearly labelled mock contracts is allowed only if the user
approves it separately, and it is never presented as a production integration.

When backend information is missing, write a ready-to-forward message in the dependency's section under
`**Message to send:**`, and show it to the user in a copyable block:

```text
Hi <name>,

We're implementing <feature> in <app>: <one or two sentences of context>.

To finish the spec we need:
1. <specific question, e.g. "Which endpoint returns the user's favorites, and is it paginated?">
2. <specific question>

Could you share an example request and response for <endpoint>, including the error responses (status codes and
body) for <cases>?

Thanks!
```

Then stop at that dependency's gate and wait. When the user brings the answer: paste it under
`**Answer received:**`, check it for contradictions and gaps, decide whether every blocking question is answered,
update the spec, change the Class to Verified with the evidence, and ask follow-up questions only if necessary.

### Other dependencies

Only when they apply: database changes and migrations, third-party SDKs, payments, device permissions, security
requirements, push notifications, background services, Android or iOS constraints, deep links, feature flags,
analytics and monitoring, environment configuration, compatibility requirements, external service behavior.

## When something blocks the work

Say it plainly, starting with a status line, then four points:

```
BLOCKED — Awaiting backend API contract

Missing: the response shape and error codes for GET /favorites.
Why it matters: FR-3 and EC-2 depend on it; the spec cannot be approved without it.
Who provides it: the backend developer (message ready above).
Next: once you paste their answer, I'll update the spec and continue.
```
