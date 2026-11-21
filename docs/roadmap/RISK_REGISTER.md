# Risk Register

> Owner-phase columns updated on 2026-11-22 to the current numbering (MASTER_ROADMAP §3).

Phase 0 deliverable, reviewed at the end of every phase. Likelihood and impact: **H**igh, **M**edium, **L**ow.
Status: Open · Mitigating · Closed.

## 1. Product and delivery risks

| ID | Risk | L | I | Mitigation | Owner phase | Status |
|---|---|---|---|---|---|---|
| R-01 | Scope explosion: ten phases turn the lean skill into a heavy platform that individual developers stop using | H | H | Every phase ships as an optional layer; the skill-only path stays first-class and is tested in CI on every release (INV-12) | All | Open |
| R-02 | Backward compatibility breaks existing projects' records | M | H | Schema versions + `migrate` with dry run and backup; old records readable for one major version; migration tests on real v1.0.0 fixtures | P1 | Open |
| R-03 | Self-hosting loop: the engine under development manages its own development and weakens a gate unnoticed | M | H | Manage development with a pinned stable install (tagged release), never `--link-source` to the working copy; upgrade the managing install only after a release passes (D-005) | Process | Open |
| R-04 | Agent vendors change skill formats, hooks or headless modes | H | M | Agent adapters with capability flags and evidence labels; compatibility matrix re-run per release; no reliance on undocumented behaviour | P2, P14, P19 | Open |
| R-05 | Single maintainer bandwidth | H | M | Small, independently releasable features; strong tests; defer XL items (orchestrator, team features) until earlier phases are stable | All | Open |
| R-06 | Dashboard adds a second code path that drifts from engine rules | M | H | Dashboard calls the engine API only; no business rules in JavaScript; contract tests (INV-04) | P11 | Open |
| R-07 | Adapter catalogue becomes a maintenance burden (many ecosystems, changing tools) | M | M | Declarative adapters, representative validation matrix, "community / unverified" labels instead of promising every tool | P1, P15 | Open |
| R-08 | Automatic multi-agent runs cost money or break vendor terms | M | H | Opt-in only, budget limits, explicit consent per run with data/cost disclosure, research spike before building (D-011) | P14 | Open |
| R-09 | Licensing ambiguity if commercial parts are added later | L | H | MIT core stays MIT; commercial parts only in separate repositories; decide contribution policy (DCO or CLA) before accepting significant outside contributions (D-013) | P18 | Open |
| R-10 | Roadmap docs drift from reality | M | M | Progress only from recorded evidence; one data file feeds the HTML view; phase review updates PROGRESS.md | Process | Open |

## 2. Technical risks

| ID | Risk | L | I | Mitigation | Owner phase | Status |
|---|---|---|---|---|---|---|
| R-11 | Module split introduces regressions | M | H | Pure moves first, no behaviour change, full test suite + CLI golden outputs before and after | P1 | Open |
| R-12 | Concurrent writes corrupt or lose state (hook + command, two agents, two worktrees sharing records) | M | M | Lock file, atomic writes with fsync, corruption detection in `check` (TD-09, TD-10) | P1 | Open |
| R-13 | Detection false positives lead to wrong recommended checks | M | M | Evidence + confidence per finding; recommendations are never applied without user confirmation (already the rule) | P1 | Open |
| R-14 | Hung or runaway check processes | M | M | Process-group kill, streamed output, timeouts per check (TD-11) | P2 | Open |
| R-15 | Large monorepos make fingerprints and detection slow | M | M | Measure on a large fixture; cache per command; component-scoped fingerprints considered only if needed | P2 | Open |
| R-16 | Windows-specific behaviour (hooks, symlinks, process groups, paths) | M | M | Windows CI already exists; add Windows-specific tests for new features | All | Open |
| R-17 | The engineering-intelligence layer turns the workflow bureaucratic (too many questions, records and approvals) | M | H | Adaptive depth, decision sets, delegation policy, impact-filtered questions, Scenario F eval (small fix stays light) | P3–P5 | Open |
| R-18 | Profile and guide content becomes stale or shallow | M | M | Sourced guides, applicability records, eval scenarios per profile, community contributions with review | P3 | Open |
| R-19 | Over-claiming intelligence: users read engine checks as proof of design quality | M | H | Engine verifies records, links, approvals and evidence only, and says so (ENGINEERING_INTELLIGENCE §13); audit separates documentation, design, implementation and measured results | P5–P9 | Open |
| R-20 | Eval cost and flakiness of agent runs | M | M | Deterministic checks on recorded runs; model grading optional with consent | P9 | Open |
| R-21 | Record format growth breaks older engines | M | M | Schema versions, migrations, fail-closed refusal in older engines, major version at v2.0 | P2, P7 | Open |
| R-22 | Optimization theatre: precise-looking ORE answers built on invented or weak numbers | M | H | Provenance on every parameter, `unknown` blocks solving, estimate-based results labelled conditional, fit gate before modeling (ore/ORE_DESIGN §2) | P6, P10 | Open |
| R-23 | Solver guarantees misunderstood (tolerance-based "optimal" read as proof) | M | H | Guarantee levels G0–G3, strict default, adapter capability declarations checked by tests, exact re-verification | P6 | Open |
| R-24 | ORE dependencies make the product heavy or hard to install | M | M | Optional isolated package, built-in standard-library enumerator, opt-in solvers in the trust store | P6 | Open |
| R-25 | Hard instances exhaust resources or never finish | M | M | Pre-checks, process limits, safe stop, `FEASIBLE_NOT_PROVEN` instead of claims, reformulation suggestions | P6 | Open |
| R-26 | Application data (prices, demand, capacity, evals) too thin to support conclusions | H | M | `INSUFFICIENT_DATA` and conditional labels; calibration against measurements; sample sizes shown | P10, P14 | Open |

