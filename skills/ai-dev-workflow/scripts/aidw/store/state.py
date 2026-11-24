"""Task state, history, checkpoints and the ACTIVE pointer."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from aidw.constants import SLUG_RE, STAGES
from aidw.errors import WorkflowError
from aidw.infra.secrets import assert_no_secrets
from aidw.infra.text import clean_session, cleanup_orphan_temps, load_json, now_iso, save_json
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
    validate_state_data(state, slug, path)
    state.setdefault("baseline", {})
    state.setdefault("progress", {})
    state.setdefault("checks", [])
    state.setdefault("checkpoints", [])
    state.setdefault("decisions", [])
    state.setdefault("excluded", [])
    return state


def validate_state_data(state: Any, slug: str, path: Path, *, expected_schema: int = 1) -> None:
    """Validate one known task schema without changing its data or accepting an unknown version."""
    if not isinstance(state, dict):
        raise WorkflowError(f"{path} is inconsistent: the root must be an object.")
    schema = state.get("schema")
    if type(schema) is not int or schema != expected_schema:
        raise WorkflowError(f"{path} has an unsupported task schema; expected {expected_schema}. Preview a supported migration.")
    problems = []
    for key, kind in (("id", str), ("stage", str), ("status", str), ("approvals", dict), ("history", list)):
        if not isinstance(state.get(key), kind):
            problems.append(f"'{key}' is missing or has the wrong type")
    if not SLUG_RE.fullmatch(slug) or len(slug) > 60:
        problems.append("task directory name is invalid")
    if isinstance(state.get("id"), str) and state["id"] != slug:
        problems.append("'id' does not match the task directory")
    for key, kind in (("baseline", dict), ("progress", dict), ("checks", list),
                      ("checkpoints", list), ("decisions", list), ("excluded", list),
                      ("discovery", dict), ("spec_review", dict)):
        if key in state and not isinstance(state[key], kind):
            problems.append(f"'{key}' has the wrong type")
    for key in ("approvals",):
        if isinstance(state.get(key), dict) and not all(isinstance(v, dict) for v in state[key].values()):
            problems.append(f"'{key}' contains a non-object entry")
    for key in ("history", "checks", "checkpoints", "decisions"):
        if isinstance(state.get(key), list) and not all(isinstance(v, dict) for v in state[key]):
            problems.append(f"'{key}' contains a non-object entry")
    if state.get("stage") not in STAGES:
        problems.append("unknown stage")
    if state.get("status") not in ("active", "paused", "closed"):
        problems.append("unknown status")
    if problems:
        raise WorkflowError(f"{path} is inconsistent: {'; '.join(problems)}.")


def save_state(repo: Path, state: Dict[str, Any]) -> None:
    state["updated_at"] = now_iso()
    assert_no_secrets(json.dumps(state, ensure_ascii=False, indent=1), "state.json")
    path = state_path(repo, state["id"])
    if path.exists():
        load_state(repo, state["id"])  # validate the existing recovery target before cleanup
        cleanup_orphan_temps(path)
    save_json(path, state)


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
    if path.is_symlink():
        raise WorkflowError(f"{path} is an invalid ACTIVE pointer: symlinks require inspection.")
    if not path.exists():
        return None
    if not path.is_file():
        raise WorkflowError(f"{path} is an invalid ACTIVE pointer: expected a regular file.")
    try:
        data = load_json(path)
    except (OSError, ValueError) as exc:
        raise WorkflowError(f"{path} cannot be read as a valid ACTIVE pointer; inspect or restore it.") from exc
    if (not isinstance(data, dict) or not isinstance(data.get("task"), str)
            or not SLUG_RE.fullmatch(data["task"]) or len(data["task"]) > 60):
        raise WorkflowError(f"{path} is an invalid ACTIVE pointer; inspect or restore it.")
    for key in ("agent", "session", "since", "preflight_session", "preflight_at"):
        if key in data and data[key] is not None and not isinstance(data[key], str):
            raise WorkflowError(f"{path} is an invalid ACTIVE pointer: '{key}' has the wrong type.")
    return data


def save_active(repo: Path, data: Dict[str, Any]) -> None:
    path = active_path(repo)
    if path.exists() or path.is_symlink():
        read_active(repo)  # preserve a corrupt pointer for inspection instead of overwriting it
        cleanup_orphan_temps(path)
    save_json(path, data)


def clear_active(repo: Path, slug: Optional[str] = None) -> None:
    current = read_active(repo)
    if current and (slug is None or current.get("task") == slug):
        active_path(repo).unlink()


def activate(repo: Path, state: Dict[str, Any], agent: str, session: Optional[str]) -> Optional[str]:
    """Make this task the one the session works on; pause a different active task. Returns its slug if paused."""
    paused = None
    current = read_active(repo)
    if current and current.get("task") != state["id"]:
        other = load_state(repo, current["task"])
        if other["status"] == "active":
            other["status"] = "paused"
            add_history(other, "paused", agent, reason=f"task {state['id']} became active")
            save_state(repo, other)
            paused = other["id"]
    save_active(repo, {
        "task": state["id"], "agent": agent, "session": clean_session(session),
        "since": now_iso(), "preflight_session": None, "preflight_at": None,
    })
    return paused
