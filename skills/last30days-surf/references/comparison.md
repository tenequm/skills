# Comparison / vs-mode reference

Full contract for `vs` topics and `--competitors` auto-discovery. Ported from upstream `docs/plans/2026-04-22-005-feat-vs-mode-n-passes-competitors-auto-discovery-plan.md`.

## Triggering

vs-mode triggers when the topic contains ` vs `, ` vs. `, or ` versus ` (case-insensitive) **and** at least 2 distinct entities are extractable.

- 2-entity: `"openai vs anthropic"` -> `["openai", "anthropic"]`
- 3-entity: `"openai vs anthropic vs xai"` -> `["openai", "anthropic", "xai"]`
- "A vs. B": punctuation handled
- "A versus B": handled
- Trailing "X vs " (empty rhs): does NOT trigger
- "Drake vs Drake" (identical entities deduped): does NOT trigger

## Fan-out

Each entity gets its own full `pipeline.run()` call in parallel via `ThreadPoolExecutor`. Wall-clock ≈ max(per-entity-latency), not sum. Per upstream this replaced an earlier 3-pass→1-pass merged-retrieval optimization that produced thinner per-entity depth.

Cap: `_max_subqueries("comparison")` = 4 per entity.

Each entity gets its own:
- Step 0.5 entity resolution (subreddit / handle / repo)
- Step 0.55 pre-research intelligence
- Step 0.75 query plan
- Phase 1 fan-out + Phase 2 supplemental + Phase 3 retry

## `--competitors` auto-discovery

When the topic is a single entity (no `vs`):

1. Run **3 SERP queries** in parallel via surf web/search:
   - `"{topic} competitors"`
   - `"{topic} alternatives"`
   - `"{topic} vs"`
2. Extract Capitalized brand-token candidates:
   - Brand-token regex: `[A-Z][A-Za-z0-9&.\-]*` OR camelCase with later capital (catches `Anthropic`, `OpenAI`, `xAI`, `eBay`, `Hugging Face`).
   - A "phrase" = 1-4 brand tokens whitespace-separated.
3. Reject candidates whose tokens are *all* stopwords (listicle fillers like `Top, Best, Worst, Popular, Leading, Similar, Alternatives`, grammar/time words, month names, years 2018-2030, noise like `AI, Apps, Software, Platform`). Containing one stopword is OK; being 100% stopword is not.
4. Reject candidates that overlap any topic token (so `OpenAI` query doesn't return `OpenAI Alternatives`).
5. Reject single tokens shorter than 2 chars.
6. Score by frequency across all SERP items, deduped case-insensitively (canonical form is first-seen casing).
7. Pick top N (default N=2, configurable via `--competitors=N`).
8. Re-invoke pipeline with `"{topic} vs {peer1} vs {peer2}"` and `--competitors-plan` JSON containing per-entity resolution.

## Override-leak invariant

Main-topic flags (`--subreddits`, `--x-handle`, `--x-related`, `--tiktok-hashtags`, `--tiktok-creators`, `--ig-creators`, `--github-user`, `--github-repos`) MUST NOT leak into peer sub-runs. Every per-entity kwarg is built explicitly; no closure-default fallthrough.

Canonical regression test (per upstream): Kanye main `--subreddits=Kanye,hiphopheads` + peer Drake → Drake must receive `subreddits=None`.

## `--competitors-plan` JSON

Inline JSON or file path. Case-insensitive entity match. Schema:

```json
{
  "openai": {
    "x_handle": "OpenAI",
    "x_related": ["sama", "kevinweil"],
    "subreddits": ["OpenAI", "ChatGPT"],
    "github_user": "openai",
    "github_repos": ["openai/openai-python"],
    "context": "Foundation model lab; ships GPT-5, Codex CLI, ChatGPT product surfaces."
  },
  "anthropic": {
    "x_handle": "AnthropicAI",
    "subreddits": ["ClaudeAI", "Anthropic"],
    "github_user": "anthropics",
    "github_repos": ["anthropics/claude-code"],
    "context": "Claude maker; Sonnet 4.6, Opus 4.5, Claude Code agent."
  }
}
```

Unknown fields warn-and-ignore; malformed JSON exits 2.

## Output structure

The ONLY allowed `##` headers in COMPARISON mode (LAW 4):

```markdown
# {A} vs {B} [vs {C}]: What the Community Says (/Last30Days-Surf)

## Quick Verdict
{One paragraph, the actual answer}

## {Entity A}
**Community Sentiment:** ...
**Strengths:**
- ...
**Weaknesses:**
- ...

## {Entity B}
[same shape]

## {Entity C}   (only if 3-way)
[same shape]

## Head-to-Head
| Dimension | {A} | {B} | {C} |
| --- | --- | --- | --- |
| What it is | ... | ... | ... |
| GitHub stars | ... | ... | ... |
| Philosophy | ... | ... | ... |
| Skills | ... | ... | ... |
| Memory | ... | ... | ... |
| Models | ... | ... | ... |
| Security | ... | ... | ... |
| Best for | ... | ... | ... |
| Install | ... | ... | ... |

## The Bottom Line
- Choose {A} if ...
- Choose {B} if ...
- Choose {C} if ...

## The emerging stack
{One paragraph synthesis: how do these fit together / where is the space heading}

[engine footer between --- lines, verbatim]

I'm now an expert on {topic}. Some things you could ask:
- ...
```

## Polymarket disambiguation

`--polymarket-keywords "kw1,kw2"` filters market titles. Auto-skip on single-token-ambiguous topics (US states, cities, common nouns like `color/animal/sport`).

## Footer-nudge suppression

When `--plan` or `--competitors-plan` is present, suppress the surf-key nudge (the user has already done the heavy lifting; they don't need a setup pointer).

## Save format (for `--save-dir`)

N save files: `{entity-slug}-raw.md`, each with its own single-row `## Resolved Entities` block. Stdout shows merged comparison plus full N-row Resolved Entities block.

## GitHub live-data override

For comparison topics, `surf_github_get(kind=repo)` star counts override star counts cited by blog posts / YouTube videos / tweets. When two sources disagree on a number, prefer the live-fetched number. The Head-to-Head table's `GitHub stars` row pulls live.

## X reply cluster

When N independent replies to a "what's the best X?" tweet converge on the same answer, that's the strongest endorsement signal in the corpus. Call it out prominently in `## Quick Verdict` or weave into per-entity sentiment.
