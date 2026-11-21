# Progress

The log of where the roadmap stands, updated only from recorded evidence (task reports, test runs, CI). Newest
entries first. Feature statuses live in [roadmap-data.js](roadmap-data.js); this file explains them.

## Now

| | |
|---|---|
| Phase | 1 — Foundations & universal technology support (in progress) |
| Done in Phase 1 | F1.0.1 self-hosting setup · F1.0.2 dev tooling (Completed with Limitations: CI after the owner pushes) |
| In progress | F1.0.3 (task `engine-package-f1-0-3`) in IMPLEMENTATION: spec v1 e4243a94 and plan v1 963f000b approved |
| Waiting on | Nothing from the owner right now; D-037 (first optional solver) will be presented after the solver research |
| Next action | Implement F1.0.3; finish the solver comparison |
| Blockers | None |

## Phase progress

Counted in features (F-IDs); `done` only with recorded evidence. Numbering after the ORE integration (D-031);
history in MASTER_ROADMAP §9.

| Phase | Features done / total | Status |
|---|---|---|
| 0 | 14 / 15 | Nearly done (F0.4.2 solver comparison in progress) |
| 1 | 2 / 25 | In progress |
| 2 | 0 / 20 | Planned |
| 3 | 0 / 12 | Planned (MVP) |
| 4 | 0 / 12 | Planned (MVP) |
| 5 | 0 / 12 | Planned (MVP complete) |
| 6 | 0 / 19 | Planned (ORE v1) |
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
