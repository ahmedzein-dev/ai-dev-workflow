# Engineering Intelligence Layer — design proposal

Deliverable of the strategic integration (brief 2, 2026-11-22). It designs how AIDevWorkflow moves from
spec-driven development to **business-driven, decision-driven, architecture-aware** engineering, without becoming a
bureaucratic workflow and without claiming that the engine can judge engineering quality by itself.

> **AI proposes, engineers decide, the workflow preserves the reasoning, and evidence verifies the result.**

Decisions marked **D-nnn** are listed in [DECISIONS.md](DECISIONS.md) for approval.

## 1. Where the intelligence lives

The engine does not become an AI. Intelligence comes from the agent, guided by curated engineering knowledge and
held to account by structured records. Each layer has one job:

| Layer | Holds | Judges semantics? | Changes need |
|---|---|---|---|
| **Workflow core** (engine) | State, modes, gates, approvals, records, links, evidence, depth policy | **No.** Verifies completeness, links, versions, approvals and evidence | Core release |
| **Engineering domain profiles** (data) | Discovery topics, questions, decision triggers, considerations, trade-offs, spec sections, diagrams, verification needs, failure cases | No (read by agents; a few fields are enforced as policy) | A profile file |
| **Technology adapters** (data) | Detection, commands, output formats, manifests | No | An adapter file |
| **Agent instructions** (skill) | How to discover, question, decide, design, challenge, explain | Agent does | Skill release |
| **Project knowledge** (records) | Objectives, requirements, constraints, assumptions, Q&A, ADRs, components, diagrams, estimates, research, outcomes | — | Normal workflow |

Separation from brief 2 §1, made concrete: *Node.js* is an adapter; *Backend engineering* is a profile; the core
knows neither. A project activates several profiles at once (for example backend + distributed systems + AI + cloud
+ forward-deployed).

## 2. Architecture

```
            Developer ─ chat (agent) · aidev CLI · dashboard
                               │
 Agent instructions ──────────┤  discovery · questioning · decisions · design · mentor overlay · research labelling
                               ▼
 Engine API ── modes & gate table ── approvals (gate · decision set · requirement baseline · delegated · assumption)
      │                 │
      │                 ├── depth policy (L0–L3 → required artifacts per mode)
      │                 └── conflict rules (decision vs mandatory requirement) · staleness propagation
      ▼
 Engineering record store  (.ai-dev-workflow/engineering/ — project level, persistent across tasks)
   objectives · requirements · constraints · assumptions · questions · decisions (ADRs) · components ·
   diagrams · estimates · research · outcomes · links  →  trace graph · RTM · impact queries
      ▲
 Registries: domain profiles (data) · technology adapters (data) · diagram linters · (later) plugins
      ▲
 Task records (.ai-dev-workflow/tasks/<task>/) — spec, plan, evidence, audit, report — reference project records by ID
```

Project-level records are new: today everything lives inside a task. Decisions, requirements and architecture
outlive tasks, so they get a project-level home that tasks reference (this pulls a slice of the project knowledge
base forward, as the brief anticipated).

## 3. Record model (proposal, D-021)

Storage follows the engine's existing pattern: **Markdown documents with labelled fields** (already parsed by the
engine's `Doc` model) for anything people read and approve, **JSON Lines written only by the engine** for logs, and
**generated Markdown views** for humans (like the checks block in `verification.md`). No database, no YAML parser
(standard library only).

