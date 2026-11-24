"""Explicit task-state migrations. No production converter is registered in F1.0.5."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
from contextlib import nullcontext
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from aidw.constants import SLUG_RE
from aidw.errors import WorkflowError
from aidw.infra.secrets import assert_no_secrets
from aidw.infra.text import write_bytes, write_text, save_json
from aidw.store.config import task_dir
from aidw.store.lock import locked_records
from aidw.store.state import state_path, validate_state_data

Converter = Callable[[Dict[str, Any]], Dict[str, Any]]
CONVERTERS: Dict[int, Tuple[int, Converter]] = {}
_BACKUP_ID = re.compile(r"[0-9a-f]{32}\Z")


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_state(path: Path, task: str, expected_schema: Optional[int] = None) -> Tuple[bytes, Dict[str, Any]]:
    try:
        raw = path.read_bytes()
        state = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise WorkflowError(f"{path} cannot be read for migration; restore or inspect it before retrying.") from exc
    if not isinstance(state, dict) or type(state.get("schema")) is not int:
        raise WorkflowError(f"{path} has no valid task schema; migration cannot guess its format.")
    schema = state["schema"]
    if expected_schema is not None and schema != expected_schema:
        raise WorkflowError(f"{path} has a different schema than the selected backup.")
    validate_state_data(state, task, path, expected_schema=schema)
    return raw, state


def _convert(state: Dict[str, Any], task: str, path: Path, target_schema: int,
             converter: Converter) -> bytes:
    proposed = converter(copy.deepcopy(state))
    validate_state_data(proposed, task, path, expected_schema=target_schema)
    for key, value in state.items():
        if key != "schema" and proposed.get(key) != value:
            raise WorkflowError(f"Migration would change existing '{key}' evidence; refused.")
    text = json.dumps(proposed, indent=2, ensure_ascii=False) + "\n"
    assert_no_secrets(text, "migration result")
    return text.encode("utf-8")


def migrate_task(repo: Path, task: str, *, apply: bool = False,
                 rollback: Optional[str] = None) -> Dict[str, Any]:
    """Preview or apply a registered conversion; rollback a chosen verified backup."""
    if apply and rollback:
        raise WorkflowError("Choose either --apply or --rollback, not both.")
    if not SLUG_RE.fullmatch(task) or len(task) > 60:
        raise WorkflowError("Invalid task ID for migration.")
    path = state_path(repo, task)
    backup_root = task_dir(repo, task) / ".migrate-backup"
    if backup_root.is_symlink():
        raise WorkflowError("Migration backup folder is a symlink; inspect it before proceeding.")
    with locked_records(repo, (task,)) if (apply or rollback) else nullcontext():
        if rollback:
            if not _BACKUP_ID.fullmatch(rollback):
                raise WorkflowError("The backup ID must be the ID printed by a completed migration.")
            folder = backup_root / rollback
            if folder.is_symlink():
                raise WorkflowError("The selected migration backup is a symlink; inspect it.")
            try:
                if (folder / "manifest.json").is_symlink() or (folder / "state.json").is_symlink():
                    raise WorkflowError("The selected migration backup contains a symlink; inspect it.")
                meta = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
                backup = (folder / "state.json").read_bytes()
            except (OSError, ValueError) as exc:
                raise WorkflowError("The selected migration backup is incomplete or unreadable.") from exc
            if (not isinstance(meta, dict)
                    or type(meta.get("source_schema")) is not int
                    or type(meta.get("target_schema")) is not int
                    or meta["target_schema"] <= meta["source_schema"]
                    or not isinstance(meta.get("source_sha256"), str)
                    or not isinstance(meta.get("result_sha256"), str)
                    or not re.fullmatch(r"[0-9a-f]{64}", meta["source_sha256"])
                    or not re.fullmatch(r"[0-9a-f]{64}", meta["result_sha256"])
                    or _digest(backup) != meta["source_sha256"]):
                raise WorkflowError("The selected migration backup failed its integrity check.")
            current, _ = _read_state(path, task, meta.get("target_schema"))
            if _digest(current) != meta.get("result_sha256"):
                raise WorkflowError("Task state changed after migration; rollback would erase newer evidence. "
                                    "Keep the backup and reconcile the records manually.")
            _read_state(folder / "state.json", task, meta.get("source_schema"))
            assert_no_secrets(backup.decode("utf-8"), "migration backup")
            write_bytes(path, backup)
            return {"action": "rollback", "task": task, "backup": str(folder.relative_to(repo)),
                    "schema": meta["source_schema"], "changed": True}
        raw, state = _read_state(path, task)
        schema = state["schema"]
        registered = CONVERTERS.get(schema)
        backup_location = str(backup_root.relative_to(repo))
        if not registered:
            if apply:
                raise WorkflowError("No production migration is registered for this task schema; nothing was changed.")
            return {"action": "preview", "task": task, "source_schema": schema, "target_schema": None,
                    "affected_file": str(path.relative_to(repo)), "backup_location": backup_location,
                    "available": False, "changed": False,
                    "validation": {"source": "passed", "proposed": "not applicable"},
                    "message": f"No migration is registered for schema {schema}; the record stays unchanged."}
        target_schema, converter = registered
        if target_schema <= schema:
            raise WorkflowError("The registered migration target must be newer than its source.")
        assert_no_secrets(raw.decode("utf-8"), "migration source")
        result = _convert(state, task, path, target_schema, converter)
        if not apply:
            return {"action": "preview", "task": task, "source_schema": schema,
                    "target_schema": target_schema, "affected_file": str(path.relative_to(repo)),
                    "backup_location": backup_location, "available": True, "changed": False,
                    "validation": {"source": "passed", "proposed": "passed"},
                    "message": "A registered migration is available; --apply requires explicit confirmation."}
        backup_root.mkdir(mode=0o700, exist_ok=True)
        local_ignore = backup_root / ".gitignore"
        if local_ignore.exists():
            if local_ignore.read_text(encoding="utf-8") != "*\n":
                raise WorkflowError("Migration backup ignore rule differs from the expected local rule; inspect it.")
        else:
            write_text(local_ignore, "*\n")
        backup_id = uuid.uuid4().hex
        folder = backup_root / backup_id
        folder.mkdir(mode=0o700)
        backup_path = folder / "state.json"
        write_bytes(backup_path, raw)
        if _digest(backup_path.read_bytes()) != _digest(raw):
            raise WorkflowError("Migration backup failed its integrity check; task state was not changed.")
        save_json(folder / "manifest.json", {
            "source_schema": schema, "target_schema": target_schema,
            "source_sha256": _digest(raw), "result_sha256": _digest(result),
        })
        write_bytes(path, result)
        return {"action": "apply", "task": task, "source_schema": schema, "target_schema": target_schema,
                "affected_file": str(path.relative_to(repo)), "backup": str(folder.relative_to(repo)),
                "backup_id": backup_id, "changed": True}
