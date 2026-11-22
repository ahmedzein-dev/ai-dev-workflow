"""F6.0.2 hands-on spike: OR-Tools CP-SAT as the first optional ORE solver (D-037, conditions C1-C13).

Throwaway trial code, not product code. Run it inside an isolated virtual environment that has `ortools`:

    python -I trial.py            # all tests, JSON results on stdout, summary on stderr

The harness mirrors the planned ORE design so the conditions can be tested end to end:
- a solver-neutral adapter interface with two adapters (built-in exact enumerator, CP-SAT) (C1, C8);
- exact model data (Fractions from strings, floats rejected) scaled exactly to integers, with an int64 pre-check (C4, C7);
- a verifier that never trusts the solver: exact feasibility and objective re-check, configuration check, exact bound
  (C5, C6, C8);
- an execution controller that runs the solver in a separate process with wall-clock kill, an RSS watchdog and
  cancellation (C10, C11).
"""
from __future__ import annotations

import itertools
import json
import os
import platform
import random
import signal
import subprocess
import sys
import threading
import time
from fractions import Fraction
from math import lcm
from typing import Any, Dict, List, Optional, Tuple

INT_SAFE = 2**62  # ORE's own headroom below int64 for every scaled linear expression (CP-SAT also checks overflow)
GUARANTEE_RANK = {"G0": 0, "G1": 1, "G2": 2, "G3": 3}
REQUIRED_LEVEL = "G2"  # D-034 default: exact = G2 or G3; never lowered automatically (owner R5)
PROOF_LABEL = {"G3": "independently certified",
               "G2": "proven by the solver under the approved model, not independently certified"}  # owner P-2, R4

# --------------------------------------------------------------------------------------------- model (ore/1 subset)
# {"vars": [{"name", "lb", "ub"}], "constraints": [{"name", "terms": {var: "p/q"}, "op": "<=|>=|==", "rhs": "p/q",
#   "enforce": var (optional Boolean)}], "objective": {"sense": "min|max", "terms": {...}, "constant": "p/q"}}


def frac(value: Any) -> Fraction:
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError(f"floats are rejected, use an exact decimal string: {value!r}")
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, str):
        return Fraction(value)
    raise ValueError(f"not an exact number: {value!r}")


def validate(model: Dict[str, Any]) -> Tuple[str, str]:
    """Model status before solving (policy section 1): valid, invalid_model, numerical_uncertainty."""
    try:
        names = set()
        for v in model["vars"]:
            if not isinstance(v["lb"], int) or not isinstance(v["ub"], int) or isinstance(v["lb"], bool):
                return "invalid_model", f"variable {v['name']}: bounds must be integers"
            if v["lb"] > v["ub"]:
                return "invalid_model", f"variable {v['name']}: empty domain {v['lb']}..{v['ub']}"
            names.add(v["name"])
        exprs = [(c["terms"], c["rhs"]) for c in model["constraints"]]
        if model.get("objective"):
            exprs.append((model["objective"]["terms"], model["objective"].get("constant", "0")))
        for c in model["constraints"]:
            if c["op"] not in ("<=", ">=", "=="):
                return "invalid_model", f"constraint {c['name']}: unknown operator {c['op']}"
            if c.get("enforce") is not None:
                ev = next((v for v in model["vars"] if v["name"] == c["enforce"]), None)
                if ev is None or (ev["lb"], ev["ub"]) != (0, 1):
                    return "invalid_model", f"constraint {c['name']}: enforcement needs a Boolean variable"
        for terms, rhs in exprs:
            frac(rhs)
            for name, coef in terms.items():
                if name not in names:
                    return "invalid_model", f"unknown variable {name}"
                frac(coef)
    except (KeyError, ValueError, ZeroDivisionError) as exc:
        return "invalid_model", str(exc)
    bounds = {v["name"]: max(abs(v["lb"]), abs(v["ub"])) for v in model["vars"]}
    for terms, rhs in exprs:
        ints, scaled_rhs, _ = scale(terms, rhs)
        if sum(abs(c) * bounds[n] for n, c in ints.items()) + abs(scaled_rhs) > INT_SAFE:
            return "numerical_uncertainty", "scaled coefficients exceed the int64 headroom (never rounded)"
    return "valid", ""


def scale(terms: Dict[str, Any], rhs: Any) -> Tuple[Dict[str, int], int, int]:
    """Exact scaling by the least common denominator: returns integer terms, integer rhs, multiplier."""
    fr = {n: frac(c) for n, c in terms.items()}
    r = frac(rhs)
    mult = 1
    for f in list(fr.values()) + [r]:
        mult = lcm(mult, f.denominator)
    ints = {n: int(f * mult) for n, f in fr.items() if f != 0}
    return ints, int(r * mult), mult


def holds(c: Dict[str, Any], values: Dict[str, int]) -> bool:
    if c.get("enforce") is not None and values[c["enforce"]] == 0:
        return True
    lhs = sum(frac(k) * values[n] for n, k in c["terms"].items())
    rhs = frac(c["rhs"])
    return lhs <= rhs if c["op"] == "<=" else lhs >= rhs if c["op"] == ">=" else lhs == rhs


def objective_exact(model: Dict[str, Any], values: Dict[str, int]) -> Fraction:
    obj = model["objective"]
    return sum((frac(k) * values[n] for n, k in obj["terms"].items()), frac(obj.get("constant", "0")))


# ------------------------------------------------------------------------------------------ adapters (C1: neutral)


def raw(adapter: str, guarantee: str, **kw: Any) -> Dict[str, Any]:
    out = {"adapter": adapter, "guarantee": guarantee, "termination": "completed", "solution_status": "unknown",
           "values": None, "reported_objective": None, "exact_bound": None, "config": {}, "info": {}}
    out.update(kw)
    return out