| Record | ID | Stored as | Key fields |
|---|---|---|---|
| Objective | `OBJ-n` | `engineering/objectives.md` | statement, stakeholders, success metrics (baseline, target, type: expected/measured), priority |
| Requirement | `REQ-n` | `engineering/requirements.md` | kind (functional / non-functional), category (performance, availability, …), statement, **measurable target** (metric, target, unit, window, conditions), priority (must/should/could), source (`OBJ`, `Q`), status, verification refs |
| Constraint | `CON-n` | `engineering/constraints.md` | statement, kind (business, technical, legal, budget, team), source, hard/soft |
| Assumption | `ASM-n` | `engineering/assumptions.md` | statement, confidence, why assumed, validation plan, review trigger, status (open / confirmed / invalidated) |
| Question | `Q-n` | `engineering/questions.jsonl` (engine-written) + `questions.md` view | key (profile topic), text, why, type (requirement / preference / constraint / assumption / decision), impact, needed-by gate, status (open / answered / derived / assumed / deferred / superseded), answer (text, by user or derived, source quote or file:line), follow-ups, contradicts |
| Decision (ADR) | `ADR-nnnn` | `engineering/decisions/ADR-nnnn-<slug>.md` + frozen `approved/` snapshots | all fields of brief 2 §5: status, context refs, problem, requirements, constraints, assumptions, alternatives table, criteria (only user-approved weights), trade-offs, AI recommendation, human decision + evidence quote, rationale, consequences, risks, mitigations, reversibility, validation (spike/PoC/test), related components/diagrams, version, SHA-256, reconsider-when triggers, supersedes/superseded-by |
| Component | `CMP-n` | `engineering/components.md` | name, responsibility, data owned, interfaces, state (as-is / proposed / approved / implemented), code paths (globs) |
| Diagram | `DGM-n` | `engineering/diagrams/DGM-n-<slug>.mmd` + index | type (C4 context, sequence, ERD, …), state (as-is / proposed / approved / implemented), version, SHA-256, depicts (`CMP`), decisions (`ADR`), requirements, last validated |
| Estimate | `EST-n` | `engineering/estimates/EST-n.md` | inputs (value, unit, source: confirmed / assumed / measured), formulas, outputs — **recomputed by the engine** (safe arithmetic, no `eval`) |
| Research | `RES-n` | `engineering/research/RES-n.md` | question, findings each labelled **fact / assumption / estimate / recommendation / unknown**, sources (URL, title, retrieved date) |
| Outcome | `MET-n` | `engineering/outcomes.md` | metric, baseline, target, actual, type (expected / measured), source, measured at |

Every record that matters can carry `refs:` to other IDs; the engine builds the trace graph from those references
and from existing links (spec `FR`→`REQ` via `review --map`, plan steps → files via `step`, checks → fingerprints,
audit findings → files).

## 4. The engineering flow and its relationships

```
Business discovery ─▶ OBJ ─▶ REQ (FR + measurable NFR) ◀─ CON · ASM
                                  │ decision triggers (profiles) + conflicts
                                  ▼
                       ADR (alternatives → trade-offs → recommendation → human decision)
                                  │
                                  ▼
                CMP + DGM (HLD) ─▶ LLD (interfaces, schema, contracts, state machines)
                                  │
                                  ▼
             Spec (task) ─▶ Plan (task) ─▶ Code (steps) ─▶ Evidence (checks, matrix) ─▶ Audit ─▶ Outcome (MET)
```

Rules the core enforces (all checkable without semantic judgement):

1. A plan can be approved only if every decision it cites is **Approved** and current (hash unchanged).
2. An approved decision that cites a requirement or constraint becomes **Needs re-evaluation** when that
   requirement or constraint changes; dependent plans lose validity until it is re-approved or explicitly kept.
3. A decision recorded as conflicting with a **must** requirement cannot be approved until the requirement is changed
   (with its own approval) or the decision is changed. The agent detects conflicts; the engine refuses to let a
   recorded conflict pass silently (brief 2 §4, Scenario H).
4. Superseded decisions are never deleted; the history of the architecture stays readable.
5. Diagrams linked to a changed decision or component are flagged **stale**.

## 5. Approvals without approval fatigue (D-022)

| Approval type | Examples | How it is given | Integrity |
|---|---|---|---|
| **Gate** | spec, plan; in other modes: design package, review report, proposal | Explicit user words for that version (unchanged rule) | SHA-256 + snapshot |
| **Decision set** | 1–N related consequential ADRs | One explicit approval covering a listed set; each ADR hashed separately | SHA-256 per ADR |
| **Requirement baseline** | objectives, NFR targets, constraints | Approved together with the spec (feature mode) or the discovery summary (other modes) | SHA-256 of the baseline section |
| **Delegated decision** | internal naming, a library inside the approved stack, local refactor shape | Agent records it under the project's delegation policy; listed in the next gate presentation; user can veto | Recorded; covered by the next gate approval |
| **Assumption** | provisional capacity figures, unknown answers | Accepted as an assumption with a review trigger; listed at every gate until confirmed | Recorded |
| **Override** | skip stages | Existing `pause --reason` rule | Recorded; never shown as completed |

What makes a decision **consequential** (needs explicit approval): hard to reverse, crosses components, affects
data, security, cost or a public contract, conflicts with a requirement, or is marked "always consequential" by an
active profile (for example database selection, authentication model, payment flow). Everything else may be
delegated, but only within a written policy the user approved (D-023).

## 6. Workflow modes (D-024)

Modes generalize today's single lifecycle using the declarative gate table (Phase 2). Existing tasks become mode
`feature`, with no change in behaviour.

