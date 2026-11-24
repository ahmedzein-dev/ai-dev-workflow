"""Setup proposal, template recommendation and records commit modes."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from aidw.adapters.detect import _read, _tool_found, ci_commands, detect_checks, project_files
from aidw.constants import COMMIT_MODES, INSTRUCTION_CANDIDATES, RECORDS
from aidw.errors import WorkflowError
from aidw.infra.gitutil import is_records_path, run_git
from aidw.infra.text import load_json, read_text, write_text
from aidw.store.config import config_path, library_dir, load_config, load_rules, records_dir, template_path


DISCOVERY_ONLY_KEYS = ("evidence", "tool_found")


OSS_LICENSE_RE = re.compile(
    r"MIT License|Apache License|GNU (?:GENERAL|LESSER|AFFERO) PUBLIC|BSD [0-9]-Clause|Mozilla Public License|"
    r"The Unlicense|ISC License|Redistribution and use in source and binary forms", re.I)


# What each records.commit mode really does (see apply_commit_mode and apply_commit_mode_in_clone).
RECORD_OPTIONS = (
    {"mode": "all", "label": "Save everything in git",
     "what": "Nothing is excluded: config.json, PROJECT.md, the template and every task folder (spec, plan, approved "
             "versions, state.json with approvals, progress and check results, verification, audit and report) are "
             "included whenever you commit. Only the local pointer ACTIVE is never committed.",
     "after_clone": "Yes: a clone has the setup and the full history of every committed task.",
     "other_machine": "Yes: another developer or AI agent on another computer can resume a task after pulling.",
     "if_lost": "Nothing that was committed and pushed; uncommitted work is lost, as with any file.",
     "privacy": "Specs, plans, the wording of approvals and audit findings are visible to everyone with access to "
                "the repository, and stay in its history."},
    {"mode": "config-only", "label": "Save only the setup in git",
     "what": "config.json, PROJECT.md and the template are included when you commit. Task folders are excluded "
             "through the local file .git/info/exclude, so they stay on the computer where they were created.",
     "after_clone": "The setup, yes. Task records, no.",
     "other_machine": "No for existing tasks: the same setup works for new tasks, but these tasks cannot be resumed "
                      "elsewhere.",
     "if_lost": "All task records on that computer: specs, plans, approval history, progress, audit and reports.",
     "privacy": "Task details stay on your computer; only the setup is shared."},
    {"mode": "none", "label": "Save nothing in git",
     "what": "The whole .ai-dev-workflow folder is excluded through the local file .git/info/exclude; nothing from "
             "AIDevWorkflow is committed.",
     "after_clone": "No: a clone has no setup and no task records.",
     "other_machine": "No: every computer needs its own setup, and tasks cannot move between computers.",
     "if_lost": "The setup and all task records.",
     "privacy": "Nothing from AIDevWorkflow leaves your computer."},
)


RECORD_NOTES = (
    "AIDevWorkflow never commits by itself: 'saved in git' means the files are included when you commit.",
    "The exclusion is a local git setting of each clone; it is re-applied automatically when a task starts in a "
    "new clone.",
    "Excluding files later does not remove what was already committed; it stays in the history.",
)


def library_settings() -> Dict[str, Any]:
    path = library_dir() / "settings.json"
    try:
        return load_json(path) if path.is_file() else {}
    except ValueError:
        return {}


def default_template_info() -> Optional[Dict[str, Any]]:
    """The template the user registered as their default (install.py add-template --default), if any."""
    name = library_settings().get("default_template")
    if not name:
        return None
    entry = library_dir() / "templates" / name
    info: Dict[str, Any] = {"name": f"user:{name}", "available": (entry / "template.md").is_file(),
                            "has_rules": (entry / "rules.json").is_file()}
    if not info["available"]:
        info["problem"] = (f"Your default template '{name}' is registered, but its files are missing from your "
                           f"private library. Register it again with `install.py add-template {name} <file> --default`.")
    return info


def template_proposal(default: Optional[Dict[str, Any]], candidates: List[str],
                      library: List[Dict[str, Any]]) -> Dict[str, Any]:
    if default and default["available"]:
        rules = "with its rules file" if default["has_rules"] else "structure only, no rules file"
        return {"recommended": default["name"],
                "reason": f"Your registered default template ({rules}), kept in your private library outside "
                          "every repository."}
    note = default["problem"] if default else "No default template is registered in your private library."
    others = [c for c in candidates] + [t["name"] for t in library]
    return {"recommended": None,
            "reason": note + (" Ask the user to choose one of the templates found or to provide one."
                              if others else " No template was found; ask the user to provide one.")
                      + " Never pick an example template on their behalf."}


def recommend_commit(repo: Path) -> Dict[str, str]:
    licence = next((f for f in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING") if (repo / f).is_file()), None)
    if licence and OSS_LICENSE_RE.search(_read(repo, licence)):
        return {"mode": "config-only",
                "reason": f"{licence} looks like an open-source licence, so the repository is probably public. Keeping "
                          "task records local avoids publishing specs, plans and audit findings; the trade-off is that "
                          "tasks cannot be resumed on another computer."}
    if run_git(repo, ["remote"]).split():
        return {"mode": "all",
                "reason": "The repository has a remote and no open-source licence, so it is probably shared with a "
                          "team. Saving task records lets other developers, computers and AI agents resume tasks; the "
                          "trade-off is that everyone with access can read the specs, plans and audit findings."}
    return {"mode": "all",
            "reason": "The repository has no remote yet. Saving task records keeps their history next to the code and "
                      "ready to share; the trade-off is that once you push, everyone with access can read them."}


def existing_setup(repo: Path) -> Optional[Dict[str, Any]]:
    """The project's confirmed settings and anything missing or invalid in them."""
    if not config_path(repo).exists():
        return None
    try:
        cfg = load_config(repo)
    except WorkflowError as exc:
        return {"valid": False, "problems": [str(exc)], "notes": []}
    problems: List[str] = []
    notes: List[str] = []
    try:
        template_path(repo, cfg)
        load_rules(repo, cfg)
    except WorkflowError as exc:
        problems.append(str(exc))
    mode = (cfg.get("records") or {}).get("commit")
    if mode not in COMMIT_MODES:
        problems.append("How task records are saved in git is not set (records.commit).")
    elif not commit_mode_applied(repo, mode):
        notes.append(f"records.commit={mode} is not yet applied in this clone; it is applied when the next task starts.")
    checks = cfg.get("checks") or []
    if not checks:
        problems.append("No checks are configured.")
    for check in checks:
        if check.get("command") and not _tool_found(repo, check["command"]):
            notes.append(f"Check '{check['id']}': '{check['command'].split()[0]}' was not found on this computer.")
    return {"valid": not problems, "template": cfg.get("template_source"), "commit": mode,
            "standards": cfg.get("standards") or [], "checks": [c.get("id") for c in checks],
            "confirmed": bool(cfg.get("setup")), "problems": problems, "notes": notes}