class EnumeratorAdapter:
    """Built-in exhaustive enumerator: standard library, exact fractions, G3 by construction."""
    name = "enumerator"
    capabilities = {"guarantee": "G3", "variables": "bounded integer", "constraints": "linear, enforced linear",
                    "max_space": 2_000_000}

    def solve(self, model: Dict[str, Any], limits: Dict[str, Any]) -> Dict[str, Any]:
        space = 1
        for v in model["vars"]:
            space *= v["ub"] - v["lb"] + 1
        if space > self.capabilities["max_space"]:
            return raw(self.name, "G3", termination="not_run", info={"reason": f"search space {space} too large"})
        names = [v["name"] for v in model["vars"]]
        pos = {n: i for i, n in enumerate(names)}
        # exact integer forms (same Fractions, scaled), evaluated directly; the result is re-checked by the verifier
        rows = []
        for c in model["constraints"]:
            ints, rhs, _ = scale(c["terms"], c["rhs"])
            rows.append(([(pos[n], k) for n, k in ints.items()], c["op"], rhs,
                         pos[c["enforce"]] if c.get("enforce") is not None else None))
        obj_ints, _, _ = scale(model["objective"]["terms"], "0")
        obj = [(pos[n], k) for n, k in obj_ints.items()]
        best, best_val, sense = None, None, model["objective"]["sense"]
        for combo in itertools.product(*[range(v["lb"], v["ub"] + 1) for v in model["vars"]]):
            ok = True
            for terms, op, rhs, enf in rows:
                if enf is not None and combo[enf] == 0:
                    continue
                lhs = sum(k * combo[i] for i, k in terms)
                if not (lhs <= rhs if op == "<=" else lhs >= rhs if op == ">=" else lhs == rhs):
                    ok = False
                    break
            if ok:
                val = sum(k * combo[i] for i, k in obj)
                if best_val is None or (val < best_val if sense == "min" else val > best_val):
                    best, best_val = combo, val
        if best is not None:
            best = dict(zip(names, best))
            best_val = objective_exact(model, best)
        if best is None:
            return raw(self.name, "G3", solution_status="infeasible_claimed", info={"space": space})
        return raw(self.name, "G3", solution_status="optimal_claimed", values=best, exact_bound=str(best_val),
                   reported_objective=str(best_val), info={"space": space, "exhaustive": True})


