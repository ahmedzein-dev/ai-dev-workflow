"""Minimal Markdown model and template structure checks."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple
from aidw.errors import WorkflowError
from aidw.infra.text import norm


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
        for ident, _, lineno, text in items:
            if lineno not in flagged and not LETTER_RE.search(clean_tokens(text, tpl.tokens)):
                problems.append(issue(rule, f"{ident} has no content.", lineno))
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
