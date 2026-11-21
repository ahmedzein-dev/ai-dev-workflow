# Gap Analysis

Phase 0 deliverable. It compares the product brief (Phases 1–10) with what v1.0.0 already does
([CURRENT_ARCHITECTURE.md](CURRENT_ARCHITECTURE.md)).

Legend: **Exists** = implemented and tested · **Partial** = a base exists, more is needed · **Missing** · **Reconsider**
= we recommend changing or dropping it (reasons in §3).

## 1. Coverage by phase

### Phase 1 — Universal development support

| Brief item | Status | What exists | Gap |
|---|---|---|---|
| 1.1 Project detection | Partial | `detect_checks`: 11 ecosystems, evidence string per check, tool-presence flag, CI `run:` harvesting, instruction files | Root-only; no components, confidence levels, frameworks, databases, IaC or Docker; no monorepo map; detection is code in the core |
| 1.2 Technology adapters | Missing | Per-ecosystem helper functions inside the core | No adapter boundary, registry or data format |
| 1.3 Generic custom adapter | Partial | Users can already add any command (`--add-check`, `config.json` checks, `rule-scan` rules) | No way to declare detection rules, output formats or success conditions without editing Python |
| 1.4 Universal specification system | Partial | Any user template plus a rules file; private library; default template | One template per project; no template per task type; task types limited to four; plan/audit/report templates are fixed |
| 1.5 Multi-technology projects | Missing | — | No component model, no mapping from changed files to components, no per-component checks (`cwd`) |
| Output parsing | Partial | Dart analyzer parser with baselines | No standard formats (JUnit XML, SARIF, TAP); baselines only for Dart |

### Phase 2 — Core engine, security and enforcement

| Brief item | Status | What exists | Gap |
|---|---|---|---|
| 2.1 Modular core | Missing | Clear sections inside one file | One 3,458-line module; gates are an `if` chain |
| 2.2 Enforcement layers | Partial | Claude hook, preflight, scope, unattributed-change detection, `check` | No git hooks, no CI recipe for user projects, no hooks for other agents, shell writes not covered |
| 2.3 Independent approval | Missing | Agent-recorded approvals with the user's words | No user-operated channel, no approval identity, no signing, no trust level per approval |
| 2.4 Checkpoint and recovery | Partial | Atomic writes, checkpoints, preflight after resume | No locking, no fsync, no schema migration framework, no corruption repair beyond "restore from git" |
| 2.5 Evidence integrity | Partial | Fingerprint, exit code, command, time, agent, duration | No git HEAD, environment or tool versions, no stored output digest or log |
| 2.6 Security / threat model | Partial | No shell execution, secret scanning, path checks in hooks, honest limits | No written threat model; untrusted `config.json` commands run without local trust confirmation; no state tamper evidence |

### Phase 3 — CLI and dashboard

| Brief item | Status | What exists | Gap |
|---|---|---|---|
| 3.1 Professional CLI | Partial | `workflow.py` has 20 commands with `--json`; `install.py` has 7 | No short `aidev` entry point; agent-oriented wording; no user-facing `approve` flow with diff |
| 3.2–3.4 Dashboard, approval center, design | Missing | `index.html` shows the design language (EN/AR, RTL, dark mode) | Everything |
| 3.5 Shared core | Exists (by design) | All logic is in the engine | Needs a stable library API, not only a CLI |

### Phase 4 — Git, GitHub, parallel work

| Brief item | Status | What exists | Gap |
|---|---|---|---|
| 4.1 Git integration | Partial | Baselines, change sets, pre-existing work, exclusions, never commits | No branch binding, no per-task diff export, no checkpoint commits/stashes (by design, so far) |
| 4.2 Parallel tasks | Partial | One active task per checkout; docs recommend worktrees | No worktree management, no task registry across worktrees |
| 4.3 Conflict detection | Missing | — | File overlap, migration and API-contract conflicts |
| 4.4 GitHub integration | Missing | CI in this repo only | Issues, PRs, status checks |

### Phases 5–10

| Phase | Status | What exists | Main gap |
|---|---|---|---|
| 5 Project intelligence | Partial (small) | `PROJECT.md`, standards files, `discover --inspected`, user decisions per task | No project-level knowledge store, ADRs, impact reports or staleness tracking |
| 6 Multi-agent | Partial | Manual handoff tested across three agents; audit independence levels; records-only resume | No role assignment, handoff packet, agent registry or automatic orchestration |
| 7 Plugins | Missing (data extension exists) | Rules files, custom checks, templates | No plugin format, permissions, trust or management |
| 8 Analytics | Partial (data only) | `history` holds timestamped events per stage, checks, approvals and agents | No metrics computation or reports |
| 9 Team / commercial | Missing | — | Study only (see §3) |
| 10 Release readiness | Partial | CI matrix, privacy scan, docs consistency tests, validation report | No packaging/release automation, coverage, lint/type checks for the engine, or per-release checklist |

## 2. What already covers parts of the brief (do not rebuild)

- **Universal spec system (1.4)**: the template + rules design is already universal. Extend it with templates per
  task type; do not replace it.
- **Custom adapter (1.3)**: custom checks and rule scans already exist; the generic adapter should be the same
  mechanism with detection and parsing added, not a second system.
