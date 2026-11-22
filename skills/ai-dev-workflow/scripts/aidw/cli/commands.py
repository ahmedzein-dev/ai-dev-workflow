"""The engine's commands."""
from __future__ import annotations

import argparse
import json
import re
import shlex
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from aidw.cli.helpers import print_summary, require_task, task_summary
from aidw.constants import CODE_STAGES, INVOCATION_RE, NEXT, RECORDS, RECORD_FILES, REFERENCE, SLUG_RE, STAGES, TASK_TYPES
from aidw.core.checks import analyzer_key, builtin_check, execute, last_line, parse_analyzer, regenerate_check_block
from aidw.core.gates import approval_status, check_freshness, plan_steps, transition
from aidw.core.outcome import compute_outcome
from aidw.core.setup import DISCOVERY_ONLY_KEYS, RECORDS_README, apply_commit_mode, discover_project, ensure_commit_mode
from aidw.core.spec import judgment_flags, plan_check, spec_check, spec_rules_and_template, verification_items
from aidw.errors import WorkflowError
from aidw.infra.gitutil import change_set, code_fingerprint, find_repo, git_baseline
from aidw.infra.secrets import assert_no_secrets, find_secrets, redact
from aidw.infra.text import agent_name, bullet_list, clean_session, load_json, make_readonly, now_iso, read_text, save_json, sha256_file, short, write_text
from aidw.records.markdown import Doc
from aidw.records.parsers import blocking_deps, parse_audit, parse_dependencies, parse_matrix, parse_report
from aidw.store.config import config_path, library_dir, load_config, load_rules, record_template, records_dir, task_dir, template_path
from aidw.store.state import activate, active_path, add_checkpoint, add_history, clear_active, list_tasks, load_state, read_active, save_state


def print_discovery(report: Dict[str, Any]) -> None:
    existing = report["existing"]
    if existing:
        print(f"AIDevWorkflow is already set up in {report['repository']}. Reuse these settings; do not ask the setup "
              "questions again unless something below is missing or invalid, or the user asks for a change "
              "(`init --update`).")
        print(f"  Template: {existing.get('template')}   Records in git: {existing.get('commit')}   "
              f"Checks: {', '.join(existing.get('checks') or []) or 'none'}")
        for problem in existing["problems"]:
            print(f"  PROBLEM: {problem}")
        for note in existing["notes"]:
            print(f"  Note: {note}")
        return
    print(f"Setup proposal for {report['repository']}. These are recommendations; nothing is saved until the user "
          "confirms them and you run `init`.")
    print("\n1. Engineering standards (instruction files every agent follows): "
          + (", ".join(report["instruction_files"]) or "none found"))
    tpl = report["template"]
    print("\n2. Specification template")
    print(f"   Recommended: {tpl['recommended']}" if tpl["recommended"] else "   Recommended: none")
    print(f"   Why: {tpl['reason']}")
    others = [c + (" (example)" if "example" in c.lower() else "") for c in report["template_candidates"]]
    others += [t["name"] for t in report["user_templates"] if t["name"] != tpl["recommended"]]
    print("   Other choices: " + (", ".join(others) + ", or a file the user provides" if others
                                  else "a file the user provides"))
    print("\n3. Checks (recommended from the project's own files; not run yet)")
    if not report["suggested_checks"]:
        print("   None detected. Inspect the project (README, CI, scripts) and propose commands to the user.")
    for check in report["suggested_checks"]:
        what = check.get("command") or f"built-in {check['builtin']}"
        flags = ("" if check.get("required") else " (optional)") + \
            ("" if check.get("tool_found", True) else " [tool not found on this computer]")
        print(f"   - {check['id']}: {what}{flags}\n     {check['explain']} Found from: {check['evidence']}.")
    if report["ci_commands"]:
        print("   Commands the project's CI already runs (for reference): " + "; ".join(report["ci_commands"]))
    records = report["records"]
    print("\n4. Saving task records in git")
    for option in records["options"]:
        print(f"   - {option['mode']} — {option['label']}: {option['what']}\n"
              f"     After cloning: {option['after_clone']} Another computer or agent: {option['other_machine']}\n"
              f"     If this computer is lost: {option['if_lost']} Privacy: {option['privacy']}")
    for note in records["notes"]:
        print(f"   Note: {note}")
    print(f"   Recommended: {records['recommended']['mode']}. {records['recommended']['reason']}")
    template_arg = tpl["recommended"] or "<template>"
    print("\nExplain these in plain language, then ask the user to accept the recommendations or change any of them. "
          "After they confirm, run for example:\n"
          f"  workflow.py init --template {template_arg} --commit {records['recommended']['mode']}"
          + (f" --standards {','.join(report['instruction_files'])}" if report["instruction_files"] else "")
          + "\n  (add --without-check <id> or --add-check <id>=<command> for changes to the checks)")


