"""Project configuration, template rules and the private template library."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from aidw.constants import RECORDS, TEMPLATES_DIR
from aidw.errors import WorkflowError
from aidw.infra.text import load_json


def records_dir(repo: Path) -> Path:
    return repo / RECORDS


def task_dir(repo: Path, slug: str) -> Path:
    return records_dir(repo) / "tasks" / slug


def config_path(repo: Path) -> Path:
    return records_dir(repo) / "config.json"


def load_config(repo: Path) -> Dict[str, Any]:
    path = config_path(repo)
    if not path.exists():
        raise WorkflowError(
            "This project has no AIDevWorkflow setup yet (.ai-dev-workflow/config.json). Run `workflow.py init "
            "--discover`, agree the setup with the user, then run `workflow.py init`.")
    try:
        cfg = load_json(path)
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"{path} is not valid JSON: {exc}") from exc
    if cfg.get("schema") != 1:
        raise WorkflowError(f"{path} has an unsupported schema; expected 1.")
    return cfg


def library_dir() -> Path:
    env = os.environ.get("AI_DEV_WORKFLOW_HOME")
    return Path(env).expanduser() if env else Path.home() / ".ai-dev-workflow"


def load_rules(repo: Path, cfg: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    rel = cfg.get("spec_rules")
    if not rel:
        return {}, None
    path = repo / rel
    if not path.exists():
        raise WorkflowError(f"The configured template rules file {rel} is missing.")
    try:
        rules = load_json(path)
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"{rel} is not valid JSON: {exc}") from exc
    if rules.get("schema") != 1:
        raise WorkflowError(f"{rel} has an unsupported schema; expected 1.")
    return rules, rel


def template_path(repo: Path, cfg: Dict[str, Any]) -> Path:
    rel = cfg.get("spec_template")
    if not rel:
        raise WorkflowError("No specification template is configured. Ask the user which template to use; never invent one.")
    path = repo / rel
    if not path.exists():
        raise WorkflowError(
            f"The configured specification template {rel} is missing. Ask the user which template to use; never invent one.")
    return path


def record_template(name: str) -> Path:
    path = TEMPLATES_DIR / name
    if not path.exists():
        raise WorkflowError(f"The skill installation is incomplete: {path} is missing. Reinstall the skill.", 3)
    return path