class CpSatAdapter:
    """OR-Tools CP-SAT. Receives only exactly scaled integers; strict parameters unless a test overrides them."""
    name = "cpsat"
    capabilities = {"guarantee": "G2", "variables": "bounded integer/Boolean", "constraints": "linear, enforced linear",
                    "conditions": "integer objective, status OPTIMAL, gaps 0, exact bound == exact objective"}

    def build(self, model: Dict[str, Any]) -> Tuple[Any, Dict[str, Any], int]:
        from ortools.sat.python import cp_model
        md = cp_model.CpModel()
        xs = {v["name"]: md.new_int_var(v["lb"], v["ub"], v["name"]) for v in model["vars"]}
        lits = {}
        for c in model["constraints"]:
            ints, rhs, _ = scale(c["terms"], c["rhs"])
            expr = sum(k * xs[n] for n, k in ints.items())
            ct = md.add(expr <= rhs) if c["op"] == "<=" else md.add(expr >= rhs) if c["op"] == ">=" \
                else md.add(expr == rhs)
            if c.get("enforce") is not None:
                ct.only_enforce_if(xs[c["enforce"]])
            if c.get("assumption"):
                lit = md.new_bool_var("lit_" + c["name"])
                ct.only_enforce_if(lit)
                lits[c["name"]] = lit
        obj_ints, _, obj_mult = scale(model["objective"]["terms"], "0")
        expr = sum(k * xs[n] for n, k in obj_ints.items())
        md.minimize(expr) if model["objective"]["sense"] == "min" else md.maximize(expr)
        if lits:
            md.add_assumptions(list(lits.values()))
        return md, {"xs": xs, "lits": lits}, obj_mult

    def solve(self, model: Dict[str, Any], limits: Dict[str, Any], stop_event: Optional[threading.Event] = None,
              overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        from ortools.sat.python import cp_model
        md, h, obj_mult = self.build(model)
        solver = cp_model.CpSolver()
        p = solver.parameters
        p.num_workers = limits.get("threads", 1)
        p.max_time_in_seconds = limits.get("time", 60)
        p.absolute_gap_limit = 0.0  # C7: strict; the default 1e-4 is harmless only on integer objectives
        p.relative_gap_limit = 0.0
        p.random_seed = limits.get("seed", 0)
        p.max_memory_in_mb = limits.get("memory_mb", 1024)
        if "deterministic_time" in limits:
            p.max_deterministic_time = limits["deterministic_time"]
        if "conflicts" in limits:
            p.max_number_of_conflicts = limits["conflicts"]
        for k, v in (overrides or {}).items():
            setattr(p, k, v)
        stopped = {"requested": False}
        if stop_event is not None:
            def watch() -> None:
                stop_event.wait()
                stopped["requested"] = True
                solver.stop_search()
            threading.Thread(target=watch, daemon=True).start()
        status = solver.solve(md)
        r = solver.response_proto
        name = solver.status_name(status)
        config = {"absolute_gap_limit": p.absolute_gap_limit, "relative_gap_limit": p.relative_gap_limit,
                  "num_workers": p.num_workers, "max_time_in_seconds": p.max_time_in_seconds,
                  "random_seed": p.random_seed, "max_memory_in_mb": p.max_memory_in_mb}
        info = {"status": name, "wall_time": round(solver.wall_time, 4), "deterministic_time": solver.deterministic_time,
                "branches": solver.num_branches, "conflicts": solver.num_conflicts,
                "solution_info": solver.solution_info(), "best_bound_double": solver.best_objective_bound}
        # termination reason is inferred: the response has no explicit limit field
        termination = "completed"
        if name in ("FEASIBLE", "UNKNOWN"):
            if stopped["requested"]:
                termination = "cancelled"
            elif "conflicts" in limits and solver.num_conflicts >= limits["conflicts"]:
                termination = "resource_limit"
            elif "deterministic_time" in limits and solver.deterministic_time >= limits["deterministic_time"]:
                termination = "resource_limit"
            elif solver.wall_time >= p.max_time_in_seconds * 0.95:
                termination = "time_limit"
            else:
                termination = "unknown_limit"
        if name == "MODEL_INVALID":
            return raw(self.name, "G2", termination="solver_error", solution_status="no_solution", config=config,
                       info={**info, "validation": md.validate()})
        if name == "INFEASIBLE":
            core = None
            if h["lits"]:
                idx = set(solver.sufficient_assumptions_for_infeasibility())
                core = [n for n, lit in h["lits"].items() if lit.index in idx]
            return raw(self.name, "G2", solution_status="infeasible_claimed", config=config, info={**info, "core": core})
        if name not in ("OPTIMAL", "FEASIBLE"):
            return raw(self.name, "G2", termination=termination, solution_status="no_solution", config=config, info=info)
        values = {n: int(solver.value(x)) for n, x in h["xs"].items()}
        # Exact bound from the int64 inner bound (never from the double): inner objective is minimised, so for a
        # maximisation (scaling_factor -1) the bound on the user objective is its negation.
        sf = md.proto.objective.scaling_factor or 1.0
        inner_lb = r.inner_objective_lower_bound
        bound_scaled = inner_lb if sf > 0 else -inner_lb
        const = frac(model["objective"].get("constant", "0"))
        exact_bound = Fraction(bound_scaled, obj_mult) + const
        return raw(self.name, "G2", termination=termination,
                   solution_status="optimal_claimed" if name == "OPTIMAL" else "feasible", values=values,
                   reported_objective=repr(solver.objective_value), exact_bound=str(exact_bound), config=config,
                   info={**info, "objective_multiplier": obj_mult, "inner_lower_bound": inner_lb})


ADAPTERS = {"enumerator": EnumeratorAdapter(), "cpsat": CpSatAdapter()}

# ---------------------------------------------------------------------------------------- verifier (C5, C6, C8)


def verify(model: Dict[str, Any], model_status: str, res: Optional[Dict[str, Any]],
           required: str = REQUIRED_LEVEL) -> Dict[str, Any]:
    """Computes verification and classification from the four dimensions; never trusts the solver's claim."""
    out: Dict[str, Any] = {"model_status": model_status, "required_level": required, "solver_claim": None,
                           "verification": "not_verified", "level_reached": None, "problems": []}
    if model_status != "valid":
        out["classification"] = model_status.upper()
        return out
    assert res is not None
    out["solver_claim"] = res["solution_status"]
    out["termination"] = res["termination"]
    term = res["termination"]
    if res["values"] is not None:
        values = res["values"]
        if set(values) != {v["name"] for v in model["vars"]} or any(
                not (v["lb"] <= values[v["name"]] <= v["ub"]) for v in model["vars"]):
            out["problems"].append("solution outside variable domains")
        broken = [c["name"] for c in model["constraints"] if not holds(c, values)]
        if broken:
            out["problems"].append(f"constraints violated: {broken}")
        obj = objective_exact(model, values)
        out["exact_objective"] = str(obj)
        if res["adapter"] == "cpsat":
            # the solver's double must be the correctly rounded exact objective; a mismatch is a failure
            ints, _, mult = scale(model["objective"]["terms"], "0")
            scaled = sum(k * values[n] for n, k in ints.items())
            if model["objective"].get("constant", "0") in ("0", 0) and mult == 1 and \
                    float(scaled) != float(res["reported_objective"]):
                out["problems"].append("reported objective differs from the exact objective")
        if out["problems"]:
            out["verification"] = "failed"
            out["classification"] = "VERIFICATION_FAILED"
            return out
        level = "G0"
        evidence = []
        if res["guarantee"] == "G3" and res["info"].get("exhaustive"):
            level = "G3"
            evidence.append("exhaustive enumeration")
        elif res["guarantee"] == "G2" and res["solution_status"] == "optimal_claimed":
            gaps_zero = res["config"].get("absolute_gap_limit") == 0 and res["config"].get("relative_gap_limit") == 0
            bound = Fraction(res["exact_bound"])
            if not gaps_zero:
                evidence.append("gap limits not zero: configuration does not meet the strict policy")
            if bound != obj:
                evidence.append(f"exact bound {bound} != exact objective {obj}: gap {abs(obj - bound)}")
            if gaps_zero and bound == obj:
                level = "G2"
                evidence.append("status OPTIMAL, gaps 0, exact bound == exact objective")
        out["evidence"] = evidence
        out["level_reached"] = level
        if term == "cancelled":  # owner P-1: distinct; a feasible solution is kept separately, never as optimal
            out["verification"] = "feasibility_only"
            out["classification"] = "CANCELLED"
            out["feasible_solution"] = {"values": values, "exact_objective": str(obj),
                                        "note": "found before cancellation; feasibility verified; not optimal"}
            return out
        if GUARANTEE_RANK[level] >= GUARANTEE_RANK[required]:
            out["verification"] = "verified"
            out["classification"] = "PROVEN_OPTIMAL"
            out["proof"] = PROOF_LABEL[level]
        else:
            out["verification"] = "feasibility_only"
            out["classification"] = "FEASIBLE_NOT_PROVEN"
            if res.get("exact_bound") is not None:
                out["gap"] = str(abs(obj - Fraction(res["exact_bound"])))
        return out
    if res["solution_status"] == "infeasible_claimed":
        level = res["guarantee"]
        out["level_reached"] = level
        if GUARANTEE_RANK[level] >= GUARANTEE_RANK[required]:
            out["classification"] = "PROVEN_INFEASIBLE"
            out["proof"] = PROOF_LABEL[level]
        else:
            out["classification"] = "UNKNOWN"
            out["evidence"] = [f"infeasibility established at {level}, below the required {required}"]
        if res["info"].get("core") is not None:
            out["conflict_set"] = res["info"]["core"]
            out["conflict_set_minimal"] = "not proven"  # owner P-2: minimal only when proven
        return out
    out["classification"] = {"time_limit": "TIMEOUT", "memory_limit": "RESOURCE_LIMIT",
                             "resource_limit": "RESOURCE_LIMIT", "solver_error": "SOLVER_ERROR",
                             "cancelled": "CANCELLED", "not_run": "UNSUPPORTED_PROBLEM"}.get(term, "UNKNOWN")
    return out


# ---------------------------------------------------------------------------- execution controller (C10, C11)


IS_WINDOWS = sys.platform == "win32"


class _Win:
    """Minimal Windows job-object and memory API through ctypes (standard library)."""

    def __init__(self) -> None:
        import ctypes
        from ctypes import wintypes
        self.ctypes, self.wintypes = ctypes, wintypes
        k = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
        self.k = k
        H = wintypes.HANDLE
        k.CreateJobObjectW.restype = H
        k.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        k.SetInformationJobObject.argtypes = [H, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        k.AssignProcessToJobObject.argtypes = [H, H]
        k.TerminateJobObject.argtypes = [H, wintypes.UINT]
        k.OpenProcess.restype = H
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.CloseHandle.argtypes = [H]

        class IoCounters(ctypes.Structure):
            _fields_ = [(n, ctypes.c_ulonglong) for n in ("r", "w", "o", "rb", "wb", "ob")]

        class Basic(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                        ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD)]

        class Extended(ctypes.Structure):
            _fields_ = [("Basic", Basic), ("Io", IoCounters), ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t),
                        ("PeakJobMemoryUsed", ctypes.c_size_t)]

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (n, ctypes.c_size_t) for n in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                                               "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                                               "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
        class PidList(ctypes.Structure):
            _fields_ = [("Assigned", wintypes.DWORD), ("InList", wintypes.DWORD),
                        ("Ids", ctypes.c_size_t * 256)]
        self.Extended, self.Counters, self.PidList = Extended, Counters, PidList
        k.K32GetProcessMemoryInfo.argtypes = [H, ctypes.POINTER(Counters), wintypes.DWORD]
        k.QueryInformationJobObject.argtypes = [H, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p]

    def job_for(self, pid: int, memory_mb: Optional[int]) -> Any:
        """Job object that kills the whole tree on close; with a per-process committed-memory limit if asked."""
        c = self.ctypes
        job = self.k.CreateJobObjectW(None, None)
        info = self.Extended()
        info.Basic.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if memory_mb:
            info.Basic.LimitFlags |= 0x100  # JOB_OBJECT_LIMIT_PROCESS_MEMORY
            info.ProcessMemoryLimit = memory_mb * 1024 * 1024
        if not self.k.SetInformationJobObject(job, 9, c.byref(info), c.sizeof(info)):
            raise OSError(c.get_last_error(), "SetInformationJobObject failed")  # type: ignore[attr-defined]
        h = self.k.OpenProcess(0x0100 | 0x0001, False, pid)  # PROCESS_SET_QUOTA | PROCESS_TERMINATE
        ok = self.k.AssignProcessToJobObject(job, h)
        self.k.CloseHandle(h)
        if not ok:
            raise OSError(c.get_last_error(), "AssignProcessToJobObject failed")  # type: ignore[attr-defined]
        return job

    def job_pids(self, job: Any) -> List[int]:
        info = self.PidList()
        ok = self.k.QueryInformationJobObject(job, 3, self.ctypes.byref(info), self.ctypes.sizeof(info), None)
        return [int(info.Ids[i]) for i in range(info.InList)] if ok else []

    def rss_kb(self, pid: int) -> int:
        h = self.k.OpenProcess(0x1000 | 0x0010, False, pid)  # QUERY_LIMITED_INFORMATION | VM_READ
        if not h:
            return 0
        cnt = self.Counters()
        cnt.cb = self.ctypes.sizeof(cnt)
        ok = self.k.K32GetProcessMemoryInfo(h, self.ctypes.byref(cnt), cnt.cb)
        self.k.CloseHandle(h)
        return int(cnt.WorkingSetSize // 1024) if ok else 0


WIN = _Win() if IS_WINDOWS else None


def tree_rss_kb(proc: "subprocess.Popen[str]", job: Any) -> int:
    """Resident memory of the child and everything it started, measured from outside, on each platform.

    Needed because a process may not do the work itself: on Windows the python.exe of a virtual environment is a
    launcher that runs the real interpreter as its own child (found by the CI run of this trial).
    """
    if WIN is not None:
        return sum(WIN.rss_kb(pid) for pid in WIN.job_pids(job))
    if sys.platform.startswith("linux"):
        total = 0
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            try:
                with open(f"/proc/{entry}/stat", encoding="ascii", errors="replace") as fh:
                    fields = fh.read().rsplit(")", 1)[1].split()
                if int(fields[2]) == proc.pid:  # process group (the child leads its own session)
                    total += rss_kb(int(entry))
            except (OSError, IndexError, ValueError):
                continue
        return total
    try:
        out = subprocess.run(["ps", "-o", "rss=", "-g", str(proc.pid)], capture_output=True, text=True,
                             timeout=2).stdout
        return sum(int(x) for x in out.split())
    except (ValueError, subprocess.TimeoutExpired):
        return 0


def rss_kb(pid: int) -> int:
    """Resident memory of one process, measured from outside it, on each platform."""
    if WIN is not None:
        return WIN.rss_kb(pid)
    if sys.platform.startswith("linux"):
        try:
            with open(f"/proc/{pid}/status", encoding="ascii") as fh:
                for line in fh:
                    if line.startswith("VmRSS:"):
                        return int(line.split()[1])
        except OSError:
            return 0
        return 0
    try:
        out = subprocess.run(["ps", "-o", "rss=", "-p", str(pid)], capture_output=True, text=True, timeout=2).stdout
        return int(out.strip() or 0)
    except (ValueError, subprocess.TimeoutExpired):
        return 0


def kill_tree(proc: "subprocess.Popen[str]", job: Any) -> str:
    """Stops the child and everything it started: process group on POSIX, job object on Windows."""
    if WIN is not None:
        WIN.k.TerminateJobObject(job, 1)
        proc.wait(timeout=10)
        return "TerminateJobObject"
    os.killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=2)
        return "SIGTERM to process group"
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)  # type: ignore[attr-defined]
        proc.wait()
        return "SIGKILL to process group"


