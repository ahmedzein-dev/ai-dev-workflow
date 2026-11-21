# Target Architecture (proposal, needs approval)

Phase 0 deliverable. It refines the architecture in the brief against the actual code. Nothing here is built yet;
decisions marked **D-nnn** are listed in [DECISIONS.md](DECISIONS.md) for approval.

## 1. Guiding constraints

1. **Simplest structure that meets the next two phases.** No services, queues or external databases.
2. **Standard library only for the skill.** Optional components (dashboard) may not add a mandatory install step
   for skill users (INV-12, INV-14).
3. **Records in the repository stay the single source of truth.** Anything else (indexes, caches) is derived and
   can be rebuilt.
4. **One engine, many front ends.** Skill instructions, CLI, dashboard and orchestrator all call the same engine
   API; none re-implements a gate.
5. **Extension by data before extension by code.** Adapters, templates, task types and policies are declarative
   first. Executable plugins come later, behind explicit trust.

## 2. Target layers

```
 Front ends      SKILL.md + references   ·   aidev CLI (human)   ·   workflow.py CLI (agent)   ·   Dashboard (optional, P3)
                        │                         │                        │                         │
 Engine API      aidw.api  — functions that take a repo + arguments and return data or raise WorkflowError
                        │
 Core            machine (stages, gate table) · approvals · evidence · outcome · scope · records (Markdown model,
                 spec/plan/audit/report parsers) · state store (schema, migrate, lock, events) · policy
                        │
 Registries      technology adapters (declarative JSON) · output parsers (exit, JUnit, SARIF, regex, dart)
                 · agent adapters (capabilities, hooks) · task types / templates · (P7) plugins
                        │
 Infrastructure  fsutil (atomic write, fsync, lock) · git · secrets · process runner (process groups, streaming)
                        │
 Storage         <repo>/.ai-dev-workflow/  (source of truth)   ·   ~/.ai-dev-workflow/ (library, trust store,
                 optional derived index for the dashboard)
 Optional (later) orchestrator (P6) · project intelligence (P5) · git provider integrations (P4) · analytics (P8)
```

The core never imports a front end, an adapter implementation or a provider. Front ends never write records
directly.

## 3. Package layout (D-002)

```
skills/ai-dev-workflow/scripts/
├── workflow.py          # unchanged path and CLI; now a thin entry point (keeps every existing install working)
├── install.py
└── aidw/                # stdlib-only package, copied with the skill folder
    ├── __init__.py      # __version__ (single source)
    ├── api.py           # engine API used by every front end
    ├── core/            # machine.py, approvals.py, evidence.py, outcome.py, scope.py, policy.py
    ├── records/         # markdown.py (Doc), spec.py, plan.py, deps.py, audit.py, report.py
    ├── store/           # state.py (load/save/validate), migrate.py, lock.py, events.py
    ├── adapters/        # registry.py, detect.py, parsers/{exitcode,junit,sarif,regex,dart}.py
    │   └── builtin/     # *.json declarative adapters (node, python, dart-flutter, go, rust, jvm, dotnet, …)
    ├── agents/          # capability profiles; hooks/claude.py (+ others when vendors support them)
    ├── infra/           # fsutil.py, gitutil.py, secrets.py, process.py
    └── cli/             # argparse wiring and printing only
```

The split is done in two steps: a mechanical move with no behaviour change (verified by the full test suite plus
golden CLI outputs), then targeted refactors (gate table, API extraction).

## 4. Key design choices and alternatives

### 4.1 Engine structure

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| Keep one file | Simplest install; no import paths | 3,458 lines and growing; review and testing harder | Rejected beyond v1.0 |
| **Stdlib package inside the skill folder** | Same install (folder copy), clear modules, testable units | Imports must work when the folder is copied anywhere; keep `workflow.py` as entry | **Recommended** |
| Separate PyPI package + skill shim | Versioned library, reusable | Forces `pip install`; breaks "skill works alone" and cloud sandboxes | Rejected for the core |

### 4.2 Technology support

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| Keep hard-coded detection | Works today | Every technology needs a core change (TD-05) | Rejected |
| Python adapter classes | Full power | Code execution → trust problem; harder for users to write | Later, as executable plugins (P7) |
| **Declarative adapters (JSON) + standard output formats** | No code execution; reviewable; users add technologies without Python; JUnit/SARIF cover most tools | Expressiveness limited to a small condition language | **Recommended** (D-003, D-004) |

Adapter sketch (illustrative, finalized in Phase 1 design):

