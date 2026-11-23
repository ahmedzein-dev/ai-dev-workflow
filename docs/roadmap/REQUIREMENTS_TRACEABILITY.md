# Requirements Traceability Matrix — all briefs

Every requirement from the four owner briefs, mapped to where it is covered, so nothing was lost when they were
merged into one roadmap. **B1** = full product evolution. **B2** = engineering intelligence, system design,
business-driven architecture. **B3** = Operations Research & Optimization Engine (ORE). **B4** = product simplicity, usability and competitive validation ("Powerful Inside. Simple Outside."). All 2026-11-22. Section numbers
follow each brief.

Status: **Exists** (in v1.0.0, kept) · **Done** (completed with evidence) · **In progress** · **Planned** (phase and
feature named) · **Process** (handled by how we develop) · **Reconsidered** (changed on purpose; reason linked).

Coverage check: 0 requirements without a home. Reconsidered items: 6 (all with reasons in GAP_ANALYSIS §3, DECISIONS or ore/ORE_DESIGN §0).

## B1 — Rules, scope and process

| ID | Requirement | Covered by | Status |
|---|---|---|---|
| B1-R01–R16 | The 16 non-negotiable rules (developer decides; explicit invocation; normal agents outside; engine as source of truth; no chat memory; cross-agent; SHA-256 approvals; no fake results; no implementation before approval; recorded overrides; preserve user work; skill usable alone; local/privacy first; no forced subscriptions; backward compatibility; MIT) | INV-01–INV-16 in MASTER_ROADMAP §2; checked in every spec, plan and audit | Exists / Process |
| B1-R17 | No unnecessary complexity; every technical decision has a reason and trade-offs | TARGET_ARCHITECTURE §1; DECISIONS | Process |
| B1-TA | Technology-agnostic: any language, framework or domain; new technology without core change | P1 E1.1–E1.4, F1.2.5, F1.6.2; P3 profiles for domains | Planned |
| B1-P0 | Phase 0 audit items (15) and outputs (9) | P0 F0.1.1–F0.2.2 | Done |
| B1-P1.1 | Detection engine: languages, frameworks, package managers, build/test tools, databases, architecture, monorepos, CI, instruction files, available tools; evidence and confidence | F1.1.1–F1.1.3 | Planned |
| B1-P1.2 | Technology adapters: detection, build, test, analysis, lint, format, dependency, security, integration, e2e checks, output parsers, quality gates; suggest, never auto-run untrusted commands | E1.2, E1.3; F2.6.2 trust store | Planned |
| B1-P1.3 | Generic custom adapter without Python changes | F1.2.5, F1.3.3 | Planned |
| B1-P1.4 | Universal spec system by task type; custom templates kept; gates unchanged | E1.5; extended by F8.1.1 | Planned |
| B1-P1.5 | Multi-technology projects | E1.4 | Planned |
| B1-P1-AC | Proof on mobile, backend, frontend, full-stack, CLI, IaC and unsupported-technology projects; adapter without core change | F1.6.1, F1.6.2 | Planned |
| B1-P2.1 | Core modules (state machine, approvals, policy, tasks, evidence, scope, registries, config, audit, events) | F1.0.3, F1.0.4, F2.1.1, F2.1.2, F2.7.1; agent registry F14.1.1 | In progress (F1.0.2 done) |
| B1-P2.2 | Layered enforcement: agent hooks, preflight, git hooks, CI, scope, protected records, document integrity, change detection | E2.2, E2.4, F2.6.2 | Planned |
| B1-P2.2b | Optional isolated execution environments | Documented guidance only | Reconsidered (GAP_ANALYSIS §3) |
| B1-P2.3 | Independent approval mechanism with trust levels | E2.3 (A0–A3), D-008 | Planned |
| B1-P2.4 | Checkpoints, recovery, atomic writes, locking, corruption detection, safe migration | F1.0.5, E2.4 | Planned |
| B1-P2.5 | Evidence integrity (fingerprint, commit, command, exit code, time, environment, tool versions; staleness rules) | E2.5 | Planned |
| B1-P2.6 | Threat model; prevented vs detected | E2.6; RISK_REGISTER §3 | Planned |
| B1-P2-AC | Bypass tests (stages, approvals, state, commands, stale evidence) | F2.6.3 | Planned |
| B1-P3.1 | Professional CLI | E11.1; user-operated approvals earlier in F2.3.1 | Planned |
| B1-P3.2–3.4 | Local dashboard, approval center, modern bilingual RTL design | E11.2–E11.4 | Planned |
| B1-P3.5 | Same core for CLI and dashboard; technology comparison; optional install | D-009, F11.2.1, F11.5.2 | Planned |
| B1-P4.1–4.4 | Git integration, parallel tasks, conflict detection, GitHub integration | E12.1–E12.4, D-017 | Planned |
| B1-P5.1 | Project knowledge base | F2.7.1 (record store), F13.1.1 | Planned |
| B1-P5.2 | ADRs | E5.1 (moved earlier, B2 §5) | Planned |
| B1-P5.3 | Impact analysis | F8.3.1 (record level), F13.3.1 (code level) | Planned |
| B1-P5.4 | Continuous knowledge update | F13.4.1 | Planned |
| B1-P5.5 | Context optimization | F13.5.1 | Planned |
| B1-P5.5b | Vector database / embeddings | Only on measured need | Reconsidered (brief allows) |
| B1-P6.1–6.2 | Agent adapters with real capabilities; specialised roles | F14.1.1, F14.2.1 | Planned |
| B1-P6.3 | Execution modes: single, manual multi-agent, automatic (optional, off by default), custom | F14.3.1, F14.3.3, F15.2.1; D-011 | Planned |
| B1-P6.4–6.6 | Independent audit; orchestration reliability; privacy and cost consent | F14.4.1, F14.3.3, F14.5.1 | Planned |
| B1-P7 | Plugin types, management, custom policies (cannot weaken core), SDK | F15.1.1–F15.3.1; declarative extension earlier (E1.2, E3.1) | Planned |
| B1-P8 | Task, agent and quality metrics; analytics views; no invented data | F17.1.1–F17.4.1 | Planned |
| B1-P9 | Team, enterprise, editions, licensing study | F18.1.1–F18.3.1 | Planned |
| B1-P10 | Testing strategy, cross-platform, technology and agent matrices, distribution, documentation, CI/CD | F19.1.1–F19.6.1; release checklist from v1.1 (D-019) | Planned |
| B1-S3 | Target architecture | TARGET_ARCHITECTURE.md; ENGINEERING_INTELLIGENCE §2 | Done |
| B1-S4 | Engineering principles | TARGET_ARCHITECTURE §1 | Process |
| B1-S5 | Develop AIDevWorkflow with AIDevWorkflow; phase records; per-task checks, audit, docs; no phase jump without approval | D-005, D-016, MASTER §6 (F1.0.2 ran this way) | In progress |
| B1-S6 | Roadmap files and interactive HTML | docs/roadmap/, roadmap.html | Done |
| B1-S7 | Versioning strategy | MASTER §5 (revised by D-029) | Done |
| B1-S8 | Phase 0 deliverables (13 items) | Phase 0 | Done |

