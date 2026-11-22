"""Git access, working-tree changes, code fingerprints and change sets."""
from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set
from aidw.constants import RECORDS, SKILL_NAME
from aidw.errors import WorkflowError
from aidw.infra.text import norm, now_iso


def git_proc(repo: Path, args: Sequence[str], input_text: Optional[str] = None) -> "subprocess.CompletedProcess[str]":
    try:
        return subprocess.run(
            ["git", *args], cwd=str(repo), input=input_text, capture_output=True,
            text=True, encoding="utf-8", errors="surrogateescape",
        )
    except FileNotFoundError as exc:
        raise WorkflowError("git is not installed or not on PATH; AIDevWorkflow needs it.", 3) from exc
    except NotADirectoryError as exc:
        raise WorkflowError(f"{repo} is not a directory.", 3) from exc


def run_git(repo: Path, args: Sequence[str], input_text: Optional[str] = None) -> str:
    proc = git_proc(repo, args, input_text)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        raise WorkflowError(f"git {' '.join(args)} failed: {detail}", 3)
    return proc.stdout


def git_ok(repo: Path, args: Sequence[str]) -> bool:
    return git_proc(repo, args).returncode == 0


def find_repo(start: Optional[str]) -> Path:
    base = Path(start).expanduser() if start else Path.cwd()
    base = base.resolve()
    if base.is_file():
        base = base.parent
    if not base.exists():
        raise WorkflowError(f"{base} does not exist.", 3)
    proc = git_proc(base, ["rev-parse", "--show-toplevel"])
    if proc.returncode != 0 or not proc.stdout.strip():
        raise WorkflowError(
            f"{base} is not inside a git repository. AIDevWorkflow uses git to track changes and evidence; "
            "run it from the project's repository.", 3)
    return Path(proc.stdout.strip()).resolve()


def is_records_path(path: str) -> bool:
    return path == RECORDS or path.startswith(RECORDS + "/")


SKILL_INSTALL_PREFIXES = (f".agents/skills/{SKILL_NAME}/", f".claude/skills/{SKILL_NAME}/")


def is_tooling_path(path: str) -> bool:
    """Task records and project-level copies of this skill: never counted as the task's code changes."""
    return is_records_path(path) or path.startswith(SKILL_INSTALL_PREFIXES)


def _blob_hash(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def hash_paths(repo: Path, paths: Sequence[str]) -> Dict[str, str]:
    """Content hash (git blob id) for each path, or 'deleted'."""
    result: Dict[str, str] = {}
    regular: List[str] = []
    for rel in paths:
        full = repo / rel
        if full.is_symlink():
            result[rel] = _blob_hash(os.readlink(str(full)).encode("utf-8", "surrogateescape"))
        elif full.is_file():
            regular.append(rel)
        elif not full.exists():
            result[rel] = "deleted"
    if regular:
        out = run_git(repo, ["hash-object", "--stdin-paths"], input_text="\n".join(regular) + "\n")
        for rel, digest in zip(regular, out.split()):
            result[rel] = digest
    return result


def worktree_changes(repo: Path) -> Dict[str, str]:
    """Files whose working-tree content differs from HEAD (including untracked), outside the records folder."""
    out = run_git(repo, ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=all"])
    parts = out.split("\0")
    paths: List[str] = []
    i = 0
    while i < len(parts):
        entry = parts[i]
        i += 1
        if len(entry) < 4:
            continue
        code, rel = entry[:2], entry[3:]
        if code[0] in "RC":
            i += 1  # the next field is the original path of the rename or copy
        if not is_tooling_path(rel):
            paths.append(rel)
    return hash_paths(repo, paths)


def code_fingerprint(repo: Path) -> str:
    """Identity of the current code (all non-ignored files outside the records folder); unchanged by commits."""
    blobs: Dict[str, str] = {}
    for record in run_git(repo, ["ls-files", "-s", "-z"]).split("\0"):
        if "\t" not in record:
            continue
        meta, rel = record.split("\t", 1)
        fields = meta.split()
        if len(fields) >= 3:
            blobs[rel] = fields[1] if fields[2] == "0" else "conflict"
    for rel, digest in worktree_changes(repo).items():
        if digest == "deleted":
            blobs.pop(rel, None)
        else:
            blobs[rel] = digest
    hasher = hashlib.sha256()
    for rel in sorted(blobs):
        if not is_tooling_path(rel):
            hasher.update(f"{rel}\t{blobs[rel]}\n".encode("utf-8", "surrogateescape"))
    return hasher.hexdigest()


def git_baseline(repo: Path) -> Dict[str, Any]:
    head = git_proc(repo, ["rev-parse", "--verify", "-q", "HEAD"]).stdout.strip() or None
    return {"head": head, "dirty": worktree_changes(repo), "captured_at": now_iso()}


def change_set(repo: Path, baseline: Dict[str, Any], excluded: Sequence[str] = ()) -> Dict[str, Any]:
    """Files changed since a baseline, separating the task's changes from changes that existed before it."""
    head = baseline.get("head")
    paths: Set[str] = set()
    notes: List[str] = []
    if head and git_ok(repo, ["cat-file", "-e", f"{head}^{{commit}}"]):
        paths.update(p for p in run_git(repo, ["diff", "--name-only", "-z", head, "--"]).split("\0") if p)
    elif head:
        notes.append("The baseline commit is no longer available; changes are measured against the current HEAD.")
    current = worktree_changes(repo)
    paths.update(current)
    paths = {p for p in paths if not is_tooling_path(p)}
    hashes = dict(current)
    hashes.update(hash_paths(repo, [p for p in paths if p not in hashes]))
    dirty0: Dict[str, str] = baseline.get("dirty") or {}
    task: Dict[str, str] = {}
    touched: List[str] = []
    for rel in sorted(paths):
        digest = hashes.get(rel, "deleted")
        if rel in dirty0:
            if dirty0[rel] == digest:
                continue
            touched.append(rel)
        task[rel] = digest
    excluded_set = set(excluded)
    return {
        "task": {p: h for p, h in task.items() if p not in excluded_set},
        "excluded": sorted(p for p in task if p in excluded_set),
        "preexisting_modified": [p for p in touched if p not in excluded_set],
        "preexisting_untouched": sorted(p for p in dirty0 if p not in task),
        "notes": notes,
    }


def file_at(repo: Path, commit: Optional[str], rel: str) -> Optional[str]:
    if not commit:
        return None
    proc = git_proc(repo, ["show", f"{commit}:{rel}"])
    return norm(proc.stdout) if proc.returncode == 0 else None
