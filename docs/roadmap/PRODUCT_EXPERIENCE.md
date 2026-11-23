# Product Experience — Powerful Inside. Simple Outside.

Design of the usability, adaptive-depth experience and competitive-validation capability (brief 4, 2026-11-22).
It is a capability design like [ENGINEERING_INTELLIGENCE.md](ENGINEERING_INTELLIGENCE.md), not a parallel plan:
the features live in the phase files, the decisions in [DECISIONS.md](DECISIONS.md) (D-041–D-045), the risks in
[RISK_REGISTER.md](RISK_REGISTER.md) (R-27, R-28), the requirements in
[REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md) (B4).
The principle, D-041–D-045 and the complete Master Roadmap were owner-approved on 2026-11-23. D-044 approves an
evaluation framework, not measured improvement or product-market fit. None of these decisions authorizes software
implementation.

## 0. The principle (D-041, owner-approved)

> **Powerful Inside. Simple Outside.** The system absorbs complexity instead of passing it to the user.
> **Simplify interactions, not guarantees.**

The engineer should experience one engineering assistant that knows what has been done, what needs their attention,
why, and what happens next, not a set of engines, configurations and stages to coordinate by hand. Excessive
interaction complexity is a **product defect**. A confirmed material complexity regression blocks a release until
it is fixed or explicitly accepted by the owner with recorded rationale, risks and follow-up. Acceptance cannot
waive mandatory security, approvals, verification or other non-negotiable guarantees (D-042).

The principle never weakens INV-01–INV-22. Gates, hash-bound approvals, security checks, honest evidence, honest
optimality classes, agent independence, local-first operation and manual invocation stay exactly as they are. Only
the effort to satisfy them may shrink.

## 1. Ownership and review (D-042, owner-approved)

| What | Where |
|---|---|
| Accountable | The product owner decides at phase and release gates; feature owners record interaction impact; reviewers check the evidence |
| Per feature | Each feature spec states whether user effort changes and applies the proportional **complexity budget** (§5) |
| Per phase | The phase review re-runs the usability scenarios that apply (§7) and reviews the usability register (§10) |
| Per release | P19 release checklist: applicable UX results and complexity regressions against the last baseline are listed; an open usability blocker stops release unless the owner records acceptance with rationale, risks and follow-up. Acceptance never waives mandatory guarantees (F19.1.1) |
| Defects | The usability register (§10), `UXR-n`, which is linked from the debt and risk registers when relevant |

## 2. What the roadmap already had

This brief mostly makes existing provisions explicit, owned and measured.

| Existing provision | Where |
|---|---|
| Derive before asking; impact-filtered `questions next`; blocking only when it matters | ENGINEERING_INTELLIGENCE §8; F4.1.2, F4.4.2 |
| Adaptive depth L0–L3 with reasons and permitted user changes; depth never removes core gates | D-025, INV-18; F3.3.1–F3.3.3 |
| Approvals without fatigue: decision sets, delegation policy, assumptions | D-022, D-023; F5.2.1, F5.2.2 |
| Small fix stays light (Scenario F); scenario evals A–I | D-028; F3.4.1, F9.2.1 |
| Fit gate: ORE only for problems that can be modelled honestly | INV-22; ore/ORE_DESIGN §2 |
| Skill-only path first-class; optional modules | INV-12, R-01; F11.5.2 |
| Scope-explosion and bureaucracy risks | R-01, R-17 |
| "Next:" line in `status` and the hooks | Existing engine; F1.7.2 improves the presentation |

**Genuinely missing before this brief:** a named principle; ownership and release consequences; user-facing depth
experiences; a qualitative complexity budget per feature; product-experience metrics and baselines; effort measures
for existing scenarios; competitive validation and product-market-fit gates; a register for usability problems.

## 3. Interaction principles

| Principle | Rule | Roadmap home |
|---|---|---|
| Derive before asking | Read the project, code, approved records, decisions and configuration first. Never ask for what is already available and reliable; show derived answers so they can be corrected | F4.1.2, F4.4.1 |
| High-value questions only | Ask only questions that change the next engineering decision. Group them, order them by impact, no long questionnaires unless the task needs them. Derivable or unjustifiably repeated questions count as defects; changed evidence can justify a documented re-ask | F4.1.4 |
| Smart defaults, human decisions | Recommend defaults with reasons. Never fabricate business assumptions, constraints, measurements, approvals, costs, benchmarks or objective weights (INV-08, INV-20). Consequential decisions stay human (INV-01) | D-022/D-023; F5.2.1 |
| One clear next action | At any point, the user can see four things: what is done, what needs their attention, why it matters, and what happens after they act. The stage machine stays internal | F1.7.2, F5.5.2, F11.1.3 |
| Progressive technical detail | Present a short recommendation first, with reasoning, trade-offs, evidence, logs, proofs and advanced options on demand. Critical risks, uncertainty, limitations and mandatory approval information are never hidden | F5.5.2, F6.1.4, F11.6.x |