## B2 — Engineering intelligence

| ID | Requirement | Covered by | Status |
|---|---|---|---|
| B2-1a | All engineering domains (system design … SDKs); list not limiting | P3 profiles, generic fallback F3.2.1 | Planned |
| B2-1b | Separate technology adapters, domain profiles and workflow core | ENGINEERING_INTELLIGENCE §1; E1.2 vs E3.1 vs core | Planned |
| B2-1c | Several profiles per project | F3.1.2 | Planned |
| B2-2a | Business context discovery (problem, users, model, rules, journeys, goals, success metrics, MVP vs future, failure impact, budget) | F4.2.1, F4.2.2 | Planned |
| B2-2b | Technical context discovery (existing system, architecture, team, technologies, integrations, data, environment, scale, security/legal, budget) | F4.2.2 (+ detection E1.1) | Planned |
| B2-2c | Functional requirements, rules, actors, flows, edge cases | F4.3.1; existing spec edge cases | Planned |
| B2-2d | Non-functional requirements as measurable targets; proposed values explained; nothing invented | F4.3.2 | Planned |
| B2-3a | Adaptive questioning: derive from code/docs/decisions, ask by domain and stage, impact order, batches, follow-ups, contradictions, requirement/preference/constraint/assumption/decision, now vs later, explain why, no repeats, surface missed requirements | E4.1, F4.4.1; ENGINEERING_INTELLIGENCE §8 | Planned |
| B2-3b | Unknown answers: why, options, effects, recommendation, assume or defer | F4.4.2 | Planned |
| B2-3c | Block only for consequential gaps | F4.1.2 (needed-by gate + impact) | Planned |
| B2-3d | Ledger any agent can continue | F4.1.1 | Planned |
| B2-4a | 14-step decision process | F5.1.1, F5.1.2 | Planned |
| B2-4b | Decision categories (project-dependent) | Profile decision triggers F3.2.2–F3.2.3; F5.2.1 | Planned |
| B2-4c | Trade-off evaluation with relevant criteria; no arbitrary scoring; sourced numbers; spikes/PoCs; no "best in absolute" | F5.1.2, F5.4.2 | Planned |
| B2-4d | Human decides; AI as engineering partner that challenges | F5.5.1 | Planned |
| B2-4e | Consequential vs delegable decisions; batch approvals | F5.2.1, F5.2.2; D-022, D-023 | Planned |
| B2-4f | Conflicts with mandatory requirements never accepted silently | F5.2.3 | Planned |
| B2-5a | ADR fields (26) and states (7) | F5.1.1, F5.1.2 | Planned |
| B2-5b | Never delete old decisions; architecture history | F5.3.3, F13.2.1 | Planned |
| B2-5c | Requirement/constraint change → re-evaluation | F5.3.2 | Planned |
| B2-5d | Approved decisions inside versioning and approval integrity | F2.7.2 | Planned |
| B2-6.1 | Requirements analysis for system design | E4.3, F7.1.1 | Planned |
| B2-6.2 | Capacity estimation with inputs, formulas, assumptions; growth vs confirmed vs measured | F7.2.3 | Planned |
| B2-6.3–6.4 | HLD and LLD, kept separate | F7.2.1, F7.2.2 | Planned |
| B2-6.5 | Distributed-systems analysis only when justified | F7.2.5 | Planned |
| B2-6.6 | Failure analysis with handling and tests | F7.2.4 | Planned |
| B2-7a | Backend, mobile, frontend profiles | F3.2.2 | Planned |
| B2-7b | Cloud & DevOps, AI engineering profiles (plus distributed, data, security) | F3.2.3 | Planned |
| B2-7c | Each profile's ten elements; references, not checklists; add/customise without core change | F3.1.1, F3.1.3 | Planned |
| B2-8a | FDE customer discovery (early) | F3.2.3 (fde-discovery), E4.2, F7.1.3 | Planned |
| B2-8b | FDE solution design | F16.2.1 | Planned |
| B2-8c | PoC discipline (PoC vs prototype vs MVP vs production) | F16.3.1 | Planned |
| B2-8d | Customer delivery | F16.4.1 | Planned |
| B2-8e | Business impact, expected vs measured, no invented ROI | F16.5.1, F17.5.1 | Planned |
| B2-9a | Diagram types (22), chosen by need | F7.3.1, F7.3.5 | Planned |
| B2-9b | Diagram rules: components, relationships, protocols, sync/async, ownership, boundaries, failures, trust; no invented components; as-is/proposed/approved/implemented | F7.3.2, F7.3.4 | Planned |
| B2-9c | Formats: Mermaid first, editable source in git; PlantUML, Structurizr, SVG, PNG, HTML optional | D-027, F7.3.1, F7.3.5 | Planned |
| B2-9d | Diagram lifecycle (generate, update, link, version, embed, audit, staleness, syntax) | F7.3.1–F7.3.4, F9.1.1 | Planned |
| B2-10 | Architecture-, domain- and business-aware specs; custom templates kept; companion documents; quality by coverage | F8.1.1, F8.1.2 | Planned |
| B2-11 | Plans built on approved spec, decisions, HLD, LLD, code, standards; extended sections; consistency check; reopen protocol | F8.2.1–F8.2.3 | Planned |
| B2-12 | End-to-end traceability and the example questions | F2.7.3, F8.3.1–F8.3.3 | Planned |
| B2-13 | Workflow modes (full, system design, architecture review, technical decision, feature, business discovery, FDE) and mentor overlay with levels | D-024, F5.4.1, F7.1.1–F7.1.4, F16.1.1, F5.5.1 | Planned |
| B2-14 | Adaptive engineering depth; never bypasses core gates | E3.3 | Planned |
| B2-15 | Knowledge and research: profiles, guides, patterns, ADRs, research evidence; official sources; facts vs assumptions vs estimates vs recommendations vs unknowns; no model training; core verifies records, not semantics | F3.2.4, F2.7.1 (`RES`), F5.1.2; ENGINEERING_INTELLIGENCE §13 | Planned |
| B2-16 | Dashboard enhancements (18 views) and actions through the core | E11.6 | Planned |
| B2-17 | Engineering verification and audit beyond code; existence is not quality | E9.1 | Planned |
| B2-18 | Scenarios A–I | A F4.5.1 · B F5.6.1, F7.4.1 · C, D F7.4.1 · E F16.6.1 · F, I F3.4.1 · G, H F5.6.1 · harness F9.2.1 | Planned |
| B2-19 | One integrated roadmap; reordered phases; hardening before decisions; knowledge before discovery; FDE discovery early; security, testing, migration, docs and release in every phase | MASTER_ROADMAP §3–4; D-020; D-019 | Done |
| B2-19b | Brief 2's proposed order (Core hardening as Phase 6) | Core hardening kept as Phase 2 | Reconsidered (D-020: decisions need hardened approvals first) |
| B2-19c | Brief 2's proposed CLI/Dashboard at Phase 8 | Phase 11, after audit/evals | Reconsidered (D-020: order keeps evals with the features they test) |
| B2-20 | The 16 requested outputs (integration, overlaps, classification, relationships, approvals, modes, data models, any domain, architecture, evals, plan, dependencies/risks/priorities/migration, RTM, MVP, roadmap + HTML, presentation) | ENGINEERING_INTELLIGENCE §1–13; phases; RISK_REGISTER; this file; MASTER §5; roadmap.html | Done (waiting for review) |