def run_isolated(job: Dict[str, Any], wall: float, memory_mb: int, cancel_after: Optional[float] = None,
                 os_limit_mb: Optional[int] = None) -> Dict[str, Any]:
    """Runs a job in a child process; enforces wall clock and RSS from outside the solver.

    os_limit_mb asks the operating system for a hard memory limit as well: POSIX RLIMIT_AS (set by the child before any
    work) or a Windows job-object process memory limit (set by this controller before the job is sent).
    """
    env = dict(os.environ, AIDW_TRIAL_OSLIMIT=str(os_limit_mb) if os_limit_mb and not IS_WINDOWS else "")
    t0 = time.monotonic()
    kw: Dict[str, Any] = {"creationflags": 0x00000200} if IS_WINDOWS else {"start_new_session": True}
    proc = subprocess.Popen([sys.executable, "-I", os.path.abspath(__file__), "--child"], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, **kw)
    win_job, os_limit = None, None
    if WIN is not None:
        win_job = WIN.job_for(proc.pid, os_limit_mb)
        os_limit = f"job object process memory limit {os_limit_mb} MB" if os_limit_mb else None
    assert proc.stdin is not None
    proc.stdin.write(json.dumps(job))
    proc.stdin.close()
    reason, peak, how = None, 0, None
    while proc.poll() is None:
        elapsed = time.monotonic() - t0
        peak = max(peak, tree_rss_kb(proc, win_job))
        if cancel_after is not None and elapsed >= cancel_after:
            reason = "cancelled"
        elif elapsed >= wall:
            reason = "time_limit"
        elif peak > memory_mb * 1024:
            reason = "memory_limit"
        if reason:
            how = kill_tree(proc, win_job)
            break
        time.sleep(0.05)
    elapsed = round(time.monotonic() - t0, 3)
    stdout = proc.stdout.read() if proc.stdout else ""
    stderr = proc.stderr.read() if proc.stderr else ""
    if win_job is not None and WIN is not None:
        WIN.k.CloseHandle(win_job)
    result = None
    if reason is None and proc.returncode == 0 and stdout.strip():
        result = json.loads(stdout)
    return {"killed_for": reason, "stopped_by": how, "returncode": proc.returncode, "elapsed": elapsed,
            "peak_rss_mb": round(peak / 1024), "os_limit": os_limit, "result": result,
            "stderr_tail": stderr.strip().splitlines()[-1:] if stderr.strip() else []}


