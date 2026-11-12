#!/usr/bin/env python3
"""AIDevWorkflow engine for the ai-dev-workflow skill.

Structured AI-Assisted Development - From Requirements to Release.

Records task state, approvals and verification evidence for tasks the user
explicitly starts with the ai-dev-workflow skill, and refuses stage changes whose
prerequisites are not met. Standard library only; Python 3.9 or newer.

Run `workflow.py --help` or `workflow.py <command> --help` for usage.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

__version__ = "1.0.0"

SKILL_NAME = "ai-dev-workflow"
RECORDS = ".ai-dev-workflow"
SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_DIR / "assets" / "templates"

STAGES = [
    "DISCOVERY", "DEPENDENCIES", "SPECIFICATION", "SPEC_APPROVAL", "PLANNING",
    "PLAN_APPROVAL", "IMPLEMENTATION", "TESTING", "FIXING", "AUDIT", "FINAL_REPORT",
]
CODE_STAGES = ("IMPLEMENTATION", "FIXING")
TASK_TYPES = ("feature", "bugfix", "enhancement", "refactor")
OUTCOMES = ("Completed", "Completed with Limitations", "Partially Completed", "Blocked")
OUTCOME_RANK = {"Completed": 0, "Completed with Limitations": 1, "Partially Completed": 2}
COMMIT_MODES = ("all", "config-only", "none")
DEP_CLASSES = {
    "blocking": "Blocking", "non-blocking": "Non-blocking", "nonblocking": "Non-blocking",
    "verified": "Verified", "not applicable": "Not applicable", "n/a": "Not applicable",
}
DEP_GATES = ("spec", "plan", "implementation", "completion")
DEP_TYPES = ("ui", "backend", "data", "platform", "security", "third-party", "decision", "environment", "other")
VERIFY_STATUS = {"passed": "Passed", "failed": "Failed", "blocked": "Blocked", "not verified": "Not Verified"}
SEVERITIES = ("Critical", "Important", "Minor")
DISPOSITIONS = ("Open", "Fixed", "Accepted", "Deferred")
INDEPENDENCE = ("independent agent", "subagent", "separate session", "second pass")
INVOCATION_RE = re.compile(r"ai[\s_-]?dev[\s_-]?workflow", re.I)
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RECORD_FILES = ("spec.md", "dependencies.md", "plan.md", "verification.md", "audit.md", "report.md", "state.json")
PLAN_SECTIONS = (
    "Goal", "Current Behavior", "Proposed Solution", "Affected Areas", "Implementation Steps",
    "Important Technical Decisions", "Edge Cases", "Testing Plan", "Risks and Dependencies", "Expected Result",
)
PLAN_NONE_OK = ("Important Technical Decisions", "Edge Cases", "Risks and Dependencies")
REPORT_SECTIONS = (
    "Overall Status", "What Was Implemented", "Specification Compliance", "Testing Results",
    "Code Audit", "Edge Cases and Regression Risks", "Pending Dependencies", "Next Actions",
)
INSTRUCTION_CANDIDATES = (
    "CLAUDE.md", ".claude/CLAUDE.md", "AGENTS.md", "GEMINI.md", ".github/copilot-instructions.md",
    ".cursorrules", ".cursor/rules", ".windsurfrules", "CONTRIBUTING.md", "ARCHITECTURE.md", "docs/ARCHITECTURE.md",
)
DEFAULT_VAGUE_WORDS = (
    "fast", "quickly", "user-friendly", "intuitive", "properly", "appropriately", "gracefully", "seamless",
    "seamlessly", "robust", "efficient", "etc", "and so on", "as needed", "handle errors", "handles errors",
    "handle the error", "handles the error", "works correctly", "work correctly",
)

REFERENCE = {
    "DISCOVERY": "references/discovery-and-dependencies.md",
    "DEPENDENCIES": "references/discovery-and-dependencies.md",
    "SPECIFICATION": "references/specification.md",
    "SPEC_APPROVAL": "references/specification.md",
    "PLANNING": "references/planning-and-implementation.md",
    "PLAN_APPROVAL": "references/planning-and-implementation.md",
    "IMPLEMENTATION": "references/planning-and-implementation.md",
    "TESTING": "references/testing-and-fixing.md",
    "FIXING": "references/testing-and-fixing.md",
    "AUDIT": "references/audit-and-report.md",
    "FINAL_REPORT": "references/audit-and-report.md",
}
NEXT = {
    "DISCOVERY": "Inspect the relevant code, instructions and related features; ask only what the code cannot "
                 "answer; record what you inspected with `discover --inspected` and `--summary`, then move to DEPENDENCIES.",
    "DEPENDENCIES": "Classify every external input in dependencies.md; draft ready-to-send backend messages; "
                    "wait for answers that block the spec, then move to SPECIFICATION.",
    "SPECIFICATION": "Fill spec.md from the project template, run `spec-check`, fix every mandatory violation and "
                     "flag, record the review with `review`, then move to SPEC_APPROVAL.",
    "SPEC_APPROVAL": "Present the spec (version and short hash) with the spec-check summary; wait for the user's "
                     "explicit approval and record it with `approve <task> spec --evidence \"<their words>\"`.",
    "PLANNING": "Inspect the code the change touches, write plan.md from the plan template, run `plan-check`, "
                "then move to PLAN_APPROVAL.",
    "PLAN_APPROVAL": "Present the plan (version and short hash); wait for explicit approval and record it with "
                     "`approve <task> plan --evidence \"<their words>\"`.",
    "IMPLEMENTATION": "Run `preflight` in this session before editing code, implement the approved steps in order, "
                      "and mark each with `step <task> <S#> done`.",
    "TESTING": "Run every required check with `run`, fill the acceptance matrix in verification.md, then move to "
               "AUDIT (or to FIXING if anything failed).",
    "FIXING": "Run `preflight`, fix the root cause of each failure or in-scope finding, then return to TESTING "
              "and re-run the affected checks.",
    "AUDIT": "Review the actual changes (`scope`) and the evidence against the spec, plan and project standards; "
             "record findings and their dispositions in audit.md, then move to FINAL_REPORT.",
    "FINAL_REPORT": "Run `outcome`, write report.md with a status no higher than allowed, then `close` the task.",
}


class WorkflowError(Exception):
    """A refused gate or invalid input, reported to the agent; exit code 1 unless set."""

    def __init__(self, message: str, code: int = 1) -> None:
        super().__init__(message)
        self.code = code


# --------------------------------------------------------------------------- basics

def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def norm(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read_text(path: Path) -> str:
    return norm(path.read_text(encoding="utf-8", errors="replace"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(norm(text).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_text(read_text(path))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(str(tmp), str(path))


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def save_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def short(value: Optional[str], n: int = 8) -> str:
    return (value or "")[:n] or "-"


def bullet_list(items: Sequence[str]) -> str:
    return "\n".join(f"  - {item}" for item in items)


def make_readonly(path: Path) -> None:
    try:
        os.chmod(str(path), stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
    except OSError:
        pass


def clean_session(value: Optional[str]) -> Optional[str]:
    if not value or "${" in value or value.strip() in ("", "none", "null"):
        return None
    return value.strip()


def agent_name(args: argparse.Namespace) -> str:
    return (getattr(args, "agent", None) or os.environ.get("AI_DEV_WORKFLOW_AGENT") or "unknown-agent").strip()


# --------------------------------------------------------------------------- secrets

SECRET_PATTERNS: List[Tuple[str, "re.Pattern[str]"]] = [
    ("private key", re.compile(r"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}")),
    ("OpenAI API key", re.compile(r"\bsk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_\-]{32,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}")),
    ("Slack token", re.compile(r"\bxox[abposr]-[A-Za-z0-9\-]{10,}")),
    ("Stripe live key", re.compile(r"\b(?:sk|rk)_live_[0-9A-Za-z]{16,}")),
    ("JSON Web Token", re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}")),
    ("credentials in a URL", re.compile(r"\b[a-z][a-z0-9+.\-]*://[^/\s:@'\"<>]+:[^/\s@'\"<>]{3,}@")),
    ("bearer token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=\-]{24,}")),
]
ASSIGNMENT_RE = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|client[_-]?secret|api[_-]?key|access[_-]?token|auth[_-]?token|private[_-]?key)"
    r"\b[\"']?\s*[:=]\s*[\"']?([^\s\"',;)]{8,})"
)
PLACEHOLDER_VALUE_RE = re.compile(
    r"(?i)^(?:<[^>]*>|\$\{[^}]*\}|\$[A-Z_][A-Z0-9_]*|x{4,}|\*{4,}|\.{3,}|your[-_a-z]*|example[-_a-z0-9]*|changeme|"
    r"placeholder|redacted|\[redacted\]|none|null|true|false|undefined|env\(.*|process\.env.*|os\.environ.*)$"
)


def find_secrets(text: str) -> List[Tuple[str, int]]:
    """Return (kind, line number) for every likely credential in text."""
    findings: List[Tuple[str, int]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                findings.append((name, lineno))
        for match in ASSIGNMENT_RE.finditer(line):
            if not PLACEHOLDER_VALUE_RE.match(match.group(2)):
                findings.append((f"{match.group(1)} value", lineno))
    return findings


def redact(text: str) -> str:
    for _, pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)

    def _assignment(match: "re.Match[str]") -> str:
        if PLACEHOLDER_VALUE_RE.match(match.group(2)):
            return match.group(0)
        return match.group(0).replace(match.group(2), "[REDACTED]")

    return ASSIGNMENT_RE.sub(_assignment, text)


def assert_no_secrets(text: str, where: str) -> None:
    found = find_secrets(text)
    if found:
        listed = ", ".join(f"{kind} (line {line})" for kind, line in found[:5])
        raise WorkflowError(
            f"Refusing to save {where}: it looks like it contains a secret — {listed}. "
            "Task records must never hold credentials, tokens, keys or passwords; refer to them by name instead."
        )


# --------------------------------------------------------------------------- git

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
    digest = hashlib.sha256()
    for rel in sorted(blobs):
        if not is_tooling_path(rel):
            digest.update(f"{rel}\t{blobs[rel]}\n".encode("utf-8", "surrogateescape"))
    return digest.hexdigest()


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


# --------------------------------------------------------------------------- markdown

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
LABEL_RE = re.compile(r"^\s*(?:[-*+]\s+)?\*\*([^*\n]+?):\*\*\s*(.*)$")
ID_RE = re.compile(r"^([A-Z]{1,8})-?(\d+)$")
ROW_RE = re.compile(r"^\s*\|(.*)\|\s*$")
SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?\s*$")
EMPTY_CHECKBOX_RE = re.compile(r"^\s*[-*+]\s+\[ \]\s*$")
CHECKBOX_RE = re.compile(r"^\s*[-*+]\s+\[[ xX]\]\s+(\S.*)$")
HR_RE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
TOKEN_RE = re.compile(r"\[([^\[\]\n]+)\](?!\()")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
NONE_RE = re.compile(r"^\s*(?:none|n/a|not applicable)\b\.?\s*(?:[—–:\-]+\s*(.*))?$", re.I)
MARKER_RE = re.compile(r"(?<![A-Za-z])(TBD|TODO|FIXME)(?![A-Za-z])|\?\?\?")
LETTER_RE = re.compile(r"[A-Za-z0-9؀-ۿ]")


def split_row(line: str) -> List[str]:
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|") and not inner.endswith("\\|"):
        inner = inner[:-1]
    return [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", inner)]


def strip_md(text: str) -> str:
    text = re.sub(r"^[-*+]\s+(?:\[[ xX]\]\s*)?", "", text.strip())
    return text.replace("**", "").replace("`", "").strip()


class Doc:
    """Minimal Markdown model: headings, bold labels, ID items, tables; comments and code ignored."""

    def __init__(self, text: str) -> None:
        self.text = COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), norm(text))
        self.lines = self.text.split("\n")
        count = len(self.lines)
        self.code = [False] * count
        fence: Optional[str] = None
        for i, line in enumerate(self.lines):
            match = FENCE_RE.match(line)
            if fence:
                self.code[i] = True
                if match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence):
                    fence = None
            elif match:
                fence = match.group(1)
                self.code[i] = True
        self.headings: List[Tuple[int, int, str]] = []
        self.labels: List[Tuple[int, str, str]] = []
        self.items: Dict[str, List[Tuple[str, int, int, str]]] = {}
        self.tables: List[Dict[str, Any]] = []
        i = 0
        while i < count:
            line = self.lines[i]
            if self.code[i]:
                i += 1
                continue
            heading = HEADING_RE.match(line)
            if heading:
                self.headings.append((i, len(heading.group(1)), heading.group(2).strip()))
                i += 1
                continue
            if ROW_RE.match(line):
                rows: List[Tuple[int, str]] = []
                while i < count and not self.code[i] and ROW_RE.match(self.lines[i]):
                    rows.append((i, self.lines[i]))
                    i += 1
                self._add_table(rows)
                continue
            label = LABEL_RE.match(line)
            if label:
                name, rest = label.group(1).strip(), label.group(2).strip()
                ident = ID_RE.match(name)
                if ident:
                    self.items.setdefault(ident.group(1), []).append((name, int(ident.group(2)), i, rest))
                else:
                    self.labels.append((i, name, rest))
            i += 1

    def _add_table(self, rows: List[Tuple[int, str]]) -> None:
        if len(rows) < 2 or not SEP_RE.match(rows[1][1]):
            return
        data = []
        for index, raw in rows[2:]:
            cells = split_row(raw)
            data.append((index, cells))
            first = cells[0].strip().strip("*") if cells else ""
            ident = ID_RE.match(first)
            if ident:
                self.items.setdefault(ident.group(1), []).append(
                    (first, int(ident.group(2)), index, " | ".join(cells[1:])))
        self.tables.append({"line": rows[0][0], "header": split_row(rows[0][1]), "rows": data})

    def table_meta_lines(self) -> Set[int]:
        meta: Set[int] = set()
        for table in self.tables:
            meta.update((table["line"], table["line"] + 1))
        return meta

    def find_table(self, *columns: str) -> Optional[Dict[str, Any]]:
        for table in self.tables:
            header = [h.lower() for h in table["header"]]
            if all(col in header for col in columns):
                return table
        return None

    def section_range(self, prefix: str, contains: bool = False) -> Optional[Tuple[int, int, int]]:
        wanted = prefix.lower()
        for k, (line, level, text) in enumerate(self.headings):
            low = text.lower()
            if (wanted in low) if contains else low.startswith(wanted):
                end = len(self.lines)
                for nxt, nxt_level, _ in self.headings[k + 1:]:
                    if nxt_level <= level:
                        end = nxt
                        break
                return line, line + 1, end
        return None

    def label_range(self, key: str) -> Optional[Tuple[int, int, int, str]]:
        wanted = key.lower()
        for line, name, rest in self.labels:
            if name.lower().startswith(wanted):
                stops = {h[0] for h in self.headings} | {lb[0] for lb in self.labels}
                end = line + 1
                while end < len(self.lines):
                    if end in stops or (not self.code[end] and HR_RE.match(self.lines[end])):
                        break
                    end += 1
                return line, line + 1, end, rest
        return None


def clean_tokens(text: str, tokens: Set[str]) -> str:
    return TOKEN_RE.sub(lambda m: "" if (m.group(1) in tokens or not m.group(1).strip()) else m.group(0), text)


def block_entries(doc: Doc, start: int, end: int, rest: str, tokens: Set[str]) -> List[str]:
    """Meaningful entries (bullets, rows, sentences) in a block, ignoring placeholders and table headers."""
    meta = doc.table_meta_lines()
    raw_lines = ([rest] if rest else []) + [doc.lines[j] for j in range(start, end) if j not in meta]
    out: List[str] = []
    for raw in raw_lines:
        line = raw.strip()
        if not line or HR_RE.match(line) or SEP_RE.match(line) or HEADING_RE.match(line):
            continue
        if ROW_RE.match(line):
            cells = [clean_tokens(c, tokens).strip() for c in split_row(line)]
            if cells and ID_RE.match(cells[0].strip("*")):
                cells = cells[1:]
            text = " | ".join(c for c in cells if c and c not in ("-", "—"))
        else:
            text = clean_tokens(line, tokens)
            text = re.sub(r"^[-*+]\s+(?:\[[ xX]\]\s*)?", "", text)
            text = re.sub(r"^\*\*[^*\n]+:\*\*", "", text).strip()
        if LETTER_RE.search(text):
            out.append(text.strip())
    return out


def target_entries(doc: Doc, target: str, tokens: Set[str]) -> Optional[List[str]]:
    kind, _, arg = target.partition(":")
    if kind == "label":
        found = doc.label_range(arg)
        if found is None:
            return None
        _, start, end, rest = found
        return block_entries(doc, start, end, rest, tokens)
    if kind == "section":
        section = doc.section_range(arg)
        if section is None:
            return None
        _, start, end = section
        return block_entries(doc, start, end, "", tokens)
    if kind == "ids":
        return [strip_md(clean_tokens(text, tokens)) for _, _, _, text in doc.items.get(arg, [])
                if LETTER_RE.search(clean_tokens(text, tokens))]
    raise WorkflowError(f"Unknown rule target '{target}' in the template rules file.")


def target_texts(doc: Doc, target: str) -> List[Tuple[str, int, str]]:
    kind, _, arg = target.partition(":")
    if kind == "label":
        found = doc.label_range(arg)
        if found is None:
            return []
        line, start, end, rest = found
        body = [rest] + [doc.lines[j] for j in range(start, end)]
        return [(arg, line, "\n".join(body).strip())]
    if kind == "section":
        section = doc.section_range(arg)
        if section is None:
            return []
        line, start, end = section
        return [(arg, line, "\n".join(doc.lines[start:end]).strip())]
    if kind == "ids":
        return [(ident, line, text) for ident, _, line, text in doc.items.get(arg, [])]
    if kind == "table":
        prefix, _, column = arg.partition(":")
        col = int(column or 1)
        out = []
        for table in doc.tables:
            for index, cells in table["rows"]:
                first = cells[0].strip().strip("*") if cells else ""
                ident = ID_RE.match(first)
                if ident and ident.group(1) == prefix:
                    out.append((first, index, cells[col] if col < len(cells) else ""))
        return out
    raise WorkflowError(f"Unknown rule target '{target}' in the template rules file.")


def is_none_entry(entries: Sequence[str]) -> Optional[str]:
    """For a single 'None — reason' entry return the reason ('' if missing); otherwise None."""
    if len(entries) != 1:
        return None
    match = NONE_RE.match(entries[0])
    if not match:
        return None
    return (match.group(1) or "").strip()


class TemplateInfo:
    """Structure derived from a template file: headings, field labels, placeholder tokens, ID prefixes."""

    def __init__(self, text: str) -> None:
        self.doc = Doc(text)
        self.tokens: Set[str] = set()
        for i, line in enumerate(self.doc.lines):
            if self.doc.code[i]:
                continue
            for match in TOKEN_RE.finditer(INLINE_CODE_RE.sub("", line)):
                token = match.group(1)
                if token.strip() and token.strip().lower() != "x":
                    self.tokens.add(token)
        self.headings = [(level, self._heading_regex(text_), text_) for _, level, text_ in self.doc.headings]
        self.labels = [name for _, name, _ in self.doc.labels]
        self.prefixes = sorted(self.doc.items.keys())

    def _heading_regex(self, text: str) -> "re.Pattern[str]":
        pattern, pos = "", 0
        for match in TOKEN_RE.finditer(text):
            pattern += re.escape(text[pos:match.start()])
            pattern += ".+" if match.group(1) in self.tokens else re.escape(match.group(0))
            pos = match.end()
        return re.compile("^" + pattern + re.escape(text[pos:]) + "$", re.I)


def issue(rule: str, message: str, line: Optional[int] = None) -> Dict[str, Any]:
    return {"rule": rule, "message": message, "line": (line + 1) if line is not None else None}


def check_structure(doc: Doc, tpl: TemplateInfo, rule: str = "M-structure") -> List[Dict[str, Any]]:
    problems = []
    pos = 0
    for level, regex, text in tpl.headings:
        found = None
        for k in range(pos, len(doc.headings)):
            _, doc_level, doc_text = doc.headings[k]
            if doc_level == level and regex.match(doc_text):
                found = k
                break
        if found is None:
            anywhere = any(lv == level and regex.match(tx) for _, lv, tx in doc.headings)
            where = "out of order" if anywhere else "missing"
            problems.append(issue(rule, f"Template heading '{'#' * level} {text}' is {where}."))
        else:
            pos = found + 1
    present = {name.lower() for _, name, _ in doc.labels}
    for label in tpl.labels:
        if label.lower() not in present:
            problems.append(issue(rule, f"Template field '**{label}:**' is missing."))
    return problems


def check_placeholders(doc: Doc, tpl: TemplateInfo, rule: str = "M-placeholder") -> List[Dict[str, Any]]:
    problems = []
    flagged: Set[int] = set()
    for i, line in enumerate(doc.lines):
        if doc.code[i]:
            continue
        visible = INLINE_CODE_RE.sub("", line)
        for match in TOKEN_RE.finditer(visible):
            if match.group(1) in tpl.tokens:
                problems.append(issue(rule, f"Template placeholder left: [{match.group(1)}]", i))
                flagged.add(i)
        if EMPTY_CHECKBOX_RE.match(line):
            problems.append(issue(rule, "Empty checklist item left from the template.", i))
            flagged.add(i)
        elif ROW_RE.match(line) and not SEP_RE.match(line) and any(c.strip() == "[ ]" for c in split_row(line)):
            if i not in flagged:
                problems.append(issue(rule, "Empty table cell '[ ]' left from the template.", i))
            flagged.add(i)
    for items in doc.items.values():
        for ident, _, line, text in items:
            if line not in flagged and not LETTER_RE.search(clean_tokens(text, tpl.tokens)):
                problems.append(issue(rule, f"{ident} has no content.", line))
    return problems


def check_markers(doc: Doc) -> List[Dict[str, Any]]:
    problems = []
    for i, line in enumerate(doc.lines):
        if not doc.code[i] and MARKER_RE.search(INLINE_CODE_RE.sub("", line)):
            problems.append(issue("M-unresolved", "Unresolved marker (TBD, TODO, FIXME or ???) left in the document.", i))
    return problems


def check_ids(doc: Doc, prefixes: Sequence[str], rule: str = "M-ids") -> List[Dict[str, Any]]:
    problems = []
    for prefix in prefixes:
        items = doc.items.get(prefix, [])
        numbers = [n for _, n, _, _ in items]
        seen: Set[int] = set()
        for ident, number, line, _ in items:
            if number in seen:
                problems.append(issue(rule, f"{ident} is used more than once.", line))
            seen.add(number)
        if sorted(seen) != list(range(1, len(seen) + 1)):
            found = ", ".join(f"{prefix}-{n}" for n in sorted(seen))
            problems.append(issue(rule, f"{prefix} IDs must start at {prefix}-1 and have no gaps (found {found})."))
        elif numbers != sorted(numbers):
            problems.append(issue(rule, f"{prefix} IDs are out of order."))
    return problems


# --------------------------------------------------------------------------- project config

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


# --------------------------------------------------------------------------- task state

def state_path(repo: Path, slug: str) -> Path:
    return task_dir(repo, slug) / "state.json"


def load_state(repo: Path, slug: str) -> Dict[str, Any]:
    path = state_path(repo, slug)
    if not path.exists():
        raise WorkflowError(f"There is no task named '{slug}'. Run `workflow.py status` to list tasks.")
    try:
        state = load_json(path)
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"{path} is not valid JSON ({exc}). It is managed by workflow.py; restore it from git.") from exc
    problems = []
    for key, kind in (("id", str), ("stage", str), ("status", str), ("approvals", dict), ("history", list)):
        if not isinstance(state.get(key), kind):
            problems.append(f"'{key}' is missing or has the wrong type")
    if state.get("stage") not in STAGES:
        problems.append(f"unknown stage {state.get('stage')!r}")
    if state.get("status") not in ("active", "paused", "closed"):
        problems.append(f"unknown status {state.get('status')!r}")
    if problems:
        raise WorkflowError(f"{path} is inconsistent: {'; '.join(problems)}.")
    state.setdefault("baseline", {})
    state.setdefault("progress", {})
    state.setdefault("checks", [])
    state.setdefault("checkpoints", [])
    state.setdefault("decisions", [])
    state.setdefault("excluded", [])
    return state


def save_state(repo: Path, state: Dict[str, Any]) -> None:
    state["updated_at"] = now_iso()
    assert_no_secrets(json.dumps(state, ensure_ascii=False, indent=1), "state.json")
    save_json(state_path(repo, state["id"]), state)


def add_history(state: Dict[str, Any], event: str, agent: str, **details: Any) -> None:
    entry = {"at": now_iso(), "event": event, "agent": agent}
    entry.update({k: v for k, v in details.items() if v is not None})
    state["history"].append(entry)


def add_checkpoint(state: Dict[str, Any], kind: str, agent: str, fingerprint: str,
                   changes: Dict[str, str], valid: bool, **extra: Any) -> None:
    entry = {"at": now_iso(), "kind": kind, "agent": agent, "fingerprint": fingerprint,
             "valid": valid, "changed_files": len(changes)}
    entry.update({k: v for k, v in extra.items() if v is not None})
    state["checkpoints"].append(entry)
    del state["checkpoints"][:-60]
    state["last_checkpoint"] = {"at": entry["at"], "fingerprint": fingerprint, "changes": changes}


def list_tasks(repo: Path) -> List[str]:
    root = records_dir(repo) / "tasks"
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if (p / "state.json").exists())


def active_path(repo: Path) -> Path:
    return records_dir(repo) / "ACTIVE"


def read_active(repo: Path) -> Optional[Dict[str, Any]]:
    path = active_path(repo)
    if not path.exists():
        return None
    try:
        data = load_json(path)
        return data if isinstance(data, dict) and data.get("task") else None
    except (OSError, ValueError):
        return None


def clear_active(repo: Path, slug: Optional[str] = None) -> None:
    current = read_active(repo)
    if current and (slug is None or current.get("task") == slug):
        active_path(repo).unlink()


def activate(repo: Path, state: Dict[str, Any], agent: str, session: Optional[str]) -> Optional[str]:
    """Make this task the one the session works on; pause a different active task. Returns its slug if paused."""
    paused = None
    current = read_active(repo)
    if current and current.get("task") != state["id"]:
        try:
            other = load_state(repo, current["task"])
            if other["status"] == "active":
                other["status"] = "paused"
                add_history(other, "paused", agent, reason=f"task {state['id']} became active")
                save_state(repo, other)
                paused = other["id"]
        except WorkflowError:
            pass
    save_json(active_path(repo), {
        "task": state["id"], "agent": agent, "session": clean_session(session),
        "since": now_iso(), "preflight_session": None, "preflight_at": None,
    })
    return paused


# --------------------------------------------------------------------------- specification checks

def spec_rules_and_template(repo: Path, cfg: Dict[str, Any]) -> Tuple[TemplateInfo, Dict[str, Any], str, Optional[str]]:
    path = template_path(repo, cfg)
    rules, rules_rel = load_rules(repo, cfg)
    return TemplateInfo(read_text(path)), rules, cfg["spec_template"], rules_rel


def judgment_flags(doc: Doc, rules: Dict[str, Any], state: Dict[str, Any]) -> List[Dict[str, Any]]:
    flags: List[Dict[str, Any]] = []
    vague = rules.get("vague_words") or list(DEFAULT_VAGUE_WORDS)
    mapping = (state.get("spec_review") or {}).get("map") or {}
    for rule in rules.get("judgment", []):
        for detector in rule.get("detectors", []):
            kind = detector.get("type")
            if kind == "vague-words":
                words = detector.get("words") or vague
                for name, line, text in target_texts(doc, detector["target"]):
                    low = strip_md(text).lower()
                    for word in words:
                        if re.search(r"(?<![a-z0-9])" + re.escape(word.lower()) + r"(?![a-z0-9])", low):
                            flags.append({
                                "id": f"{rule['id']}:{name}:{word}", "rule": rule["id"], "dismissable": True,
                                "line": line + 1,
                                "message": f"{name} uses vague wording \"{word}\" ({rule['rule']}).",
                            })
            elif kind == "inspected-files":
                if not (state.get("discovery") or {}).get("inspected"):
                    flags.append({
                        "id": f"{rule['id']}:no-inspection", "rule": rule["id"], "dismissable": False, "line": None,
                        "message": "No inspected files are recorded. Inspect the project and record it with "
                                   "`discover <task> --inspected <paths>` before proposing structures.",
                    })
            elif kind == "coverage-map":
                prefix = detector.get("of", "FR")
                for ident, _, line, _ in doc.items.get(prefix, []):
                    if not mapping.get(ident):
                        flags.append({
                            "id": f"{rule['id']}:{ident}:unmapped", "rule": rule["id"], "dismissable": False,
                            "line": line + 1,
                            "message": f"{ident} is not mapped to an acceptance criterion, edge case, checklist item "
                                       f"or named test. Record it with `review <task> --map {ident}=AC-1`.",
                        })
            else:
                raise WorkflowError(f"Unknown judgment detector '{kind}' in the template rules file.")
    return flags


def advisory_warnings(doc: Doc, rules: Dict[str, Any], tokens: Set[str],
                      state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[str]]:
    warnings: List[Dict[str, Any]] = []
    prompts: List[str] = []
    answered = (state.get("spec_review") or {}).get("questions") or {}
    for adv in rules.get("advisory", []):
        kind = adv.get("type")
        if kind == "questions":
            for key, text in adv.get("questions", {}).items():
                if key not in answered:
                    warnings.append(issue(adv["id"], f"Not yet considered: {text}. Record `review <task> --question "
                                                      f"{key}=EC-n` or `--question {key}=n/a:<reason>`."))
        elif kind == "label-mentions":
            entries = target_entries(doc, adv["target"], tokens) or []
            joined = " ".join(entries).lower()
            if entries and not any(word.lower() in joined for word in adv.get("words", [])):
                warnings.append(issue(adv["id"], adv["message"]))
        elif kind == "none-entry":
            entries = target_entries(doc, adv["target"], tokens) or []
            if is_none_entry(entries) is not None:
                warnings.append(issue(adv["id"], adv["message"]))
        elif kind == "prompts":
            prompts.extend(adv.get("prompts", []))
        else:
            raise WorkflowError(f"Unknown advisory type '{kind}' in the template rules file.")
    return warnings, prompts


def checklist_items(doc: Doc, label: Optional[str]) -> List[str]:
    if not label:
        return []
    found = doc.label_range(label)
    if not found:
        return []
    _, start, end, _ = found
    return [m.group(1).strip() for m in (CHECKBOX_RE.match(doc.lines[j]) for j in range(start, end)) if m]


def verification_items(doc: Doc, rules: Dict[str, Any], tpl: TemplateInfo) -> List[Tuple[str, str]]:
    """Items the acceptance matrix must cover: IDs (AC, EC, …) plus checklist entries numbered DW-n."""
    spec = rules.get("verification") or {}
    prefixes = spec.get("ids")
    if prefixes is None:
        prefixes = [p for p in tpl.prefixes if p not in ("FR", "REQ", "R", "NFR")]
    label = spec.get("checklist_label")
    if label is None:
        label = next((lb for lb in tpl.labels if lb.lower().startswith(("done when", "definition of done"))), None)
    items = [(ident, text) for prefix in prefixes for ident, _, _, text in doc.items.get(prefix, [])]
    checklist_prefix = spec.get("checklist_prefix", "DW")
    items += [(f"{checklist_prefix}-{n}", text) for n, text in enumerate(checklist_items(doc, label), 1)]
    return items


def spec_check(repo: Path, state: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    tpl, rules, tpl_rel, rules_rel = spec_rules_and_template(repo, cfg)
    spec_file = task_dir(repo, state["id"]) / "spec.md"
    doc = Doc(read_text(spec_file))
    tokens = tpl.tokens
    prefixes = rules.get("id_prefixes") or tpl.prefixes
    mandatory = check_structure(doc, tpl) + check_placeholders(doc, tpl) + check_markers(doc) + check_ids(doc, prefixes)
    for rule in rules.get("patterns", []):
        regex = re.compile(rule["regex"], re.I | re.S)
        for name, line, text in target_texts(doc, rule["target"]):
            cleaned = strip_md(clean_tokens(text, tokens))
            if cleaned and not regex.search(cleaned):
                mandatory.append(issue(rule["id"], f"{name}: {rule['message']}", line))
    for rule in rules.get("tables", []):
        for table in doc.tables:
            for index, cells in table["rows"]:
                first = cells[0].strip().strip("*") if cells else ""
                ident = ID_RE.match(first)
                if ident and ident.group(1) == rule["id_prefix"]:
                    rest = [clean_tokens(c, tokens).strip() for c in cells[1:]]
                    if len(rest) < len(table["header"]) - 1 or any(not c or c in ("-", "—") for c in rest):
                        mandatory.append(issue(rule["id"], f"{first}: {rule['message']}", index))
    for rule in rules.get("content_required", []):
        entries = target_entries(doc, rule["target"], tokens)
        kind, _, name = rule["target"].partition(":")
        if kind == "ids":
            name = f"{name}-n items"
        if entries is None:
            continue
        reason = is_none_entry(entries)
        if not entries:
            hint = " Write the entries, or 'None — <reason>'." if rule.get("allow_none") else ""
            mandatory.append(issue("M-content", f"'{name}' has no content.{hint}"))
        elif reason is not None and not rule.get("allow_none"):
            mandatory.append(issue("M-content", f"'{name}' must describe real content; it cannot be None."))
        elif reason == "":
            mandatory.append(issue("M-content", f"'{name}' says None without a reason; write 'None — <reason>'."))
    for dep in blocking_deps(repo, state, ("spec",)):
        mandatory.append(issue("M-dependency", f"{dep['id']} ({dep['summary']}) still blocks the spec — owner: {dep['owner'] or 'unassigned'}."))
    spec_hash = sha256_file(spec_file)
    review = state.get("spec_review") or {}
    current = review if review.get("spec_sha256") == spec_hash else {}
    dismissed = review.get("dismissed") or {}
    flags = [f for f in judgment_flags(doc, rules, state) if not (f["dismissable"] and f["id"] in dismissed)]
    judgment = {}
    for rule in rules.get("judgment", []):
        recorded = (current.get("rules") or {}).get(rule["id"], {})
        judgment[rule["id"]] = {"rule": rule["rule"], "source": rule.get("source", ""),
                                "status": recorded.get("status", "pending"), "note": recorded.get("note", "")}
    warnings, prompts = advisory_warnings(doc, rules, tokens, state)
    template_changed = bool(state.get("template", {}).get("sha256")) and \
        state["template"]["sha256"] != sha256_file(template_path(repo, cfg))
    return {
        "task": state["id"], "spec_sha256": spec_hash, "template": tpl_rel, "rules": rules_rel,
        "mandatory": mandatory, "flags": flags, "judgment": judgment, "advisory": warnings, "prompts": prompts,
        "ids": {p: [ident for ident, _, _, _ in doc.items.get(p, [])] for p in prefixes},
        "verification_items": [i for i, _ in verification_items(doc, rules, tpl)],
        "template_changed": template_changed,
        "ready": not mandatory and not flags and all(j["status"] == "pass" for j in judgment.values()),
    }


def plan_check(repo: Path, state: Dict[str, Any]) -> Dict[str, Any]:
    plan_file = task_dir(repo, state["id"]) / "plan.md"
    tpl = TemplateInfo(read_text(record_template("plan.md")))
    doc = Doc(read_text(plan_file))
    mandatory = check_structure(doc, tpl, "M-plan") + check_placeholders(doc, tpl, "M-plan") + check_markers(doc)
    if not doc.items.get("S"):
        mandatory.append(issue("M-plan", "Implementation Steps lists no steps (- **S1:** …)."))
    mandatory += check_ids(doc, ["S"], "M-plan")
    for name in PLAN_SECTIONS:
        section = doc.section_range(name, contains=True)
        if section is None:
            continue
        _, start, end = section
        entries = block_entries(doc, start, end, "", tpl.tokens)
        reason = is_none_entry(entries)
        if not entries:
            mandatory.append(issue("M-plan", f"Section '{name}' is empty."))
        elif reason is not None and name not in PLAN_NONE_OK:
            mandatory.append(issue("M-plan", f"Section '{name}' cannot be None."))
        elif reason == "":
            mandatory.append(issue("M-plan", f"Section '{name}' says None without a reason."))
    for dep in blocking_deps(repo, state, ("spec", "plan")):
        mandatory.append(issue("M-dependency", f"{dep['id']} ({dep['summary']}) still blocks the plan."))
    warnings = []
    for name in ("Current Behavior", "Proposed Solution", "Affected Areas"):
        section = doc.section_range(name, contains=True)
        if section and not re.search(r"`[^`]*[/.][^`]*`", "\n".join(doc.lines[section[1]:section[2]])):
            warnings.append(issue("A-plan", f"'{name}' cites no files; name the existing code the plan is based on."))
    return {"task": state["id"], "plan_sha256": sha256_file(plan_file), "mandatory": mandatory, "advisory": warnings,
            "steps": [ident for ident, _, _, _ in doc.items.get("S", [])], "ready": not mandatory}


# --------------------------------------------------------------------------- other records

def parse_dependencies(repo: Path, slug: str) -> Dict[str, Any]:
    doc = Doc(read_text(task_dir(repo, slug) / "dependencies.md"))
    deps: List[Dict[str, Any]] = []
    problems: List[str] = []
    explicit_none = any(re.match(r"(?i)^\s*no dependencies identified\s*[—–:\-]+\s*\S", ln) for ln in doc.lines)
    table = doc.find_table("id", "class")
    if table:
        columns = {name.lower(): i for i, name in enumerate(table["header"])}
        for index, cells in table["rows"]:
            row = {name: (cells[i].strip() if i < len(cells) else "") for name, i in columns.items()}
            ident = row.get("id", "")
            if not any(c.strip() for c in cells):
                continue
            if not re.match(r"^DEP-\d+$", ident):
                problems.append(f"line {index + 1}: dependency IDs look like DEP-1.")
                continue
            cls = DEP_CLASSES.get(row.get("class", "").lower())
            gate = row.get("gate", "").lower()
            kind = row.get("type", "").lower()
            if not cls:
                problems.append(f"{ident}: Class must be Blocking, Non-blocking, Verified or Not applicable.")
            if cls == "Blocking" and gate not in DEP_GATES:
                problems.append(f"{ident}: a Blocking dependency needs Gate spec, plan, implementation or completion.")
            if kind and kind not in DEP_TYPES:
                problems.append(f"{ident}: Type should be one of {', '.join(DEP_TYPES)}.")
            deps.append({"id": ident, "type": kind, "class": cls, "gate": gate if gate in DEP_GATES else None,
                         "owner": row.get("owner", ""), "summary": row.get("summary", ""), "line": index + 1})
    for dep in deps:
        if dep["class"] == "Blocking" and dep["type"] == "backend" and not _has_message(doc, dep["id"]):
            problems.append(f"{dep['id']}: add a '### {dep['id']}' section with a ready-to-send "
                            "'**Message to send:**' for the backend developer.")
    return {"deps": deps, "problems": problems, "classified": bool(deps) or explicit_none,
            "explicit_none": explicit_none}


def _has_message(doc: Doc, ident: str) -> bool:
    section = doc.section_range(ident)
    if not section:
        return False
    _, start, end = section
    body = doc.lines[start:end]
    if not any(re.match(r"^\s*\*\*Message to send:\*\*", ln) for ln in body):
        return False
    after = "\n".join(body).split("**Message to send:**", 1)[1]
    return bool(LETTER_RE.search(after.split("**Answer received:**", 1)[0]))


def blocking_deps(repo: Path, state: Dict[str, Any], gates: Sequence[str]) -> List[Dict[str, Any]]:
    path = task_dir(repo, state["id"]) / "dependencies.md"
    if not path.exists():
        return []
    return [d for d in parse_dependencies(repo, state["id"])["deps"] if d["class"] == "Blocking" and d["gate"] in gates]


def parse_matrix(repo: Path, slug: str) -> Tuple[Dict[str, Dict[str, str]], List[str]]:
    doc = Doc(read_text(task_dir(repo, slug) / "verification.md"))
    table = doc.find_table("item", "status")
    if not table:
        return {}, ["verification.md has no acceptance matrix (| Item | Status | Evidence |)."]
    rows: Dict[str, Dict[str, str]] = {}
    problems: List[str] = []
    for _, cells in table["rows"]:
        item = cells[0].strip().strip("*") if cells else ""
        if not item:
            continue
        status = VERIFY_STATUS.get(cells[1].strip().lower()) if len(cells) > 1 else None
        evidence = cells[2].strip() if len(cells) > 2 else ""
        if not status:
            problems.append(f"{item}: Status must be Passed, Failed, Blocked or Not Verified.")
        elif not LETTER_RE.search(evidence):
            problems.append(f"{item}: give the evidence, or the reason it could not be verified.")
        if item in rows:
            problems.append(f"{item} appears more than once in the matrix.")
        rows[item] = {"status": status or "", "evidence": evidence}
    return rows, problems


def parse_audit(repo: Path, slug: str) -> Dict[str, Any]:
    doc = Doc(read_text(task_dir(repo, slug) / "audit.md"))
    tpl = TemplateInfo(read_text(record_template("audit.md")))
    problems = [p["message"] for p in check_placeholders(doc, tpl) + check_markers(doc)]

    def field(name: str) -> str:
        found = doc.label_range(name)
        if not found:
            problems.append(f"'**{name}:**' is missing.")
            return ""
        _, start, end, rest = found
        return " ".join(block_entries(doc, start, end, rest, tpl.tokens)).strip()

    independence = field("Review independence").lower()
    reviewer = field("Reviewer")
    scope = field("Reviewed scope")
    if independence and independence not in INDEPENDENCE:
        problems.append("Review independence must be one of: " + ", ".join(INDEPENDENCE) + ".")
    for name, value in (("Review independence", independence), ("Reviewer", reviewer), ("Reviewed scope", scope)):
        if not value and f"'**{name}:**' is missing." not in problems:
            problems.append(f"'{name}' is empty.")
    findings: List[Dict[str, str]] = []
    table = doc.find_table("id", "severity")
    explicit_none = any(re.match(r"(?i)^\s*no findings\b", ln) for ln in doc.lines)
    if table:
        columns = {name.lower(): i for i, name in enumerate(table["header"])}
        for _, cells in table["rows"]:
            row = {name: (cells[i].strip() if i < len(cells) else "") for name, i in columns.items()}
            ident = row.get("id", "")
            if not ident:
                continue
            severity = next((s for s in SEVERITIES if s.lower() == row.get("severity", "").lower()), None)
            disposition = next((d for d in DISPOSITIONS if d.lower() == row.get("disposition", "").lower()), None)
            if not re.match(r"^F-\d+$", ident):
                problems.append(f"{ident}: finding IDs look like F-1.")
            if not severity:
                problems.append(f"{ident}: Severity must be Critical, Important or Minor.")
            if not disposition:
                problems.append(f"{ident}: Disposition must be Open, Fixed, Accepted or Deferred.")
            if disposition == "Accepted" and not LETTER_RE.search(row.get("notes", "")):
                problems.append(f"{ident}: an Accepted finding needs the user's words in Notes.")
            if disposition == "Deferred" and severity != "Minor":
                problems.append(f"{ident}: only Minor findings can be Deferred.")
            findings.append({"id": ident, "severity": severity or "", "disposition": disposition or "",
                             "finding": row.get("finding", ""), "notes": row.get("notes", "")})
    if not findings and not explicit_none:
        problems.append("Record the findings table, or write 'No findings.' if the review found none.")
    open_items = [f["id"] for f in findings if f["disposition"] == "Open"]
    return {"independence": independence, "reviewer": reviewer, "findings": findings, "problems": problems,
            "open": open_items, "complete": not problems and not open_items}


def parse_report(repo: Path, slug: str) -> Dict[str, Any]:
    doc = Doc(read_text(task_dir(repo, slug) / "report.md"))
    tpl = TemplateInfo(read_text(record_template("report.md")))
    problems = [p["message"] for p in check_structure(doc, tpl) + check_placeholders(doc, tpl) + check_markers(doc)]
    status = None
    found = doc.label_range("Status")
    if found:
        value = strip_md(found[3])
        status = next((o for o in OUTCOMES if o.lower() == value.lower()), None)
    if not status:
        problems.append("Overall Status needs '**Status:**' followed by exactly one of: " + ", ".join(OUTCOMES) + ".")
    for name in REPORT_SECTIONS:
        section = doc.section_range(name, contains=True)
        if section and not block_entries(doc, section[1], section[2], "", tpl.tokens):
            problems.append(f"Report section '{name}' is empty.")
    return {"status": status, "problems": problems}


# --------------------------------------------------------------------------- approvals and gates

def approval_status(repo: Path, state: Dict[str, Any], doc_name: str) -> Tuple[bool, str]:
    record = state["approvals"].get(doc_name)
    if not record:
        return False, f"The {doc_name} has not been approved."
    tdir = task_dir(repo, state["id"])
    snapshot = tdir / record["snapshot"]
    if not snapshot.exists():
        return False, f"The approved {doc_name} snapshot {record['snapshot']} is missing."
    if sha256_file(snapshot) != record["sha256"]:
        return False, f"The approved {doc_name} snapshot {record['snapshot']} was modified."
    current = tdir / f"{doc_name}.md"
    if not current.exists() or sha256_file(current) != record["sha256"]:
        return False, (f"{doc_name}.md changed after v{record['version']} was approved; the change needs the "
                       "user's renewed approval.")
    if doc_name == "plan":
        spec_record = state["approvals"].get("spec")
        if not spec_record or record.get("spec_sha256") != spec_record.get("sha256"):
            return False, "The plan approval belongs to an older spec version; the plan needs renewed approval."
        ok, message = approval_status(repo, state, "spec")
        if not ok:
            return False, message
    return True, f"v{record['version']} approved ({short(record['sha256'])})"


def approved_doc(repo: Path, state: Dict[str, Any], doc_name: str) -> Optional[Doc]:
    record = state["approvals"].get(doc_name)
    if not record:
        return None
    path = task_dir(repo, state["id"]) / record["snapshot"]
    return Doc(read_text(path)) if path.exists() else None


def plan_steps(repo: Path, state: Dict[str, Any]) -> List[str]:
    doc = approved_doc(repo, state, "plan")
    return [ident for ident, _, _, _ in doc.items.get("S", [])] if doc else []


def latest_results(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    latest: Dict[str, Dict[str, Any]] = {}
    for entry in state.get("checks", []):
        if entry.get("kind", "result") == "result":
            latest[entry["id"]] = entry
    return latest


def check_freshness(repo: Path, state: Dict[str, Any], cfg: Dict[str, Any],
                    fingerprint: Optional[str] = None) -> List[Tuple[Dict[str, Any], Optional[Dict[str, Any]], str]]:
    """(check, latest result, state) for each required check; state is fresh, stale or missing."""
    fingerprint = fingerprint or code_fingerprint(repo)
    latest = latest_results(state)
    rows = []
    for check in cfg.get("checks", []):
        if not check.get("required"):
            continue
        result = latest.get(check["id"])
        if not result:
            rows.append((check, None, "missing"))
        elif result.get("fingerprint") != fingerprint:
            rows.append((check, result, "stale"))
        else:
            rows.append((check, result, "fresh"))
    return rows


def expected_items(repo: Path, state: Dict[str, Any], cfg: Dict[str, Any]) -> List[str]:
    doc = approved_doc(repo, state, "spec")
    if doc is None:
        return []
    tpl, rules, _, _ = spec_rules_and_template(repo, cfg)
    return [ident for ident, _ in verification_items(doc, rules, tpl)]


def forward_problems(repo: Path, state: Dict[str, Any], cfg: Dict[str, Any], target: str) -> List[str]:
    slug = state["id"]
    problems: List[str] = []
    if target == "DEPENDENCIES":
        discovery = state.get("discovery") or {}
        if not discovery.get("inspected"):
            problems.append("Record the files you inspected: `discover <task> --inspected <paths>`.")
        if not (discovery.get("summary") or "").strip():
            problems.append("Record the discovery summary (goal, scope, exclusions, affected areas): "
                            "`discover <task> --summary \"…\"`.")
    elif target == "SPECIFICATION":
        deps = parse_dependencies(repo, slug)
        if not deps["classified"]:
            problems.append("Classify dependencies in dependencies.md, or write "
                            "'No dependencies identified — <reason>'.")
        problems += deps["problems"]
    elif target == "SPEC_APPROVAL":
        result = spec_check(repo, state, cfg)
        problems += [f"[{p['rule']}] {p['message']}" for p in result["mandatory"]]
        problems += [f"[flag] {f['message']}" for f in result["flags"]]
        pending = [k for k, v in result["judgment"].items() if v["status"] != "pass"]
        if pending:
            problems.append(f"Review not recorded for this spec version: {', '.join(pending)} (`review <task> --pass …`).")
    elif target == "PLANNING":
        problems.append("PLANNING starts only through `approve <task> spec`, after the user's explicit approval.")
    elif target == "PLAN_APPROVAL":
        ok, message = approval_status(repo, state, "spec")
        if not ok:
            problems.append(message)
        problems += [f"[{p['rule']}] {p['message']}" for p in plan_check(repo, state)["mandatory"]]
    elif target == "IMPLEMENTATION":
        problems.append("IMPLEMENTATION starts only through `approve <task> plan`, after the user's explicit approval.")
    elif target == "TESTING":
        for doc_name in ("spec", "plan"):
            ok, message = approval_status(repo, state, doc_name)
            if not ok:
                problems.append(message)
        undone = [s for s in plan_steps(repo, state) if state["progress"].get(s, {}).get("status") != "done"]
        if undone:
            problems.append(f"Plan steps not marked done: {', '.join(undone)} (`step <task> <S#> done`).")
    elif target == "AUDIT":
        fingerprint = code_fingerprint(repo)
        for check, result, freshness in check_freshness(repo, state, cfg, fingerprint):
            if freshness != "fresh":
                problems.append(f"Required check '{check['id']}' is {freshness}; run it on the current code.")
            elif result and result["status"] == "failed":
                problems.append(f"Required check '{check['id']}' failed; move to FIXING.")
        rows, matrix_problems = parse_matrix(repo, slug)
        problems += matrix_problems
        missing = [i for i in expected_items(repo, state, cfg) if i not in rows]
        if missing:
            problems.append(f"No verification result for: {', '.join(missing)}.")
        failed = [i for i, row in rows.items() if row["status"] == "Failed"]
        if failed:
            problems.append(f"Failed items: {', '.join(failed)}; move to FIXING, or report the task as Partially Completed.")
    elif target == "FINAL_REPORT":
        audit = parse_audit(repo, slug)
        problems += audit["problems"]
        if audit["open"]:
            problems.append(f"Findings still Open: {', '.join(audit['open'])}. Fix them (FIXING), or record the "
                            "user's acceptance, or defer Minor ones.")
    return problems


def transition(repo: Path, state: Dict[str, Any], cfg: Dict[str, Any], target: str, reason: Optional[str], agent: str) -> None:
    current = state["stage"]
    if state["status"] == "closed":
        raise WorkflowError("The task is closed.")
    if target not in STAGES:
        raise WorkflowError(f"Unknown stage {target}. Stages: {', '.join(STAGES)}.")
    ci, ti = STAGES.index(current), STAGES.index(target)
    if ti == ci:
        raise WorkflowError(f"The task is already in {target}.")
    early_report = target == "FINAL_REPORT" and current != "AUDIT"
    if ti < ci:
        if not reason:
            raise WorkflowError("Moving back to an earlier stage needs --reason.")
    elif early_report:
        if not reason:
            raise WorkflowError("Going to FINAL_REPORT before the audit is finished needs --reason "
                                "(the report will be Partially Completed or Blocked).")
    else:
        allowed = {ci + 1}
        if current == "TESTING":
            allowed.add(STAGES.index("AUDIT"))
        if ti not in allowed:
            raise WorkflowError(f"From {current} the next stage is {' or '.join(STAGES[i] for i in sorted(allowed))}.")
        if target == "FIXING" and not reason:
            raise WorkflowError("Say what needs fixing with --reason.")
        problems = forward_problems(repo, state, cfg, target)
        if problems:
            raise WorkflowError(f"Cannot move to {target}:\n{bullet_list(problems)}")
    add_history(state, "stage", agent, **{"from": current, "to": target, "reason": reason})
    state["stage"] = target


# --------------------------------------------------------------------------- checks

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
        proc = subprocess.run(tokens, cwd=str(repo), capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "", float(timeout), f"it timed out after {timeout} seconds"
    except OSError as exc:
        return None, "", 0.0, f"it could not start: {exc}"
    return proc.returncode, (proc.stdout or "") + (proc.stderr or ""), time.time() - started, None


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
        new_errors, preexisting, warnings = [], [], []
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


# --------------------------------------------------------------------------- outcome

def compute_outcome(repo: Path, state: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    level = 0
    reasons: List[str] = []

    def cap(new_level: int, why: str) -> None:
        nonlocal level
        level = max(level, new_level)
        reasons.append(why)

    slug = state["id"]
    for doc_name in ("spec", "plan"):
        ok, message = approval_status(repo, state, doc_name)
        if not ok:
            cap(2, message)
    blockers = blocking_deps(repo, state, DEP_GATES)
    for dep in blockers:
        cap(2, f"Blocked by {dep['id']}: {dep['summary']} (owner: {dep['owner'] or 'unassigned'}).")
    undone = [s for s in plan_steps(repo, state) if state["progress"].get(s, {}).get("status") != "done"]
    if undone:
        cap(2, f"Plan steps not done: {', '.join(undone)}.")
    if state["approvals"].get("spec"):
        rows, problems = parse_matrix(repo, slug)
        for problem in problems:
            cap(2, problem)
        for item in expected_items(repo, state, cfg):
            row = rows.get(item)
            if not row:
                cap(2, f"{item} has no verification result.")
            elif row["status"] == "Failed":
                cap(2, f"{item} failed verification.")
            elif row["status"] in ("Blocked", "Not Verified"):
                cap(1, f"{item} is {row['status']}: {row['evidence']}")
    fingerprint = code_fingerprint(repo)
    for check, result, freshness in check_freshness(repo, state, cfg, fingerprint):
        if freshness == "missing":
            cap(2, f"Required check '{check['id']}' was never run.")
        elif freshness == "stale":
            cap(2, f"Required check '{check['id']}' ran on older code; re-run it.")
        elif result["status"] == "failed":
            cap(2, f"Required check '{check['id']}' failed: {result.get('summary', '')}")
        elif result["status"] == "preexisting":
            cap(1, f"Check '{check['id']}': only problems that existed before the task remain ({result.get('summary', '')}).")
        elif result["status"] == "blocked":
            cap(1, f"Check '{check['id']}' could not run: {result.get('reason') or result.get('summary', '')}")
    audit = parse_audit(repo, slug) if (task_dir(repo, slug) / "audit.md").exists() else None
    if not audit or audit["problems"]:
        cap(2, "The audit is not complete.")
    if audit:
        for finding in audit["findings"]:
            sev, disp = finding["severity"], finding["disposition"]
            if sev == "Critical" and disp in ("Open", "Accepted", "Deferred"):
                cap(2, f"Critical finding {finding['id']} is {disp.lower()}.")
            elif sev == "Important" and disp in ("Open", "Deferred"):
                cap(2, f"Important finding {finding['id']} is {disp.lower()}.")
            elif sev == "Important" and disp == "Accepted":
                cap(1, f"Important finding {finding['id']} was accepted by the user, not fixed.")
    maximum = ("Completed", "Completed with Limitations", "Partially Completed")[level]
    allowed = [o for o, rank in OUTCOME_RANK.items() if rank >= level]
    if blockers:
        allowed.append("Blocked")
    return {"max": maximum, "allowed": allowed, "blocked": bool(blockers), "reasons": reasons, "fingerprint": fingerprint}


# --------------------------------------------------------------------------- discovery for init

def detect_checks(repo: Path) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    pubspec = repo / "pubspec.yaml"
    if pubspec.exists():
        text = read_text(pubspec)
        tool = "flutter" if re.search(r"sdk:\s*flutter", text) else "dart"
        checks.append({"id": "analyze", "name": f"{tool} analyze", "command": f"{tool} analyze",
                       "parser": "dart-analyzer", "fail_on": ["error", "warning", "new"], "required": True})
        if (repo / "test").is_dir():
            checks.append({"id": "test", "name": f"{tool} test", "command": f"{tool} test", "required": True,
                           "accepts_args": True})
        if "build_runner" in text:
            checks.append({"id": "codegen", "name": "build_runner", "required": False,
                           "command": "dart run build_runner build --delete-conflicting-outputs",
                           "when": "Run when code-generated sources (models, serializers) change."})
        checks.append({"id": "dependencies", "name": "New dependencies", "builtin": "manifest-diff",
                       "files": ["pubspec.yaml"], "required": True})
    package = repo / "package.json"
    if package.exists():
        try:
            scripts = (load_json(package).get("scripts") or {})
        except ValueError:
            scripts = {}
        runner = "pnpm" if (repo / "pnpm-lock.yaml").exists() else "yarn" if (repo / "yarn.lock").exists() else "npm run"
        for name in ("lint", "typecheck", "test", "build"):
            if name in scripts:
                checks.append({"id": name, "name": f"{runner} {name}", "command": f"{runner} {name}",
                               "required": name != "build", "accepts_args": name == "test"})
        checks.append({"id": "dependencies", "name": "New dependencies", "builtin": "manifest-diff",
                       "files": ["package.json"], "required": True})
    if (repo / "pyproject.toml").exists() or (repo / "requirements.txt").exists():
        if (repo / "tests").is_dir() or (repo / "test").is_dir():
            checks.append({"id": "test", "name": "pytest", "command": "python -m pytest", "required": True,
                           "accepts_args": True})
    if (repo / "go.mod").exists():
        checks.append({"id": "vet", "name": "go vet", "command": "go vet ./...", "required": True})
        checks.append({"id": "test", "name": "go test", "command": "go test ./...", "required": True})
    if (repo / "Cargo.toml").exists():
        checks.append({"id": "clippy", "name": "cargo clippy", "command": "cargo clippy", "required": True})
        checks.append({"id": "test", "name": "cargo test", "command": "cargo test", "required": True})
    unique: Dict[str, Dict[str, Any]] = {}
    for check in checks:
        unique.setdefault(check["id"], check)
    return list(unique.values())


def discover_project(repo: Path) -> Dict[str, Any]:
    files = run_git(repo, ["ls-files", "-co", "--exclude-standard", "-z"]).split("\0")
    pattern = re.compile(r"(?i)(spec[^/]*template|template[^/]*spec)[^/]*\.md$")
    candidates = sorted(f for f in files if f and not is_records_path(f) and pattern.search(f))
    library = []
    lib_root = library_dir() / "templates"
    if lib_root.is_dir():
        for entry in sorted(lib_root.iterdir()):
            if (entry / "template.md").exists():
                library.append({"name": f"user:{entry.name}", "has_rules": (entry / "rules.json").exists()})
    return {
        "repository": repo.name,
        "instruction_files": [p for p in INSTRUCTION_CANDIDATES if (repo / p).exists()],
        "template_candidates": candidates,
        "user_templates": library,
        "suggested_checks": detect_checks(repo),
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
    write_text(records_dir(repo) / ".gitignore", "# Local pointer to the task this checkout is working on\nACTIVE\n*.local.json\n")
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


# --------------------------------------------------------------------------- command helpers

def require_task(args: argparse.Namespace) -> Tuple[Path, Dict[str, Any], Dict[str, Any]]:
    repo = find_repo(args.repo)
    cfg = load_config(repo)
    state = load_state(repo, args.task)
    return repo, cfg, state


def status_line(repo: Path, state: Dict[str, Any]) -> str:
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


# --------------------------------------------------------------------------- commands

def cmd_init(args: argparse.Namespace) -> int:
    repo = find_repo(args.repo)
    if args.discover:
        report = discover_project(repo)
        if args.json:
            print(json.dumps(report, indent=2))
            return 0
        print(f"Repository: {report['repository']}")
        print("Instruction files: " + (", ".join(report["instruction_files"]) or "none found"))
        print("Specification templates in the repository: " + (", ".join(report["template_candidates"]) or "none found"))
        print("Templates in your private library: " + (", ".join(t["name"] for t in report["user_templates"]) or "none"))
        print("Suggested checks:" + ("" if report["suggested_checks"] else " none detected; ask the user which commands verify this project."))
        for check in report["suggested_checks"]:
            print(f"  - {check['id']}: {check.get('command') or 'built-in ' + check['builtin']}"
                  f"{'' if check.get('required') else ' (optional)'}")
        print("Ask the user to confirm the instruction files, the template and the checks, and how task records are "
              "committed (all, config-only or none). Then run `workflow.py init` with those choices.")
        return 0
    cfg_file = config_path(repo)
    if cfg_file.exists() and not args.update:
        raise WorkflowError("AIDevWorkflow is already set up here. Use --update with --commit or --standards to change those.")
    if args.update:
        cfg = load_config(repo)
        if args.commit:
            cfg.setdefault("records", {})["commit"] = args.commit
            apply_commit_mode(repo, args.commit)
        if args.standards:
            cfg["standards"] = [s.strip() for s in args.standards.split(",") if s.strip()]
        save_json(cfg_file, cfg)
        print("Updated the AIDevWorkflow settings.")
        return 0
    if not args.commit:
        raise WorkflowError("Choose how task records are committed with --commit all, config-only or none (ask the user).")
    if not args.template:
        raise WorkflowError("Choose the specification template with --template <path> or --template user:<name>. "
                            "Ask the user; never invent one. `init --discover` lists candidates.")
    base: Dict[str, Any] = {}
    if args.config:
        try:
            base = load_json(Path(args.config).expanduser())
        except (OSError, ValueError) as exc:
            raise WorkflowError(f"Could not read --config {args.config}: {exc}") from exc
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
    standards = [s.strip() for s in (args.standards or "").split(",") if s.strip()] or base.get("standards") or \
        [p for p in ("CLAUDE.md", "AGENTS.md", "GEMINI.md") if (repo / p).exists()]
    cfg = {
        "schema": 1,
        "project": args.project or base.get("project") or repo.name,
        "standards": standards,
        "spec_template": f"{RECORDS}/templates/{name}.md",
        "spec_rules": f"{RECORDS}/templates/{name}.rules.json" if rules_src else None,
        "template_source": source_label,
        "records": {"commit": args.commit},
        "checks": base["checks"] if "checks" in base else detect_checks(repo),
        "rules": base.get("rules", []),
    }
    assert_no_secrets(json.dumps(cfg), "config.json")
    templates = records_dir(repo) / "templates"
    write_text(templates / f"{name}.md", read_text(template_src))
    if rules_src:
        rules = load_json(rules_src)
        if rules.get("schema") != 1:
            raise WorkflowError(f"{rules_src.name} has an unsupported schema; expected 1.")
        write_text(templates / f"{name}.rules.json", read_text(rules_src))
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
          f"records.commit={args.commit}).")
    if args.commit != "all":
        print(f"Local git exclude rules were written to {exclude} (no tracked files changed).")
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    if not args.invocation or not INVOCATION_RE.search(args.invocation):
        raise WorkflowError(
            "Task files are created only when the user explicitly starts AIDevWorkflow. Pass the user's starting "
            "message with --invocation; it must name the skill (for example '/ai-dev-workflow …'). If the user did not "
            "ask for AIDevWorkflow, stop and work normally.")
    repo = find_repo(args.repo)
    cfg = load_config(repo)
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


# --------------------------------------------------------------------------- agent hooks

def _find_records(start: Path) -> Optional[Path]:
    for folder in [start, *start.parents]:
        if (folder / RECORDS / "ACTIVE").is_file():
            return folder
    return None


def _hook_log(hook: str, **data: Any) -> None:
    """Append one line per hook decision when AI_DEV_WORKFLOW_HOOK_LOG names a file (for diagnosing installs)."""
    path = os.environ.get("AI_DEV_WORKFLOW_HOOK_LOG")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"at": now_iso(), "hook": hook, **data}) + "\n")
    except OSError:
        pass


def _deny(reason: str) -> int:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))
    return 0


def gate_decision(repo: Path, active: Dict[str, Any], target: Path, session: Optional[str]) -> Optional[str]:
    """Return a denial reason, or None to allow the edit."""
    state = load_state(repo, active["task"])
    if state["status"] != "active":
        return None
    try:
        rel = target.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return None
    slug = state["id"]
    stage_i = STAGES.index(state["stage"])
    prefix = f"{RECORDS}/tasks/{slug}/"
    if is_records_path(rel):
        if re.match(rf"^{re.escape(RECORDS)}/tasks/[^/]+/approved/", rel):
            return "Approved snapshots are immutable. To change the spec or plan, move the task back a stage and edit spec.md or plan.md."
        if rel.endswith("/state.json") or rel == f"{RECORDS}/ACTIVE":
            return "state.json and ACTIVE are written by workflow.py only; use its commands instead of editing them."
        if rel == prefix + "spec.md" and stage_i > STAGES.index("SPEC_APPROVAL"):
            return (f"The spec is approved. To change it, first move back: `workflow.py stage {slug} SPECIFICATION "
                    "--reason …`, then edit and get renewed approval.")
        if rel == prefix + "plan.md" and stage_i > STAGES.index("PLAN_APPROVAL"):
            return (f"The plan is approved and immutable. To change it, first move back: `workflow.py stage {slug} "
                    "PLANNING --reason …`, then edit and get renewed approval.")
        return None
    unrelated = (f" If this edit is unrelated to task '{slug}', pause the task first (`workflow.py pause {slug}`); "
                 "normal editing resumes immediately.")
    if state["stage"] not in CODE_STAGES:
        return f"AIDevWorkflow task '{slug}' is in {state['stage']}; code may change only in IMPLEMENTATION or FIXING after a passing preflight." + unrelated
    for doc_name in ("spec", "plan"):
        ok, message = approval_status(repo, state, doc_name)
        if not ok:
            return f"AIDevWorkflow task '{slug}': {message}" + unrelated
    for dep in blocking_deps(repo, state, ("spec", "plan", "implementation")):
        return f"AIDevWorkflow task '{slug}' is blocked by {dep['id']} ({dep['summary']})." + unrelated
    if active.get("preflight_session") != session or not active.get("preflight_at"):
        return f"Run `workflow.py preflight {slug} --agent claude-code --session <this session>` before editing code in this session." + unrelated
    return None


def hook_claude_pre_edit(raw: str) -> int:
    try:
        data = json.loads(raw or "{}")
        tool_input = data.get("tool_input") or {}
        file_path = tool_input.get("file_path") or tool_input.get("notebook_path") or tool_input.get("path")
        if not file_path:
            return 0
        session = clean_session(data.get("session_id"))
        target = Path(file_path)
        if not target.is_absolute():
            target = Path(data.get("cwd") or os.getcwd()) / target
        repo = _find_records(target.parent)
        if repo is None:
            _hook_log("claude-pre-edit", session=session, file=str(target), decision="allow", why="no active task")
            return 0
        active = read_active(repo)
        if not active:
            return 0
        bound = active.get("session")
        if bound and session and bound != session:
            _hook_log("claude-pre-edit", session=session, file=str(target), decision="allow", why="other session")
            return 0
        if not bound:
            if active.get("agent") not in (None, "claude-code", "unknown-agent"):
                _hook_log("claude-pre-edit", session=session, file=str(target), decision="allow", why="other agent")
                return 0
            active["session"] = session
            if active.get("preflight_at") and not active.get("preflight_session"):
                active["preflight_session"] = session
            save_json(active_path(repo), active)
        if not (task_dir(repo, active["task"]) / "state.json").exists():
            return 0
    except Exception:  # noqa: BLE001 - without an active task the hook must never interfere
        return 0
    try:
        reason = gate_decision(repo, active, target, session)
    except Exception as exc:  # noqa: BLE001 - inside an active task, fail closed
        reason = f"AIDevWorkflow could not validate task '{active.get('task')}' ({exc}). Fix the records or pause the task."
    _hook_log("claude-pre-edit", session=session, file=str(target), task=active.get("task"),
              decision="deny" if reason else "allow", why=reason or "gates satisfied")
    return _deny(reason) if reason else 0


def hook_claude_prompt(raw: str) -> int:
    try:
        data = json.loads(raw or "{}")
        session = clean_session(data.get("session_id"))
        repo = _find_records(Path(data.get("cwd") or os.getcwd()))
        if repo is None:
            return 0
        active = read_active(repo)
        if not active or (active.get("session") and session and active["session"] != session):
            return 0
        state = load_state(repo, active["task"])
        if state["status"] != "active":
            return 0
        print(f"[AIDevWorkflow] Active task '{state['id']}': {status_line(repo, state)}. Next: {NEXT[state['stage']]} "
              f"(Rules: re-read the skill's {REFERENCE[state['stage']]}. Pause with `workflow.py pause {state['id']}` "
              "for unrelated work.)")
    except Exception:  # noqa: BLE001 - status reminders must never interfere
        return 0
    return 0


def cmd_hook(args: argparse.Namespace) -> int:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    if args.name == "claude-pre-edit":
        return hook_claude_pre_edit(raw)
    if args.name == "claude-prompt":
        return hook_claude_prompt(raw)
    raise WorkflowError(f"Unknown hook '{args.name}'.")


# --------------------------------------------------------------------------- CLI

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
    p.add_argument("--discover", action="store_true", help="Only list instruction files, templates and suggested checks.")
    p.add_argument("--template", help="Template file path, or user:<name> from your private library.")
    p.add_argument("--rules", help="Template rules file (default: <template>.rules.json next to the template).")
    p.add_argument("--no-rules", action="store_true", help="Use structural checks only.")
    p.add_argument("--commit", choices=COMMIT_MODES, help="How task records are committed to git.")
    p.add_argument("--standards", help="Comma-separated engineering instruction files, e.g. CLAUDE.md,AGENTS.md.")
    p.add_argument("--config", help="JSON file with checks and rules to start from.")
    p.add_argument("--project-notes", help="Markdown file to use as .ai-dev-workflow/PROJECT.md.")
    p.add_argument("--project", help="Project name.")
    p.add_argument("--update", action="store_true", help="Change --commit or --standards of an existing setup.")
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


if __name__ == "__main__":
    sys.exit(main())