## B3 — Operations Research & Optimization Engine (ORE)

| ID | Requirement | Covered by | Status |
|---|---|---|---|
| B3-1 | Official name and principle (AI understands … business measures success); "no proof of optimality, no claim of optimality" | ore/ORE_DESIGN; INV-19 | Done (design) |
| B3-2 | Separation of responsibilities (AI, ORE, decision framework, engineer, core, audit); model optimum vs real-world optimum | ore/ORE_DESIGN §1 | Done (design) |
| B3-3.1–3.13 | Universal problem support: business strategy, MVP planning, pricing, resource allocation, scheduling, architecture, backend, mobile, frontend, cloud, databases, logistics, booking — never hard-coded | Problem templates as data: F6.1.5 (first), F10.4.1–F10.4.4, F16.7.1; ore/ORE_DESIGN §5 | Planned |
| B3-3.14 | AI model selection from task-specific evals, versions, dates, samples; routing, fallback, local for sensitive data, or no LLM | F9.3.2, F10.4.5; ore/ORE_DESIGN §6 | Planned |
| B3-3.15 | Forward deployed engineering optimization | F16.7.1 | Planned |
| B3-3.16 | Other domains via extensions; no hard-coded domain list | F6.1.5 templates, F15.4.1 | Planned |
| B3-4.1–4.3 | Agent selection, performance registry (measured / expected / unavailable), optimal allocation incl. single vs multi-agent and auditor choice | F9.3.1, F14.6.1 | Planned |
| B3-4.4 | Execution strategy optimization within gates, permissions, privacy, cost | F14.6.1, F14.3.1–F14.3.3 | Planned |
| B3-4.5 | Continuous feedback; normalisation by task size; `INSUFFICIENT_DATA` fallback | F14.6.2, F9.3.1 | Planned |
| B3-5 | 12-step lifecycle | ore/ORE_DESIGN §3; E6.1–E6.5 | Planned |
| B3-6 | Mathematical model schema (variable types, objectives, hard/soft constraints, provenance, integrity) | ore/MATHEMATICAL_MODEL_SCHEMA; F6.1.1–F6.1.4, F6.5.1 | Planned |
| B3-6b | Continuous, graph and scheduling variable types beyond v1 | Interval/assignment via templates in F6.1.5; continuous in F10.3.1 | Planned |
| B3-7 | OR methods delivered gradually by use case and provability | Phase 6 (enumeration, integer linear, logical, lexicographic), Phase 10 (Pareto, scenarios, LP with certificates) | Planned |
| B3-7b | Nonlinear, stochastic, simulation | Research only; never presented as proven | Reconsidered (ore/STRICT_OPTIMALITY_POLICY §7) |
| B3-8 | Strict Optimality Mode default; all listed statuses; separation of solution, termination and verification | ore/STRICT_OPTIMALITY_POLICY §1; F6.3.1 | Planned |
| B3-9 | Optimality proof and independent verification; exact arithmetic; gap ≠ proof | ore/STRICT_OPTIMALITY_POLICY §2–4; F6.3.2, F10.3.1, F10.3.2 | Planned |
| B3-10 | Resource limits, pre-checks, safe stop, no auto-raise, best-known feasible only on request and labelled | ore/STRICT_OPTIMALITY_POLICY §5; F6.4.1 | Planned |
| B3-11 | Multi-objective: Pareto, lexicographic, approved weights, epsilon-constraint, frontier completeness labels | F6.5.3, F10.1.1 | Planned |
| B3-12 | What-if, sensitivity, break-even, thresholds, robustness, reconsideration triggers | F10.2.1 | Planned |
| B3-13 | Uncertainty handling; no false certainty | ore/STRICT_OPTIMALITY_POLICY §7; F10.2.1 | Planned |
| B3-14 | Solver research and comparison from official sources | ore/SOLVER_COMPARISON, ore/CPSAT_TRIAL; F6.0.1, F6.0.2 | Done (CP-SAT trialled, D-037 accepted; Z3/HiGHS hands-on in Phase 10) |
| B3-15 | Internal architecture (logical responsibilities, not services); adapter contract; dependency isolation; local-first | ore/ORE_DESIGN §4; F6.2.1–F6.2.3 | Planned |
| B3-16 | Security and trust (declarative models, no eval/exec, isolation, verifier-only classification) | ore/SECURITY_AND_THREAT_MODEL; F6.6.1 | Planned |
| B3-17 | Mathematical decision evidence; re-verification instead of promised identical reproduction | ore/ORE_DESIGN §9; F6.5.1 | Planned |
| B3-18 | Integration with discovery and profiles; fit gate; simplest verifiable method first | ore/ORE_DESIGN §2; F6.5.2 | Planned |
| B3-19 | Integration with system design, specs, plans, traceability, measurements, re-evaluation | ore/ORE_DESIGN §8; F6.5.2, F10.3.3, F8.3.3 | Planned |
| B3-20 | Dashboard ORE section | F11.6.5 | Planned |
| B3-21 | Validation and testing strategy (correctness, failures, security, integration) | ore/VALIDATION_STRATEGY §1; F6.6.1 | Planned |
| B3-22 | Scenarios A–M | ore/VALIDATION_STRATEGY §2 (Phases 6, 10, 14, 16) | Planned |
| B3-23 | ORE implementation phases 0–11 | Merged into master Phases 6 (ORE 0–5), 10 (ORE 6–8, model selection), 9 and 14 (ORE 9), 11 (ORE 10), 15 and 19 (ORE 11) | Done (D-031) |
| B3-24 | Overall architecture | MASTER_ROADMAP §8; TARGET_ARCHITECTURE §7 | Done |
| B3-25 | Non-negotiable rules (16) | INV-19–INV-22; ore/STRICT_OPTIMALITY_POLICY; ore/SECURITY_AND_THREAT_MODEL | Done (design) |
| B3-26 | Proposed 16 documents in `docs/ore/` | Consolidated into 6 design docs in `docs/roadmap/ore/`; user docs in `docs/ore/` with F6.6.2 | Reconsidered (D-039) |
| B3-27 | The 22 requested outputs | This integration (ore/*, phases, RTM, risks, decisions, master roadmap, HTML) | Done (waiting for review) |

## B4 — Product simplicity, usability & competitive validation

| ID | Requirement | Covered by | Status |
|---|---|---|---|
| B4-01 | Permanent principle "Powerful Inside. Simple Outside."; the system absorbs complexity | D-041; INV-23; PRODUCT_EXPERIENCE §0 | Done (roadmap) |
| B4-02 | Usability as a first-class capability from Phase 1; material regression acceptance records rationale, risks and follow-up without waiving mandatory guarantees | D-042; E1.7 (F1.7.1–F1.7.3); F19.1.1; PRODUCT_EXPERIENCE §1, §10 | Planned |
| B4-03 | Progressive disclosure and Quick / Standard / Deep mapped onto one L0–L3 policy; Standard resolves to one recorded level; permitted changes are recorded and impermissible ones refused | D-043; F1.7.2, F3.3.3, F3.3.4; ENGINEERING_INTELLIGENCE §7 | Planned |
| B4-04 | Interaction principles: derive before asking, high-value questions, smart defaults with human decisions, one clear next action, progressive technical detail | PRODUCT_EXPERIENCE §3; F4.1.2, F4.1.4, F1.7.2, F5.5.2 | Planned |
| B4-05 | Prevent feature overload through proportional qualitative review, without arbitrary quotas or reduced engineering quality; ORE, multi-agent, diagrams and documents only when justified | D-045; INV-22; F14.7.1; PRODUCT_EXPERIENCE §5 | Planned |
| B4-06 | Competitive validation and product-market fit: current, evidence-based comparison with Spec Kit, BMad, OpenSpec, Kiro, Claude Code, Copilot and others; gates A (v1.5), B (v1.6), C (before v3.x/v4.x expansion) | D-044; F1.7.4, F5.6.2, F6.6.3, F11.0.1; R-27 | Planned |
| B4-07 | Product-experience and quality metrics, baselines first, honest labels, fair comparisons | D-044; F1.7.1, F17.6.1; PRODUCT_EXPERIENCE §6 | Planned |
| B4-08 | Usability measures UX-A–UX-E with outcome quality and user effort; UX-A/UX-B extend existing fixtures and UX-E waits for Phase 14 | PRODUCT_EXPERIENCE §7; F3.4.1, F4.5.1, F9.2.1, F14.7.1 | Planned |
| B4-09 | Master roadmap integration items 1–16 (phase-by-phase additions, register, no silent removal, no new phases or parallel documents) | PRODUCT_EXPERIENCE §9; phase files P1, P3–P6, P9–P11, P14, P16, P17, P19; MASTER_ROADMAP §5 | Done (roadmap) |
| B4-10 | Architectural guardrails: simplify interactions, not guarantees | INV-01–INV-23; PRODUCT_EXPERIENCE §11 | Done (roadmap) |
