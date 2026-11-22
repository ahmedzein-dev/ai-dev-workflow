"""Parsers for dependencies, the acceptance matrix, the audit and the final report."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple
from aidw.constants import DEP_CLASSES, DEP_GATES, DEP_TYPES, DISPOSITIONS, INDEPENDENCE, OUTCOMES, REPORT_SECTIONS, SEVERITIES, VERIFY_STATUS
from aidw.infra.text import read_text
from aidw.records.markdown import Doc, LETTER_RE, TemplateInfo, block_entries, check_markers, check_placeholders, check_structure, strip_md
from aidw.store.config import record_template, task_dir


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
