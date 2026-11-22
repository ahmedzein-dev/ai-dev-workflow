#!/usr/bin/env python3
"""AIDevWorkflow engine for the ai-dev-workflow skill.

Structured AI-Assisted Development - From Requirements to Release.

Records task state, approvals and verification evidence for tasks the user
explicitly starts with the ai-dev-workflow skill, and refuses stage changes whose
prerequisites are not met. Standard library only; Python 3.9 or newer.

This file is the entry point; the engine lives in the aidw package next to it.
Names are re-exported here for compatibility; to patch engine internals in tests, patch them in their
aidw module (patching a name on this module does not affect calls inside the package).
Run `workflow.py --help` or `workflow.py <command> --help` for usage.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Like the former single-file engine, never write bytecode caches into the skill folder: project-level installs live
# inside users' repositories, where __pycache__ folders would show up as untracked files.
sys.dont_write_bytecode = True
# The bundled package wins over any other module named aidw (the hooks run this file by absolute path).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import locale  # noqa: E402,F401  (tests patch workflow.locale and workflow.shutil)
import shutil  # noqa: E402,F401

from aidw import __version__  # noqa: E402,F401
from aidw.adapters.detect import (  # noqa: E402,F401
    PY_CMD, TRANSLATION_DIRS, _builtin, _check, _dart_checks, _node_checks,
    _other_checks, _python_checks, _read, _tool_found, _translation_check, ci_commands,
    detect_checks, project_files,
)
from aidw.agents.claude_hooks import (  # noqa: E402,F401
    _deny, _find_records, _hook_log, cmd_hook, gate_decision, hook_claude_pre_edit,
    hook_claude_prompt,
)
from aidw.api import (  # noqa: E402,F401
    change_checks, install_template, open_tasks, scan_records, status_line, task_summary,
    validate_task,
)
from aidw.cli.commands import (  # noqa: E402,F401
    cmd_approve, cmd_check, cmd_close, cmd_decision, cmd_discover, cmd_init,
    cmd_new, cmd_outcome, cmd_pause, cmd_plan_check, cmd_preflight, cmd_resume,
    cmd_review, cmd_run, cmd_scope, cmd_spec_check, cmd_stage, cmd_status,
    cmd_step, ensure_commit_mode, print_discovery, print_spec_check, resolve_template, update_setup,
)
from aidw.cli.helpers import (  # noqa: E402,F401
    print_summary, require_task,
)
from aidw.cli.main import (  # noqa: E402,F401
    build_parser, main,
)
from aidw.constants import (  # noqa: E402,F401
    CODE_STAGES, COMMIT_MODES, DEFAULT_VAGUE_WORDS, DEP_CLASSES, DEP_GATES, DEP_TYPES,
    DISPOSITIONS, INDEPENDENCE, INSTRUCTION_CANDIDATES, INVOCATION_RE, NEXT, OUTCOMES,
    OUTCOME_RANK, PLAN_NONE_OK, PLAN_SECTIONS, RECORDS, RECORD_FILES, REFERENCE,
    REPORT_SECTIONS, SEVERITIES, SKILL_DIR, SKILL_NAME, SLUG_RE, STAGES,
    TASK_TYPES, TEMPLATES_DIR, VERIFY_STATUS,
)
from aidw.core.checks import (  # noqa: E402,F401
    ANALYZER_RE, analyzer_key, builtin_check, decode_command_output, execute, flatten_keys,
    glob_match, glob_to_regex, last_line, manifest_dependencies, parse_analyzer, regenerate_check_block,
)
from aidw.core.gates import (  # noqa: E402,F401
    approval_status, approved_doc, check_freshness, expected_items, forward_problems, latest_results,
    plan_steps, transition,
)
from aidw.core.outcome import (  # noqa: E402,F401
    compute_outcome,
)
from aidw.core.setup import (  # noqa: E402,F401
    DISCOVERY_ONLY_KEYS, OSS_LICENSE_RE, RECORDS_README, RECORD_NOTES, RECORD_OPTIONS, apply_commit_mode,
    commit_mode_applied, default_template_info, discover_project, existing_setup, library_settings,
    recommend_commit, template_proposal,
)
from aidw.core.spec import (  # noqa: E402,F401
    advisory_warnings, checklist_items, judgment_flags, plan_check, spec_check, spec_rules_and_template,
    verification_items,
)
from aidw.errors import (  # noqa: E402,F401
    WorkflowError,
)
from aidw.infra.gitutil import (  # noqa: E402,F401
    SKILL_INSTALL_PREFIXES, _blob_hash, change_set, code_fingerprint, file_at, find_repo,
    git_baseline, git_ok, git_proc, hash_paths, is_records_path, is_tooling_path,
    run_git, worktree_changes,
)
from aidw.infra.secrets import (  # noqa: E402,F401
    ASSIGNMENT_RE, PLACEHOLDER_VALUE_RE, SECRET_PATTERNS, assert_no_secrets, find_secrets, redact,
)
from aidw.infra.text import (  # noqa: E402,F401
    agent_name, bullet_list, clean_session, load_json, make_readonly, norm,
    now_iso, read_text, save_json, sha256_file, sha256_text, short,
    write_text,
)
from aidw.records.markdown import (  # noqa: E402,F401
    CHECKBOX_RE, COMMENT_RE, Doc, EMPTY_CHECKBOX_RE, FENCE_RE, HEADING_RE,
    HR_RE, ID_RE, INLINE_CODE_RE, LABEL_RE, LETTER_RE, MARKER_RE,
    NONE_RE, ROW_RE, SEP_RE, TOKEN_RE, TemplateInfo, block_entries,
    check_ids, check_markers, check_placeholders, check_structure, clean_tokens, is_none_entry,
    issue, split_row, strip_md, target_entries, target_texts,
)
from aidw.records.parsers import (  # noqa: E402,F401
    _has_message, blocking_deps, parse_audit, parse_dependencies, parse_matrix, parse_report,
)
from aidw.store.config import (  # noqa: E402,F401
    config_path, library_dir, load_config, load_rules, record_template, records_dir,
    task_dir, template_path,
)
from aidw.store.state import (  # noqa: E402,F401
    activate, active_path, add_checkpoint, add_history, clear_active, list_tasks,
    load_state, read_active, save_state, state_path,
)


if __name__ == "__main__":
    sys.exit(main())
