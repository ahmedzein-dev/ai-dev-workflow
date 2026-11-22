"""Specification and plan checks."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from aidw.constants import DEFAULT_VAGUE_WORDS, PLAN_NONE_OK, PLAN_SECTIONS
from aidw.errors import WorkflowError
from aidw.infra.text import read_text, sha256_file
from aidw.records.markdown import CHECKBOX_RE, Doc, ID_RE, TemplateInfo, block_entries, check_ids, check_markers, check_placeholders, check_structure, clean_tokens, is_none_entry, issue, strip_md, target_entries, target_texts
from aidw.records.parsers import blocking_deps
from aidw.store.config import load_rules, record_template, task_dir, template_path


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
