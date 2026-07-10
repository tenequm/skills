# Claude Code Skill Features

Features specific to skills running in Claude Code, beyond the base Agent Skills standard.

## Contents

- Invocation control
- Subagent execution (context: fork)
- Dynamic context injection
- Argument substitution
- Skill discovery and locations
- Bundled skills
- Skill content lifecycle
- Permission control
- Settings overrides
- Context budget

## Invocation Control

Two frontmatter fields control who can invoke a skill:

### disable-model-invocation: true

Only the user can invoke via `/skill-name`. Claude cannot auto-trigger. It also blocks the skill from being preloaded into subagents and, as of v2.1.196, from running when a scheduled task fires with the skill as its prompt.

Use for: deploy, commit, send-message - actions with side effects you want to control.

```yaml
---
name: deploy
description: Deploy the application to production
disable-model-invocation: true
---
```

### user-invocable: false

Only Claude can invoke. Hidden from `/` menu.

Use for: background knowledge that isn't actionable as a command.

```yaml
---
name: legacy-system-context
description: Context about the legacy authentication system
user-invocable: false
---
```

### Invocation Matrix

| Frontmatter | User can invoke | Claude can invoke | Description in context |
|-------------|----------------|-------------------|----------------------|
| (default) | Yes | Yes | Always |
| `disable-model-invocation: true` | Yes | No | Not loaded |
| `user-invocable: false` | No | Yes | Always |

### Additional frontmatter keys

- `display-name` - label shown in listings, independent of the invocation name.
- `default-enabled` - whether the skill is active by default.
- `fallback` - fallback behavior for the skill.

Frontmatter keys (and `metadata.*` keys) are parsed case-insensitively: kebab-case, snake_case, and camelCase all resolve to the same field.

## Subagent Execution

Add `context: fork` to run a skill in an isolated subagent. The skill content becomes the prompt. No conversation history access.

```yaml
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
---

Research $ARGUMENTS thoroughly:
1. Find relevant files using Glob and Grep
2. Read and analyze the code
3. Summarize findings with specific file references
```

The `agent` field selects the execution environment:
- `Explore` - read-only codebase exploration
- `Plan` - architectural planning
- `general-purpose` - full tool access (default)
- Custom agents from `.claude/agents/`

`context: fork` only works for skills with explicit task instructions, not passive guidelines.

## Dynamic Context Injection

The `` !`command` `` syntax runs shell commands before content reaches Claude:

```yaml
---
name: pr-summary
description: Summarize changes in a pull request
context: fork
agent: Explore
---

## Pull request context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`
- Changed files: !`gh pr diff --name-only`

## Your task
Summarize this pull request...
```

Each `` !`command` `` executes immediately, output replaces the placeholder. Claude only sees the final rendered content. This is preprocessing, not something Claude runs.

The inline form is recognized only when `!` is at the start of a line or immediately after whitespace. If `!` follows another character (e.g. `` KEY=!`cmd` ``), the placeholder is left as literal text and the command does not run.

**Documenting this syntax is itself a footgun.** The preprocessor is not markdown-aware: a literal example written in a SKILL.md or command file executes at load time even inside a code fence or inline code span, and a placeholder command that fails (e.g. a bare `cmd`) makes the whole skill error on load. Put live examples only in `references/` files - they are read with the Read tool and never preprocessed, which is why this file can show them - or break the trigger by keeping the `!` from directly touching the backtick (wrap the `!` in its own code span). Assume the fenced block form below carries the same hazard when nested inside a documentation fence.

For multi-line commands, use a fenced code block opened with ` ```! ` instead of the inline form:

````markdown
## Environment
```!
node --version
npm --version
git status --short
```
````

To disable shell execution for skills and custom commands from user, project, plugin, or additional-directory sources, set `"disableSkillShellExecution": true` in settings. Each command is replaced with `[shell command execution disabled by policy]`. Bundled and managed skills are unaffected.

## Argument Substitution

Skills support these substitution variables:

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed when invoking |
| `$ARGUMENTS[N]` | Specific argument by 0-based index |
| `$N` | Shorthand for `$ARGUMENTS[N]` |
| `$name` | Named argument declared in the `arguments` frontmatter list (bound by position) |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_EFFORT}` | Current effort level: `low`, `medium`, `high`, `xhigh`, or `max`. Ultracode is not a distinct level and reports as `xhigh` |
| `${CLAUDE_SKILL_DIR}` | Directory containing the skill's SKILL.md |
| `${CLAUDE_PROJECT_DIR}` | Project root (same path hooks/MCP servers receive). Requires v2.1.196+; works in the body and in `allowed-tools` |

To include a literal `$` before a digit, `ARGUMENTS`, or a declared argument name (e.g. `$1.00` in prose), escape it with a backslash: `\$1.00`. A backslash before any other `$` is left unchanged.

Example:

```yaml
---
name: fix-issue
description: Fix a GitHub issue
disable-model-invocation: true
---

