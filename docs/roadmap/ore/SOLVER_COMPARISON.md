# ORE solver comparison (desk study F6.0.1 / F0.4.2)

Compiled on 2026-11-22 from official documentation, release notes, source code at release tags, PyPI metadata and OSV
(no software was installed). Items marked **unverified** could not be confirmed and go to the hands-on spike (F6.0.2).
Selection criterion: what each tool can **prove** under the strict policy ([STRICT_OPTIMALITY_POLICY.md](STRICT_OPTIMALITY_POLICY.md)).

## 1. Summary table

| | OR-Tools CP-SAT | HiGHS (highspy) | SciPy milp/linprog | Z3 (z3-solver) | SCIP / PySCIPOpt | Pyomo |
|---|---|---|---|---|---|---|
| Version (2026-11) | 9.15 | 1.16.0 | 1.18.1 | 5.4.1.0 | PySCIPOpt 6.3.0 (bundles SCIP 10.0.2) | 6.11.0 |
| Licence | Apache-2.0 | MIT | BSD-3-Clause | MIT | MIT (bindings), Apache-2.0 (SCIP, SoPlex) | BSD-3-Clause |
| Python 3.9 | yes (cp39–cp314) | yes | **no** (last 3.9 release: 1.13.1) | installs (pure wheel); 3.9 not stated | yes | **no** (last 3.9 release: 6.9.5) |
| Wheels | macOS arm64/x86_64, Windows x64, Linux x86_64/aarch64 | all three OSes | all three | all three (macOS 13+) | all three | all three (solvers not included) |
| Download size | 22–30 MB **plus** numpy, pandas, protobuf, absl-py | 2.4–3.3 MB plus numpy | 20–38 MB plus numpy | 15–49 MB | 9–48 MB plus numpy | 3–17 MB plus a solver |
| Classes | CP, integer programming, SAT | LP, MILP, QP | LP, MILP | SAT, SMT, optimisation over Int/Real | MILP, MINLP, CIP | modelling only |
| Arithmetic | **integer (int64) constraints**; float objective scaled to integer | floating point | floating point | **exact** (mathematical integers, rationals) | floating point; exact mode needs a GMP build | solver's |
| Default gap | absolute 1e-4, relative 0 | rel 1e-4, abs 1e-6 | rel 1e-4 | none (exact) | 0 / 0 | solver's |
| Status at gap limit | `OPTIMAL` | `kOptimal` | "Optimal solution found" | n/a | **`GAPLIMIT`** (distinct from OPTIMAL) | solver's |
| Proofs | DRAT/LRAT for **pure SAT only** | none | none | `Solver.proof()`; **none on `Optimize`** | VIPR certificates in exact mode only | none |
| Infeasibility explanation | core (not guaranteed minimal) | IIS (documented for LP), dual ray | status only | `unsat_core` (also on `Optimize`) | IIS for any CIP, Farkas duals | solver's |
| LP duals | n/a | yes, with ranging | `linprog` marginals | n/a | yes | solver's |
| Limits | time, deterministic time, threads; memory only for pure SAT | time, threads; **no memory option** | time, nodes | timeout, rlimit, memory, threads | time, memory, threads | time, threads |
| Cancel from Python | `stop_search()` | `cancelSolve()` | **unverified** | `interrupt()` | `interruptSolve()` | solver's |
| Multi-objective | none found | native lexicographic or blended | none | native lex / pareto / box | none found | none found |

Sources (selection): OR-Tools v9.15 release, `sat_parameters.proto`, `cp_model.proto`, `linear_solver.h`
(github.com/google/or-tools, tag v9.15); HiGHS v1.16.0 release, options, `HighsMipSolverData.cpp`
(github.com/ERGO-Code/HiGHS, tag v1.16.0; ergo-code.github.io/HiGHS); SciPy 1.18 manual and release notes; Z3 5.4.1
release and z3guide (microsoft.github.io/z3guide); SCIP 10.1.0 parameters and `type_stat.h`, SCIP exact-mode docs and
the SCIP 10 report (arXiv 2511.18580); scipoptsuite-deploy v0.12.0 build scripts; Pyomo 6.11.0 changelog and sources;
SoPlex 8.1.0 exact mode; SymPy 1.14.0 docs; PyPI; osv.dev (no advisories found for these packages).

