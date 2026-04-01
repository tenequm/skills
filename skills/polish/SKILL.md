---
name: polish
description: Pre-release code review - runs lint/type checks, then launches 3 parallel review agents (cleanliness, design, efficiency) to analyze the diff, synthesizes a unified report, and fixes with approval. Use before committing, pushing, or releasing changes. Triggers on "review code", "check before commit", "cleanup before release", "review changes", "is this ready to ship", "polish before release", "simplify".
metadata:
  version: "2.2.0"
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
- Only flag issues in changed/added lines, not pre-existing code
- Reuse suggestions must point to a specific existing function/utility in the codebase, not hypothetical "you could extract this"
- Do not flag efficiency on cold paths, one-time setup code, or scripts that run once

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

## Phase 3: Parallel Review

Use the Agent tool to launch all three agents concurrently in a single message with `model: "opus"`. Pass each agent the full diff and the list of changed files so it has the complete context.

### Agent 1: Cleanliness

Fast, mechanical, high-confidence. Looks for junk that should be removed.

- **Debug leftovers**: `console.log`, `console.debug`, `console.warn` added during development; temporary debug variables, hardcoded test values. NOT structured logger calls (`logger.info`, `logger.error`, `c.var.logger`)
- **AI slop**: comments explaining obvious code ("// increment counter", "// return the result") - flag each such comment individually, even if the code it describes is also flagged under another category; JSDoc on internal/private functions that aren't part of a public API; verbose docstrings on simple helpers; `TODO`/`FIXME`/`HACK` markers left by Claude (not by the user); unnecessary type annotations where the language infers correctly; emoji in code or comments (unless the project uses them)
- **Dead code**: unreferenced functions, variables, types; commented-out code blocks (git has history); unused function parameters (unless required by interface/callback signature)
- **Unused imports**: imports added but never referenced, imports left behind after refactoring (linter catches most - verify edge cases)
- **Hardcoded values**: magic numbers or strings that should be in constants; URLs, prices, limits that belong in config. NOT obvious constants like `0`, `1`, `true`, HTTP status codes

### Agent 2: Design & Reuse

Requires codebase exploration beyond the diff. Looks for structural and design issues.

- **Reuse opportunities**: search the codebase for existing utilities, helpers, and shared modules that could replace newly written code. Look in utility directories, shared modules, and files adjacent to the changed ones. Flag hand-rolled logic where a utility already exists (string manipulation, path handling, type guards, env checks)
- **Over-engineering**: helper functions used exactly once (should be inlined); abstractions wrapping a single call with no added value; try/catch adding nothing (re-throwing same error, catching impossibilities); validation of internal data already validated at route boundary; feature flags or config for things that could just be code; backwards-compat shims for code that was just written
- **Redundant state**: state that duplicates existing state; cached values that could be derived; observers/effects that could be direct calls
- **Parameter sprawl**: adding new parameters to a function instead of generalizing or restructuring existing ones
- **Copy-paste with slight variation**: near-duplicate code blocks that should be unified
- **Leaky abstractions**: exposing internal details that should be encapsulated, or breaking existing abstraction boundaries
- **Stringly-typed code**: using raw strings where constants, enums, or branded types already exist in the codebase
- **Structural issues**: functions that grew too long during changes (>50 lines, consider splitting); inconsistent naming with existing codebase conventions

### Agent 3: Efficiency

Looks for runtime performance and resource issues.

- **Redundant work**: redundant computations, repeated file reads, duplicate network/API calls, N+1 patterns
- **Missed concurrency**: independent operations run sequentially when they could run in parallel
- **Hot-path bloat**: new blocking work added to startup or per-request/per-render hot paths
- **No-op updates**: state/store updates inside polling loops, intervals, or event handlers that fire unconditionally without change detection. Also: wrapper functions that take updater/reducer callbacks but don't honor same-reference returns
- **TOCTOU anti-patterns**: pre-checking file/resource existence before operating - operate directly and handle the error
- **Memory**: unbounded data structures, missing cleanup, event listener leaks
- **Overly broad operations**: reading entire files when only a portion is needed, loading all items when filtering for one
- **Unchecked system boundaries**: fetch/HTTP calls without response status checks (`r.ok`), unhandled promise rejections on external calls, missing error handling at I/O boundaries

## Phase 4: Validate Findings

Before presenting anything, verify every finding from the agents against actual code. Drop any finding that fails validation.

For each finding:
- **Read the exact file and lines cited** - confirm the code exists and matches the description. Drop findings where the line number is wrong or the code doesn't match what was claimed
- **Dead code / unused imports** - grep the entire codebase for references. If the symbol is referenced anywhere (imports, calls, type usage), drop the finding
- **Reuse suggestions** - confirm the suggested utility/function actually exists at the claimed path. If it doesn't exist, drop the finding
- **Debug leftovers** - confirm the flagged line is actually a debug artifact, not structured logging (`logger.*`, `c.var.logger.*`)
- **Efficiency / design claims** - read the surrounding context to confirm the pattern matches. Drop speculative findings that don't hold up with full context

Only findings that survive validation proceed to the report.

## Phase 5: Report

Synthesize validated findings into a single deduplicated report. If multiple agents flagged the same code, merge into one finding. Group by category:

```
## Review Findings

### Cleanliness (N issues)
1. `path/to/file.ts:42` - console.log("debug response")
2. ...

### Design (N issues)
1. `path/to/file.ts:15-18` - hand-rolled path join, use existing `resolveAssetPath` from shared/utils
2. ...

### Efficiency (N issues)
1. `path/to/file.ts:30-45` - sequential awaits on independent API calls, use Promise.all
2. ...

**Total: X issues across Y categories**

**Awaiting approval before proceeding with fixes.**
```

If zero issues found, report "Clean - no issues found" and stop.

The report MUST end with the line "**Awaiting approval before proceeding with fixes.**" (or "Clean - no issues found"). Do not proceed to Phase 6 until the user explicitly approves.

## Phase 6: Fix and Verify

After user approves:
1. Fix all reported issues with minimal targeted edits
2. Re-run the project's validation command
3. If new errors appear, fix them
4. Show summary: what was fixed, final check status