## 4. Adaptive workflow depth: Quick, Standard and Deep (D-043, owner-approved)

The user-facing experiences are names for the existing depth policy, not a second system. The engine recommends one
with a one-line reason from the D-025 signals: size, risk, architecture impact, data sensitivity, reversibility and
regulation. It selects and records exactly one underlying L0–L3 level. For Standard, the existing policy resolves
L1 or L2; the exact level and reason remain available on demand. A user can request a different level within
permitted policy boundaries. Permitted changes are recorded. A selection below a mandatory profile minimum, or one
that would evade security, approval or required checks, is refused with an explanation (F3.3.3–F3.3.4).

| Experience | Depth levels | Typical work | What the user sees | Never removed |
|---|---|---|---|---|
| **Quick** | L0, only when permitted by the applicable minimum | bug fix, small improvement, limited refactor | Inspect first, only essential questions, short spec and plan, no extra documents or diagrams | spec and plan approval, secret and safety checks, verification evidence, audit, outcome caps |
| **Standard** | L1 or L2, resolved and recorded by the existing policy | new feature, integration, moderately complex change | Relevant discovery, requirements and alternatives, consequential ADRs, artifacts at reasonable depth; exact level and reason available on demand | the same, plus traceability |
| **Deep** | L3 | distributed systems, architectural redesign, critical security, complex business rules | Thorough business and technical discovery, HLD/LLD and diagrams where useful, failure analysis, ORE only when the fit gate holds, stronger verification and review | the same, plus stronger review requirements |

L0–L3 stay the recorded and enforced levels. Quick, Standard and Deep are presentation choices, never a route around
mandatory policy. An impermissible depth request is refused, not silently accepted or called a completed stage.

## 5. Preventing feature overload: the complexity budget (D-045, owner-approved)

Every feature spec started after F1.7.3 states whether it adds user-visible interaction. **No new interaction**
needs one concise statement. A **small change** needs brief justification and relevant alternatives. A
**significant interaction or architectural change** receives deeper evaluation when warranted. This qualitative
review is not a numerical quota or a lengthy mandatory checklist for trivial work:
- **New user-visible surface:** commands, options, questions, records, approvals, files, configuration keys.
- **Default:** what happens when the user does nothing. Advanced behaviour stays optional and modular.
- **Who needs it** and which scenario (§7) shows its value; the simpler alternative and why it is not enough.
- **Overlap** with what the coding agent or environment already does, and the added advantage.
- **Cost:** maintenance, learning curve, performance, cognitive load.

Activation rules:
- ORE only through the fit gate (INV-22).
- Automatic multi-agent use only after comparison with a single-agent baseline (F14.7.1); without measured benefit,
  do not recommend it, and record any explicit owner decision to proceed without claiming an advantage.
- Diagrams, ADRs and long documents only when they serve an engineering decision at the chosen depth.

A low-value feature may be postponed, simplified or redesigned on measured evidence, but only through an owner
decision recorded in DECISIONS.md. Engineering quality and verification guarantees remain. **Validation findings
never silently remove an approved capability.**

## 6. Product-experience metrics (D-044)

**Baselines come first;** quantitative targets and improvement claims follow reproducible evidence (F1.7.1).
For UX-A and UX-B, use reliable existing task evidence plus the planned representative runs. Record the managing
engine version, task context, measurement method, interactions, commands, approvals, questions, time to first useful
result and record overhead. Every value is labelled **measured**, **estimated**, **assumed** or **unavailable**;
nothing is fabricated (INV-08). Comparisons use equivalent requirements, consistent environments and representative
projects, and record versions and dates. The table below is a menu of relevant measures, **not** a requirement to
collect all 14 for every feature or gate. Reuse the existing scenario fixtures and evaluation harness.

| Metric | Source (first available) |
|---|---|
| Time to first useful result | Recorded sessions and events (F1.7.1, then F2.1.2 events) |
| End-to-end task completion time | Task history timestamps |
| Number of required user interactions | Commands and approvals per task (events) |
| Number of repeated or unnecessary questions | Question ledger: re-asked or derivable keys (F4.1.4) |
| Number of approval interactions | Approval records |
| Time spent understanding workflow state | Usability sessions (observed or self-reported, labelled) |
| Documentation and configuration overhead | Record files and words per task; setup steps |
| Engineering decision quality | Scenario rubric (D-028), human review |
| Requirement coverage | Trace graph (P8) |
| Defects and regressions | Audit findings, CI, reopened tasks |
| Rework and reopened tasks | Stage moves backwards; re-approvals |
| Token and execution costs | Only when actual data is available (registry, P9); otherwise unavailable |
| User satisfaction and willingness to reuse | Usability sessions and surveys (Gate C) |
| Completion rate by task complexity | Scenario runs per experience (Quick / Standard / Deep) |

