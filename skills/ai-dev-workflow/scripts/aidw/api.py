"""The engine API: every command as a function that writes the records and returns data.

Internal and unversioned: the CLI, the Claude Code hooks and later front ends (dashboard, orchestrator) call these
functions; nothing outside this repository should rely on them yet. Rules for every function here:

- keyword parameters only, with the repository and the agent name passed explicitly (no working-directory default,
  no `AI_DEV_WORKFLOW_AGENT` lookup, no `argparse.Namespace`); pass absolute paths: a relative path (repository,
  template, config, notes) is resolved against the process's working directory, as `pathlib` does;
- the result is a JSON-serialisable dict whose keys are named in the docstring;
- a refusal raises `WorkflowError` at the same point as before F1.0.4, which is before any write except where a
  function's docstring says otherwise (`new_task`, `update_setup`, `run_check`);
- nothing is printed, `sys.argv` is never read and the process never exits.

The only environment input is `AI_DEV_WORKFLOW_HOME` (the user's template library, through `store.config`), as before.
"""
from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
from aidw.constants import CODE_STAGES, DEP_GATES, INVOCATION_RE, NEXT, RECORDS, RECORD_FILES, REFERENCE, SLUG_RE, STAGES, TASK_TYPES
from aidw.core.checks import analyzer_key, builtin_check, execute, last_line, parse_analyzer, regenerate_check_block
from aidw.core.gates import approval_status, check_freshness, plan_steps, transition
from aidw.core.outcome import compute_outcome
from aidw.core.setup import DISCOVERY_ONLY_KEYS, RECORDS_README, apply_commit_mode, apply_commit_mode_in_clone, discover_project
from aidw.core.spec import judgment_flags, spec_rules_and_template, verification_items
from aidw.core.spec import plan_check as _plan_check
from aidw.core.spec import spec_check as _spec_check
from aidw.errors import WorkflowError
from aidw.infra.gitutil import change_set, code_fingerprint, find_repo, git_baseline
from aidw.infra.secrets import assert_no_secrets, find_secrets, redact
from aidw.infra.text import bullet_list, clean_session, load_json, make_readonly, now_iso, read_text, save_json, sha256_file, short, write_text
from aidw.records.markdown import Doc
from aidw.records.parsers import blocking_deps, parse_audit, parse_dependencies, parse_matrix, parse_report
from aidw.store.config import config_path, library_dir, load_config, load_rules, record_template, records_dir, task_dir, template_path
from aidw.store.state import activate, active_path, add_checkpoint, add_history, clear_active, list_tasks, load_state, read_active, save_state

PathLike = Union[str, Path]


# ---------------------------------------------------------------------------------------------- shared builders

def status_line(repo: Path, state: Dict[str, Any]) -> str:
    """One-line status of a task: CLOSED/BLOCKED/PAUSED with the reason, or the stage name."""
    deps = blocking_deps(repo, state, DEP_GATES) if (task_dir(repo, state["id"]) / "dependencies.md").exists() else []
    gate_index = {"spec": STAGES.index("SPEC_APPROVAL"), "plan": STAGES.index("PLAN_APPROVAL"),
                  "implementation": STAGES.index("IMPLEMENTATION"), "completion": STAGES.index("FINAL_REPORT")}
    stage_i = STAGES.index(state["stage"])
    blocking_now = [d for d in deps if gate_index.get(d["gate"] or "", 99) <= stage_i + 1]
    if state["status"] == "closed":
        return f"CLOSED — {state.get('outcome')}"
    if blocking_now:
        first = blocking_now[0]
        return f"BLOCKED — Awaiting {first['summary'] or first['id']} ({first['owner'] or 'owner not set'})"
    if state["status"] == "paused":
        return f"PAUSED — {state['stage']}"
    return state["stage"]


def task_summary(repo: Path, cfg: Dict[str, Any], state: Dict[str, Any], detailed: bool) -> Dict[str, Any]:
    """Task summary. Returns `task`, `title`, `type`, `stage`, `stage_number`, `status`, `outcome`, `status_line`,
    `updated_at`; when detailed also `approvals`, `progress`, `active_here`, `warnings`, `next`, `read`."""
    slug = state["id"]
    summary: Dict[str, Any] = {
        "task": slug, "title": state.get("title"), "type": state.get("type"), "stage": state["stage"],
        "stage_number": STAGES.index(state["stage"]) + 1, "status": state["status"], "outcome": state.get("outcome"),
        "status_line": status_line(repo, state), "updated_at": state.get("updated_at"),
    }
    if not detailed:
        return summary
    approvals = {}
    for doc_name in ("spec", "plan"):
        record = state["approvals"].get(doc_name)
        ok, message = approval_status(repo, state, doc_name)
        current = task_dir(repo, slug) / f"{doc_name}.md"
        approvals[doc_name] = {"valid": ok, "message": message,
                               "approved_version": record["version"] if record else None,
                               "current_sha256": short(sha256_file(current)) if current.exists() else None}
    summary["approvals"] = approvals
    steps = plan_steps(repo, state)
    summary["progress"] = {s: state["progress"].get(s, {}).get("status", "todo") for s in steps}
    warnings: List[str] = []
    stage_i = STAGES.index(state["stage"])
    if stage_i < STAGES.index("IMPLEMENTATION") and state["baseline"].get("start"):
        pre = change_set(repo, state["baseline"]["start"], state.get("excluded", []))["task"]
        if pre:
            warnings.append("Files changed since the task started, before any implementation was approved: " +
                            ", ".join(sorted(pre)[:10]) + (" …" if len(pre) > 10 else "") +
                            ". If you made them, revert them; otherwise ask the user and exclude them with `scope --exclude`.")
    if stage_i >= STAGES.index("TESTING"):
        fingerprint = code_fingerprint(repo)
        for check, result, freshness in check_freshness(repo, state, cfg, fingerprint):
            if freshness != "fresh":
                warnings.append(f"Required check '{check['id']}' is {freshness}.")
    active = read_active(repo)
    summary["active_here"] = bool(active and active.get("task") == slug)
    summary["warnings"] = warnings
    summary["next"] = NEXT[state["stage"]] if state["status"] != "closed" else "The task is closed."
    if state["status"] == "paused":
        summary["next"] = f"Resume first: `workflow.py resume {slug} --agent <you>`. Then: {summary['next']}"
    summary["read"] = REFERENCE[state["stage"]]
    return summary


# ------------------------------------------------------------------------------------------------ setup helpers

