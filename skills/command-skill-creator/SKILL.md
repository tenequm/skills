---
name: command-skill-creator
description: Create automation command skills (slash commands) for Claude Code projects. Use when building `/slash-commands` that automate multi-step workflows - deploys, commits, releases, migrations, cross-repo operations, or any repeatable process. Triggers on "create a command", "make a slash command", "automate this workflow", "turn this into a command", "build a command skill", or when designing phased execution skills with approval gates. For command-type skills (imperative prompts in `.claude/skills/`), NOT knowledge/reference skills.
metadata:
  version: "0.1.1"
---

# Command Skill Creator

Create command-type skills - imperative prompts that guide Claude through phased execution of multi-step workflows. These are `/slash-commands` users invoke explicitly, not passive reference material.

Command skills live in project-level `.claude/skills/<name>/SKILL.md` and are invoked as `/name [arguments]`.

## When to use this vs skill-creator

- **This skill**: Commands that DO things - deploy, commit, migrate, sync, release, scaffold. Side effects, approval gates, phased execution.
- **skill-creator**: Knowledge that INFORMS Claude - coding standards, API references, framework guides. No side effects, auto-triggered by context.

## Creation Workflow

### Step 1: Understand Intent

Establish what the command automates. Ask (or extract from conversation context):

- What does this command do? What are the major phases?
- Which actions have side effects? (commits, deploys, file mutations, external APIs)
- Does it take arguments? What kind?
- Does it operate across multiple repos/projects?
- Are there approval gates needed before irreversible actions?
- What model complexity is needed? (most commands work with default; complex multi-phase reasoning may need `opus`)

If the user says "turn this into a command," extract the workflow from conversation history - tools used, sequence, corrections made.

### Step 2: Design Frontmatter

Choose fields based on the command's nature. See the frontmatter reference table below.

Minimum viable frontmatter:
```yaml
---
name: my-command
description: What it does and when to use it
disable-model-invocation: true
---
```

The reason `disable-model-invocation: true` is the default for command skills: commands have side effects by definition. If it had no side effects, it would be a knowledge skill instead. Setting this to `true` ensures the command only runs when the user explicitly invokes it, preventing Claude from autonomously deploying, committing, or mutating state.

Add more fields based on characteristics:
- Takes arguments → `argument-hint: "[arg-name]"`
- Needs strong reasoning → `model: opus`
- Should restrict tools → `allowed-tools: Read, Bash(specific-cmd *)`
- Self-contained exploration → `context: fork` + `agent: Explore`

### Step 3: Structure Phases

Break the command into numbered phases with markdown headers (`##`). Claude follows numbered sequences with headers reliably - dense paragraphs get lost.

Common phase progression:
1. **Pre-flight** - validate preconditions, read config, check state
2. **Research/Discovery** - gather info for decisions (parallelize with subagents when possible)
3. **Present/Approve** - show recommendations, wait for explicit user approval
4. **Execute** - make the changes
5. **Verify** - smoke tests, health checks
6. **Summary** - report outcomes

Not every command needs all phases. A simple formatter might just be execute + verify.

### Step 4: Add Safety

For each phase with side effects:
- **Approval gate**: "**STOP and wait for user approval before proceeding.**"
- **Error handling**: "If X fails, stop and show the error. Do NOT proceed to Phase N."
- **Rollback path**: How to undo if something goes wrong
- **Verification**: Check that each action succeeded before moving on

These aren't bureaucracy - they prevent the command from autonomously deploying broken code or committing garbage. A 2-second approval pause costs nothing compared to rolling back a bad deploy.

### Step 5: Write the SKILL.md

Generate the complete skill file. Keep it under 200 lines - command skills are prompts, not documentation. If the command needs extensive reference material, use supporting files.

Always start with the argument guard:
```markdown
The target is: $ARGUMENTS

If no argument was provided, ask the user for one and stop.
```

Then: rules section, phases, summary template.

### Step 6: Audit

Run through every item on the audit checklist below. Fix failures before finalizing. Present the audit results to the user.

### Step 7: Place

Save the skill to the target project:
```
<project>/.claude/skills/<command-name>/SKILL.md
```

If supporting files are needed, they go alongside SKILL.md.

---

## Frontmatter Reference

| Field | Type | Default | When to Use |
|-------|------|---------|-------------|
| `name` | string | dir name | Always. Lowercase, hyphens, max 64 chars |
| `description` | string | required | Action-oriented: what it does + when to trigger |
| `model` | string | inherit | Complex reasoning: `opus`. Cost savings: `haiku` |
| `disable-model-invocation` | bool | `false` | Always `true` for command skills (they have side effects) |
| `argument-hint` | string | none | If command takes args: `[service-name]`, `[model-id]` |
| `allowed-tools` | string | all | Restrict: `Read, Bash(npm *)`, `mcp__github__*` |
| `context` | string | inline | `fork` for isolated subagent (read-only exploration) |
| `agent` | string | general | With `context: fork`: `Explore`, `Plan` |
| `user-invocable` | bool | `true` | `false` hides from menu (background knowledge only) |

## $ARGUMENTS

`$ARGUMENTS` is replaced with the user's full argument string. Positional access via `$0`, `$1`, or `$ARGUMENTS[N]` (0-based).

```
/deploy twitter staging
# $ARGUMENTS = "twitter staging", $0 = "twitter", $1 = "staging"
```

Don't over-specify argument parsing. Trust Claude to understand natural language - describe what you expect and let Claude validate, rather than writing brittle format parsers.

## Path Variables

Never hardcode absolute paths. Use:
- `${CLAUDE_PROJECT_DIR}` - project root
- `${CLAUDE_SKILL_DIR}` - skill's own directory (for bundled scripts)
- Relative paths from repo root

## Design Patterns

See [references/design-patterns.md](references/design-patterns.md) for detailed patterns with full examples. Quick reference:

| Scenario | Pattern |
|----------|---------|
| One action, no approval needed | Simple Task |
| Multiple steps, some irreversible | Phased Workflow with Approval Gate |
| Need info from multiple sources | Parallel Research + Sequential Implementation |
| Modifying another project | Cross-Repo with Adaptive Discovery |
| Command exceeds 200 lines | Progressive Disclosure with supporting files |

## Anti-Patterns

Watch for these when reviewing command skills:
- **Hardcoded paths**: `/Users/someone/...` → use `${CLAUDE_PROJECT_DIR}` or relative
- **Missing safety**: no `disable-model-invocation` on commands with side effects
- **Over-specification**: complex argument parsers instead of natural language
- **No checkpoints**: making changes without showing what will happen first
- **Blind edits**: modifying files without reading them
- **Silent failures**: no error handling or status reporting
- **Context ignorance**: not reading CLAUDE.md, existing conventions, or config files
- **Monolithic prompt**: 500+ line SKILL.md instead of using supporting files

## Audit Checklist

Every command skill must pass before finalizing:

1. `disable-model-invocation: true` if any side effects exist
2. `argument-hint` present if command takes arguments
3. No hardcoded absolute paths
4. Adaptive discovery (grep/glob) for cross-repo file references
5. Guard clause for missing `$ARGUMENTS`
6. Approval gate before destructive/irreversible operations
7. Clear outcome reporting (succeeded, failed, next steps)
8. SKILL.md under 200 lines (supporting files for overflow)
9. Explicit error handling ("if X fails, stop and show error")
10. `${CLAUDE_PROJECT_DIR}` or relative paths, never absolute
11. Reads files before editing (no blind modifications)
12. Reads target project's CLAUDE.md for cross-repo operations
