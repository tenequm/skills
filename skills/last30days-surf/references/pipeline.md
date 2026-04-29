# Pipeline reference

Full 7-stage pipeline contract, depth budgets, per-source policy, fan-out caps, scoring formula, render envelope contract. Ported from upstream `mvanhorn/last30days-skill@5b87cca`.

## 7-stage contract

```
plan -> resolve -> retrieve -> normalize -> fuse -> rerank -> cluster -> render
```

## Depth budgets (defaults)

| Depth | per_stream_limit | pool_limit | rerank_limit | Subqueries |
|---|---|---|---|---|
| `quick` | 6 | 15 | 12 | 1 |
| `default` | 12 | 40 | 40 | 1-3 |
| `deep` | 20 | 60 | 60 | 3-5 |

Subquery caps by intent: how_to/opinion/product/breaking_news = 5; comparison = 4; factual/concept = 2.

Hard fetch caps:
- **X / Twitter**: max 2 fetches per run total. Shared across subqueries.
- **`--competitors` fan-out**: max 6 parallel sub-runs.

## Routing matrix

| Source | Primary | Fallback | Auth |
|---|---|---|---|
| Reddit | `reddit_public.search_reddit_public` (direct .json) | `surf_adapters.reddit_search` (surf v2) | Free → SURF_API_KEY |
| X / Twitter | `surf_adapters.twitter_search` (surf v2) | — | SURF_API_KEY |
| YouTube | `surf_adapters.youtube_search` (surf web/search + youtube/subtitles) | — | SURF_API_KEY |
| GitHub | `github.search_github` (direct REST, anonymous) | `surf_adapters.github_search` (surf v2) on 429 | Free → SURF_API_KEY |
| Hacker News | `hackernews.search_hackernews` (direct Algolia) | `surf_adapters.hackernews_search` (web/crawl json) on exception | Free → SURF_API_KEY |
| Polymarket | `polymarket.search_polymarket` (direct Gamma) | `surf_adapters.polymarket_search` (web/crawl json) on exception | Free → SURF_API_KEY |
| Bluesky | `surf_adapters.bluesky_search` (surf web/crawl json against AppView) | — | SURF_API_KEY |
| TikTok / Instagram / Threads / Pinterest | `surf_adapters.{X}_search` (surf web/crawl) | — | SURF_API_KEY |
| Web (grounding) | `surf_adapters.web_search` (surf v2) | — | SURF_API_KEY |
| Truth Social, Xiaohongshu, Perplexity, xquik | dropped — no surf path or duplicates of surf web tier | — | — |

## Source quality baselines

```
youtube     0.85
hackernews  0.80
x           0.68
bluesky     0.66
reddit      0.60
instagram   0.58
tiktok      0.58
polymarket  0.50
default     0.60
```

## Engagement weights (log1p of each field, weighted sum, then * 100)

```
reddit:      0.50*score + 0.35*comments + 0.05*(upvote_ratio*10) + 0.10*top_comment
youtube:     0.45*views + 0.32*likes    + 0.13*comments          + 0.10*top_comment
tiktok:      0.45*views + 0.27*likes    + 0.18*comments          + 0.10*top_comment
x:           0.55*likes + 0.25*reposts  + 0.15*replies           + 0.05*quotes
instagram:   0.50*views + 0.30*likes    + 0.20*comments
hackernews:  0.55*points + 0.45*comments
bluesky:     0.40*likes + 0.30*reposts  + 0.20*replies + 0.10*quotes
polymarket:  0.60*volume + 0.40*liquidity
```

Freshness modulation per `freshness_mode`:

```
strict_recent:    score = recency_score              (linear 100 -> 0 over 30 days)
balanced_recent:  score = recency_score * 0.8 + 10
evergreen_ok:     score = recency_score * 0.6 + 40   (YouTube how_to typical)
```

Local pre-rank (used pre-LLM and as fallback): `0.65*local_relevance + 0.25*(freshness/100) + 0.10*(engagement_score/100)`.