def resolve_template(*, template: str, rules: Optional[str] = None,
                     no_rules: bool = False) -> Tuple[Path, Optional[Path], str, str]:
    """Locate a spec template (`user:<name>` or a path) and its rules file: (template, rules or None, name, label)."""
    if template.startswith("user:"):
        name = template[5:]
        source_dir = library_dir() / "templates" / name
        template_src = source_dir / "template.md"
        rules_src: Optional[Path] = source_dir / "rules.json"
        source_label = f"user:{name}"
    else:
        template_src = Path(template).expanduser()
        name = template_src.stem
        rules_src = Path(rules).expanduser() if rules else template_src.with_name(template_src.stem + ".rules.json")
        source_label = f"file:{template_src.name}"
    if not template_src.is_file():
        raise WorkflowError(f"Template not found: {template}. Ask the user for the right template.")
    if no_rules or not (rules_src and rules_src.is_file()):
        if rules and not no_rules:
            raise WorkflowError(f"Rules file not found: {rules}")
        rules_src = None
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-") or "spec-template"
    return template_src, rules_src, name, source_label


def install_template(repo: Path, cfg: Dict[str, Any], template_src: Path, rules_src: Optional[Path], name: str,
                     source_label: str) -> None:
    """Copy a template (and its rules) into the project records and point `cfg` at it (cfg is changed in place)."""
    rules = None
    if rules_src:
        rules = load_json(rules_src)
        if rules.get("schema") != 1:
            raise WorkflowError(f"{rules_src.name} has an unsupported schema; expected 1.")
    templates = records_dir(repo) / "templates"
    write_text(templates / f"{name}.md", read_text(template_src))
    if rules_src:
        write_text(templates / f"{name}.rules.json", read_text(rules_src))
    cfg["spec_template"] = f"{RECORDS}/templates/{name}.md"
    cfg["spec_rules"] = f"{RECORDS}/templates/{name}.rules.json" if rules_src else None
    cfg["template_source"] = source_label


def change_checks(checks: List[Dict[str, Any]], without: Sequence[str], add: Sequence[str]) -> List[Dict[str, Any]]:
    """The check list with `without` ids removed and `add` (`<id>=<command>`) added; the input is not changed."""
    result = [dict(c) for c in checks]
    for cid in without or []:
        if not any(c.get("id") == cid for c in result):
            raise WorkflowError(f"There is no check '{cid}' to remove. Checks: {', '.join(c['id'] for c in result)}.")
        result = [c for c in result if c.get("id") != cid]
    for spec in add or []:
        cid, sep, command = spec.partition("=")
        cid, command = cid.strip(), command.strip()
        if not sep or not SLUG_RE.match(cid) or not command:
            raise WorkflowError(f"--add-check needs <id>=<command>, for example unit='python3 -m unittest'; got {spec!r}.")
        assert_no_secrets(command, "the check command")
        result = [c for c in result if c.get("id") != cid]
        result.append({"id": cid, "name": cid, "command": command, "required": True, "explain": "Added by the user."})
    return result


def open_tasks(repo: Path) -> List[str]:
    """Ids of the tasks that are not closed."""
    return [slug for slug in list_tasks(repo) if load_state(repo, slug).get("status") != "closed"]


# ---------------------------------------------------------------------------------------------- record checks

def scan_records(repo: Path, slug: str) -> List[str]:
    """Problems for task records (and approved snapshots) that look like they contain a secret."""
    tdir = task_dir(repo, slug)
    problems = []
    paths = [tdir / name for name in RECORD_FILES]
    approved = tdir / "approved"
    if approved.is_dir():
        paths += sorted(approved.glob("*.md"))
    for path in paths:
        if path.exists():
            for kind, line in find_secrets(read_text(path)):
                problems.append(f"{path.relative_to(tdir)}:{line} looks like it contains a {kind}.")
    return problems