def child() -> None:
    lim = os.environ.get("AIDW_TRIAL_OSLIMIT")
    os_note = None
    if lim:
        import resource
        notes = []
        for rname in ("RLIMIT_AS", "RLIMIT_DATA"):
            res_id = getattr(resource, rname)
            hard = resource.getrlimit(res_id)[1]
            try:
                resource.setrlimit(res_id, (int(lim) * 1024 * 1024, hard))  # soft limit only
                notes.append(f"{rname} soft limit set")
            except (ValueError, OSError) as exc:
                notes.append(f"{rname} setrlimit failed: {exc}")
        os_note = "; ".join(notes)
    job = json.loads(sys.stdin.read())
    if job["kind"] == "spawn":  # the work happens in a grandchild: the watchdog must see and stop the whole tree
        sub = subprocess.Popen([sys.executable, "-I", os.path.abspath(__file__), "--child"], stdin=subprocess.PIPE,
                               text=True)
        assert sub.stdin is not None
        sub.stdin.write(json.dumps(job["job"]))
        sub.stdin.close()
        sub.wait()
        return
    if job["kind"] == "hog":
        blocks = []
        try:
            for _ in range(job["mb"]):
                blocks.append(bytearray(b"\x01" * (1024 * 1024)))  # written, so the pages are really committed
                time.sleep(job.get("delay", 0))
            print(json.dumps({"allocated_mb": len(blocks), "os_limit": os_note}))
        except MemoryError:
            print(json.dumps({"memory_error_after_mb": len(blocks), "os_limit": os_note}))
        return
    if job["kind"] == "solve":
        t0 = time.process_time()
        res = CpSatAdapter().solve(job["model"], job["limits"], overrides=job.get("overrides"))
        res["child_cpu_s"] = round(time.process_time() - t0, 3)  # CPU of all threads of this process
        res["os_limit"] = os_note
        print(json.dumps(res))


# -------------------------------------------------------------------------------------------------- generators


def random_model(rng: random.Random, medium: bool = False) -> Dict[str, Any]:
    n = rng.randint(5, 6) if medium else rng.randint(2, 4)
    vs = []
    for i in range(n):
        lb = rng.randint(-4, 2)
        vs.append({"name": f"x{i}", "lb": lb, "ub": lb + rng.randint(3 if medium else 0, 7 if medium else 5)})
    has_b = rng.random() < 0.5
    if has_b:
        vs.append({"name": "b", "lb": 0, "ub": 1})
    names = [v["name"] for v in vs]

    def rf() -> str:
        return str(Fraction(rng.randint(-9, 9), rng.choice([1, 1, 2, 3, 4, 6])))
    point = {v["name"]: rng.randint(v["lb"], v["ub"]) for v in vs}  # most constraints hold here: mix of answers
    cons = []
    for j in range(rng.randint(3, 6) if medium else rng.randint(1, 4)):
        terms = {nm: rf() for nm in rng.sample(names, rng.randint(1, len(names)))}
        op = rng.choice(["<=", ">=", "<=", "=="])
        at = sum(Fraction(k) * point[nm] for nm, k in terms.items())
        slack = Fraction(rng.randint(0, 6), rng.choice([1, 2, 3]))
        rhs = (at + slack if op == "<=" else at - slack if op == ">=" else at) if rng.random() < 0.8 else Fraction(rf())
        c = {"name": f"c{j}", "terms": terms, "op": op, "rhs": str(rhs)}
        if has_b and rng.random() < 0.4:
            c["enforce"] = "b"
        cons.append(c)
    obj = {"sense": rng.choice(["min", "max"]), "terms": {nm: rf() for nm in names}, "constant": rf()}
    return {"vars": vs, "constraints": cons, "objective": obj}


def market_split(seed: int, m: int, n: int, optimise: bool) -> Dict[str, Any]:
    """Cornuejols-Dawande style instances: tiny to state, very hard to prove (binary, 0-99 coefficients)."""
    rng = random.Random(seed)
    vs = [{"name": f"x{j}", "lb": 0, "ub": 1} for j in range(n)]
    cons, obj_terms = [], {}
    for i in range(m):
        a = [rng.randint(0, 99) for _ in range(n)]
        rhs = sum(a) // 2
        terms = {f"x{j}": str(a[j]) for j in range(n)}
        if optimise:  # rhs - a.x = p - q with p, q >= 0; minimise sum(p + q)
            vs += [{"name": f"p{i}", "lb": 0, "ub": 5000}, {"name": f"q{i}", "lb": 0, "ub": 5000}]
            terms.update({f"p{i}": "-1", f"q{i}": "1"})
            obj_terms.update({f"p{i}": "1", f"q{i}": "1"})
        cons.append({"name": f"row{i}", "terms": terms, "op": "==", "rhs": str(rhs)})
    if not optimise:
        obj_terms = {"x0": "0"}
    return {"vars": vs, "constraints": cons, "objective": {"sense": "min", "terms": obj_terms, "constant": "0"}}


def solve_verified(model: Dict[str, Any], adapter: str, limits: Dict[str, Any], required: str = REQUIRED_LEVEL,
                   **kw: Any) -> Dict[str, Any]:
    status, why = validate(model)
    res = ADAPTERS[adapter].solve(model, limits, **kw) if status == "valid" else None
    v = verify(model, status, res, required)
    if why:
        v["why"] = why
    return {"raw": res, "verdict": v}


# ------------------------------------------------------------------------------------------------------- tests

STRICT = {"threads": 1, "time": 20, "seed": 0}


def t_correctness(count: int, medium: bool = False) -> Dict[str, Any]:
    """C9: CP-SAT vs exhaustive enumeration on random small models with known (enumerated) answers."""
    rng = random.Random(20261122 + (1 if medium else 0))
    tally: Dict[str, int] = {}
    mismatches = []
    for i in range(count):
        model = random_model(rng, medium)
        e = solve_verified(model, "enumerator", STRICT)["verdict"]
        c = solve_verified(model, "cpsat", STRICT)["verdict"]
        key = f"{e['classification']}"
        tally[key] = tally.get(key, 0) + 1
        same = e["classification"] == c["classification"] and e.get("exact_objective") == c.get("exact_objective")
        if not same:
            mismatches.append({"i": i, "enumerator": e, "cpsat": c, "model": model})
    return {"models": count, "by_classification": tally, "mismatches": len(mismatches), "examples": mismatches[:3],
            "pass": not mismatches}


def t_gap_trap() -> Dict[str, Any]:
    """C6/C7/C8: OPTIMAL status reached through a gap limit is not accepted; strict gaps are."""
    model = market_split(7, 4, 30, optimise=True)
    trap = solve_verified(model, "cpsat", {"threads": 1, "time": 10}, overrides={"absolute_gap_limit": 50.0})
    rel = solve_verified(model, "cpsat", {"threads": 1, "time": 10}, overrides={"relative_gap_limit": 0.99})
    small = {"vars": [{"name": "x", "lb": 0, "ub": 10}, {"name": "y", "lb": 0, "ub": 10}],
             "constraints": [{"name": "cap", "terms": {"x": "1", "y": "2"}, "op": "<=", "rhs": "13"}],
             "objective": {"sense": "max", "terms": {"x": "3/2", "y": "2"}, "constant": "1/3"}}
    strict = solve_verified(small, "cpsat", STRICT)
    enum = solve_verified(small, "enumerator", STRICT)
    ok = (trap["raw"]["info"]["status"] == "OPTIMAL" and trap["verdict"]["classification"] == "FEASIBLE_NOT_PROVEN"
          and strict["verdict"]["classification"] == "PROVEN_OPTIMAL"
          and strict["verdict"]["exact_objective"] == enum["verdict"]["exact_objective"])
    return {"absolute_gap_50": trap, "relative_gap_0_99": rel, "strict_small": strict,
            "enumerator_small": enum["verdict"], "pass": ok}


