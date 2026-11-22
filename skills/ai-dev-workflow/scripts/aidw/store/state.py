"""Task state, history, checkpoints and the ACTIVE pointer."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from aidw.constants import STAGES
from aidw.errors import WorkflowError
from aidw.infra.secrets import assert_no_secrets
from aidw.infra.text import clean_session, load_json, now_iso, save_json
from aidw.store.config import records_dir, task_dir


def state_path(repo: Path, slug: str) -> Path:
    return task_dir(repo, slug) / "state.json"


def load_state(repo: Path, slug: str) -> Dict[str, Any]:
    path = state_path(repo, slug)
    if not path.exists():
        raise WorkflowError(f"There is no task named '{slug}'. Run `workflow.py status` to list tasks.")
    try:
        state = load_json(path)
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"{path} is not valid JSON ({exc}). It is managed by workflow.py; restore it from git.") from exc
    problems = []
    for key, kind in (("id", str), ("stage", str), ("status", str), ("approvals", dict), ("history", list)):
        if not isinstance(state.get(key), kind):
            problems.append(f"'{key}' is missing or has the wrong type")
    if state.get("stage") not in STAGES:
        problems.append(f"unknown stage {state.get('stage')!r}")
    if state.get("status") not in ("active", "paused", "closed"):
        problems.append(f"unknown status {state.get('status')!r}")
    if problems:
        raise WorkflowError(f"{path} is inconsistent: {'; '.join(problems)}.")
    state.setdefault("baseline", {})
    state.setdefault("progress", {})
    state.setdefault("checks", [])
    state.setdefault("checkpoints", [])
    state.setdefault("decisions", [])
    state.setdefault("excluded", [])
    return state


def save_state(repo: Path, state: Dict[str, Any]) -> None:
    state["updated_at"] = now_iso()
    assert_no_secrets(json.dumps(state, ensure_ascii=False, indent=1), "state.json")
    save_json(state_path(repo, state["id"]), state)


def add_history(state: Dict[str, Any], event: str, agent: str, **details: Any) -> None:
    entry = {"at": now_iso(), "event": event, "agent": agent}
    entry.update({k: v for k, v in details.items() if v is not None})
    state["history"].append(entry)


def add_checkpoint(state: Dict[str, Any], kind: str, agent: str, fingerprint: str,
                   changes: Dict[str, str], valid: bool, **extra: Any) -> None:
    entry = {"at": now_iso(), "kind": kind, "agent": agent, "fingerprint": fingerprint,
             "valid": valid, "changed_files": len(changes)}
    entry.update({k: v for k, v in extra.items() if v is not None})
    state["checkpoints"].append(entry)
    del state["checkpoints"][:-60]
    state["last_checkpoint"] = {"at": entry["at"], "fingerprint": fingerprint, "changes": changes}


def list_tasks(repo: Path) -> List[str]:
    root = records_dir(repo) / "tasks"
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if (p / "state.json").exists())


def active_path(repo: Path) -> Path:
    return records_dir(repo) / "ACTIVE"


def read_active(repo: Path) -> Optional[Dict[str, Any]]:
    path = active_path(repo)
    if not path.exists():
        return None
    try:
        data = load_json(path)
        return data if isinstance(data, dict) and data.get("task") else None
    except (OSError, ValueError):
        return None


def clear_active(repo: Path, slug: Optional[str] = None) -> None:
    current = read_active(repo)
    if current and (slug is None or current.get("task") == slug):
        active_path(repo).unlink()


def activate(repo: Path, state: Dict[str, Any], agent: str, session: Optional[str]) -> Optional[str]:
    """Make this task the one the session works on; pause a different active task. Returns its slug if paused."""
    paused = None
    current = read_active(repo)
    if current and current.get("task") != state["id"]:
        try:
            other = load_state(repo, current["task"])
            if other["status"] == "active":
                other["status"] = "paused"
                add_history(other, "paused", agent, reason=f"task {state['id']} became active")
                save_state(repo, other)
                paused = other["id"]
        except WorkflowError:
            pass
    save_json(active_path(repo), {
        "task": state["id"], "agent": agent, "session": clean_session(session),
        "since": now_iso(), "preflight_session": None, "preflight_at": None,
    })
    return paused
