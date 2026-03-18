# Command Skill Design Patterns

## Pattern 1: Simple Task

Single-purpose commands that do one thing. 5-30 seconds execution. No approval gate needed because the action is low-risk or easily reversible.

```yaml
---
name: format-changed
description: Format all changed files with the project formatter
disable-model-invocation: true
allowed-tools: Read, Bash(npx prettier *), Bash(git diff *)
---

Format all files changed since the last commit:

1. Get changed files: `git diff --name-only HEAD`
2. Filter for formattable extensions (.ts, .tsx, .js, .json, .css, .md)
3. Run the project's formatter on each file
4. Report which files were formatted

If the formatter fails on any file, show the error and continue with the rest.
```

When to use: quick utilities, linting, formatting, status checks. The key signal is "just run X."

## Pattern 2: Phased Workflow with Approval Gate

Multi-step commands where some actions are irreversible. The approval gate is the critical feature - it separates research from action.

```yaml
---
name: release
description: Cut a new release with changelog and tag
disable-model-invocation: true
argument-hint: "[version]"
---

Release version: $ARGUMENTS

If no version was provided, ask the user for one and stop.

## Phase 1: Pre-flight

1. Verify version is valid semver
2. Check git is clean (no uncommitted changes)
3. Check current branch is main
4. Run `pnpm check` to verify build passes

If any check fails, report the failure and stop.

## Phase 2: Changelog

1. Read commits since last tag: `git log $(git describe --tags --abbrev=0)..HEAD --oneline`
2. Group by type (feat, fix, chore)
3. Draft changelog entry

Present the changelog to the user.

**STOP and wait for user approval before proceeding.**

## Phase 3: Execute

1. Update version in package.json
2. Add changelog entry
3. Commit: `git commit -am "chore: release vX.Y.Z"`
4. Tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
5. Push: `git push && git push --tags`

## Phase 4: Summary

Report: version released, changelog entry, tag created, push status.
```

When to use: releases, migrations, schema changes - anything with a point of no return. The key signal is that some steps can't be undone.

## Pattern 3: Parallel Research + Sequential Implementation

Spawn subagents for independent research tasks, wait for results, then implement sequentially. This saves significant time when multiple pieces of information are needed.

```yaml
---
name: add-dependency
description: Research, evaluate, and add a new dependency
disable-model-invocation: true
model: opus
argument-hint: "[package-name]"
---

Add dependency: $ARGUMENTS

If no package name was provided, ask the user and stop.

## Phase 1: Research (parallel subagents)

Spawn these research agents simultaneously:

### Agent A: Package Analysis
Use a `deep-researcher` agent to find:
- Latest version, release frequency, maintenance status
- Bundle size, tree-shaking support
- Known security vulnerabilities
- License

### Agent B: Alternatives
Use a `deep-researcher` agent to find:
- Competing packages solving the same problem
- Community recommendations and comparison
- Download trends and ecosystem adoption

## Phase 2: Recommendation

Present findings:
1. Recommended package and version with justification
2. Alternatives considered and why they were rejected
3. Any concerns (size, security, license, maintenance)

**STOP and wait for user approval.**

## Phase 3: Install

1. Add the dependency
2. Run validation (`pnpm check` or equivalent)
3. Report success or failures
```

When to use: decisions that benefit from gathering information from multiple sources. The key signal is needing to research before acting.

## Pattern 4: Cross-Repo with Adaptive Discovery

When a command modifies files in another project, it must adapt to that project's structure rather than assuming hardcoded paths. The core technique: grep for known content patterns to discover files, then read each file to understand its format before editing.

```yaml
---
name: sync-api-docs
description: Sync API documentation from backend to docs site
disable-model-invocation: true
---

Sync API docs from this repo to the docs site at ~/pj/docs/.

## Phase 1: Read conventions

Read `~/pj/docs/.claude/CLAUDE.md` for the docs project's conventions
(build commands, commit style, deploy process).

## Phase 2: Discover files to update

Use a Grep/Glob agent to find ALL files in `~/pj/docs/` that reference
existing API endpoint names from this project (e.g., grep for route paths
like `/v1/users` or model names from this repo's constants).

This discovers every file that needs updating, even if the docs project
has been restructured since this command was written.

## Phase 3: Update

For each discovered file, read it first, then add/update entries matching
the existing format exactly:
- Match column count, field names, value format of existing rows
- Use the same naming conventions (short names where others use short names)
- If the file has a summary range, update it if new entries extend it

## Phase 4: Validate and deploy

Follow the deploy process from the docs project's CLAUDE.md:
1. Run validation
2. Stage only modified files
3. Commit with conventional format
4. Deploy
```

When to use: any command that touches another project. The key signal is modifying files in a different repo. The critical principle: never hardcode paths or formats that might change in the target project.

## Pattern 5: Progressive Disclosure

For complex commands that exceed 200 lines, keep SKILL.md as the orchestrator and move details into supporting files. Claude reads these on demand, keeping the main prompt lean.

```
my-complex-command/
├── SKILL.md              # ~150 lines: phases + orchestration
├── CHECKLIST.md           # Detailed pre-flight checks
├── ROLLBACK.md            # Emergency rollback procedures
└── scripts/
    └── validate.sh        # Bundled validation script
```

SKILL.md references supporting files inline:
```markdown
## Phase 1: Pre-flight
Follow the checklist in [CHECKLIST.md](CHECKLIST.md).

## Phase 5: Rollback (if needed)
If deployment fails, follow [ROLLBACK.md](ROLLBACK.md).

## Phase 3: Validate
Run the bundled validation script:
`bash ${CLAUDE_SKILL_DIR}/scripts/validate.sh`
```

When to use: commands with extensive checklists, detailed rollback procedures, or reusable scripts. The key signal is SKILL.md approaching 200 lines.

## Choosing the Right Pattern

| Scenario | Pattern | Key Signal |
|----------|---------|-----------|
| One action, no approval needed | Simple Task | "just run X" |
| Multiple steps, some irreversible | Phased Workflow | commits, deploys, deletions |
| Need info from multiple sources | Parallel Research | pricing, alternatives, capabilities |
| Modifying files in another project | Cross-Repo | different repo, different conventions |
| Command exceeds 200 lines | Progressive Disclosure | complex checklists, rollback procedures |

Patterns combine naturally. A real-world command might use Parallel Research for Phase 1, Cross-Repo for Phase 4, and Progressive Disclosure to keep it manageable. The `surf-inference-add-new-model` command uses all three: parallel research agents for pricing and capabilities, cross-repo adaptive discovery for the landing page updates, and the pricing considerations doc as external reference.
