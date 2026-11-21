# ORE strict optimality policy, guarantees, resource limits and multi-objective rules (proposal)

**Strict Optimality Mode is the default and cannot be weakened by an agent.** A result is presented as optimal only
when the engine has evidence that meets the required guarantee level for the approved model.

## 1. Status model: three dimensions plus a derived classification

A single status cannot carry "timed out **and** found a feasible solution". ORE records four separate things:

| Dimension | Values |
|---|---|
| **Model status** (before solving) | `valid` · `invalid_model` · `insufficient_data` · `unsupported_problem` · `not_modelable` · `numerical_uncertainty` |
| **Termination reason** | `completed` · `time_limit` · `memory_limit` · `resource_limit` · `cancelled` · `solver_error` · `not_run` |
| **Solution status** (what the solver established) | `optimal_claimed` · `feasible` · `infeasible_claimed` · `unbounded_claimed` · `no_solution` · `unknown` |
| **Verification status** (what ORE checked itself) | `verified` (feasibility + objective exact; optimality evidence meets the level) · `feasibility_only` · `failed` · `not_verified` |

The **result classification** shown to people is computed by the engine from these four and the policy:

| Classification | Rule |
|---|---|
| `PROVEN_OPTIMAL` | valid model · solution `optimal_claimed` (or proven by the built-in enumerator) · verification `verified` at or above the required guarantee level |
| `FEASIBLE_NOT_PROVEN` | a solution passes the exact feasibility check, but optimality evidence is missing or below the level (for example a time limit, a non-zero gap, a floating-point-only proof) |
| `PROVEN_INFEASIBLE` | infeasibility established at the required level; conflicting constraints named when an explanation is available |
| `UNBOUNDED` | unboundedness established at the required level |
| `INVALID_MODEL` · `INSUFFICIENT_DATA` · `UNSUPPORTED_PROBLEM` · `NOT_MODELABLE` · `NUMERICAL_UNCERTAINTY` | from the model status |
| `TIMEOUT` · `RESOURCE_LIMIT` | termination before any verified solution; with a feasible solution, the classification is `FEASIBLE_NOT_PROVEN` and the termination reason is kept |
| `VERIFICATION_FAILED` | the solver's answer failed ORE's own check (the answer is never shown as a result) |
| `SOLVER_ERROR` · `UNKNOWN` | otherwise |

A `FEASIBLE_NOT_PROVEN` solution is shown only on request ("best known feasible solution, not proven optimal"), never
as ORE's recommendation. Agents cannot write classifications; only the verifier can.

## 2. Guarantee levels

| Level | Meaning | Examples |
|---|---|---|
| G0 none | heuristic or approximate | local search, time-limited run |
| G1 tolerance | solver reports optimal within floating-point tolerances and a gap setting | float LP/MIP solvers with default gaps |
| G2 exact-solver | solver proves optimality in exact (integer or rational) arithmetic with zero gap; ORE independently re-checks feasibility and objective exactly | an integer-only model solved with zero gap limits by a solver whose arithmetic is exact for that class (to be confirmed per solver in SOLVER_COMPARISON) |
| G3 independent | optimality established by a method independent of the solving solver, checked by ORE | built-in exhaustive enumeration; an exact LP dual certificate checked in rational arithmetic; a second exact solver proving the same optimal value |

**Recommended default (D-034): `exact` = G2 or G3.** G1 results are classified `FEASIBLE_NOT_PROVEN` in strict mode,
with the solver's reported gap shown. Projects can require G3 for critical decisions.

## 3. Verification procedure

1. Re-evaluate every hard constraint and the objective of the returned solution in **exact rational arithmetic**
   (Python `fractions`) from the original model, not the solver's internal form.
2. Check the solver configuration actually used (gap limits, tolerances, presolve options, time limit) against the
   adapter's declared conditions for its guarantee.
3. Check optimality evidence by level: enumeration (exhaustive, so optimal by construction); dual certificate
   (primal feasibility, dual feasibility, equal objective values, exact); second exact solver (same optimal value under
   the same model fingerprint); exact-solver claim (status, zero gap, exact-arithmetic class, bound equals objective).
4. Any mismatch → `VERIFICATION_FAILED`, recorded with the details.

Checking that a solution is feasible never proves it is optimal; step 3 is always required for `PROVEN_OPTIMAL`.

## 4. Numerical precision

- Inputs are exact fractions; floats are rejected at validation.
- Adapters needing integers receive coefficients scaled exactly by the least common denominator; scaling beyond the
  adapter's integer range → `NUMERICAL_UNCERTAINTY` (never rounding).
- Floating-point solvers stay at G1 unless their answer is independently proven (G3). A zero gap setting does not
  remove floating-point tolerance effects and is not treated as exact.

## 5. Resource limits and safe execution

| Control | Default proposal | Mechanism |
|---|---|---|
| Time limit | 60 s per run (policy) | solver time limit + wall-clock kill of the process group |
| Memory | 1 GB | solver memory parameter where it exists; OS limit where available (POSIX `setrlimit`; Windows job objects later); otherwise wall-clock + monitoring |
| Threads | 1 by default (deterministic, light) | solver parameter |
| Model size | variables, constraints, exact search-space size for enumeration | validator |
| Parallel runs | 1 | execution controller |
| Cancellation | user or agent request | process-group termination (Phase 2 process runner) |

Before running, ORE estimates difficulty honestly: the exact search-space size for enumeration, and problem-class
indicators for other solvers; it does not pretend that the number of constraints predicts hardness. If a problem is
clearly outside the limits it is not run, with the reason. When a run hits a limit: stop safely, record the reason, keep
any verified feasible solution as `FEASIBLE_NOT_PROVEN`, never relax constraints, never raise limits without an approved
policy, and suggest legitimate reformulations (tighter bounds, symmetry breaking, decomposition, smaller scope).

## 6. Multi-objective rules

| Method | Use | Guarantee |
|---|---|---|
| Lexicographic | Priorities set by the user | Each stage solved to the required level → the lexicographic optimum is proven |
| Pareto via epsilon-constraint | Two (later more) integer objectives | For integer objectives, iterating proven-optimal epsilon steps yields a **proven complete frontier**; otherwise frontier labelled partial |
| Weighted sum | Only with weights the user approved | Proven optimal for those weights only; may miss unsupported Pareto points (stated) |

Results distinguish: proven complete frontier · proven individual Pareto-optimal points · partial or approximate
frontier. Each point shows its objective values, constraints met, and what is given up to improve another objective.

## 7. Sensitivity, scenarios and uncertainty

- Scenarios re-solve the model with changed parameters; each scenario result has its own classification.
- Thresholds and break-even points are reported as proven only when computed by exact re-solves or exact parametric
  analysis; otherwise as sampled observations.
- Estimates, ranges and probabilities stay labelled; expected values are not facts; robust formulations (worst case
  over approved ranges) are used only when the user approves the ranges.
- Simulation results are never presented as proof.