def resolve_template(args: argparse.Namespace) -> Tuple[Path, Optional[Path], str, str]:
    if args.template.startswith("user:"):
        name = args.template[5:]
        source_dir = library_dir() / "templates" / name
        template_src = source_dir / "template.md"
        rules_src: Optional[Path] = source_dir / "rules.json"
        source_label = f"user:{name}"
    else:
        template_src = Path(args.template).expanduser()
        name = template_src.stem
        rules_src = Path(args.rules).expanduser() if args.rules else template_src.with_name(template_src.stem + ".rules.json")
        source_label = f"file:{template_src.name}"
    if not template_src.is_file():
        raise WorkflowError(f"Template not found: {args.template}. Ask the user for the right template.")
    if args.no_rules or not (rules_src and rules_src.is_file()):
        if args.rules and not args.no_rules:
            raise WorkflowError(f"Rules file not found: {args.rules}")
        rules_src = None
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-") or "spec-template"
    return template_src, rules_src, name, source_label


def install_template(repo: Path, cfg: Dict[str, Any], template_src: Path, rules_src: Optional[Path], name: str,
                     source_label: str) -> None:
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
    return [slug for slug in list_tasks(repo) if load_state(repo, slug).get("status") != "closed"]


def cmd_init(args: argparse.Namespace) -> int:
    repo = find_repo(args.repo)
    if args.discover:
        report = discover_project(repo)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print_discovery(report)
        return 0
    cfg_file = config_path(repo)
    if cfg_file.exists() and not args.update:
        raise WorkflowError("AIDevWorkflow is already set up here; reuse its settings. To change them, use --update "
                            "with --commit, --standards, --template, --add-check or --without-check.")
    if args.update:
        return update_setup(repo, args)
    if not args.commit:
        raise WorkflowError("Choose how task records are saved in git with --commit all, config-only or none. Explain "
                            "the options (`init --discover`) and ask the user.")
    if not args.template:
        raise WorkflowError("Choose the specification template with --template <path> or --template user:<name>. "
                            "Ask the user; never invent one. `init --discover` lists the recommendation and candidates.")
    base: Dict[str, Any] = {}
    if args.config:
        try:
            base = load_json(Path(args.config).expanduser())
        except (OSError, ValueError) as exc:
            raise WorkflowError(f"Could not read --config {args.config}: {exc}") from exc
    template_src, rules_src, name, source_label = resolve_template(args)
    proposal = discover_project(repo)
    recommended_checks = [{k: v for k, v in c.items() if k not in DISCOVERY_ONLY_KEYS}
                          for c in proposal["suggested_checks"]]
    checks = change_checks(base["checks"] if "checks" in base else recommended_checks,
                           args.without_check, args.add_check)
    standards = [s.strip() for s in (args.standards or "").split(",") if s.strip()] or base.get("standards") or \
        [p for p in ("CLAUDE.md", "AGENTS.md", "GEMINI.md") if (repo / p).exists()]
    cfg: Dict[str, Any] = {
        "schema": 1,
        "project": args.project or base.get("project") or repo.name,
        "standards": standards,
        "records": {"commit": args.commit},
        "checks": checks,
        "rules": base.get("rules", []),
        "setup": {
            "confirmed_at": now_iso(), "recorded_by": agent_name(args),
            "recommended": {"template": proposal["template"]["recommended"],
                            "commit": proposal["records"]["recommended"]["mode"],
                            "checks": [c["id"] for c in recommended_checks]},
            "chosen": {"template": source_label, "commit": args.commit, "checks": [c["id"] for c in checks]},
        },
    }
    install_template(repo, cfg, template_src, rules_src, name, source_label)
    cfg = {k: cfg[k] for k in ("schema", "project", "standards", "spec_template", "spec_rules", "template_source",
                               "records", "checks", "rules", "setup")}
    assert_no_secrets(json.dumps(cfg), "config.json")
    save_json(cfg_file, cfg)
    write_text(records_dir(repo) / "README.md", RECORDS_README)
    if args.project_notes:
        notes = read_text(Path(args.project_notes).expanduser())
    else:
        notes = ("# Project notes for AIDevWorkflow\n\nEngineering standards: " + (", ".join(standards) or "none listed")
                 + "\n\n## Standards conflicts and decisions\n\nNone recorded yet.\n\n## Audit checklist\n\n"
                 "List the sections of the standards files the audit must check.\n")
    assert_no_secrets(notes, "PROJECT.md")
    write_text(records_dir(repo) / "PROJECT.md", notes)
    exclude = apply_commit_mode(repo, args.commit)
    print(f"AIDevWorkflow is set up in {RECORDS}/ (template: {source_label}, rules: {'yes' if rules_src else 'none'}, "
          f"records.commit={args.commit}, checks: {', '.join(c['id'] for c in checks) or 'none'}).")
    if args.commit != "all":
        print(f"Local git exclude rules were written to {exclude} (no tracked files changed).")
    print("These settings are reused for every task in this project.")
    return 0