def t_precision() -> Dict[str, Any]:
    """C7: objective values beyond 2^53 lose precision as doubles; the exact path uses ints only."""
    big = 2**55 + 1
    model = {"vars": [{"name": "x", "lb": 0, "ub": 1}, {"name": "y", "lb": 0, "ub": 1}],
             "constraints": [{"name": "one", "terms": {"x": "1", "y": "1"}, "op": "<=", "rhs": "1"}],
             "objective": {"sense": "max", "terms": {"x": str(big), "y": str(big - 1)}, "constant": "0"}}
    r = solve_verified(model, "cpsat", STRICT)
    reported = r["raw"]["reported_objective"]
    return {"exact_objective": r["verdict"].get("exact_objective"), "solver_double": reported,
            "double_equals_exact": float(reported) == big and int(float(reported)) == big,
            "double_as_int": int(float(reported)), "exact_bound": r["raw"]["exact_bound"],
            "classification": r["verdict"]["classification"],
            "pass": r["verdict"]["classification"] == "PROVEN_OPTIMAL" and r["raw"]["exact_bound"] == str(big)}


def t_overflow_and_floats() -> Dict[str, Any]:
    """C4/C7: no silent rounding; overflow refused before the solver; the solver's own refusals recorded."""
    from ortools.sat.python import cp_model
    primes = [101, 103, 107, 109, 113, 127, 131, 137, 139, 149]
    lcd_model = {"vars": [{"name": f"x{i}", "lb": 0, "ub": 10**6} for i in range(len(primes))],
                 "constraints": [{"name": "c", "terms": {f"x{i}": f"1/{p}" for i, p in enumerate(primes)},
                                  "op": "<=", "rhs": "1"}],
                 "objective": {"sense": "max", "terms": {"x0": "1"}, "constant": "0"}}
    lcd = solve_verified(lcd_model, "cpsat", STRICT)["verdict"]
    float_model = {"vars": [{"name": "x", "lb": 0, "ub": 3}], "constraints": [],
                   "objective": {"sense": "min", "terms": {"x": 0.1}, "constant": "0"}}
    flt = solve_verified(float_model, "cpsat", STRICT)["verdict"]
    md = cp_model.CpModel()
    a = md.new_int_var(0, 2**61, "a")
    b = md.new_int_var(0, 2**61, "b")
    md.add(4 * a + 4 * b <= 5)
    solver_status = cp_model.CpSolver().status_name(cp_model.CpSolver().solve(md))
    raises = {}
    for label, fn in [("float in constraint", lambda m, x: m.add(0.5 * x <= 3)),
                      ("2^63 coefficient", lambda m, x: m.add((2**63) * x <= 3))]:
        m2 = cp_model.CpModel()
        x2 = m2.new_int_var(0, 10, "x")
        try:
            fn(m2, x2)
            raises[label] = "accepted"
        except TypeError as exc:
            raises[label] = "TypeError: " + str(exc)[:70]
    m3 = cp_model.CpModel()
    x3 = m3.new_int_var(0, 10, "x")
    m3.minimize(0.1 * x3 + 0.25)
    raises["float objective"] = "accepted silently as floating_point_objective" if \
        m3.proto.has_floating_point_objective() else "rejected"
    ok = lcd["classification"] == "NUMERICAL_UNCERTAINTY" and flt["classification"] == "INVALID_MODEL" and \
        solver_status == "MODEL_INVALID"
    return {"lcd_overflow_precheck": lcd, "float_input": flt, "cpsat_overflow_status": solver_status,
            "cpsat_api": raises, "pass": ok}


def t_infeasible() -> Dict[str, Any]:
    """C10/ORE-I/P-2: contradictory constraints; G2 label; conflict set minimal only when proven."""
    model = {"vars": [{"name": "a", "lb": 0, "ub": 5}, {"name": "b", "lb": 0, "ub": 5}, {"name": "c", "lb": 0, "ub": 5}],
             "constraints": [
                 {"name": "budget", "terms": {"a": "1", "b": "1"}, "op": "<=", "rhs": "3", "assumption": True},
                 {"name": "need_a", "terms": {"a": "1"}, "op": ">=", "rhs": "2", "assumption": True},
                 {"name": "need_b", "terms": {"b": "1"}, "op": ">=", "rhs": "2", "assumption": True},
                 {"name": "c_small", "terms": {"c": "1"}, "op": "<=", "rhs": "4", "assumption": True}],
             "objective": {"sense": "max", "terms": {"a": "1", "b": "1", "c": "1"}, "constant": "0"}}

    def subset(names: Any) -> Dict[str, Any]:
        return dict(model, constraints=[k for k in model["constraints"] if k["name"] in names])
    c = solve_verified(model, "cpsat", STRICT)
    e = solve_verified(model, "enumerator", STRICT)
    reported = list(c["raw"]["info"].get("core") or [])
    # deletion filter with CP-SAT: drop a constraint while the rest stays infeasible
    shrunk = list(reported)
    for name in list(shrunk):
        rest = [n for n in shrunk if n != name]
        if solve_verified(subset(rest), "cpsat", STRICT)["verdict"]["classification"] == "PROVEN_INFEASIBLE":
            shrunk = rest
    # minimality proof: the set is infeasible (G2) and every set without one member has an exactly verified solution
    set_infeasible = solve_verified(subset(shrunk), "cpsat", STRICT)["verdict"]["classification"] == "PROVEN_INFEASIBLE"
    witnesses = {}
    for name in shrunk:
        v = solve_verified(subset([n for n in shrunk if n != name]), "cpsat", STRICT)["verdict"]
        witnesses[name] = v["classification"] == "PROVEN_OPTIMAL" and v["problems"] == []
    minimal_proven = set_infeasible and all(witnesses.values())
    enum_shrunk = solve_verified(subset(shrunk), "enumerator", STRICT)["verdict"]["classification"]
    return {"cpsat_verdict": c["verdict"], "enumerator": e["verdict"]["classification"],
            "enumerator_proof": e["verdict"].get("proof"),
            "reported_conflict_set": reported, "reported_set_minimal": len(shrunk) == len(reported) and minimal_proven,
            "deletion_filter_set": shrunk, "deletion_filter_minimal_proven": minimal_proven,
            "minimality_evidence": "set infeasible at G2; each set without one member has an exactly verified solution",
            "deletion_filter_set_infeasible_by_enumeration_G3": enum_shrunk == "PROVEN_INFEASIBLE",
            "pass": c["verdict"]["classification"] == e["verdict"]["classification"] == "PROVEN_INFEASIBLE"
            and c["verdict"].get("proof") == PROOF_LABEL["G2"] and c["verdict"].get("conflict_set_minimal") == "not proven"
            and minimal_proven and enum_shrunk == "PROVEN_INFEASIBLE"}


