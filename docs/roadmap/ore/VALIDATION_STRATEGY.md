# ORE validation strategy and known limitations (proposal)

The goal is not to show that ORE returns answers, but that it **refuses to claim optimality without sufficient proof**.

## 1. Test layers

| Layer | Contents |
|---|---|
| Mathematical correctness | Problems with known optima; small problems cross-checked by exhaustive enumeration; assignment, knapsack, scheduling, resource allocation; multiple optimal solutions (any optimum accepted, value checked); conflicting objectives; lexicographic and Pareto results checked against enumerated frontiers |
| Failure behaviour | Infeasible and contradictory models; invalid models; missing data; wrong units; unsupported classes (products of variables); unbounded objectives; time and memory limits; cancellation; solver crashes; precision problems; non-zero gaps; feasible-but-not-proven results; incomplete frontiers; stale results after model, data or solver changes |
| Security | Malicious expressions and identifiers; resource exhaustion; untrusted plugins; tampered models; fake solver output; fake optimality claims; unauthorized changes to constraints or weights |
| Integration | ORE with decisions and ADRs, system design, specs, plans, the multi-agent orchestrator, project intelligence, the dashboard, verification and audit |
| Property tests | Random small integer models solved by the enumerator and by each optional adapter must agree on optimal value and status |

## 2. Required scenarios (brief 3 §22)

| ID | Scenario | Phase | Must show |
|---|---|---|---|
| ORE-A | MVP feature selection (budget, deadline, resources, dependencies, value) | 6 | Proven optimal subset; value inputs labelled estimates |
| ORE-B | Cloud infrastructure cost under capacity, latency, availability constraints | 10 | Result conditional on the documented capacity model |
| ORE-C | Backend system design combinations (servers, databases, workers, processing) | 10 | Only measured or approved parameters used |
| ORE-D | Booking allocation without conflicts | 10 | No overlapping allocations; proven optimal or honestly unproven |
| ORE-E | Logistics: orders to vehicles/drivers with capacity, time windows, cost | 16 | Guarantee level stated; heuristics never labelled optimal |
| ORE-F | AI model selection from real evals | 10 | Sample size shown; optimal only for the candidates and sample |
| ORE-G | AIDevWorkflow agent allocation | 14 | Single-agent chosen when it is optimal; `INSUFFICIENT_DATA` when data is thin |
| ORE-H | Cost vs performance Pareto analysis | 10 | Frontier marked complete only when proven |
| ORE-I | Contradictory constraints | 6 | `PROVEN_INFEASIBLE`, no constraint ignored, conflict named when possible |
| ORE-J | Problem beyond resource limits | 6 | Safe stop; `TIMEOUT`/`RESOURCE_LIMIT` or `FEASIBLE_NOT_PROVEN`; no optimality claim |
| ORE-K | Precision requirement above the solver's guarantee | 6 (enumerator vs float stub), 10 (real float solver) | Tolerance-only result not classified as proven |
| ORE-L | Missing real-world data | 6 | `INSUFFICIENT_DATA`; no invented values |
| ORE-M | Unknown domain added as a template | 6 | No ORE code change |

## 3. Known limitations (by design)

- Optimality is always relative to the approved model, data and candidate set; real-world optimality is never claimed.
- Results built on estimates are conditional on those estimates.
- Version 1 handles bounded integer/Boolean variables and linear constraints; continuous, nonlinear and stochastic
  problems come later and only with matching guarantees.
- The built-in enumerator is exact but only practical for small search spaces; larger problems need optional solvers.
- Floating-point solvers provide tolerance-level guarantees (G1) unless their answers are independently proven.
- Multi-threaded solvers may not reproduce byte-identical runs; ORE re-verifies instead of promising identical output.
- Some instances are hard regardless of size; pre-checks reduce, but cannot remove, the chance of hitting limits.
- Business success, market behaviour and demand are never guaranteed by ORE.