def update_setup(repo: Path, args: argparse.Namespace) -> int:
    cfg = load_config(repo)
    chosen = cfg.setdefault("setup", {}).setdefault("chosen", {})
    changed: List[str] = []
    if args.commit:
        cfg.setdefault("records", {})["commit"] = args.commit
        apply_commit_mode(repo, args.commit)
        chosen["commit"] = args.commit
        changed.append(f"records.commit={args.commit}")
    if args.standards:
        cfg["standards"] = [s.strip() for s in args.standards.split(",") if s.strip()]
        changed.append("standards")
    if args.template:
        busy = open_tasks(repo)
        if busy:
            raise WorkflowError("Finish or close these tasks before changing the template, so their specs keep the "
                                f"template they were written for: {', '.join(busy)}.")
        template_src, rules_src, name, source_label = resolve_template(args)
        install_template(repo, cfg, template_src, rules_src, name, source_label)
        chosen["template"] = source_label
        changed.append(f"template={source_label}")
    if args.without_check or args.add_check:
        cfg["checks"] = change_checks(cfg.get("checks") or [], args.without_check, args.add_check)
        chosen["checks"] = [c["id"] for c in cfg["checks"]]
        changed.append("checks")
    if not changed:
        raise WorkflowError("Nothing to change: pass --commit, --standards, --template, --add-check or --without-check.")
    cfg["setup"].setdefault("changes", []).append({"at": now_iso(), "by": agent_name(args), "changed": changed})
    assert_no_secrets(json.dumps(cfg), "config.json")
    save_json(config_path(repo), cfg)
    print("Updated the AIDevWorkflow settings: " + ", ".join(changed) + ".")
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    if not args.invocation or not INVOCATION_RE.search(args.invocation):
        raise WorkflowError(
            "Task files are created only when the user explicitly starts AIDevWorkflow. Pass the user's starting "
            "message with --invocation; it must name the skill (for example '/ai-dev-workflow …'). If the user did not "
            "ask for AIDevWorkflow, stop and work normally.")
    repo = find_repo(args.repo)
    cfg = load_config(repo)
    ensure_commit_mode(repo, cfg)
    agent = agent_name(args)
    if not SLUG_RE.match(args.task) or len(args.task) > 60:
        raise WorkflowError("Task names use lowercase letters, digits and single hyphens (e.g. saved-places), at most 60 characters.")
    tdir = task_dir(repo, args.task)
    if tdir.exists():
        raise WorkflowError(f"Task '{args.task}' already exists; resume it with `workflow.py resume {args.task}`.")
    if args.type not in TASK_TYPES:
        raise WorkflowError(f"--type must be one of {', '.join(TASK_TYPES)}.")
    tpl_path = template_path(repo, cfg)
    load_rules(repo, cfg)
    title = args.title.strip()
    invocation = redact(args.invocation.strip())[:500]
    assert_no_secrets(title, "the task title")
    tdir.mkdir(parents=True)
    write_text(tdir / "spec.md", read_text(tpl_path))
    for name in ("dependencies.md", "plan.md", "verification.md", "audit.md", "report.md"):
        write_text(tdir / name, read_text(record_template(name)).replace("[Task title]", title))
    state: Dict[str, Any] = {
        "schema": 1, "id": args.task, "title": title, "type": args.type,
        "created_at": now_iso(), "created_by": agent, "invocation": invocation,
        "stage": "DISCOVERY", "status": "active", "outcome": None,
        "template": {"path": cfg["spec_template"], "sha256": sha256_file(tpl_path), "rules": cfg.get("spec_rules")},
        "discovery": {"inspected": [], "summary": ""},
        "approvals": {}, "spec_review": {}, "progress": {}, "checks": [], "checkpoints": [],
        "decisions": [], "excluded": [], "history": [],
        "baseline": {"start": git_baseline(repo)},
    }
    add_history(state, "created", agent, invocation=invocation)
    paused = activate(repo, state, agent, args.session)
    save_state(repo, state)
    print(f"Created task '{args.task}' in {RECORDS}/tasks/{args.task}/ (stage DISCOVERY).")
    if paused:
        print(f"Task '{paused}' was active and is now paused.")
    pre = state["baseline"]["start"]["dirty"]
    if pre:
        print(f"{len(pre)} file(s) already had uncommitted changes; they are recorded as pre-existing and must be preserved.")
    print(f"Next: {NEXT['DISCOVERY']}")
    print(f"Read: {REFERENCE['DISCOVERY']}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    repo = find_repo(args.repo)
    if not config_path(repo).exists():
        message = "AIDevWorkflow is not set up in this repository (no .ai-dev-workflow/config.json)."
        print(json.dumps({"setup": False, "message": message}) if args.json else message)
        return 0
    cfg = load_config(repo)
    if args.task:
        info = task_summary(repo, cfg, load_state(repo, args.task), detailed=True)
        if args.json:
            print(json.dumps(info, indent=2, ensure_ascii=False))
        else:
            print_summary(info)
        return 0
    tasks = [task_summary(repo, cfg, load_state(repo, slug), detailed=False) for slug in list_tasks(repo)]
    active = read_active(repo)
    if args.json:
        print(json.dumps({"setup": True, "active": active.get("task") if active else None, "tasks": tasks}, indent=2))
        return 0
    if not tasks:
        print("No AIDevWorkflow tasks yet.")
        return 0
    for info in tasks:
        marker = "*" if active and active.get("task") == info["task"] else " "
        print(f"{marker} {info['task']:<32} {info['status_line']:<48} {info.get('title') or ''}")
    print("(* = active in this checkout)  Details: workflow.py status <task>")
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    repo, _, state = require_task(args)
    discovery = state.setdefault("discovery", {"inspected": [], "summary": ""})
    missing = []
    for rel in args.inspected or []:
        rel = rel.strip().replace("\\", "/")
        if rel and rel not in discovery["inspected"]:
            discovery["inspected"].append(rel)
            if not (repo / rel).exists():
                missing.append(rel)
    if args.summary is not None:
        assert_no_secrets(args.summary, "the discovery summary")
        discovery["summary"] = args.summary.strip()
    add_history(state, "discovery", agent_name(args), inspected=len(discovery["inspected"]))
    save_state(repo, state)
    print(f"Recorded {len(discovery['inspected'])} inspected path(s); summary {'set' if discovery.get('summary') else 'not set'}.")
    if missing:
        print("Note: these paths do not exist in the repository: " + ", ".join(missing))
    return 0


def print_spec_check(result: Dict[str, Any]) -> None:
    print(f"Spec check for '{result['task']}' — spec {short(result['spec_sha256'])}, template {result['template']}, "
          f"rules {result['rules'] or 'none (structure only)'}")
    if result["template_changed"]:
        print("Note: the project template changed since this task was created.")
    print(f"Mandatory (block approval): {len(result['mandatory'])}")
    for item in result["mandatory"]:
        print(f"  - [{item['rule']}]{' line ' + str(item['line']) if item['line'] else ''}: {item['message']}")
    print(f"Review flags (block approval until fixed or dismissed with a reason): {len(result['flags'])}")
    for flag in result["flags"]:
        extra = "" if flag["dismissable"] else " (cannot be dismissed)"
        print(f"  - {flag['id']}{extra}: {flag['message']}")
    if result["judgment"]:
        print("Judgment rules (reviewed by the agent, confirmed by the user's approval):")
        for rule_id, data in result["judgment"].items():
            print(f"  - {rule_id} [{data['status']}] {data['rule']}" + (f" — {data['note']}" if data["note"] else ""))
    print(f"Advisory warnings (do not block): {len(result['advisory'])}")
    for item in result["advisory"]:
        print(f"  - [{item['rule']}] {item['message']}")
    for prompt in result["prompts"]:
        print(f"  ? {prompt}")
    print("Ready for approval: " + ("yes" if result["ready"] else "no"))


def cmd_spec_check(args: argparse.Namespace) -> int:
    repo, cfg, state = require_task(args)
    result = spec_check(repo, state, cfg)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_spec_check(result)
    return 0 if not result["mandatory"] else 1


def cmd_plan_check(args: argparse.Namespace) -> int:
    repo, _, state = require_task(args)
    result = plan_check(repo, state)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["ready"] else 1
    print(f"Plan check for '{state['id']}' — plan {short(result['plan_sha256'])}, steps: {', '.join(result['steps']) or 'none'}")
    print(f"Mandatory: {len(result['mandatory'])}")
    for item in result["mandatory"]:
        print(f"  - [{item['rule']}]{' line ' + str(item['line']) if item['line'] else ''}: {item['message']}")
    print(f"Advisory: {len(result['advisory'])}")
    for item in result["advisory"]:
        print(f"  - {item['message']}")
    print("Ready for approval: " + ("yes" if result["ready"] else "no"))
    return 0 if result["ready"] else 1


def cmd_review(args: argparse.Namespace) -> int:
    repo, cfg, state = require_task(args)
    agent = agent_name(args)
    if state["stage"] not in ("SPECIFICATION", "SPEC_APPROVAL"):
        raise WorkflowError("The spec review is recorded in SPECIFICATION or SPEC_APPROVAL.")
    _, rules, _, _ = spec_rules_and_template(repo, cfg)
    spec_file = task_dir(repo, state["id"]) / "spec.md"
    spec_hash = sha256_file(spec_file)
    doc = Doc(read_text(spec_file))
    review = state.setdefault("spec_review", {})
    if review.get("spec_sha256") != spec_hash:
        review["spec_sha256"] = spec_hash
        review["rules"] = {}
    review.setdefault("map", {})
    review.setdefault("questions", {})
    review.setdefault("dismissed", {})
    tpl, _, _, _ = spec_rules_and_template(repo, cfg)
    known_targets = {ident for items in doc.items.values() for ident, _, _, _ in items}
    known_targets.update(i for i, _ in verification_items(doc, rules, tpl))
    for item in args.map or []:
        source, _, targets = item.partition("=")
        source = source.strip()
        values = [t.strip() for t in targets.split(",") if t.strip()]
        if source not in known_targets or not values:
            raise WorkflowError(f"--map {item}: use REQ=TARGET[,TARGET…] with IDs from the spec (e.g. FR-1=AC-2,DW-3) or test:<name>.")
        for value in values:
            if not value.startswith("test:") and value not in known_targets:
                raise WorkflowError(f"--map {item}: {value} is not an ID in the spec (use AC-n, EC-n, DW-n or test:<name>).")
        review["map"][source] = values
    question_keys = {k for adv in rules.get("advisory", []) if adv.get("type") == "questions" for k in adv.get("questions", {})}
    for item in args.question or []:
        key, _, value = item.partition("=")
        key, value = key.strip(), value.strip()
        if key not in question_keys:
            raise WorkflowError(f"--question {item}: unknown question key; known keys: {', '.join(sorted(question_keys)) or 'none'}.")
        if not (value in known_targets or (value.lower().startswith("n/a:") and len(value) > 5)):
            raise WorkflowError(f"--question {item}: use {key}=EC-n, or {key}=n/a:<reason>.")
        review["questions"][key] = value
    current_flags = {f["id"]: f for f in judgment_flags(doc, rules, state)}
    for flag_id, reason in args.dismiss or []:
        flag = current_flags.get(flag_id)
        if not flag:
            raise WorkflowError(f"There is no current flag '{flag_id}'. Run spec-check to list flags.")
        if not flag["dismissable"]:
            raise WorkflowError(f"Flag '{flag_id}' cannot be dismissed; resolve it instead.")
        if len(reason.strip()) < 5:
            raise WorkflowError("Give a real reason when dismissing a flag.")
        assert_no_secrets(reason, "the dismissal reason")
        review["dismissed"][flag_id] = {"reason": reason.strip(), "agent": agent, "at": now_iso()}
    notes = {}
    for item in args.note or []:
        rule_id, _, text = item.partition("=")
        notes[rule_id.strip()] = text.strip()
    rule_defs = {r["id"]: r for r in rules.get("judgment", [])}
    remaining = {f["id"]: f for f in judgment_flags(doc, rules, state)
                 if not (f["dismissable"] and f["id"] in review["dismissed"])}
    for rule_id in args.pass_ or []:
        rule = rule_defs.get(rule_id)
        if not rule:
            raise WorkflowError(f"Unknown judgment rule '{rule_id}'. Rules: {', '.join(rule_defs) or 'none'}.")
        open_for_rule = [f["id"] for f in remaining.values() if f["rule"] == rule_id]
        if open_for_rule:
            raise WorkflowError(f"{rule_id} still has open flags: {', '.join(open_for_rule)}.")
        note = notes.get(rule_id, "")
        if rule.get("requires_note") and len(note) < 10:
            raise WorkflowError(f"{rule_id} needs --note {rule_id}=\"…\" explaining the basis (for structures: the "
                                "existing files or patterns each proposal follows).")
        assert_no_secrets(note, "the review note")
        review["rules"][rule_id] = {"status": "pass", "note": note, "agent": agent, "at": now_iso()}
    add_history(state, "spec-review", agent, spec_sha256=short(spec_hash))
    save_state(repo, state)
    print_spec_check(spec_check(repo, state, cfg))
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    repo, cfg, state = require_task(args)
    agent = agent_name(args)
    doc_name = args.document
    evidence = (args.evidence or "").strip()
    if len(evidence) < 2:
        raise WorkflowError("--evidence must quote the user's explicit approval (their own words).")
    assert_no_secrets(evidence, "the approval evidence")
    if doc_name == "spec":
        if state["stage"] != "SPEC_APPROVAL":
            raise WorkflowError(f"The spec can be approved only in SPEC_APPROVAL (current stage {state['stage']}).")
        result = spec_check(repo, state, cfg)
        if not result["ready"]:
            problems = [p["message"] for p in result["mandatory"]] + [f["message"] for f in result["flags"]]
            problems += [f"{k} not reviewed" for k, v in result["judgment"].items() if v["status"] != "pass"]
            raise WorkflowError("The spec is not ready for approval:\n" + bullet_list(problems))
    else:
        if state["stage"] != "PLAN_APPROVAL":
            raise WorkflowError(f"The plan can be approved only in PLAN_APPROVAL (current stage {state['stage']}).")
        ok, message = approval_status(repo, state, "spec")
        if not ok:
            raise WorkflowError(message)
        result = plan_check(repo, state)
        if not result["ready"]:
            raise WorkflowError("The plan is not ready for approval:\n" + bullet_list([p["message"] for p in result["mandatory"]]))
    tdir = task_dir(repo, state["id"])
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
    record = {"version": version, "sha256": digest, "snapshot": snapshot_rel, "approved_by": (args.by or "user").strip(),
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
        blockers = blocking_deps(repo, state, ("spec", "plan", "implementation"))
        if blockers:
            message = (f"Plan v{version} ({short(digest)}) approved and frozen as {snapshot_rel}, but implementation is "
                       f"blocked by {', '.join(d['id'] for d in blockers)}. Stage stays PLAN_APPROVAL.")
        else:
            add_history(state, "stage", agent, **{"from": "PLAN_APPROVAL", "to": "IMPLEMENTATION", "reason": "plan approved"})
            state["stage"] = "IMPLEMENTATION"
            state["baseline"]["implementation"] = git_baseline(repo)
            add_checkpoint(state, "implementation-start", agent, code_fingerprint(repo), {}, True)
            message = (f"Plan v{version} ({short(digest)}) approved; frozen as {snapshot_rel}. Stage: IMPLEMENTATION. "
                       "Run `preflight` before editing code.")
    save_state(repo, state)
    print(message)
    return 0


def cmd_stage(args: argparse.Namespace) -> int:
    repo, cfg, state = require_task(args)
    agent = agent_name(args)
    if args.reason:
        assert_no_secrets(args.reason, "the reason")
    transition(repo, state, cfg, args.stage.upper(), args.reason, agent)
    save_state(repo, state)
    print(f"Task '{state['id']}' is now in {state['stage']}.")
    print(f"Next: {NEXT[state['stage']]}")
    print(f"Read: {REFERENCE[state['stage']]}")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    repo, cfg, state = require_task(args)
    agent = agent_name(args)
    if state["status"] == "closed":
        raise WorkflowError(f"Task '{state['id']}' is closed ({state.get('outcome')}).")
    was = state["status"]
    state["status"] = "active"
    paused = activate(repo, state, agent, args.session)
    add_history(state, "resumed", agent, previous=was)
    save_state(repo, state)
    if paused:
        print(f"Task '{paused}' was active and is now paused.")
    print_summary(task_summary(repo, cfg, state, detailed=True))
    if state["stage"] in CODE_STAGES:
        print("Before editing any code in this session, run `workflow.py preflight` for this task.")
    return 0


def cmd_pause(args: argparse.Namespace) -> int:
    repo, _, state = require_task(args)
    if state["status"] == "closed":
        raise WorkflowError("The task is closed.")
    state["status"] = "paused"
    add_history(state, "paused", agent_name(args), reason=args.reason)
    clear_active(repo, state["id"])
    save_state(repo, state)
    print(f"Task '{state['id']}' is paused; AIDevWorkflow gates no longer apply to your edits. "
          f"Resume with `workflow.py resume {state['id']}`.")
    return 0


def scan_records(repo: Path, slug: str) -> List[str]:
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


def cmd_preflight(args: argparse.Namespace) -> int:
    repo, _, state = require_task(args)
    agent = agent_name(args)
    session = clean_session(args.session)
    problems = []
    if state["status"] == "closed":
        problems.append("The task is closed.")
    elif state["status"] == "paused":
        problems.append(f"The task is paused; run `workflow.py resume {state['id']}` first.")
    if state["stage"] not in CODE_STAGES:
        problems.append(f"The stage is {state['stage']}; code may change only in IMPLEMENTATION or FIXING.")
    for doc_name in ("spec", "plan"):
        ok, message = approval_status(repo, state, doc_name)
        if not ok:
            problems.append(message)
    for dep in blocking_deps(repo, state, ("spec", "plan", "implementation")):
        problems.append(f"{dep['id']} ({dep['summary']}) still blocks implementation.")
    problems += scan_records(repo, state["id"])
    base = state["baseline"].get("implementation")
    changes: Dict[str, str] = {}
    unattributed: List[str] = []
    if base:
        cs = change_set(repo, base, state.get("excluded", []))
        changes = cs["task"]
        last = (state.get("last_checkpoint") or {}).get("changes") or {}
        unattributed = sorted({p for p, h in changes.items() if last.get(p) != h} | {p for p in last if p not in changes})
    valid = not problems
    add_checkpoint(state, "preflight", agent, code_fingerprint(repo), changes, valid,
                   session=session, unattributed=unattributed[:50] or None)
    if valid:
        active = read_active(repo)
        if not active or active.get("task") != state["id"]:
            activate(repo, state, agent, session)
            active = read_active(repo) or {}
        active.update({"agent": agent, "session": session or active.get("session"),
                       "preflight_session": session, "preflight_at": now_iso()})
        save_json(active_path(repo), active)
    add_history(state, "preflight", agent, valid=valid)
    save_state(repo, state)
    if args.json:
        print(json.dumps({"valid": valid, "problems": problems, "unattributed": unattributed}, indent=2))
    elif valid:
        print(f"PREFLIGHT PASSED — task '{state['id']}' ({state['stage']}): approvals valid, nothing blocking. "
              "You may edit code for this task in this session.")
    else:
        print(f"PREFLIGHT FAILED — do not edit code for task '{state['id']}':\n" + bullet_list(problems))
    if unattributed:
        print("Changes since the last checkpoint that no recorded step explains (show them to the user):\n" +
              bullet_list(unattributed[:20]))
    if valid and state["stage"] == "IMPLEMENTATION" and not any(e.get("kind") == "baseline" for e in state["checks"]):
        analyzers = [c["id"] for c in load_config(repo).get("checks", []) if c.get("parser") == "dart-analyzer"]
        if analyzers and not changes:
            print(f"Capture the analyzer baseline before your first edit: `workflow.py run {state['id']} {analyzers[0]} --baseline`.")
    return 0 if valid else 1


def cmd_step(args: argparse.Namespace) -> int:
    repo, _, state = require_task(args)
    agent = agent_name(args)
    if state["stage"] not in CODE_STAGES or state["status"] != "active":
        raise WorkflowError("Steps are recorded during IMPLEMENTATION or FIXING on an active task.")
    for doc_name in ("spec", "plan"):
        ok, message = approval_status(repo, state, doc_name)
        if not ok:
            raise WorkflowError(message)
    steps = plan_steps(repo, state)
    if args.step not in steps:
        raise WorkflowError(f"{args.step} is not a step of the approved plan ({', '.join(steps)}).")
    if args.status not in ("done", "in-progress", "todo"):
        raise WorkflowError("Status must be done, in-progress or todo.")
    base = state["baseline"].get("implementation") or {}
    changes = change_set(repo, base, state.get("excluded", []))["task"] if base else {}
    last = (state.get("last_checkpoint") or {}).get("changes") or {}
    changed = sorted({p for p, h in changes.items() if last.get(p) != h} | {p for p in last if p not in changes})
    files = [f.strip() for f in (args.files or "").split(",") if f.strip()] or changed
    if args.note:
        assert_no_secrets(args.note, "the step note")
    state["progress"][args.step] = {"status": args.status, "files": files, "note": (args.note or "").strip(),
                                    "agent": agent, "at": now_iso()}
    add_checkpoint(state, "step", agent, code_fingerprint(repo), changes, True, step=args.step)
    add_history(state, "step", agent, step=args.step, status=args.status)
    save_state(repo, state)
    done = sum(1 for s in steps if state["progress"].get(s, {}).get("status") == "done")
    print(f"{args.step} marked {args.status} ({len(files)} file(s) attributed). Progress: {done}/{len(steps)} steps done.")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    repo, cfg, state = require_task(args)
    agent = agent_name(args)
    checks = {c["id"]: c for c in cfg.get("checks", [])}
    check = checks.get(args.check)
    if check is None:
        if not args.extra:
            raise WorkflowError(f"Unknown check '{args.check}'. Configured: {', '.join(checks) or 'none'}. "
                                "For an extra command use: run <task> <name> -- <command …>.")
        check = {"id": args.check, "name": args.check, "command": " ".join(shlex.quote(a) for a in args.extra),
                 "required": False}
        extra: List[str] = []
    else:
        extra = list(args.extra or [])
        if extra and not check.get("accepts_args"):
            raise WorkflowError(f"Check '{check['id']}' does not take extra arguments.")
    entry: Dict[str, Any] = {"id": check["id"], "name": check.get("name", check["id"]), "kind": "result",
                             "agent": agent, "at": now_iso(), "counts": None, "reason": None}
    if args.not_applicable:
        if check.get("required") and not check.get("when"):
            raise WorkflowError(f"'{check['id']}' is always required; if it cannot run, use --blocked \"<reason>\".")
        entry.update(status="not-applicable", summary="", reason=args.not_applicable.strip())
    elif args.blocked:
        entry.update(status="blocked", summary="", reason=args.blocked.strip())
    elif check.get("builtin"):
        status, summary, _ = builtin_check(repo, state, cfg, check)
        entry.update(status=status, summary=redact(summary)[:500], command=f"built-in {check['builtin']}")
    else:
        if args.baseline and check.get("parser") != "dart-analyzer":
            raise WorkflowError("--baseline is only for analyzer checks (parser dart-analyzer).")
        if args.baseline:
            base = state["baseline"].get("implementation")
            if not base:
                raise WorkflowError("Capture the baseline after the plan is approved (IMPLEMENTATION), before editing code.")
            if change_set(repo, base, state.get("excluded", []))["task"] and not args.force:
                raise WorkflowError("Code already changed since implementation started; a baseline now would hide new "
                                    "issues. Use --force only if the user agrees.")
        code, output, duration, error = execute(repo, check["command"], extra, int(check.get("timeout_s", 1800)))
        command_text = redact(" ".join([check["command"], *extra]))
        entry.update(command=command_text, duration_s=round(duration, 1), exit_code=code)
        if error:
            entry.update(status="blocked", summary="", reason=f"Could not run: {error}.")
        else:
            tail = output.splitlines()[-120:]
            if tail:
                print("\n".join(redact(line) for line in tail))
            if check.get("parser") == "dart-analyzer":
                issues, counts = parse_analyzer(output)
                entry["counts"] = counts
                if args.baseline:
                    state["baseline"].setdefault("analyzer", {})[check["id"]] = sorted({analyzer_key(i) for i in issues})
                    entry.update(kind="baseline", status="baseline",
                                 summary=f"{counts['error']} errors, {counts['warning']} warnings, {counts['info']} infos")
                else:
                    recognized = bool(issues) or "no issues found" in output.lower()
                    baseline_keys = state["baseline"].get("analyzer", {}).get(check["id"])
                    has_baseline = baseline_keys is not None
                    baseline_set = set(baseline_keys or [])
                    fail_on = check.get("fail_on", ["error", "warning"])
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
    entry["fingerprint"] = code_fingerprint(repo)
    state["checks"].append(entry)
    del state["checks"][:-200]
    add_history(state, "check", agent, check=check["id"], status=entry["status"])
    regenerate_check_block(repo, state)
    save_state(repo, state)
    shown = entry.get("summary") or entry.get("reason") or ""
    print(f"Check '{check['id']}': {entry['status']}{' — ' + shown if shown else ''} (code {short(entry['fingerprint'], 10)})")
    recorded_on_purpose = bool(args.blocked or args.not_applicable)
    return 0 if recorded_on_purpose or entry["status"] in ("passed", "preexisting", "baseline") else 1


def cmd_scope(args: argparse.Namespace) -> int:
    repo, _, state = require_task(args)
    agent = agent_name(args)
    if args.exclude:
        if not args.reason:
            raise WorkflowError("Excluding a file from the task scope needs --reason (e.g. the user confirmed it is unrelated).")
        assert_no_secrets(args.reason, "the reason")
        for rel in args.exclude:
            if rel not in state["excluded"]:
                state["excluded"].append(rel)
        add_history(state, "scope-exclude", agent, files=args.exclude, reason=args.reason)
        save_state(repo, state)
    base = state["baseline"].get("implementation") or state["baseline"].get("start") or {}
    cs = change_set(repo, base, state.get("excluded", []))
    attributed = {f for p in state["progress"].values() for f in p.get("files", [])}
    result = {
        "baseline": "implementation" if state["baseline"].get("implementation") else "task start",
        "task_changes": sorted(cs["task"]), "unattributed": sorted(p for p in cs["task"] if p not in attributed),
        "preexisting_modified": cs["preexisting_modified"], "preexisting_untouched": cs["preexisting_untouched"],
        "excluded": cs["excluded"], "notes": cs["notes"],
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print(f"Scope of task '{state['id']}' since the {result['baseline']} baseline:")
    print(f"Task changes ({len(result['task_changes'])}):" + ("\n" + bullet_list(result["task_changes"]) if result["task_changes"] else " none"))
    if state["baseline"].get("implementation"):
        print(f"Not attributed to any step ({len(result['unattributed'])}):" +
              ("\n" + bullet_list(result["unattributed"]) if result["unattributed"] else " none"))
    if result["preexisting_modified"]:
        print("Files that already had uncommitted changes and were modified during the task (check you preserved "
              "the earlier work):\n" + bullet_list(result["preexisting_modified"]))
    if result["preexisting_untouched"]:
        print(f"Pre-existing uncommitted changes left untouched: {len(result['preexisting_untouched'])}")
    if result["excluded"]:
        print("Excluded as unrelated:\n" + bullet_list(result["excluded"]))
    for note in result["notes"]:
        print(f"Note: {note}")
    return 0


def cmd_decision(args: argparse.Namespace) -> int:
    repo, _, state = require_task(args)
    text, evidence = (args.text or "").strip(), (args.evidence or "").strip()
    if not text or not evidence:
        raise WorkflowError("A decision needs --text and --evidence (the user's own words).")
    assert_no_secrets(text + "\n" + evidence, "the decision")
    state["decisions"].append({"text": text, "evidence": evidence, "by": (args.by or "user").strip(),
                               "recorded_by": agent_name(args), "at": now_iso()})
    add_history(state, "decision", agent_name(args))
    save_state(repo, state)
    print(f"Decision recorded ({len(state['decisions'])} in total).")
    return 0


def validate_task(repo: Path, cfg: Dict[str, Any], state: Dict[str, Any]) -> Tuple[List[str], List[str]]:
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
        result = spec_check(repo, state, cfg)
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


def cmd_check(args: argparse.Namespace) -> int:
    repo = find_repo(args.repo)
    cfg = load_config(repo)
    errors: List[str] = []
    warnings: List[str] = []
    for name in ("config.json", "PROJECT.md"):
        path = records_dir(repo) / name
        if path.exists():
            errors += [f"{name}:{line} looks like it contains a {kind}." for kind, line in find_secrets(read_text(path))]
    template_path(repo, cfg)
    load_rules(repo, cfg)
    slugs = [args.task] if args.task else list_tasks(repo)
    for slug in slugs:
        state = load_state(repo, slug)
        task_errors, task_warnings = validate_task(repo, cfg, state)
        errors += [f"{slug}: {e}" for e in task_errors]
        warnings += [f"{slug}: {w}" for w in task_warnings]
    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors, "warnings": warnings}, indent=2))
    else:
        for error in errors:
            print(f"ERROR   {error}")
        for warning in warnings:
            print(f"WARNING {warning}")
        print("OK — records are consistent." if not errors else f"{len(errors)} error(s).")
    return 0 if not errors else 1


