# AIDevWorkflow — Master Roadmap

**Structured AI-Assisted Software Engineering Platform — From Requirements to Release.**
One roadmap for all four owner briefs: product evolution (B1), engineering intelligence (B2), the Operations
Research & Optimization Engine (B3), and product simplicity with competitive validation (B4).

> *AI understands. Science optimizes. Engineers decide. Architecture guides. Evidence verifies. Business measures success.*
> *AI proposes, engineers decide, the workflow preserves the reasoning, and evidence verifies the result.*
>
> **Powerful Inside. Simple Outside.** The system absorbs complexity instead of passing it to the user;
> simplify interactions, not guarantees (D-041, [PRODUCT_EXPERIENCE.md](PRODUCT_EXPERIENCE.md)).

> **Coming back after a break?** Read [PROGRESS.md](PROGRESS.md) first, then the current phase in [phases/](phases/),
> then open items in [DECISIONS.md](DECISIONS.md). [roadmap.html](roadmap.html) is the visual view. No chat history is
> needed.

## 1. Where we are

| | |
|---|---|
| Current phase | **Phase 1 — Foundations & universal technology support: in progress** (F1.0.1–F1.0.4 done) |
| Approved | The complete revised Master Roadmap and D-041–D-045 (owner, 2026-11-23), including the proportional validation framework. Approval of an evaluation plan is not a claim of demonstrated benefit; ORE integration (D-031–D-040) remains approved |
| Managing engine | Verified user-level AIDevWorkflow v1.0.1 from the published tag; `main` contains the TD-25 security fix, while `main` and `phase-1/foundations` also contain unreleased development work |
| Remaining TD-25 limits | F-9 detection limitation remains Deferred; TD-29 (multi-file persistence) and TD-30 (internal writer boundary) remain open separately. See TECHNICAL_DEBT and the closed task report |
| Next action | TD-25 is closed — Completed with Limitations. Use the approved roadmap to prepare F1.0.5 through the normal task workflow; implementation has not started. E1.7 follows it within Phase 1 |

## 2. Invariants (hold in every phase)

| ID | Invariant |
|---|---|
| INV-01 | The developer makes the final decision, not the AI. |
| INV-02 | The skill runs only on explicit invocation by default. |
| INV-03 | Outside the workflow, every agent works normally. |
| INV-04 | The workflow engine is the single source of truth; no front end duplicates its rules. |
| INV-05 | Task state never depends on chat memory. |
| INV-06 | A task can start in one agent and continue in another. |
| INV-07 | Approvals are kept and bound to the approved version with SHA-256. |
| INV-08 | No invented approvals, test results, benchmarks, measurements, prices, weights, ROI or business results. |
| INV-09 | No implementation before the required approvals. |
| INV-10 | Explicit user overrides are recorded; skipped stages are never claimed as completed. |
| INV-11 | Project files and user changes outside the task's scope are preserved; no commit, push, merge or deployment without explicit permission. |
| INV-12 | The skill stays usable on its own, without dashboard, orchestrator, ORE or cloud services. |
| INV-13 | Local-first and privacy-first. |
| INV-14 | Core capabilities never require subscriptions, external services or commercial solvers. |
| INV-15 | Backward compatibility with existing projects, or a clear and safe migration. |
| INV-16 | The existing code stays MIT-licensed; nothing is re-licensed implicitly. |
| INV-17 | The engine verifies records, links, approvals and evidence; it never claims to prove that a design or decision is right. |
| INV-18 | Depth scales the process to the task, but never removes the core approval gates. |
| INV-19 | **No proof of optimality, no claim of optimality.** Optimal means optimal for the approved model and data, never "best in reality". |
| INV-20 | Hard constraints are never relaxed and soft-constraint weights never set without the engineer's approval. |
| INV-21 | Only the verifier classifies optimization results; agents and LLM text are never proof. |
| INV-22 | Problems are modelled only when the fit gate holds; qualitative decisions stay in engineering analysis. |
| INV-23 | **Powerful Inside. Simple Outside.** The engine absorbs complexity; every feature justifies the interaction it adds; excessive interaction complexity is a product defect. Simplification never weakens INV-01–INV-22. |

## 3. Phases at a glance

MVP = the first usable version of the engineering-intelligence vision (v1.5, D-030). ORE's first usable version is
v1.6 (D-040). Effort is rough (one developer with an AI agent).

