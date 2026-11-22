# Final Report: F1.0.3 Split workflow.py into the aidw package (no behaviour change)

## 1. Overall Status

**Status:** Completed with Limitations

Everything was implemented and verified locally on macOS with Python 3.13 and 3.9. The only item not verified is CI on
three operating systems (DW-4), which runs after the owner pushes the branch.

## 2. What Was Implemented

- The 3,458-line engine moved verbatim into `skills/ai-dev-workflow/scripts/aidw/`: 19 modules in 7 subpackages
  (`infra`, `records`, `store`, `core`, `adapters`, `agents`, `cli`) plus `errors` and `constants`, with 5 layer levels.
- `workflow.py` is now an entry point without engine logic: it disables bytecode writing (as the single file never
  wrote any), puts its own folder first on `sys.path`, re-exports every public name and runs `main()`.
- New tests (`tests/test_package.py`): public names, standard-module patches, template path, fresh imports, layer rule
  and no cycles, no logic in the entry point, user and project install round trips, no bytecode in project copies,
  shadowing by another `aidw`.
- README "Development" describes the layers.

## 3. Specification Compliance

Matches spec v1 (e4243a94) and plan v1 (963f000b). An independent AST comparison confirmed the move is verbatim except
`SKILL_DIR`. Not verified: DW-4 (CI).

## 4. Testing Results

On code 9b5f860b53: `unit` 156 tests (147 existing + 9 new) on Python 3.13, `unit-py39` on Python 3.9.6, `privacy` (167
files), `ruff`, `mypy` (30 files), golden files byte-identical, `tools/prepublish_check.py` loads the engine by path,
startup `--version` 58.3 → 61.5 ms and hook 57.6 → 62.8 ms (median of 15).

## 5. Code Audit

Independent read-only subagent: one Important finding — bytecode caches were written into installed copies, visible in
users' repositories for project installs — fixed and covered by a test that failed before the fix; four Minor findings
(evidence counts, evidence coverage, documented module surface, README wording), all fixed.

## 6. Edge Cases and Regression Risks

Patching a name on `workflow` no longer changes behaviour inside the package (documented; no current test relies on
it). A manual copy missing `aidw/` would now fail on import instead of running; the installer always copies it.

## 7. Pending Dependencies

The owner's push to run CI (DW-4).

## 8. Next Actions

- After the push: confirm the three-OS test matrix and lint job.
- Next feature: F1.0.4 (engine API layer separated from printing) or F1.0.5 (state schema check, migration, locking).
