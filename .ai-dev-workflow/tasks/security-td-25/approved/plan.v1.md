# Implementation Plan: TD-25: keep secret-like check ids and agent names out of task records

> Spec: 2fdbc034 (revised after the owner's nine points; becomes approved version v1)
> Frozen once approved. Progress is recorded with `workflow.py step`, never by editing this plan.

## 1. Goal

Refuse a secret-like agent name, session id or check name as the first step of every API function that takes one,
before any command runs or any file is written. Make the two affected multi-file writes (`run_check`, `new_task`)
unable to leave a refused or half-created record behind. Document the persistence and detection limits that remain,
and plan the v1.0.1 patch release that brings the fix to installed copies.

## 2. Current Behavior

Inspected in discovery (records: discovery summary, dependencies.md DEP-2):
- **Identity values reach the API unchecked.**
  - `infra/text.py` L71–72: `agent_name(args)` returns `--agent`, or else `AI_DEV_WORKFLOW_AGENT`, or else
    `unknown-agent`.
  - `infra/text.py` L65–68: `clean_session` drops only empty values, `${…}`, `none` and `null`.
  - No API function checks either value. The only secret check on them is `save_state` (`store/state.py` L45–48),
    which scans the whole `state.json` just before writing it.
- **`run_check`** (`api.py` L761–849):
  - The check name is used as given (L769–777). For an unknown name without `--`, the refusal message prints it
    (L774).
  - The command runs (L805), and `regenerate_check_block` writes `verification.md` (L848, `core/checks.py`
    L238–258) **before** `save_state` (L849).
  - A secret-like check name or agent name therefore lands in the check block, and then `state.json` is refused.
- **`new_task`** (`api.py` L384–439):
  - The order is: commit-mode exclude rules (L399), `mkdir` (L422), six record files (L423–425), then `activate`
    (L437), which may pause another task's `state.json` and writes `ACTIVE` (`store/state.py` L95–113).
  - `save_state` comes last (L438).
  - A refusal there leaves the folder without `state.json`; the name is then blocked ("already exists; resume it",
    and resume cannot work).
- **`resume`** (L649–661) and **`preflight`** (L678–718) write `ACTIVE` (through `activate`, or `save_json` at L716)
  before `save_state`. A secret-like `--session` is stored in `ACTIVE` and `resume` succeeds, because `state.json`
  does not hold the session.
- **File writes:** `write_text` (`infra/text.py` L33–38) writes a temporary file and calls `os.replace`, so each
  file is replaced atomically. There is no fsync, a failed write can leave the temporary file, and there is no
  multi-file transaction or lock (F1.0.5).
- **Reproduced** with a synthetic token on this engine and on the installed v1.0.0 (DEP-2). The installed v1.0.0 is
  the monolithic `scripts/workflow.py` (2,996 lines) at tag `v1.0.0`. `main` is 14 unreleased commits ahead of
  that tag.

## 3. Proposed Solution

All changes are in `aidw/api.py`, at layer 4, as the F1.0.4 layering requires. No new modules, classes or packages.

**Two private helpers next to `_root` / `_task`:**

```python
def _check_agent(agent: str) -> None:
    assert_no_secrets(agent, "the agent name")

def _check_session(session: Optional[str]) -> None:
    value = clean_session(session)
    if value is None:
        return
    assert_no_secrets(value, "the session id")
    if not (len(value) <= 256 and value.isprintable() and not any(ch.isspace() for ch in value)):
        raise WorkflowError("The session id must be 1–256 printable characters without spaces.")
```

They reuse the existing detection (`assert_no_secrets`, whose message names the field and the kind, never the value)
and the existing placeholder rule (`clean_session`).

**Call sites (FR-1 to FR-3):**
- **The 15 functions of FR-1:** `_check_agent(agent)` is the first statement, before any other check, `_root`,
  `_task`, any write and any command.
- **`new_task`, `resume`, `preflight`:** `_check_session(session)` right after `_check_agent`.
- **`run_check`:** `assert_no_secrets(check, "the check name")` right after `_check_agent`, before `_task` and before
  the configured-check lookup.

**Write order (FR-4, FR-5):**
- **`run_check`:** `save_state(root, state)` first, then `regenerate_check_block(root, state)`. The check block is a
  view of `state.json`, so it is never ahead of it. An error writing the block propagates as before; the
  `output_tail` attribute is kept.
- **`_create_task`:** the order becomes `mkdir` → record files → `add_history` → `save_state` (new task) →
  `activate`. The writes from `mkdir` up to and including that `save_state` are wrapped in `try/except BaseException`.
  If the folder was created by this call and `state.json` was not yet saved, the folder is removed
  (`shutil.rmtree`); a failed removal never hides the original error, which is re-raised unchanged. The returned
  data and every file's final content stay the same.

**Documentation (FR-9, FR-10, FR-11):**
- **CHANGELOG "Unreleased → Security":** the new refusals and the session-id format.
- **TECHNICAL_DEBT.md:**
  - TD-25 status: "fixed on the development branch; installed copies still affected until v1.0.1";
  - new rows TD-27 (approve snapshot not scanned), TD-28 (echoing refusal messages; `|`/line breaks in check names)
    and TD-29 (multi-file persistence limits, linked to F1.0.5).
- **report.md:** the persistence and detection limits.

## 4. Affected Areas

- **Changed:** `skills/ai-dev-workflow/scripts/aidw/api.py`, `CHANGELOG.md`.
- **New:** `tests/test_secret_identity.py`.
- **Roadmap files (standing rule):** `docs/roadmap/TECHNICAL_DEBT.md`, `PROGRESS.md`, `roadmap-data.js`.
- **Unchanged by design:**
  - `aidw/infra/secrets.py`, `aidw/store/`, `aidw/core/`, `aidw/cli/`, `aidw/agents/`;
  - every existing test and golden file;
  - `SKILL.md`, `references/`, `install.py`;
  - the records of other tasks.

## 5. Implementation Steps

- **S1:** Write `tests/test_secret_identity.py` first (FR-8; AC-1 to AC-6, AC-9, AC-10; EC-1 to EC-13).
  - Run it on the unchanged engine: the DEP-2 tests must fail.
  - Run it against `git archive` exports of `5a7576a` (CLI classes) and `fa6a676` (CLI and API classes).
  - Record the failing lists in verification.md.
  - Run the existing suite to confirm that it still passes untouched.
- **S2:** Add `_check_agent` and `_check_session` and call them first in the 15 functions, plus the check-name check
  in `run_check` (FR-1, FR-2, FR-3, FR-6; EC-1 to EC-5, EC-7 to EC-9, EC-11). Run the new and the existing tests.
- **S3:** Reorder `run_check` and `_create_task` and add the folder cleanup (FR-4, FR-5; EC-6, EC-12, EC-13). Run
  the full suite on Python 3.13 and 3.9.
- **S4:** Verification through the engine (AC-7, AC-8):
  - `unit`, `unit-py39`, `privacy`, `ruff`, `mypy`;
  - the byte comparison of every existing golden file;
  - the pins against `5a7576a`;
  - a grep that no repository file contains a literal secret-like test value;
  - the exposure check over this repository's records and `ACTIVE`, counts only (DW-6).
- **S5:** Documentation (FR-9, FR-10, FR-11; AC-11): CHANGELOG, TECHNICAL_DEBT (TD-25 status, TD-27, TD-28, TD-29),
  PROGRESS, `roadmap-data.js`.
- **S6:** Publish and review the change (DW-4, DW-5):
  - Commit and push, with the owner's approval.
  - CI on Linux, Windows and macOS × Python 3.9/3.13 (DW-4).
  - An independent read-only audit, given the spec, the plan and the diff, not my conclusions. It checks every FR
    and AC and verifies that no secret check, gate or refusal was weakened (DW-5).
  - FIXING for anything found.
- **S7:** Final report.
  - Status no higher than `outcome` allows.
  - TD-25 stays open for installed copies.
  - Propose the follow-up task for v1.0.1 (§9, Release follow-up) as a separate session card (DW-7).

## 6. Important Technical Decisions

- **Refuse, not redact.** Every other free-text input already goes through `assert_no_secrets` and is refused (title,
  evidence, reasons, notes, decisions). Redacting an agent name or check name would silently change attribution in
  the records, and the user would not learn that a credential was typed.
- **Check in the API, not in the CLI.** Every front end (CLI, hooks, the future dashboard and orchestrator) goes
  through the API, and the CLI stays a renderer (F1.0.4, AC-3).
- **Check first.** A fixed position ("first statement") is simple to verify for all 15 functions, and it changes
  nothing for legitimate values. Its only effect on ordering is that a secret-like identity value wins over other
  refusals (EC-9).
- **Session format: a bounded structure, not a charset.** Alternatives:
  - UUID only: breaks unknown agents' ids.
  - `[A-Za-z0-9._-]`: may break ids with `:` `/` `+` `=` or `@`.
  - No format: leaves line breaks and control characters that can corrupt `ACTIVE` readers.

  The rule "1–256 printable characters, no whitespace" accepts every documented and plausible single-token id
  (Claude Code UUIDs are 36). It refuses explicitly, never silently. It does not detect secrets: tokens are single
  tokens too (FR-10).
- **Agent names: no format rule.** The documentation allows "other" as free text, so the secret check alone applies.
- **New task recovery: save before activating, remove own folder on failure.** A journal or transaction would be the
  storage rewrite that the owner excluded (F1.0.5). After this change, a failed `new` leaves either no folder or a
  complete task. A failure inside `activate` after the save leaves a complete but inactive task, which `resume`
  fixes (TD-29).
- **`run_check`: save first, then derive the block.** The rejected alternative is pre-scanning the state JSON before
  writing the block. It duplicates `save_state` and still leaves two writes in the wrong order.

## 7. Edge Cases

- **EC-1, EC-2:** `run` with a secret-like check name. The check-name check happens before `_task`, the lookup and
  `execute`, so neither the marker script nor the "Unknown check" message is reached.
- **EC-3, EC-4:** `run` with a secret-like agent name. `_check_agent` comes first. The CLI resolves
  `AI_DEV_WORKFLOW_AGENT` into `agent`, so one check covers both.
- **EC-5 to EC-7:** a secret-like agent name or session in `new`, `resume` or `preflight`. The checks run before
  `activate`, `save_json(ACTIVE)` or `mkdir`. For `new`, they also run before the commit-mode exclude rules (L399).
- **EC-8:** placeholders. `clean_session` runs before both session checks. `'api_key=changeme'` is a placeholder for
  `find_secrets`. A UUID passes the format rule.
- **EC-9:** the agent check precedes `SLUG_RE` and every other refusal. With legitimate values, the existing order is
  untouched, which the 27 pins show.
- **EC-10:** an existing `ACTIVE` is not migrated. The report gives `pause <task>` as the clean-up. The exposure
  check covers this repository's `ACTIVE`.
- **EC-11:** the format rule, tested with a line break, a tab, a space, U+200B and 257 characters. Exactly 256
  characters passes.
- **EC-12:** `aidw.api.save_state` patched to raise `OSError` during `new_task`. The test asserts that the folder is
  gone, the other task and `ACTIVE` are byte-identical, and the `OSError` propagates.
- **EC-13:** `aidw.api.regenerate_check_block` patched to raise `OSError` in `run_check`. The test asserts that the
  error propagates and `state.json` has the entry, then that an unpatched `run` makes the block match `state.json`.
- **Windows:** extra commands use a script file, not `python -c` quoting (the lesson from the second F1.0.4 CI
  failure). Working directories are restored with `try/finally`.

## 8. Testing Plan

`tests/test_secret_identity.py` (synthetic values built at run time, for example `"ghp_" + "A" * 36` and
`"sk-ant-" + "b" * 24`, so no literal token is stored):

| Class | Covers | How |
|---|---|---|
| `CliRefusalTest` | AC-1, AC-2, AC-3; EC-1 to EC-7, EC-11 | CLI through the existing `wf` runner of `tests/helpers.py` (subprocess for the `AI_DEV_WORKFLOW_AGENT` case). Before and after each command it takes a byte snapshot of every file under `.ai-dev-workflow/` and `.git/info/exclude`, asserts that the value is absent from stdout and stderr, asserts the field name in the message, and asserts that the marker file is absent |
| `ApiRefusalTest` | AC-4 | Each of the 15 functions with a secret-like `agent` on a repository in the right stage; `new_task`, `resume`, `preflight` with secret-like and malformed `session`; the same snapshot assertion |
| `LegitimateValuesTest` | AC-5; EC-8, EC-9 | Placeholder session, UUID session, 256-character token, `'api_key=changeme'` agent. The commands succeed with today's output. A bad task name with a legitimate agent keeps today's refusal |
| `RecoveryTest` | AC-9, AC-10; EC-12, EC-13 | Patched failures as in §7 |

- **Old-engine proof (AC-6):** the file is copied into exports of `5a7576a` and `fa6a676`. API classes skip where
  `aidw.api` does not exist (`5a7576a`). verification.md records each failing and passing test.
- **Existing safety net (AC-7):** the full suite on Python 3.13 and 3.9, the 27 refusal pins, the late-refusal pin,
  the signature pin, and a byte comparison of `tests/golden/` with the copy taken before S2.
- **Static and privacy (AC-8):** ruff, mypy, `tools/prepublish_check.py`, and a grep for the token patterns in the
  repository (expect 0).
- **Documentation (AC-11):** reviewed in the audit.
- **CI:** the `tests` workflow, 7 jobs.

## 9. Risks and Dependencies

- **Installed copies stay vulnerable until v1.0.1.** Until then the mitigation is operational: agents pass fixed
  names (`claude-code`), and the owner never types credentials into `--agent`, `--session` or check names.
- **False positives:** a legitimate value that looks like a credential, for example an agent name `password=…`, is
  now refused, with a message that says why. This is acceptable for a security control.
- **Session ids with spaces or over 256 characters from an unknown agent** are refused explicitly. Documented in the
  CHANGELOG; no such format is known.
- **Folder cleanup on Windows:** a file held open could make `rmtree` fail. The original error is still raised, and
  the leftover folder is the pre-existing behaviour, documented under TD-29.
- **Detection limits:** formats unknown to the scanner pass (FR-10). Pattern changes are out of scope.
- **Dependencies:** DEP-1 to DEP-3 are Verified; nothing blocks.

**Release follow-up (FR-11), a separate task `security-release-v1-0-1` with its own spec and plan approvals:**
- **R1:** Branch `release/1.0.x` from tag `v1.0.0`. Its CI also runs on `release/**`.
- **R2:** Port FR-1 to FR-6 into v1.0.0's monolithic `scripts/workflow.py`, with only the security fix and no
  features from `main` or Phase 1. Adapt the CLI regression tests to v1.0.0. Show that they fail on `v1.0.0` and
  pass on the patched code.
- **R3:** Version 1.0.1 (`__version__` and the install metadata), and a CHANGELOG section "1.0.1 — Security". It
  covers affected versions (≤ 1.0.0, and `main` before the fix), impact, the fix and mitigation, with no secret
  values.
- **R4:** CI on Linux, Windows and macOS × Python 3.9/3.13, plus an independent audit.
- **R5 (owner approval):** tag `v1.0.1`, push it, and publish the GitHub release notes. Publishing a GitHub security
  advisory is the owner's choice.
- **R6 (owner approval):** `install.py update` from the v1.0.1 checkout for every install (user and project), then
  `install.py doctor`. Check that `.aidw-install.json` shows 1.0.1, and repeat the CLI regression scenarios against
  the installed copy.
- **R7:** Bring the fix to `main`, which has 14 unreleased commits. Mark TD-25 **Resolved** only after R6.

## 10. Expected Result

- A secret-like agent name (from `--agent` or `AI_DEV_WORKFLOW_AGENT`), session id or check name is refused before
  anything runs or is written, without echoing it.
- `new` leaves no partial folder.
- `verification.md` never runs ahead of `state.json`.
- Legitimate use is byte-for-byte unchanged.
- The remaining persistence and detection limits are written down.
- The path to fix installed copies (v1.0.1) is planned and tracked, with TD-25 open until it is done.
