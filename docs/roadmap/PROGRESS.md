# Progress

The log of where the roadmap stands, updated only from recorded evidence (task reports, test runs, CI). Newest
entries first. Feature statuses live in [roadmap-data.js](roadmap-data.js); this file explains them.

## Now

| | |
|---|---|
| Phase | 1 — Foundations & universal technology support (in progress) |
| Done in Phase 1 | F1.0.1 self-hosting setup · F1.0.2 dev tooling · F1.0.3 engine package (CI passed on 3 OSes × Python 3.9/3.13 at `3837bb2`) |
| In progress | F1.0.4 engine API (task `engine-api-f1-0-4`): spec v1 and plan v1 ready |
| Waiting on | The owner: approval of the F1.0.4 spec and plan |
| Next action | F1.0.4 implementation after approval; then F1.0.5 (state schema, migration, locking) |
| Blockers | None |

## Phase progress

Counted in features (F-IDs); `done` only with recorded evidence. Numbering after the ORE integration (D-031);
history in MASTER_ROADMAP §9.

| Phase | Features done / total | Status |
|---|---|---|
| 0 | 15 / 15 | Done |
| 1 | 3 / 25 | In progress |
| 2 | 0 / 20 | Planned |
| 3 | 0 / 12 | Planned (MVP) |
| 4 | 0 / 12 | Planned (MVP) |
| 5 | 0 / 12 | Planned (MVP complete) |
| 6 | 1 / 19 | Planned (ORE v1); F6.0.2 done early for D-037 |
| 7 | 0 / 15 | Planned |
| 8 | 0 / 8 | Planned |
| 9 | 0 / 8 | Planned |
| 10 | 0 / 11 | Planned (ORE advanced) |
| 11 | 0 / 16 | Planned |
| 12 | 0 / 10 | Planned |
| 13 | 0 / 6 | Planned |
| 14 | 0 / 9 | Planned |
| 15 | 0 / 5 | Planned |
| 16 | 0 / 7 | Planned |
| 17 | 0 / 5 | Planned |
| 18 | 0 / 3 | Future (study) |
| 19 | 0 / 8 | Planned (checklist from v1.1) |

## Log

### 2026-11-22 — D-037 accepted; F6.0.2 closed; F1.0.4 started

- Owner: «Final approval granted for D-037» with conditions FA-1–FA-8 (DECISIONS.md). Recorded: policy rule refusing
  runs that require a hard memory limit where none exists (macOS), support matrix, cold start as an observation, the
  two Windows controller fixes as a named permanent regression test (trial workflow now also on `main` and pull
  requests).
- CI at `7e35018`: `tests` 7/7 and `ore-cpsat-trial` 6/6 (with the FA-3 regression test) passed, so F6.0.2 is closed
  (FA-8). Z3 and HiGHS hands-on checks stay with Phase 10.
- Next feature in the agreed order: F1.0.4 engine API, as task `engine-api-f1-0-4`; spec v1 (`f4dd4068`) and plan v1
  (`6d7e2c07`) await the owner's approval.

### 2026-11-22 — Pushed; CI green; CP-SAT trial complete on three operating systems

- Owner approved the push and P-1–P-3, and added R1–R6 (quoted in DECISIONS.md).
- Branch `phase-1/foundations` pushed (the active GitHub CLI account had no access, so the push used the owner's
  `ahmedzein-dev` credential for that command only). CI now also runs on `phase-*` branches.
- `tests` at `3837bb2`: 6 jobs (Linux, Windows, macOS × Python 3.9, 3.13) and lint passed. F1.0.2 and F1.0.3 verified
  by CI.
- `ore-cpsat-trial` at `3837bb2`: 6 of 6 jobs passed after two controller fixes found by the first runs on Windows
  (memory over the whole process tree; pipes drained while running). 0 mismatches against enumeration in 1,650 models
  per run; the gap trap reproduced on every platform; OS memory limits enforced on Linux and Windows, unavailable on
  macOS; cold start of 38–42 s reproduced only on the owner's Mac.
- D-037 stays approved in principle until the owner's final review.

### 2026-11-22 — F1.0.3 committed; D-037 conditionally approved; CP-SAT trial (F6.0.2, part 1)

