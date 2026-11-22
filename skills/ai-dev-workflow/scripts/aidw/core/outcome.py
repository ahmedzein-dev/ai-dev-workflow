"""The highest final status the evidence allows."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, cast
from aidw.constants import DEP_GATES, OUTCOME_RANK
from aidw.core.gates import approval_status, check_freshness, expected_items, plan_steps
from aidw.infra.gitutil import code_fingerprint
from aidw.records.parsers import blocking_deps, parse_audit, parse_matrix
from aidw.store.config import task_dir


def compute_outcome(repo: Path, state: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    level = 0
    reasons: List[str] = []

    def cap(new_level: int, why: str) -> None:
        nonlocal level
        level = max(level, new_level)
        reasons.append(why)

    slug = state["id"]
    for doc_name in ("spec", "plan"):
        ok, message = approval_status(repo, state, doc_name)
        if not ok:
            cap(2, message)
    blockers = blocking_deps(repo, state, DEP_GATES)
    for dep in blockers:
        cap(2, f"Blocked by {dep['id']}: {dep['summary']} (owner: {dep['owner'] or 'unassigned'}).")
    undone = [s for s in plan_steps(repo, state) if state["progress"].get(s, {}).get("status") != "done"]
    if undone:
        cap(2, f"Plan steps not done: {', '.join(undone)}.")
    if state["approvals"].get("spec"):
        rows, problems = parse_matrix(repo, slug)
        for problem in problems:
            cap(2, problem)
        for item in expected_items(repo, state, cfg):
            row = rows.get(item)
            if not row:
                cap(2, f"{item} has no verification result.")
            elif row["status"] == "Failed":
                cap(2, f"{item} failed verification.")
            elif row["status"] in ("Blocked", "Not Verified"):
                cap(1, f"{item} is {row['status']}: {row['evidence']}")
    fingerprint = code_fingerprint(repo)
    for check, result, freshness in check_freshness(repo, state, cfg, fingerprint):
        res = cast(Dict[str, Any], result)  # None only when freshness is "missing"; not read in that branch
        if freshness == "missing":
            cap(2, f"Required check '{check['id']}' was never run.")
        elif freshness == "stale":
            cap(2, f"Required check '{check['id']}' ran on older code; re-run it.")
        elif res["status"] == "failed":
            cap(2, f"Required check '{check['id']}' failed: {res.get('summary', '')}")
        elif res["status"] == "preexisting":
            cap(1, f"Check '{check['id']}': only problems that existed before the task remain ({res.get('summary', '')}).")
        elif res["status"] == "blocked":
            cap(1, f"Check '{check['id']}' could not run: {res.get('reason') or res.get('summary', '')}")
    audit = parse_audit(repo, slug) if (task_dir(repo, slug) / "audit.md").exists() else None
    if not audit or audit["problems"]:
        cap(2, "The audit is not complete.")
    if audit:
        for finding in audit["findings"]:
            sev, disp = finding["severity"], finding["disposition"]
            if sev == "Critical" and disp in ("Open", "Accepted", "Deferred"):
                cap(2, f"Critical finding {finding['id']} is {disp.lower()}.")
            elif sev == "Important" and disp in ("Open", "Deferred"):
                cap(2, f"Important finding {finding['id']} is {disp.lower()}.")
            elif sev == "Important" and disp == "Accepted":
                cap(1, f"Important finding {finding['id']} was accepted by the user, not fixed.")
    maximum = ("Completed", "Completed with Limitations", "Partially Completed")[level]
    allowed = [o for o, rank in OUTCOME_RANK.items() if rank >= level]
    if blockers:
        allowed.append("Blocked")
    return {"max": maximum, "allowed": allowed, "blocked": bool(blockers), "reasons": reasons, "fingerprint": fingerprint}
