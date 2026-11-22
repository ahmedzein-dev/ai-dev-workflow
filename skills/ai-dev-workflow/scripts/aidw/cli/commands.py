"""The CLI commands: each one calls the engine API (aidw.api), prints the result and returns the exit code.

Nothing here writes records. `resolve_template`, `update_setup` and `ensure_commit_mode` are thin compatibility
wrappers that keep the signatures `workflow` has always exported.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from aidw import api
from aidw.cli.helpers import print_summary, require_task
from aidw.constants import RECORDS
from aidw.infra.gitutil import find_repo
from aidw.infra.text import agent_name, bullet_list, short
from aidw.store.config import load_config


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
    """Compatibility wrapper (old signature) around `aidw.api.resolve_template`."""
    return api.resolve_template(template=args.template, rules=getattr(args, "rules", None),
                                no_rules=getattr(args, "no_rules", False))


def ensure_commit_mode(repo: Path, cfg: Dict[str, Any]) -> None:
    """Compatibility wrapper (old behaviour: prints) around `aidw.api.apply_clone_commit_mode`."""
    message = api.apply_clone_commit_mode(repo=repo, cfg=cfg)["message"]
    if message:
        print(message)


def repo_arg(args: argparse.Namespace) -> str:
    """The CLI's repository default: --repo, else the current directory (the API never assumes one)."""
    return args.repo or os.getcwd()


def cmd_init(args: argparse.Namespace) -> int:
    if args.discover:
        report = api.discover_setup(repo=repo_arg(args))
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print_discovery(report)
        return 0
    if args.update:
        return update_setup(find_repo(repo_arg(args)), args)
    result = api.init_project(repo=repo_arg(args), template=args.template, commit=args.commit, agent=agent_name(args),
                              rules=args.rules, no_rules=args.no_rules, standards=args.standards, config=args.config,
                              project=args.project, project_notes=args.project_notes,
                              without_check=args.without_check or (), add_check=args.add_check or ())
    print(f"AIDevWorkflow is set up in {RECORDS}/ (template: {result['source_label']}, rules: "
          f"{'yes' if result['has_rules'] else 'none'}, records.commit={result['commit']}, checks: "
          f"{', '.join(result['checks']) or 'none'}).")
    if result["commit"] != "all":
        print(f"Local git exclude rules were written to {result['exclude']} (no tracked files changed).")
    print("These settings are reused for every task in this project.")
    return 0


