"""Running checks, analyzer parsing and built-in checks."""
from __future__ import annotations

import json
import locale
import os
import re
import shlex
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple
from aidw.core.gates import latest_results
from aidw.errors import WorkflowError
from aidw.infra.gitutil import change_set, file_at
from aidw.infra.secrets import redact
from aidw.infra.text import read_text, short, write_text
from aidw.store.config import task_dir


ANALYZER_RE = re.compile(
    r"^\s*(error|warning|info)\s+[•?\-]\s+(.+?)\s+[•?\-]\s+(\S+?):(\d+):(\d+)\s+[•?\-]\s+([\w.\-]+)\s*$", re.I)


def parse_analyzer(output: str) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    issues = []
    for line in output.splitlines():
        match = ANALYZER_RE.match(line)
        if match:
            severity, message, path, line_no, _, code = match.groups()
            issues.append({"severity": severity.lower(), "message": message.strip(),
                           "path": path.replace("\\", "/"), "line": int(line_no), "code": code})
    counts = {s: sum(1 for i in issues if i["severity"] == s) for s in ("error", "warning", "info")}
    return issues, counts


def analyzer_key(item: Dict[str, Any]) -> str:
    return f"{item['severity']}|{item['code']}|{item['path']}|{item['message']}"


def glob_to_regex(pattern: str) -> "re.Pattern[str]":
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile("^" + out + "$")


def glob_match(path: str, pattern: str) -> bool:
    return bool(glob_to_regex(pattern).match(path))