def discover_project(repo: Path) -> Dict[str, Any]:
    files = project_files(repo)
    pattern = re.compile(r"(?i)(spec[^/]*template|template[^/]*spec)[^/]*\.md$")
    candidates = sorted(f for f in files if not is_records_path(f) and pattern.search(f))
    default = default_template_info()
    library = []
    lib_root = library_dir() / "templates"
    if lib_root.is_dir():
        for entry in sorted(lib_root.iterdir()):
            if (entry / "template.md").exists():
                library.append({"name": f"user:{entry.name}", "has_rules": (entry / "rules.json").exists(),
                                "default": bool(default and default["name"] == f"user:{entry.name}")})
    return {
        "repository": repo.name,
        "existing": existing_setup(repo),
        "instruction_files": [p for p in INSTRUCTION_CANDIDATES if (repo / p).exists()],
        "template_candidates": candidates,
        "user_templates": library,
        "default_template": default,
        "template": template_proposal(default, candidates, library),
        "suggested_checks": detect_checks(repo, files),
        "ci_commands": ci_commands(repo, files),
        "records": {"options": list(RECORD_OPTIONS), "notes": list(RECORD_NOTES), "recommended": recommend_commit(repo)},
    }


RECORDS_README = """# AIDevWorkflow records

This folder is managed by the `ai-dev-workflow` skill (AIDevWorkflow — Structured AI-Assisted
Development, From Requirements to Release).

- `config.json` — this project's setup: instruction files, specification template, checks.
- `templates/` — the specification template this project uses (and its rules file, if any).
- `tasks/<task>/` — one folder per task: spec, dependencies, plan, approved snapshots, state,
  verification, audit and final report.

To continue a task, invoke the skill explicitly (for example `/ai-dev-workflow <task>` in
Claude Code or Gemini CLI, `$ai-dev-workflow <task>` in Codex). Outside the skill these files are
just records; agents are not bound by them. `state.json` and `approved/` are written by
`workflow.py` only — do not edit them by hand.
"""


def apply_commit_mode(repo: Path, mode: str) -> Path:
    write_text(records_dir(repo) / ".gitignore",
               "# Local workflow files; never commit locks or migration backups\n"
               "ACTIVE\n*.local.json\n.locks/\ntasks/*/.migrate-backup/\n")
    exclude_rel = run_git(repo, ["rev-parse", "--git-path", "info/exclude"]).strip()
    exclude = Path(exclude_rel)
    if not exclude.is_absolute():
        exclude = repo / exclude
    text = read_text(exclude) if exclude.exists() else ""
    text = re.sub(r"\n?# >>> ai-dev-workflow.*?# <<< ai-dev-workflow\n?", "\n", text, flags=re.S).rstrip("\n")
    lines = {"config-only": [f"/{RECORDS}/tasks/"], "none": [f"/{RECORDS}/"]}.get(mode, [])
    if lines:
        text += f"\n# >>> ai-dev-workflow (records.commit={mode})\n" + "\n".join(lines) + "\n# <<< ai-dev-workflow\n"
    else:
        text += "\n"
    write_text(exclude, text.lstrip("\n") if text.strip() else "")
    return exclude


def commit_mode_applied(repo: Path, mode: str) -> bool:
    if mode == "all":
        return True
    exclude_rel = run_git(repo, ["rev-parse", "--git-path", "info/exclude"]).strip()
    exclude = Path(exclude_rel) if Path(exclude_rel).is_absolute() else repo / exclude_rel
    return exclude.exists() and f"records.commit={mode})" in read_text(exclude)


def apply_commit_mode_in_clone(repo: Path, cfg: Dict[str, Any]) -> Optional[str]:
    """Apply the project's records.commit choice in this clone (the exclude file is local to each clone).

    Returns the message for the user when something was applied, otherwise None; it prints nothing.
    """
    mode = (cfg.get("records") or {}).get("commit")
    if mode in ("config-only", "none") and not commit_mode_applied(repo, mode):
        apply_commit_mode(repo, mode)
        return f"Applied records.commit={mode} in this clone (local git exclude only)."
    return None