def t_no_downgrade() -> Dict[str, Any]:
    """R4/R5: a G2 result never satisfies a G3 requirement, and the requirement is never lowered automatically."""
    small = {"vars": [{"name": "x", "lb": 0, "ub": 10}, {"name": "y", "lb": 0, "ub": 10}],
             "constraints": [{"name": "cap", "terms": {"x": "1", "y": "2"}, "op": "<=", "rhs": "13"}],
             "objective": {"sense": "max", "terms": {"x": "3/2", "y": "2"}, "constant": "1/3"}}
    bad = dict(small, constraints=small["constraints"] + [
        {"name": "big", "terms": {"x": "1", "y": "1"}, "op": ">=", "rhs": "30"}])
    cp_g3 = solve_verified(small, "cpsat", STRICT, required="G3")["verdict"]
    en_g3 = solve_verified(small, "enumerator", STRICT, required="G3")["verdict"]
    cp_inf_g3 = solve_verified(bad, "cpsat", STRICT, required="G3")["verdict"]
    return {"cpsat_required_G3": {k: cp_g3.get(k) for k in ("classification", "level_reached", "required_level")},
            "enumerator_required_G3": {k: en_g3.get(k) for k in ("classification", "level_reached", "proof")},
            "cpsat_infeasible_required_G3": {k: cp_inf_g3.get(k) for k in ("classification", "level_reached",
                                                                            "evidence")},
            "pass": cp_g3["classification"] == "FEASIBLE_NOT_PROVEN" and cp_g3["required_level"] == "G3"
            and en_g3["classification"] == "PROVEN_OPTIMAL" and cp_inf_g3["classification"] == "UNKNOWN"}


def t_limits_and_cancel() -> Dict[str, Any]:
    """C10/C11/ORE-J: time limit with and without a solution, resource limit, invalid model, cancellation."""
    opt = market_split(7, 4, 30, optimise=True)
    feas = market_split(7, 4, 30, optimise=False)
    out: Dict[str, Any] = {}
    r = solve_verified(opt, "cpsat", {"threads": 1, "time": 1.0})
    out["timeout_with_solution"] = {"status": r["raw"]["info"]["status"], "termination": r["raw"]["termination"],
                                    "classification": r["verdict"]["classification"], "gap": r["verdict"].get("gap")}
    r = solve_verified(feas, "cpsat", {"threads": 1, "time": 1.0})
    out["timeout_no_solution"] = {"status": r["raw"]["info"]["status"], "termination": r["raw"]["termination"],
                                  "classification": r["verdict"]["classification"]}
    r = solve_verified(feas, "cpsat", {"threads": 1, "time": 30, "conflicts": 2000})
    out["conflict_limit"] = {"status": r["raw"]["info"]["status"], "termination": r["raw"]["termination"],
                             "classification": r["verdict"]["classification"], "conflicts": r["raw"]["info"]["conflicts"]}
    bad = {"vars": [{"name": "x", "lb": 5, "ub": 3}], "constraints": [],
           "objective": {"sense": "min", "terms": {"x": "1"}, "constant": "0"}}
    out["invalid_model"] = solve_verified(bad, "cpsat", STRICT)["verdict"]
    ev = threading.Event()
    timer = threading.Timer(0.5, ev.set)
    t0 = time.monotonic()
    timer.start()
    r = solve_verified(opt, "cpsat", {"threads": 1, "time": 30}, stop_event=ev)
    out["cancel_in_process"] = {"status": r["raw"]["info"]["status"], "termination": r["raw"]["termination"],
                                "classification": r["verdict"]["classification"],
                                "feasible_solution_kept": "feasible_solution" in r["verdict"],
                                "returned_after_s": round(time.monotonic() - t0, 3)}
    iso = run_isolated({"kind": "solve", "model": opt, "limits": {"threads": 1, "time": 600}}, wall=60,
                       memory_mb=2048, cancel_after=1.0)
    out["cancel_process_group"] = {k: iso[k] for k in ("killed_for", "stopped_by", "returncode", "elapsed", "peak_rss_mb")}
    iso = run_isolated({"kind": "solve", "model": opt, "limits": {"threads": 1, "time": 600}}, wall=1.5,
                       memory_mb=2048)
    out["hard_wall_clock_kill"] = {k: iso[k] for k in ("killed_for", "stopped_by", "returncode", "elapsed", "peak_rss_mb")}
    ok = (out["timeout_with_solution"]["classification"] == "FEASIBLE_NOT_PROVEN"
          and out["timeout_no_solution"]["classification"] == "TIMEOUT"
          and out["conflict_limit"]["classification"] in ("RESOURCE_LIMIT", "FEASIBLE_NOT_PROVEN")
          and out["invalid_model"]["classification"] == "INVALID_MODEL"
          and out["cancel_in_process"]["classification"] == "CANCELLED"
          and out["cancel_in_process"]["feasible_solution_kept"]
          and out["cancel_process_group"]["killed_for"] == "cancelled"
          and out["hard_wall_clock_kill"]["killed_for"] == "time_limit")
    out["pass"] = ok
    return out


