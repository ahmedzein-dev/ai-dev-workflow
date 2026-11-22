"""CLI helpers: loading a task from the command-line arguments and printing a task summary."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, Tuple
from aidw.infra.gitutil import find_repo
from aidw.store.config import load_config
from aidw.store.state import load_state


def require_task(args: argparse.Namespace) -> Tuple[Path, Dict[str, Any], Dict[str, Any]]:
    repo = find_repo(args.repo)
    cfg = load_config(repo)
    state = load_state(repo, args.task)
    return repo, cfg, state


def print_summary(info: Dict[str, Any]) -> None:
    print(f"AIDevWorkflow task '{info['task']}' ({info.get('type')}): {info.get('title')}")
    print(f"Status: {info['status_line']}  ·  stage {info['stage_number']}/11  ·  {info['status']}"
          + ("  ·  active in this checkout" if info.get("active_here") else ""))
    for doc_name, data in info.get("approvals", {}).items():
        marker = "valid" if data["valid"] else "not valid"
        print(f"{doc_name.capitalize()}: {marker} — {data['message']} (current file {data['current_sha256'] or 'missing'})")
    if info.get("progress"):
        print("Progress: " + ", ".join(f"{s} {st}" for s, st in info["progress"].items()))
    for warning in info.get("warnings", []):
        print(f"Warning: {warning}")
    print(f"Next: {info['next']}")
    print(f"Read: {info['read']}")
