# Decisions Log

Architecture and process decisions for the AIDevWorkflow roadmap, in ADR form. A decision is **Proposed** until
the project owner approves it in their own words; the approval is then quoted here with the date. Agent proposals
never become Accepted on their own (INV-01).

Status: Proposed · Accepted · Rejected · Superseded.

## Needed before Phase 1 starts

**Approved by the owner on 2026-11-22:** «موافق على كله و قالب المواصفات الخاص بيا» ("I approve all of it, and my own spec template"). The approval covers every recommendation in this table; for D-007 the owner chose their private template `user:spec-kit`. The decisions under "Needed later" stay Proposed and are confirmed at the start of their phase.

| ID | Decision | Recommendation | Main trade-off | Status |
|---|---|---|---|---|
| D-001 | Execution order | Keep the phase numbers, but start Phase 1 with a **foundations epic (E1.0)** pulled from Phase 2: module split, schema migration, locking, engine API skeleton | Phase 1 features arrive a little later; in return they land on a structure that can hold them | **Accepted** |
| D-002 | Engine structure | Stdlib package `aidw/` inside the skill folder; `workflow.py` stays as the entry point | More files; same install and CLI | **Accepted** |
| D-003 | Adapter model | Declarative JSON adapters first; executable plugins only in Phase 7 behind explicit trust | A small condition language instead of arbitrary code | **Accepted** |
| D-004 | Output parsing | Exit code + JUnit XML + SARIF + declared regex; keep the Dart parser | Tools without these formats need a regex or a wrapper | **Accepted** |
| D-005 | Self-hosting | Manage this repository's development with a **pinned install of the latest release** (now `v1.0.0`), never `--link-source`; upgrade the managing install only after a release passes its checklist | New engine features are used for our own work one release late | **Accepted** |
| D-006 | Records mode for this repository | `all`: commit task records, so the development history is visible, reviewable and resumable on any machine (the repository is public; records contain no private data, and the privacy scan runs on them) | Specs, plans and approval quotes become public | **Accepted** |
| D-007 | Spec template for our own tasks | Ask the owner: their private `user:spec-kit` template, or a new project template committed to this repository so contributors can use it | Private template keeps one personal standard; a committed one lets others follow the same process | **Accepted** — `user:spec-kit` |
| D-012 | Minimum Python version | Keep **3.9** for v1.x (stock macOS `python3` is 3.9), use a minimal TOML reader for detection; revisit at v2 | 3.9 and 3.10 are past end of life; no `tomllib` until 3.11 | **Accepted** |
| D-014 | Versioning plan (mapping superseded by D-029 on 2026-11-22) | v1.1 foundations + universal detection; v1.2 hardening; v1.3 CLI; v2.0 dashboard + approval channels + parallel work; v3 intelligence + orchestration; v4 plugins + analytics; v5 team (see MASTER_ROADMAP §5) | Major versions follow record compatibility, not marketing | **Accepted** |
| D-015 | Language of roadmap documents | English (the repository's language); the roadmap HTML has an Arabic/English switch for its interface and phase summaries; reviews with the owner happen in Arabic | Detailed task text is English only | **Accepted** |
| D-016 | Planning granularity | Phase = Epic container; each **Feature** is one AIDevWorkflow task (one spec + one plan approval); progress is counted in features done, never in estimated percentages | More approval rounds; each is small and reviewable | **Accepted** |
| D-018 | Dev tooling for the engine | ruff + mypy in CI and for contributors only; nothing added to the shipped skill | CI gains two dev dependencies | **Accepted** |

## Strategic integration (brief 2, 2026-11-22)

**Approved by the owner on 2026-11-22:** «Approved», in reply to the presentation of the merged roadmap and
decisions D-020–D-030. All eleven are Accepted.

| ID | Decision | Recommendation | Main trade-off | Status |
|---|---|---|---|---|
| D-020 | Integrated phase order | 18 phases (0–17): foundations and **core hardening stay early (P1–P2)**, then the engineering-intelligence phases (P3 profiles & depth, P4 discovery, P5 decisions, P6 modes & design, P7 specs/plans/traceability, P8 audit & evals), then CLI/dashboard (P9), git (P10), project intelligence (P11), multi-agent (P12), plugins (P13), FDE delivery (P14), analytics (P15), team (P16); release readiness (P17) applies to every release. Unstarted phases are renumbered (old P3→P9, P4→P10, P5→P11, P6→P12, P7→P13, P8→P15, P9→P16, P10→P17; feature IDs follow) | The dashboard arrives later (v3) than in the first plan; in return it shows decisions and designs from day one | **Accepted** |
| D-021 | Engineering record model | Project-level store in `.ai-dev-workflow/engineering/`: Markdown documents with labelled fields for anything people read or approve, JSON Lines written only by the engine for logs (questions), generated Markdown views; IDs `OBJ, REQ, CON, ASM, Q, ADR, CMP, DGM, EST, RES, MET` | More files in the repository; no database and no new dependency | **Accepted** |
| D-022 | Approval types | Gate · decision set · requirement baseline · delegated decision · assumption · override (ENGINEERING_INTELLIGENCE §5) | Six kinds to learn; far fewer approval interruptions | **Accepted** |
| D-023 | Delegation policy | Consequential = hard to reverse, crosses components, touches data/security/cost/public contracts, conflicts with a requirement, or marked by a profile; everything else may be delegated under a written policy the owner approves, and is listed at the next gate | The agent decides small things without asking; the owner can veto them at the next gate | **Accepted** |
| D-024 | Workflow modes | Per-mode stage sets on the declarative gate table: feature (default), full, decision, system-design, architecture-review, business-discovery, fde; mentor as an overlay (brief / standard / deep) | A bigger state machine; each mode keeps its own completion criteria | **Accepted** |
| D-025 | Adaptive depth | L0 trivial · L1 standard · L2 significant · L3 critical; proposed with reasons, shown at the first gate, user can change, enforced as required artifacts; never removes core gates | Classification can be argued; signals and warnings keep it honest | **Accepted** |
| D-026 | Domain profiles | Data only (`profile.json` + Markdown guides), built-in plus project-local overrides, `generic` as fallback; agents record applicability per topic | Content maintenance; no code execution | **Accepted** |
| D-027 | Diagrams | Mermaid first (text in git, renders on GitHub); diagrams have states, versions and hashes; PlantUML/Structurizr/SVG/PNG/HTML as optional renderers | Mermaid's C4 support is less rich than Structurizr; good enough to start | **Accepted** |
| D-028 | Measuring question and decision quality | Scenario evals A–I: deterministic record checks in CI, human rubric per release, optional model-graded rubric only with cost consent | Deterministic checks catch structure, not insight; the human rubric covers insight | **Accepted** |
| D-029 | Revised versioning | v1.1 P1 · v1.2 P2 · v1.3 P3 · v1.4 P4 · **v1.5 P5 = engineering-intelligence MVP** · v2.0 P6 (modes change records → major) · v2.1 P7 · v2.2 P8 · v3.x P9–P11 · v4.x P12–P14 · v5.x P15–P16 · P17 every release (replaces D-014's mapping) | Later items move one or two majors out | **Accepted** |
| D-030 | MVP scope | The usable first version of the new vision is **v1.5**: P1–P2 complete, plus the MVP-flagged features of P3–P5 (profiles generic/backend/mobile/frontend, depth L0–L3, question ledger, objectives and measurable requirements, ADRs with decision sets, conflict and staleness rules, decision mode, partner behaviour, Scenarios B, F, G, H, I). Deferred: other modes, HLD/LLD and diagrams (v2.0), traceability queries (v2.1), eval harness (v2.2), dashboard (v3), orchestration, plugins, FDE delivery, analytics, team | The MVP has no diagrams or dashboard; it proves the business → requirement → decision → spec → plan → evidence loop first | **Accepted** |

## ORE integration (brief 3, 2026-11-22)

**Owner's words, 2026-11-22:** «Approved all and you do the commit», in reply to the summary of the ORE integration.
Recorded as approval of the integration as presented (phase structure, design documents, the three key design
choices). **D-037 is not approved yet**: its recommendation depends on the solver research, which had not been
presented; it will be presented separately.

| ID | Decision | Recommendation | Main trade-off | Status |
|---|---|---|---|---|
| D-031 | Phase order with ORE | 20 phases (0–19): ORE foundations as **Phase 6** (v1.6, after the MVP decisions phase), ORE advanced as **Phase 10** (v2.3, after audit/evals), ORE epics in phases 9, 11, 14, 15, 16, 19; unstarted phases renumbered (6→7, 7→8, 8→9, 9→11, 10→12, 11→13, 12→14, 13→15, 14→16, 15→17, 16→18, 17→19) | Another renumbering of unstarted phases; history kept in MASTER_ROADMAP §9 | **Accepted** |
| D-032 | ORE packaging | Optional isolated package (`aidw_ore`); core and skill stay standard library; built-in exact enumerator also standard library | Two packages to maintain; the skill never gets heavier | **Accepted** |
| D-033 | Model schema `ore/1` | Declarative JSON, allow-listed expression AST, exact decimal strings as fractions, units, provenance; v1 limited to bounded integer/Boolean variables, linear and logical constraints | Narrow first version; everything in it can be proven | **Accepted** |
| D-034 | Strict optimality default | Guarantee levels G0–G3; default requirement `exact` (G2 or G3); tolerance-only results classified `FEASIBLE_NOT_PROVEN` | Fewer results called optimal; every such claim is defensible | **Accepted** |
| D-035 | Result status model | Four recorded dimensions (model, termination, solution, verification) and a verifier-computed classification | More fields; no information lost (for example timeout plus feasible solution) | **Accepted** |
| D-036 | Resource defaults | 60 s, 1 GB, 1 thread, 1 parallel run; exact search-space pre-check for enumeration; never raised automatically | Some problems need explicit higher limits | **Accepted** |
| D-037 | First optional solver | **OR-Tools CP-SAT** for integer models (G2 under stated conditions), confirmed by the spike F6.0.2; Z3 as the independent exact cross-checker and HiGHS for LP with exact certificates later (Phase 10) — ore/SOLVER_COMPARISON.md §3 | Heavy optional dependencies (numpy, pandas, protobuf); no optimality certificate; memory limited at process level | **Accepted** (final, 2026-11-22) — within `ore/1` v1 only; conditions FA-1–FA-8 in the record below |
| D-038 | Model approval | Approved model as a new approval type (hash-bound), extending D-022 | One more approval for consequential optimization decisions | **Accepted** |
| D-039 | ORE documents | Six design documents in `docs/roadmap/ore/` now (instead of 16 files); user docs in `docs/ore/` when features ship | Fewer, denser files | **Accepted** |
| D-040 | Versions with ORE | v1.6 ORE v1; v2.0 modes and design, v2.1 specs/plans/traceability, v2.2 audit/evals/registry, v2.3 ORE advanced; v3.x, v4.x, v5.x as in MASTER_ROADMAP §5; MVP stays v1.5 without ORE | ORE arrives right after the MVP, not inside it | **Accepted** |

## Needed later (decide at the start of the named phase)

| ID | Decision | Recommendation | Phase | Status |
|---|---|---|---|---|
| D-008 | Approval trust levels | A0 agent-recorded (default, unchanged) · A1 user CLI · A2 signed receipt · A3 hardware-confirmed (optional); minimum level configurable per gate; CI can require one | 2 | Proposed |
| D-009 | Dashboard technology | Python `http.server` + vanilla JS (ES modules, no build), 127.0.0.1 only, per-launch token | 3 | Proposed |
| D-010 | Human CLI | `aidev` launcher installed by `install.py` (shell script / `.cmd`) that calls the same engine with human-oriented output | 3 | Proposed |
| D-011 | Automatic orchestration | Research spike on each vendor's official headless mode, terms and costs before any build; opt-in, budget-limited, never default | 6 | Proposed |
| D-013 | Licensing and contributions | Core stays MIT; any commercial part lives in separate repositories under its own licence; adopt DCO sign-off for contributions now (lighter than a CLA, keeps future options open for MIT code) | 9 (DCO now) | Proposed |
| D-017 | Git host integration | Through the user's own `gh` CLI (and later `glab`), never storing tokens; provider interface for GitLab/Bitbucket | 4 | Proposed |
| D-019 | Release discipline | A per-release checklist (tests on 3 OSes, privacy scan, docs consistency, compatibility re-check, changelog, migration test) from v1.1 on, instead of a final hardening phase only | 1 → 10 | Proposed |

## Decision records

### D-001 — Start Phase 1 with an engine foundations epic

- **Problem.** Phase 1 adds detection, adapters, parsers and templates. Today all logic is one 3,458-line file,
  `state.json` has no schema check or migration path, and nothing locks concurrent writes.
- **Options.** (a) Phase 1 as written, restructure in Phase 2. (b) Full Phase 2 first. (c) Pull only the minimal
  foundations (split, migration, locking, API skeleton) into Phase 1.
- **Recommendation.** (c). (a) grows the debt Phase 2 must later untangle; (b) delays visible value for weeks.
- **Consequences.** Phase 1 gets one extra epic (≈ M effort); Phase 2 shrinks accordingly.

### D-005 — Self-hosting with a pinned stable engine

- **Problem.** The brief asks to develop AIDevWorkflow with AIDevWorkflow. If the managing engine were the working
  copy, an unapproved change could weaken the gates that govern its own approval (R-03).
- **Recommendation.** Install the latest release from its tag into the user-level skills folder (a copy, not a link
  to the clone). Use it for every task in this repository. After each release passes its checklist, upgrade the
  managing install with `install.py update` from the new tag.
- **Note.** The skill was not installed on the owner's Mac (`install.py doctor`: no canonical copy). Installing
  it is F1.0.1, approved with this decision on 2026-11-22.

### D-006 — Records mode for this repository

- **Problem.** `recommend_commit` would suggest `config-only` because the repository has an MIT licence (it is
  public). For this repository, the records are the product's own showcase and the owner wants to resume from any
  machine without chat history.
- **Recommendation.** `all`. The records contain specs and plans for the product itself and quotes of approvals;
  the pre-publish scan already runs over every tracked file.
- **Alternative.** `config-only` keeps tasks private but loses cross-machine resume and the public process history.

### D-012 — Python 3.9 floor

- **Problem.** Detection wants to read TOML (`pyproject.toml`, `Cargo.toml`); `tomllib` exists only from 3.11.
  Python 3.9 and 3.10 are past end of life.
- **Recommendation.** Keep 3.9 in v1.x because macOS ships `python3` 3.9 with the Command Line Tools, and the skill
  must work there out of the box. Read only the TOML keys detection needs with a small, tested reader. Revisit for
  v2.0.

### D-016 — One AIDevWorkflow task per feature

- **Problem.** A phase is too large for one spec and one plan; a single task would mean a huge spec that cannot be
  reviewed.
- **Recommendation.** Each feature (F-ID in the phase files) is one task with its own spec and plan approvals. The
  phase is closed by a phase review (summary, evidence, roadmap update) that the owner approves before the next phase.

### D-037 — First optional solver: OR-Tools CP-SAT (accepted)

**Conditionally approved by the owner on 2026-11-22:** «موافق مبدئيًا على D-037 واستخدام Google OR-Tools CP-SAT كأول
Optional Solver داخل ORE، وموافق على تحميله وتجربته عمليًا في F6.0.2 داخل بيئة Python معزولة.» ("I approve D-037 in
principle, using Google OR-Tools CP-SAT as the first optional solver in ORE, and I approve downloading it and trying it
in practice in F6.0.2 inside an isolated Python environment.") Final adoption depends on the trial meeting every
condition below; if it does not, alternatives are studied. The owner restated the principle: «No proof of optimality,
no claim of optimality.» The proof standard is never lowered to fit the solver.

| ID | Condition set by the owner |
|---|---|
| C1 | ORE is not tied to any solver: an extensible solver adapter architecture |
| C2 | The core stays light; OR-Tools dependencies are never forced on users |
| C3 | Version and dependencies compatible with Python 3.9 on macOS, Windows and Linux |
| C4 | First version limited to integer models that can be verified exactly; no silent rounding |
| C5 | Strict Optimality Mode: verify every constraint, the objective value, the best bound and the optimality gap |
| C6 | Never rely on the `OPTIMAL` status alone (CP-SAT can return it when a gap limit is reached) |
| C7 | Absolute and relative gap limits set to match the strict proof policy; numerical precision and integer overflow checked |
| C8 | Solver-reported optimality and independently verified optimality are kept distinct |
| C9 | Results compared with exhaustive enumeration on small problems with known solutions, to prove the adapter correct |
| C10 | Cases tested: infeasible, feasible but not proven optimal, timeout, resource limit, invalid model, cancellation |
| C11 | Real limits on time, memory and threads, not only solver settings where these give no sufficient guarantee |
| C12 | CP-SAT limits, unsupported problem types and the proof level it can give are documented |
| C13 | The agreed proof criteria are not relaxed because the solver cannot meet them |

Trial results and evidence: [ore/CPSAT_TRIAL.md](ore/CPSAT_TRIAL.md).

**Owner's answers after part 1 of the trial (2026-11-22), quoted:**

- «Push: Yes. Push the current branch and run the CI tests and CP-SAT trials on Linux and Windows.»
- «P-1: Yes. Add CANCELLED as a distinct termination reason. Preserve any feasible solution found before
  cancellation separately, without claiming optimality.»
- «P-2: Yes. Accept CP-SAT’s infeasibility result at G2, provided it is explicitly labelled as proven by the solver
  under the approved model, but not independently certified. Do not classify the reported conflict set as minimal
  unless minimality has been proven.»
- «P-3: Yes. Pin the tested OR-Tools version and compatible dependencies for each supported Python version. Future
  upgrades must pass compatibility, mathematical correctness, optimality and regression tests before approval.»

Additional requirements from the owner (R1–R6):

| ID | Requirement |
|---|---|
| R1 | Verify that resource limits and external watchdog enforcement work correctly on Linux and Windows |
| R2 | Keep the 46-second cold-start import documented and investigate whether it is reproducible |
| R3 | Keep OR-Tools completely optional and isolated from the Core Engine |
| R4 | Preserve the distinction between solver-proven results (G2) and independently certified results |
| R5 | Never downgrade the required proof level automatically to obtain a successful result |
| R6 | Do not mark untested platforms or unsupported mathematical models as verified |

«D-037 remains approved in principle until the cross-platform validation is complete and the final evidence is
presented for review.»

**Final approval by the owner on 2026-11-22**, after the cross-platform evidence
([ore/CPSAT_TRIAL.md](ore/CPSAT_TRIAL.md); CI `ore-cpsat-trial` and `tests` green at `3837bb2` and `6188b29`):

> «Final approval granted for D-037. Google OR-Tools CP-SAT is officially approved as the first optional ORE solver,
> strictly within the supported ore/1 v1 scope and subject to all documented verification, security, resource-control
> and optimality requirements.»

| ID | Condition of the final approval (owner's words, condensed) | Where it is enforced |
|---|---|---|
| FA-1 | Keep G2 solver-proven and G3 independently certified results distinct; never downgrade the required level automatically | STRICT_OPTIMALITY_POLICY §3 labels; verifier (F6.3.2) |
| FA-2 | macOS memory enforcement is documented as watchdog-based, not a guaranteed hard limit; a problem that requires strict OS-level memory enforcement where it is unavailable is refused | STRICT_OPTIMALITY_POLICY §5; execution controller (F6.4.1) |
| FA-3 | Both Windows controller fixes stay as permanent regression tests | `ore-cpsat-trial` workflow (also on `main` and pull requests); acceptance criteria of F2.5.2 and F6.4.1 |
| FA-4 | The tested solver version stays pinned; any upgrade is revalidated before approval | `cpsat_trial/requirements-py*.txt`; F6.2.3 |
| FA-5 | Verified platforms, Python versions and problem classes are clearly separated from untested or unsupported ones | CPSAT_TRIAL §6 support matrix |
| FA-6 | OR-Tools stays optional and isolated from the core engine | D-032; CI check in `ore-cpsat-trial` |
| FA-7 | The cold-start delay is a known observation; its suspected cause is not presented as fact | CPSAT_TRIAL §3.4 |
| FA-8 | The latest CI run is verified before closing validation tasks | Done for F6.0.2 (run of `6188b29`) |

The supported mathematical scope is **not** expanded without new validation and approval: bounded integer/Boolean
variables, linear and enforced linear constraints, one integer objective (after exact scaling).