| Phase | Name | Target | Status | Effort |
|---|---|---|---|---|
| [0](phases/PHASE_00.md) | Audit, assessment & strategic integrations (B2, B3) | — | Done | done |
| [1](phases/PHASE_01.md) | Foundations & universal technology support | v1.1 | In progress | 7–10 wk |
| [2](phases/PHASE_02.md) | Core engine: records, modes, approvals, security & recovery | v1.2 | Planned | 7–9 wk |
| [3](phases/PHASE_03.md) | Engineering domain profiles & adaptive depth · MVP | v1.3 | Planned | 5–7 wk |
| [4](phases/PHASE_04.md) | Business discovery, requirements & adaptive questioning · MVP | v1.4 | Planned | 5–6 wk |
| [5](phases/PHASE_05.md) | Engineering decisions, trade-offs & ADRs · MVP complete | v1.5 | Planned | 5–7 wk |
| [6](phases/PHASE_06.md) | **ORE foundations: modeling, exact solving & strict optimality** | v1.6 | Planned | 7–9 wk |
| [7](phases/PHASE_07.md) | Workflow modes, system design & diagrams | v2.0 | Planned | 7–9 wk |
| [8](phases/PHASE_08.md) | Intelligent specs, planning & end-to-end traceability | v2.1 | Planned | 5–6 wk |
| [9](phases/PHASE_09.md) | Engineering audit, verification, evals & performance registry | v2.2 | Planned | 6–7 wk |
| [10](phases/PHASE_10.md) | **ORE advanced: multi-objective, scenarios, certificates & applications** | v2.3 | Planned | 8–10 wk |
| [11](phases/PHASE_11.md) | CLI, dashboard, decision center & ORE views | v3.x | Planned | 2 + 9–13 wk |
| [12](phases/PHASE_12.md) | Git, GitHub & parallel development | v3.x | Planned | 5–7 wk |
| [13](phases/PHASE_13.md) | Project intelligence & architecture evolution | v3.x | Planned | 6–8 wk |
| [14](phases/PHASE_14.md) | Multi-agent orchestration & ORE agent/model allocation | v4.x | Planned | 4 (+6–10) wk |
| [15](phases/PHASE_15.md) | Plugin ecosystem incl. solver adapters | v4.x | Planned | 6–8 wk |
| [16](phases/PHASE_16.md) | Forward deployed engineering & delivery (incl. ORE for FDE) | v4.x | Planned | 6–8 wk |
| [17](phases/PHASE_17.md) | Engineering analytics & business impact | v3.x basic · v5.x full | Planned | 1–2 + 4–6 wk |
| [18](phases/PHASE_18.md) | Team collaboration & enterprise (study first) | after v4 | Future | 2–3 wk study |
| [19](phases/PHASE_19.md) | Production readiness & release (incl. ORE validation matrix) | every release | Planned | continuous |

## 4. Order and dependencies (D-020, D-031)

```
P0 ─▶ P1 foundations + universal tech ─▶ P2 core: records · modes · approvals · security                  v1.1–v1.2
     ─▶ P3 profiles + depth ─▶ P4 discovery + requirements ─▶ P5 decisions + ADRs                         v1.3–v1.5 ◀ MVP
     ─▶ P6 ORE foundations (models · exact solving · strict optimality · limits · evidence)               v1.6      ◀ ORE v1
     ─▶ P7 modes + system design + diagrams ─▶ P8 specs/plans + traceability ─▶ P9 audit + evals + registry  v2.0–v2.2
     ─▶ P10 ORE advanced (Pareto · scenarios · certificates · applications · model selection)             v2.3
     ─▶ P11 CLI + dashboard + decision center + ORE views ∥ P12 git ∥ P13 project intelligence             v3.x
     ─▶ P14 multi-agent + ORE allocation ∥ P15 plugins + solver adapters ∥ P16 FDE (+ ORE for FDE)          v4.x
     ─▶ P17 analytics + business impact ─▶ P18 team (study first)                                           v5.x
P19 release checklist, security, tests, migration and docs: part of every phase and release.
```

How brief 3's ORE phases 0–11 were merged (one roadmap, not a parallel plan):

| Brief 3 ORE phase | Master placement | Why |
|---|---|---|
| 0 Research & feasibility | Phase 0 (desk study now) + F6.0.2 spike | Decide solvers on evidence before building |
| 1–5 Model, solvers, strict optimality, resource safety, decision integration | **Phase 6** | Needs records, approvals, trust store and process runner (P2), questions (P4) and ADRs (P5); resource limits ship with the first solver run, as the brief requires |
| 6–8 Multi-objective, scenarios, applications | **Phase 10** | Applications need capacity models and designs (P7), traceability (P8) and eval data (P9) |
| 9 Model & agent optimization | Registry in **P9**, model selection in **P10**, agent allocation in **P14** | Allocation needs measured data and the orchestrator |
| 10 Dashboard | **P11** | With the other dashboard work |
| 11 Extensibility & production validation | **P15** (solver adapters) and **P19** (validation matrix) | With plugins and release readiness |

ORE is **not** in the v1.5 MVP: the MVP proves the engineering loop first, and ORE needs a solver spike. ORE's own first
usable version (v1.6) follows immediately and needs no third-party install (built-in exact enumerator).

## 5. Versions (D-029 as amended by D-040)