- Owner: «Commit» — F1.0.3 committed (`7925fed`) with the roadmap updates (`97a63bd`); not pushed.
- Owner conditionally approved D-037 and the download and trial of OR-Tools in an isolated environment, with
  conditions C1–C13 (quoted in DECISIONS.md).
- Trial on macOS, Python 3.13.2 and 3.9.6, `ortools` 9.15.6755: 0 mismatches against exhaustive enumeration in 1,650
  models; the gap trap was reproduced (`OPTIMAL` with objective 50, bound 0 → `FEASIBLE_NOT_PROVEN`); doubles lose
  precision above 2^53 (the exact path does not); `max_memory_in_mb` is not enforced and macOS `setrlimit` fails, while
  the external RSS watchdog works; one worker uses one core; runs are identical under a deterministic time limit.
- Verdict: conditions met on macOS with the ORE controls in CPSAT_TRIAL §4. Open: Linux/Windows runs, P-1–P-3,
  final D-037.

### 2026-11-22 — F1.0.3 closed: Completed with Limitations; solver comparison done

- `workflow.py` (3,458 lines) moved verbatim into `scripts/aidw/` (19 modules, 7 subpackages, 5 layer levels); the entry
  point has no engine logic. Independent AST comparison: identical except `SKILL_DIR`.
- Audit: one Important finding (bytecode written into installed copies) fixed with `sys.dont_write_bytecode` and a
  project-install test; four Minor findings fixed. Checks on code 9b5f860b53: 156 tests on Python 3.13 and 3.9, privacy,
  ruff, mypy, golden byte-identical, startup +3 to +5 ms. CI after push.
- ORE solver comparison written from official sources (ore/SOLVER_COMPARISON.md); D-037 recommends OR-Tools CP-SAT.

### 2026-11-22 — Approvals and first commit

- Owner: «Approved all and you do the commit». Recorded: F1.0.3 spec v1 and plan v1 approved; DEP-1 (commit
  F1.0.2 first) and DEP-2 (roadmap files always out of task scope, written to PROJECT.md) resolved; ORE integration
  D-031–D-040 accepted except D-037 (not yet presented; depends on the solver research).
- Work committed on branch `phase-1/foundations` (not pushed).

### 2026-11-22 — ORE integration (brief 3)

- New design set [ore/](ore/): ORE design (responsibilities, fit gate, lifecycle, architecture, applications, AI model
  selection, agent allocation, evidence), mathematical model schema, strict optimality policy (status model, guarantee
  levels G0–G3, verification, precision, resource limits, multi-objective, uncertainty), solver comparison (from
  official sources), security and threat model, validation strategy and known limitations.
- Phases renumbered to 0–19 (D-031): new Phase 6 (ORE foundations, v1.6) and Phase 10 (ORE advanced, v2.3); ORE epics in
  phases 9 (performance registry), 11 (ORE views), 14 (agent/model allocation), 15 (solver adapters), 16 (ORE for FDE),
  19 (validation matrix). RTM extended with brief 3 (34 rows); risks R-22–R-26; invariants INV-19–INV-22.
- F1.0.3 stays at SPEC_APPROVAL; nothing of brief 3 is implemented before approval.

### 2026-11-22 — Strategic integration of brief 2 (engineering intelligence) — approved

- Owner's approval: «Approved». D-020–D-030 Accepted; D-014's version mapping superseded by D-029. Phase 0 done.

- New: [ENGINEERING_INTELLIGENCE.md](ENGINEERING_INTELLIGENCE.md) (layers, record model, approval types, modes, depth,
  questioning, profiles, diagrams, evals, change classification) and
  [REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md) (every requirement of both briefs mapped; 0 unmapped,
  4 reconsidered with reasons).
- Phases restructured to 0–17 (D-020): new phases 3–8 and 14; Phase 2 extended with the engineering record store,
  generic and decision-set approvals and a mode-ready gate table; unstarted phases renumbered (old 3→9, 4→10, 5→11,
  6→12, 7→13, 8→15, 9→16, 10→17). Phases 1 and 2 keep their numbers.
