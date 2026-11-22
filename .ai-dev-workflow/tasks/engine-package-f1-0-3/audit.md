# Audit: F1.0.3 Split workflow.py into the aidw package (no behaviour change)

**Review independence:** subagent
**Reviewer:** Claude Code read-only general-purpose subagent (Opus 5.5), given the task folder, the pre-split engine at HEAD and the list of changed files, not the implementer's summary
**Reviewed scope:** HEAD `workflow.py` vs `aidw/**` (AST and source comparison of every top-level statement), `workflow.py`, `tests/test_package.py`, `tests/golden/workflow-public-names.txt`, `README.md`, approved spec v1 and plan v1, verification.md, state.json; installs, hooks and timing re-run by the reviewer

## Dimensions

- **A. Specification compliance:** FR-1–FR-8 met. The verbatim move was confirmed by an independent AST comparison: 213 → 212 top-level statements (the `__main__` block stays in `workflow.py`), no name missing or duplicated, the only difference is `SKILL_DIR` (`parent.parent` → `parents[2]`), order and interior comments preserved.
- **B. Architecture compliance:** Acyclic import graph; modules import only from their own layer or lower; no logic in the entry point. README wording corrected (F-5).
- **C. Code quality:** No shared mutable state, no dynamic global lookups; the only `__file__` use is `SKILL_DIR`.
- **D. Security and privacy:** Privacy scan clean (167 files); the bundled package cannot be shadowed by another `aidw` on the path (now tested).
- **E. Edge cases:** All seven handled; EC-4 and EC-5 evidence strengthened with real tests (F-3).
- **F. Regression risk:** One real behaviour change found and fixed: bytecode caches written into installed copies (F-1). Narrower module surface documented (F-4).
- **G. Test adequacy:** Added project-install, shadowing and doctor "No problems found" assertions; the bytecode regression test fails without the fix (observed).
- **H. Scope compliance:** Only planned files changed; `install.py`, `SKILL.md`, `tools/`, existing tests untouched.
- **I. Reliability and performance:** Startup +3.2 ms (`--version`) and +5.2 ms (hook), below the 50 ms threshold.

## Project standards checklist

No standards files configured. Spec constraints: standard library only (yes), CLI and records unchanged (golden byte-identical, 147 existing tests unchanged and passing), protected files untouched (yes).

## Findings

| ID | Severity | Dimension | Finding | Location | Disposition | Notes |
|----|----------|-----------|---------|----------|-------------|-------|
| F-1 | Important | F | Importing `aidw` wrote `__pycache__` into installed copies (the single file never did); project installs showed untracked bytecode in users' repositories | `scripts/workflow.py` | Fixed | `sys.dont_write_bytecode = True` before the imports; `ProjectInstallTest` checks copies and `git status` stay clean (it failed before the fix) |
| F-2 | Minor | A | Wrong counts in verification.md (tests, modules, layers) | verification.md | Fixed | 156 tests (147 + 9), 27 import units (19 modules + 8 packages), 5 layer levels |
| F-3 | Minor | A | EC-4 project copies, EC-5 shadowing and AC-3 "no problems" were claimed beyond what tests covered | tests/test_package.py | Fixed | `ProjectInstallTest`, `ShadowingTest`, doctor assertion added |
| F-4 | Minor | C | `workflow` no longer exposes stdlib modules and typing names; patching a re-exported name no longer affects package internals | `scripts/workflow.py` | Fixed | Allowed by FR-3; documented in the entry point's docstring |
| F-5 | Minor | B | README said layers import "only downwards"; same-layer imports exist | README.md | Fixed | Wording: own layer or lower |

## Remediation log

FIXING (reason recorded in state.json): `workflow.py` (F-1, F-4), `tests/test_package.py` (F-1, F-3), `README.md` (F-5), verification.md (F-2). Re-run on code 9b5f860b53: `unit` 156 tests, `unit-py39`, `privacy`, `ruff`, `mypy`, `golden-byte-compare`, `prepublish-loads-engine`, `startup-timing` — all passed.
