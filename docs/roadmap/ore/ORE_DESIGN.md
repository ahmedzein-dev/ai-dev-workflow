# Operations Research & Optimization Engine (ORE) — design proposal

**محرك بحوث العمليات والتحسين الرياضي · Mathematical Modeling · Constraint Solving · Proven Optimality**

Deliverable of the third strategic integration (brief 3, 2026-11-22). ORE is part of the single master roadmap, not
a separate plan. Decisions marked **D-nnn** are in [../DECISIONS.md](../DECISIONS.md).

> **AI understands. Science optimizes. Engineers decide. Architecture guides. Evidence verifies. Business measures success.**
> **No proof of optimality, no claim of optimality.**

## 0. Documents

The brief proposed 16 files. Before anything is built, six documents avoid repeating the same design in several
places; user documentation in `docs/ore/` is written when the features ship.

| Proposed file | Where it lives now |
|---|---|
| ORE_OVERVIEW, ENGINEERING_INTEGRATION, BUSINESS_APPLICATIONS, AI_MODEL_OPTIMIZATION, AGENT_ALLOCATION, DECISION_EVIDENCE, SOLVER_ADAPTER_ARCHITECTURE | this file |
| MATHEMATICAL_MODEL_SCHEMA | [MATHEMATICAL_MODEL_SCHEMA.md](MATHEMATICAL_MODEL_SCHEMA.md) |
| OPTIMALITY_GUARANTEES, STRICT_OPTIMALITY_POLICY, RESOURCE_LIMITS, MULTI_OBJECTIVE_OPTIMIZATION | [STRICT_OPTIMALITY_POLICY.md](STRICT_OPTIMALITY_POLICY.md) |
| SOLVER_COMPARISON | [SOLVER_COMPARISON.md](SOLVER_COMPARISON.md) |
| SECURITY_AND_THREAT_MODEL | [SECURITY_AND_THREAT_MODEL.md](SECURITY_AND_THREAT_MODEL.md) |
| VALIDATION_STRATEGY, KNOWN_LIMITATIONS | [VALIDATION_STRATEGY.md](VALIDATION_STRATEGY.md) |

## 1. Responsibilities

| Part | Does | Never does |
|---|---|---|
| Engineering intelligence (agent + profiles) | Understands the problem, asks for objectives, variables, constraints, data; judges whether the problem is modelable | Declares a result optimal |
| **ORE** | Validates models, runs trusted solvers within limits, verifies solutions independently, classifies results, records evidence | Invents data or weights, relaxes hard constraints, runs untrusted code |
| Decision framework (ADRs) | Presents results, alternatives and trade-offs | Treats a model optimum as a real-world optimum |
| Engineer | Approves the model, decides | — |
| Workflow core | Approvals, hashes, evidence, staleness | Lets an agent set a result classification |
| Verification & audit | Checks implementation against the approved decision and real measurements | Accepts a proof without its guarantee level |

Two optimality claims are always kept apart: **optimal for this approved model and data** (what ORE can prove) and
**best in reality** (what nobody can prove: data may be incomplete, the model may miss aspects).

## 2. Is a problem a good fit? (the gate before modeling)

ORE runs only when all hold; otherwise the agent gives normal engineering analysis (ENGINEERING_INTELLIGENCE §4).

1. The decision can be written as variables with finite domains or bounds, an objective (or several) and constraints.
2. The data each term needs exists with a provenance (measured, verified, user-provided or approved assumption).
3. The number of alternatives is large enough that direct comparison is not simpler. For three or four alternatives
   with known numbers, a table is the verifiable method; ORE is not used just because it exists.
4. The decision is consequential enough to justify modeling (depth L2/L3, or the user asks).

Qualitative architecture choices without reliable numbers stay in the decision framework; ORE never turns guesses into
precise-looking numbers.

## 3. Lifecycle (brief 3 §5) mapped to the workflow

| Step | ORE action | Record / gate |
|---|---|---|
| 1 Problem discovery | Agent uses the `optimization` topics of the active profiles (objectives, variables, hard vs soft, data, conflicts) | Questions ledger (`Q`), requirements (`REQ`), constraints (`CON`) |
| 2 Formulation | Agent writes a declarative model (`OPT-n`), never code | `engineering/optimization/OPT-n/model.json` |
| 3 Input validation | Engine: schema, domains, units, provenance, linearity, numeric scaling, search-space size | Validation report; `INVALID_MODEL` / `INSUFFICIENT_DATA` / `UNSUPPORTED_PROBLEM` |
| 4 Human model review | Engine renders the model in plain language (what it decides, optimizes, must never violate, data, assumptions, what it does **not** represent) | **Model approval** (hash-bound, a gate or part of a decision set) |
| 5 Solver selection | Engine picks an adapter whose declared capabilities cover the problem class and the required guarantee level | Selection recorded with reasons |
| 6 Bounded execution | Separate process, time/memory/thread limits, cancellation | Termination reason |
| 7 Verification | Independent exact re-check of feasibility and objective; optimality evidence checked against the policy | Verification status |
| 8 Classification | Computed by the engine from solution status, termination and verification (agents cannot set it) | Result classification |
| 9 Explanation | Agent explains result, trade-offs, limits, assumptions in plain language | Part of the ADR |
| 10 Human decision | Engineer decides (may reject the recommendation) | ADR approval |
| 11 Evidence & ADR | Run evidence linked to ADR, requirements, design, plan | Trace links |
| 12 Re-evaluation | Model, data or constraint change → result stale → decision needs re-evaluation | Staleness rules (Phase 2/5) |

