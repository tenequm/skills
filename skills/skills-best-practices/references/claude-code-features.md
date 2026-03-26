# Claude Code Skill Features

Features specific to skills running in Claude Code, beyond the base Agent Skills standard.

## Contents

- Invocation control
- Subagent execution (context: fork)
- Dynamic context injection
- Argument substitution
- Skill discovery and locations
- Bundled skills
- Permission control
- Context budget

## Invocation Control

Two frontmatter fields control who can invoke a skill:

### disable-model-invocation: true

Only the user can invoke via `/skill-name`. Claude cannot auto-trigger.

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

## Argument Substitution

Skills support these substitution variables:

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed when invoking |
| `$ARGUMENTS[N]` | Specific argument by 0-based index |
| `$N` | Shorthand for `$ARGUMENTS[N]` |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_SKILL_DIR}` | Directory containing the skill's SKILL.md |

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

## Skill Discovery and Locations

Priority order (higher wins on name conflicts):

| Location | Path | Scope |
|----------|------|-------|
| Enterprise | Managed settings | All org users |
| Personal | `~/.claude/skills/<name>/SKILL.md` | All your projects |
| Project | `.claude/skills/<name>/SKILL.md` | This project |
| Plugin | `<plugin>/skills/<name>/SKILL.md` | Where plugin enabled |

### Automatic Discovery

- Skills in subdirectory `.claude/skills/` are auto-discovered when editing files there
- Skills from `--add-dir` directories are loaded and support live change detection
- Monorepo support: `packages/frontend/.claude/skills/` discovered when editing in that package

## Bundled Skills

Ships with Claude Code, available in every session:

| Skill | Purpose |
|-------|---------|
| `/batch <instruction>` | Parallel large-scale codebase changes via worktrees |
| `/claude-api` | Claude API/SDK reference for your project's language |
| `/debug [description]` | Enable debug logging, troubleshoot issues |
| `/loop [interval] <prompt>` | Run a prompt repeatedly on an interval |
| `/simplify [focus]` | Review changed files for reuse, quality, efficiency |

## Permission Control

### Restrict tool access per skill

```yaml
---
name: safe-reader
description: Read files without making changes
allowed-tools: Read, Grep, Glob
---
```

### Restrict Claude's skill access

In `/permissions` deny rules:
- `Skill` - disable all skills
- `Skill(deploy *)` - deny specific skill
- `Skill(commit)` - deny exact match

### Path-based activation

```yaml
---
name: frontend-lint
description: Lint frontend code
paths: "src/components/**/*.tsx, src/pages/**/*.tsx"
---
```

Skill only activates when working with files matching the patterns.

## Context Budget

Skill descriptions are loaded into context at startup. Budget: **2% of context window** (fallback: 16,000 characters).

If you have many skills and some are excluded, check with `/context`.

Override with env var: `SLASH_COMMAND_TOOL_CHAR_BUDGET=32000`

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