| Mode | Stages (gates in **bold**) | Main deliverables | Done when |
|---|---|---|---|
| `feature` (today) | Discovery → Dependencies → Specification → **Spec approval** → Planning → **Plan approval** → Implementation → Testing ⇄ Fixing → Audit → Report | spec, plan, code, evidence, audit, report | `outcome` allows the reported status |
| `full` | `feature` with business discovery, requirements and design stages switched on by depth | + objectives, requirements, decisions, HLD/LLD | as `feature`, plus decisions and design approved |
| `decision` | Frame → Options → Evaluate (optional spike) → **Decision approval** → Record | one or more ADRs, research, spike results | ADR approved, rejected or deferred with rationale |
| `system-design` | Business discovery → Requirements → **Requirement baseline** → Decisions (**decision sets**) → HLD → LLD → Diagrams → **Design approval** → Design review → Report | requirements, ADRs, capacity estimates, HLD, LLD, failure analysis, diagrams | design package approved and reviewed; **no code expected** |
| `architecture-review` | As-is discovery → Analysis → Findings → Options → **Review approval** → Report | as-is diagrams, findings, debt, options, improvement plan | report approved |
| `business-discovery` | Stakeholders → Problem & workflows → Objectives & metrics → Solution options → **Proposal approval** → Report | objectives, success metrics, solution proposal | proposal approved |
| `fde` (forward deployed) | business-discovery → system-design (scaled) → PoC (**PoC criteria approval**) → Integration → UAT → Pilot → **Delivery approval** → Handover → Impact | + PoC results, integration validation, runbooks, handover, measured outcomes | delivery accepted; outcomes recorded as expected vs measured |

**Mentor overlay** (not a mode): `explain: brief | standard | deep`, stored in the task, read by the agent. It adds
explanations, comparisons and diagrams; it never lets the agent take consequential decisions.

## 7. Adaptive engineering depth (D-025)

At the start of every task the agent proposes a depth level with reasons; the user sees it with the first gate and
can raise or lower it within applicable policy. The engine records the resolved level and enforces its artifacts.
An impermissible change is refused with an explanation. **Depth never removes the core gates.**

| Level | Typical work | Requires (feature mode) |
|---|---|---|
| L0 Trivial | typo, copy change, config value | short spec + plan, checks, report |
| L1 Standard | feature inside the existing architecture | + affected requirements, impact notes, relevant profile questions |
| L2 Significant | new integration, data model change, shared component | + measurable NFRs that apply, consequential ADRs, as-is/proposed diagram where helpful, failure cases |
| L3 Critical | payments, bookings, auth, distributed or regulated systems | + HLD/LLD, capacity estimates, failure analysis, security review, validation strategy (spike or load test where claims need it) |

Signals: size, complexity, business and technical risk, architecture impact, data sensitivity, components affected,
reversibility, production impact, regulation. Profiles can force a minimum level for paths or topics (for example any
change under `payments/` is at least L2). A requested level below a mandatory profile minimum is refused; a level
below non-mandatory risk signals but within policy is shown as a warning at the gate.

Users see the levels as three experiences (D-043, [PRODUCT_EXPERIENCE §4](PRODUCT_EXPERIENCE.md)): **Quick** = L0,
**Standard** = L1 or L2 as resolved by the existing policy, **Deep** = L3. The single resolved L0–L3 level is
recorded and enforced; its reason remains accessible. No second depth state machine is introduced.

## 8. Adaptive questioning (brief 2 §3)

The engine supplies structure; the agent supplies judgement.

- **Question banks** come from active profiles: each topic has a key, the question, why it matters, its type, impact,
  the gate that needs it, what evidence could answer it (files, configs), and follow-ups.
- **Derive before asking**: the agent answers what the code and records show and records it as `derived` with the
  file and line; the user sees derived answers and can correct them.
- **`questions next`** (engine) proposes the next batch: open, needed by the next gate, highest impact, grouped by
  topic, excluding answered and deferred keys.
- **Unknown answers**: the agent explains why it matters, gives realistic options with effects and a recommendation;
  the user picks one, accepts an assumption (with a review trigger) or defers it.
- **Question budget** (F4.1.4): the chosen experience limits unnecessary non-blocking questions without an
  arbitrary count; derivable or unjustifiably repeated questions are defects. A changed source may justify a
  documented re-ask (PRODUCT_EXPERIENCE §3).
- **Blocking only when it matters**: a question blocks its gate only if marked needed-by that gate with high impact;
  everything else proceeds with recorded assumptions.
- **Contradictions**: the engine flags structured ones (two answers for one key, a requirement contradicting a
  constraint by recorded refs); the agent is instructed to look for semantic ones.