The minimum evidence at each gate is specified in §8. Cost is measured only where actual data exists. If essential
evidence is missing, report the evaluation as **insufficient or blocked** rather than passing it. An owner-approved
exception records rationale, consequences and follow-up and never presents skipped validation as completed. No
numeric target or expected improvement is invented before evidence exists.

## 7. Usability scenarios UX-A to UX-E (D-044)

The prefix `UX-` keeps them distinct from the engineering scenarios A–I (D-028) and ORE-A–ORE-M. Each scenario is
judged on two axes: **outcome quality** and **user effort** (§6 metrics).

| ID | Scenario | Pass means | Linked scenarios | First run |
|---|---|---|---|---|
| UX-A | Small bug fix | Lightweight: Quick recommended, essential questions only, no extra documents. All gates and checks still hold; outcome and effort are compared with the baseline | Scenario F with an added user-effort measure, not a second fixture | Baseline F1.7.1; eval F3.4.1 |
| UX-B | Standard feature | Discovery, plan, implementation and tests with appropriate structure; derivable or unjustifiably repeated questions are detected | Scenario A with an added user-effort measure, not a second fixture | Baseline F1.7.1; eval F4.5.1 |
| UX-C | Complex architecture | Meaningful design analysis, alternatives, traceability at Deep depth; the decision presentation stays one screen first | Scenarios B, C, G, H | Gate A (F5.6.2) |
| UX-D | ORE-eligible decision | A mathematically justified result, correctly classified (G0–G3), explained to an engineer unfamiliar with OR | ORE-A, ORE-I–ORE-M | Gate B (F6.6.3) |
| UX-E | Multi-agent engineering | Multi-agent compared with a single-agent baseline on quality, time, cost and interactions before any benefit is claimed | — | F14.7.1 |

F9.2.1 extends the existing eval harness with outcome and effort measures for scenarios available by Phase 9.
UX-E first runs in Phase 14 after manual multi-agent capability exists; earlier gates and releases record it as
unavailable. F19.1.1 re-runs only applicable scenarios in each release checklist.

## 8. Competitive validation and product-market fit (D-044)

The goal is evidence that AIDevWorkflow solves real engineering problems better than relevant alternatives, not a
completed feature list. **Feature completeness is not proof of product-market fit.**

| Gate | When | Question | Evidence | Possible outcomes |
|---|---|---|---|---|
| **A** | Before v1.5 MVP release (F5.6.2) | Do capabilities actually available by v1.5 improve engineering decisions and user effort compared with alternatives? Scope: the existing short spec/plan and approvals, plus Phase 3–5 profiles, discovery, requirements and decisions. Phase 8 expanded specs, planning and traceability are not yet available | UX-A–UX-C on equivalent tasks; a consistent evaluation method fixed before interpretation; decision quality, observed rework and user effort; named alternative, version, configuration and evidence source. Label unavailable values | Proceed · adjust priorities · simplify · redesign. Gate report, limitations and owner decision recorded |
| **B** | Before v1.6 ORE release (F6.6.3) | Does optimization add measurable practical value? | Verify ORE result correctness and solver guarantees; assess practical value and complexity (UX-D), input provenance, time and actual costs when measurable; compare with a relevant non-ORE baseline where feasible | The same. No unsupported claim of mathematical optimality without proof or sufficient solver evidence, or of practical superiority without comparison (INV-19) |
| **C** | Before the dashboard build (E11.2) and automatic-orchestration expansion (F14.3.3) (F11.0.1) | Do target users understand how to start, complete meaningful tasks with less unnecessary effort, trust the evidence, choose to reuse it, and prefer it for relevant problems? | Appropriate real-user usability study and relevant competitor comparisons using then-available capabilities; assess task initiation, completion, unnecessary interaction overhead, trust, discoverability and willingness to reuse; record participant and task limitations. Desk research alone does not satisfy the real-user requirement; UX-E is a separate Phase 14 precondition | The same. Findings can resequence, never silently remove |

