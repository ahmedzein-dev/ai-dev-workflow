"""Secret detection and redaction (also used by tools/prepublish_check.py through workflow.py)."""
from __future__ import annotations

import re
from typing import List, Tuple
from aidw.errors import WorkflowError


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
