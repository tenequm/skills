---
name: polish
description: Pre-release code review - runs lint/type checks, analyzes diff, detects AI slop and common issues, fixes with approval. Use before committing, pushing, or releasing changes. Triggers on "review code", "check before commit", "cleanup before release", "review changes", "is this ready to ship", "polish before release".
disable-model-invocation: true
---

# Pre-Release Polish

Current branch: !`git rev-parse --abbrev-ref HEAD`
Uncommitted changes: !`git diff --stat 2>/dev/null | tail -1`

## Rules

- Read every changed file fully before reviewing - never assess code you haven't opened
- Only flag real issues, not style preferences already handled by the formatter
- Do NOT add comments, docstrings, or type annotations to code that doesn't have them
- Distinguish legitimate operational logging (`logger.info`, `logger.error`) from debug leftovers (`console.log`, `console.debug`)
- When fixing, make minimal targeted edits - don't refactor surrounding code

## Phase 1: Automated Checks

Run the project's lint + type-check command. Check CLAUDE.md for the correct validation command (commonly `pnpm check`, `just check`, `cargo clippy`, `uv run ruff check`, etc.).

If checks fail:
1. Fix all errors
2. Re-run checks until clean
3. Then proceed to Phase 2

If no validation command is found in CLAUDE.md, ask the user what to run.

## Phase 2: Diff Analysis

Determine what changed:
1. Check for uncommitted changes: `git diff` + `git diff --cached`
2. If no uncommitted changes, diff against main: `git diff main...HEAD`
3. If no changes at all, report "nothing to review" and stop

Read every changed file fully. Understand what each change does and why.

## Phase 3: Slop Detection

Review all changed code for these categories. Only flag issues in changed/added lines, not pre-existing code.

### 3.1 Debug Leftovers
- `console.log`, `console.debug`, `console.warn` added during development
- Temporary debug variables, hardcoded test values
- NOT: structured logger calls (`logger.info`, `logger.error`, `c.var.logger`)

### 3.2 Unused Imports
- Imports added but never referenced
- Imports left behind after refactoring
- The linter catches most of these, but verify manually for edge cases

### 3.3 AI Slop
- Comments explaining obvious code ("// increment counter", "// return the result")
- JSDoc on internal/private functions that aren't part of a public API
- Verbose docstrings on simple one-liner helpers
- `TODO`, `FIXME`, `HACK` markers left by Claude (not by the user)
- Unnecessary type annotations where TypeScript infers correctly
- Emoji in code or comments (unless the project uses them)

### 3.4 Over-Engineering
- Helper functions used exactly once (should be inlined)
- Abstractions wrapping a single call with no added value
- try/catch adding nothing (re-throwing same error, catching impossibilities)
- Validation of internal data already validated at route boundary
- Feature flags or config for things that could just be code
- Backwards-compat shims for code that was just written

### 3.5 Dead Code
- Unreferenced functions, variables, types
- Commented-out code blocks (just delete it, git has history)
- Unused function parameters (unless required by interface/callback signature)

### 3.6 Hardcoded Values
- Magic numbers or strings that should be in constants
- URLs, prices, limits that belong in config
- NOT: obvious constants like `0`, `1`, `true`, HTTP status codes

### 3.7 Structural Issues
- Functions that grew too long during changes (>50 lines, consider splitting)
- Duplicated logic across changed files that should be shared
- Inconsistent naming with existing codebase conventions

## Phase 4: Report

Present findings as a numbered list grouped by category:

```
## Review Findings

### Debug Leftovers (N issues)
1. `packages/twitter/src/routes.ts:42` - console.log("debug response")
2. ...

### AI Slop (N issues)
1. `packages/inference/src/handler.ts:15-18` - JSDoc on internal helper
2. ...

### [category] (N issues)
...

**Total: X issues across Y categories**
```

If zero issues found, report "Clean - no issues found" and stop.

**STOP and wait for user approval before making any fixes.**

## Phase 5: Fix and Verify

After user approves:
1. Fix all reported issues with minimal targeted edits
2. Re-run the project's validation command
3. If new errors appear, fix them
4. Show summary: what was fixed, final check status