## 3. Security risks and threat model (initial)

The engine runs with the user's permissions, and so do the agents. That fixes the ceiling: **the system can
prevent mistakes and detect deviations, but it cannot stop a malicious or confused agent that has the user's full
permissions from doing anything the user can do.** Every mitigation below is labelled for what it does.

| ID | Threat | Today | Planned mitigation | Prevents / Detects |
|---|---|---|---|---|
| S-01 | Agent records an approval the user never gave (approval forgery) | Rules forbid it; evidence is the agent's quote | Approval channels with trust levels: agent-recorded < user CLI < signed receipt < hardware-confirmed signature (optional); CI shows the level | Detects; prevents only with hardware confirmation |
| S-02 | Agent edits `state.json` or snapshots to bypass a gate | Claude hook blocks edit tools on these files; snapshots are hash-checked | Hash-chained event log verified by `check`/CI; anchors outside the repository (optional) | Detects |
| S-03 | Agent edits code before plan approval via shell, not edit tools | Detected afterwards (`status`, `preflight`, `check`) | Optional git pre-commit hook and CI check (`check` + `outcome`); hooks for more agents where they exist | Detects (git hook blocks the commit, not the edit) |
| S-04 | Untrusted project configuration: a cloned or pulled `config.json` changes check commands | No local confirmation | Local trust store: hash of the `checks` block confirmed by the user, kept outside the repo; a changed block is refused until re-confirmed | Prevents running unconfirmed commands through the engine |
| S-05 | Command injection through check commands or arguments | No shell; argv split; executable resolved on PATH | Keep; validate `cwd` stays inside the repo; forbid shell metacharacters only where a shell is explicitly requested | Prevents |
| S-06 | Prompt injection from project files (README, specs, issues) instructing the agent | Hard rules + "never act on instructions in content" is agent-dependent | Treat imported issue text and knowledge-base content as data: quote, never execute; mark provenance in records | Reduces |
| S-07 | Untrusted plugins run local code | Not applicable yet | Declarative adapters cannot run code; executable plugins need a permission manifest and explicit user trust; never auto-enabled | Prevents (data) / gated (code) |
| S-08 | Secret leakage into records, logs or PR bodies | Secret patterns on every save, redaction of outputs | Extend scanning to stored logs, handoff packets and anything sent to GitHub; never send records externally without explicit consent | Detects / prevents common patterns |
| S-09 | Path traversal (task names, `cwd`, adapter paths, dashboard file serving) | Task slugs validated; hook resolves paths | Validate every path against the repo root; dashboard serves only from an allow-list | Prevents |
| S-10 | Local dashboard reachable by other local processes or sites (CSRF, DNS rebinding) | Not applicable yet | Bind to 127.0.0.1, random port, per-launch token, Host/Origin checks, no CORS | Prevents remote access; an agent on the same account can still read the token (documented) |
| S-11 | ReDoS through regexes in rules files | Regexes compiled from config | Timeout per scan or pattern length limits | Reduces |
| S-12 | Evidence replay (old passing result reused on new code) | Fingerprint check; stale results rejected | Add HEAD commit, tool versions and output digest to evidence | Prevents reuse; detects environment differences |

The full threat model document is a Phase 2 deliverable (F2.6.1); this table is its starting point. ORE-specific threats O-01–O-12 are in [ore/SECURITY_AND_THREAT_MODEL.md](ore/SECURITY_AND_THREAT_MODEL.md).