```json
{
  "schema": 1, "id": "node", "name": "Node.js",
  "detect": {"files": ["package.json"], "confidence": "high"},
  "frameworks": [{"id": "nextjs", "if": {"json_has": ["package.json", "dependencies.next"]}}],
  "package_managers": [{"id": "pnpm", "if": {"file": "pnpm-lock.yaml"}, "run": "pnpm"},
                       {"id": "npm", "default": true, "run": "npm run"}],
  "checks": [{"id": "test", "if": {"json_has": ["package.json", "scripts.test"]}, "command": "{run} test",
              "format": "exit-code", "required": true, "explain": "Runs the automated tests."}],
  "manifests": [{"file": "package.json", "reader": "json-keys",
                 "keys": ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies"]}]
}
```

Detection produces **components**: `{path, technologies, frameworks, package manager, evidence[], confidence}`.
Check IDs become component-scoped (`web:test`), and checks gain an optional `cwd`.

### 4.3 Output parsing

| Format | Covers | Plan |
|---|---|---|
| Exit code | Everything | Exists |
| JUnit XML | pytest, Jest/Vitest, Go (via gotestsum), JUnit/Gradle/Maven, .NET (trx→junit), PHPUnit, RSpec, Rust (cargo2junit/nextest) | P1 |
| SARIF | ESLint, Semgrep, CodeQL, ruff, Bandit, many security scanners | P1 |
| Regex (declared in adapter) | Anything with line-based output | P1 |
| Dart analyzer | Flutter/Dart (existing) | Kept |

Baselines (new-vs-existing issues) work for any structured parser, not only Dart.

### 4.4 State store and integrity

| Concern | Choice | Alternative considered |
|---|---|---|
| Format | Keep `state.json` per task; move history to append-only `events.jsonl` with a hash chain | SQLite in the repo (binary, merge-unfriendly) — rejected |
| Concurrency | Lock file per task (`O_CREAT|O_EXCL`, timeout, stale-lock detection) | OS file locks (`fcntl`/`msvcrt`) — different per OS; kept as an option inside `lock.py` |
| Durability | Atomic replace + fsync of file and directory | — |
| Versioning | `schema` checked on load; `migrate` with dry run and backup | Silent upgrade on read — rejected (surprises, merge noise) |
| Cross-project view | Optional derived index in `~/.ai-dev-workflow/index.db` (stdlib `sqlite3`) for the dashboard, rebuildable from records | A server database — rejected |

### 4.5 Enforcement layers (prevention vs detection)

| Layer | Type | Agent-independent? | Phase |
|---|---|---|---|
| Hard rules in SKILL.md | Instruction | No | Exists |
| Engine gates (`transition`, `approve`, `close`) | Prevention for state changes | Yes | Exists |
| Agent hooks (Claude now; others where vendors provide scoped hooks) | Prevention for edit tools | No | Exists / P2 |
| `preflight` + unattributed changes | Detection | Yes | Exists |
| Local trust store for check commands | Prevention (engine runs only confirmed commands) | Yes | P2 |
| Git pre-commit hook (opt-in) | Blocks the **commit**, not the edit | Yes | P2 |
| CI check (`check` + `outcome` + approval trust level) | Detection outside the agent's control | Yes | P2/P4 |
| Hash-chained events | Tamper evidence | Yes | P2 |
| Optional isolated execution | Prevention | Depends on agent sandbox | Documented only |

### 4.6 Approval trust levels (D-008)

| Level | Channel | Shows | Can an agent with the user's permissions fake it? |
|---|---|---|---|
| A0 `agent-recorded` | Agent runs `approve --evidence "<user words>"` (today) | The quote | Yes |
| A1 `user-cli` | User runs `aidev approve <task> spec` in their own terminal; sees version, hash, diff | Interactive confirmation | Yes, technically (it can run the same command); visible in history as a separate channel |
| A2 `signed` | Approval receipt signed with the user's SSH/GPG key (`ssh-keygen -Y sign`, as git does) | Signature verifiable in CI | Yes if the key is unlocked in an agent-reachable keyring; no if a passphrase is required per use |
| A3 `hardware` (optional) | Signed with a security key that requires a touch (`sk-ed25519`) | Human presence | No |

Projects choose a minimum level per gate (default A0, unchanged behaviour). CI can require a level.

