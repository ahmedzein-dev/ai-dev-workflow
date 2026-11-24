"""Local task and ACTIVE locks. They serialize writers, not multi-file transactions."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import socket
import stat
import time
import uuid
from pathlib import Path
from typing import Dict, Iterator, Optional, Sequence, Tuple

from aidw.errors import WorkflowError
from aidw.infra.gitutil import git_ok, run_git
from aidw.store.config import records_dir

_HOST = socket.gethostname()
_WAIT_SECONDS = 3.0
_POLL_SECONDS = 0.05
_IGNORE_RULE = b"/.ai-dev-workflow/.locks/\n"


def _ensure_lock_ignored(repo: Path) -> None:
    """Keep lock metadata out of Git even in projects created by an older engine."""
    samples = (".ai-dev-workflow/.locks/active.lock",
               ".ai-dev-workflow/.locks/task-" + "0" * 64 + ".lock")
    if all(git_ok(repo, ["check-ignore", "-q", "--", sample]) for sample in samples):
        return
    exclude_rel = run_git(repo, ["rev-parse", "--git-path", "info/exclude"]).strip()
    exclude = Path(exclude_rel)
    if not exclude.is_absolute():
        exclude = repo / exclude
    exclude.parent.mkdir(parents=True, exist_ok=True)
    previous = exclude.read_bytes() if exclude.exists() else b""
    if _IGNORE_RULE not in previous.splitlines(keepends=True):
        with exclude.open("ab") as handle:
            if previous and not previous.endswith(b"\n"):
                handle.write(b"\n")
            handle.write(_IGNORE_RULE)
            handle.flush()
            os.fsync(handle.fileno())
    if not all(git_ok(repo, ["check-ignore", "-q", "--", sample]) for sample in samples):
        raise WorkflowError("Task locks cannot be excluded from Git; inspect this repository before writing records.")


def _lock_path(repo: Path, task: Optional[str]) -> Path:
    name = "active" if task is None else "task-" + hashlib.sha256(task.encode("utf-8")).hexdigest()
    return records_dir(repo) / ".locks" / (name + ".lock")


def _lock_bytes(path: Path) -> Optional[Tuple[os.stat_result, bytes]]:
    """Read only small regular lock files; never wait on a FIFO or follow a symlink."""
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            return None
        flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(str(path), flags)
        with os.fdopen(fd, "rb") as handle:
            info = os.fstat(handle.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > 4096:
                return None
            data = handle.read(4097)
            if len(data) > 4096:
                return None
            return info, data
    except OSError:
        return None


def _identity(path: Path) -> Optional[Tuple[int, int, int, int, bytes]]:
    result = _lock_bytes(path)
    if result is None:
        return None
    info, data = result
    return (info.st_dev, info.st_ino, info.st_mtime_ns, info.st_size, data)


def _owner(path: Path) -> Optional[Dict[str, object]]:
    result = _lock_bytes(path)
    if result is None:
        return None
    try:
        data = json.loads(result[1].decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _dead_same_host(owner: Optional[Dict[str, object]]) -> bool:
    if not owner or owner.get("host") != _HOST:
        return False
    pid = owner.get("pid")
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False
    if os.name == "nt":
        # On Windows os.kill(pid, 0) can terminate the process. Treat liveness as unknown.
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except (PermissionError, OSError):
        return False
    return False  # live or PID reused: never steal


def _create(path: Path, data: Dict[str, object]) -> bool:
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        # A partial lock is intentionally left for inspection; it must not be stolen as "stale".
        raise
    return True


def _release(path: Path, token: str) -> None:
    owner = _owner(path)
    if owner and owner.get("token") == token:
        path.unlink()


def _recover_stale(path: Path) -> bool:
    observed = _identity(path)
    owner = _owner(path)
    if observed is None or not _dead_same_host(owner):
        return False
    guard = path.with_name(path.name + ".recovery")
    guard_token = uuid.uuid4().hex
    guard_data: Dict[str, object] = {
        "token": guard_token, "pid": os.getpid(), "host": _HOST, "created": time.time(),
    }
    if not _create(guard, guard_data):
        return False
    try:
        # Cooperating writers check the guard before and after acquisition. Recheck both identity
        # and owner under it, so two concurrent recoverers cannot delete a newly acquired lock.
        if _identity(path) != observed or not _dead_same_host(_owner(path)):
            return False
        path.unlink()
        return True
    finally:
        _release(guard, guard_token)


@contextlib.contextmanager
def _acquire(path: Path, timeout: float, label: str) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    data: Dict[str, object] = {"token": token, "pid": os.getpid(), "host": _HOST, "created": time.time()}
    guard = path.with_name(path.name + ".recovery")
    deadline = time.monotonic() + timeout
    while True:
        if not guard.exists() and _create(path, data):
            if not guard.exists():
                break
            _release(path, token)
        elif path.exists():
            _recover_stale(path)
        if time.monotonic() >= deadline:
            owner = _owner(path)
            who = "same-host process" if owner and owner.get("host") == _HOST else "unknown owner"
            raise WorkflowError(
                f"Timed out waiting for the AIDevWorkflow {label} lock ({who}). "
                f"Inspect {path} and check for a live writer before removing it; "
                "an uncertain lock needs manual inspection."
            )
        time.sleep(_POLL_SECONDS)
    try:
        yield
    finally:
        _release(path, token)


@contextlib.contextmanager
def locked_records(repo: Path, tasks: Sequence[str] = (), *, active: bool = False,
                   timeout: float = _WAIT_SECONDS) -> Iterator[None]:
    """Acquire ACTIVE first, then distinct task locks in slug order; release in reverse."""
    _ensure_lock_ignored(repo)
    with contextlib.ExitStack() as stack:
        if active:
            stack.enter_context(_acquire(_lock_path(repo, None), timeout, "ACTIVE"))
        for task in sorted(set(tasks)):
            stack.enter_context(_acquire(_lock_path(repo, task), timeout, f"task '{task}'"))
        yield
