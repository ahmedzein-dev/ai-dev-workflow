# CP-SAT technical trial (F6.0.2) — final evidence for D-037

Trial of OR-Tools CP-SAT as the first optional ORE solver, against the owner's conditions **C1–C13**, answers
**P-1–P-3** and requirements **R1–R6** (all quoted in [DECISIONS.md](../DECISIONS.md#d-037--first-optional-solver-or-tools-cp-sat-conditional)).
Run on 2026-11-22 with `ortools==9.15.6755` and the pinned dependencies in
[cpsat_trial/requirements-py39.txt](cpsat_trial/requirements-py39.txt) and
[cpsat_trial/requirements-py313.txt](cpsat_trial/requirements-py313.txt), always in throwaway virtual environments.

| Where | Python | Evidence |
|---|---|---|
| GitHub Actions `ubuntu-24.04` (x86_64, glibc 2.39) | 3.9.25, 3.13.18 | [ci/Linux-py3.9.json](cpsat_trial/ci/Linux-py3.9.json), [ci/Linux-py3.13.json](cpsat_trial/ci/Linux-py3.13.json) |
| GitHub Actions `windows-latest` (AMD64) | 3.9.13, 3.13.17 | [ci/Windows-py3.9.json](cpsat_trial/ci/Windows-py3.9.json), [ci/Windows-py3.13.json](cpsat_trial/ci/Windows-py3.13.json) |
| GitHub Actions `macos-latest` (arm64, macOS 26.7) | 3.9.13, 3.13.17 | [ci/macOS-py3.9.json](cpsat_trial/ci/macOS-py3.9.json), [ci/macOS-py3.13.json](cpsat_trial/ci/macOS-py3.13.json) |
| Owner's Mac (arm64, macOS 26.3) | 3.9.6, 3.13.2 | [local-macos-py39.json](cpsat_trial/local-macos-py39.json), [local-macos-py313.json](cpsat_trial/local-macos-py313.json) (final code); part 1 files kept |

The CI run is workflow `ore-cpsat-trial` on branch `phase-1/foundations`, commit `3837bb2`: **6 of 6 jobs passed**. The
same commit passed the engine's own test matrix (`tests`: 6 jobs and lint).

- **Trial code:** [cpsat_trial/trial.py](cpsat_trial/trial.py) (throwaway; standard library apart from OR-Tools).
- **Harness:** it mirrors the planned ORE design. It has:
  - solver-neutral adapters (built-in exact enumerator, CP-SAT);
  - exact input (fractions, floats rejected, exact integer scaling, int64 pre-check);
  - a verifier that never trusts the solver;
  - an execution controller that runs the solver in a separate process, with a wall-clock kill, a memory watchdog over
    the whole process tree, operating-system memory limits, cancellation and pipe draining.

## 1. Verdict

**Every condition and requirement is met on Linux, Windows and macOS with Python 3.9 and 3.13, for bounded
integer/Boolean models with linear and (enforced) linear constraints, provided ORE implements the controls in §4.**
The trial exposes no reason to lower the proof standard, and none was lowered (C13, R5).

- **Recommendation:** final adoption of CP-SAT as the first optional ORE solver, for the `ore/1` v1 model scope only.
- **Status:** D-037 stays *approved in principle* until the owner reviews this evidence.

Two platform facts limit the claims:
- **macOS memory:** macOS offers no operating-system memory limit for these processes (`setrlimit` fails), so there the
  memory limit rests on ORE's watchdog alone.
- **Cold start:** the 38–42 s first import was reproduced on the owner's Mac only; its exact cause is not proven (§3.4).

## 2. Results by condition and requirement

| ID | Condition | Result | Evidence (all 8 runs unless stated) |
|---|---|---|---|
| C1 | Extensible adapter architecture | **Met** | One verifier, classification and controller for both adapters; CP-SAT declares its capabilities like any adapter |
| C2 / R3 | Core light; OR-Tools optional and isolated | **Met** | In CI the engine is imported **inside the environment that has OR-Tools** and loads none of numpy, pandas, ortools, protobuf, absl (6 platforms). The engine's tests never install OR-Tools |
| C3 | Python 3.9; macOS, Windows, Linux | **Met — tested at runtime on all three** | Pinned versions installed with `--only-binary :all:` and `pip check` clean on every platform; Python 3.9 uses numpy 2.0.2 and pandas 2.3.3 |
| C4 | Integer models only; no silent rounding | **Met with an ORE guard** | Float input → `INVALID_MODEL`. CP-SAT rejects floats in constraints but silently accepts a float objective, so the adapter never passes one |
| C5 | Constraints, objective, bound, gap verified | **Met** | Exact re-check in fractions; exact bound from the int64 `inner_objective_lower_bound`; exact gap |
| C6 | Never trust `OPTIMAL` alone | **Met — the trap reproduced everywhere** | With `absolute_gap_limit=50`, CP-SAT returned **`OPTIMAL`** with a gap of 24 (Linux, Windows) or 50 (macOS); the verifier classified every case `FEASIBLE_NOT_PROVEN` |
| C7 | Strict gaps; precision; overflow | **Met** | Gaps forced to 0 and checked. Objective 2^55+1: the double reads …968, the exact path …969. Int64 overflow refused before solving (`NUMERICAL_UNCERTAINTY`) and by CP-SAT (`MODEL_INVALID`) |
| C8 / R4 | Solver-proven vs certified kept apart | **Met** | Each verdict records `solver_claim`, `level_reached`, `verification` and a proof label: G2 "proven by the solver under the approved model, not independently certified"; G3 "independently certified" |
| C9 | Agreement with exhaustive enumeration | **Met: 0 mismatches** | 1,650 models per run (1,225 + 116 optimal, 275 + 34 infeasible), identical counts on all 8 runs |
| C10 | Failure cases | **Met** | §3.1 |
| C11 / R1 | Real time, memory, thread limits; Linux and Windows | **Met** | §3.2 and §3.3 |
| C12 | Limits and proof level documented | **Met** | §4–§6 |
| C13 / R5 | No relaxed criteria; no automatic downgrade | **Met** | With G3 required, a CP-SAT optimum stays `FEASIBLE_NOT_PROVEN` (level G2 recorded), and CP-SAT infeasibility stays `UNKNOWN` with "established at G2, below the required G3"; the enumerator reaches G3 |
| P-1 | `CANCELLED` distinct; feasible solution kept apart | **Met** | Cancelled run → `CANCELLED`, with its verified feasible solution under `feasible_solution` ("found before cancellation; feasibility verified; not optimal") |
| P-2 | G2 infeasibility label; minimal only when proven | **Met** | CP-SAT infeasibility → `PROVEN_INFEASIBLE` with the G2 label; its conflict set (4 constraints) is marked `conflict_set_minimal: not proven`. A deletion filter reduced it to 3, **proven minimal** (the set infeasible at G2; each set without one member has an exactly verified solution), and confirmed at G3 by enumeration |
| P-3 | Pinned versions per Python version | **Met** | Requirements files above; installs on all platforms reproduce the tested versions |
| R2 | 46 s cold start documented and investigated | **Done** | §3.4 |
| R6 | Untested platforms and unsupported models not marked verified | **Met** | §6 lists what is not covered |

## 3. Measurements

### 3.1 Scenarios (same classification on all 8 runs)

| Scenario | CP-SAT status | Termination | ORE classification |
|---|---|---|---|
| Strict gaps, small rational model | OPTIMAL | completed | `PROVEN_OPTIMAL` (G2), 107/6, equal to enumeration |
| Gap trap: absolute gap 50 | **OPTIMAL** | completed | `FEASIBLE_NOT_PROVEN`, gap 24 or 50 |
| Contradictory constraints (ORE-I) | INFEASIBLE | completed | `PROVEN_INFEASIBLE` (G2 label) |
| Hard instance, 1 s, a solution exists (ORE-J) | FEASIBLE | time_limit | `FEASIBLE_NOT_PROVEN` |
| Hard feasibility instance, 1 s | UNKNOWN | time_limit | `TIMEOUT` |
| Conflict limit 2,000 | UNKNOWN | resource_limit | `RESOURCE_LIMIT` |
| Empty domain | — (ORE validation) | — | `INVALID_MODEL` |
| `stop_search` after 0.5 s | FEASIBLE | cancelled | `CANCELLED`, feasible solution kept apart; returned in 0.50–0.54 s |

### 3.2 Execution controller

| Control | Linux | Windows | macOS |
|---|---|---|---|
| Cancel the process tree at 1 s | 1.02–1.05 s (process group) | 1.01–1.03 s (job object) | 1.02 s (process group) |
| Hard wall clock 1.5 s (solver limit 600 s) | 1.52–1.54 s | 1.52–1.55 s | 1.64–1.65 s |
| Memory watchdog 300 MB, the process itself | stopped at 302 MB | stopped at 302–314 MB | stopped at 302–307 MB |
| Memory watchdog 300 MB, a **grandchild** process | stopped at 304–305 MB | stopped at 301–313 MB | stopped at 303–311 MB |
| Operating-system limit 1 GB, 2 GB requested | **enforced** (RLIMIT_AS: stopped near 1,000 MB) | **enforced** (job object: stopped near 1,003 MB) | **not available** (`setrlimit` fails) |
| CP-SAT `max_memory_in_mb=64` | not enforced (115–126 MB) | not enforced (96–104 MB) | not enforced (108–116 MB) |
| 1 MB of child output | completed in 0.05 s | completed in 0.10 s | completed in 0.09–0.18 s |

### 3.3 Threads and reproducibility

| | Linux | Windows | macOS |
|---|---|---|---|
| CPU per wall-second, 1 worker | 1.17 | 1.08–1.11 | 1.10–1.24 |
| CPU per wall-second, 4 workers | 4.06–4.07 | 3.95–4.00 | 2.95–2.99 |
| 5 runs, 1 worker, deterministic time 2.0 | identical | identical | identical |
| Same, compared across platforms | 63,695 branches | 50,163 branches | 48,235 branches |
| 3 runs with a 1 s wall-clock limit | branches differ | branches differ | branches differ |

One worker uses one core; the slightly higher ratio includes the child's own model building. A run is reproducible
only with one worker, a deterministic time limit, and the same platform and versions. Its search path, and possibly
which feasible solution it reports, differs between platforms. A verified optimum's value never depends on that path.

### 3.4 Cold start (R2)

| Where | First `cp_model` import in a fresh environment | Later imports |
|---|---|---|
| Owner's Mac, Python 3.9 (original trial) | 46 s | 0.83 s |
| Owner's Mac, Python 3.9, new environment (pip compiled) | **38.5 s** | 0.84 s |
| Owner's Mac, Python 3.9, new environment, no bytecode at all | **38.7 s** | 0.84 s |
| Owner's Mac, copy of an already warmed environment | **41.3 s** | — |
| Owner's Mac, only loading `libortools.9.dylib` in a fresh copy | **23.2 s** (then 15.7 s for the rest) | — |
| Owner's Mac, Python 3.13, new environment | **42.3 s** | 0.24 s |
| CI Linux / Windows / macOS (first import right after `pip install`, workflow log) | 0.24–0.72 s | 0.22–0.71 s |

- **Reproducible on the owner's Mac:** every new install or copy of the native libraries pays 38–42 s once, on both
  Python versions.
- **Not reproduced elsewhere:** not on Linux, not on Windows, and not on GitHub's macOS image.
- **Not Python bytecode:** the delay is the same without any bytecode.
- **Follows new native-library files:** a copy of a warm environment is slow again, and loading `libortools` alone takes
  23 s.
- **Signing:** the libraries are ad-hoc signed (`codesign`: `adhoc,linker-signed`).
- **Most likely cause, not proven:** a security check on the owner's Mac when a newly written, unnotarised native
  library is loaded for the first time.
- **Consequence for ORE:** the opt-in install (F6.2.3) warms the import once after installing, says so to the user, and
  never counts that time against a solve's time limit.

## 4. Controls ORE must implement (inputs to F6.2.3, F6.3.x, F6.4.1, F2.5.2)

1. **Exact integers only.**
   - Scale exact fractions by the least common denominator.
   - Int64 headroom 2^62 → otherwise `NUMERICAL_UNCERTAINTY`; never round.
   - Before solving, assert `not has_floating_point_objective()`.
2. **Strict parameters, recorded with every run:**
   - gaps 0;
   - `num_workers=1` by default;
   - a fixed seed;
   - the policy time limit.
   - The verifier rejects a G2 claim made under any other configuration.
3. **No doubles in verification.**
   - Recompute the objective exactly.
   - Take the bound from the int64 `inner_objective_lower_bound`; negate it for maximisation.
4. **G2 rule:** status `OPTIMAL`, gaps 0, exact bound equal to the exact objective, and an exact feasibility re-check.
   **G3 needs an independent method.** Labels as in P-2 and R4.
5. **Classification:**
   - `CANCELLED` is distinct, and a feasible solution found before it is kept apart (P-1).
   - Termination reasons are inferred from counters, because CP-SAT has no field for them; kills by the controller are
     authoritative.
6. **Conflict sets** are "these constraints conflict together". They are called minimal only after a proof (deletion
   filter plus exactly verified witnesses) (P-2).
7. **Execution controller** (found necessary by this trial):
   - (a) measure memory over the **whole process tree**: the process group on POSIX, the job object on Windows. The
     python.exe of a Windows virtual environment is a launcher whose child does the work;
   - (b) **drain stdout and stderr while the child runs.** A Windows pipe holds about 4 KB; a child writing more blocked
     until the wall-clock kill;
   - (c) stop the tree: process group on POSIX, job object with kill-on-close on Windows;
   - (d) operating-system memory limit where it exists (Linux RLIMIT_AS, Windows job object), plus the watchdog
     everywhere. On macOS, the watchdog only;
   - (e) never rely on `max_memory_in_mb`.
8. **Reproducibility:** use one worker and `max_deterministic_time` for reproducible runs, and record platform and
   versions with the evidence.
9. **Install:**
   - pinned versions per Python version (P-3), in a separate environment (C2, R3);
   - warm the import after installing (§3.4);
   - any upgrade re-runs this trial (compatibility, correctness against enumeration, optimality rules, regression)
     before approval.

## 5. Trade-offs

| Item | Measured |
|---|---|
| Installed size | 145 MB (Python 3.9) – 201 MB (Python 3.13) per environment |
| Download | 20–28 MB wheel per platform, plus numpy, pandas, protobuf, absl-py, immutabledict, typing-extensions |
| Warm import | 0.21–0.72 s (all CI platforms); 0.24 s (3.13) / 0.83 s (3.9) on the owner's Mac |
| Memory per solver process | 76–110 MB on small models |
| Highest proof level | G2 for integer models under §4; never G3 alone; no optimality certificate |
| Platform support (wheels) | Linux needs glibc 2.27/2.28+ (no musl/Alpine); Windows x64 only (no Windows on Arm); macOS arm64 and x86_64 |
| Python 3.9 | supported by OR-Tools 9.15 with numpy 2.0.2 (the last numpy for 3.9); a later OR-Tools may drop 3.9, so the pin matters |

## 6. Not covered (not marked verified, R6)

- **Models outside `ore/1` v1:**
  - continuous variables (CP-SAT scales them approximately);
  - float objectives;
  - nonlinear or global constraints beyond enforced linear ones;
  - native multi-objective (ORE runs lexicographic stages itself; not trialled yet);
  - large or industrial-size models (only small and medium models were compared with enumeration).
- **Platforms not tested:** Windows on Arm (no wheel), Linux on aarch64 (wheel exists, not run), Alpine/musl (no
  wheel), macOS x86_64 (wheel exists, not run), Python 3.10–3.12 and 3.14 (wheels exist, not run).
- **Memory limit on macOS:** no operating-system limit is available there; the watchdog samples every 50 ms, so a very
  fast allocation can overshoot between samples. In the trial it overshot by at most 17 MB (300 MB limit).
- **Z3 and HiGHS** hands-on checks (Phase 10 candidates).
- **Cold start:** the exact mechanism on the owner's Mac (§3.4).
