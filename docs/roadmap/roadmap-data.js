/* AIDevWorkflow roadmap data: the single source of feature statuses for roadmap.html.
 * Generated on 2026-11-22 from the phase files, DECISIONS.md and REQUIREMENTS_TRACEABILITY.md; afterwards, update a
 * status only from recorded evidence (a closed AIDevWorkflow task, a test run, CI) and log it in PROGRESS.md.
 * Statuses: planned · in-progress · review · waiting · blocked · done. mvp: part of v1.5 (D-030).
 */
window.ROADMAP = {
 "updated": "2026-11-22",
 "baselineCommit": "6849eca",
 "current": {
  "phase": 1,
  "next": {
   "en": "F1.0.3 committed. D-037 conditionally approved; CP-SAT trial on macOS met the conditions with ORE controls. Waiting on the owner: policy questions P-1–P-3, Linux/Windows trial runs (push), final D-037. Next feature: F1.0.4 or F1.0.5.",
   "ar": "F1.0.3 اتعملها commit. D-037 متوافق عليه بشروط، وتجربة CP-SAT على macOS حققت الشروط مع ضوابط ORE. مستنيين صاحب المشروع: أسئلة السياسة P-1–P-3، تشغيل التجربة على Linux وWindows (بعد الـ push)، والقرار النهائي في D-037. الخاصية الجاية: F1.0.4 أو F1.0.5."
  }
 },
 "phases": [
  {
   "id": 0,
   "target": "—",
   "status": "done",
   "effort": "done",
   "deps": [],
   "file": "phases/PHASE_00.md",
   "name": {
    "en": "Audit, assessment & strategic integrations",
    "ar": "المراجعة ودمج الرؤى الاستراتيجية"
   },
   "goal": {
    "en": "Understand the system, then merge briefs 2 and 3 into one roadmap.",
    "ar": "نفهم النظام، وبعدين ندمج الرؤيتين التانية والتالتة في خطة واحدة."
   },
   "epics": [
    {
     "id": "E0.1",
     "name": "Audit",
     "features": [
      {
       "id": "F0.1.1",
       "t": "Read the repository: SKILL.md, references, engine (all 3,458 lines), installer, templates, schema, examples, docs, guide structure, tests, CI",
       "pri": "P0",
       "eff": "—",
       "st": "done"
      },
      {
       "id": "F0.1.2",
       "t": "Baseline: run the test suite and privacy scan; check CI history, tags, installed copies",
       "pri": "P0",
       "eff": "—",
       "st": "done"
      },
      {
       "id": "F0.1.3",
       "t": "Reports: current architecture, capability inventory, technology-specific parts, gap analysis, technical debt (TD-03/TD-04 reproduced), risk register with an initial threat model",
       "pri": "P0",
       "eff": "—",
       "st": "done"
      }
     ]
    },
    {
     "id": "E0.2",
     "name": "Planning",
     "features": [
      {
       "id": "F0.2.1",
       "t": "Target architecture with compared alternatives, migration and compatibility plan",
       "pri": "P0",
       "eff": "—",
       "st": "done"
      },
      {
       "id": "F0.2.2",
       "t": "Master roadmap, phase plans 0–10 with epics, features and tasks, decisions log, progress log, HTML view",
       "pri": "P0",
       "eff": "—",
       "st": "done"
      },
      {
       "id": "F0.2.3",
       "t": "Owner review: approve, change or reject the proposed decisions and the phase order",
       "pri": "P0",
       "eff": "—",
       "st": "done"
      }
     ]
    },
    {
     "id": "E0.3",
     "name": "Strategic integration (brief 2)",
     "features": [
      {
       "id": "F0.3.1",
       "t": "Engineering Intelligence layer: architecture, record model, approval types, modes, depth, questioning, profiles, diagrams, evals, change classification",
       "pri": "P0",
       "eff": "—",
       "st": "done"
      },
      {
       "id": "F0.3.2",
       "t": "Phase restructure (0–17), new phase plans 3–8 and 14, renumbering of unstarted phases, versions and MVP",
       "pri": "P0",
       "eff": "—",
       "st": "done"
      },
      {
       "id": "F0.3.3",
       "t": "Requirements traceability matrix covering every requirement of both briefs",
       "pri": "P0",
       "eff": "—",
       "st": "done"
      },
      {
       "id": "F0.3.4",
       "t": "Owner review of the integration and decisions D-020–D-030",
       "pri": "P0",
       "eff": "—",
       "st": "done",
       "note": "Owner: «Approved»"
      }
     ]
    },
    {
     "id": "E0.4",
     "name": "ORE integration (brief 3)",
     "features": [
      {
       "id": "F0.4.1",
       "t": "ORE design: responsibilities, fit gate, lifecycle, architecture, schema, strict policy, security, validation",
       "pri": "P0",
       "eff": "—",
       "st": "done"
      },
      {
       "id": "F0.4.2",
       "t": "Solver comparison from official sources",
       "pri": "P0",
       "eff": "—",
       "st": "done"
      },
      {
       "id": "F0.4.3",
       "t": "Phase renumbering (0–19) with ORE phases 6 and 10 and ORE epics in phases 9, 11, 14, 15, 16, 19",
       "pri": "P0",
       "eff": "—",
       "st": "done"
      },
      {
       "id": "F0.4.4",
       "t": "Traceability matrix extended to brief 3",
       "pri": "P0",
       "eff": "—",
       "st": "done"
      },
      {
       "id": "F0.4.5",
       "t": "Owner review of the ORE integration and decisions D-031–D-040",
       "pri": "P0",
       "eff": "—",
       "st": "done",
       "note": "Owner approved; D-037 pending research"
      }
     ]
    }
   ]
  },
  {
   "id": 1,
   "target": "v1.1",
   "status": "in-progress",
   "effort": "6–9 wk",
   "deps": [
    0
   ],
   "file": "phases/PHASE_01.md",
   "name": {
    "en": "Foundations & universal technology support",
    "ar": "الأساس ودعم أي تقنية"
   },
   "goal": {
    "en": "Package split, migrations, locking; detect any project's components and support any technology without core changes.",
    "ar": "تقسيم المحرك وترحيل البيانات والقفل، واكتشاف مكونات أي مشروع ودعم أي تقنية من غير تعديل القلب."
   },
   "epics": [
    {
     "id": "E1.0",
     "name": "Engine foundations",
     "features": [
      {
       "id": "F1.0.1",
       "t": "Self-hosting setup: install the pinned v1.0.0 release as the managing engine; init this repository with the owner's choices (D-005–D-007)",
       "pri": "P0",
       "eff": "S",
       "st": "done",
       "mvp": true
      },
      {
       "id": "F1.0.2",
       "t": "Dev tooling: ruff + mypy configuration (dev only), CI job; golden CLI output tests for status, spec-check, outcome, init --discover",
       "pri": "P0",
       "eff": "S",
       "st": "done",
       "dep": [
        "F1.0.1"
       ],
       "mvp": true,
       "note": "Closed as Completed with Limitations: CI runs after the owner pushes"
      },
      {
       "id": "F1.0.3",
       "t": "Mechanical split of workflow.py into the aidw/ package; workflow.py becomes the entry point; no behaviour change",
       "pri": "P0",
       "eff": "L",
       "st": "done",
       "dep": [
        "F1.0.2"
       ],
       "mvp": true,
       "note": "Closed as Completed with Limitations: CI runs after the owner pushes"
      },
      {
       "id": "F1.0.4",
       "t": "Engine API (aidw/api.py): commands return data; CLI only prints",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F1.0.3"
       ],
       "mvp": true
      },
      {
       "id": "F1.0.5",
       "t": "State store: schema check on load, migrate (dry run, backup, rollback), lock file with stale detection, fsync, temp-file cleanup",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F1.0.3"
       ],
       "mvp": true
      },
      {
       "id": "F1.0.6",
       "t": "Single version source + consistency test (__version__, SKILL.md metadata, changelog)",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F1.0.3"
       ],
       "mvp": true
      }
     ]
    },
    {
     "id": "E1.1",
     "name": "Project detection engine",
     "features": [
      {
       "id": "F1.1.1",
       "t": "Component discovery over git ls-files (manifests at any depth, bounded, ignored paths respected) with evidence and confidence",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F1.0.4"
       ],
       "mvp": true
      },
      {
       "id": "F1.1.2",
       "t": "Detection report: languages, frameworks, package managers, build and test tools, databases, IaC, Docker, CI (including multi-line run: blocks), instruction files, tools available on PATH",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F1.1.1"
       ],
       "mvp": true
      },
      {
       "id": "F1.1.3",
       "t": "Component-scoped check IDs (web:test), fixing the silent de-duplication (TD-03)",
       "pri": "P0",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F1.1.1"
       ],
       "mvp": true
      }
     ]
    },
    {
     "id": "E1.2",
     "name": "Declarative technology adapters",
     "features": [
      {
       "id": "F1.2.1",
       "t": "Adapter format, JSON Schema, small condition language (file, glob, contains, json_has, toml_has), registry and loader",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F1.0.4"
       ],
       "mvp": true
      },
      {
       "id": "F1.2.2",
       "t": "Port the 11 existing ecosystems to built-in adapters with v1.0.0-equivalent output for root-level single-tech repos",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F1.2.1",
        "F1.1.1"
       ],
       "mvp": true
      },
      {
       "id": "F1.2.3",
       "t": "New built-in adapters: PHP/Composer/Laravel, Docker, Terraform, GitHub Actions, Xcode projects, React Native/Expo and Next.js/Angular/Vue/Svelte framework detection",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F1.2.2"
       ],
       "mvp": true
      },
      {
       "id": "F1.2.4",
       "t": "Manifest readers declared by adapters, so manifest-diff covers Go, Rust, Maven, Gradle, .NET, Composer, Gemfile, pyproject",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F1.2.1"
       ],
       "mvp": true
      },
      {
       "id": "F1.2.5",
       "t": "Project-local adapters in .ai-dev-workflow/adapters/.json (the generic custom adapter), validated, never executing code",
       "pri": "P0",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F1.2.1"
       ],
       "mvp": true
      }
     ]
    },
    {
     "id": "E1.3",
     "name": "Output parsers and quality gates",
     "features": [
      {
       "id": "F1.3.1",
       "t": "Parser interface + JUnit XML parser (counts, failures, test names in the summary)",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F1.0.3"
       ],
       "mvp": true
      },
      {
       "id": "F1.3.2",
       "t": "SARIF parser; baselines (new vs existing issues) for any structured parser",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F1.3.1"
       ],
       "mvp": true
      },
      {
       "id": "F1.3.3",
       "t": "Declared regex parser and explicit success/failure conditions per check",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F1.3.1"
       ],
       "mvp": true
      }
     ]
    },
    {
     "id": "E1.4",
     "name": "Multi-technology projects",
     "features": [
      {
       "id": "F1.4.1",
       "t": "config.json schema 2 (components, cwd, adapter references, task types); migrate from schema 1; schema 1 still read",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F1.0.5",
        "F1.1.1"
       ],
       "mvp": true
      },
      {
       "id": "F1.4.2",
       "t": "Changed files → affected components → suggested checks in status/scope (advisory; required checks unchanged)",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F1.4.1"
       ],
       "mvp": true
      }
     ]
    },
    {
     "id": "E1.5",
     "name": "Universal specification system",
     "features": [
      {
       "id": "F1.5.1",
       "t": "Configurable task types (defaults stay feature, bugfix, enhancement, refactor)",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F1.4.1"
       ],
       "mvp": true
      },
      {
       "id": "F1.5.2",
       "t": "Spec template per task type with fallback to the project default; library entries per type",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F1.5.1"
       ],
       "mvp": true
      },
      {
       "id": "F1.5.3",
       "t": "Example template pack (feature, bugfix, refactor, research, infrastructure, documentation) with rules files; never applied without confirmation",
       "pri": "P2",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F1.5.2"
       ],
       "mvp": true
      }
     ]
    },
    {
     "id": "E1.6",
     "name": "Validation and documentation",
     "features": [
      {
       "id": "F1.6.1",
       "t": "Fixture repositories: Flutter, Node/React, Python/FastAPI, Go CLI, Terraform, full-stack monorepo (Flutter + React + Node + Postgres + Docker), unsupported technology with a project-local adapter",
       "pri": "P0",
       "eff": "L",
       "st": "planned",
       "dep": [
        "E1.1",
        "E1.4"
       ],
       "mvp": true
      },
      {
       "id": "F1.6.2",
       "t": "Proof test: a new adapter added as data changes detection without any core file change",
       "pri": "P0",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F1.2.5"
       ],
       "mvp": true
      },
      {
       "id": "F1.6.3",
       "t": "Docs: adapters guide, configuration and templates updates, migration notes, compatibility and validation reports, both languages of the guide where user-facing",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "mvp": true
      }
     ]
    }
   ]
  },
  {
   "id": 2,
   "target": "v1.2",
   "status": "planned",
   "effort": "7–9 wk",
   "deps": [
    1
   ],
   "file": "phases/PHASE_02.md",
   "name": {
    "en": "Core engine: records, modes, approvals, security & recovery",
    "ar": "قلب المحرك: السجلات والأوضاع والموافقات والأمان"
   },
   "goal": {
    "en": "Record store, decision-set approvals, mode-ready gates, trust store, evidence v2, event log.",
    "ar": "مخزن السجلات، والموافقة على مجموعة قرارات، وبوابات تدعم الأوضاع، والأوامر الموثوقة، وأدلة أقوى."
   },
   "epics": [
    {
     "id": "E2.1",
     "name": "Core structure",
     "features": [
      {
       "id": "F2.1.1",
       "t": "Declarative gate table with per-mode stage sets (only feature defined here), replacing the forward_problems chain; identical behaviour proven by the scenario and golden tests",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "E1.0"
       ],
       "mvp": true
      },
      {
       "id": "F2.1.2",
       "t": "In-process event system (emit on stage, approval, check, step) feeding the event log and later analytics",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F2.1.1"
       ],
       "mvp": true
      }
     ]
    },
    {
     "id": "E2.2",
     "name": "Enforcement layers",
     "features": [
      {
       "id": "F2.2.1",
       "t": "Optional git pre-commit hook: install-hook / uninstall-hook; no-op without an active task; blocks commits of code changes made outside IMPLEMENTATION/FIXING",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "E1.0"
       ],
       "mvp": true
      },
      {
       "id": "F2.2.2",
       "t": "CI recipe: GitHub Actions workflow running check and outcome on task records, failing on inconsistencies",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F2.4.1"
       ],
       "mvp": true
      },
      {
       "id": "F2.2.3",
       "t": "Agent hooks review: native Windows Claude hook (TD-18); scoped hooks for other agents only where the vendor offers them, otherwise documented as not available",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "mvp": true
      },
      {
       "id": "F2.2.4",
       "t": "Scope warning: changed files outside the plan's Affected Areas are listed for the audit",
       "pri": "P2",
       "eff": "M",
       "st": "planned",
       "dep": [
        "E1.4"
       ],
       "mvp": true
      }
     ]
    },
    {
     "id": "E2.3",
     "name": "Approval channels",
     "features": [
      {
       "id": "F2.3.1",
       "t": "Approval channel and identity fields; A1 user CLI approval with version, hash and diff against the previous snapshot",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "E1.0"
       ],
       "mvp": true
      },
      {
       "id": "F2.3.2",
       "t": "A2/A3 signed approval receipts and verification in check and CI",
       "pri": "P2",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.3.1"
       ],
       "mvp": true
      },
      {
       "id": "F2.3.3",
       "t": "Minimum trust level per gate in project policy",
       "pri": "P2",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F2.3.1"
       ],
       "mvp": true
      }
     ]
    },
    {
     "id": "E2.4",
     "name": "Checkpoint and recovery",
     "features": [
      {
       "id": "F2.4.1",
       "t": "events.jsonl append-only log with a hash chain; check verifies it; history migrated on next write",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.1.2"
       ],
       "mvp": true
      },
      {
       "id": "F2.4.2",
       "t": "Corruption detection and guided recovery (from git history or migration backups)",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.4.1"
       ],
       "mvp": true
      }
     ]
    },
    {
     "id": "E2.5",
     "name": "Evidence integrity",
     "features": [
      {
       "id": "F2.5.1",
       "t": "Evidence v2: HEAD commit, OS, tool versions (from adapters), output SHA-256, optional redacted log file",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "E1.2"
       ],
       "mvp": true
      },
      {
       "id": "F2.5.2",
       "t": "Process runner: new process group/session, kill the group on timeout, stream output to a temp file (TD-11, TD-12)",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "E1.0"
       ],
       "mvp": true
      },
      {
       "id": "F2.5.3",
       "t": "Documented staleness rules; optional component-scoped staleness",
       "pri": "P2",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F2.5.1"
       ],
       "mvp": true
      }
     ]
    },
    {
     "id": "E2.6",
     "name": "Security",
     "features": [
      {
       "id": "F2.6.1",
       "t": "Threat model document (assets, actors, entry points, prevented vs detected)",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "mvp": true
      },
      {
       "id": "F2.6.2",
       "t": "Local trust store for check commands (confirm on first use and after any change)",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "E1.0"
       ],
       "mvp": true
      },
      {
       "id": "F2.6.3",
       "t": "Security test suite: forged approval, edited state, broken chain, stale-evidence replay, unconfirmed command, path traversal, ReDoS limits",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "E2.3",
        "E2.6"
       ],
       "mvp": true
      }
     ]
    },
    {
     "id": "E2.7",
     "name": "Engineering record store (strategic integration)",
     "features": [
      {
       "id": "F2.7.1",
       "t": "Project-level record store in .ai-dev-workflow/engineering/: typed records with IDs (OBJ, REQ, CON, ASM, Q, ADR, CMP, DGM, EST, RES, MET), refs links, schema, migration",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "E1.0"
       ],
       "mvp": true
      },
      {
       "id": "F2.7.2",
       "t": "Generic hash-bound approvals for any approvable document (decisions, requirement baselines, design packages) and decision-set approvals (one user approval covering a listed set, each item hashed)",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.7.1",
        "F2.3.1"
       ],
       "mvp": true
      },
      {
       "id": "F2.7.3",
       "t": "Reference index and trace-graph core (who references what), consistency checks for dangling IDs in check",
       "pri": "P0",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F2.7.1"
       ],
       "mvp": true
      }
     ]
    }
   ]
  },
  {
   "id": 3,
   "target": "v1.3",
   "status": "planned",
   "effort": "5–7 wk",
   "deps": [
    1,
    2
   ],
   "file": "phases/PHASE_03.md",
   "name": {
    "en": "Engineering domain profiles & adaptive depth",
    "ar": "ملفات المجالات الهندسية وعمق مرن"
   },
   "goal": {
    "en": "Curated knowledge per domain, separate from technologies; process depth scaled to the task.",
    "ar": "معرفة هندسية لكل مجال منفصلة عن التقنيات، وعمق الشغل على قد المهمة."
   },
   "epics": [
    {
     "id": "E3.1",
     "name": "Profile system",
     "features": [
      {
       "id": "F3.1.1",
       "t": "Profile format (profile.json + Markdown guides), JSON Schema, registry, project-local overrides",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F1.2.1"
       ],
       "mvp": true
      },
      {
       "id": "F3.1.2",
       "t": "Profile activation from detected components and the user's confirmation; several profiles per project",
       "pri": "P0",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F3.1.1",
        "F1.1.1"
       ],
       "mvp": true
      },
      {
       "id": "F3.1.3",
       "t": "Topic applicability records (applied / not applicable with reason)",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F3.1.1"
       ],
       "mvp": true
      }
     ]
    },
    {
     "id": "E3.2",
     "name": "Built-in profiles and knowledge",
     "features": [
      {
       "id": "F3.2.1",
       "t": "generic profile (fallback for any domain): business, technical, functional and non-functional topics",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F3.1.1"
       ],
       "mvp": true
      },
      {
       "id": "F3.2.2",
       "t": "backend, mobile, frontend profiles (brief 2 §7 contents)",
       "pri": "P0",
       "eff": "L",
       "st": "planned",
       "dep": [
        "F3.2.1"
       ],
       "mvp": true
      },
      {
       "id": "F3.2.3",
       "t": "cloud-devops, ai-engineering, distributed-systems, data-engineering, security, fde-discovery profiles",
       "pri": "P1",
       "eff": "L",
       "st": "planned",
       "dep": [
        "F3.2.1"
       ]
      },
      {
       "id": "F3.2.4",
       "t": "Decision guides, trade-off guides, architecture patterns, failure-pattern references (Markdown, sourced)",
       "pri": "P1",
       "eff": "L",
       "st": "planned",
       "dep": [
        "F3.1.1"
       ]
      }
     ]
    },
    {
     "id": "E3.3",
     "name": "Adaptive depth",
     "features": [
      {
       "id": "F3.3.1",
       "t": "Depth levels L0–L3: proposal with signals and reasons, user override, shown at the first gate, recorded",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.1.1"
       ],
       "mvp": true
      },
      {
       "id": "F3.3.2",
       "t": "Depth policy: required artifacts per depth and mode, enforced by the gate table",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F3.3.1"
       ],
       "mvp": true
      },
      {
       "id": "F3.3.3",
       "t": "Profile minimum-depth rules (paths, topics) and under-depth warnings",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F3.3.2"
       ]
      }
     ]
    },
    {
     "id": "E3.4",
     "name": "Validation and docs",
     "features": [
      {
       "id": "F3.4.1",
       "t": "Eval fixtures: Scenario F (small bug fix stays L0/L1, no HLD or ADR) and Scenario I (unknown domain via generic profile)",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F3.3.2"
       ],
       "mvp": true
      },
      {
       "id": "F3.4.2",
       "t": "Docs: profiles guide, depth guide, writing a custom profile",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "mvp": true
      }
     ]
    }
   ]
  },
  {
   "id": 4,
   "target": "v1.4",
   "status": "planned",
   "effort": "5–6 wk",
   "deps": [
    2,
    3
   ],
   "file": "phases/PHASE_04.md",
   "name": {
    "en": "Business discovery, requirements & adaptive questioning",
    "ar": "فهم البيزنس والمتطلبات والأسئلة الذكية"
   },
   "goal": {
    "en": "Understand the real problem; ask only what the code cannot answer; measurable requirements.",
    "ar": "نفهم المشكلة الحقيقية، ونسأل بس عن اللي الكود مايجاوبش عليه، ومتطلبات تتقاس."
   },
   "epics": [
    {
     "id": "E4.1",
     "name": "Question ledger",
     "features": [
      {
       "id": "F4.1.1",
       "t": "questions.jsonl + commands ask, answer, derive, assume, defer + generated questions.md view",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.7.1"
       ],
       "mvp": true
      },
      {
       "id": "F4.1.2",
       "t": "questions next: open, needed by the next gate, highest impact, grouped, excluding answered/deferred keys",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F4.1.1",
        "F3.1.2"
       ],
       "mvp": true
      },
      {
       "id": "F4.1.3",
       "t": "Structured contradiction detection; re-ask triggers when a related record changes",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F4.1.1"
       ]
      }
     ]
    },
    {
     "id": "E4.2",
     "name": "Business context",
     "features": [
      {
       "id": "F4.2.1",
       "t": "Objectives (OBJ) with stakeholders, success metrics (baseline, target, expected/measured), MVP vs future scope, failure impact",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.7.1"
       ],
       "mvp": true
      },
      {
       "id": "F4.2.2",
       "t": "Business and technical context topics in the generic profile; instructions for discovery interviews",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F3.2.1"
       ],
       "mvp": true
      }
     ]
    },
    {
     "id": "E4.3",
     "name": "Requirements engineering",
     "features": [
      {
       "id": "F4.3.1",
       "t": "Requirement records (REQ, functional / non-functional, priority, source, verification refs)",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.7.1"
       ],
       "mvp": true
      },
      {
       "id": "F4.3.2",
       "t": "Measurable NFR targets with proposed values, basis and status (proposed / approved)",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F4.3.1"
       ],
       "mvp": true
      },
      {
       "id": "F4.3.3",
       "t": "Constraints (CON) and assumptions (ASM) with confidence, validation plan and review trigger",
       "pri": "P0",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F2.7.1"
       ],
       "mvp": true
      },
      {
       "id": "F4.3.4",
       "t": "Requirement-baseline approval (with the spec in feature mode)",
       "pri": "P0",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F2.7.2"
       ],
       "mvp": true
      }
     ]
    },
    {
     "id": "E4.4",
     "name": "Discovery in the feature workflow",
     "features": [
      {
       "id": "F4.4.1",
       "t": "Feature-mode discovery uses the ledger and active profiles, scaled by depth; spec FR map to REQ",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F4.1.2",
        "F3.3.2"
       ],
       "mvp": true
      },
      {
       "id": "F4.4.2",
       "t": "Unknown-answer protocol in instructions and records (options, effects, recommendation, assume/defer)",
       "pri": "P0",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F4.1.1"
       ],
       "mvp": true
      }
     ]
    },
    {
     "id": "E4.5",
     "name": "Validation",
     "features": [
      {
       "id": "F4.5.1",
       "t": "Eval fixture Scenario A (mobile offline/sync): right questions asked, derivable ones not asked, no imposed architecture",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F4.4.1"
       ]
      }
     ]
    }
   ]
  },
  {
   "id": 5,
   "target": "v1.5 · MVP",
   "status": "planned",
   "effort": "5–7 wk",
   "deps": [
    2,
    3,
    4
   ],
   "file": "phases/PHASE_05.md",
   "name": {
    "en": "Engineering decisions, trade-offs & ADRs",
    "ar": "القرارات الهندسية والمفاضلات وسجلات القرارات"
   },
   "goal": {
    "en": "Explicit decisions with alternatives and trade-offs; the engineer decides; history kept.",
    "ar": "قرارات واضحة ببدائلها ومفاضلاتها، والمهندس هو اللي يقرر، والتاريخ محفوظ."
   },
   "epics": [
    {
     "id": "E5.1",
     "name": "ADR records",
     "features": [
      {
       "id": "F5.1.1",
       "t": "ADR format and lifecycle: proposed, under discussion, approved, rejected, deferred, superseded, needs re-evaluation",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.7.1"
       ],
       "mvp": true
      },
      {
       "id": "F5.1.2",
       "t": "Alternatives table, criteria (approved weights only), trade-offs, claim types (fact / assumption / estimate / recommendation / unknown), number sources",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F5.1.1"
       ],
       "mvp": true
      }
     ]
    },
    {
     "id": "E5.2",
     "name": "Decision approvals",
     "features": [
      {
       "id": "F5.2.1",
       "t": "Consequential vs delegated classification and the project's delegation policy",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F5.1.1"
       ],
       "mvp": true
      },
      {
       "id": "F5.2.2",
       "t": "Decision-set approval for related ADRs",
       "pri": "P0",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F2.7.2"
       ],
       "mvp": true
      },
      {
       "id": "F5.2.3",
       "t": "Conflict rule: recorded conflict with a must requirement blocks approval until resolved",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F4.3.1"
       ],
       "mvp": true
      }
     ]
    },
    {
     "id": "E5.3",
     "name": "Integration with the workflow",
     "features": [
      {
       "id": "F5.3.1",
       "t": "Plan approval requires every cited decision to be approved and current",
       "pri": "P0",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F5.1.1"
       ],
       "mvp": true
      },
      {
       "id": "F5.3.2",
       "t": "Staleness: requirement/constraint change → decisions need re-evaluation → dependent plans lose validity",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.7.3"
       ],
       "mvp": true
      },
      {
       "id": "F5.3.3",
       "t": "Reconsider-when triggers and supersede chains",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F5.1.1"
       ]
      }
     ]
    },
    {
     "id": "E5.4",
     "name": "Technical decision mode",
     "features": [
      {
       "id": "F5.4.1",
       "t": "decision mode: frame → options → evaluate → decision approval → record",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.1.1"
       ],
       "mvp": true
      },
      {
       "id": "F5.4.2",
       "t": "Spike / PoC results recorded as decision validation evidence",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F5.1.1"
       ]
      }
     ]
    },
    {
     "id": "E5.5",
     "name": "Partner behaviour",
     "features": [
      {
       "id": "F5.5.1",
       "t": "Instructions: challenge, expose risks, offer better alternatives, explain future impact, no sycophancy; mentor overlay (brief / standard / deep)",
       "pri": "P0",
       "eff": "S",
       "st": "planned",
       "mvp": true
      }
     ]
    },
    {
     "id": "E5.6",
     "name": "Validation",
     "features": [
      {
       "id": "F5.6.1",
       "t": "Eval fixtures: Scenario B (booking concurrency — decision part), G (changed business requirement), H (decision conflict)",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "E5.1",
        "E5.3"
       ],
       "mvp": true
      }
     ]
    }
   ]
  },
  {
   "id": 6,
   "target": "v1.6 · ORE v1",
   "status": "planned",
   "effort": "7–9 wk",
   "deps": [
    2,
    4,
    5
   ],
   "file": "phases/PHASE_06.md",
   "name": {
    "en": "ORE foundations: modeling, exact solving & strict optimality",
    "ar": "أساس محرك بحوث العمليات: النمذجة والحل الدقيق والأمثلية المثبتة"
   },
   "goal": {
    "en": "Declarative models, exact solving within limits, independent verification; no proof, no claim of optimality.",
    "ar": "نماذج رياضية وصفية، وحل دقيق في حدود الموارد، وتحقق مستقل؛ من غير إثبات مافيش ادعاء بالأمثلية."
   },
   "epics": [
    {
     "id": "E6.0",
     "name": "Research and feasibility",
     "features": [
      {
       "id": "F6.0.1",
       "t": "Desk study: solver comparison from official sources (SOLVER_COMPARISON.md; done in Phase 0 as F0.4.2)",
       "pri": "P0",
       "eff": "S",
       "st": "planned"
      },
      {
       "id": "F6.0.2",
       "t": "Hands-on spike: candidate solvers in a throwaway virtual environment, run scenarios ORE-A/I/J/K/L, confirm guarantees, status mapping and resource controls; decision record",
       "pri": "P0",
       "eff": "M",
       "st": "in-progress",
       "dep": [
        "F6.0.1"
       ],
       "note": "CP-SAT part run on macOS (Python 3.9, 3.13): conditions met with ORE controls; Linux/Windows runs and owner decisions pending (ore/CPSAT_TRIAL.md)"
      }
     ]
    },
    {
     "id": "E6.1",
     "name": "Mathematical model foundation",
     "features": [
      {
       "id": "F6.1.1",
       "t": "ore/1 JSON Schema, allow-listed expression AST, safe parser",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.7.1"
       ]
      },
      {
       "id": "F6.1.2",
       "t": "Exact numbers (fractions), units algebra, data provenance classes",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F6.1.1"
       ]
      },
      {
       "id": "F6.1.3",
       "t": "Validation pipeline and model statuses (invalid, insufficient data, unsupported, not modelable, numerical uncertainty)",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F6.1.2"
       ]
      },
      {
       "id": "F6.1.4",
       "t": "Plain-language rendering and hash-bound model approval",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F6.1.3",
        "F2.7.2"
       ]
      },
      {
       "id": "F6.1.5",
       "t": "Problem templates as data; first template: feature selection",
       "pri": "P0",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F6.1.1"
       ]
      }
     ]
    },
    {
     "id": "E6.2",
     "name": "Solver foundation",
     "features": [
      {
       "id": "F6.2.1",
       "t": "Adapter contract (capability declarations) and registry with policy matching",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F6.1.3"
       ]
      },
      {
       "id": "F6.2.2",
       "t": "Built-in exact enumerator (standard library) with exact search-space pre-check",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F6.2.1"
       ]
      },
      {
       "id": "F6.2.3",
       "t": "First optional adapter chosen by the spike, opt-in install recorded in the trust store",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F6.0.2",
        "F2.6.2"
       ]
      }
     ]
    },
    {
     "id": "E6.3",
     "name": "Strict optimality and verification",
     "features": [
      {
       "id": "F6.3.1",
       "t": "Status model (model, termination, solution, verification) and verifier-computed classification",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F6.2.1"
       ]
      },
      {
       "id": "F6.3.2",
       "t": "Exact re-verification of feasibility and objective; guarantee levels G0–G3; default policy",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F6.3.1"
       ]
      },
      {
       "id": "F6.3.3",
       "t": "Infeasibility explanations where the adapter provides them",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F6.3.1"
       ]
      }
     ]
    },
    {
     "id": "E6.4",
     "name": "Resource safety",
     "features": [
      {
       "id": "F6.4.1",
       "t": "Execution controller: separate process, time, memory and thread limits, cancellation, termination reasons",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.5.2"
       ]
      }
     ]
    },
    {
     "id": "E6.5",
     "name": "Evidence and decisions",
     "features": [
      {
       "id": "F6.5.1",
       "t": "Run evidence records, fingerprints (model, data, solver), staleness",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F6.3.2",
        "F2.4.1"
       ]
      },
      {
       "id": "F6.5.2",
       "t": "ADR integration (ORE result as decision evidence) and optimization topics in profiles and discovery",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "E5.1",
        "F3.2.1"
       ]
      },
      {
       "id": "F6.5.3",
       "t": "Lexicographic objectives",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F6.3.2"
       ]
      }
     ]
    },
    {
     "id": "E6.6",
     "name": "Validation and documentation",
     "features": [
      {
       "id": "F6.6.1",
       "t": "Scenarios ORE-A, I, J, K (tolerance stub), L, M; property tests (enumerator vs optional adapter); security tests O-01–O-10",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "E6.1",
        "E6.5"
       ]
      },
      {
       "id": "F6.6.2",
       "t": "User documentation docs/ore/ (overview, schema, strict policy, limits, known limitations)",
       "pri": "P0",
       "eff": "M",
       "st": "planned"
      }
     ]
    }
   ]
  },
  {
   "id": 7,
   "target": "v2.0",
   "status": "planned",
   "effort": "7–9 wk",
   "deps": [
    5
   ],
   "file": "phases/PHASE_07.md",
   "name": {
    "en": "Workflow modes, system design & diagrams",
    "ar": "أوضاع الشغل وتصميم الأنظمة والرسومات"
   },
   "goal": {
    "en": "System design as a goal of its own: HLD, LLD, estimates, failure analysis, editable diagrams.",
    "ar": "تصميم الأنظمة كهدف لوحده: HLD وLLD وتقديرات وتحليل أعطال ورسومات قابلة للتعديل."
   },
   "epics": [
    {
     "id": "E7.1",
     "name": "Modes",
     "features": [
      {
       "id": "F7.1.1",
       "t": "system-design mode: requirements baseline → decision sets → HLD → LLD → diagrams → design approval → design review → report",
       "pri": "P0",
       "eff": "L",
       "st": "planned",
       "dep": [
        "F2.1.1",
        "E5.1"
       ]
      },
      {
       "id": "F7.1.2",
       "t": "architecture-review mode: as-is discovery → analysis → findings → options → review approval → report",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F7.1.1"
       ]
      },
      {
       "id": "F7.1.3",
       "t": "business-discovery mode: stakeholders → workflows → objectives & metrics → solution options → proposal approval",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "E4.2"
       ]
      },
      {
       "id": "F7.1.4",
       "t": "full development mode: feature mode with discovery and design stages switched on by depth",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F7.1.1"
       ]
      }
     ]
    },
    {
     "id": "E7.2",
     "name": "System design artifacts",
     "features": [
      {
       "id": "F7.2.1",
       "t": "Components (CMP) and HLD structure: context, style, components, boundaries, data ownership, communication, data flow, integrations, storage, scalability, availability, security boundaries, deployment, major failures",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.7.1"
       ]
      },
      {
       "id": "F7.2.2",
       "t": "LLD documents: modules, interfaces, models, schema, API/event contracts, state machines, algorithms, validation, errors, concurrency, transactions, patterns",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F7.2.1"
       ]
      },
      {
       "id": "F7.2.3",
       "t": "Capacity estimates (EST) with safe engine recomputation and confirmed/assumed/measured inputs",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.7.1"
       ]
      },
      {
       "id": "F7.2.4",
       "t": "Failure analysis records (database, network, service, duplicates, partial failure, races, timeouts, data loss, external APIs, payments, overload, disaster recovery) mapped to tests",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F7.2.1"
       ]
      },
      {
       "id": "F7.2.5",
       "t": "Distributed-systems guidance in the profile with the justify-complexity rule",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F3.2.3"
       ]
      }
     ]
    },
    {
     "id": "E7.3",
     "name": "Diagrams",
     "features": [
      {
       "id": "F7.3.1",
       "t": "Diagram registry (DGM), Mermaid source, states, versions, hashes, links to CMP/ADR/REQ",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.7.1"
       ]
      },
      {
       "id": "F7.3.2",
       "t": "Lint: supported type, referenced components exist, linked decisions current, staleness flags",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F7.3.1"
       ]
      },
      {
       "id": "F7.3.3",
       "t": "Optional syntax validation with Mermaid CLI when installed",
       "pri": "P2",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F7.3.1"
       ]
      },
      {
       "id": "F7.3.4",
       "t": "Diagrams embedded in spec and plan; as-is vs proposed vs approved vs implemented",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F7.3.1"
       ]
      },
      {
       "id": "F7.3.5",
       "t": "Optional renderers and exports: PlantUML, Structurizr DSL, SVG/PNG, interactive HTML",
       "pri": "P2",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F7.3.1"
       ]
      }
     ]
    },
    {
     "id": "E7.4",
     "name": "Validation",
     "features": [
      {
       "id": "F7.4.1",
       "t": "Eval fixtures: Scenario C (high scale: estimates, consistency trade-offs, no unjustified distribution), D (frontend rendering/SEO/performance), B design part (ERD, sequence diagram, duplicate-booking tests)",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "E7.1",
        "E7.3"
       ]
      }
     ]
    }
   ]
  },
  {
   "id": 8,
   "target": "v2.1",
   "status": "planned",
   "effort": "5–6 wk",
   "deps": [
    4,
    5,
    7
   ],
   "file": "phases/PHASE_08.md",
   "name": {
    "en": "Intelligent specs, planning & traceability",
    "ar": "مواصفات وخطط أذكى وتتبع كامل"
   },
   "goal": {
    "en": "Architecture-aware specs and plans; trace from business objective to outcome.",
    "ar": "مواصفات وخطط فاهمة المعمارية، وتتبع من هدف البيزنس لحد النتيجة."
   },
   "epics": [
    {
     "id": "E8.1",
     "name": "Specifications",
     "features": [
      {
       "id": "F8.1.1",
       "t": "Profile-suggested spec sections; companion documents when the template lacks a needed section",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F3.1.1"
       ]
      },
      {
       "id": "F8.1.2",
       "t": "Spec quality by requirement coverage (REQ ↔ AC / tests / edge cases)",
       "pri": "P0",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F4.3.1"
       ]
      }
     ]
    },
    {
     "id": "E8.2",
     "name": "Planning",
     "features": [
      {
       "id": "F8.2.1",
       "t": "Extended plan sections scaled by depth (custom plan templates allowed)",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F3.3.2"
       ]
      },
      {
       "id": "F8.2.2",
       "t": "Plan consistency checks against approved decisions, HLD and LLD (cited IDs current and approved)",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F5.3.1",
        "F7.2.1"
       ]
      },
      {
       "id": "F8.2.3",
       "t": "Reopen-decision protocol during planning and implementation",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F5.3.2"
       ]
      }
     ]
    },
    {
     "id": "E8.3",
     "name": "Traceability",
     "features": [
      {
       "id": "F8.3.1",
       "t": "trace why",
       "pri": "impact",
       "eff": "coverage <ID>` over the reference graph",
       "st": "planned"
      },
      {
       "id": "F8.3.2",
       "t": "Generated RTM (OBJ → REQ → CON → ADR → CMP → spec → plan → code → evidence → finding → outcome) and gaps report",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F8.3.1"
       ]
      },
      {
       "id": "F8.3.3",
       "t": "Links from code changes (steps, commits when available) and delivery outcomes (MET)",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F8.3.1"
       ]
      }
     ]
    }
   ]
  },
  {
   "id": 9,
   "target": "v2.2",
   "status": "planned",
   "effort": "6–7 wk",
   "deps": [
    3,
    8
   ],
   "file": "phases/PHASE_09.md",
   "name": {
    "en": "Engineering audit, verification, evals & performance registry",
    "ar": "المراجعة الهندسية والتقييم وسجل أداء المساعدين والنماذج"
   },
   "goal": {
    "en": "Audit beyond code; measure question and decision quality with scenario evals.",
    "ar": "مراجعة أبعد من الكود، وقياس جودة الأسئلة والقرارات بسيناريوهات."
   },
   "epics": [
    {
     "id": "E9.1",
     "name": "Engineering audit",
     "features": [
      {
       "id": "F9.1.1",
       "t": "Audit dimensions as data by mode, depth and profile (business alignment, requirement coverage, architecture and decision compliance, data correctness, transaction safety, security, performance, scalability, failure recovery, API contracts, integration, maintainability, test quality, diagram accuracy, deployment and operational readiness, customer acceptance)",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F3.1.1"
       ]
      },
      {
       "id": "F9.1.2",
       "t": "Audit and outcome distinguish documentation completeness, design correctness, implementation correctness and measured results",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F9.1.1"
       ]
      },
      {
       "id": "F9.1.3",
       "t": "Architecture drift check: implemented code paths vs approved components and diagrams",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F7.2.1"
       ]
      }
     ]
    },
    {
     "id": "E9.2",
     "name": "Evals",
     "features": [
      {
       "id": "F9.2.1",
       "t": "Eval harness: scenario fixtures A–I, deterministic record checks, results registry with agent/model/version",
       "pri": "P0",
       "eff": "L",
       "st": "planned",
       "dep": [
        "F3.4.1",
        "F5.6.1"
       ]
      },
      {
       "id": "F9.2.2",
       "t": "Human rubric workflow (relevance, missing considerations, trade-off quality, sycophancy)",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F9.2.1"
       ]
      },
      {
       "id": "F9.2.3",
       "t": "Optional model-graded rubric with cost consent",
       "pri": "P2",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F9.2.1"
       ]
      }
     ]
    },
    {
     "id": "E9.3",
     "name": "Agent and model performance registry (ORE integration)",
     "features": [
      {
       "id": "F9.3.1",
       "t": "Registry per agent, model, version and task category: success, coverage, test success, findings, rework, time; tokens and cost only when reported; context, tools, privacy and rate limits; every value labelled measured / expected / unavailable; normalised by task category and size",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.4.1",
        "F9.2.1"
       ]
      },
      {
       "id": "F9.3.2",
       "t": "Task-specific model eval sets built from the user's own samples, with versions, dates and sample sizes",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F9.2.1"
       ]
      }
     ]
    }
   ]
  },
  {
   "id": 10,
   "target": "v2.3",
   "status": "planned",
   "effort": "8–10 wk",
   "deps": [
    6,
    7,
    8,
    9
   ],
   "file": "phases/PHASE_10.md",
   "name": {
    "en": "ORE advanced: multi-objective, scenarios, certificates & applications",
    "ar": "محرك بحوث العمليات المتقدم: أهداف متعددة وسيناريوهات وشهادات إثبات وتطبيقات"
   },
   "goal": {
    "en": "Pareto trade-offs, what-if analysis, proven LP results, applications and AI model selection from real evals.",
    "ar": "مفاضلات Pareto، وتحليل «ماذا لو»، ونتايج LP مثبتة، وتطبيقات، واختيار نماذج AI من تقييمات حقيقية."
   },
   "epics": [
    {
     "id": "E10.1",
     "name": "Multi-objective",
     "features": [
      {
       "id": "F10.1.1",
       "t": "Pareto via exact epsilon-constraint; complete vs partial frontier labels; approved weighted sums; trade-off reporting",
       "pri": "P1",
       "eff": "L",
       "st": "planned",
       "dep": [
        "F6.3.2"
       ]
      }
     ]
    },
    {
     "id": "E10.2",
     "name": "Scenarios and sensitivity",
     "features": [
      {
       "id": "F10.2.1",
       "t": "What-if scenarios, thresholds, break-even, robustness with approved ranges, reconsideration triggers",
       "pri": "P1",
       "eff": "L",
       "st": "planned",
       "dep": [
        "F6.5.1"
       ]
      }
     ]
    },
    {
     "id": "E10.3",
     "name": "Problem classes and certificates",
     "features": [
      {
       "id": "F10.3.1",
       "t": "Continuous LP through an optional float solver, verified by an exact dual certificate (G3)",
       "pri": "P1",
       "eff": "L",
       "st": "planned",
       "dep": [
        "F6.2.1"
       ]
      },
      {
       "id": "F10.3.2",
       "t": "Optional second exact solver cross-check for small and medium integer models",
       "pri": "P2",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F6.2.1"
       ]
      },
      {
       "id": "F10.3.3",
       "t": "Model calibration: measured values vs model parameters, re-evaluation flags",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F6.5.1",
        "F8.3.3"
       ]
      }
     ]
    },
    {
     "id": "E10.4",
     "name": "Applications (templates and scenarios)",
     "features": [
      {
       "id": "F10.4.1",
       "t": "System design, cloud and database capacity templates (ORE-B, ORE-C)",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F7.2.3"
       ]
      },
      {
       "id": "F10.4.2",
       "t": "Booking allocation template (ORE-D)",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F6.1.5"
       ]
      },
      {
       "id": "F10.4.3",
       "t": "MVP planning, resource allocation and project scheduling templates",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F6.1.5"
       ]
      },
      {
       "id": "F10.4.4",
       "t": "Pricing and business templates with demand-model provenance rules",
       "pri": "P2",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F6.1.5"
       ]
      },
      {
       "id": "F10.4.5",
       "t": "AI model selection template from task-specific evals (ORE-F)",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F9.3.2"
       ]
      },
      {
       "id": "F10.4.6",
       "t": "Cost vs performance Pareto scenario (ORE-H)",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F10.1.1"
       ]
      }
     ]
    }
   ]
  },
  {
   "id": 11,
   "target": "v3.x",
   "status": "planned",
   "effort": "2 + 9–13 wk",
   "deps": [
    2,
    9
   ],
   "file": "phases/PHASE_11.md",
   "name": {
    "en": "CLI, dashboard, decision center & ORE views",
    "ar": "سطر الأوامر ولوحة التحكم ومركز القرارات وعرض نتايج المحرك"
   },
   "goal": {
    "en": "Manage tasks, decisions, designs and traceability without opening files.",
    "ar": "تدير المهام والقرارات والتصميم والتتبع من غير ما تفتح ملفات."
   },
   "epics": [
    {
     "id": "E11.1",
     "name": "Human CLI (v3.0)",
     "features": [
      {
       "id": "F11.1.1",
       "t": "CLI design record: command map, output style, exit codes, localisation approach",
       "pri": "P0",
       "eff": "S",
       "st": "planned",
       "dep": [
        "E1.0"
       ]
      },
      {
       "id": "F11.1.2",
       "t": "aidev launcher installed by install.py; commands init, doctor, tasks, status, resume, pause, check, interactive approve",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F11.1.1",
        "F2.3.1"
       ]
      },
      {
       "id": "F11.1.3",
       "t": "handoff <task>: one generated brief (stage, next step, open items, files to read, last evidence)",
       "pri": "P1",
       "eff": "S",
       "st": "planned",
       "dep": [
        "E1.0"
       ]
      }
     ]
    },
    {
     "id": "E11.2",
     "name": "Dashboard foundation (v3.x)",
     "features": [
      {
       "id": "F11.2.1",
       "t": "Technology and security design record",
       "pri": "P0",
       "eff": "S",
       "st": "planned",
       "dep": [
        "F11.1.1"
       ]
      },
      {
       "id": "F11.2.2",
       "t": "Local server on http.server, token, JSON endpoints over the engine API (read first, then approval actions)",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F11.2.1"
       ]
      },
      {
       "id": "F11.2.3",
       "t": "Opt-in project registry (~/.ai-dev-workflow/projects.json) and derived index (index.db)",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F11.2.2"
       ]
      }
     ]
    },
    {
     "id": "E11.3",
     "name": "Views",
     "features": [
      {
       "id": "F11.3.1",
       "t": "Projects and tasks overview; task detail: stage, spec, plan, acceptance criteria, check results, audit findings, history, final report",
       "pri": "P0",
       "eff": "L",
       "st": "planned",
       "dep": [
        "F11.2.2"
       ]
      },
      {
       "id": "F11.3.2",
       "t": "Approval center: document version, diff against the previous version, hash, warnings, decisions; Approve / Request changes / Reject through the engine",
       "pri": "P0",
       "eff": "L",
       "st": "planned",
       "dep": [
        "F11.2.2",
        "F2.3.1"
       ]
      }
     ]
    },
    {
     "id": "E11.4",
     "name": "Design",
     "features": [
      {
       "id": "F11.4.1",
       "t": "Design system reused from index.html: tokens, light/dark, responsive, Arabic/English, RTL, accessible contrast",
       "pri": "P0",
       "eff": "M",
       "st": "planned"
      }
     ]
    },
    {
     "id": "E11.5",
     "name": "Quality",
     "features": [
      {
       "id": "F11.5.1",
       "t": "Tests: API contract, rendering smoke tests, security tests (token, Origin, path traversal)",
       "pri": "P0",
       "eff": "M",
       "st": "planned",
       "dep": [
        "E11.2",
        "E11.3"
       ]
      },
      {
       "id": "F11.5.2",
       "t": "Regression test proving the skill-only path works with no dashboard files used",
       "pri": "P0",
       "eff": "S",
       "st": "planned"
      }
     ]
    },
    {
     "id": "E11.6",
     "name": "Engineering views (brief 2 §16)",
     "features": [
      {
       "id": "F11.6.1",
       "t": "Business objectives, discovery questions and answers (answer from the UI), requirements explorer, risks and assumptions",
       "pri": "P1",
       "eff": "L",
       "st": "planned"
      },
      {
       "id": "F11.6.2",
       "t": "Engineering decision center: alternatives, trade-off matrix (user-approved criteria only), AI recommendation and reasons, choose a different option, request more information or a spike, approve decision sets, ADR history",
       "pri": "P0",
       "eff": "L",
       "st": "planned"
      },
      {
       "id": "F11.6.3",
       "t": "Architecture explorer and diagram viewer; design version comparison; impact of changing an old decision",
       "pri": "P1",
       "eff": "L",
       "st": "planned"
      },
      {
       "id": "F11.6.4",
       "t": "Traceability explorer, open engineering questions, project health, production readiness, customer delivery status, business outcome metrics",
       "pri": "P2",
       "eff": "L",
       "st": "planned"
      },
      {
       "id": "F11.6.5",
       "t": "ORE views: problem explorer, results with guarantee levels and classifications, trade-off and Pareto charts (complete vs partial), scenarios, decision review through the core",
       "pri": "P2",
       "eff": "L",
       "st": "planned"
      }
     ]
    }
   ]
  },
  {
   "id": 12,
   "target": "v3.x",
   "status": "planned",
   "effort": "5–7 wk",
   "deps": [
    2,
    11
   ],
   "file": "phases/PHASE_12.md",
   "name": {
    "en": "Git, GitHub & parallel development",
    "ar": "Git وGitHub والشغل المتوازي"
   },
   "goal": {
    "en": "Branches, safe parallel tasks, conflicts, issues and PRs — never committing on its own.",
    "ar": "فروع ومهام متوازية بأمان وتعارضات وissues وPRs، من غير أي commit لوحده."
   },
   "epics": [
    {
     "id": "E12.1",
     "name": "Git integration",
     "features": [
      {
       "id": "F12.1.1",
       "t": "Optional branch binding per task (new --branch, checks in preflight)",
       "pri": "P1",
       "eff": "S",
       "st": "planned"
      },
      {
       "id": "F12.1.2",
       "t": "Per-task diff export and change ownership per step",
       "pri": "P1",
       "eff": "M",
       "st": "planned"
      }
     ]
    },
    {
     "id": "E12.2",
     "name": "Parallel tasks",
     "features": [
      {
       "id": "F12.2.1",
       "t": "Worktree management per task (create, list, remove) with a records strategy for each commit mode; study of alternatives recorded first",
       "pri": "P0",
       "eff": "L",
       "st": "planned"
      },
      {
       "id": "F12.2.2",
       "t": "Cross-worktree task registry and locking",
       "pri": "P0",
       "eff": "M",
       "st": "planned"
      }
     ]
    },
    {
     "id": "E12.3",
     "name": "Conflict detection",
     "features": [
      {
       "id": "F12.3.1",
       "t": "File overlap between active tasks (approved Affected Areas and actual changes)",
       "pri": "P0",
       "eff": "S",
       "st": "planned"
      },
      {
       "id": "F12.3.2",
       "t": "Heuristics for migration ordering and API contract files (OpenAPI, protobuf, GraphQL schemas), labelled as heuristics",
       "pri": "P2",
       "eff": "M",
       "st": "planned"
      }
     ]
    },
    {
     "id": "E12.4",
     "name": "GitHub",
     "features": [
      {
       "id": "F12.4.1",
       "t": "Provider interface + gh CLI provider (auth stays in gh)",
       "pri": "P1",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F12.4.2",
       "t": "Import an issue as task input (quoted, with link)",
       "pri": "P1",
       "eff": "S",
       "st": "planned"
      },
      {
       "id": "F12.4.3",
       "t": "Create a pull request after explicit permission, with report summary, acceptance criteria, test results and audit findings chosen by the user",
       "pri": "P1",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F12.4.4",
       "t": "Optional status check from check + outcome in CI; guidance for branch protection",
       "pri": "P2",
       "eff": "M",
       "st": "planned"
      }
     ]
    }
   ]
  },
  {
   "id": 13,
   "target": "v3.x",
   "status": "planned",
   "effort": "6–8 wk",
   "deps": [
    2,
    5,
    7
   ],
   "file": "phases/PHASE_13.md",
   "name": {
    "en": "Project intelligence & architecture evolution",
    "ar": "فهم المشروع وتطور المعمارية"
   },
   "goal": {
    "en": "Cumulative sourced knowledge; architecture history and drift.",
    "ar": "معرفة متراكمة بمصادرها، وتاريخ المعمارية وانحرافها."
   },
   "epics": [
    {
     "id": "E13",
     "name": "Features",
     "features": [
      {
       "id": "F13.1.1",
       "t": "Knowledge entries on top of the engineering record store (Phase 2 E2.7): architecture overview, modules, APIs, schema, auth, shared components, conventions, limitations, business rules — each with source hashes",
       "pri": "P1",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F13.1.2",
       "t": "Architecture map: components, internal dependency graph from manifests and imports (adapter-provided extractors)",
       "pri": "P1",
       "eff": "L",
       "st": "planned"
      },
      {
       "id": "F13.2.1",
       "t": "Architecture evolution timeline: ADR and diagram history, as-is / approved / implemented over time, drift between approved and implemented architecture (ADRs themselves moved to Phase 5)",
       "pri": "P1",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F13.3.1",
       "t": "Deep, code-level impact report at PLANNING (basic record-level impact queries arrive in Phase 8): modules, shared components, API consumers, schema/migrations, auth, permissions, performance, compatibility, security, tests, infrastructure",
       "pri": "P1",
       "eff": "L",
       "st": "planned"
      },
      {
       "id": "F13.4.1",
       "t": "Post-task update: changed knowledge, new ADRs, stale entries flagged by hash",
       "pri": "P2",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F13.5.1",
       "t": "Task context pack: relevant files and knowledge for the agent, from metadata and the dependency graph",
       "pri": "P2",
       "eff": "M",
       "st": "planned"
      }
     ]
    }
   ]
  },
  {
   "id": 14,
   "target": "v4.x",
   "status": "planned",
   "effort": "4 (+6–10) wk",
   "deps": [
    2,
    11,
    12
   ],
   "file": "phases/PHASE_14.md",
   "name": {
    "en": "Multi-agent orchestration & ORE allocation",
    "ar": "تعاون أكتر من مساعد AI وتوزيعهم بالمحرك"
   },
   "goal": {
    "en": "Roles, handoffs, independent audits; automation only after a spike.",
    "ar": "أدوار وتسليم وتدقيق مستقل، والتشغيل التلقائي بعد دراسة."
   },
   "epics": [
    {
     "id": "E14",
     "name": "Features",
     "features": [
      {
       "id": "F14.1.1",
       "t": "Agent capability profiles (data), aidev agents report",
       "pri": "P1",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F14.2.1",
       "t": "Role assignment per task; policy \"auditor must differ from implementer\"",
       "pri": "P1",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F14.3.1",
       "t": "Manual multi-agent mode via handoff packets and role prompts",
       "pri": "P1",
       "eff": "S",
       "st": "planned"
      },
      {
       "id": "F14.3.2",
       "t": "Research spike: official headless modes, terms, rate limits, cost reporting per vendor; decision record",
       "pri": "P1",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F14.3.3",
       "t": "Automatic orchestrator (opt-in): state machine driving agents, budgets, retries, timeouts, iteration limits, cancellation, recovery",
       "pri": "P2",
       "eff": "XL",
       "st": "planned"
      },
      {
       "id": "F14.4.1",
       "t": "Independent audit packet (diff, spec, plan, standards, evidence) for a separate agent",
       "pri": "P1",
       "eff": "S",
       "st": "planned"
      },
      {
       "id": "F14.5.1",
       "t": "Consent and cost disclosure before external agent runs",
       "pri": "P2",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F14.6.1",
       "t": "ORE agent and model allocation: per-stage choice, number of agents, parallel split, independent auditor, single vs multi-agent; human gates, privacy and budgets as hard constraints; INSUFFICIENT_DATA fallback to manual choice (ORE-G)",
       "pri": "P2",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F14.6.2",
       "t": "Feedback loop: measured task results update the registry; allocation results go stale when inputs change",
       "pri": "P2",
       "eff": "S",
       "st": "planned"
      }
     ]
    }
   ]
  },
  {
   "id": 15,
   "target": "v4.x",
   "status": "planned",
   "effort": "6–8 wk",
   "deps": [
    1,
    2,
    11
   ],
   "file": "phases/PHASE_15.md",
   "name": {
    "en": "Plugin ecosystem incl. solver adapters",
    "ar": "الإضافات وقابلية التوسع"
   },
   "goal": {
    "en": "Executable plugins and policies that can never weaken core guarantees.",
    "ar": "إضافات وسياسات من غير ما تضعف ضمانات المحرك."
   },
   "epics": [
    {
     "id": "E15",
     "name": "Features",
     "features": [
      {
       "id": "F15.1.1",
       "t": "Plugin manifest, permission model, API versioning and compatibility contract",
       "pri": "P1",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F15.1.2",
       "t": "Plugin management: install, uninstall, enable, disable, trusted sources, hash pinning",
       "pri": "P1",
       "eff": "L",
       "st": "planned"
      },
      {
       "id": "F15.2.1",
       "t": "Custom workflow policy file (cannot remove core gates)",
       "pri": "P1",
       "eff": "L",
       "st": "planned"
      },
      {
       "id": "F15.3.1",
       "t": "SDK: API docs, development guide, example plugins, test utilities",
       "pri": "P1",
       "eff": "L",
       "st": "planned"
      },
      {
       "id": "F15.4.1",
       "t": "Additional solver adapters and custom problem types as plugins, including bring-your-own commercial solvers (never required)",
       "pri": "P2",
       "eff": "M",
       "st": "planned"
      }
     ]
    }
   ]
  },
  {
   "id": 16,
   "target": "v4.x",
   "status": "planned",
   "effort": "6–8 wk",
   "deps": [
    7,
    8,
    9
   ],
   "file": "phases/PHASE_16.md",
   "name": {
    "en": "Forward deployed engineering & delivery",
    "ar": "هندسة النشر عند العميل والتسليم"
   },
   "goal": {
    "en": "From customer problem to PoC, delivery, handover and measured impact.",
    "ar": "من مشكلة العميل لحد PoC والتسليم وقياس الأثر."
   },
   "epics": [
    {
     "id": "E16",
     "name": "Features",
     "features": [
      {
       "id": "F16.1.1",
       "t": "fde mode composed from business-discovery, system-design (scaled), PoC, integration, UAT, pilot, delivery, handover, impact stages",
       "pri": "P1",
       "eff": "L",
       "st": "planned",
       "dep": [
        "F7.1.1",
        "F7.1.3"
       ]
      },
      {
       "id": "F16.2.1",
       "t": "Solution-design extras in the fde profile and records: build vs buy, legacy/API integration, data mapping and quality, ETL/ELT, sync, multi-tenancy, customer configuration vs product capability",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F3.2.3"
       ]
      },
      {
       "id": "F16.3.1",
       "t": "PoC records: hypotheses, success criteria, scope, result; PoC / prototype / MVP / production-ready distinction",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.7.1"
       ]
      },
      {
       "id": "F16.4.1",
       "t": "Delivery records: environment, integration validation, UAT, onboarding, pilot, demo, handover, runbooks, incident response, training, ownership",
       "pri": "P1",
       "eff": "L",
       "st": "planned",
       "dep": [
        "F16.1.1"
       ]
      },
      {
       "id": "F16.5.1",
       "t": "Business impact records (MET): baseline, target, actual, expected vs measured, ROI assumptions labelled",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F2.7.1"
       ]
      },
      {
       "id": "F16.6.1",
       "t": "Eval fixture Scenario E: service-operations AI copilot (discovery, data integration, RAG, tools, human approval, security, tenant isolation, evals, monitoring, deployment, demo, handover, impact)",
       "pri": "P1",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F9.2.1"
       ]
      },
      {
       "id": "F16.7.1",
       "t": "ORE for forward deployed work: build vs buy with measurable terms, rollout and implementation scheduling, logistics template (ORE-E)",
       "pri": "P2",
       "eff": "M",
       "st": "planned",
       "dep": [
        "F10.4.3"
       ]
      }
     ]
    }
   ]
  },
  {
   "id": 17,
   "target": "v3.x · v5.x",
   "status": "planned",
   "effort": "1–2 + 4–6 wk",
   "deps": [
    2,
    11
   ],
   "file": "phases/PHASE_17.md",
   "name": {
    "en": "Engineering analytics & business impact",
    "ar": "التحليلات الهندسية وأثر البيزنس"
   },
   "goal": {
    "en": "Metrics from real data; missing data shown as unavailable.",
    "ar": "مقاييس من بيانات حقيقية، واللي مش متاح يظهر «غير متاح»."
   },
   "epics": [
    {
     "id": "E17",
     "name": "Features",
     "features": [
      {
       "id": "F17.1.1",
       "t": "Task metrics computed from events (CLI + dashboard)",
       "pri": "P1",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F17.2.1",
       "t": "Agent metrics with availability flags",
       "pri": "P2",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F17.3.1",
       "t": "Engineering quality metrics (coverage from parsers, churn from git)",
       "pri": "P2",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F17.4.1",
       "t": "Analytics views by task, project, agent, technology, period; report export",
       "pri": "P2",
       "eff": "L",
       "st": "planned"
      },
      {
       "id": "F17.5.1",
       "t": "Business impact view from outcome records (baseline, target, actual; expected vs measured; ROI assumptions labelled)",
       "pri": "P2",
       "eff": "M",
       "st": "planned"
      }
     ]
    }
   ]
  },
  {
   "id": 18,
   "target": "after v4",
   "status": "planned",
   "effort": "2–3 wk study",
   "deps": [
    14
   ],
   "file": "phases/PHASE_18.md",
   "name": {
    "en": "Team collaboration & enterprise (study first)",
    "ar": "الفرق والمؤسسات (دراسة الأول)"
   },
   "goal": {
    "en": "Architecture and licensing study for teams; no code before approval.",
    "ar": "دراسة معمارية وترخيص للفرق، من غير كود قبل الموافقة."
   },
   "epics": [
    {
     "id": "E18",
     "name": "Features",
     "features": [
      {
       "id": "F18.1.1",
       "t": "Technical study: team model, RBAC, multiple approvers, sync options (git-based first), self-hosted design",
       "pri": "P2",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F18.2.1",
       "t": "Product study: editions, pricing hypotheses, what stays Community",
       "pri": "P2",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F18.3.1",
       "t": "Licensing study: open-core separation, repository layout, DCO vs CLA, trademark",
       "pri": "P2",
       "eff": "S",
       "st": "planned"
      }
     ]
    }
   ]
  },
  {
   "id": 19,
   "target": "every release",
   "status": "planned",
   "effort": "continuous",
   "deps": [],
   "file": "phases/PHASE_19.md",
   "name": {
    "en": "Production readiness & release",
    "ar": "الجاهزية للإنتاج والإصدار"
   },
   "goal": {
    "en": "Release checklist, validation matrices, distribution, docs — in every release.",
    "ar": "قائمة فحص وتحقق وتوزيع وتوثيق في كل إصدار."
   },
   "epics": [
    {
     "id": "E19",
     "name": "Features",
     "features": [
      {
       "id": "F19.1.1",
       "t": "Release checklist and tools/release_check.py (versions, changelog, tests, scan, docs consistency, migration test) — used from v1.1",
       "pri": "P0",
       "eff": "S",
       "st": "planned"
      },
      {
       "id": "F19.2.1",
       "t": "Test strategy completion: concurrency, recovery, migration, interoperability suites",
       "pri": "P1",
       "eff": "L",
       "st": "planned"
      },
      {
       "id": "F19.3.1",
       "t": "Technology validation matrix with fixtures in CI",
       "pri": "P1",
       "eff": "L",
       "st": "planned"
      },
      {
       "id": "F19.3.2",
       "t": "Agent validation matrix with recorded live runs per release",
       "pri": "P1",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F19.4.1",
       "t": "Distribution: compare options, release archives on GitHub Releases, update and rollback commands",
       "pri": "P1",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F19.5.1",
       "t": "Documentation set: architecture, user, configuration, adapters, plugins, security, troubleshooting, FAQ, contributing; bilingual guide refresh",
       "pri": "P1",
       "eff": "L",
       "st": "planned"
      },
      {
       "id": "F19.6.1",
       "t": "CI/CD: coverage report, security checks (secret scan, dependency-free audit), packaging and release validation, version consistency",
       "pri": "P1",
       "eff": "M",
       "st": "planned"
      },
      {
       "id": "F19.7.1",
       "t": "ORE validation matrix per release: solvers × scenarios × operating systems, guarantee levels re-confirmed",
       "pri": "P1",
       "eff": "M",
       "st": "planned"
      }
     ]
    }
   ]
  }
 ],
 "decisions": [
  {
   "id": "D-001",
   "t": "Execution order",
   "st": "accepted"
  },
  {
   "id": "D-002",
   "t": "Engine structure",
   "st": "accepted"
  },
  {
   "id": "D-003",
   "t": "Adapter model",
   "st": "accepted"
  },
  {
   "id": "D-004",
   "t": "Output parsing",
   "st": "accepted"
  },
  {
   "id": "D-005",
   "t": "Self-hosting",
   "st": "accepted"
  },
  {
   "id": "D-006",
   "t": "Records mode for this repository",
   "st": "accepted"
  },
  {
   "id": "D-007",
   "t": "Spec template for our own tasks",
   "st": "accepted"
  },
  {
   "id": "D-012",
   "t": "Minimum Python version",
   "st": "accepted"
  },
  {
   "id": "D-014",
   "t": "Versioning plan (mapping superseded by D-029 on 2026-11-22)",
   "st": "accepted"
  },
  {
   "id": "D-015",
   "t": "Language of roadmap documents",
   "st": "accepted"
  },
  {
   "id": "D-016",
   "t": "Planning granularity",
   "st": "accepted"
  },
  {
   "id": "D-018",
   "t": "Dev tooling for the engine",
   "st": "accepted"
  },
  {
   "id": "D-020",
   "t": "Integrated phase order",
   "st": "accepted"
  },
  {
   "id": "D-021",
   "t": "Engineering record model",
   "st": "accepted"
  },
  {
   "id": "D-022",
   "t": "Approval types",
   "st": "accepted"
  },
  {
   "id": "D-023",
   "t": "Delegation policy",
   "st": "accepted"
  },
  {
   "id": "D-024",
   "t": "Workflow modes",
   "st": "accepted"
  },
  {
   "id": "D-025",
   "t": "Adaptive depth",
   "st": "accepted"
  },
  {
   "id": "D-026",
   "t": "Domain profiles",
   "st": "accepted"
  },
  {
   "id": "D-027",
   "t": "Diagrams",
   "st": "accepted"
  },
  {
   "id": "D-028",
   "t": "Measuring question and decision quality",
   "st": "accepted"
  },
  {
   "id": "D-029",
   "t": "Revised versioning",
   "st": "accepted"
  },
  {
   "id": "D-030",
   "t": "MVP scope",
   "st": "accepted"
  },
  {
   "id": "D-031",
   "t": "Phase order with ORE",
   "st": "accepted"
  },
  {
   "id": "D-032",
   "t": "ORE packaging",
   "st": "accepted"
  },
  {
   "id": "D-033",
   "t": "Model schema ore/1",
   "st": "accepted"
  },
  {
   "id": "D-034",
   "t": "Strict optimality default",
   "st": "accepted"
  },
  {
   "id": "D-035",
   "t": "Result status model",
   "st": "accepted"
  },
  {
   "id": "D-036",
   "t": "Resource defaults",
   "st": "accepted"
  },
  {
   "id": "D-037",
   "t": "First optional solver",
   "st": "proposed"
  },
  {
   "id": "D-038",
   "t": "Model approval",
   "st": "accepted"
  },
  {
   "id": "D-039",
   "t": "ORE documents",
   "st": "accepted"
  },
  {
   "id": "D-040",
   "t": "Versions with ORE",
   "st": "accepted"
  },
  {
   "id": "D-008",
   "t": "Approval trust levels",
   "st": "proposed"
  },
  {
   "id": "D-009",
   "t": "Dashboard technology",
   "st": "proposed"
  },
  {
   "id": "D-010",
   "t": "Human CLI",
   "st": "proposed"
  },
  {
   "id": "D-011",
   "t": "Automatic orchestration",
   "st": "proposed"
  },
  {
   "id": "D-013",
   "t": "Licensing and contributions",
   "st": "proposed"
  },
  {
   "id": "D-017",
   "t": "Git host integration",
   "st": "proposed"
  },
  {
   "id": "D-019",
   "t": "Release discipline",
   "st": "proposed"
  }
 ],
 "rtm": {
  "B1": {
   "Exists": 1,
   "Process": 2,
   "Planned": 29,
   "Done": 5,
   "In progress": 2,
   "Reconsidered": 2
  },
  "B2": {
   "Planned": 47,
   "Done": 2,
   "Reconsidered": 2
  },
  "B3": {
   "Done": 6,
   "Planned": 25,
   "Reconsidered": 2,
   "In progress": 1
  }
 },
 "issues": [
  {
   "id": "TD-03",
   "kind": "debt",
   "sev": "high",
   "t": "Detected checks de-duplicated across ecosystems (reproduced)"
  },
  {
   "id": "TD-04",
   "kind": "debt",
   "sev": "high",
   "t": "Detection inspects only the repository root (reproduced)"
  },
  {
   "id": "TD-08",
   "kind": "debt",
   "sev": "high",
   "t": "state.json schema never checked on load"
  },
  {
   "id": "R-17",
   "kind": "risk",
   "sev": "high",
   "t": "Engineering-intelligence layer turns the workflow bureaucratic"
  },
  {
   "id": "R-19",
   "kind": "risk",
   "sev": "high",
   "t": "Over-claiming intelligence: checks read as proof of design quality"
  },
  {
   "id": "R-22",
   "kind": "risk",
   "sev": "high",
   "t": "Optimization theatre: precise answers from invented numbers"
  },
  {
   "id": "R-23",
   "kind": "risk",
   "sev": "high",
   "t": "Solver guarantees misunderstood (tolerance read as proof)"
  },
  {
   "id": "R-03",
   "kind": "risk",
   "sev": "high",
   "t": "Engine under development manages its own development"
  },
  {
   "id": "S-04",
   "kind": "security",
   "sev": "high",
   "t": "Pulled config.json can change check commands without confirmation"
  },
  {
   "id": "TD-11",
   "kind": "debt",
   "sev": "medium",
   "t": "Timeouts kill only the direct child process (to confirm)"
  }
 ],
 "tests": [
  {
   "date": "2026-11-22",
   "what": "Baseline: 141 unit, scenario and doc tests",
   "result": "OK · 44.2 s",
   "ok": true
  },
  {
   "date": "2026-11-22",
   "what": "install.py doctor after installing v1.0.0",
   "result": "No problems found",
   "ok": true
  },
  {
   "date": "2026-11-22",
   "what": "F1.0.2: unit (147 tests) on Python 3.13 and 3.9, privacy, ruff, mypy",
   "result": "All passed · code 1705ed3d78",
   "ok": true
  },
  {
   "date": "2026-11-22",
   "what": "F1.0.3: 156 tests on 3.13 and 3.9, ruff, mypy, privacy, golden byte-identical",
   "result": "All passed · code 9b5f860b53",
   "ok": true
  },
  {
   "date": "2026-11-22",
   "what": "F6.0.2 CP-SAT trial: 1,650 models vs enumeration, gap trap, limits, cancellation, memory, threads (Python 3.13 and 3.9, macOS)",
   "result": "0 mismatches · all checks as expected",
   "ok": true
  },
  {
   "date": "2026-11-22",
   "what": "F1.0.2: GitHub Actions (lint job, 6 test jobs)",
   "result": "Not run until the owner pushes",
   "ok": false
  }
 ],
 "releases": [
  {
   "v": "v1.0.0",
   "date": "2026-11-12",
   "notes": "First release: 11-stage lifecycle, hash-bound approvals, evidence, Claude hooks, installer, bilingual guide"
  },
  {
   "v": "Unreleased",
   "date": "—",
   "notes": "Guided setup; dev tooling (ruff, mypy, golden CLI tests) from F1.0.2"
  }
 ]
};