UX-E (F14.7.1) compares representative multi-agent and single-agent runs on comparable tasks **after** manual
multi-agent capability exists and **before** F14.3.3 can be enabled. It records quality, time, cost and interactions
where available. No multi-agent benefit is claimed without supporting evidence. At every gate, the owner records a
decision and limitations; missing essential evidence cannot be silently treated as a pass. Paid tools, additional
costs and participant recruitment beyond the approved scope need separate owner decisions.

**Alternatives to evaluate:** GitHub Spec Kit, BMad Method, OpenSpec, Kiro, Claude Code and its agent capabilities,
GitHub Copilot and coding-agent workflows, and other relevant engineering or orchestration platforms found by the
desk study.
- **Status: not yet researched.** No capability is assumed unique until the alternatives are checked from their
  official sources.
- The desk study (F1.7.4) records, per alternative: version, date, source, what it covers, and how it was verified
  (documentation read, or hands-on). It is refreshed at each gate.
- Hands-on comparison may need paid tools or accounts. That spending is an owner decision per gate, and the core
  never depends on them (INV-14).

## 9. Where it lands in the phases

| Phase | Addition | Feature IDs |
|---|---|---|
| 1 | Usability foundations epic E1.7: baseline, concise recommendation first with details on demand, register and complexity budget, competitive desk study. TD-25 is closed; E1.7 follows F1.0.5 without changing its scope | F1.7.1–F1.7.4 |
| 3 | Quick/Standard/Deep presentation over L0–L3; UX-A measured in the existing Scenario F | F3.3.4, F3.4.1 |
| 4 | Question budget by depth; repeated or derivable questions detected; UX-B measured in the existing Scenario A | F4.1.4, F4.5.1 |
| 5 | One-screen decision presentation; Gate A | F5.5.2, F5.6.2 |
| 6 · 10 | Gate B; ORE stays context-sensitive and explained first in plain language | F6.6.3; P10 requirement 7 |
| 9 | Available usability scenarios in the existing eval harness; complexity-regression report | F9.2.1 |
| 11 | Gate C before the dashboard build; the dashboard must improve discoverability, not compensate for engine complexity; CLI/agent-only parity study | F11.0.1, F11.5.3 |
| 14 | Introduce UX-E after manual multi-agent capability; compare with a single-agent baseline before automatic orchestration | F14.7.1 |
| 16 · 17 | Customer usability in existing FDE delivery records; product-experience metrics with availability flags | F16.4.1, F17.6.1 |
| 19 | Applicable usability checks in the existing release checklist | F19.1.1 |

## 10. Usability register

The register records usability problems, complexity regressions and their follow-ups. An entry needs evidence:
**measured**, **observed** (from a real task, named) or **reported** (a user's words). Severity is **blocker**
(a confirmed material complexity regression or a critical defect against the principle), **major** or **minor**.
Materiality is judged from affected tasks, user effort, outcome quality and risk, with a recorded reason; there is
no invented numeric cutoff. A blocker stops a release unless the owner records acceptance with rationale, risks and
appropriate follow-up. That acceptance cannot waive mandatory security, approval or verification guarantees.

| ID | Problem | Evidence | Severity | Status | Follow-up |
|---|---|---|---|---|---|
| UXR-1 | Moving to the next stage needs an explicit `stage` command even when the next stage is the only valid one | Observed: task `security-td-25` recorded 12 `stage` events before implementation; `engine-api-f1-0-4` recorded 17 | Major | Open | Candidate for F1.7.2 / Phase 2 gate table: suggest or auto-advance where safe, never past an approval |
| UXR-2 | After any spec edit, `review` must restate the whole coverage map, notes and question answers | Observed: `security-td-25` recorded 5 `spec-review` events, each with the full map | Major | Open | Candidate: keep unchanged mappings and ask only for the changed IDs (Phase 2/4) |
| UXR-3 | Editing project files outside the task (for example roadmap documents) while a task is active needs `pause` and `resume` | Observed: this roadmap update (2026-11-22) | Minor | Open | Candidate: declared out-of-task paths in configuration (needs a security review, S-02/S-03) |
| UXR-4 | A behaviour-pin test was built on a defect (TD-25), so the security fix needed a test change and an owner decision | Observed: `security-td-25`, LateRefusalTest | Minor | Open | Process: pins must not depend on known-defective behaviour; noted for F9.2.x review guidelines |

## 11. Guardrails

Preserve:
- human ownership of consequential decisions;
- explicit approval gates and hash-bound approvals;
- security and privacy protections;
- accurate verification and evidence;
- honest optimality classifications;
- agent independence and local-first operation;
- backward compatibility or safe migration;
- manual invocation by default;
- use of the core without cloud services, subscriptions, dashboards or ORE.

**Simplify interactions, not guarantees.**