- MVP defined as v1.5 (D-030); versions revised (D-029); new risks R-17–R-21; new invariants INV-17, INV-18.
- Decisions D-020–D-030 proposed; nothing of brief 2 is implemented before approval.

### 2026-11-22 — F1.0.2 closed: Completed with Limitations

- First feature run through AIDevWorkflow v1.0.0 itself (task `dev-tooling-f1-0-2`): spec v1 (6415e7ce) and plan v1
  (e0647c97) approved with the owner's words; DEP-1 (tool download) and DEP-3 (roadmap files out of scope) resolved.
- Implemented: `pyproject.toml`, `requirements-dev.txt` (ruff 0.17.6, mypy 1.20.2), CI `lint` job, golden CLI tests
  (8 golden files) and a script-entry smoke test, lint-only fixes (2 unused imports, 18 mypy findings), README.
- FIXING twice: once for EC-5 (not exercised), once for the independent audit's 8 Minor findings (no Critical or
  Important). Final checks on code 1705ed3d78: 147 tests on Python 3.13 and 3.9, privacy, ruff, mypy all passed.
- Not verified until the owner pushes: CI lint job, Ubuntu and Windows runs. Deviation: mypy pinned to 1.20.2
  (2.4.1 refused `python_version = 3.9`). The owner allowed publishing the spec-kit template copy (decision recorded).

### 2026-11-22 — Phase 0 approved; Phase 1 started (F1.0.1 in progress)

- Owner's approval, in their words: «موافق على كله و قالب المواصفات الخاص بيا». All recommendations needed before
  Phase 1 are Accepted ([DECISIONS.md](DECISIONS.md)); D-007 = the owner's private template `user:spec-kit` (it has a
  rules file and is their registered default). Decisions for later phases stay Proposed until their phase starts.
- F1.0.1 step 1 done: AIDevWorkflow **v1.0.0** extracted from the `v1.0.0` tag (`git archive`, working copy
  untouched) and installed at user level: canonical copy in `~/.agents/skills/ai-dev-workflow` (mode: copy), Claude
  Code and Antigravity linked to it. `install.py doctor`: no problems. `workflow.py --version`: 1.0.0.
- F1.0.1 step 2 waiting: `init --discover` (v1.0.0) found no instruction files and **no checks** for this repository
  (the detection gap Phase 1 fixes). Proposed checks from the CI workflow, both verified from the repository root:
  `python3 -m unittest discover -s tests` (141 tests OK, 44 s) and `python3 tools/prepublish_check.py` (no findings).

### 2026-11-22 — Phase 0 deliverables written

- Read the whole repository: SKILL.md, all references, the engine (3,458 lines), installer, record templates, rules
  schema, examples, docs, structure of the bilingual guide, all tests, CI.
- Reproduced two findings in a scratch repository: detected checks are de-duplicated across ecosystems (TD-03) and
  detection ignores sub-folders (TD-04).
- Wrote: CURRENT_ARCHITECTURE, GAP_ANALYSIS, TECHNICAL_DEBT, RISK_REGISTER, TARGET_ARCHITECTURE, DECISIONS,
  MASTER_ROADMAP, PROGRESS, phases 0–10, roadmap.html with roadmap-data.js.
- No production code, test, skill or guide file changed. Nothing committed.
- This Phase 0 work was done as a planning session, not as an AIDevWorkflow task: the skill is not installed on
  this machine yet and setting it up in this repository needs the owner's decisions (D-005–D-007).

### Baseline (2026-11-22)

Environment: macOS, Python 3.13.2, git 2.50.1, commit `6849eca` on `main` (clean, up to date with `origin/main`).

| Check | Command | Result |
|---|---|---|
| Unit, scenario and doc tests | `cd tests && python3 -m unittest` | **141 tests, OK** (44.2 s) |
| Privacy scan | `python3 tools/prepublish_check.py` | 65 files, no findings |
| CI | GitHub Actions `tests` (last 3 runs on `main`) | All passed |
| Install state on this machine | `install.py doctor` | No canonical copy installed |
| Tags | `git tag` | `v1.0.0` |

After the roadmap files were added (same day): `python3 -m unittest` → 141 tests OK (43.8 s); privacy scan → 86
files, no findings; `git status` shows only the new `docs/roadmap/` folder.