Fix GitHub issue $ARGUMENTS following our coding standards.
1. Read the issue description
2. Implement the fix
3. Write tests
4. Create a commit
```

`/fix-issue 123` becomes "Fix GitHub issue 123 following our coding standards..."

If `$ARGUMENTS` is not present in content, arguments are appended as `ARGUMENTS: <value>`.

### Positional Arguments

```yaml
---
name: migrate-component
description: Migrate a component between frameworks
---

Migrate the $0 component from $1 to $2.
Preserve all existing behavior and tests.
```

`/migrate-component SearchBar React Vue` replaces `$0`=SearchBar, `$1`=React, `$2`=Vue.

### Named Arguments

Declare an `arguments` frontmatter field to give positions readable names:

```yaml
---
name: fix-issue
description: Fix a GitHub issue on a branch
arguments: [issue, branch]
---

Fix issue $issue on branch $branch.
```

`/fix-issue 123 hotfix` maps `$issue`=123, `$branch`=hotfix - names bind to positions in order.

## Skill Discovery and Locations

Priority order (higher wins on name conflicts):

| Location | Path | Scope |
|----------|------|-------|
| Enterprise | Managed settings | All org users |
| Personal | `~/.claude/skills/<name>/SKILL.md` | All your projects |
| Project | `.claude/skills/<name>/SKILL.md` | This project |
| Plugin | `<plugin>/skills/<name>/SKILL.md` | Where plugin enabled |

Enterprise overrides personal, and personal overrides project. Plugin skills use a `plugin-name:skill-name` namespace, so they never conflict with the other levels.

**Custom commands are skills.** A file at `.claude/commands/deploy.md` and a skill at `.claude/skills/deploy/SKILL.md` both create `/deploy`. Existing `.claude/commands/` files keep working; if a skill and a command share a name, the skill takes precedence. A personal, project, or enterprise skill also **overrides a same-named bundled skill** - a `code-review` skill in your project's `.claude/skills/` replaces the bundled `/code-review`.

**Command name vs. `name`.** The command you type after `/` is derived from the skill's directory, not its frontmatter `name`. Except for a plugin-root `SKILL.md`, `name` is only the display label shown in listings. A nested skill can be invoked explicitly by its qualified name, e.g. `/apps/web:deploy` runs the nested variant while `/deploy` runs the project-root one.

**Symlinks and skills-dir plugins.** A `<skill-name>` entry can be a symlink to a directory elsewhere; Claude Code follows it and, if the same target is reachable from multiple locations, loads the skill once. Add a `.claude-plugin/plugin.json` to a skill folder and it loads as a plugin named `<name>@skills-dir`, letting it bundle agents, hooks, and MCP servers.

**Malformed frontmatter.** If the YAML frontmatter is malformed, Claude Code loads the body with empty metadata - `/skill-name` still works but Claude has no `description` to match against for auto-triggering. Run with `--debug` to see the parse error.

### Automatic Discovery

- Skills in subdirectory `.claude/skills/` are auto-discovered when editing files there
- Skills from `--add-dir` directories are loaded and support live change detection
- Monorepo support: `packages/frontend/.claude/skills/` discovered when editing in that package
- Live change detection covers `SKILL.md` **text only**. For a skill folder that is also a plugin, changes to `hooks/`, `.mcp.json`, `agents/`, and `output-styles/` need `/reload-plugins`
- `/reload-skills` (v2.1.152+) re-scans skill and command directories so skills added or changed on disk during the session become available without restarting. A `SessionStart` hook can return `reloadSkills: true` to hot-load skills it installs

## Bundled Skills

Ships with Claude Code, available in every session unless disabled with the `disableBundledSkills` setting (or the `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS=1` env var):

| Skill | Purpose |
|-------|---------|
| `/batch <instruction>` | Parallel large-scale codebase changes via worktrees |
| `/claude-api` | Claude API/SDK reference for your project's language |
| `/code-review [effort] [--fix] [--comment]` | Review the diff for correctness bugs plus reuse/simplify/efficiency cleanups |
| `/debug [description]` | Enable debug logging, troubleshoot issues |
| `/design-sync` | Sync design/context artifacts |
| `/fewer-permission-prompts` | Scan transcripts and add a read-only allowlist to project settings |
| `/loop [interval] <prompt>` | Run a prompt repeatedly on an interval |
| `/simplify [focus]` | Review changed files for reuse, quality, efficiency. Since v2.1.154 it is cleanup-only - use `/code-review` to find correctness bugs |

Three more bundled skills launch and verify your app (require Claude Code v2.1.145+):

| Skill | Purpose |
|-------|---------|
| `/run` | Launch and drive your app to see a change working |
| `/verify` | Build and run your app to confirm a change, without falling back to tests |
| `/run-skill-generator` | Record a per-project recipe so `/run` and `/verify` know how to build and launch |

## Skill Content Lifecycle

When a skill is invoked, the rendered `SKILL.md` content enters the conversation as a single message and stays there for the rest of the session. Claude Code does not re-read the file on later turns - write standing instructions, not one-time steps.

Auto-compaction carries invoked skills forward within a token budget: after a summary, Claude Code re-attaches the most recent invocation of each skill, keeping the first 5,000 tokens of each. Re-attached skills share a combined budget of 25,000 tokens, filled from the most recently invoked skill - so older skills can be dropped after compaction. Re-invoke a skill after compaction to restore its full content.

## Permission Control

### Pre-approve tools per skill

`allowed-tools` grants permission for the listed tools while the skill is active, so Claude uses them without a prompt. It does **not** restrict which tools are available - every tool stays callable, and your permission settings still govern the rest. Accepts a space-separated string or a YAML list:

```yaml
---
name: safe-reader
description: Read files without making changes
allowed-tools: Read Grep Glob
---
```

To block a skill from a tool, add a deny rule in permission settings instead.

### Remove tools while a skill is active

`disallowed-tools` removes the listed tools from Claude's available pool while the skill is active - use it for autonomous skills that should never call certain tools (e.g. `AskUserQuestion` in a background loop). The restriction clears when you send your next message. To block tools across all skills and prompts, use deny rules in permission settings.

```yaml
---
name: background-loop
description: Run unattended
disallowed-tools: AskUserQuestion
---
```

### Restrict Claude's skill access

In `/permissions` deny rules:
- `Skill` - disable all skills
- `Skill(deploy *)` - deny specific skill
- `Skill(commit)` - deny exact match

A few built-in commands are also reachable through the Skill tool: `/init`, `/review`, `/security-review`. Others such as `/compact` are not.

### Path-based activation

```yaml
---
name: frontend-lint
description: Lint frontend code
paths: "src/components/**/*.tsx, src/pages/**/*.tsx"
---
```

Skill only activates when working with files matching the patterns.

## Settings Overrides

`skillOverrides` controls skill visibility from settings instead of the skill's own frontmatter - useful for skills you don't want to edit (shared repo, MCP-provided). Each key is a skill name; each value is one of four states:

| Value | Listed to Claude | In `/` menu |
|-------|-----------------|-------------|
| `"on"` | Name and description | Yes |
| `"name-only"` | Name only | Yes |
| `"user-invocable-only"` | Hidden | Yes |
| `"off"` | Hidden | Hidden |

A skill absent from `skillOverrides` is treated as `"on"`. The `/skills` menu writes it to `.claude/settings.local.json` for you. Plugin skills are unaffected.

## Context Budget

Skill descriptions are loaded into context at startup. The budget scales at **1% of the model's context window**. When it overflows, the descriptions of least-used skills are dropped first; names are always kept.

Run `/doctor` to see whether the budget is overflowing and which skills are affected.

Raise the budget with the `skillListingBudgetFraction` setting (e.g. `0.02` = 2%) or the `SLASH_COMMAND_TOOL_CHAR_BUDGET` env var (fixed character count). Independently, each entry's combined `description` + `when_to_use` text is capped at **1,536 characters** in the listing (configurable via `skillListingMaxDescChars`). Both settings require Claude Code v2.1.105+. Set low-priority skills to `"name-only"` in `skillOverrides` to free budget.

As of v2.1.196, the Skills row in `/context` reports the listing size *after* the budget is applied, so it matches what the model actually receives.

## Extended Thinking

To enable extended thinking in a skill, include the word "ultrathink" anywhere in the skill content.

## Shell Override

For Windows PowerShell support:

```yaml
---
shell: powershell
---
```

Requires `CLAUDE_CODE_USE_POWERSHELL_TOOL=1`.
