#!/usr/bin/env python3
"""Install, update, check and remove the ai-dev-workflow skill (AIDevWorkflow) for each supported agent.

One canonical copy lives in ~/.agents/skills/ai-dev-workflow, which Codex and Gemini CLI read directly. Claude Code
(~/.claude/skills) and Antigravity (~/.gemini/config/skills) get a symlink to it where symlinks work, or a copy that
`doctor` compares with the canonical one. A project-level install puts real copies (no symlinks) into the repository
so teammates and cloud agents get the skill from git.

Standard library only; Python 3.9 or newer. Run `install.py --help`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

SKILL_NAME = "ai-dev-workflow"
SOURCE = Path(__file__).resolve().parent.parent
MANIFEST = ".aidw-install.json"
IGNORED_NAMES = {"__pycache__", ".DS_Store", MANIFEST}
LINKED_AGENTS = ("claude", "antigravity")
ALL_AGENTS = ("claude", "codex", "gemini", "antigravity")


def home() -> Path:
    return Path.home()


def canonical_dir() -> Path:
    return home() / ".agents" / "skills" / SKILL_NAME


def user_location(agent: str) -> Path:
    if agent == "claude":
        return home() / ".claude" / "skills" / SKILL_NAME
    if agent == "antigravity":
        return home() / ".gemini" / "config" / "skills" / SKILL_NAME
    return canonical_dir()


def library_dir() -> Path:
    env = os.environ.get("AI_DEV_WORKFLOW_HOME")
    return Path(env).expanduser() if env else home() / ".ai-dev-workflow"


def skill_name_and_version(folder: Path) -> tuple:
    skill = folder / "SKILL.md"
    if not skill.is_file():
        return None, None
    text = skill.read_text(encoding="utf-8", errors="replace")
    front = text.split("---", 2)[1] if text.startswith("---") else ""
    name = re.search(r"^name:\s*['\"]?([^'\"\n]+)", front, re.M)
    version = re.search(r"^\s+version:\s*['\"]?([^'\"\n]+)", front, re.M)
    return (name.group(1).strip() if name else None), (version.group(1).strip() if version else None)


def is_ours(path: Path) -> bool:
    if path.is_symlink():
        return skill_name_and_version(path.resolve())[0] == SKILL_NAME if path.exists() else True
    return path.is_dir() and skill_name_and_version(path)[0] == SKILL_NAME


def file_hashes(folder: Path) -> Dict[str, str]:
    hashes = {}
    for path in sorted(folder.rglob("*")):
        if path.is_file() and not any(part in IGNORED_NAMES for part in path.relative_to(folder).parts) \
                and path.suffix != ".pyc":
            data = path.read_bytes().replace(b"\r\n", b"\n")
            hashes[path.relative_to(folder).as_posix()] = hashlib.sha256(data).hexdigest()
    return hashes


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def copy_skill(source: Path, target: Path, dry_run: bool) -> str:
    if target.exists() or target.is_symlink():
        if not is_ours(target):
            raise SystemExit(f"Refusing to replace {target}: it exists and is not an ai-dev-workflow install.")
        if not dry_run:
            remove_path(target)
    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, ignore=shutil.ignore_patterns(*IGNORED_NAMES, "*.pyc"))
        _, version = skill_name_and_version(target)
        manifest = {"skill": SKILL_NAME, "version": version, "mode": "copy", "files": file_hashes(target)}
        (target / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return f"copied to {target}"


def link_or_copy(target: Path, link: Path, prefer_copy: bool, dry_run: bool) -> str:
    if link.exists() or link.is_symlink():
        if link.is_symlink() and link.resolve() == target.resolve() and not prefer_copy:
            return f"already linked: {link} -> {target}"
        if not is_ours(link):
            raise SystemExit(f"Refusing to replace {link}: it exists and is not an ai-dev-workflow install.")
        if not dry_run:
            remove_path(link)
    if prefer_copy:
        return copy_skill(target, link, dry_run)
    if dry_run:
        return f"would link {link} -> {target}"
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(str(target), str(link), target_is_directory=True)
        return f"linked {link} -> {target}"
    except (OSError, NotImplementedError) as exc:
        result = copy_skill(target, link, dry_run)
        return f"{result} (symlink not available: {exc.__class__.__name__})"


def detect_agents() -> List[str]:
    agents = ["codex", "gemini"]
    if (home() / ".claude").exists() or shutil.which("claude"):
        agents.append("claude")
    if (home() / ".gemini" / "config").exists() or Path("/Applications/Antigravity.app").exists():
        agents.append("antigravity")
    return agents


def parse_agents(value: Optional[str]) -> List[str]:
    if not value or value == "auto":
        return detect_agents()
    if value == "all":
        return list(ALL_AGENTS)
    agents = [a.strip() for a in value.split(",") if a.strip()]
    unknown = [a for a in agents if a not in ALL_AGENTS]
    if unknown:
        raise SystemExit(f"Unknown agent(s): {', '.join(unknown)}. Choose from {', '.join(ALL_AGENTS)}, auto or all.")
    return agents


def git_root(path: Path) -> Path:
    proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=str(path), capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"{path} is not inside a git repository.")
    return Path(proc.stdout.strip()).resolve()


INVOCATION_HELP = """How to start it:
  Claude Code      /ai-dev-workflow <request or task>
  Codex            $ai-dev-workflow <request or task>   (or pick it in /skills)
  Gemini CLI       /ai-dev-workflow <request or task>   (see docs/compatibility.md for the verified method)
  Antigravity      /ai-dev-workflow <request or task>
