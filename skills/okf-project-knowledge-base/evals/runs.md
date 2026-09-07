# Eval run ledger

Append-only. One row per (scenario, executor) run. Full transcripts of the
2026-09-07 baseline are recoverable from the operator's pond archive, session
`9881bfe4-397d-418e-915d-53707b6a39ed` (Claude Code, project build-workflow).

## 2026-09-07 - baseline (no skill), build-workflow @ v0.1.15

| Scenario | Harness | Model | Effort | Verdict | Notes |
|---|---|---|---|---|---|
| capture | codex-cli (acpx) | gpt-5.6-sol | medium | baseline-fail | Invented `docs/decisions/` ADR (Status/Context/Decision), +5 lines AGENTS.md, README link; committed. No frontmatter, no provenance fields. |
| capture | claude-code (acpx) | claude-opus-5 | default | baseline-fail | Dated flat doc in `docs/`, +8 lines AGENTS.md, README line; ran repo checks, declined commit on detached HEAD. No frontmatter, triple-write scatter. |
| recall | codex-cli (acpx) | gpt-5.6-sol | medium | pass-at-cost | Full workspace-at-first-write story reconstructed via git archaeology (~10 tool calls); external evidence (retro session 35c0a261) correctly reported unreachable. |
| recall | claude-code (acpx) | claude-opus-5 | default | pass-at-cost | Same story, ~15 tool calls; same external-evidence wall; cited commits 0813b96 / add7263 / 9f857b7. |
| cold_start | codex-cli (acpx) | gpt-5.6-sol | medium | baseline-fail | Invented `docs/knowledge/` tree with README index, decisions/ (4-digit ADR ids), findings/, templates/; lifecycle + search-before-write rules; +6 lines AGENTS.md. Concepts right, mechanics bespoke: no YAML frontmatter, positional ids. |
| cold_start | claude-code (acpx) | claude-opus-5 | default | baseline-fail | Invented `docs/decisions/` numbered series with bold-header metadata; wrote own validator inline in Justfile + lefthook glob and negative-tested it; +8 lines AGENTS.md. Strongest craft, still bespoke mechanics. |

### Baseline findings

1. Four write-tasks produced four incompatible structures; the skill's core
   job is standardizing mechanics, not teaching capture.
2. Every writer grew the instruction file by a rationale paragraph (+5 to +8
   lines each).
3. Zero YAML frontmatter, zero machine-parseable provenance, zero bundle
   markers across all six runs.
4. Models already converge on concepts (index, lifecycle, search-before-write,
   knowledge-vs-memory exclusions) - invariants can be terse.
5. Recall without a bundle works but costs 10-15 tool calls and dead-ends at
   externally-held evidence; resolvable `sources` are the fix.