def update_setup(repo: Path, args: argparse.Namespace) -> int:
    """Compatibility wrapper (old signature) around `aidw.api.update_setup`; prints the result.

    Like the old function, `repo` must be the repository root: the setup is read from it before anything else, so a
    path that is not a set-up root is refused with the same message as before.
    """
    load_config(Path(repo))
    result = api.update_setup(repo=repo, agent=agent_name(args), commit=args.commit, standards=args.standards,
                              template=args.template, rules=getattr(args, "rules", None),
                              no_rules=getattr(args, "no_rules", False),
                              without_check=getattr(args, "without_check", None) or (),
                              add_check=getattr(args, "add_check", None) or ())
    print("Updated the AIDevWorkflow settings: " + ", ".join(result["changed"]) + ".")
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    try:
        result = api.new_task(repo=repo_arg(args), task=args.task, title=args.title, task_type=args.type,
                              invocation=args.invocation, agent=agent_name(args), session=args.session)
    except BaseException as exc:
        for notice in getattr(exc, "notices", ()):
            print(notice)
        raise
    if result["commit_mode_message"]:
        print(result["commit_mode_message"])
    print(f"Created task '{result['task']}' in {RECORDS}/tasks/{result['task']}/ (stage DISCOVERY).")
    if result["paused"]:
        print(f"Task '{result['paused']}' was active and is now paused.")
    if result["preexisting"]:
        print(f"{result['preexisting']} file(s) already had uncommitted changes; they are recorded as pre-existing and must be preserved.")
    print(f"Next: {result['next']}")
    print(f"Read: {result['read']}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    result = api.status(repo=repo_arg(args), task=args.task)
    if result.get("setup") is False:
        print(json.dumps(result) if args.json else result["message"])
        return 0
    if args.task:
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print_summary(result)
        return 0
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    if not result["tasks"]:
        print("No AIDevWorkflow tasks yet.")
        return 0
    for info in result["tasks"]:
        marker = "*" if result["active"] and result["active"] == info["task"] else " "
        print(f"{marker} {info['task']:<32} {info['status_line']:<48} {info.get('title') or ''}")
    print("(* = active in this checkout)  Details: workflow.py status <task>")
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    result = api.record_discovery(repo=repo_arg(args), task=args.task, agent=agent_name(args),
                                  inspected=args.inspected or (), summary=args.summary)
    print(f"Recorded {result['inspected']} inspected path(s); summary {'set' if result['summary_set'] else 'not set'}.")
    if result["missing"]:
        print("Note: these paths do not exist in the repository: " + ", ".join(result["missing"]))
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


def task_id(args: argparse.Namespace) -> str:
    """The id recorded in the task's state (printed by some commands), read without writing anything."""
    return require_task(args)[2]["id"]


def cmd_spec_check(args: argparse.Namespace) -> int:
    result = api.spec_check(repo=repo_arg(args), task=args.task)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_spec_check(result)
    return 0 if not result["mandatory"] else 1


def cmd_plan_check(args: argparse.Namespace) -> int:
    result = api.plan_check(repo=repo_arg(args), task=args.task)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["ready"] else 1
    print(f"Plan check for '{task_id(args)}' — plan {short(result['plan_sha256'])}, steps: {', '.join(result['steps']) or 'none'}")
    print(f"Mandatory: {len(result['mandatory'])}")
    for item in result["mandatory"]:
        print(f"  - [{item['rule']}]{' line ' + str(item['line']) if item['line'] else ''}: {item['message']}")
    print(f"Advisory: {len(result['advisory'])}")
    for item in result["advisory"]:
        print(f"  - {item['message']}")
    print("Ready for approval: " + ("yes" if result["ready"] else "no"))
    return 0 if result["ready"] else 1


def cmd_review(args: argparse.Namespace) -> int:
    result = api.review(repo=repo_arg(args), task=args.task, agent=agent_name(args), maps=args.map or (),
                        questions=args.question or (), dismiss=args.dismiss or (), notes=args.note or (),
                        passes=args.pass_ or ())
    print_spec_check(result["spec_check"])
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    result = api.approve(repo=repo_arg(args), task=args.task, document=args.document, evidence=args.evidence,
                         agent=agent_name(args), by=args.by)
    print(result["message"])
    return 0


def cmd_stage(args: argparse.Namespace) -> int:
    result = api.stage(repo=repo_arg(args), task=args.task, stage=args.stage, agent=agent_name(args), reason=args.reason)
    print(f"Task '{result['task']}' is now in {result['stage']}.")
    print(f"Next: {result['next']}")
    print(f"Read: {result['read']}")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    result = api.resume(repo=repo_arg(args), task=args.task, agent=agent_name(args), session=args.session)
    if result["paused"]:
        print(f"Task '{result['paused']}' was active and is now paused.")
    print_summary(result["summary"])
    if result["code_stage"]:
        print("Before editing any code in this session, run `workflow.py preflight` for this task.")
    return 0


def cmd_pause(args: argparse.Namespace) -> int:
    result = api.pause(repo=repo_arg(args), task=args.task, agent=agent_name(args), reason=args.reason)
    print(f"Task '{result['task']}' is paused; AIDevWorkflow gates no longer apply to your edits. "
          f"Resume with `workflow.py resume {result['task']}`.")
    return 0


def cmd_preflight(args: argparse.Namespace) -> int:
    result = api.preflight(repo=repo_arg(args), task=args.task, agent=agent_name(args), session=args.session)
    valid, unattributed = result["valid"], result["unattributed"]
    if args.json:
        print(json.dumps({"valid": valid, "problems": result["problems"], "unattributed": unattributed}, indent=2))
    elif valid:
        print(f"PREFLIGHT PASSED — task '{result['task']}' ({result['stage']}): approvals valid, nothing blocking. "
              "You may edit code for this task in this session.")
    else:
        print(f"PREFLIGHT FAILED — do not edit code for task '{result['task']}':\n" + bullet_list(result["problems"]))
    # Printed after the JSON object too, as before F1.0.4 (TD-24: kept unchanged until a separately approved fix).
    if unattributed:
        print("Changes since the last checkpoint that no recorded step explains (show them to the user):\n" +
              bullet_list(unattributed[:20]))
    if result["analyzer_hint"]:
        print(result["analyzer_hint"])
    return 0 if valid else 1


def cmd_step(args: argparse.Namespace) -> int:
    result = api.step(repo=repo_arg(args), task=args.task, step=args.step, status=args.status, agent=agent_name(args),
                      files=args.files, note=args.note)
    print(f"{result['step']} marked {result['status']} ({len(result['files'])} file(s) attributed). "
          f"Progress: {result['done']}/{result['total']} steps done.")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    try:
        result = api.run_check(repo=repo_arg(args), task=args.task, check=args.check, agent=agent_name(args),
                               extra=args.extra or (), baseline=args.baseline, force=args.force, blocked=args.blocked,
                               not_applicable=args.not_applicable)
    except BaseException as exc:
        tail = getattr(exc, "output_tail", None)
        if tail:
            print("\n".join(tail))
        raise
    if result["output_tail"]:
        print("\n".join(result["output_tail"]))
    entry = result["entry"]
    shown = entry.get("summary") or entry.get("reason") or ""
    print(f"Check '{entry['id']}': {entry['status']}{' — ' + shown if shown else ''} (code {short(entry['fingerprint'], 10)})")
    return 0 if result["recorded_on_purpose"] or entry["status"] in ("passed", "preexisting", "baseline") else 1


def cmd_scope(args: argparse.Namespace) -> int:
    result = api.scope(repo=repo_arg(args), task=args.task, agent=agent_name(args), exclude=args.exclude or (),
                       reason=args.reason)
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print(f"Scope of task '{task_id(args)}' since the {result['baseline']} baseline:")
    print(f"Task changes ({len(result['task_changes'])}):" + ("\n" + bullet_list(result["task_changes"]) if result["task_changes"] else " none"))
    if result["baseline"] == "implementation":
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
    result = api.decision(repo=repo_arg(args), task=args.task, text=args.text, evidence=args.evidence,
                          agent=agent_name(args), by=args.by)
    print(f"Decision recorded ({result['count']} in total).")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    result = api.check_records(repo=repo_arg(args), task=args.task)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for error in result["errors"]:
            print(f"ERROR   {error}")
        for warning in result["warnings"]:
            print(f"WARNING {warning}")
        print("OK — records are consistent." if result["ok"] else f"{len(result['errors'])} error(s).")
    return 0 if result["ok"] else 1


def cmd_outcome(args: argparse.Namespace) -> int:
    result = api.outcome(repo=repo_arg(args), task=args.task)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    print(f"Highest status the evidence allows: {result['max']}" + (" (or Blocked)" if result["blocked"] else ""))
    print("Allowed in report.md: " + ", ".join(result["allowed"]))
    if result["reasons"]:
        print("Why not higher:\n" + bullet_list(result["reasons"]))
    return 0


def cmd_close(args: argparse.Namespace) -> int:
    result = api.close(repo=repo_arg(args), task=args.task, agent=agent_name(args))
    print(f"Task '{result['task']}' closed as {result['outcome']}. AIDevWorkflow gates no longer apply to your edits.")
    return 0