def cmd_outcome(args: argparse.Namespace) -> int:
    repo, cfg, state = require_task(args)
    result = compute_outcome(repo, state, cfg)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    print(f"Highest status the evidence allows: {result['max']}" + (" (or Blocked)" if result["blocked"] else ""))
    print("Allowed in report.md: " + ", ".join(result["allowed"]))
    if result["reasons"]:
        print("Why not higher:\n" + bullet_list(result["reasons"]))
    return 0


def cmd_close(args: argparse.Namespace) -> int:
    repo, cfg, state = require_task(args)
    agent = agent_name(args)
    if state["status"] == "closed":
        raise WorkflowError("The task is already closed.")
    if state["stage"] != "FINAL_REPORT":
        raise WorkflowError(f"Close the task from FINAL_REPORT (current stage {state['stage']}).")
    report = parse_report(repo, state["id"])
    if report["problems"]:
        raise WorkflowError("report.md is not complete:\n" + bullet_list(report["problems"]))
    result = compute_outcome(repo, state, cfg)
    claimed = report["status"]
    if claimed not in result["allowed"]:
        raise WorkflowError(f"report.md says '{claimed}', but the evidence allows at most '{result['max']}'"
                            + (" (or Blocked)" if result["blocked"] else "") + ":\n" + bullet_list(result["reasons"]))
    state["status"] = "closed"
    state["outcome"] = claimed
    state["closed_at"] = now_iso()
    add_history(state, "closed", agent, outcome=claimed)
    clear_active(repo, state["id"])
    save_state(repo, state)
    print(f"Task '{state['id']}' closed as {claimed}. AIDevWorkflow gates no longer apply to your edits.")
    return 0
