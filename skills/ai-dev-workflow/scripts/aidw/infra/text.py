"""Text, hashing, atomic file writes and small helpers."""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import stat
import uuid
from pathlib import Path
from typing import Any, Optional, Sequence

from aidw.errors import WorkflowError


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def norm(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read_text(path: Path) -> str:
    return norm(path.read_text(encoding="utf-8", errors="replace"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(norm(text).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_text(read_text(path))


def write_text(path: Path, text: str) -> None:
    write_bytes(path, text.encode("utf-8"))


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    original = os.fstat(fd)
    replaced = False
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(tmp), str(path))
        replaced = True
        if os.name != "nt":
            directory = os.open(str(path.parent), os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    except BaseException as exc:
        if not replaced:
            try:
                if os.path.samestat(tmp.lstat(), original):
                    tmp.unlink()
            except OSError:
                pass
            raise
        raise WorkflowError(
            f"{path} was replaced, but its directory sync failed; durability is indeterminate. "
            "Inspect the file before retrying."
        ) from exc


def cleanup_orphan_temps(path: Path) -> int:
    """Remove known, dead-writer temps only after the caller validated an existing target under its lock."""
    if os.name == "nt":
        # os.kill(pid, 0) can terminate a Windows process; leave ambiguous temps for inspection.
        return 0
    if not path.is_file():
        return 0
    pattern = re.compile(rf"\.{re.escape(path.name)}\.(\d+)(?:\.[0-9a-f]{{32}})?\.tmp\Z")
    removed = 0
    for candidate in path.parent.iterdir():
        match = pattern.fullmatch(candidate.name)
        if not match:
            continue
        try:
            info = candidate.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                continue
            if hasattr(os, "getuid") and info.st_uid != os.getuid():
                continue
            pid = int(match.group(1))
            if pid <= 0:
                continue
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                pass
            except (PermissionError, OSError):
                continue  # alive or not reliably known
            else:
                continue
            if os.path.samestat(candidate.lstat(), info):
                candidate.unlink()
                removed += 1
        except OSError:
            continue
    return removed


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def save_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def short(value: Optional[str], n: int = 8) -> str:
    return (value or "")[:n] or "-"


def bullet_list(items: Sequence[str]) -> str:
    return "\n".join(f"  - {item}" for item in items)


def make_readonly(path: Path) -> None:
    try:
        os.chmod(str(path), stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
    except OSError:
        pass


def clean_session(value: Optional[str]) -> Optional[str]:
    if not value or "${" in value or value.strip() in ("", "none", "null"):
        return None
    return value.strip()


def agent_name(args: argparse.Namespace) -> str:
    return (getattr(args, "agent", None) or os.environ.get("AI_DEV_WORKFLOW_AGENT") or "unknown-agent").strip()
