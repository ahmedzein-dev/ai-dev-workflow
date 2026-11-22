# Technical Debt Report

> Phase references updated on 2026-11-22 to the current numbering (MASTER_ROADMAP §3).

Phase 0 deliverable. Each item has evidence in the code, its impact, and the phase planned to address it.
Severity: **High** blocks a roadmap goal or can produce wrong results · **Medium** slows development or affects
some users · **Low** is cosmetic or rare.

| ID | Debt | Evidence | Impact | Severity | Fix (phase) |
|---|---|---|---|---|---|
| TD-01 | Single 3,458-line engine module | `workflow.py` | Hard to navigate, review and extend; every phase adds to it | High | Split into a stdlib package with a thin `workflow.py` entry point, behaviour unchanged (P1 · E1.0) |
| TD-02 | Gates are an imperative `if` chain | `forward_problems` L1329, `transition` L1393, special cases for PLANNING/IMPLEMENTATION | Custom stages or policies (P15) would need edits in several places | Medium | Declarative gate table; same behaviour, tested by the existing scenario tests (P2 · E2.1) |
| TD-03 | Detected checks are de-duplicated by `id` across ecosystems | `detect_checks` L1973–1975: `unique.setdefault(check["id"], check)` | In a repository with both `package.json` and pytest, the Python `test` check is silently dropped. **Reproduced** on 2026-11-22: a repo with a `test` script, pytest config and `apps/mobile/pubspec.yaml` got only `lint`, `npm run test` and `manifest-diff`; no pytest, no Flutter checks (also confirms TD-04) | High (for multi-tech repos) | Component-scoped check IDs (`web:test`, `api:test`) from the detection engine (P1 · E1.1) |
| TD-04 | Detection inspects only the repository root | `_read(repo, "pubspec.yaml")`, `repo / "go.mod"`, … in L1806–1979 | Monorepos, `apps/*`, `packages/*`, `services/*` get no recommendations | High | Component discovery over `git ls-files` (P1 · E1.1) |
| TD-05 | Technology knowledge lives in core code | `_dart_checks`, `_node_checks`, `_python_checks`, `_other_checks` | Adding a technology needs a core change and a release | High | Declarative adapters (P1 · E1.2) |
| TD-06 | One output parser (Dart analyzer) | `parse_analyzer` L1431, `--baseline` refused for other parsers L2926 | No new-vs-existing issue separation for other linters | Medium | JUnit XML, SARIF, regex parsers; baselines for any parser (P1 · E1.3) |
| TD-07 | Checks always run at the repository root | `execute(repo, …)` uses `cwd=str(repo)` | Component commands need wrappers | Medium | Optional `cwd` per check (P1 · E1.4), with schema bump |
| TD-08 | `state.json` schema is never checked on load | `load_state` L813 validates keys but not `schema` | A future format would be misread instead of migrated | High (before any state change) | Schema check + `migrate` command (P1 · E1.0) |
| TD-09 | No locking around read-modify-write of `state.json` and `ACTIVE` | `save_state`, `activate`, the Claude hook writes `ACTIVE` (L3253) | Two processes (hook + command, or two agents) can lose an update | Medium | Lock file with timeout, stale-lock detection (P1 · E1.0) |
| TD-10 | Atomic write without `fsync`; temp files not cleaned after a crash | `write_text` L146 | Rare data loss on power failure; stray `.state.json.<pid>.tmp` files | Low | fsync file and directory; cleanup on next run (P1 · E1.0) |
| TD-11 | Timeouts kill only the direct child | `execute` L1494: `subprocess.run(…, timeout=…)` with captured pipes | A test runner's child processes can survive, and holding the pipes can make the call hang past the timeout | Medium — the same pattern failed on Windows in the F6.0.2 trial (child of a venv launcher; output blocked on a ~4 KB pipe until the kill) | Run in a new process group/session and kill the group; stream output to a file (P2 · E2.5) |
| TD-12 | Full command output held in memory | `capture_output=True` | Very verbose test runs use a lot of memory | Low | Stream to a temp file, keep tail + digest (P2 · E2.5) |
| TD-13 | `history` grows without limit | `add_history` L846 (checks capped at 200, checkpoints at 60) | Long tasks grow `state.json`; slower saves and secret scans | Low | Move history to an append-only `events.jsonl` (P2 · E2.4) |
| TD-14 | The code fingerprint is recomputed several times per command | `status`, `outcome`, `task_summary` each call `code_fingerprint` | Slow on very large repositories | Low | Compute once per command; measure on a large fixture (P2) |
| TD-15 | Business logic and printing are mixed | `cmd_*` functions build results and print | A dashboard or orchestrator would have to parse text or duplicate logic | High (for P11) | Engine API returning data; CLI and dashboard render it (P1 · E1.0, finished in P11) |
| TD-16 | Version string in several places | `__version__`, SKILL.md `metadata.version`, `test_metadata_values_are_strings` asserts `"1.0.0"` | Easy to release with mismatched versions | Low | One source of truth + consistency test (P1) |
| TD-17 | No lint or type checking for the engine | No ruff/mypy configuration in the repo | Regressions caught only by tests | Medium | Dev-only ruff + mypy in CI, nothing added to the shipped skill (P1) |
| TD-18 | Claude hook command is POSIX shell | SKILL.md frontmatter `for d in …; do …` | Behaviour on native Windows Claude Code is unverified | Medium | Test on Windows; add a `python`-only fallback command if needed (P2 · E2.2) |
| TD-19 | Approver identity is free text | `approve --by` default `"user"` | No link between an approval and a person | Medium | Approval channel + optional identity (git user, signing key) (P2 · E2.3) |
| TD-20 | `manifest-diff` understands three manifest formats | `manifest_dependencies` L1518 | New-dependency control is missing for most ecosystems | Medium | Manifest readers provided by adapters (P1 · E1.2) |
| TD-21 | Hand-maintained bilingual HTML guide (1,296 lines) | `index.html` | Every feature needs two-language edits; doc tests catch drift but not omissions | Medium | Keep the guide; generate the command reference from the engine's parser (P19); keep the roadmap HTML data-driven |
| TD-22 | The CI harvesting reads only single-line `run:` commands | `ci_commands` L1982 | Multi-line CI steps are not suggested | Low | Read multi-line `run: |` blocks (P1 · E1.1) |
| TD-23 | Task types are fixed | `TASK_TYPES` L42 | Research, docs, infrastructure and security tasks map poorly | Medium | Task types from config with templates per type (P1 · E1.5) |

## Not debt (deliberate choices to keep)

- Standard library only, single skill folder.
- No shell in check execution.
- Fingerprints that ignore commits (evidence stays valid across a commit of the same code).
- Fail-open hooks without a task, fail-closed inside one.
- Records in Markdown that humans and agents can read and edit (except `state.json` and `approved/`).
