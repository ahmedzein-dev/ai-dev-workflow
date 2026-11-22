# CP-SAT technical trial (F6.0.2, part 1) — results for D-037

Run on 2026-11-22 on the owner's Mac (macOS 26.3, Apple silicon) in two throwaway virtual environments, as approved in
D-037: Python **3.13.2** and Python **3.9.6** (the system Python), each with `ortools==9.15.6755` from PyPI. Nothing was
installed outside those environments; the AIDevWorkflow engine and skill were not changed.

- Trial code: [cpsat_trial/trial.py](cpsat_trial/trial.py). Run it with `python -I trial.py` inside a virtual
  environment that has `ortools`.
- Raw results: [cpsat_trial/results-py313.json](cpsat_trial/results-py313.json) and
  [cpsat_trial/results-py39.json](cpsat_trial/results-py39.json).

The harness follows the planned ORE design so the conditions are tested end to end:
- **adapters:** a solver-neutral adapter interface with two adapters, the built-in exact enumerator (standard library)
  and CP-SAT;
- **exact input:** model data as exact fractions, with floats rejected, scaled exactly to integers and pre-checked
  against int64;
- **verifier:** it never trusts the solver's claim;
- **execution controller:** it runs the solver in a separate process, with a wall-clock kill, a memory (RSS) watchdog
  and cancellation.

## 1. Verdict

**CP-SAT meets the owner's conditions on macOS with Python 3.9 and 3.13, provided ORE adds the controls listed in §4.**
Recommendation: adopt it as the first optional solver for `ore/1` v1.

Two items are still open before final adoption:
- **Windows and Linux at runtime (C3, C11):** wheels exist for both, but the trial ran only on macOS. The trial must
  also run in CI on Linux and Windows.
- **The owner's decision on the policy questions in §5.**

The proof standard was not changed to suit the solver (C13). The solver's `OPTIMAL` status is never enough on its own.

## 2. Results by condition

| ID | Condition | Result | Evidence |
|---|---|---|---|
| C1 | No tie to one solver; extensible adapters | **Met (design shown)** | Same verifier, classification and controller for both adapters. CP-SAT is one adapter with a capability declaration |
| C2 | Core stays light; OR-Tools never forced | **Met** | The engine imports none of numpy, pandas, ortools, protobuf or absl (checked with `/usr/bin/python3`). OR-Tools lives only in the isolated environment |
| C3 | Python 3.9; macOS, Windows, Linux | **Met on macOS (3.9 and 3.13); Windows and Linux: wheels confirmed, runtime not tested** | PyPI 9.15.6755: `requires_python >=3.9`; cp39–cp314 wheels for macOS (arm64, x86_64), Windows x64, Linux x86_64 and aarch64 (glibc 2.27/2.28 or newer) |
| C4 | Integer models only; no silent rounding | **Met with an ORE guard** | Float input → `INVALID_MODEL`. Rational coefficients are scaled exactly by the least common denominator. CP-SAT itself rejects floats in constraints (TypeError) but **accepts a float objective silently** (`floating_point_objective`), so the adapter builds objectives from integers only |
| C5 | Verify constraints, objective, bound, gap | **Met** | Every solution is re-checked in exact fractions from the original model. The bound is taken from the int64 `inner_objective_lower_bound`. The gap is computed exactly |
| C6 | Never trust `OPTIMAL` alone | **Met — the trap was reproduced** | With `absolute_gap_limit=50`, CP-SAT returned **`OPTIMAL` with objective 50 and bound 0**. The verifier classified it `FEASIBLE_NOT_PROVEN` (gap 50; configuration not strict) |
| C7 | Strict gap limits; precision; overflow | **Met** | The adapter sets both gaps to 0 (the default absolute gap is 1e-4). Objective 2^55+1: the solver's double reported 36028797018963968; the exact path gave 36028797018963969, and the int64 bound matched it exactly. Exact scaling past int64 → `NUMERICAL_UNCERTAINTY` before solving. CP-SAT's own overflow check → `MODEL_INVALID` |
| C8 | Solver claim vs verified result kept apart | **Met** | Every verdict records `solver_claim` (for example `optimal_claimed`) separately from `verification`, `level_reached` and `classification` |
| C9 | Agreement with exhaustive enumeration | **Met: 0 mismatches in 1,650 models** | 1,500 small models (1,225 optimal, 275 infeasible) and 150 medium models (116 optimal, 34 infeasible), with rational coefficients, min and max, equalities and enforced (conditional) constraints. Classification and exact optimal value agree on Python 3.13 and 3.9 |
| C10 | Infeasible, not proven, timeout, resource limit, invalid, cancellation | **Met** | See §3 |
| C11 | Real time, memory and thread limits | **Met for time and threads; memory needs ORE's watchdog** | See §3. `max_memory_in_mb=64` did **not** stop CP-SAT (peak 115 MB, ran to its time limit). On macOS, `setrlimit` for RLIMIT_AS and RLIMIT_DATA fails. The external RSS watchdog stopped a process at 300 MB in under 1 s |
| C12 | Limits and proof level documented | **Met** | §4 and §6 |
| C13 | Proof criteria never relaxed | **Met** | The default required level stays G2. Every non-strict outcome is classified below `PROVEN_OPTIMAL` |

