# Progress

The log of where the roadmap stands, updated only from recorded evidence (task reports, test runs, CI). Newest
entries first. Feature statuses live in [roadmap-data.js](roadmap-data.js); this file explains them.

## Now

| | |
|---|---|
| Phase | 1 — Foundations & universal technology support (in progress) |
| Done in Phase 1 | F1.0.1 self-hosting setup · F1.0.2 dev tooling · F1.0.3 engine package · F1.0.4 engine API (closed Completed with Limitations; CI 7/7 at `fa6a676`) |
| Security status | TD-25 closed — Completed with Limitations; v1.0.1 published and verified, user-level installation verified, fix integrated into `main`. F-9 remains Deferred; TD-29 and TD-30 remain open |
| Roadmap status | Final revised Master Roadmap approved by the owner on 2026-11-23; D-041–D-045 accepted with their recorded clarifications. Evaluation outcomes remain unproven |
| Next action | Prepare F1.0.5 (state schema, migration, locking) through the normal task workflow when separately initiated; implementation has not started. E1.7 follows it in Phase 1 |
| Blockers | None |

## Phase progress

Counted in features (F-IDs); `done` only with recorded evidence. Numbering after the ORE integration (D-031);
history in MASTER_ROADMAP §9.

| Phase | Features done / total | Status |
|---|---|---|
| 0 | 15 / 15 | Done |
| 1 | 4 / 29 | In progress |
| 2 | 0 / 20 | Planned |
| 3 | 0 / 13 | Planned (MVP) |
| 4 | 0 / 13 | Planned (MVP) |
| 5 | 0 / 14 | Planned (MVP complete) |
| 6 | 1 / 20 | Planned (ORE v1); F6.0.2 done early for D-037 |
| 7 | 0 / 15 | Planned |
| 8 | 0 / 8 | Planned |
| 9 | 0 / 8 | Planned |
| 10 | 0 / 11 | Planned (ORE advanced) |
| 11 | 0 / 18 | Planned |
| 12 | 0 / 10 | Planned |
| 13 | 0 / 6 | Planned |
| 14 | 0 / 10 | Planned |
| 15 | 0 / 5 | Planned |
| 16 | 0 / 7 | Planned |
| 17 | 0 / 6 | Planned |
| 18 | 0 / 3 | Future (study) |
| 19 | 0 / 8 | Planned (checklist from v1.1) |

## Log

### 2026-11-23 — Final Master Roadmap approved

- Owner explicitly approved the revised roadmap baseline: **20 phases**, **239 features**, **84 MVP features** and
  **20 completed features**, together with D-041–D-045 and their recorded limits. The D-044 evaluation framework is
  approved; product-market fit, competitive superiority and usability improvement remain unproven.
- Owner accepted partial Arabic localization for this version and authorized a roadmap-only commit and push to
  `phase-1/foundations`. Remaining English roadmap descriptions are identified in the Arabic interface and tracked
  for scoping under the existing documentation refresh F19.5.1, without a new feature or count change.
- No implementation, merge into `main` or change to the stable v1.0.1 release is authorized by this approval.

### 2026-11-23 — D-044 framework approved; visual roadmap corrections authorized

- Owner approved D-044's proportional minimum evidence per gate, baseline and UX scenario timing, while preserving
  the earlier gates-only approval history. This approves an evaluation framework, not measured improvement,
  product-market fit or competitive superiority. Missing essential evidence is insufficient or blocked; exceptions
  record rationale, consequences and follow-up without claiming validation was completed.
- Owner authorized corrections to undefined decision dates, D-044 presentation, Arabic fixed labels and release
  descriptions, and RTL progress values. Full translation of authored feature descriptions remains outside this
  focused correction and is labelled as original English in the Arabic view.
- The full Master Roadmap still awaits final approval; commit, push and F1.0.5 implementation are not authorized.

### 2026-11-23 — Product experience decisions approved with conditions

- Owner approved D-042, D-043 and D-045 with the wording and limits in DECISIONS.md. Acceptance of a material
  usability regression records rationale, risks and follow-up, and cannot waive mandatory engineering guarantees.
  Standard resolves to one recorded L1 or L2 level under the existing policy; depth changes below mandatory profile
  minimums or around required gates/checks are refused with an explanation. Complexity review scales with impact
  and has no invented numeric quota.
- Owner approved retaining 13 net-new feature IDs and the five consolidations from the previous draft: **239**
  features across **20** phases. F11.5.3 versus F11.5.2 and F17.6.1 versus F17.1.1 are flagged for review when their
  detailed specifications are prepared; neither pair is consolidated now. F3.3.3 (an existing feature) is made P0
  and MVP-required so the Quick/Standard/Deep presentation cannot precede mandatory profile-minimum enforcement.
- This is approval of these decisions and the strategic direction, not final approval of the Master Roadmap, a
  commit/push authorization or permission to start F1.0.5.

