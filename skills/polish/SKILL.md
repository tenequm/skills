---
name: polish
description: Pre-release code review - runs lint/type checks, launches parallel review agents (cleanliness, design, efficiency, side-effect gating) on the diff, validates findings, and fixes with approval. Use before committing, pushing, or releasing changes.
metadata:
  version: "2.4.1"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/polish
    emoji: "✨"
disable-model-invocation: true
argument-hint: "[base-ref]"
allowed-tools: "Bash(git diff *), Bash(git show *), Bash(git status *), Bash(git rev-parse *), Bash(git log *)"
---

# Pre-Release Polish

Repository state:

```!
git rev-parse --abbrev-ref HEAD
git status --short
git diff --stat 2>/dev/null | tail -1
```

Base ref argument (optional): $ARGUMENTS

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
2. Check for untracked (`??`) files in `git status --short`. Include new untracked source files in the review. A staged change that references an untracked file (a new module, benchmark target, or test) is itself a finding: if the change lands without the file, fresh checkouts and CI break on the missing reference
3. If a base ref was passed as an argument, diff against it: `git diff <base-ref>...HEAD`
4. If no uncommitted changes and no base ref, diff against main: `git diff main...HEAD`. If the work under review was already committed this session, scope the review to those session commits rather than the whole branch
5. If no changes at all, report "nothing to review" and stop

Exclude lockfiles and generated files from the review (`Cargo.lock`, `pnpm-lock.yaml`, `package-lock.json`, `*.snap`, generated bindings) - they are outputs, not authored code.

Read every changed file fully. Understand what each change does and why.

When a change relocates or rewrites an existing code path (a moved file, a handler split into middleware, a renamed/replaced function), open the prior version - the file it moved from, or `git show <ref>:<path>` for a deleted/renamed file - and compare behavior, not just lines. Note any dropped validation, reordered side-effects, or removed guards; pass those to the agents.

## Phase 3: Parallel Review

Write the diff to a scratchpad file. Use the Agent tool to launch all four agents concurrently in a single message. Pass each agent the diff file path and the list of changed files so it has the complete context - do not inline a large diff into four prompts.

Enrich each agent's prompt with:
- Relevant project constraints from CLAUDE.md (performance assumptions, logging conventions, platform quirks) so findings are domain-correct
- Known-intentional patterns in the diff that would otherwise be flagged (e.g. a deliberate `console.log` in a test-skip path matching project convention) so agents don't return known false positives

**Small-diff fast path**: if the diff is tiny (roughly under 50 changed lines), skip the agent fan-out and review all four lenses below directly yourself, reading every changed line in full. All later phases still apply.

### Agent 1: Cleanliness

Fast, mechanical, high-confidence. Looks for junk that should be removed.

- **Debug leftovers**: `console.log`, `console.debug`, `console.warn` added during development; temporary debug variables, hardcoded test values. NOT structured logger calls (`logger.info`, `logger.error`, `c.var.logger`)
- **AI slop**: comments explaining obvious code ("// increment counter", "// return the result") - flag each such comment individually, even if the code it describes is also flagged under another category; JSDoc on internal/private functions that aren't part of a public API; verbose docstrings on simple helpers; `TODO`/`FIXME`/`HACK` markers left by Claude (not by the user); unnecessary type annotations where the language infers correctly; emoji in code or comments (unless the project uses them)
- **Non-ASCII punctuation**: em-dashes, smart quotes, or other unicode punctuation introduced in changed lines (unless the project uses them). Plain-text grep over a diff can miss multi-byte characters - scan the changed files byte-aware, e.g. `rg -n '[\x{2010}-\x{2015}\x{2018}-\x{201F}]'`
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
- **Behavior drift in relocated code**: when the diff moves or rewrites an existing path, compare it against the code it replaced (see Phase 2). Flag dropped input validation, removed guards or early-returns, and changed error semantics (status codes, return shapes). A refactor that changes *behavior* is a regression even when every line looks clean.

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

### Agent 4: Side-Effect Gating

Closed-scope correctness check. Finds costly or irreversible side-effects that run before the checks meant to gate them. Does NOT judge whether business logic is correct - that is `/review`'s job.

