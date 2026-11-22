"""Names, stages, record tables and stage guidance shared by the whole engine."""
from __future__ import annotations

import re
from pathlib import Path


SKILL_NAME = "ai-dev-workflow"


RECORDS = ".ai-dev-workflow"


SKILL_DIR = Path(__file__).resolve().parents[2]  # aidw/constants.py -> skill folder


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