## 3. Scenario results (identical on Python 3.13 and 3.9)

| Scenario | CP-SAT status | Termination | ORE classification |
|---|---|---|---|
| Strict gaps, small rational model (max 3/2·x + 2·y + 1/3) | OPTIMAL | completed | `PROVEN_OPTIMAL` (G2), 107/6, same as enumeration |
| Gap trap: absolute gap 50 | **OPTIMAL** | completed | `FEASIBLE_NOT_PROVEN`, gap 50 |
| Relative gap 0.99, 10 s | FEASIBLE | time_limit | `FEASIBLE_NOT_PROVEN`, gap 1 |
| Contradictory constraints (ORE-I) | INFEASIBLE | completed | `PROVEN_INFEASIBLE` (G2), agrees with enumeration |
| Time limit 1 s, hard instance with a solution (ORE-J) | FEASIBLE | time_limit | `FEASIBLE_NOT_PROVEN`, gap 2 |
| Time limit 1 s, hard feasibility instance | UNKNOWN | time_limit | `TIMEOUT` |
| Conflict limit 2,000 | UNKNOWN | resource_limit | `RESOURCE_LIMIT` |
| Empty domain (5..3) | — (stopped by ORE validation) | — | `INVALID_MODEL` |
| Cancel in process (`stop_search` after 0.5 s) | FEASIBLE | cancelled | `FEASIBLE_NOT_PROVEN`; returned after 0.511 s |
| Cancel the process group after 1 s | — | cancelled (SIGTERM) | process ended at 1.02 s |
| Hard wall clock 1.5 s (solver's own limit 600 s) | — | time_limit (SIGTERM) | process ended at 1.51 s |
| Threads: 1 worker, 3 s | — | — | CPU/wall 1.01–1.02 (4 workers: 3.3–3.7) |
| Determinism: 1 worker, deterministic time 2.0, 5 runs | — | — | identical (48,235 branches, 13,991 conflicts, same solution) |
| Wall-clock limit 1 s, 3 runs | — | — | branches differ from run to run (44,115–44,352) |

The test instances are hard "market split" problems (Cornuéjols–Dawande style, generated from fixed seeds). Every
random model is reproducible from the seeds in `trial.py`.

## 4. Controls ORE's CP-SAT adapter must have (input to F6.2.3 and F6.4.1)

1. **Exact integers only.**
   - Scale exact fractions by the least common denominator.
   - Pre-check every scaled expression against an int64 headroom of 2^62; above it → `NUMERICAL_UNCERTAINTY`, never
     rounding.
   - Before solving, assert `not has_floating_point_objective()`.
2. **Strict parameters, recorded with every run:**
   - `absolute_gap_limit = 0`, `relative_gap_limit = 0`;
   - `num_workers = 1` by default;
   - a fixed `random_seed`;
   - `max_time_in_seconds` from the policy.
   - The verifier rejects a G2 claim made under any other configuration.
3. **No doubles in verification.**
   - Recompute the objective exactly from the solution values.
   - Take the bound from the int64 `inner_objective_lower_bound`; for maximisation the bound is its negation.
   - `objective_value` and `best_objective_bound` are doubles and are informational only.
4. **G2 rule:** status `OPTIMAL`, gaps 0, and exact bound equal to the exact objective, plus the exact feasibility
   re-check.
5. **Termination reason** is inferred from counters (wall time, deterministic time, conflicts, stop flag), because the
   CP-SAT response has no field for it. Kills by the execution controller are authoritative.
6. **Memory** is enforced outside the solver: an RSS watchdog on every platform; on Linux also POSIX `RLIMIT_AS`;
   Windows job objects later. `max_memory_in_mb` is set too, but is not relied on.
7. **Reproducibility:** for a reproducible run use one worker and `max_deterministic_time`, and record the
   deterministic time. Runs bounded by the wall clock may differ between runs.
8. **Infeasibility explanation:** the assumption core is a conflicting set but **not necessarily minimal**. In the
   trial it returned all 4 constraints when 3 suffice. Show it as "these constraints conflict together". ORE may shrink
   it later by re-solving (deletion filter).

## 5. Questions for the owner (policy, not solver)

| ID | Question | Recommendation |
|---|---|---|
| P-1 | A run cancelled before any solution has no classification in the policy (today `UNKNOWN`) | Add `CANCELLED` to the classifications |
| P-2 | CP-SAT's `INFEASIBLE` rests on its internal proof (no certificate except for pure SAT), exactly like its `OPTIMAL` | Treat both as G2. Reaching G3 needs the enumerator or a second exact solver (Z3, Phase 10). Label G2 infeasibility "proven by an exact solver, not independently certified" |
| P-3 | Python 3.9 keeps working only with OR-Tools 9.15 or older if a later release drops 3.9 (numpy 2.0.2, OR-Tools' minimum, is the last numpy for 3.9) | Pin the tested version per Python version in the opt-in install (F6.2.3); re-check at each release |

## 6. Trade-offs and limits measured

| Item | Measured |
|---|---|
| Installed size (environment with dependencies) | 201 MB (Python 3.13: numpy 2.5.5, pandas 3.1.1); 145 MB (Python 3.9: numpy 2.0.2, pandas 2.3.3); protobuf 6.33.6, absl-py, immutabledict |
| Download (wheel only) | 20–28 MB per platform, plus dependencies |
| Import time of `cp_model` (warm) | 0.24 s (3.13), 0.83 s (3.9). **The first import after installing took 46 s on 3.9**, a one-off cold start (later imports 0.83 s); ORE's install step should warm it up |
| Memory per solver process | 80–100 MB peak on small models |
| Not supported in `ore/1` v1 via CP-SAT | continuous variables (MIP scaling is approximate), float objectives, nonlinear terms beyond CP-SAT's integer constraints, native multi-objective (ORE runs lexicographic stages itself) |
| Highest proof level | G2 for integer models under the rules in §4; never G3 alone; no optimality certificate |
| Platform notes | Linux wheels need glibc 2.27/2.28 or newer (no Alpine/musl); Windows x64 only (no Windows on Arm wheel) |

## 7. Still to do before final adoption

- Run `trial.py` on Linux and Windows with Python 3.9 (a CI job on a branch, or the owner's machines). For Linux, also
  confirm `RLIMIT_AS` enforcement.
- The owner's answers to P-1–P-3, and the final D-037 decision.
- Not covered by this part of F6.0.2: the hands-on checks of Z3 and HiGHS (Phase 10 candidates).
