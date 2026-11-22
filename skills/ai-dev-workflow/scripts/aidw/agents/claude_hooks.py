"""Claude Code hook entry points."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from aidw.api import status_line
from aidw.constants import CODE_STAGES, NEXT, RECORDS, REFERENCE, STAGES
from aidw.core.gates import approval_status
from aidw.errors import WorkflowError
from aidw.infra.gitutil import is_records_path
from aidw.infra.text import clean_session, now_iso, save_json
from aidw.records.parsers import blocking_deps
from aidw.store.config import task_dir
from aidw.store.state import active_path, load_state, read_active


def _find_records(start: Path) -> Optional[Path]:
    for folder in [start, *start.parents]:
        if (folder / RECORDS / "ACTIVE").is_file():
            return folder
    return None


def _hook_log(hook: str, **data: Any) -> None:
    """Append one line per hook decision when AI_DEV_WORKFLOW_HOOK_LOG names a file (for diagnosing installs)."""
    path = os.environ.get("AI_DEV_WORKFLOW_HOOK_LOG")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"at": now_iso(), "hook": hook, **data}) + "\n")
    except OSError:
        pass


def _deny(reason: str) -> int:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))
    return 0


def gate_decision(repo: Path, active: Dict[str, Any], target: Path, session: Optional[str]) -> Optional[str]:
    """Return a denial reason, or None to allow the edit."""
    state = load_state(repo, active["task"])
    if state["status"] != "active":
        return None
    try:
        rel = target.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return None
    slug = state["id"]
    stage_i = STAGES.index(state["stage"])
    prefix = f"{RECORDS}/tasks/{slug}/"
    if is_records_path(rel):
        if re.match(rf"^{re.escape(RECORDS)}/tasks/[^/]+/approved/", rel):
            return "Approved snapshots are immutable. To change the spec or plan, move the task back a stage and edit spec.md or plan.md."
        if rel.endswith("/state.json") or rel == f"{RECORDS}/ACTIVE":
            return "state.json and ACTIVE are written by workflow.py only; use its commands instead of editing them."
        if rel == prefix + "spec.md" and stage_i > STAGES.index("SPEC_APPROVAL"):
            return (f"The spec is approved. To change it, first move back: `workflow.py stage {slug} SPECIFICATION "
                    "--reason …`, then edit and get renewed approval.")
        if rel == prefix + "plan.md" and stage_i > STAGES.index("PLAN_APPROVAL"):
            return (f"The plan is approved and immutable. To change it, first move back: `workflow.py stage {slug} "
                    "PLANNING --reason …`, then edit and get renewed approval.")
        return None
    unrelated = (f" If this edit is unrelated to task '{slug}', pause the task first (`workflow.py pause {slug}`); "
                 "normal editing resumes immediately.")
    if state["stage"] not in CODE_STAGES:
        return f"AIDevWorkflow task '{slug}' is in {state['stage']}; code may change only in IMPLEMENTATION or FIXING after a passing preflight." + unrelated
    for doc_name in ("spec", "plan"):
        ok, message = approval_status(repo, state, doc_name)
        if not ok:
            return f"AIDevWorkflow task '{slug}': {message}" + unrelated
    for dep in blocking_deps(repo, state, ("spec", "plan", "implementation")):
        return f"AIDevWorkflow task '{slug}' is blocked by {dep['id']} ({dep['summary']})." + unrelated
    if active.get("preflight_session") != session or not active.get("preflight_at"):
        return f"Run `workflow.py preflight {slug} --agent claude-code --session <this session>` before editing code in this session." + unrelated
    return None


def hook_claude_pre_edit(raw: str) -> int:
    try:
        data = json.loads(raw or "{}")
        tool_input = data.get("tool_input") or {}
        file_path = tool_input.get("file_path") or tool_input.get("notebook_path") or tool_input.get("path")
        if not file_path:
            return 0
        session = clean_session(data.get("session_id"))
        target = Path(file_path)
        if not target.is_absolute():
            target = Path(data.get("cwd") or os.getcwd()) / target
        repo = _find_records(target.parent)
        if repo is None:
            _hook_log("claude-pre-edit", session=session, file=str(target), decision="allow", why="no active task")
            return 0
        active = read_active(repo)
        if not active:
            return 0
        bound = active.get("session")
        if bound and session and bound != session:
            _hook_log("claude-pre-edit", session=session, file=str(target), decision="allow", why="other session")
            return 0
        if not bound:
            if active.get("agent") not in (None, "claude-code", "unknown-agent"):
                _hook_log("claude-pre-edit", session=session, file=str(target), decision="allow", why="other agent")
                return 0
            active["session"] = session
            if active.get("preflight_at") and not active.get("preflight_session"):
                active["preflight_session"] = session
            save_json(active_path(repo), active)
        if not (task_dir(repo, active["task"]) / "state.json").exists():
            return 0
    except Exception:  # noqa: BLE001 - without an active task the hook must never interfere
        return 0
    try:
        reason = gate_decision(repo, active, target, session)
    except Exception as exc:  # noqa: BLE001 - inside an active task, fail closed
        reason = f"AIDevWorkflow could not validate task '{active.get('task')}' ({exc}). Fix the records or pause the task."
    _hook_log("claude-pre-edit", session=session, file=str(target), task=active.get("task"),
              decision="deny" if reason else "allow", why=reason or "gates satisfied")
    return _deny(reason) if reason else 0


def hook_claude_prompt(raw: str) -> int:
    try:
        data = json.loads(raw or "{}")
        session = clean_session(data.get("session_id"))
        repo = _find_records(Path(data.get("cwd") or os.getcwd()))
        if repo is None:
            return 0
        active = read_active(repo)
        if not active or (active.get("session") and session and active["session"] != session):
            return 0
        state = load_state(repo, active["task"])
        if state["status"] != "active":
            return 0
        print(f"[AIDevWorkflow] Active task '{state['id']}': {status_line(repo, state)}. Next: {NEXT[state['stage']]} "
              f"(Rules: re-read the skill's {REFERENCE[state['stage']]}. Pause with `workflow.py pause {state['id']}` "
              "for unrelated work.)")
    except Exception:  # noqa: BLE001 - status reminders must never interfere
        return 0
    return 0


def cmd_hook(args: argparse.Namespace) -> int:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    if args.name == "claude-pre-edit":
        return hook_claude_pre_edit(raw)
    if args.name == "claude-prompt":
        return hook_claude_prompt(raw)
    raise WorkflowError(f"Unknown hook '{args.name}'.")
