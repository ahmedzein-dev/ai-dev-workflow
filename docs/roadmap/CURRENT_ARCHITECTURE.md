# Current Architecture (baseline: v1.0.0 + Unreleased, commit `6849eca`)

Phase 0 deliverable. It describes the system as it is, so later phases can be measured against it. Code
references point to [`workflow.py`](../../skills/ai-dev-workflow/scripts/workflow.py) unless stated otherwise.

## 1. Shape of the system

```
Developer ── invokes ──▶ Agent (Claude Code · Codex · Gemini CLI · Antigravity)
                              │ reads SKILL.md + references/*.md (instructions)
                              ▼
                     scripts/workflow.py  (engine, single file, 3,458 lines, stdlib only)
                              │ reads/writes
                              ▼
   <project>/.ai-dev-workflow/  config.json · PROJECT.md · templates/ · ACTIVE · tasks/<task>/…
                              │ uses
                              ▼
                     git (status, ls-files, hash-object, diff, show)  +  project commands (checks)

Claude Code only: SKILL.md frontmatter hooks ──▶ workflow.py hook claude-pre-edit / claude-prompt
Installer: scripts/install.py (441 lines) ──▶ ~/.agents/skills (canonical) + links/copies per agent
```

There are three layers, and only the engine is code:

| Layer | Files | Role |
|---|---|---|
| Instructions | `SKILL.md` (166 lines), `references/*.md` (7 files, ~690 lines) | Hard rules, stage guidance, what the agent must do and never do |
| Engine | `scripts/workflow.py` | Guarded state machine, approvals, checks, evidence, outcome caps, hooks, setup discovery |
| Distribution | `scripts/install.py`, `agents/openai.yaml` | Install/link/copy per agent, doctor, private template library |

Supporting assets: record templates (`assets/templates/*.md`), the rules JSON Schema (`assets/rules.schema.json`),
the example config. Docs: `README.md`, `docs/*.md` (6 files), a hand-written bilingual guide `index.html`
(1,296 lines), `examples/` (template + rules, starting configs, a complete sample task).

## 2. Engine internals (by section of `workflow.py`)

| Section | Lines | Responsibilities | Notes |
|---|---|---|---|
| Constants | 30–113 | Stages, task types, outcomes, dependency classes, plan/report sections, instruction-file candidates, vague words, NEXT/REFERENCE maps | Stage list and gate texts are hard-coded |
| Basics | 126–185 | Time, text normalization, SHA-256, atomic `write_text` (tmp + `os.replace`), JSON I/O, read-only chmod | No file locking, no fsync |
| Secrets | 189–245 | 11 secret patterns + assignment detector, `redact`, `assert_no_secrets` | Shared with `tools/prepublish_check.py` |
| Git | 249–408 | Repo discovery, worktree changes, **code fingerprint** (SHA-256 over path+blob of every non-ignored file), baselines, change sets (task vs pre-existing work) | Fingerprint is commit-independent by design |
| Markdown model | 412–737 | `Doc` parser (headings, bold labels, ID items, tables, code fences, comments), `TemplateInfo`, structure/placeholder/marker/ID checks | Custom parser, no Markdown library |
| Project config | 741–805 | `config.json` (schema 1), rules file (schema 1), private library location | Strict `schema == 1` check |
| Task state | 809–909 | `state.json` load/validate/save, history, checkpoints, `ACTIVE` pointer, task activation | `state.schema` is written but never checked on load |
| Spec checks | 913–1103 | Mandatory / judgment / advisory rules from the template's rules file; plan check against the fixed plan template | Rule targets: `label:`, `section:`, `ids:`, `table:` |
| Other records | 1108–1252 | Parsers for dependencies, acceptance matrix, audit findings, report | Fixed record formats |
| Approvals & gates | 1257–1422 | Hash-bound approvals, snapshot integrity, plan↔spec binding, check freshness, `forward_problems` (one `if` branch per target stage), `transition` | Gate logic is imperative, not data-driven |
| Checks | 1427–1661 | Command execution without a shell (`shlex` + `shutil.which`), Dart analyzer parser + baselines, built-ins (`json-key-parity`, `rule-scan`, `manifest-diff`), verification block regeneration | One output parser (Dart) |
| Outcome | 1666–1726 | Highest allowed final status from evidence, approvals, matrix, checks, audit findings | Well-defined capping rules |
| Setup discovery | 1731–2157 | Technology detection and check recommendations (Dart/Flutter, Node, Python, Go, Rust, Gradle/Android, Maven, .NET, Ruby, Swift, Makefile), CI command harvesting, template proposal, records-commit recommendation, git-exclude handling | Hard-coded per technology, repository root only |
| Commands | 2162–3155 | 20 CLI commands (`init`, `new`, `status`, `discover`, `spec-check`, `review`, `plan-check`, `approve`, `stage`, `resume`, `pause`, `preflight`, `step`, `run`, `scope`, `decision`, `check`, `outcome`, `close`, `hook`) | argparse; `--json` on most read commands |
| Hooks | 3160–3294 | Claude Code `PreToolUse` edit gate and `UserPromptSubmit` status reminder; optional decision log | Fail-open without a task, fail-closed inside one |
| CLI | 3299–3458 | Parser and `main` | Exit codes: 0 ok, 1 refusal, 3 environment |