| Version | Contents |
|---|---|
| v1.1 · v1.2 | Foundations and universal technology support · core records, modes, approvals, security |
| v1.3 · v1.4 · **v1.5 MVP** | Profiles and depth · discovery and requirements · decisions and ADRs |
| **v1.6 ORE v1** | Declarative models, exact enumerator, optional solver, strict optimality, verification, limits, evidence |
| v2.0 · v2.1 · v2.2 · v2.3 | Modes and system design (records v1 engines cannot read → major) · specs, plans, traceability · audit, evals, registry · ORE advanced |
| v3.x · v4.x · v5.x | Dashboard, git, project intelligence · multi-agent, plugins, FDE · analytics, team |

**Validation gates (D-044).** A version ships only after its gate report and the owner's recorded decision:
**Gate A** before v1.5 (F5.6.2: value of capabilities shipped by that milestone, excluding Phase 8's expanded
specification, planning and traceability), **Gate B** before v1.6 (F6.6.3: ORE's practical value), **Gate C** before
the dashboard build and automatic orchestration (F11.0.1: real-user usability and product-market fit using then
available scenarios and required real-user evidence). UX-E is a separate Phase 14 precondition for automatic orchestration. Each gate requires proportional evidence, honest availability labels, a report of limitations and the owner's recorded decision; missing essential evidence is insufficient or blocked rather than a silent pass. Findings can resequence
or simplify work through a recorded decision; they never silently remove an approved capability. Feature
completeness is not proof of product-market fit.

## 6. How we develop AIDevWorkflow with AIDevWorkflow

1. A pinned install of the latest release manages every task here (D-005); the working copy never manages itself.
2. Each feature (F-ID) is one AIDevWorkflow task with spec and plan approvals (D-016). F1.0.2 was the first.
3. After each task: checks, full regression suite, independent audit, docs, roadmap status from recorded evidence.
4. A phase review approved by the owner opens the next phase.
5. Progress counts features closed with evidence, never estimated percentages.

## 7. Documents

| File | Purpose |
|---|---|
| [PROGRESS.md](PROGRESS.md) | Where we are, baseline, log |
| [ENGINEERING_INTELLIGENCE.md](ENGINEERING_INTELLIGENCE.md) | Engineering-intelligence layer (B2) |
| [PRODUCT_EXPERIENCE.md](PRODUCT_EXPERIENCE.md) | Powerful Inside. Simple Outside.: usability, Quick/Standard/Deep, metrics, UX scenarios, validation gates, usability register (B4) |
| [ore/](ore/) | ORE design (B3): [ORE_DESIGN](ore/ORE_DESIGN.md) · [MATHEMATICAL_MODEL_SCHEMA](ore/MATHEMATICAL_MODEL_SCHEMA.md) · [STRICT_OPTIMALITY_POLICY](ore/STRICT_OPTIMALITY_POLICY.md) · [SOLVER_COMPARISON](ore/SOLVER_COMPARISON.md) · [SECURITY_AND_THREAT_MODEL](ore/SECURITY_AND_THREAT_MODEL.md) · [VALIDATION_STRATEGY](ore/VALIDATION_STRATEGY.md) |
| [REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md) | Requirements of all four briefs mapped |
| [TARGET_ARCHITECTURE.md](TARGET_ARCHITECTURE.md) | Engine architecture, alternatives, migration, overall architecture (§7) |
| [CURRENT_ARCHITECTURE.md](CURRENT_ARCHITECTURE.md) · [GAP_ANALYSIS.md](GAP_ANALYSIS.md) | Phase 0 audit (uses brief-1 phase numbers; see §9) |
| [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) · [RISK_REGISTER.md](RISK_REGISTER.md) | Living registers |
| [DECISIONS.md](DECISIONS.md) | Decisions and approvals |
| [phases/](phases/) · [roadmap.html](roadmap.html) | Phase plans 0–19 · interactive view |

## 8. Overall architecture

See [TARGET_ARCHITECTURE.md §7](TARGET_ARCHITECTURE.md#7-overall-architecture-after-the-three-integrations-brief-3-24-simplified):
one engine with logical components; ORE, dashboard and orchestrator are optional modules; the core never depends on them.

## 9. Phase numbering history

| Brief 1 (first plan) | After brief 2 (D-020) | Now (D-031) |
|---|---|---|
| 0, 1, 2 | 0, 1, 2 | 0, 1, 2 |
| — | 3, 4, 5 (new) | 3, 4, 5 |
| — | — | 6 (new, ORE foundations) |
| — | 6, 7, 8 (new) | 7, 8, 9 |
| — | — | 10 (new, ORE advanced) |
| 3 CLI/dashboard | 9 | 11 |
| 4 Git | 10 | 12 |
| 5 Project intelligence | 11 | 13 |
| 6 Multi-agent | 12 | 14 |
| 7 Plugins | 13 | 15 |
| — | 14 FDE (new) | 16 |
| 8 Analytics | 15 | 17 |
| 9 Team | 16 | 18 |
| 10 Release | 17 | 19 |