## 2. What each one can prove (mapping to guarantee levels)

| Tool | Highest level under the strict policy | Conditions |
|---|---|---|
| **Built-in enumerator** (ORE, standard library) | **G3** | Exhaustive search over a finite space with exact fractions; practical only for small spaces |
| **CP-SAT** | **G2** | Integer model (ORE scales rationals exactly to integers), integer objective, status `OPTIMAL` and best bound equal to the objective value (the proto states that any absolute gap below 1 on an integer objective is a true optimum), plus ORE's exact re-check. Never for models with continuous variables: MIP scaling is approximate and `only_solve_ip` defaults to false |
| **HiGHS** | **G1** alone; **G3 for LP** with an exact certificate | "Optimal" means within gap and feasibility tolerances, even with gaps 0 (pruning uses the feasibility tolerance). For LP, ORE can rebuild the optimal basis in exact rational arithmetic and check primal and dual feasibility (Phase 10) |
| **Z3** | **G2** (exact arithmetic); independent cross-check towards G3 | Exact Int/Real arithmetic; `Optimize` gives no proof object and can return `unknown` (nonlinear integer arithmetic is undecidable); limited scalability |
| **SCIP** | G1 with pip wheels | Exact SCIP (rational MIP with VIPR certificates) needs GMP/MPFR; the pip wheels are built without them (from build scripts; **unverified at runtime**). Clear status semantics (`GAPLIMIT` ≠ `OPTIMAL`) |
| SciPy, Pyomo | — | Both dropped Python 3.9 in current releases; SciPy wraps HiGHS (use HiGHS directly); Pyomo duplicates ORE's own schema |
| SymPy simplex | G3 for small LPs | Exact fractions, pure Python; never call `sympify` on untrusted text (it uses `eval`) — build expressions programmatically only |
| pycddlib, python-qsoptex | — | GPL licences, limited wheels or stale releases; unsuitable as options for an MIT project |

No pip-installable tool provides a certificate for gap-based MIP optimality. The only certificate route for MILP
(exact SCIP with VIPR) needs a source build.

## 3. Recommendation for D-037 (first optional solver)

**OR-Tools CP-SAT** as the first optional adapter, for bounded integer/Boolean models with linear and logical
constraints (exactly the scope of `ore/1` v1).

- **Why:** integer-native constraints match ORE's exact data; `OPTIMAL` on an integer objective with bound equal to the
  objective is a real optimum (G2); strong at assignment and scheduling; Apache-2.0; Python 3.9 wheels on all three
  operating systems; cancellation and time limits.
- **Trade-offs:** heavy optional footprint (numpy, pandas, protobuf, absl-py); no optimality certificate; memory limit
  only for pure SAT (ORE enforces memory at process level); multi-threaded runs are not deterministic (ORE default:
  one worker).
- **Alternatives considered:** Z3 first — exact, native lexicographic and Pareto, but weaker at scale and without a proof
  object for optimisation; recommended as the **independent exact cross-checker** in Phase 10. HiGHS first — light, LP
  duals; better for continuous LP with exact certificates in Phase 10. SCIP — revisit when an exact-enabled build is
  installable.
- **The spike (F6.0.2) must confirm on this machine (Python 3.9.6 and 3.13):** installation; status and bound behaviour
  on scaled integer objectives; `stop_search()` and time limits; identical results with one worker; process-level memory
  limits on macOS, Linux and Windows; infeasibility core output.

## 4. Could not verify (to the spike)

PySCIPOpt exact mode failing at runtime on pip wheels; HiGHS IIS for MIP (documentation conflicts); HiGHS
multi-threaded determinism; SciPy cancellation; Z3 determinism and Python 3.9 testing; SoPlex exact duals; installed
sizes (only download sizes known); native multi-objective support in CP-SAT and SCIP (none found, not proven absent);
whether the next OR-Tools release keeps Python 3.9.