def t_memory() -> Dict[str, Any]:
    """C11: memory limits from outside the solver; what the OS and CP-SAT give on this platform."""
    out: Dict[str, Any] = {}
    watched = run_isolated({"kind": "hog", "mb": 2048, "delay": 0.002}, wall=60, memory_mb=300)
    out["rss_watchdog_300mb"] = {k: watched[k] for k in ("killed_for", "stopped_by", "returncode", "elapsed", "peak_rss_mb")}
    tree = run_isolated({"kind": "spawn", "job": {"kind": "hog", "mb": 2048, "delay": 0.002}}, wall=90, memory_mb=300)
    out["rss_watchdog_grandchild_300mb"] = {k: tree[k] for k in ("killed_for", "stopped_by", "returncode", "elapsed",
                                                                 "peak_rss_mb")}
    small = market_split(3, 2, 12, optimise=True)
    base = run_isolated({"kind": "solve", "model": small, "limits": {"threads": 1, "time": 5}}, wall=30,
                        memory_mb=4096)
    out["cpsat_child_peak_rss_small_model"] = {"peak_rss_mb": base["peak_rss_mb"], "elapsed": base["elapsed"],
                                               "killed_for": base["killed_for"], "stderr_tail": base["stderr_tail"],
                                               "status": (base["result"] or {}).get("info", {}).get("status")}
    big = market_split(11, 40, 400, optimise=True)
    mm = run_isolated({"kind": "solve", "model": big, "limits": {"threads": 1, "time": 8, "memory_mb": 64}},
                      wall=60, memory_mb=4096)
    out["cpsat_max_memory_in_mb_64"] = {"peak_rss_mb": mm["peak_rss_mb"], "elapsed": mm["elapsed"],
                                        "killed_for": mm["killed_for"], "stderr_tail": mm["stderr_tail"],
                                        "status": (mm["result"] or {}).get("info", {}).get("status"),
                                        "termination": (mm["result"] or {}).get("termination")}
    out["pass"] = watched["killed_for"] == "memory_limit" and tree["killed_for"] == "memory_limit" and \
        base["result"] is not None and mm["result"] is not None
    return out


def t_memory_os_limit() -> Dict[str, Any]:
    """C11/R1: does the operating system stop a 2 GB allocation under a 1 GB limit? (RSS watchdog disabled)

    POSIX: RLIMIT_AS soft limit set by the child; Windows: job-object process memory limit set by the controller.
    """
    r = run_isolated({"kind": "hog", "mb": 2048}, wall=120, memory_mb=100000, os_limit_mb=1024)
    out = {k: r.get(k) for k in ("killed_for", "returncode", "elapsed", "peak_rss_mb", "os_limit", "result",
                                 "stderr_tail")}
    res = r["result"] or {}
    stopped_early = "memory_error_after_mb" in res or (r["returncode"] not in (0, None) and r["killed_for"] is None)
    out["enforced"] = stopped_early and res.get("allocated_mb") != 2048
    out["platform"] = sys.platform
    # a platform fact on macOS (setrlimit fails there); Linux and Windows are expected to enforce it
    out["pass"] = None if sys.platform == "darwin" else out["enforced"]
    return out


def t_threads_and_determinism() -> Dict[str, Any]:
    """C11: num_workers=1 really uses one core; identical runs are reproducible under a deterministic limit."""
    opt = market_split(7, 4, 30, optimise=True)
    cpu = {}
    for w in (1, 4):
        iso = run_isolated({"kind": "solve", "model": opt, "limits": {"threads": w, "time": 3}}, wall=60, memory_mb=4096)
        res = iso["result"] or {}
        used, wall = res.get("child_cpu_s", 0.0), res.get("info", {}).get("wall_time", 0.0) or 1e-9
        cpu[f"workers_{w}"] = {"cpu_s": used, "solver_wall_s": wall, "cpu_per_wall": round(used / wall, 2)}
    runs = []
    for _ in range(5):
        r = solve_verified(opt, "cpsat", {"threads": 1, "time": 60, "deterministic_time": 2.0})
        runs.append((json.dumps(r["raw"]["values"], sort_keys=True), r["raw"]["info"]["branches"],
                     r["raw"]["info"]["conflicts"], r["verdict"].get("exact_objective")))
    wall_runs = []
    for _ in range(3):
        r = solve_verified(opt, "cpsat", {"threads": 1, "time": 1.0})
        wall_runs.append((r["raw"]["info"]["branches"], r["verdict"].get("exact_objective")))
    det = len(set(runs)) == 1
    return {"cpu": cpu, "deterministic_limit_identical_runs": det,
            "deterministic_runs": [{"branches": b, "conflicts": c, "objective": o} for _, b, c, o in runs],
            "wall_limit_runs": [{"branches": b, "objective": o} for b, o in wall_runs],
            "pass": det and cpu["workers_1"]["cpu_per_wall"] < 1.3}


def environment() -> Dict[str, Any]:
    from importlib import metadata
    t0 = time.perf_counter()
    import ortools
    from ortools.sat.python import cp_model  # noqa: F401
    imp = time.perf_counter() - t0
    probe = "import time; t = time.perf_counter(); from ortools.sat.python import cp_model; print(time.perf_counter() - t)"
    fresh = []
    for _ in range(3):  # R2: later imports in new processes, to tell a one-off cold start from a steady cost
        out = subprocess.run([sys.executable, "-I", "-c", probe], capture_output=True, text=True, timeout=600)
        fresh.append(round(float(out.stdout.strip() or "nan"), 3))
    deps = {}
    for d in ("ortools", "numpy", "pandas", "protobuf", "absl-py", "immutabledict"):
        try:
            deps[d] = metadata.version(d)
        except metadata.PackageNotFoundError:
            deps[d] = None
    return {"python": platform.python_version(), "platform": platform.platform(terse=True),
            "machine": platform.machine(), "ortools": ortools.__version__, "dependencies": deps,
            "cp_model_import_s": round(imp, 3), "cp_model_import_fresh_processes_s": fresh,
            "bytecode_writing_disabled": bool(sys.flags.dont_write_bytecode or os.environ.get("PYTHONDONTWRITEBYTECODE"))}


def main() -> int:
    if "--child" in sys.argv:
        child()
        return 0
    results: Dict[str, Any] = {"environment": environment()}
    tests = [("C9 correctness vs enumeration", lambda: t_correctness(int(os.environ.get("AIDW_TRIAL_N", "400")))),
             ("C9 correctness vs enumeration, medium models",
              lambda: t_correctness(int(os.environ.get("AIDW_TRIAL_M", "40")), medium=True)),
             ("C6 C7 C8 gap trap and strict gaps", t_gap_trap),
             ("C7 precision beyond 2^53", t_precision),
             ("C4 C7 overflow and floats", t_overflow_and_floats),
             ("C10 P-2 infeasible and conflict set", t_infeasible),
             ("R4 R5 no automatic downgrade", t_no_downgrade),
             ("C10 C11 limits and cancellation", t_limits_and_cancel),
             ("C11 memory", t_memory),
             ("C11 R1 memory OS limit", t_memory_os_limit),
             ("C11 threads and determinism", t_threads_and_determinism)]
    for name, fn in tests:
        t0 = time.monotonic()
        try:
            results[name] = fn()
        except Exception as exc:  # recorded, never hidden
            results[name] = {"error": f"{type(exc).__name__}: {exc}", "pass": False}
        results[name]["seconds"] = round(time.monotonic() - t0, 2)
        print(f"{name}: pass={results[name].get('pass')} ({results[name]['seconds']} s)", file=sys.stderr)
    print(json.dumps(results, indent=1, default=str))
    failed = [name for name, r in results.items() if isinstance(r, dict) and r.get("pass") is False]
    if failed:
        print(f"FAILED: {failed}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
