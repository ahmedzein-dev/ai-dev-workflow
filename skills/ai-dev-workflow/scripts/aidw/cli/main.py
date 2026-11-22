"""Argument parser and entry point."""
from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence
from aidw import __version__
from aidw.agents.claude_hooks import cmd_hook
from aidw.cli.commands import cmd_approve, cmd_check, cmd_close, cmd_decision, cmd_discover, cmd_init, cmd_new, cmd_outcome, cmd_pause, cmd_plan_check, cmd_preflight, cmd_resume, cmd_review, cmd_run, cmd_scope, cmd_spec_check, cmd_stage, cmd_status, cmd_step
from aidw.constants import COMMIT_MODES, STAGES, TASK_TYPES
from aidw.errors import WorkflowError


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", help="Path inside the project's git repository (default: current directory).")
    common.add_argument("--agent", help="Your agent name: claude-code, codex, gemini-cli, antigravity or other.")
    common.add_argument("--json", action="store_true", help="Machine-readable output where supported.")
    parser = argparse.ArgumentParser(
        prog="workflow.py", description="AIDevWorkflow engine for the ai-dev-workflow skill.",
        epilog="Stages: " + " → ".join(STAGES))
    parser.add_argument("--version", action="version", version=f"AIDevWorkflow {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", parents=[common], help="Set up AIDevWorkflow in a project (after asking the user).")
    p.add_argument("--discover", action="store_true",
                   help="Show the setup proposal (or the existing setup) without changing anything.")
    p.add_argument("--template", help="Template file path, or user:<name> from your private library.")
    p.add_argument("--rules", help="Template rules file (default: <template>.rules.json next to the template).")
    p.add_argument("--no-rules", action="store_true", help="Use structural checks only.")
    p.add_argument("--commit", choices=COMMIT_MODES, help="How task records are committed to git.")
    p.add_argument("--standards", help="Comma-separated engineering instruction files, e.g. CLAUDE.md,AGENTS.md.")
    p.add_argument("--config", help="JSON file with checks and rules to start from.")
    p.add_argument("--project-notes", help="Markdown file to use as .ai-dev-workflow/PROJECT.md.")
    p.add_argument("--project", help="Project name.")
    p.add_argument("--without-check", action="append", metavar="ID", help="Leave out a recommended check (repeatable).")
    p.add_argument("--add-check", action="append", metavar="ID=COMMAND", help="Add a check (repeatable).")
    p.add_argument("--update", action="store_true",
                   help="Change an existing setup: --commit, --standards, --template, --add-check, --without-check.")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("new", parents=[common], help="Create a task (only after an explicit invocation).")
    p.add_argument("task")
    p.add_argument("--title", required=True)
    p.add_argument("--type", default="feature", choices=TASK_TYPES)
    p.add_argument("--invocation", required=True, help="The user's starting message; it must name ai-dev-workflow.")
    p.add_argument("--session", help="Agent session id (Claude Code: ${CLAUDE_SESSION_ID}).")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("status", parents=[common], help="List tasks, or show one task with its next step.")
    p.add_argument("task", nargs="?")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("discover", parents=[common], help="Record inspected files and the discovery summary.")
    p.add_argument("task")
    p.add_argument("--inspected", nargs="*", help="Paths you inspected (code, standards, related features).")
    p.add_argument("--summary", help="Goal, scope, exclusions and affected areas, in a few sentences.")
    p.set_defaults(func=cmd_discover)

    p = sub.add_parser("spec-check", parents=[common], help="Validate the spec against the template and its rules.")
    p.add_argument("task")
    p.set_defaults(func=cmd_spec_check)

    p = sub.add_parser("review", parents=[common], help="Record the spec review (judgment rules, flags, coverage).")
    p.add_argument("task")
    p.add_argument("--pass", dest="pass_", action="append", metavar="RULE", help="Mark a judgment rule reviewed and satisfied.")
    p.add_argument("--note", action="append", metavar="RULE=TEXT", help="Basis for a rule, e.g. J3=\"follows lib/x\".")
    p.add_argument("--dismiss", nargs=2, action="append", metavar=("FLAG", "REASON"), help="Dismiss a flag with a reason.")
    p.add_argument("--map", action="append", metavar="REQ=TARGETS", help="Coverage, e.g. FR-1=AC-1,DW-2 or FR-2=test:<name>.")
    p.add_argument("--question", action="append", metavar="KEY=VALUE", help="Edge-case question: KEY=EC-n or KEY=n/a:<reason>.")
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("plan-check", parents=[common], help="Validate plan.md against the plan template.")
    p.add_argument("task")
    p.set_defaults(func=cmd_plan_check)

    p = sub.add_parser("approve", parents=[common], help="Record the user's explicit approval of the spec or plan.")
    p.add_argument("task")
    p.add_argument("document", choices=("spec", "plan"))
    p.add_argument("--evidence", required=True, help="The user's own words approving this version.")
    p.add_argument("--by", help="Who approved, only if the user said so (default: user).")
    p.set_defaults(func=cmd_approve)

    p = sub.add_parser("stage", parents=[common], help="Move the task to another stage (prerequisites are checked).")
    p.add_argument("task")
    p.add_argument("stage")
    p.add_argument("--reason")
    p.set_defaults(func=cmd_stage)

    p = sub.add_parser("resume", parents=[common], help="Make a task active again for this session.")
    p.add_argument("task")
    p.add_argument("--session")
    p.set_defaults(func=cmd_resume)

    p = sub.add_parser("pause", parents=[common], help="Pause a task; its gates stop applying.")
    p.add_argument("task")
    p.add_argument("--reason")
    p.set_defaults(func=cmd_pause)

    p = sub.add_parser("preflight", parents=[common], help="Revalidate state and approvals before editing code.")
    p.add_argument("task")
    p.add_argument("--session")
    p.set_defaults(func=cmd_preflight)

    p = sub.add_parser("step", parents=[common], help="Record progress on an approved plan step.")
    p.add_argument("task")
    p.add_argument("step")
    p.add_argument("status", choices=("done", "in-progress", "todo"))
    p.add_argument("--files", help="Comma-separated files (default: files changed since the last checkpoint).")
    p.add_argument("--note")
    p.set_defaults(func=cmd_step)

    p = sub.add_parser("run", parents=[common], help="Run a configured check and record the evidence.")
    p.add_argument("task")
    p.add_argument("check")
    p.add_argument("extra", nargs="*", help="After --: extra arguments, or a command for an ad-hoc check.")
    p.add_argument("--baseline", action="store_true", help="Record analyzer issues that exist before the task's changes.")
    p.add_argument("--force", action="store_true")
    p.add_argument("--blocked", metavar="REASON", help="Record that the check cannot run here, and why.")
    p.add_argument("--not-applicable", metavar="REASON", help="Record that a conditional check does not apply, and why.")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("scope", parents=[common], help="Show the task's changes vs. pre-existing work.")
    p.add_argument("task")
    p.add_argument("--exclude", nargs="*", help="Files the user confirmed are unrelated to the task.")
    p.add_argument("--reason")
    p.set_defaults(func=cmd_scope)

    p = sub.add_parser("decision", parents=[common], help="Record a user decision with their words.")
    p.add_argument("task")
    p.add_argument("--text", required=True)
    p.add_argument("--evidence", required=True)
    p.add_argument("--by")
    p.set_defaults(func=cmd_decision)

    p = sub.add_parser("check", parents=[common], help="Validate records (all tasks, or one).")
    p.add_argument("task", nargs="?")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("outcome", parents=[common], help="Highest final status the evidence allows, and why.")
    p.add_argument("task")
    p.set_defaults(func=cmd_outcome)

    p = sub.add_parser("close", parents=[common], help="Close the task with the status written in report.md.")
    p.add_argument("task")
    p.set_defaults(func=cmd_close)

    p = sub.add_parser("hook", help="Agent hook entry points (used by the skill's Claude Code hooks).")
    p.add_argument("name", choices=("claude-pre-edit", "claude-prompt"))
    p.set_defaults(func=cmd_hook)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(errors="replace")
            except (ValueError, OSError):
                pass
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "extra", None) and args.extra[:1] == ["--"]:
        args.extra = args.extra[1:]
    try:
        return int(args.func(args) or 0)
    except WorkflowError as exc:
        print(f"AIDevWorkflow: {exc}", file=sys.stderr)
        return exc.code
