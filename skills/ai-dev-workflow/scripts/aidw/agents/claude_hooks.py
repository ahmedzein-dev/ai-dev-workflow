"""Claude Code hook entry points."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from aidw.api import session_problem, status_line
from aidw.constants import CODE_STAGES, NEXT, RECORDS, REFERENCE, STAGES
from aidw.core.gates import approval_status
from aidw.errors import WorkflowError
from aidw.infra.gitutil import is_records_path
from aidw.infra.text import clean_session, now_iso
from aidw.records.parsers import blocking_deps
from aidw.store.config import task_dir
from aidw.store.lock import locked_records
from aidw.store.state import load_state, read_active, save_active


def _find_records(start: Path) -> Optional[Path]:
    for folder in [start, *start.parents]:
        pointer = folder / RECORDS / "ACTIVE"
        if pointer.exists() or pointer.is_symlink():
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


def _session_rejected(raw: Any) -> bool:
    """The payload session id is untrusted input (TD-25): refuse it when it is not text, looks like a secret or breaks
    the session format. Missing ids and the placeholders `clean_session` drops are not rejected, as before."""
    if raw is None:
        return False
    return not isinstance(raw, str) or session_problem(raw) is not None


def _rejected_session_reason(repo: Path, active: Dict[str, Any]) -> Optional[str]:
    """Deny inside an active task, whatever the binding, so an invalid session can never bypass the gates; without an
    active task there is nothing to gate. The reason never contains the session id."""
    if not (task_dir(repo, active["task"]) / "state.json").exists():
        return "AIDevWorkflow cannot validate the active task; repair ACTIVE or its task state before editing."
    state = load_state(repo, active["task"])
    if state["status"] != "active":
        return None
    return (f"AIDevWorkflow: this session's id is not valid (it must be 1–256 printable characters without spaces and "
            f"must not look like a credential), so this edit cannot be checked against task '{state['id']}'. "
            f"Pause the task (`workflow.py pause {state['id']}`) for unrelated work.")


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
        rejected = _session_rejected(data.get("session_id"))
        session = None if rejected else clean_session(data.get("session_id"))
        flags: Dict[str, Any] = {"session_rejected": True} if rejected else {}
        target = Path(file_path)
        if not target.is_absolute():
            target = Path(data.get("cwd") or os.getcwd()) / target
        repo = _find_records(target.parent)
        if repo is None:
            _hook_log("claude-pre-edit", session=session, file=str(target), decision="allow", why="no active task", **flags)
            return 0
    except Exception:  # noqa: BLE001 - without a known repository the hook must never interfere
        return 0
    try:
        with locked_records(repo, active=True):
            active = read_active(repo)
            if not active:
                return 0
            with locked_records(repo, (active["task"],)):
                if rejected:
                    reason = _rejected_session_reason(repo, active)
                    _hook_log("claude-pre-edit", session=None, file=str(target), task=active["task"],
                              decision="deny" if reason else "allow", why=reason or "no active task", **flags)
                    return _deny(reason) if reason else 0
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
                    save_active(repo, active)
                reason = gate_decision(repo, active, target, session)
                _hook_log("claude-pre-edit", session=session, file=str(target), task=active["task"],
                          decision="deny" if reason else "allow", why=reason or "gates satisfied")
                return _deny(reason) if reason else 0
    except Exception as exc:  # noqa: BLE001 - a present but invalid ACTIVE/task fails closed
        reason = (f"AIDevWorkflow could not validate the active workflow ({type(exc).__name__}). "
                  "Inspect ACTIVE and the task records before editing.")
        _hook_log("claude-pre-edit", session=None if rejected else session, file=str(target),
                  decision="deny", why=reason, **flags)
        return _deny(reason)


def hook_claude_prompt(raw: str) -> int:
    try:
        data = json.loads(raw or "{}")
        if _session_rejected(data.get("session_id")):
            return 0  # an invalid session gets no reminder and nothing is written (TD-25)
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