## 4. Architecture (brief 3 §15, simplified)

The brief's 18 responsibilities are kept as logical responsibilities inside **one optional package**, not services:

```
aidw_ore/                      optional package, installed separately; the skill never imports it unless asked
├── schema/        model JSON Schema, problem templates (data), provenance, units
├── validate/      structural, domain, unit, provenance, linearity, scaling, search-space checks
├── render/        plain-language model rendering for human review
├── solvers/       adapter interface + registry; built-in exact enumerator (stdlib); optional adapters (CP-SAT, HiGHS, Z3, …)
├── run/           execution controller: subprocess, limits, cancellation, termination reasons
├── verify/        exact feasibility/objective re-check (fractions), certificate checkers, policy evaluation, classification
├── analyze/       lexicographic, Pareto (epsilon-constraint), sensitivity, scenarios
└── evidence/      run records, fingerprints, links to ADRs and requirements
```

Integration points with the workflow core: the record store (`OPT` records), approvals (model approval), staleness,
the trace graph, the trust store (which adapters may run), the event log. **Dependency isolation:** the core and the
skill stay standard-library only; the built-in enumerator is standard library too, so ORE's first useful version needs
no third-party install; other solvers are opt-in installs recorded in the trust store.

### Solver adapter contract

Each adapter declares (as data, checked by tests): supported problem classes, variable types, constraint types,
objective types, arithmetic (exact integer / exact rational / floating point with tolerances), optimality guarantee and
the conditions for it, proof or certificate capabilities, native status mapping, resource controls, execution method,
verification method, known limitations, version. The registry refuses an adapter whose declared guarantee cannot meet
the policy's required level for the problem (STRICT_OPTIMALITY_POLICY §3).

## 5. Universal problem support without hard-coded domains

Domains (business strategy, MVP planning, pricing, resource allocation, scheduling, architecture, backend, mobile,
frontend, cloud, databases, logistics, booking, AI models, FDE, manufacturing, …) are **problem templates**: data
files that map a domain vocabulary to the generic schema (for example "feature selection" → binary variables, value
objective, budget and dependency constraints). Templates live in profiles or `.ai-dev-workflow/ore/templates/`; adding
a domain never changes ORE code (Scenario M).

| Domain | What ORE can rigorously do | What stays analysis |
|---|---|---|
| Business strategy | Budget/investment allocation, break-even, scenario comparison on given numbers | Market behaviour, business success (never claimed) |
| MVP planning | Feature subset under budget, deadline, dependencies, value; release ordering | Value estimates are estimates (provenance says so) |
| Pricing | Optimize price within constraints **for a given demand model** | Whether the demand model is right (needs data; unsupported demand models are not facts) |
| Resource allocation, scheduling | Assignment, resource-constrained scheduling, critical path, time–cost trade-offs | Productivity assumptions |
| System design, backend, cloud, databases | Capacity planning, instance mix, placement, pool/worker sizing **from measured or approved capacity models** | Qualitative trade-offs (maintainability, team fit) |
| Mobile, frontend | Sync scheduling, cache/bundle budgets with measured costs | Perceived UX |
| Logistics, booking | Routing, assignment with capacity and time windows, conflict-free allocation | Demand forecasts |
| AI models | Choose a model, set or routing from **task-specific eval results** (§6) | Performance outside the evaluated sample |
| FDE | Build vs buy and rollout plans when the comparison terms are measurable | Customer politics, adoption |

Brief 3 lists methods (LP, IP, MILP, CP, CP-SAT, network flow, assignment, knapsack, scheduling, VRP, DP,
multi-objective, robust, sensitivity, scenarios). They are delivered gradually, ordered by real use cases and by what
can be **proven**; nonlinear, stochastic and simulation methods are later studies and never labelled as global optima
without proof.

## 6. AI model selection (brief 3 §3.14)

- **Candidates** are models the user can actually use (local or cloud), each with version, modality, context window,
  licence, data-residency and privacy properties, price source and date.
