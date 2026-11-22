"""Helpers shared by commands and hooks: task loading and status summaries."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List, Tuple
from aidw.constants import DEP_GATES, NEXT, REFERENCE, STAGES
from aidw.core.gates import approval_status, check_freshness, plan_steps
from aidw.infra.gitutil import change_set, code_fingerprint, find_repo
from aidw.infra.text import sha256_file, short
from aidw.records.parsers import blocking_deps
from aidw.store.config import load_config, task_dir
from aidw.store.state import load_state, read_active


def require_task(args: argparse.Namespace) -> Tuple[Path, Dict[str, Any], Dict[str, Any]]:
    repo = find_repo(args.repo)
    cfg = load_config(repo)
    state = load_state(repo, args.task)
    return repo, cfg, state


def status_line(repo: Path, state: Dict[str, Any]) -> str:
    deps = blocking_deps(repo, state, DEP_GATES) if (task_dir(repo, state["id"]) / "dependencies.md").exists() else []
    gate_index = {"spec": STAGES.index("SPEC_APPROVAL"), "plan": STAGES.index("PLAN_APPROVAL"),
                  "implementation": STAGES.index("IMPLEMENTATION"), "completion": STAGES.index("FINAL_REPORT")}
    stage_i = STAGES.index(state["stage"])
    blocking_now = [d for d in deps if gate_index.get(d["gate"] or "", 99) <= stage_i + 1]
    if state["status"] == "closed":
        return f"CLOSED — {state.get('outcome')}"
    if blocking_now:
        first = blocking_now[0]
        return f"BLOCKED — Awaiting {first['summary'] or first['id']} ({first['owner'] or 'owner not set'})"
    if state["status"] == "paused":
        return f"PAUSED — {state['stage']}"
    return state["stage"]


def task_summary(repo: Path, cfg: Dict[str, Any], state: Dict[str, Any], detailed: bool) -> Dict[str, Any]:
    slug = state["id"]
    summary: Dict[str, Any] = {
        "task": slug, "title": state.get("title"), "type": state.get("type"), "stage": state["stage"],
        "stage_number": STAGES.index(state["stage"]) + 1, "status": state["status"], "outcome": state.get("outcome"),
        "status_line": status_line(repo, state), "updated_at": state.get("updated_at"),
    }
    if not detailed:
        return summary
    approvals = {}
    for doc_name in ("spec", "plan"):
        record = state["approvals"].get(doc_name)
        ok, message = approval_status(repo, state, doc_name)
        current = task_dir(repo, slug) / f"{doc_name}.md"
        approvals[doc_name] = {"valid": ok, "message": message,
                               "approved_version": record["version"] if record else None,
                               "current_sha256": short(sha256_file(current)) if current.exists() else None}
    summary["approvals"] = approvals
    steps = plan_steps(repo, state)
    summary["progress"] = {s: state["progress"].get(s, {}).get("status", "todo") for s in steps}
    warnings: List[str] = []
    stage_i = STAGES.index(state["stage"])
    if stage_i < STAGES.index("IMPLEMENTATION") and state["baseline"].get("start"):
        pre = change_set(repo, state["baseline"]["start"], state.get("excluded", []))["task"]
        if pre:
            warnings.append("Files changed since the task started, before any implementation was approved: " +
                            ", ".join(sorted(pre)[:10]) + (" …" if len(pre) > 10 else "") +
                            ". If you made them, revert them; otherwise ask the user and exclude them with `scope --exclude`.")
    if stage_i >= STAGES.index("TESTING"):
        fingerprint = code_fingerprint(repo)
        for check, result, freshness in check_freshness(repo, state, cfg, fingerprint):
            if freshness != "fresh":
                warnings.append(f"Required check '{check['id']}' is {freshness}.")
    active = read_active(repo)
    summary["active_here"] = bool(active and active.get("task") == slug)
    summary["warnings"] = warnings
    summary["next"] = NEXT[state["stage"]] if state["status"] != "closed" else "The task is closed."
    if state["status"] == "paused":
        summary["next"] = f"Resume first: `workflow.py resume {slug} --agent <you>`. Then: {summary['next']}"
    summary["read"] = REFERENCE[state["stage"]]
    return summary


def print_summary(info: Dict[str, Any]) -> None:
    print(f"AIDevWorkflow task '{info['task']}' ({info.get('type')}): {info.get('title')}")
    print(f"Status: {info['status_line']}  ·  stage {info['stage_number']}/11  ·  {info['status']}"
          + ("  ·  active in this checkout" if info.get("active_here") else ""))
    for doc_name, data in info.get("approvals", {}).items():
        marker = "valid" if data["valid"] else "not valid"
        print(f"{doc_name.capitalize()}: {marker} — {data['message']} (current file {data['current_sha256'] or 'missing'})")
    if info.get("progress"):
        print("Progress: " + ", ".join(f"{s} {st}" for s, st in info["progress"].items()))
    for warning in info.get("warnings", []):
        print(f"Warning: {warning}")
    print(f"Next: {info['next']}")
    print(f"Read: {info['read']}")
