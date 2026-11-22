"""Text, hashing, atomic file writes and small helpers."""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any, Optional, Sequence


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
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(str(tmp), str(path))


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