- **Explicit override recording (rule set)**: `pause --reason` already implements "skip with a record, never claim
  completion". Keep it.
- **Outcome honesty (rules)**: `compute_outcome` already enforces "no fake results"; analytics and dashboards must read
  from it, not recompute status.
- **Manual multi-agent (6.3 manual mode)**: already works and is tested across agents.
- **Metrics data (8)**: most task metrics can be derived from `history` without new collection.

## 3. Items we recommend changing, deferring or dropping

| Item | Recommendation | Why |
|---|---|---|
| Phase 1 before any core restructuring | **Pull a small "foundations" epic into the start of Phase 1** (module split without behaviour change, schema migration framework, state locking) | Adapters added to a 3,458-line file make the debt worse; new config fields need a migration path; parallel tasks and hooks already race on `ACTIVE` |
| Adapters as executable plugins (1.2, 7) | **Declarative adapters first (JSON data), executable plugins later** | Data adapters cannot run code, so they need no sandbox or trust model and are easy to review. Most ecosystems only need detection rules, commands and an output format |
| Per-tool output parsers (1.2) | **Standard formats first**: exit code, JUnit XML, SARIF, plus generic regex | Almost every test runner emits JUnit XML and most analyzers emit SARIF; one parser each covers dozens of tools |
| Long technology list as acceptance (1, 10) | **Validation matrix of ~10 representative fixtures**, not every language | Each fixture costs CI time and maintenance; representative coverage plus the generic adapter proves extensibility |
| 2.3 "independent approval" as protection | **Ship it as trust levels, not as a guarantee** | An agent running as the user can call any CLI the user can. A user-operated CLI and signed receipts raise the bar and make provenance visible; only a hardware-confirmed signature (optional) shows a human was present |
| 2.2 optional isolated execution environments | **Defer** (document how to use existing sandboxes: Codex sandbox, containers) | Building sandboxes is out of proportion; agents already provide them |
| Dashboard as a desktop app (3.5) | **Local web dashboard served by the Python standard library**, no build step | Keeps zero dependencies, works on all three OSes, no app signing or updater. Desktop wrappers can come later if needed |
| Phase 3 as one block | **Split: CLI in v1.x, dashboard in v2** | The CLI is cheap, needed for user-operated approvals (2.3), and useful without a UI |
| 4.4 GitHub integration via API tokens | **Use the user's `gh` CLI when present**, never store tokens | Reuses the user's auth, keeps credentials out of the product, works for GitHub Enterprise |
| 5.5 vector database / embeddings | **Drop unless measured need** (brief already says so) | Metadata + dependency graph + `git grep` cover the need at zero cost |
| 6.3 automatic multi-agent mode | **Research spike first, then opt-in only** | Depends on each vendor's headless mode and terms, costs money per run, and is the hardest to make reliable. Better handoff packets and role assignment deliver most of the value |
| Phase 8 as a late phase | **Basic task metrics with the dashboard (v2)**, advanced analytics later | Data already exists; the dashboard is the natural place to show it |
| Phase 9 commercial features | **Study only, no code, until v3 is stable** (brief agrees) | Licensing and contribution policy (CLA/DCO) should be decided before outside contributions grow, though |
| Phase 10 at the end | **Make release readiness continuous**: a per-release checklist from v1.1 on | Quality left to the end becomes a big-bang effort |

## 4. Capabilities the brief does not mention, which we recommend

| Capability | Why it matters | Phase |
|---|---|---|
| **Schema versioning and `migrate` command** for `config.json` and `state.json` | Every later phase changes records; without migrations, backward compatibility cannot be promised | 1 (E1.0) |
| **Local trust store for project commands** (trust-on-first-use of the `checks` block, kept outside the repo) | A cloned or pulled `config.json` can change the commands the agent will run; today nothing asks the user | 2 |
| **Tamper-evident history** (hash chain over events, verified by `check`) | Makes edits to `state.json` history detectable; honest about not preventing them | 2 |
| **Check output digests and optional logs** | An audit can then see what actually ran, not only the last line | 2 |
| **Process-tree timeouts** (kill the process group) | Today a timed-out test runner's child processes can keep running or hang the call | 2 |
| **Handoff packet** (`handoff <task>`: one generated brief with state, next step, open items, files to read) | Cuts the cost of switching agents and supports Phase 6 without orchestration | 3 / 6 |
| **Task-type profiles** (bugfix, research spike, docs, infra) that choose templates and required artifacts while keeping both approval gates | Removes friction for small and non-code tasks without weakening gates | 1 (templates), 7 (policies) |
| **Self-hosting guard** (the managing engine is a pinned install, never the working copy) | Prevents the engine under development from weakening its own gates | 0 / process |
| **Engine API (library) layer** separate from CLI printing | Needed by CLI, dashboard and orchestrator so business rules are not duplicated | 1 (E1.0) |
| **CI recipe for user projects** (`check` + `outcome` in GitHub Actions, optional status check) | Moves enforcement to a place the agent does not control | 2 / 4 |
| **Lint and type checks for the engine itself** (ruff, mypy, run in CI) | Large stdlib codebase; catches regressions cheaply; dev-only, not shipped | 1 |