def decode_command_output(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode(locale.getpreferredencoding(False), errors="replace")


def execute(repo: Path, command: str, extra: Sequence[str], timeout: int) -> Tuple[Optional[int], str, float, Optional[str]]:
    try:
        tokens = shlex.split(command, posix=(os.name != "nt")) + list(extra)
    except ValueError as exc:
        return None, "", 0.0, f"the command could not be parsed: {exc}"
    if os.name == "nt":  # non-POSIX shlex keeps the quotes around tokens
        tokens = [t[1:-1] if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'" else t for t in tokens]
    if not tokens:
        return None, "", 0.0, "the command is empty"
    executable = shutil.which(tokens[0])
    if not executable:
        return None, "", 0.0, f"'{tokens[0]}' was not found on PATH"
    tokens[0] = executable
    started = time.time()
    try:
        proc = subprocess.run(tokens, cwd=str(repo), capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "", float(timeout), f"it timed out after {timeout} seconds"
    except OSError as exc:
        return None, "", 0.0, f"it could not start: {exc}"
    return proc.returncode, decode_command_output(proc.stdout or b"") + \
        decode_command_output(proc.stderr or b""), time.time() - started, None


def last_line(output: str) -> str:
    lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
    return redact(lines[-1])[:300] if lines else ""


def flatten_keys(value: Any, prefix: str = "") -> Set[str]:
    keys: Set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            nested = flatten_keys(item, name)
            keys.update(nested or {name})
    return keys


def manifest_dependencies(name: str, text: Optional[str]) -> Optional[Set[str]]:
    if text is None:
        return set()
    if name.endswith("package.json"):
        try:
            data = json.loads(text)
        except ValueError:
            return None
        found: Set[str] = set()
        for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            found.update((data.get(key) or {}).keys())
        return found
    if name.endswith("pubspec.yaml"):
        found = set()
        section = None
        for line in text.splitlines():
            top = re.match(r"^([A-Za-z_][\w]*):", line)
            if top:
                section = top.group(1)
                continue
            entry = re.match(r"^  ([A-Za-z_][\w]*):", line)
            if entry and section in ("dependencies", "dev_dependencies", "dependency_overrides"):
                found.add(entry.group(1))
        return found
    if name.endswith(".txt"):
        return {re.split(r"[<>=!~;\[ ]", ln.strip(), 1)[0].lower() for ln in text.splitlines()
                if ln.strip() and not ln.strip().startswith(("#", "-"))}
    return None


def builtin_check(repo: Path, state: Dict[str, Any], cfg: Dict[str, Any], check: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
    kind = check["builtin"]
    base = state["baseline"].get("implementation") or state["baseline"].get("start") or {}
    head = base.get("head")
    if kind == "json-key-parity":
        files = check.get("files") or []
        now, then = {}, {}
        for rel in files:
            full = repo / rel
            try:
                now[rel] = flatten_keys(json.loads(read_text(full))) if full.exists() else set()
            except ValueError:
                return "failed", f"{rel} is not valid JSON", {}
            old = file_at(repo, head, rel)
            try:
                then[rel] = flatten_keys(json.loads(old)) if old else set()
            except ValueError:
                then[rel] = set()
        union_now = set().union(*now.values()) if now else set()
        union_then = set().union(*then.values()) if then else set()
        missing_now = {rel: union_now - keys for rel, keys in now.items()}
        missing_then = {rel: union_then - keys for rel, keys in then.items()}
        new_missing = {rel: sorted(keys - missing_then.get(rel, set())) for rel, keys in missing_now.items()}
        new_missing = {rel: keys for rel, keys in new_missing.items() if keys}
        old_missing = {rel: keys for rel, keys in missing_now.items() if keys}
        if new_missing:
            listed = "; ".join(f"{rel} lacks {', '.join(keys[:8])}" for rel, keys in new_missing.items())
            return "failed", f"Missing keys: {listed}", {"missing": new_missing}
        if old_missing:
            return "preexisting", "Only key gaps that existed before the task remain.", {}
        return "passed", f"All {len(union_now)} keys present in {len(files)} files.", {}
    if kind == "rule-scan":
        rules = cfg.get("rules") or []
        changes = change_set(repo, base, state.get("excluded", []))["task"] if base else {}
        new_errors: List[str] = []
        preexisting: List[str] = []
        warnings: List[str] = []
        for rel, digest in changes.items():
            if digest == "deleted":
                continue
            applicable = [r for r in rules if any(glob_match(rel, g) for g in r.get("paths", ["**"]))
                          and not any(glob_match(rel, g) for g in r.get("exclude", []))]
            if not applicable:
                continue
            try:
                current = read_text(repo / rel)
            except OSError:
                continue
            before = file_at(repo, head, rel) or ""
            for rule in applicable:
                regex = re.compile(rule["pattern"], re.M)
                n_now, n_before = len(regex.findall(current)), len(regex.findall(before))
                limit = int(rule.get("max_per_file", 0))
                if n_now <= limit:
                    continue
                entry = f"{rel}: {rule['id']} — {rule['message']}"
                if n_now > max(n_before, limit):
                    (new_errors if rule.get("severity", "error") == "error" else warnings).append(entry)
                elif rule.get("severity", "error") == "error":
                    preexisting.append(entry)
        details = {"new": new_errors, "preexisting": preexisting, "warnings": warnings}
        if new_errors:
            return "failed", f"{len(new_errors)} new rule violation(s): " + "; ".join(new_errors[:5]), details
        summary = f"No new violations in {len(changes)} changed file(s)"
        if warnings:
            summary += f"; {len(warnings)} warning(s): " + "; ".join(warnings[:3])
        return ("preexisting" if preexisting else "passed"), summary, details
    if kind == "manifest-diff":
        added: Dict[str, List[str]] = {}
        unsupported = []
        for rel in check.get("files") or []:
            full = repo / rel
            now_text = read_text(full) if full.exists() else None
            now_deps = manifest_dependencies(rel, now_text)
            old_deps = manifest_dependencies(rel, file_at(repo, head, rel))
            if now_deps is None or old_deps is None:
                if now_text != file_at(repo, head, rel):
                    unsupported.append(rel)
                continue
            new = sorted(now_deps - old_deps)
            if new:
                added[rel] = new
        decisions = " ".join(f"{d.get('text', '')} {d.get('evidence', '')}" for d in state.get("decisions", [])).lower()
        unapproved = [n for names in added.values() for n in names if n.lower() not in decisions]
        if unapproved:
            return "failed", ("New dependencies need the user's recorded approval: " + ", ".join(unapproved) +
                              ". Record it with `decision <task> --text … --evidence …`, then re-run."), {"added": added}
        if unsupported:
            return "failed", "Changed manifests could not be compared automatically: " + ", ".join(unsupported), {}
        if added:
            return "passed", "New dependencies with recorded approval: " + ", ".join(n for v in added.values() for n in v), {}
        return "passed", "No new dependencies.", {}
    raise WorkflowError(f"Unknown built-in check '{kind}'.")


def regenerate_check_block(repo: Path, state: Dict[str, Any]) -> None:
    path = task_dir(repo, state["id"]) / "verification.md"
    if not path.exists():
        return
    latest = latest_results(state)
    lines = ["| Check | Status | Summary | Code fingerprint | When | Agent |", "|---|---|---|---|---|---|"]
    for check_id, entry in sorted(latest.items()):
        summary = (entry.get("summary") or entry.get("reason") or "").replace("|", "\\|")
        lines.append(f"| {check_id} | {entry['status']} | {summary} | `{short(entry.get('fingerprint'), 10)}` | "
                     f"{entry['at']} | {entry['agent']} |")
    baselines = [e for e in state.get("checks", []) if e.get("kind") == "baseline"]
    if baselines:
        lines.append("")
        lines.append(f"Analyzer baseline captured {baselines[-1]['at']}: {baselines[-1].get('summary', '')}")
    if not latest and not baselines:
        lines = ["_No checks recorded yet. Run `workflow.py run <task> <check>`._"]
    block = "<!-- aidw:checks:start -->\n" + "\n".join(lines) + "\n<!-- aidw:checks:end -->"
    text = read_text(path)
    pattern = re.compile(r"<!-- aidw:checks:start -->.*?<!-- aidw:checks:end -->", re.S)
    text = pattern.sub(lambda _: block, text) if pattern.search(text) else text.rstrip("\n") + "\n\n" + block + "\n"
    write_text(path, text)