- **Hand-over**: the ledger is in the repository, so any agent can continue the discussion.

## 9. Engineering domain profiles (D-026)

A profile is a folder of data: `profile.json` (metadata, applicability signals, topics, decision triggers, minimum
depth rules, spec section suggestions, diagram recommendations, verification requirements, failure cases) plus
Markdown guides (considerations, trade-off guides, patterns). Built-in profiles ship with the skill; projects add or
override profiles in `.ai-dev-workflow/profiles/` without touching the core.

| Profile | First version | Later |
|---|---|---|
| `generic` (any domain, the fallback) | v1.3 | — |
| backend, mobile, frontend | v1.3 | refinements |
| cloud-devops, ai-engineering, distributed-systems, data-engineering, security | v1.3–v1.4 | refinements |
| fde (forward deployed) | discovery topics v1.4; delivery v4 | — |
| database, embedded, desktop, game, sdk-library | community / later | — |

Profiles are references, not checklists: the agent records which topics applied, which did not and why (the same
pattern as today's advisory questions).

## 10. Diagrams (D-027)

- **Mermaid first**: plain text, diffable, rendered by GitHub, IDEs and the dashboard, no install needed. C4 via
  Mermaid's C4 syntax, with Structurizr DSL and PlantUML as optional renderers later (they need Java or other tools).
- **Source of truth is the text file in git**; SVG/PNG are generated views, never the only copy.
- **States**: as-is, proposed, approved, implemented. Approved diagrams are hash-bound like other approved documents.
- **Engine checks** (standard library): the file declares a supported diagram type; referenced component IDs exist;
  linked decisions are current; stale flags after changes. Full syntax validation uses Mermaid's CLI when present
  (optional, never required).
- **No invented components**: every box in an approved diagram maps to a `CMP` record or an external system record.

## 11. Measuring the quality of questions, recommendations and decisions (D-028)

The engine cannot prove a recommendation is good. We measure it with **scenario evals**, labelled honestly:

| Layer | What | Cost | When |
|---|---|---|---|
| Deterministic record checks | After an agent run on a scenario fixture: required topics asked or derived, forbidden questions not asked (derivable), required decision categories recorded with ≥ 2 real alternatives, conflicts detected, depth within the expected range, trace links complete | Free, in CI on recorded runs | Every phase from P4 |
| Human rubric | Reviewer scores relevance, missing considerations, trade-off quality, sycophancy (did it challenge a bad choice?) | Reviewer time | Per release |
| Model-graded rubric (optional) | Same rubric graded by a model, with consent for the cost | Paid API use, opt-in only | Optional |

Scenario fixtures A–I from brief 2 §18 become the eval suite, each with expected properties (for example Scenario F:
depth ≤ L1, no HLD, no ADR; Scenario H: decision blocked until the conflict is resolved). Results are recorded with
agent, model and version, like the compatibility report today.

## 12. Change classification (brief 2 §20.3)

| Capability | Core | Profiles / data | Instructions | Optional module | Plugin later |
|---|---|---|---|---|---|
| Domain profiles, question banks, decision triggers | registry + policy fields | ✔ | ✔ | | custom profiles |
| Business discovery, Q&A ledger | ledger, `questions next`, contradictions (structured) | topics | ✔ | dashboard views | |
| Requirements with measurable NFRs | records, baseline approval | categories | ✔ | | |
| Decisions, trade-offs, ADRs | records, approvals, batching, conflict rule, staleness | triggers, trade-off guides | ✔ (partner behaviour) | decision center UI | |
| Modes | gate table per mode | | ✔ | | custom modes (policy) |
| Adaptive depth | depth policy | minimum-depth rules | ✔ | | |
| System design (HLD, LLD, capacity, failure analysis) | records, estimate recompute | ✔ | ✔ | | |
| Diagrams | registry, lint, staleness | recommendations | ✔ | renderers | PlantUML / Structurizr |
| Traceability, RTM, impact queries | trace graph, `trace` | | | dashboard explorer | |
| Engineering audit | new dimensions as data | verification needs | ✔ | | audit rules |
| Research labelling | claim-type field | | ✔ | | research fetchers |
| FDE delivery, business impact | outcome records | fde profile | ✔ | delivery pack | |
| Evals | — | scenarios | | eval harness | model grader |

## 13. What the engine will never claim

It verifies that records are complete, linked, versioned, approved and backed by evidence. It does **not** verify that
a design is good, a trade-off is right or a requirement is true. Those are human and agent judgements, recorded with
their reasons, reviewed in the audit, and measured by evals.
