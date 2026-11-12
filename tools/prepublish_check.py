#!/usr/bin/env python3
"""Scan the AIDevWorkflow repository for secrets and private information before it is published.

    python3 tools/prepublish_check.py [--root .] [--private-terms FILE] [--fingerprints DIR ...]

- Secret patterns come from the skill's engine (one list for both).
- Email addresses outside example domains, and home-directory paths with a real user name.
- --private-terms: a file kept OUTSIDE the repository, one term per line (company, client and personal names).
- --fingerprints: folders of private files (for example a personal spec template) that must not appear in the
  repository, verbatim or in part.
Exit code 1 when anything is found.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "skills" / "ai-dev-workflow" / "scripts" / "workflow.py"
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")
ALLOWED_EMAIL = re.compile(r"@(?:example\.(?:com|org|net)|(?:users\.)?noreply\.github\.com|anthropic\.com)$", re.I)
HOME_RE = re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\+Users\\+)([A-Za-z0-9._-]+)")
ALLOWED_HOME = {"you", "user", "username", "me", "runner", "name", "your-name", "example", "<you>", "shared"}
RISKY_FILES = re.compile(r"(?i)(^|/)(\.env(\..*)?|id_rsa|id_ed25519|.*\.pem|.*\.p12|.*\.keystore|.*\.jks|credentials\.json)$")
MAX_BYTES = 2_000_000


def load_engine():
    spec = importlib.util.spec_from_file_location("aidw_workflow", ENGINE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def repo_files(root: Path) -> List[Path]:
    proc = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=str(root),
                          capture_output=True, text=True)
    if proc.returncode == 0:
        return [root / p for p in proc.stdout.split("\0") if p]
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__", "node_modules")]
        files += [Path(dirpath) / f for f in filenames]
    return files


def normalized(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).strip()


def distinctive_lines(text: str) -> Set[str]:
    lines = set()
    for line in text.split("\n"):
        stripped = re.sub(r"\s+", " ", line).strip()
        if len(stripped) >= 40 and not re.fullmatch(r"[|\-:\s]+", stripped):
            lines.add(stripped)
    return lines


def load_fingerprints(folders: List[str]) -> List[Tuple[str, str, Set[str]]]:
    prints = []
    for folder in folders:
        for path in sorted(Path(folder).expanduser().rglob("*")):
            if path.is_file() and path.stat().st_size < MAX_BYTES:
                try:
                    text = normalized(path.read_text(encoding="utf-8"))
                except UnicodeDecodeError:
                    continue
                prints.append((str(path), hashlib.sha256(text.encode()).hexdigest(), distinctive_lines(text)))
    return prints


def scan(root: Path, terms: List[str], prints: List[Tuple[str, str, Set[str]]]) -> List[str]:
    engine = load_engine()
    findings: List[str] = []
    for path in repo_files(root):
        rel = path.relative_to(root).as_posix()
        if not path.is_file():
            continue
        if RISKY_FILES.search(rel):
            findings.append(f"{rel}: file type that usually holds secrets")
        size = path.stat().st_size
        if size > MAX_BYTES:
            findings.append(f"{rel}: large file ({size} bytes); check it belongs in the repository")
            continue
        data = path.read_bytes()
        if b"\0" in data[:8000]:
            continue
        text = data.decode("utf-8", errors="replace")
        for kind, line in engine.find_secrets(text):
            findings.append(f"{rel}:{line}: possible {kind}")
        for lineno, line in enumerate(text.split("\n"), 1):
            for email in EMAIL_RE.findall(line):
                if not ALLOWED_EMAIL.search(email):
                    findings.append(f"{rel}:{lineno}: email address {email}")
            for match in HOME_RE.finditer(line):
                if match.group(1).lower() not in ALLOWED_HOME:
                    findings.append(f"{rel}:{lineno}: home-directory path with a user name ({match.group(0)})")
            low = line.lower()
            for term in terms:
                if term.lower() in low:
                    findings.append(f"{rel}:{lineno}: private term '{term}'")
        if prints:
            norm_text = normalized(text)
            digest = hashlib.sha256(norm_text.encode()).hexdigest()
            lines = distinctive_lines(norm_text)
            for private_path, private_digest, private_lines in prints:
                if digest == private_digest:
                    findings.append(f"{rel}: identical to private file {Path(private_path).name}")
                else:
                    shared = len(lines & private_lines)
                    if shared >= 3:
                        findings.append(f"{rel}: shares {shared} lines with private file {Path(private_path).name}")
    return findings


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(description="Scan for secrets and private information before publishing.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--private-terms", help="File outside the repository with one private term per line.")
    parser.add_argument("--fingerprints", action="append", default=[], help="Folder of private files that must not appear.")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    terms: List[str] = []
    if args.private_terms:
        terms_path = Path(args.private_terms).expanduser().resolve()
        if root in terms_path.parents:
            print("The private terms file must live outside the repository.", file=sys.stderr)
            return 2
        terms = [t.strip() for t in terms_path.read_text(encoding="utf-8").splitlines() if t.strip() and not t.startswith("#")]
    findings = scan(root, terms, load_fingerprints(args.fingerprints))
    for finding in findings:
        print(finding)
    scanned = len(repo_files(root))
    print(f"Scanned {scanned} files: " + ("no findings." if not findings else f"{len(findings)} finding(s)."))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