Pruning floors:
- `local_relevance < 0.15` -> drop
- Social items with zero engagement: need `>= 0.225` local_relevance to survive
- TikTok/Instagram with <1000 views: drop unless that source has no other items
- YouTube with views > 100k: needs `local_relevance >= 0.3`

## Final score formula

```
final_score =
    0.60 * rerank_score          (LLM relevance 0-100)
  + 0.20 * normalized_rrf        ((rrf_score / 0.08) * 100, clamped 0-100)
  + 0.10 * freshness             (0-100 from recency, modulated by freshness_mode)
  + 0.05 * source_quality * 100  (per-source baseline; default 0.60)
  + 0.05 * min(engagement * 6, 100)

if rerank_score < 20:                         final_score *= 0.3
if entity-miss flagged in fallback path:      final_score = max(0, final_score - 20)
```

`fun_score` is a **separate** ranking dimension. Does NOT feed `final_score`. Use it to weave 2-3 short punchy quotes into prose synthesis.

## RRF parameters

```
K = 60                                       (Cormack 2009)
rrf_score = sum_streams [ subquery.weight * source_weight / (K + native_rank) ]
tie-break: (-rrf_score, -local_relevance, -freshness, source, title)
```

## Per-author cap and per-source diversity floor

- **Per-author cap**: max 3 candidates from any one author across the merged pool.
- **Per-source diversity floor**: reserve >=2 slots per source IF that source's max `local_relevance >= 0.25`. Lower-relevance sources compete on merit.

## URL normalization (cross-source dedup)

```
host -> lowercase
strip prefixes: www., old., m.
drop query params matching: utm_*
strip trailing /
```

Same canonical URL across sources -> merge. When merging, prefer the variant with higher `local_relevance*100 + freshness + source_quality*10`.

## Cluster invariants

- Cluster only when `intent in {breaking_news, opinion, comparison, prediction}` AND `cluster_mode != "none"`.
- Pass 1 threshold: `>= 0.42` (breaking_news), `>= 0.48` (others).
- Pass 2 entity-overlap merge: only when `|A∩B| / min(|A|,|B|) >= 0.45` AND source sets differ AND Polymarket never merges with non-Polymarket.
- MMR rep selection: `lambda = 0.75`, diversity penalty scaled `*100` to be commensurate with `final_score`.
- Uncertainty tags: `single-source` if all candidates from one source; `thin-evidence` if max final_score < 55.

## Date window

`window = [today - 30 days, today]` UTC ISO `YYYY-MM-DD`. Per-source date handling:

- **Reddit**: native `time=month` filter; items without dates are kept.
- **HN Algolia**: `numericFilters=created_at_i>{epoch_30d_ago}`.
- **Web / surf_web_search**: `published_within_days: 30`; items with no date are dropped.
- **YouTube**: `freshness_mode="evergreen_ok"` allows out-of-window items for `how_to`.
- **TikTok / Instagram / Bluesky / Threads**: hard 30-day filter post-fetch.
- **Polymarket**: filter on `event.endDate`; engagement = `volume1mo` + liquidity.
- **GitHub**: hard 30-day filter post-fetch.

## Render envelope contract

Two HTML-comment envelopes wrap the engine-emitted brief:

- `<!-- EVIDENCE FOR SYNTHESIS:` ... `<!-- END EVIDENCE FOR SYNTHESIS -->` wraps `## Ranked Evidence Clusters`, `## Stats`, `## Source Coverage`. **Read and transform; never emit verbatim.**
- `<!-- PASS-THROUGH FOOTER:` ... `<!-- END PASS-THROUGH FOOTER -->` wraps the emoji "All agents reported back!" footer. **Emit verbatim per LAW 5.**

## DEGRADED RUN WARNING (LAW 7 backstop)

Emit a `## Pre-Research Status: degraded` banner before the EVIDENCE envelope when:

- Topic is a bare named entity AND
- No `primary_entity` resolved in Step 0.5 AND
- Plan was deterministic (no LLM planner ran)

Suppress when plan_source is `external` / `llm`, or when pre-research flags resolved any signal, or when topic is multi-word lowercase abstract phrase.