def validate_task(repo: Path, cfg: Dict[str, Any], state: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Consistency of one task's records for its stage: (errors, warnings)."""
    errors: List[str] = []
    warnings: List[str] = []
    slug = state["id"]
    tdir = task_dir(repo, slug)
    for name in RECORD_FILES:
        if not (tdir / name).exists():
            errors.append(f"{name} is missing.")
    if errors:
        return errors, warnings
    errors += scan_records(repo, slug)
    stage_i = STAGES.index(state["stage"])
    if stage_i > STAGES.index("DEPENDENCIES"):
        errors += [f"dependencies.md: {p}" for p in parse_dependencies(repo, slug)["problems"]]
    if stage_i >= STAGES.index("SPEC_APPROVAL"):
        result = _spec_check(repo, state, cfg)
        if stage_i == STAGES.index("SPEC_APPROVAL"):
            errors += [f"spec.md: {p['message']}" for p in result["mandatory"]]
        if result["template_changed"]:
            warnings.append("The project template changed after this task was created.")
    if stage_i > STAGES.index("SPEC_APPROVAL"):
        ok, message = approval_status(repo, state, "spec")
        if not ok:
            errors.append(message + " Move back to SPECIFICATION and get renewed approval.")
    if stage_i > STAGES.index("PLAN_APPROVAL"):
        ok, message = approval_status(repo, state, "plan")
        if not ok:
            errors.append(message + " Move back to PLANNING and get renewed approval.")
    if stage_i < STAGES.index("IMPLEMENTATION") and state["baseline"].get("start"):
        pre = change_set(repo, state["baseline"]["start"], state.get("excluded", []))["task"]
        if pre:
            warnings.append("Files changed before implementation was approved: " + ", ".join(sorted(pre)[:10]))
    if stage_i >= STAGES.index("AUDIT"):
        rows, problems = parse_matrix(repo, slug)
        errors += [f"verification.md: {p}" for p in problems]
        for check, _, freshness in check_freshness(repo, state, cfg):
            if freshness != "fresh":
                warnings.append(f"Required check '{check['id']}' is {freshness}.")
    if stage_i >= STAGES.index("FINAL_REPORT") and state["status"] != "closed":
        audit = parse_audit(repo, slug)
        if stage_i == STAGES.index("FINAL_REPORT") and state["history"] and \
                state["history"][-1].get("from") == "AUDIT":
            errors += [f"audit.md: {p}" for p in audit["problems"]]
    if state["status"] == "closed":
        report = parse_report(repo, slug)
        errors += [f"report.md: {p}" for p in report["problems"]]
    return errors, warnings


# ------------------------------------------------------------------------------------------- loading a task

def _root(repo: PathLike) -> Path:
    """The repository root for an explicit path; the API never falls back to the current directory.

    An empty path or a path of spaces is refused: `pathlib` would turn either into the current directory (on Windows
    also a path of spaces). The CLI resolves those values itself, exactly as before F1.0.4.
    """
    if not str(repo).strip():
        raise WorkflowError("The engine API needs an explicit repository path.")
    return find_repo(str(repo))


def _task(repo: PathLike, task: str) -> Tuple[Path, Dict[str, Any], Dict[str, Any]]:
    """Repository root, project config and task state, loaded in the same order as the CLI always did."""
    root = _root(repo)
    cfg = load_config(root)
    state = load_state(root, task)
    return root, cfg, state


# ------------------------------------------------------------------------------------------ setup and tasks

def apply_clone_commit_mode(*, repo: PathLike, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Apply the project's records commit mode in this clone if it is not applied yet. Returns `message` (the notice
    for the user, or None when nothing was applied). Used by the `ensure_commit_mode` compatibility wrapper.

    `repo` must be the repository root, as for the old `ensure_commit_mode`: it is used as given, not resolved.
    """
    if not str(repo).strip():
        raise WorkflowError("The engine API needs an explicit repository path.")
    return {"message": apply_commit_mode_in_clone(Path(repo), cfg)}


def discover_setup(*, repo: PathLike) -> Dict[str, Any]:
    """Setup proposal for a repository (nothing is written). Returns the discovery report: `repository`, `existing`,
    `instruction_files`, `template`, `template_candidates`, `user_templates`, `suggested_checks`, `ci_commands`,
    `records`."""
    return discover_project(_root(repo))


def init_project(*, repo: PathLike, template: Optional[str], commit: Optional[str], agent: str,
                 rules: Optional[str] = None, no_rules: bool = False, standards: Optional[str] = None,
                 config: Optional[str] = None, project: Optional[str] = None, project_notes: Optional[str] = None,
                 without_check: Sequence[str] = (), add_check: Sequence[str] = ()) -> Dict[str, Any]:
    """Set up AIDevWorkflow in a repository. Returns `source_label`, `has_rules`, `commit`, `checks` (ids) and
    `exclude` (the git exclude file written for `config-only`/`none`)."""
    root = _root(repo)
    cfg_file = config_path(root)
    if cfg_file.exists():
        raise WorkflowError("AIDevWorkflow is already set up here; reuse its settings. To change them, use --update "
                            "with --commit, --standards, --template, --add-check or --without-check.")
    if not commit:
        raise WorkflowError("Choose how task records are saved in git with --commit all, config-only or none. Explain "
                            "the options (`init --discover`) and ask the user.")
    if not template:
        raise WorkflowError("Choose the specification template with --template <path> or --template user:<name>. "
                            "Ask the user; never invent one. `init --discover` lists the recommendation and candidates.")
    base: Dict[str, Any] = {}
    if config:
        try:
            base = load_json(Path(config).expanduser())
        except (OSError, ValueError) as exc:
            raise WorkflowError(f"Could not read --config {config}: {exc}") from exc
    template_src, rules_src, name, source_label = resolve_template(template=template, rules=rules, no_rules=no_rules)
    proposal = discover_project(root)
    recommended_checks = [{k: v for k, v in c.items() if k not in DISCOVERY_ONLY_KEYS}
                          for c in proposal["suggested_checks"]]
    checks = change_checks(base["checks"] if "checks" in base else recommended_checks, without_check, add_check)
    chosen_standards = [s.strip() for s in (standards or "").split(",") if s.strip()] or base.get("standards") or \
        [p for p in ("CLAUDE.md", "AGENTS.md", "GEMINI.md") if (root / p).exists()]
    cfg: Dict[str, Any] = {
        "schema": 1,
        "project": project or base.get("project") or root.name,
        "standards": chosen_standards,
        "records": {"commit": commit},
        "checks": checks,
        "rules": base.get("rules", []),
        "setup": {
            "confirmed_at": now_iso(), "recorded_by": agent,
            "recommended": {"template": proposal["template"]["recommended"],
                            "commit": proposal["records"]["recommended"]["mode"],
                            "checks": [c["id"] for c in recommended_checks]},
            "chosen": {"template": source_label, "commit": commit, "checks": [c["id"] for c in checks]},
        },
    }
    install_template(root, cfg, template_src, rules_src, name, source_label)
    cfg = {k: cfg[k] for k in ("schema", "project", "standards", "spec_template", "spec_rules", "template_source",
                               "records", "checks", "rules", "setup")}
    assert_no_secrets(json.dumps(cfg), "config.json")
    save_json(cfg_file, cfg)
    write_text(records_dir(root) / "README.md", RECORDS_README)
    if project_notes:
        notes = read_text(Path(project_notes).expanduser())
    else:
        notes = ("# Project notes for AIDevWorkflow\n\nEngineering standards: "
                 + (", ".join(chosen_standards) or "none listed")
                 + "\n\n## Standards conflicts and decisions\n\nNone recorded yet.\n\n## Audit checklist\n\n"
                 "List the sections of the standards files the audit must check.\n")
    assert_no_secrets(notes, "PROJECT.md")
    write_text(records_dir(root) / "PROJECT.md", notes)
    exclude = apply_commit_mode(root, commit)
    return {"source_label": source_label, "has_rules": bool(rules_src), "commit": commit,
            "checks": [c["id"] for c in checks], "exclude": str(exclude)}


def update_setup(*, repo: PathLike, agent: str, commit: Optional[str] = None, standards: Optional[str] = None,
                 template: Optional[str] = None, rules: Optional[str] = None, no_rules: bool = False,
                 without_check: Sequence[str] = (), add_check: Sequence[str] = ()) -> Dict[str, Any]:
    """Change an existing setup. Returns `changed` (the list of changed settings)."""
    root = _root(repo)
    cfg = load_config(root)
    chosen = cfg.setdefault("setup", {}).setdefault("chosen", {})
    changed: List[str] = []
    if commit:
        cfg.setdefault("records", {})["commit"] = commit
        apply_commit_mode(root, commit)
        chosen["commit"] = commit
        changed.append(f"records.commit={commit}")
    if standards:
        cfg["standards"] = [s.strip() for s in standards.split(",") if s.strip()]
        changed.append("standards")
    if template:
        busy = open_tasks(root)
        if busy:
            raise WorkflowError("Finish or close these tasks before changing the template, so their specs keep the "
                                f"template they were written for: {', '.join(busy)}.")
        template_src, rules_src, name, source_label = resolve_template(template=template, rules=rules,
                                                                       no_rules=no_rules)
        install_template(root, cfg, template_src, rules_src, name, source_label)
        chosen["template"] = source_label
        changed.append(f"template={source_label}")
    if without_check or add_check:
        cfg["checks"] = change_checks(cfg.get("checks") or [], without_check, add_check)
        chosen["checks"] = [c["id"] for c in cfg["checks"]]
        changed.append("checks")
    if not changed:
        raise WorkflowError("Nothing to change: pass --commit, --standards, --template, --add-check or --without-check.")
    cfg["setup"].setdefault("changes", []).append({"at": now_iso(), "by": agent, "changed": changed})
    assert_no_secrets(json.dumps(cfg), "config.json")
    save_json(config_path(root), cfg)
    return {"changed": changed}


def new_task(*, repo: PathLike, task: str, title: str, task_type: str, invocation: Optional[str], agent: str,
             session: Optional[str] = None) -> Dict[str, Any]:
    """Create a task. Returns `task`, `commit_mode_message` (or None), `paused` (task paused by this one, or None),
    `preexisting` (count of files with uncommitted changes), `next` and `read`.

    If the records commit mode was applied in this clone and anything later fails, the exception carries the
    message in its `notices` attribute, because it was already applied.
    """
    if not invocation or not INVOCATION_RE.search(invocation):
        raise WorkflowError(
            "Task files are created only when the user explicitly starts AIDevWorkflow. Pass the user's starting "
            "message with --invocation; it must name the skill (for example '/ai-dev-workflow …'). If the user did not "
            "ask for AIDevWorkflow, stop and work normally.")
    root = _root(repo)
    cfg = load_config(root)
    notice = apply_commit_mode_in_clone(root, cfg)
    try:
        return _create_task(root, cfg, task, title, task_type, invocation, agent, session, notice)
    except BaseException as exc:
        if notice:
            setattr(exc, "notices", [notice])
        raise


def _create_task(root: Path, cfg: Dict[str, Any], task: str, title: str, task_type: str, invocation: str,
                 agent: str, session: Optional[str], notice: Optional[str]) -> Dict[str, Any]:
    if not SLUG_RE.match(task) or len(task) > 60:
        raise WorkflowError("Task names use lowercase letters, digits and single hyphens (e.g. saved-places), at most 60 characters.")
    tdir = task_dir(root, task)
    if tdir.exists():
        raise WorkflowError(f"Task '{task}' already exists; resume it with `workflow.py resume {task}`.")
    if task_type not in TASK_TYPES:
        raise WorkflowError(f"--type must be one of {', '.join(TASK_TYPES)}.")
    tpl_path = template_path(root, cfg)
    load_rules(root, cfg)
    title = title.strip()
    invocation = redact(invocation.strip())[:500]
    assert_no_secrets(title, "the task title")
    tdir.mkdir(parents=True)
    write_text(tdir / "spec.md", read_text(tpl_path))
    for name in ("dependencies.md", "plan.md", "verification.md", "audit.md", "report.md"):
        write_text(tdir / name, read_text(record_template(name)).replace("[Task title]", title))
    state: Dict[str, Any] = {
        "schema": 1, "id": task, "title": title, "type": task_type,
        "created_at": now_iso(), "created_by": agent, "invocation": invocation,
        "stage": "DISCOVERY", "status": "active", "outcome": None,
        "template": {"path": cfg["spec_template"], "sha256": sha256_file(tpl_path), "rules": cfg.get("spec_rules")},
        "discovery": {"inspected": [], "summary": ""},
        "approvals": {}, "spec_review": {}, "progress": {}, "checks": [], "checkpoints": [],
        "decisions": [], "excluded": [], "history": [],
        "baseline": {"start": git_baseline(root)},
    }
    add_history(state, "created", agent, invocation=invocation)
    paused = activate(root, state, agent, session)
    save_state(root, state)
    return {"task": task, "commit_mode_message": notice, "paused": paused,
            "preexisting": len(state["baseline"]["start"]["dirty"]), "next": NEXT["DISCOVERY"],
            "read": REFERENCE["DISCOVERY"]}


def status(*, repo: PathLike, task: Optional[str] = None) -> Dict[str, Any]:
    """Status. Without setup: `setup` (False) and `message`. With `task`: the detailed task summary (`task`, `title`,
    `type`, `stage`, `stage_number`, `status`, `outcome`, `status_line`, `updated_at`, `approvals`, `progress`,
    `active_here`, `warnings`, `next`, `read`). Otherwise `setup` (True), `active` and `tasks` (short summaries)."""
    root = _root(repo)
    if not config_path(root).exists():
        return {"setup": False, "message": "AIDevWorkflow is not set up in this repository (no .ai-dev-workflow/config.json)."}
    cfg = load_config(root)
    if task:
        return task_summary(root, cfg, load_state(root, task), detailed=True)
    tasks = [task_summary(root, cfg, load_state(root, slug), detailed=False) for slug in list_tasks(root)]
    active = read_active(root)
    return {"setup": True, "active": active.get("task") if active else None, "tasks": tasks}


def record_discovery(*, repo: PathLike, task: str, agent: str, inspected: Sequence[str] = (),
                     summary: Optional[str] = None) -> Dict[str, Any]:
    """Record inspected paths and the discovery summary. Returns `inspected` (count), `summary_set` and `missing`
    (inspected paths that do not exist)."""
    root, _, state = _task(repo, task)
    discovery = state.setdefault("discovery", {"inspected": [], "summary": ""})
    missing = []
    for rel in inspected or []:
        rel = rel.strip().replace("\\", "/")
        if rel and rel not in discovery["inspected"]:
            discovery["inspected"].append(rel)
            if not (root / rel).exists():
                missing.append(rel)
    if summary is not None:
        assert_no_secrets(summary, "the discovery summary")
        discovery["summary"] = summary.strip()
    add_history(state, "discovery", agent, inspected=len(discovery["inspected"]))
    save_state(root, state)
    return {"inspected": len(discovery["inspected"]), "summary_set": bool(discovery.get("summary")), "missing": missing}


# ------------------------------------------------------------------------------- specification and lifecycle

def spec_check(*, repo: PathLike, task: str) -> Dict[str, Any]:
    """Specification check (nothing is written). Returns `task`, `spec_sha256`, `template`, `rules`,
    `template_changed`, `mandatory`, `flags`, `judgment`, `advisory`, `prompts`, `ready`."""
    root, cfg, state = _task(repo, task)
    return _spec_check(root, state, cfg)


def plan_check(*, repo: PathLike, task: str) -> Dict[str, Any]:
    """Plan check (nothing is written). Returns `plan_sha256`, `steps`, `mandatory`, `advisory`, `ready`."""
    root, _, state = _task(repo, task)
    return _plan_check(root, state)


def review(*, repo: PathLike, task: str, agent: str, maps: Sequence[str] = (), questions: Sequence[str] = (),
           dismiss: Sequence[Tuple[str, str]] = (), notes: Sequence[str] = (),
           passes: Sequence[str] = ()) -> Dict[str, Any]:
    """Record the agent's spec review (mappings, question answers, dismissed flags, passed judgment rules). Returns
    `spec_check`: the fresh spec check after recording."""
    root, cfg, state = _task(repo, task)
    if state["stage"] not in ("SPECIFICATION", "SPEC_APPROVAL"):
        raise WorkflowError("The spec review is recorded in SPECIFICATION or SPEC_APPROVAL.")
    _, rules, _, _ = spec_rules_and_template(root, cfg)
    spec_file = task_dir(root, state["id"]) / "spec.md"
    spec_hash = sha256_file(spec_file)
    doc = Doc(read_text(spec_file))
    spec_review = state.setdefault("spec_review", {})
    if spec_review.get("spec_sha256") != spec_hash:
        spec_review["spec_sha256"] = spec_hash
        spec_review["rules"] = {}
    spec_review.setdefault("map", {})
    spec_review.setdefault("questions", {})
    spec_review.setdefault("dismissed", {})
    tpl, _, _, _ = spec_rules_and_template(root, cfg)
    known_targets = {ident for items in doc.items.values() for ident, _, _, _ in items}
    known_targets.update(i for i, _ in verification_items(doc, rules, tpl))
    for item in maps or []:
        source, _, targets = item.partition("=")
        source = source.strip()
        values = [t.strip() for t in targets.split(",") if t.strip()]
        if source not in known_targets or not values:
            raise WorkflowError(f"--map {item}: use REQ=TARGET[,TARGET…] with IDs from the spec (e.g. FR-1=AC-2,DW-3) or test:<name>.")
        for value in values:
            if not value.startswith("test:") and value not in known_targets:
                raise WorkflowError(f"--map {item}: {value} is not an ID in the spec (use AC-n, EC-n, DW-n or test:<name>).")
        spec_review["map"][source] = values
    question_keys = {k for adv in rules.get("advisory", []) if adv.get("type") == "questions" for k in adv.get("questions", {})}
    for item in questions or []:
        key, _, value = item.partition("=")
        key, value = key.strip(), value.strip()
        if key not in question_keys:
            raise WorkflowError(f"--question {item}: unknown question key; known keys: {', '.join(sorted(question_keys)) or 'none'}.")
        if not (value in known_targets or (value.lower().startswith("n/a:") and len(value) > 5)):
            raise WorkflowError(f"--question {item}: use {key}=EC-n, or {key}=n/a:<reason>.")
        spec_review["questions"][key] = value
    current_flags = {f["id"]: f for f in judgment_flags(doc, rules, state)}
    for flag_id, reason in dismiss or []:
        flag = current_flags.get(flag_id)
        if not flag:
            raise WorkflowError(f"There is no current flag '{flag_id}'. Run spec-check to list flags.")
        if not flag["dismissable"]:
            raise WorkflowError(f"Flag '{flag_id}' cannot be dismissed; resolve it instead.")
        if len(reason.strip()) < 5:
            raise WorkflowError("Give a real reason when dismissing a flag.")
        assert_no_secrets(reason, "the dismissal reason")
        spec_review["dismissed"][flag_id] = {"reason": reason.strip(), "agent": agent, "at": now_iso()}
    rule_notes = {}
    for item in notes or []:
        rule_id, _, text = item.partition("=")
        rule_notes[rule_id.strip()] = text.strip()
    rule_defs = {r["id"]: r for r in rules.get("judgment", [])}
    remaining = {f["id"]: f for f in judgment_flags(doc, rules, state)
                 if not (f["dismissable"] and f["id"] in spec_review["dismissed"])}
    for rule_id in passes or []:
        rule = rule_defs.get(rule_id)
        if not rule:
            raise WorkflowError(f"Unknown judgment rule '{rule_id}'. Rules: {', '.join(rule_defs) or 'none'}.")
        open_for_rule = [f["id"] for f in remaining.values() if f["rule"] == rule_id]
        if open_for_rule:
            raise WorkflowError(f"{rule_id} still has open flags: {', '.join(open_for_rule)}.")
        note = rule_notes.get(rule_id, "")
        if rule.get("requires_note") and len(note) < 10:
            raise WorkflowError(f"{rule_id} needs --note {rule_id}=\"…\" explaining the basis (for structures: the "
                                "existing files or patterns each proposal follows).")
        assert_no_secrets(note, "the review note")
        spec_review["rules"][rule_id] = {"status": "pass", "note": note, "agent": agent, "at": now_iso()}
    add_history(state, "spec-review", agent, spec_sha256=short(spec_hash))
    save_state(root, state)
    return {"spec_check": _spec_check(root, state, cfg)}


def approve(*, repo: PathLike, task: str, document: str, evidence: Optional[str], agent: str,
            by: Optional[str] = None) -> Dict[str, Any]:
    """Record the user's approval of the spec or the plan and freeze a snapshot. Returns `document`, `version`,
    `sha256`, `snapshot`, `stage` (after the approval) and `message`."""
    root, cfg, state = _task(repo, task)
    doc_name = document
    evidence = (evidence or "").strip()
    if len(evidence) < 2:
        raise WorkflowError("--evidence must quote the user's explicit approval (their own words).")
    assert_no_secrets(evidence, "the approval evidence")
    if doc_name == "spec":
        if state["stage"] != "SPEC_APPROVAL":
            raise WorkflowError(f"The spec can be approved only in SPEC_APPROVAL (current stage {state['stage']}).")
        result = _spec_check(root, state, cfg)
        if not result["ready"]:
            problems = [p["message"] for p in result["mandatory"]] + [f["message"] for f in result["flags"]]
            problems += [f"{k} not reviewed" for k, v in result["judgment"].items() if v["status"] != "pass"]
            raise WorkflowError("The spec is not ready for approval:\n" + bullet_list(problems))
    else:
        if state["stage"] != "PLAN_APPROVAL":
            raise WorkflowError(f"The plan can be approved only in PLAN_APPROVAL (current stage {state['stage']}).")
        ok, message = approval_status(root, state, "spec")
        if not ok:
            raise WorkflowError(message)
        result = _plan_check(root, state)
        if not result["ready"]:
            raise WorkflowError("The plan is not ready for approval:\n" + bullet_list([p["message"] for p in result["mandatory"]]))
    tdir = task_dir(root, state["id"])
    source = tdir / f"{doc_name}.md"
    digest = sha256_file(source)
    previous = state["approvals"].get(doc_name)
    version = (previous["version"] + 1) if previous else 1
    snapshot_rel = f"approved/{doc_name}.v{version}.md"
    while (tdir / snapshot_rel).exists():
        version += 1
        snapshot_rel = f"approved/{doc_name}.v{version}.md"
    write_text(tdir / snapshot_rel, read_text(source))
    make_readonly(tdir / snapshot_rel)
    record = {"version": version, "sha256": digest, "snapshot": snapshot_rel, "approved_by": (by or "user").strip(),
              "evidence": evidence, "recorded_by": agent, "recorded_at": now_iso()}
    if doc_name == "plan":
        record["spec_sha256"] = state["approvals"]["spec"]["sha256"]
        record["spec_version"] = state["approvals"]["spec"]["version"]
    state["approvals"][doc_name] = record
    add_history(state, "approved", agent, document=doc_name, version=version, sha256=short(digest))
    if doc_name == "spec":
        add_history(state, "stage", agent, **{"from": "SPEC_APPROVAL", "to": "PLANNING", "reason": "spec approved"})
        state["stage"] = "PLANNING"
        message = f"Spec v{version} ({short(digest)}) approved; frozen as {snapshot_rel}. Stage: PLANNING."
    else:
        blockers = blocking_deps(root, state, ("spec", "plan", "implementation"))
        if blockers:
            message = (f"Plan v{version} ({short(digest)}) approved and frozen as {snapshot_rel}, but implementation is "
                       f"blocked by {', '.join(d['id'] for d in blockers)}. Stage stays PLAN_APPROVAL.")
        else:
            add_history(state, "stage", agent, **{"from": "PLAN_APPROVAL", "to": "IMPLEMENTATION", "reason": "plan approved"})
            state["stage"] = "IMPLEMENTATION"
            state["baseline"]["implementation"] = git_baseline(root)
            add_checkpoint(state, "implementation-start", agent, code_fingerprint(root), {}, True)
            message = (f"Plan v{version} ({short(digest)}) approved; frozen as {snapshot_rel}. Stage: IMPLEMENTATION. "
                       "Run `preflight` before editing code.")
    save_state(root, state)
    return {"document": doc_name, "version": version, "sha256": digest, "snapshot": snapshot_rel,
            "stage": state["stage"], "message": message}


def stage(*, repo: PathLike, task: str, stage: str, agent: str, reason: Optional[str] = None) -> Dict[str, Any]:
    """Move the task to another stage (the gates decide). Returns `task`, `stage`, `next`, `read`."""
    root, cfg, state = _task(repo, task)
    if reason:
        assert_no_secrets(reason, "the reason")
    transition(root, state, cfg, stage.upper(), reason, agent)
    save_state(root, state)
    return {"task": state["id"], "stage": state["stage"], "next": NEXT[state["stage"]],
            "read": REFERENCE[state["stage"]]}


def resume(*, repo: PathLike, task: str, agent: str, session: Optional[str] = None) -> Dict[str, Any]:
    """Make the task active in this checkout. Returns `paused` (the task paused by this one, or None), `summary`
    (the detailed task summary) and `code_stage` (True in IMPLEMENTATION or FIXING)."""
    root, cfg, state = _task(repo, task)
    if state["status"] == "closed":
        raise WorkflowError(f"Task '{state['id']}' is closed ({state.get('outcome')}).")
    was = state["status"]
    state["status"] = "active"
    paused = activate(root, state, agent, session)
    add_history(state, "resumed", agent, previous=was)
    save_state(root, state)
    return {"paused": paused, "summary": task_summary(root, cfg, state, detailed=True),
            "code_stage": state["stage"] in CODE_STAGES}


def pause(*, repo: PathLike, task: str, agent: str, reason: Optional[str] = None) -> Dict[str, Any]:
    """Pause the task. Returns `task`."""
    root, _, state = _task(repo, task)
    if state["status"] == "closed":
        raise WorkflowError("The task is closed.")
    state["status"] = "paused"
    add_history(state, "paused", agent, reason=reason)
    clear_active(root, state["id"])
    save_state(root, state)
    return {"task": state["id"]}


# --------------------------------------------------------------------------------- implementation and evidence

def preflight(*, repo: PathLike, task: str, agent: str, session: Optional[str] = None) -> Dict[str, Any]:
    """Revalidate the task before code edits and record a checkpoint. Returns `valid`, `problems`, `unattributed`
    (changes no recorded step explains), `task`, `stage` and `analyzer_hint` (the baseline reminder, or None).
    The CLI's `--json` output shows only `valid`, `problems` and `unattributed`."""
    root, _, state = _task(repo, task)
    session = clean_session(session)
    problems = []
    if state["status"] == "closed":
        problems.append("The task is closed.")
    elif state["status"] == "paused":
        problems.append(f"The task is paused; run `workflow.py resume {state['id']}` first.")
    if state["stage"] not in CODE_STAGES:
        problems.append(f"The stage is {state['stage']}; code may change only in IMPLEMENTATION or FIXING.")
    for doc_name in ("spec", "plan"):
        ok, message = approval_status(root, state, doc_name)
        if not ok:
            problems.append(message)
    for dep in blocking_deps(root, state, ("spec", "plan", "implementation")):
        problems.append(f"{dep['id']} ({dep['summary']}) still blocks implementation.")
    problems += scan_records(root, state["id"])
    base = state["baseline"].get("implementation")
    changes: Dict[str, str] = {}
    unattributed: List[str] = []
    if base:
        cs = change_set(root, base, state.get("excluded", []))
        changes = cs["task"]
        last = (state.get("last_checkpoint") or {}).get("changes") or {}
        unattributed = sorted({p for p, h in changes.items() if last.get(p) != h} | {p for p in last if p not in changes})
    valid = not problems
    add_checkpoint(state, "preflight", agent, code_fingerprint(root), changes, valid,
                   session=session, unattributed=unattributed[:50] or None)
    if valid:
        active = read_active(root)
        if not active or active.get("task") != state["id"]:
            activate(root, state, agent, session)
            active = read_active(root) or {}
        active.update({"agent": agent, "session": session or active.get("session"),
                       "preflight_session": session, "preflight_at": now_iso()})
        save_json(active_path(root), active)
    add_history(state, "preflight", agent, valid=valid)
    save_state(root, state)
    analyzer_hint = None
    if valid and state["stage"] == "IMPLEMENTATION" and not any(e.get("kind") == "baseline" for e in state["checks"]):
        analyzers = [c["id"] for c in load_config(root).get("checks", []) if c.get("parser") == "dart-analyzer"]
        if analyzers and not changes:
            analyzer_hint = (f"Capture the analyzer baseline before your first edit: "
                             f"`workflow.py run {state['id']} {analyzers[0]} --baseline`.")
    return {"valid": valid, "problems": problems, "unattributed": unattributed, "task": state["id"],
            "stage": state["stage"], "analyzer_hint": analyzer_hint}


def step(*, repo: PathLike, task: str, step: str, status: str, agent: str, files: Optional[str] = None,
         note: Optional[str] = None) -> Dict[str, Any]:
    """Record progress on a step of the approved plan. Returns `step`, `status`, `files` (attributed), `done` and
    `total` (steps)."""
    root, _, state = _task(repo, task)
    if state["stage"] not in CODE_STAGES or state["status"] != "active":
        raise WorkflowError("Steps are recorded during IMPLEMENTATION or FIXING on an active task.")
    for doc_name in ("spec", "plan"):
        ok, message = approval_status(root, state, doc_name)
        if not ok:
            raise WorkflowError(message)
    steps = plan_steps(root, state)
    if step not in steps:
        raise WorkflowError(f"{step} is not a step of the approved plan ({', '.join(steps)}).")
    if status not in ("done", "in-progress", "todo"):
        raise WorkflowError("Status must be done, in-progress or todo.")
    base = state["baseline"].get("implementation") or {}
    changes = change_set(root, base, state.get("excluded", []))["task"] if base else {}
    last = (state.get("last_checkpoint") or {}).get("changes") or {}
    changed = sorted({p for p, h in changes.items() if last.get(p) != h} | {p for p in last if p not in changes})
    attributed = [f.strip() for f in (files or "").split(",") if f.strip()] or changed
    if note:
        assert_no_secrets(note, "the step note")
    state["progress"][step] = {"status": status, "files": attributed, "note": (note or "").strip(),
                               "agent": agent, "at": now_iso()}
    add_checkpoint(state, "step", agent, code_fingerprint(root), changes, True, step=step)
    add_history(state, "step", agent, step=step, status=status)
    save_state(root, state)
    done = sum(1 for s in steps if state["progress"].get(s, {}).get("status") == "done")
    return {"step": step, "status": status, "files": attributed, "done": done, "total": len(steps)}


def run_check(*, repo: PathLike, task: str, check: str, agent: str, extra: Sequence[str] = (),
              baseline: bool = False, force: bool = False, blocked: Optional[str] = None,
              not_applicable: Optional[str] = None) -> Dict[str, Any]:
    """Run a configured check (or an extra command) and record the evidence. Returns `entry` (the recorded result:
    `id`, `status`, `summary`, `reason`, `fingerprint`, …), `output_tail` (the last 120 output lines, redacted;
    empty when nothing ran) and `recorded_on_purpose` (True for --blocked or --not-applicable).

    If anything fails after the command ran, the exception carries the output in its `output_tail` attribute."""
    root, cfg, state = _task(repo, task)
    checks = {c["id"]: c for c in cfg.get("checks", [])}
    chosen = checks.get(check)
    if chosen is None:
        if not extra:
            raise WorkflowError(f"Unknown check '{check}'. Configured: {', '.join(checks) or 'none'}. "
                                "For an extra command use: run <task> <name> -- <command …>.")
        chosen = {"id": check, "name": check, "command": " ".join(shlex.quote(a) for a in extra), "required": False}
        extra_args: List[str] = []
    else:
        extra_args = list(extra or [])
        if extra_args and not chosen.get("accepts_args"):
            raise WorkflowError(f"Check '{chosen['id']}' does not take extra arguments.")
    entry: Dict[str, Any] = {"id": chosen["id"], "name": chosen.get("name", chosen["id"]), "kind": "result",
                             "agent": agent, "at": now_iso(), "counts": None, "reason": None}
    output_tail: List[str] = []
    try:
        if not_applicable:
            if chosen.get("required") and not chosen.get("when"):
                raise WorkflowError(f"'{chosen['id']}' is always required; if it cannot run, use --blocked \"<reason>\".")
            entry.update(status="not-applicable", summary="", reason=not_applicable.strip())
        elif blocked:
            entry.update(status="blocked", summary="", reason=blocked.strip())
        elif chosen.get("builtin"):
            builtin_status, summary, _ = builtin_check(root, state, cfg, chosen)
            entry.update(status=builtin_status, summary=redact(summary)[:500], command=f"built-in {chosen['builtin']}")
        else:
            if baseline and chosen.get("parser") != "dart-analyzer":
                raise WorkflowError("--baseline is only for analyzer checks (parser dart-analyzer).")
            if baseline:
                base = state["baseline"].get("implementation")
                if not base:
                    raise WorkflowError("Capture the baseline after the plan is approved (IMPLEMENTATION), before editing code.")
                if change_set(root, base, state.get("excluded", []))["task"] and not force:
                    raise WorkflowError("Code already changed since implementation started; a baseline now would hide new "
                                        "issues. Use --force only if the user agrees.")
            code, output, duration, error = execute(root, chosen["command"], extra_args, int(chosen.get("timeout_s", 1800)))
            command_text = redact(" ".join([chosen["command"], *extra_args]))
            entry.update(command=command_text, duration_s=round(duration, 1), exit_code=code)
            if error:
                entry.update(status="blocked", summary="", reason=f"Could not run: {error}.")
            else:
                output_tail = [redact(line) for line in output.splitlines()[-120:]]
                if chosen.get("parser") == "dart-analyzer":
                    issues, counts = parse_analyzer(output)
                    entry["counts"] = counts
                    if baseline:
                        state["baseline"].setdefault("analyzer", {})[chosen["id"]] = sorted({analyzer_key(i) for i in issues})
                        entry.update(kind="baseline", status="baseline",
                                     summary=f"{counts['error']} errors, {counts['warning']} warnings, {counts['info']} infos")
                    else:
                        recognized = bool(issues) or "no issues found" in output.lower()
                        baseline_keys = state["baseline"].get("analyzer", {}).get(chosen["id"])
                        has_baseline = baseline_keys is not None
                        baseline_set = set(baseline_keys or [])
                        fail_on = chosen.get("fail_on", ["error", "warning"])
                        failing = [i for i in issues if i["severity"] in fail_on]
                        new = [i for i in issues if analyzer_key(i) not in baseline_set] if has_baseline else []
                        if has_baseline and "new" in fail_on:
                            failing += [i for i in new if i not in failing]
                        summary = f"{counts['error']} errors, {counts['warning']} warnings, {counts['info']} infos"
                        summary += f"; {len(new)} new since baseline" if has_baseline else "; no baseline captured"
                        if not recognized and code != 0:
                            entry.update(status="failed", summary=f"exit {code}: {last_line(output)}")
                        elif not failing:
                            entry.update(status="passed", summary=summary)
                        elif has_baseline and all(analyzer_key(i) in baseline_set for i in failing):
                            entry.update(status="preexisting", summary=summary)
                        else:
                            entry.update(status="failed", summary=summary)
                else:
                    entry.update(status="passed" if code == 0 else "failed",
                                 summary=(f"exit {code}: " if code else "") + last_line(output))
        if entry.get("reason"):
            assert_no_secrets(entry["reason"], "the reason")
        entry["fingerprint"] = code_fingerprint(root)
        state["checks"].append(entry)
        del state["checks"][:-200]
        add_history(state, "check", agent, check=chosen["id"], status=entry["status"])
        regenerate_check_block(root, state)
        save_state(root, state)
    except BaseException as exc:
        # The CLI printed the output before any later refusal; keep that by handing the tail to the caller.
        if output_tail:
            setattr(exc, "output_tail", output_tail)
        raise
    return {"entry": entry, "output_tail": output_tail, "recorded_on_purpose": bool(blocked or not_applicable)}


def scope(*, repo: PathLike, task: str, agent: str, exclude: Sequence[str] = (),
          reason: Optional[str] = None) -> Dict[str, Any]:
    """Changes in the task's scope, optionally excluding unrelated files first. Returns exactly `baseline`
    ("implementation" or "task start"), `task_changes`, `unattributed`, `preexisting_modified`,
    `preexisting_untouched`, `excluded` and `notes`."""
    root, _, state = _task(repo, task)
    if exclude:
        if not reason:
            raise WorkflowError("Excluding a file from the task scope needs --reason (e.g. the user confirmed it is unrelated).")
        assert_no_secrets(reason, "the reason")
        for rel in exclude:
            if rel not in state["excluded"]:
                state["excluded"].append(rel)
        add_history(state, "scope-exclude", agent, files=list(exclude), reason=reason)
        save_state(root, state)
    base = state["baseline"].get("implementation") or state["baseline"].get("start") or {}
    cs = change_set(root, base, state.get("excluded", []))
    attributed = {f for p in state["progress"].values() for f in p.get("files", [])}
    return {
        "baseline": "implementation" if state["baseline"].get("implementation") else "task start",
        "task_changes": sorted(cs["task"]), "unattributed": sorted(p for p in cs["task"] if p not in attributed),
        "preexisting_modified": cs["preexisting_modified"], "preexisting_untouched": cs["preexisting_untouched"],
        "excluded": cs["excluded"], "notes": cs["notes"],
    }


def decision(*, repo: PathLike, task: str, text: Optional[str], evidence: Optional[str], agent: str,
             by: Optional[str] = None) -> Dict[str, Any]:
    """Record a user decision with the user's own words. Returns `count` (decisions recorded in total)."""
    root, _, state = _task(repo, task)
    text, evidence = (text or "").strip(), (evidence or "").strip()
    if not text or not evidence:
        raise WorkflowError("A decision needs --text and --evidence (the user's own words).")
    assert_no_secrets(text + "\n" + evidence, "the decision")
    state["decisions"].append({"text": text, "evidence": evidence, "by": (by or "user").strip(),
                               "recorded_by": agent, "at": now_iso()})
    add_history(state, "decision", agent)
    save_state(root, state)
    return {"count": len(state["decisions"])}


def check_records(*, repo: PathLike, task: Optional[str] = None) -> Dict[str, Any]:
    """Consistency check of the records (nothing is written). Returns `ok`, `errors`, `warnings`."""
    root = _root(repo)
    cfg = load_config(root)
    errors: List[str] = []
    warnings: List[str] = []
    for name in ("config.json", "PROJECT.md"):
        path = records_dir(root) / name
        if path.exists():
            errors += [f"{name}:{line} looks like it contains a {kind}." for kind, line in find_secrets(read_text(path))]
    template_path(root, cfg)
    load_rules(root, cfg)
    slugs = [task] if task else list_tasks(root)
    for slug in slugs:
        state = load_state(root, slug)
        task_errors, task_warnings = validate_task(root, cfg, state)
        errors += [f"{slug}: {e}" for e in task_errors]
        warnings += [f"{slug}: {w}" for w in task_warnings]
    return {"ok": not errors, "errors": errors, "warnings": warnings}


def outcome(*, repo: PathLike, task: str) -> Dict[str, Any]:
    """Highest final status the evidence allows (nothing is written). Returns `max`, `blocked`, `allowed`,
    `reasons` and the other keys of `compute_outcome`."""
    root, cfg, state = _task(repo, task)
    return compute_outcome(root, state, cfg)


def close(*, repo: PathLike, task: str, agent: str) -> Dict[str, Any]:
    """Close the task with the status written in report.md, if the evidence allows it. Returns `task`, `outcome`."""
    root, cfg, state = _task(repo, task)
    if state["status"] == "closed":
        raise WorkflowError("The task is already closed.")
    if state["stage"] != "FINAL_REPORT":
        raise WorkflowError(f"Close the task from FINAL_REPORT (current stage {state['stage']}).")
    report = parse_report(root, state["id"])
    if report["problems"]:
        raise WorkflowError("report.md is not complete:\n" + bullet_list(report["problems"]))
    result = compute_outcome(root, state, cfg)
    claimed = report["status"]
    if claimed not in result["allowed"]:
        raise WorkflowError(f"report.md says '{claimed}', but the evidence allows at most '{result['max']}'"
                            + (" (or Blocked)" if result["blocked"] else "") + ":\n" + bullet_list(result["reasons"]))
    state["status"] = "closed"
    state["outcome"] = claimed
    state["closed_at"] = now_iso()
    add_history(state, "closed", agent, outcome=claimed)
    clear_active(root, state["id"])
    save_state(root, state)
    return {"task": state["id"], "outcome": claimed}