- **Quality comes from task-specific evals** run on the user's own task samples (Phase 9 eval harness), never from
  general leaderboards alone; latency, throughput and cost are measured or taken from dated official price pages.
- **Formulation**: choose one model, a set, a routing (task type → model) or a fallback chain, minimizing cost or
  latency subject to quality thresholds, privacy rules (sensitive data → local model) and rate limits — or conclude
  that a non-LLM solution meets the requirements better.
- **Honesty about samples**: optimality holds for the candidates, the model and the measured sample; quality is
  reported with sample size and, where it matters, as a range; robust formulations (worst case over the range) are
  offered when the user approves them.
- **Records** keep model version, measurement date, dataset description and limits; a new model version or price makes
  the result stale.

## 7. ORE inside AIDevWorkflow: agents and models (brief 3 §4)

- **Agent & model performance registry** (Phase 9): per agent/model/version and task category — success rate,
  requirement coverage, test success, audit findings, rework, time, tokens and cost **only when reported**, context
  limit, tools, privacy limits, rate limits, availability. Every value is labelled measured / expected / unavailable.
- **Normalisation**: results are compared per task category and size (depth level, changed lines, number of
  requirements), so an agent is not "better" because it ran more or easier tasks.
- **Allocation** (Phase 14): ORE chooses, per stage, the agent and model that meet quality targets at the lowest cost or
  time, the number of agents, parallel distribution, the independent auditor (must differ from the implementer), and
  whether single-agent beats multi-agent. Human gates, permissions, privacy and budgets are hard constraints.
- **Not enough data** → `INSUFFICIENT_DATA`: the fallback is manual selection, an engineering recommendation labelled
  unproven, or a benchmark run the user authorises (and pays for, if paid).
- **Feedback loop**: after each task the event log adds measured results; the registry updates; earlier allocation
  results become stale when their inputs change.

## 8. Integration with engineering intelligence, design, specs and plans

```
Business objective → requirements & constraints → mathematical model (OPT, approved) → bounded solver run
  → verified, classified result → human decision (ADR) → HLD / LLD / diagrams → spec & plan → implementation
  → actual measurements → model calibration → re-evaluation
```

- ORE results enter ADRs as **evidence** for one alternative; the ADR keeps the human decision and rationale.
- NFR targets from Phase 4 become constraints; approved capacity estimates (Phase 7) become parameters.
- Plans add tests or measurements that check the constraints and objective in reality.
- **Calibration** (added requirement): after implementation, measured values are compared with the model's
  parameters; a deviation beyond a stated threshold flags the decision for re-evaluation.

## 9. Mathematical decision evidence (brief 3 §17)

Each run record (`OPT-n/runs/<id>.json`, engine-written) holds: problem ID, model version and fingerprint, input data
fingerprint (data itself stored only if it is not sensitive; otherwise a reference and hash), data sources and
provenance, approved assumptions, variables, objectives, hard and soft constraints, solver name, version and binary
hash, configuration, seed and threads, environment, resource limits, time, termination reason, native solver status,
solution, objective value, best bound, gap, exact verification results, tolerances, proof or certificate (or its hash),
verification status, guarantee level, classification, known limitations, related ADRs and requirements, the human
decision. Re-running proves the result again; byte-identical reproduction is not promised when solvers are
multi-threaded or nondeterministic.

## 10. Dashboard (Phase 11)

Problem explorer, results (statuses, guarantee level, classification, objective values, gap, time, resources,
limitations), trade-off views (Pareto frontier marked complete or partial, scenario and sensitivity charts) and a
decision review where the engineer approves models, requests data changes or re-runs, and approves or rejects
recommendations — all through the core. Charts never show unproven solutions as proven and always label estimated data.

## 11. Gaps and improvements found while designing (brief 3 §27.21)

| Item | Why it matters | Where |
|---|---|---|
| Built-in exact enumerator (standard library) | Proves optimality by construction for small discrete problems with zero installs; exact search-space size gives an honest complexity pre-check | Phase 6 |
| Exact rational data (`"0.1"` as a fraction, not a float) | Avoids floating-point error before the solver even runs | Phase 6 |
| Model approval as an approval type | The engineer approves what is optimized before results exist | Phase 6 (extends D-022) |
| Infeasibility explanations (unsat cores / irreducible subsets) | "Proven infeasible" is only useful if the conflicting constraints are named | Phases 6, 10 |
| Model calibration against reality | Closes the loop the brief asks for in §19 | Phase 10 |
| Solver supply chain (pinned versions, binary hash in evidence) | A changed solver changes results and guarantees | Phase 6 |
| Commercial solvers only as bring-your-own adapters | Keeps INV-14; never required | Phase 15 |
| "Optimization theatre" risk (precise answers from invented numbers) | The main way ORE could mislead | R-22, provenance rules |