## 3. The state machine

```
DISCOVERY → DEPENDENCIES → SPECIFICATION → SPEC_APPROVAL ─(approve spec)→ PLANNING → PLAN_APPROVAL
   ─(approve plan)→ IMPLEMENTATION → TESTING ⇄ FIXING → AUDIT → FINAL_REPORT → closed
```

- Task status is `active | paused | closed`; stage is one of 11.
- Forward moves are one stage at a time (TESTING → AUDIT allowed directly); PLANNING and IMPLEMENTATION are entered
  **only** through `approve`. Backward moves always allowed with `--reason`. FINAL_REPORT before AUDIT needs a
  reason and caps the outcome.
- Blocking dependencies (`dependencies.md`, gate `spec|plan|implementation|completion`) hold a gate at any stage.
- An explicit user override is recorded by `pause --reason`; the stage and approvals stay unchanged, so nothing
  skipped is ever shown as complete.
- One active task per checkout (`.ai-dev-workflow/ACTIVE`, never committed); activating another pauses the first.

## 4. Trust model as implemented

| Guarantee | How | Strength |
|---|---|---|
| Stage order and prerequisites | `transition` + `forward_problems` | Enforced for every agent that uses the engine |
| Approval bound to an exact version | SHA-256 of normalized text, read-only snapshot, plan bound to spec hash | Enforced; tampering with both record and snapshot is not detected |
| Approval came from the user | Agent passes the user's words as `--evidence` | **Asserted by the agent** (documented honestly) |
| No code before approved plan | Claude Code: skill-scoped `PreToolUse` hook on edit tools. Others: instructions + later detection (`status`, `check`, `preflight` "unattributed changes") | Prevention in Claude Code edit tools only; shell writes bypass it |
| Evidence is fresh | Check results carry the code fingerprint; stale/missing evidence blocks AUDIT and caps the outcome | Enforced |
| Honest final status | `outcome` computes the cap; `close` refuses a higher claim | Enforced |
| No secrets in records | `assert_no_secrets` on every save; `check`/`preflight` rescan | Pattern-based, best effort |
| Explicit start only | Claude `disable-model-invocation`, Codex `allow_implicit_invocation: false`, first hard rule, `new --invocation` must name the skill | Agent settings where available; the engine check is a speed bump |
| Pre-existing work preserved | Baseline of dirty files at task start; `scope` separates task vs pre-existing changes | Detection, not prevention |

## 5. Existing capabilities inventory

Everything below exists and is tested (141 tests). Later phases must keep it and must not rebuild it.

