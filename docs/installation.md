# Installation

AIDevWorkflow needs **git** and **Python 3.9+** on every machine (or cloud environment) where an agent runs it.

## User-level install (recommended)

Install once, use in every project:

```bash
git clone https://github.com/ahmedzein-dev/ai-dev-workflow.git
cd ai-dev-workflow
python3 skills/ai-dev-workflow/scripts/install.py
python3 skills/ai-dev-workflow/scripts/install.py doctor
```

What the installer does:

| Location | Used by | How |
|---|---|---|
| `~/.agents/skills/ai-dev-workflow` | Codex, Gemini CLI | the canonical copy |
| `~/.claude/skills/ai-dev-workflow` | Claude Code | symlink to the canonical copy (a copy if symlinks are not available) |
| `~/.gemini/config/skills/ai-dev-workflow` | Antigravity (app, IDE, CLI) | symlink or copy; only if Antigravity is detected or `--agents` includes it |

Options:

```bash
install.py --agents claude,codex,gemini,antigravity   # choose agents (default: auto-detect)
install.py --copy                                      # copies instead of symlinks
install.py --dry-run                                   # show what would happen
install.py --link-source                               # canonical copy points at this clone (for development)
```

`doctor` checks Python and git, the canonical copy, every link or copy (reporting drift when a copy differs), and
duplicates (for example a second copy in `~/.gemini/skills`, which Gemini CLI would also read).

### Agent-native alternatives

- **Gemini CLI** can manage the skill itself: `gemini skills link <clone>/skills/ai-dev-workflow` (symlink, updates
  follow the clone) or `gemini skills install <clone>/skills/ai-dev-workflow` (copy). Use either this or the
  installer, not both.
- **Manual copy**: copy `skills/ai-dev-workflow/` into the agent's skills folder (see
  [compatibility](compatibility.md)). The folder name must stay `ai-dev-workflow`.

## Project-level install

For teammates and cloud agents (Codex cloud, Claude Code on the web and similar) that only see the repository:

```bash
python3 skills/ai-dev-workflow/scripts/install.py install --project /path/to/repo
python3 skills/ai-dev-workflow/scripts/install.py doctor --project /path/to/repo
```

This writes **real copies** (no symlinks) to `.agents/skills/ai-dev-workflow` (Codex, Gemini CLI, Antigravity) and
`.claude/skills/ai-dev-workflow` (Claude Code). Commit both folders. Use `--symlinks` to link the Claude folder to
the `.agents` copy instead, if every checkout supports symlinks.

Notes:

- Use either a user-level or a project-level install for a given project, not both; otherwise some agents list
  the skill twice. `doctor` warns about this.
- Gemini CLI loads project-level skills only in trusted folders.
- Codex's `workspace-write` sandbox keeps `.agents/` read-only, which is fine: the skill is never modified at run time.

## Symlinks, Windows and cloud environments

Symlinks are not guaranteed everywhere. On Windows they need Developer Mode or administrator rights, git may check
them out as plain files, and cloud sandboxes vary. The installer falls back to copies automatically and records a
manifest in each copy; `install.py doctor` reports any copy that drifts from the canonical one, and
`install.py update` refreshes them.

## Private specification templates

Keep personal templates outside any repository and offer them to projects:

```bash
python3 skills/ai-dev-workflow/scripts/install.py add-template my-template /path/to/spec-template.md \
    --rules /path/to/spec-template.rules.json
python3 skills/ai-dev-workflow/scripts/install.py list-templates
```

Templates are stored in `~/.ai-dev-workflow/templates/<name>/` (or `$AI_DEV_WORKFLOW_HOME`). A project uses one
only when you choose it during setup (`user:my-template`).

## Updating

```bash
cd ai-dev-workflow && git pull
python3 skills/ai-dev-workflow/scripts/install.py update
python3 skills/ai-dev-workflow/scripts/install.py update --project /path/to/repo   # if you use project installs
```

## Uninstalling

```bash
python3 skills/ai-dev-workflow/scripts/install.py uninstall          # shows what would be removed
python3 skills/ai-dev-workflow/scripts/install.py uninstall --yes
```

The uninstaller only removes folders and links it recognizes as `ai-dev-workflow`. Task records in your projects
(`.ai-dev-workflow/`) are never touched.

## Troubleshooting

| Symptom | Check |
|---|---|
| The agent does not know the skill | Restart the agent or start a new session; run `install.py doctor`; check the agent's folder in [compatibility](compatibility.md) |
| Claude Code shows the skill but the hooks never fire | Confirm the skill was invoked in this session; hooks register on invocation |
| `python3` not found | Use `python`, or install Python 3.9+ |
| The skill is listed twice | Remove either the user-level or the project-level install |