### 2026-11-23 — TD-25 closed; brief-4 roadmap draft revised for owner review

- TD-25 closed through the official workflow as **Completed with Limitations** (`eb49f62` on
  `phase-1/foundations`). The v1.0.1 tag/release is published at `6a7cba0`, the security fix is integrated into
  remote `main` (`a964cad`), and the accessible user-level v1.0.1 installation was verified. F-9 stays Deferred;
  TD-29 and TD-30 stay open. Unreleased development on `main` and `phase-1/foundations` is distinct from the
  stable installed release.
- Owner approved five corrections to the uncommitted brief-4 draft, **not** final roadmap approval or D-042,
  D-043 and D-045. Consolidated five proposed IDs into existing work: F3.4.3→F3.4.1,
  F4.5.2→F4.5.1, F9.2.4→F9.2.1, F16.8.1→F16.4.1 and F19.8.1→F19.1.1. The measurable
  acceptance criteria and evidence remain. Net addition: **13** feature IDs, from 226 to **239** total;
  no new phase. UX-E starts in Phase 14, and the Gate A scope is limited to shipped v1.5 capabilities.
- No software feature was started by this roadmap revision. F1.0.5 remains planned.

### 2026-11-22 — Brief 4 integrated: Powerful Inside. Simple Outside.; competitive validation

- Owner: «I approve adding Competitive Validation & Product-Market Fit to the AIDevWorkflow Master Roadmap … a
  permanent, non-negotiable product principle: Powerful Inside. Simple Outside.» This is a roadmap and design update
  only; no software feature was implemented.
- Initial uncommitted draft integrated the brief into the existing roadmap, with no new phase or parallel plan:
  - new design document PRODUCT_EXPERIENCE.md (capability design, like ENGINEERING_INTELLIGENCE.md);
  - INV-23; decisions D-041–D-045 (D-041 and the D-044 gates Accepted, the rest Proposed);
  - risks R-27 and R-28; RTM section B4;
  - 18 proposed IDs initially; five were consolidated in the 2026-11-23 revision above. The current draft has
    13 net new IDs: E1.7 (F1.7.1–F1.7.4), F3.3.4, F4.1.4, F5.5.2, F5.6.2 (Gate A), F6.6.3 (Gate B),
    F11.0.1 (Gate C), F11.5.3, F14.7.1 and F17.6.1;
  - usability register UXR-1–UXR-4, seeded from observed friction in tasks `security-td-25` and
    `engine-api-f1-0-4`.
- Initial effort estimate: about +5–7 weeks over the whole roadmap (Phase 1 +1–1.5 weeks), to be revisited at
  feature planning and each validation gate. Consolidating IDs does not remove their evaluation work or justify
  reducing this estimate mechanically. TD-25 was paused only for these document edits; its scope was unchanged.

### 2026-11-22 — F1.0.4 closed (Completed with Limitations); TD-25 task opened

- Owner: «Approved. Close F1.0.4 with the status Completed with Limitations.» Closed with the engine's `close`
  after `outcome` allowed at most Completed with Limitations. The only reason it is not Completed is the accepted
  Important finding F-7, recorded as **TD-25** (pre-existing, security-sensitive).
- Evidence (tested commit `fa6a676`, code fingerprint `23f78e988f`):
  - CI run 45005422565: lint + Linux, Windows, macOS × Python 3.9/3.13, 7/7 passed;
  - the records-only commit `4bb3cd9` passed too (run 45006054918, 7/7);
  - independent audit in three rounds (cea2e9f, b2f5b8e, fa6a676), final verdict GO;
  - 27 refusal scenarios, the late-refusal output and the public signatures pinned from the pre-refactor engine
    `5a7576a`, passing on both engines with Python 3.13 and 3.9;
  - the 9 pre-existing golden files are byte-identical; 173 tests.
- Records: `.ai-dev-workflow/tasks/engine-api-f1-0-4/` (spec v1 `303f07fe`, plan v1 `4e4b2a66`, verification,
  audit F-1–F-19, report).
- Owner's next priority: TD-25 before F1.0.5, through Discovery → Specification → Approval → Planning → Approval,
  with no implementation before approval. TD-24 and TD-26 stay separate tracked defects.

### 2026-11-22 — F1.0.4 spec and plan revised after the owner's review

- Owner approved the three technical decisions in principle (single `aidw/api.py`, keyword parameters, plain
  dictionaries) and asked for seven points before final approval. Addressed in spec `303f07fe` and plan `4e4b2a66`:
  scope JSON projection, `preflight --json` behaviour pinned (TD-24 recorded, not fixed), no hidden state with a
  two-repository test, refusal golden file, signature-preserving wrappers for three names, internal API only, closed
  F1.0.2/F1.0.3 reports untouched.

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