| Area | Capability | Where |
|---|---|---|
| Activation | Manual-only per agent; refusal to create tasks without an invoking message | SKILL.md, `openai.yaml`, `cmd_new` |
| Setup | Guided `init --discover` (standards files, template proposal, checks with explanations and tool presence, CI commands, records-commit options with trade-offs); `init`, `init --update` | `discover_project`, `cmd_init`, `update_setup` |
| Templates | Project-owned spec template copied into the repo; private library with default template; rules files with mandatory / judgment / advisory classes; no numeric limits | `install.py add-template`, `spec_check`, `rules.schema.json` |
| Spec quality | Structure, placeholders, unresolved markers, ID order, regex formats, complete tables, content-required, vague-word / inspection / coverage-map detectors, dismissals with reasons, advisory questions | `spec_check`, `cmd_review` |
| Dependencies | Typed, classified, gated dependencies; ready-to-send backend messages required for blocking backend items; BLOCKED status line | `parse_dependencies`, `status_line` |
| Approvals | Hash-bound, versioned, frozen snapshots, renewal on change, fast path (both approvals in one message, still two records) | `cmd_approve`, `approval_status` |
| Implementation control | Preflight per session, step progress with automatic file attribution, unattributed-change detection, checkpoints | `cmd_preflight`, `cmd_step` |
| Evidence | Engine-run checks, exit codes, redacted summaries, fingerprints, staleness, blocked / not-applicable with reasons, analyzer baselines, ad-hoc checks | `cmd_run`, `check_freshness` |
| Built-in checks | Translation key parity, project rule scan (new violations only), new-dependency approval | `builtin_check` |
| Audit | Independence levels, nine dimensions, severity × disposition rules (Deferred only Minor; Accepted needs user words) | `parse_audit`, `references/audit-and-report.md` |
| Outcome | Evidence-derived cap; accepted Critical never Completed; accepted Important → Completed with Limitations | `compute_outcome`, `cmd_close` |
| Scope safety | Task vs pre-existing changes, exclusions with reasons, project skill copies ignored | `change_set`, `cmd_scope` |
| Records & privacy | Three commit modes via local git exclude, re-applied in new clones; secret refusal on save | `apply_commit_mode`, `ensure_commit_mode` |
| Cross-agent | Records-only handoff, resume, per-agent invocation docs, tested in Claude Code, Codex, Gemini CLI | `cmd_resume`, `docs/compatibility.md` |
| Hooks | Claude Code edit gate scoped to the active task and session; prompt reminder; fail-closed inside a task | `gate_decision`, `hook_claude_pre_edit` |
| Distribution | Canonical copy + links/copies, drift detection, project installs, uninstall, doctor | `install.py` |
| Quality | 141 unit/scenario/doc-consistency tests; CI on Ubuntu, macOS, Windows × Python 3.9 / 3.13; pre-publish privacy scan | `tests/`, `.github/workflows/tests.yml`, `tools/prepublish_check.py` |
| Docs | README, six guides, bilingual HTML guide (EN/AR, RTL, dark mode), validation and compatibility reports with evidence labels | `docs/`, `index.html` |

## 6. Technology-specific parts (relevant to Phase 1)

The core lifecycle is already technology-agnostic: specs come from the user's template, checks are arbitrary
commands. The coupling is concentrated in four places:

| Place | Coupling | Effect |
|---|---|---|
| `detect_checks` and helpers (L1806–1979) | One hard-coded function per ecosystem; only files at the **repository root** are inspected (`repo / "pubspec.yaml"`, `repo / "go.mod"`, …) | Monorepos and sub-projects are not detected; adding a technology means editing the core |
| Output parsing (`parse_analyzer`, L1427–1444; `--baseline`, `fail_on`) | Only the Dart analyzer format; baselines are allowed only for `parser: dart-analyzer` | No new-vs-existing separation for any other linter or analyzer |
| `manifest_dependencies` (L1518–1545) | `package.json`, `pubspec.yaml`, `requirements*.txt` only | `manifest-diff` cannot cover Go, Rust, Maven, Gradle, .NET, Composer, Gemfile, pyproject |
| Checks run at the repository root | No `cwd` per check | A monorepo component's command must be wrapped by hand |
| Smaller items | `TRANSLATION_DIRS` lean toward Flutter/JS layouts; task types limited to `feature, bugfix, enhancement, refactor`; examples cover Flutter and Node | Cosmetic to moderate |

The instructions (SKILL.md, references) contain almost no technology-specific wording (one mention each of
mobile-oriented dependency examples).

## 7. Strengths to preserve

1. **Honesty by construction.** Evidence-capped outcomes, stale-evidence rejection, explicit limits in the docs
   ("cannot make self-approval technically impossible"). This is the product's core differentiator.
2. **Zero dependencies, single folder.** Standard library only; the skill folder is the product. Installation works
   in cloud sandboxes and on Windows.
3. **Records in the repository.** Cross-agent and cross-machine handoff without any service.
4. **Template-driven specs.** The user's template defines the spec; rules are classified, not invented.
5. **Scoped enforcement.** The Claude hook is silent outside the active task, so normal agent use is untouched.
6. **Test discipline.** Scenario tests mirror the required behaviours; doc-consistency tests keep docs and engine in
   step; CI runs on three operating systems.
7. **Evidence-labelled compatibility docs.** "Tested / checked / vendor docs / unverified" is a strong pattern to
   reuse for adapters and agents.

## 8. Baseline measurements (2026-11-22, macOS, Python 3.13.2, git 2.50.1)

| Measure | Result |
|---|---|
| `cd tests && python3 -m unittest` | 141 tests, **OK**, 44.2 s |
| `python3 tools/prepublish_check.py` | 65 files scanned, no findings |
| GitHub Actions (last 3 runs on `main`) | All passed |
| `install.py doctor` on this machine | No canonical copy installed (the skill is not installed on this Mac yet) |
| Release tags | `v1.0.0` only; `CHANGELOG.md` has an Unreleased section (guided setup) |
| Size | `workflow.py` 3,458 lines · `install.py` 441 · tests ~1,800 · `index.html` 1,296 |