### 4.7 Front ends

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **Local web dashboard on Python `http.server` + vanilla JS/ES modules, no build step** | Zero dependencies, cross-platform, same engine in-process, RTL via CSS | No framework conveniences; careful security (token, Origin checks) | **Recommended** (D-009) |
| FastAPI/Flask + React | Rich ecosystem | Dependencies and a build chain for every user | Rejected for v2 |
| Electron / Tauri desktop app | Native feel | Signing, updates, size, a second language (Tauri: Rust) | Revisit after v2 if users ask |
| Terminal UI | Fast | Weak for diffs, Arabic/RTL and reading long specs | Not a replacement; the CLI covers terminal use |

The `aidev` CLI is a human-oriented front for the same engine: short commands, readable output, interactive approval
with diff (D-007).

### 4.8 Agents and orchestration

- **Agent adapters** declare capabilities (invocation, session id, hooks, resume, structured output, headless mode,
  cost reporting) with evidence labels, like `docs/compatibility.md` today.
- **Manual multi-agent** improvements first: role assignment in the task (`implementer`, `auditor`, …), an
  auditor-must-differ policy, and a generated handoff packet.
- **Automatic orchestration** is a separate optional module that drives agents through their official headless
  modes, only after a research spike confirms terms, costs and reliability (D-011). It uses the same engine API and
  can never record human approvals.

## 5. Migration and backward compatibility plan

| Step | Change | Old records | Old installs | Rollback |
|---|---|---|---|---|
| M1 (v1.1) | Package split behind `workflow.py` | Unchanged | `workflow.py` path unchanged; project copies refresh with `install.py update --project` | Reinstall v1.0.0 tag |
| M2 (v1.1) | `state.schema` checked; `migrate` command (dry run, backup); locking | Read as before | — | Backups in `tasks/<task>/.migrate-backup/` |
| M3 (v1.2) | `config.json` schema 2: components, `cwd`, adapters, task types, templates per type | Schema 1 still read; schema 2 written only after the user confirms `migrate` or `init --update` | A v1.0 engine refuses schema 2 with its existing "unsupported schema" message (fails closed) | `migrate --rollback` restores the backup |
| M4 (v1.3) | Evidence v2 (HEAD, environment, tool versions, output digest); `events.jsonl` | Old evidence stays valid but is labelled "v1 evidence"; history migrated on the task's next write | — | Backup |
| M5 (v2.0) | Approval channels and trust levels; dashboard; any change old engines cannot read safely | v1 records readable; migration on resume | Major version because records written by v2 are not readable by v1 | Backup + documented downgrade |

Policy: an engine reads every older record format of its major version and the previous major; it never rewrites
records without an explicit user action, except appending events to an active task.

## 6. What stays out of the core

Project type, language, framework, agent vendor, the dashboard, GitHub or any git host, cloud providers and
commercial features. The core knows only: stages, gates, approvals, evidence, scope, outcome and records.

## 7. Overall architecture after the three integrations (brief 3 §24, simplified)

One engine, logical components, no services. Optional modules install separately and never become mandatory for the
skill.

```
AIDevWorkflow
├── Skill · aidev CLI · dashboard (P11)                       front ends; no business rules
├── Workflow core (aidw/)                                      standard library only
│   ├── state machine + gate table per mode (P2, P7)
│   ├── approvals: gate · decision set · requirement baseline · model · delegated · assumption (P2, P5, P6)
│   ├── policies, evidence, event log, trust store (P2)
│   └── engineering record store + trace graph (P2, P8)
├── Engineering intelligence (data + instructions)            profiles, depth, discovery, questions (P3, P4)
├── Engineering decision framework                            ADRs, trade-offs, conflict and staleness rules (P5)
├── ORE (aidw_ore/, optional)                                  modeling, exact solving, verification, Pareto,
│                                                              scenarios, evidence (P6, P10)
├── System design & architecture                              modes, HLD/LLD, estimates, failure analysis, diagrams (P7)
├── Specs, plans & traceability                               (P8)
├── Verification, audit & evals + performance registry        (P9)
├── Git & parallel work (P12) · project intelligence (P13)
├── Multi-agent orchestrator incl. ORE allocation (P14, optional)
├── Plugins: technology adapters, profiles, solver adapters (P15)
├── Forward deployed engineering & delivery (P16)
├── Analytics & business impact (P17) · team (P18, study)
└── Release readiness (P19, every release)
```

Dependency direction: front ends → core API → core modules → registries (adapters, profiles, solvers) → infrastructure.
ORE depends on the core (records, approvals, trust store, process runner, events); the core never depends on ORE.