- **Inventory the side-effects**: list every costly or irreversible side-effect introduced or relocated in the diff - charges/payments, DB writes/deletes, mutating external calls, file writes, notifications/emails, irreversible state changes
- **Inventory the gates**: for each side-effect, list the checks that must precede it - input validation (shape/type/range), authentication, authorization, precondition/existence checks, idempotency/dedup
- **Cross-check ordering**: flag any side-effect reachable on a control-flow path where a gate runs after it, or not at all. Trace ACROSS the middleware/handler boundary - middleware that fires a side-effect before calling `next()` is the prime suspect; the validation that should gate it often lives in the downstream handler
- **Missing rollback**: flag a committed side-effect with no compensation when a later step on the same request can still fail (e.g. charged, then the request errors)
- **Out of scope** - route to `/review`: whether the business logic is correct, pricing math, algorithmic correctness, anything without a crisp invariant

Every finding must cite the side-effect line, the gate it precedes (or "ungated"), and the control-flow path. No finding without two line references.

## Phase 4: Validate Findings

Before presenting anything, verify every finding from the agents against actual code. Drop any finding that fails validation.

For each finding:
- **Read the exact file and lines cited** - confirm the code exists and matches the description. Drop findings where the line number is wrong or the code doesn't match what was claimed
- **Dead code / unused imports** - grep the entire codebase for references. If the symbol is referenced anywhere (imports, calls, type usage), drop the finding
- **Reuse suggestions** - confirm the suggested utility/function actually exists at the claimed path. If it doesn't exist, drop the finding
- **Debug leftovers** - confirm the flagged line is actually a debug artifact, not structured logging (`logger.*`, `c.var.logger.*`)
- **Efficiency / design claims** - read the surrounding context to confirm the pattern matches. Drop speculative findings that don't hold up with full context
- **Side-effect gating / behavior-drift claims** - confirm by reading the actual control flow: the side-effect line, the gate line, and the path between (including downstream handlers and middleware order). Validate a relocation regression against *the code it replaced*, not against sibling paths that may share the same flaw. Never drop one as "a behavior decision" or "out of scope" - if it holds up it is the highest-severity finding
- **Rewritten or moved paths** - when a finding lands on rewritten/relocated code, check whether the flaw already existed at HEAD (or in the pre-move version). If it did, keep it but report it as pre-existing-carried-through, not a new regression. Separately flag any test coverage deleted with the old path and not replaced

Only findings that survive validation proceed to the report.

## Phase 5: Report

Synthesize validated findings into a single deduplicated report. If multiple agents flagged the same code, merge into one finding. Group by category:

```
## Review Findings

### Correctness (N issues)
1. `path/to/file.ts:55` - chargeUser() runs before body validation (handler validates at :78, after next()); a malformed request is charged then 400s
2. ...

### Cleanliness (N issues)
1. `path/to/file.ts:42` - console.log("debug response")
2. ...

### Design (N issues)
1. `path/to/file.ts:15-18` - hand-rolled path join, use existing `resolveAssetPath` from shared/utils
2. ...

### Efficiency (N issues)
1. `path/to/file.ts:30-45` - sequential awaits on independent API calls, use Promise.all
2. ...

### Observations (non-blocking)
1. `path/to/file.ts:88` - flock fallback catches all lock errors, not just unsupported-filesystem ones - a behavior note, not a defect; your call

### Dropped after validation
1. `path/to/view.py:12` - per-mousemove getBoundingClientRect - the element is CSS-fixed, so the rect is cached and there is no layout flush

**Total: X issues across Y categories**

**Recommendation:** fix correctness #1, cleanliness #1-2, efficiency #1; skip design #2 (marginal).

**Awaiting approval before proceeding with fixes.**
```

List **Correctness** first, and always - including at `(0 issues)`, since a zero there is a real signal that side-effect ordering was checked. A correctness zero must state what was traced - which side-effects were inventoried and which gates cover them - not just the count. It must never be batch-approved alongside cosmetic items.

**Observations** are validated behavior notes that aren't defects - the user's call, never blocking. **Dropped after validation** lists agent findings Phase 4 dismissed, with the reason - it substantiates the counts. Omit either section when empty.

End the report with a per-finding **Recommendation** line: which findings you'd fix and which you'd skip, so the user can approve by reference.

If zero issues found, report "Clean - no issues found", substantiate the correctness zero (what was traced and why it's clean), and offer next actions - e.g. commit as-is, or leave for the user's own review - then stop.

The report MUST end with the line "**Awaiting approval before proceeding with fixes.**" (or the clean-case report above). Do not proceed to Phase 6 until the user explicitly approves.

## Phase 6: Fix and Verify

After user approves:
1. Fix all reported issues with minimal targeted edits
2. Re-run the project's validation command
3. If new errors appear, fix them
4. Show summary: what was fixed, final check status
5. If the reviewed work was already committed, ask whether the fixes should amend those commits or land as a new commit - default to a new commit