Run `install.py doctor` to check every installed copy."""


def cmd_install(args: argparse.Namespace) -> int:
    agents = parse_agents(args.agents)
    actions: List[str] = []
    if args.project:
        repo = git_root(Path(args.project).expanduser().resolve())
        agents_copy = repo / ".agents" / "skills" / SKILL_NAME
        actions.append(".agents/skills (Codex, Gemini CLI, Antigravity): " + copy_skill(SOURCE, agents_copy, args.dry_run))
        if "claude" in agents or args.agents in (None, "auto", "all"):
            claude_copy = repo / ".claude" / "skills" / SKILL_NAME
            if args.symlinks:
                relative = os.path.relpath(agents_copy, claude_copy.parent)
                if args.dry_run:
                    actions.append(f".claude/skills: would link -> {relative}")
                else:
                    if claude_copy.exists() or claude_copy.is_symlink():
                        if not is_ours(claude_copy):
                            raise SystemExit(f"Refusing to replace {claude_copy}.")
                        remove_path(claude_copy)
                    claude_copy.parent.mkdir(parents=True, exist_ok=True)
                    os.symlink(relative, str(claude_copy), target_is_directory=True)
                    actions.append(f".claude/skills (Claude Code): linked -> {relative}")
            else:
                actions.append(".claude/skills (Claude Code): " + copy_skill(SOURCE, claude_copy, args.dry_run))
        print(f"Project install in {repo}:")
        print("\n".join(f"  - {a}" for a in actions))
        print("Commit these folders to share the skill. Gemini CLI loads project skills only in trusted folders.")
        if canonical_dir().exists():
            print(f"Note: a user-level copy also exists ({canonical_dir()}); some agents will list the skill twice.")
        print(INVOCATION_HELP)
        return 0
    canonical = canonical_dir()
    if SOURCE.resolve() != canonical.resolve():
        if args.link_source:
            actions.append("canonical: " + link_or_copy(SOURCE, canonical, False, args.dry_run))
        else:
            actions.append("canonical (Codex, Gemini CLI): " + copy_skill(SOURCE, canonical, args.dry_run))
    else:
        actions.append(f"canonical (Codex, Gemini CLI): already at {canonical}")
    for agent in LINKED_AGENTS:
        if agent in agents:
            actions.append(f"{agent}: " + link_or_copy(canonical, user_location(agent), args.copy, args.dry_run))
    print("User-level install:" + (" (dry run)" if args.dry_run else ""))
    print("\n".join(f"  - {a}" for a in actions))
    skipped = [a for a in LINKED_AGENTS if a not in agents]
    if skipped:
        print(f"Not installed for: {', '.join(skipped)} (not detected; use --agents to include them).")
    print(INVOCATION_HELP)
    return 0


def describe(location: Path, reference: Dict[str, str], canonical: Path) -> tuple:
    if not (location.exists() or location.is_symlink()):
        return "missing", ""
    if location.is_symlink():
        if not location.exists():
            return "broken", f"symlink target {os.readlink(str(location))} is missing"
        if location.resolve() == canonical.resolve():
            return "ok", f"symlink -> {canonical}"
        return "warn", f"symlink -> {location.resolve()} (not the canonical copy)"
    if not is_ours(location):
        return "warn", "a different skill with this name"
    hashes = file_hashes(location)
    if hashes == reference:
        return "ok", "copy, identical to the canonical copy"
    changed = sorted(set(hashes) ^ set(reference) | {k for k in hashes if k in reference and hashes[k] != reference[k]})
    return "drift", "copy differs from the canonical copy: " + ", ".join(changed[:6])


def cmd_doctor(args: argparse.Namespace) -> int:
    problems = 0
    lines: List[str] = []
    if sys.version_info < (3, 9):
        lines.append(f"ERROR  Python {sys.version.split()[0]} is too old; AIDevWorkflow needs 3.9+.")
        problems += 1
    else:
        lines.append(f"ok     Python {sys.version.split()[0]}")
    if shutil.which("git"):
        lines.append("ok     git found")
    else:
        lines.append("ERROR  git not found on PATH")
        problems += 1
    if args.project:
        repo = git_root(Path(args.project).expanduser().resolve())
        agents_copy = repo / ".agents" / "skills" / SKILL_NAME
        claude_copy = repo / ".claude" / "skills" / SKILL_NAME
        if not agents_copy.exists():
            lines.append(f"ERROR  no project install at {agents_copy}")
            problems += 1
        else:
            reference = file_hashes(agents_copy)
            status, detail = describe(claude_copy, reference, agents_copy)
            lines.append(f"{'ok' if status == 'ok' else status.upper():<6} .claude/skills: {detail or status}")
            problems += status in ("drift", "broken")
            if file_hashes(SOURCE) != reference and SOURCE.resolve() != agents_copy.resolve():
                lines.append("info   the project copy differs from this package; run `install.py update --project …` to refresh it")
        if canonical_dir().exists():
            lines.append("warn   a user-level copy also exists; Codex may list the skill twice, Gemini CLI prefers the project copy")
    else:
        canonical = canonical_dir()
        if not canonical.exists():
            lines.append(f"ERROR  no canonical copy at {canonical}; run `install.py`")
            problems += 1
        else:
            name, version = skill_name_and_version(canonical)
            lines.append(f"ok     canonical copy {canonical} (version {version})")
            reference = file_hashes(canonical)
            for agent in LINKED_AGENTS:
                status, detail = describe(user_location(agent), reference, canonical)
                label = "ok" if status == "ok" else ("-" if status == "missing" else status.upper())
                lines.append(f"{label:<6} {agent}: {detail or 'not installed'}")
                problems += status in ("drift", "broken")
            if file_hashes(SOURCE) != reference and SOURCE.resolve() != canonical.resolve():
                lines.append("info   the canonical copy differs from this package; run `install.py update` to refresh it")
            duplicate = home() / ".gemini" / "skills" / SKILL_NAME
            if duplicate.exists():
                lines.append(f"warn   {duplicate} also exists; Gemini CLI reads it and ~/.agents/skills, so it will see two copies")
    print("\n".join(lines))
    print("No problems found." if not problems else f"{problems} problem(s) found.")
    return 0 if not problems else 1


def cmd_update(args: argparse.Namespace) -> int:
    if args.project:
        return cmd_install(args)
    present = [a for a in LINKED_AGENTS if user_location(a).exists() or user_location(a).is_symlink()]
    args.agents = ",".join(present) if present else "codex"
    return cmd_install(args)


def cmd_uninstall(args: argparse.Namespace) -> int:
    if args.project:
        repo = git_root(Path(args.project).expanduser().resolve())
        targets = [repo / ".claude" / "skills" / SKILL_NAME, repo / ".agents" / "skills" / SKILL_NAME]
    else:
        targets = [user_location("claude"), user_location("antigravity"), canonical_dir()]
    found = [t for t in targets if (t.exists() or t.is_symlink()) and is_ours(t)]
    if not found:
        print("Nothing to remove.")
        return 0
    if not args.yes:
        print("Would remove:\n" + "\n".join(f"  - {t}" for t in found) + "\nRe-run with --yes to remove them.")
        return 1
    for target in found:
        remove_path(target)
        print(f"Removed {target}")
    return 0


def cmd_add_template(args: argparse.Namespace) -> int:
    if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", args.name):
        raise SystemExit("Template names use lowercase letters, digits and hyphens.")
    template = Path(args.template).expanduser()
    if not template.is_file():
        raise SystemExit(f"Template not found: {template}")
    rules = Path(args.rules).expanduser() if args.rules else None
    if rules and not rules.is_file():
        raise SystemExit(f"Rules file not found: {rules}")
    if rules:
        data = json.loads(rules.read_text(encoding="utf-8"))
        if data.get("schema") != 1:
            raise SystemExit(f"{rules} is not an AIDevWorkflow rules file (schema 1).")
    target = library_dir() / "templates" / args.name
    if target.exists() and not args.force:
        raise SystemExit(f"{target} already exists; use --force to replace it.")
    target.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template, target / "template.md")
    if rules:
        shutil.copyfile(rules, target / "rules.json")
    elif (target / "rules.json").exists():
        (target / "rules.json").unlink()
    meta = {"name": args.name, "template_sha256": hashlib.sha256((target / "template.md").read_bytes()).hexdigest(),
            "has_rules": bool(rules)}
    (target / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"Template '{args.name}' saved in {target}. Projects can choose it with `workflow.py init --template user:{args.name}`.")
    return 0


def cmd_list_templates(_: argparse.Namespace) -> int:
    root = library_dir() / "templates"
    entries = sorted(p for p in root.iterdir() if (p / "template.md").exists()) if root.is_dir() else []
    if not entries:
        print(f"No templates in {root}.")
        return 0
    for entry in entries:
        print(f"user:{entry.name}  ({'with rules' if (entry / 'rules.json').exists() else 'structure only'})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="install.py", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command")

    def scope(p: argparse.ArgumentParser) -> None:
        p.add_argument("--project", metavar="REPO", help="Install into a repository instead of your home folder.")

    for name, func, help_text in (("install", cmd_install, "Install the skill (default)."),
                                  ("update", cmd_update, "Refresh existing installs from this package.")):
        p = sub.add_parser(name, help=help_text)
        scope(p)
        p.add_argument("--agents", help="claude,codex,gemini,antigravity, auto (default) or all.")
        p.add_argument("--copy", action="store_true", help="Copy instead of symlinking for Claude Code and Antigravity.")
        p.add_argument("--link-source", action="store_true", help="Point the canonical copy at this folder (for development).")
        p.add_argument("--symlinks", action="store_true", help="Project install: link .claude/skills to .agents/skills.")
        p.add_argument("--dry-run", action="store_true")
        p.set_defaults(func=func)
    p = sub.add_parser("doctor", help="Check every installed copy.")
    scope(p)
    p.set_defaults(func=cmd_doctor)
    p = sub.add_parser("uninstall", help="Remove installs made by this script.")
    scope(p)
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_uninstall)
    p = sub.add_parser("add-template", help="Add a specification template to your private library.")
    p.add_argument("name")
    p.add_argument("template")
    p.add_argument("--rules")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_add_template)
    p = sub.add_parser("list-templates", help="List your private templates.")
    p.set_defaults(func=cmd_list_templates)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0].startswith("-") and argv[0] not in ("-h", "--help"):
        argv = ["install", *argv]
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
