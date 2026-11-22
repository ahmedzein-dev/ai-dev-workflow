"""Approvals, check freshness and stage transitions."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from aidw.constants import STAGES
from aidw.core.spec import plan_check, spec_check, spec_rules_and_template, verification_items
from aidw.errors import WorkflowError
from aidw.infra.gitutil import code_fingerprint
from aidw.infra.text import bullet_list, read_text, sha256_file, short
from aidw.records.markdown import Doc
from aidw.records.parsers import parse_audit, parse_dependencies, parse_matrix
from aidw.store.config import task_dir
from aidw.store.state import add_history


def approval_status(repo: Path, state: Dict[str, Any], doc_name: str) -> Tuple[bool, str]:
    record = state["approvals"].get(doc_name)
    if not record:
        return False, f"The {doc_name} has not been approved."
    tdir = task_dir(repo, state["id"])
    snapshot = tdir / record["snapshot"]
    if not snapshot.exists():
        return False, f"The approved {doc_name} snapshot {record['snapshot']} is missing."
    if sha256_file(snapshot) != record["sha256"]:
        return False, f"The approved {doc_name} snapshot {record['snapshot']} was modified."
    current = tdir / f"{doc_name}.md"
    if not current.exists() or sha256_file(current) != record["sha256"]:
        return False, (f"{doc_name}.md changed after v{record['version']} was approved; the change needs the "
                       "user's renewed approval.")
    if doc_name == "plan":
        spec_record = state["approvals"].get("spec")
        if not spec_record or record.get("spec_sha256") != spec_record.get("sha256"):
            return False, "The plan approval belongs to an older spec version; the plan needs renewed approval."
        ok, message = approval_status(repo, state, "spec")
        if not ok:
            return False, message
    return True, f"v{record['version']} approved ({short(record['sha256'])})"


def approved_doc(repo: Path, state: Dict[str, Any], doc_name: str) -> Optional[Doc]:
    record = state["approvals"].get(doc_name)
    if not record:
        return None
    path = task_dir(repo, state["id"]) / record["snapshot"]
    return Doc(read_text(path)) if path.exists() else None


def plan_steps(repo: Path, state: Dict[str, Any]) -> List[str]:
    doc = approved_doc(repo, state, "plan")
    return [ident for ident, _, _, _ in doc.items.get("S", [])] if doc else []


def latest_results(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    latest: Dict[str, Dict[str, Any]] = {}
    for entry in state.get("checks", []):
        if entry.get("kind", "result") == "result":
            latest[entry["id"]] = entry
    return latest


def check_freshness(repo: Path, state: Dict[str, Any], cfg: Dict[str, Any],
                    fingerprint: Optional[str] = None) -> List[Tuple[Dict[str, Any], Optional[Dict[str, Any]], str]]:
    """(check, latest result, state) for each required check; state is fresh, stale or missing."""
    fingerprint = fingerprint or code_fingerprint(repo)
    latest = latest_results(state)
    rows: List[Tuple[Dict[str, Any], Optional[Dict[str, Any]], str]] = []
    for check in cfg.get("checks", []):
        if not check.get("required"):
            continue
        result = latest.get(check["id"])
        if not result:
            rows.append((check, None, "missing"))
        elif result.get("fingerprint") != fingerprint:
            rows.append((check, result, "stale"))
        else:
            rows.append((check, result, "fresh"))
    return rows


def expected_items(repo: Path, state: Dict[str, Any], cfg: Dict[str, Any]) -> List[str]:
    doc = approved_doc(repo, state, "spec")
    if doc is None:
        return []
    tpl, rules, _, _ = spec_rules_and_template(repo, cfg)
    return [ident for ident, _ in verification_items(doc, rules, tpl)]


def forward_problems(repo: Path, state: Dict[str, Any], cfg: Dict[str, Any], target: str) -> List[str]:
    slug = state["id"]
    problems: List[str] = []
    if target == "DEPENDENCIES":
        discovery = state.get("discovery") or {}
        if not discovery.get("inspected"):
            problems.append("Record the files you inspected: `discover <task> --inspected <paths>`.")
        if not (discovery.get("summary") or "").strip():
            problems.append("Record the discovery summary (goal, scope, exclusions, affected areas): "
                            "`discover <task> --summary \"…\"`.")
    elif target == "SPECIFICATION":
        deps = parse_dependencies(repo, slug)
        if not deps["classified"]:
            problems.append("Classify dependencies in dependencies.md, or write "
                            "'No dependencies identified — <reason>'.")
        problems += deps["problems"]
    elif target == "SPEC_APPROVAL":
        spec_result = spec_check(repo, state, cfg)
        problems += [f"[{p['rule']}] {p['message']}" for p in spec_result["mandatory"]]
        problems += [f"[flag] {f['message']}" for f in spec_result["flags"]]
        pending = [k for k, v in spec_result["judgment"].items() if v["status"] != "pass"]
        if pending:
            problems.append(f"Review not recorded for this spec version: {', '.join(pending)} (`review <task> --pass …`).")
    elif target == "PLANNING":
        problems.append("PLANNING starts only through `approve <task> spec`, after the user's explicit approval.")
    elif target == "PLAN_APPROVAL":
        ok, message = approval_status(repo, state, "spec")
        if not ok:
            problems.append(message)
        problems += [f"[{p['rule']}] {p['message']}" for p in plan_check(repo, state)["mandatory"]]
    elif target == "IMPLEMENTATION":
        problems.append("IMPLEMENTATION starts only through `approve <task> plan`, after the user's explicit approval.")
    elif target == "TESTING":
        for doc_name in ("spec", "plan"):
            ok, message = approval_status(repo, state, doc_name)
            if not ok:
                problems.append(message)
        undone = [s for s in plan_steps(repo, state) if state["progress"].get(s, {}).get("status") != "done"]
        if undone:
            problems.append(f"Plan steps not marked done: {', '.join(undone)} (`step <task> <S#> done`).")
    elif target == "AUDIT":
        fingerprint = code_fingerprint(repo)
        for check, result, freshness in check_freshness(repo, state, cfg, fingerprint):
            if freshness != "fresh":
                problems.append(f"Required check '{check['id']}' is {freshness}; run it on the current code.")
            elif result and result["status"] == "failed":
                problems.append(f"Required check '{check['id']}' failed; move to FIXING.")
        rows, matrix_problems = parse_matrix(repo, slug)
        problems += matrix_problems
        missing = [i for i in expected_items(repo, state, cfg) if i not in rows]
        if missing:
            problems.append(f"No verification result for: {', '.join(missing)}.")
        failed = [i for i, row in rows.items() if row["status"] == "Failed"]
        if failed:
            problems.append(f"Failed items: {', '.join(failed)}; move to FIXING, or report the task as Partially Completed.")
    elif target == "FINAL_REPORT":
        audit = parse_audit(repo, slug)
        problems += audit["problems"]
        if audit["open"]:
            problems.append(f"Findings still Open: {', '.join(audit['open'])}. Fix them (FIXING), or record the "
                            "user's acceptance, or defer Minor ones.")
    return problems


def transition(repo: Path, state: Dict[str, Any], cfg: Dict[str, Any], target: str, reason: Optional[str], agent: str) -> None:
    current = state["stage"]
    if state["status"] == "closed":
        raise WorkflowError("The task is closed.")
    if target not in STAGES:
        raise WorkflowError(f"Unknown stage {target}. Stages: {', '.join(STAGES)}.")
    ci, ti = STAGES.index(current), STAGES.index(target)
    if ti == ci:
        raise WorkflowError(f"The task is already in {target}.")
    early_report = target == "FINAL_REPORT" and current != "AUDIT"
    if ti < ci:
        if not reason:
            raise WorkflowError("Moving back to an earlier stage needs --reason.")
    elif early_report:
        if not reason:
            raise WorkflowError("Going to FINAL_REPORT before the audit is finished needs --reason "
                                "(the report will be Partially Completed or Blocked).")
    else:
        allowed = {ci + 1}
        if current == "TESTING":
            allowed.add(STAGES.index("AUDIT"))
        if ti not in allowed:
            raise WorkflowError(f"From {current} the next stage is {' or '.join(STAGES[i] for i in sorted(allowed))}.")
        if target == "FIXING" and not reason:
            raise WorkflowError("Say what needs fixing with --reason.")
        problems = forward_problems(repo, state, cfg, target)
        if problems:
            raise WorkflowError(f"Cannot move to {target}:\n{bullet_list(problems)}")
    add_history(state, "stage", agent, **{"from": current, "to": target, "reason": reason})
    state["stage"] = target
