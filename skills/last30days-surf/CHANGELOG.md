# Changelog

All notable changes to `last30days-surf` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.2.1] - 2026-04-30

### Changed

- Replaced inline 40-char upstream SHA `5b87cca886c98d47b0dcbf00a7363320d935c82e` with short SHA `5b87cca` (linked to GitHub commit) in `SKILL.md` `metadata.upstream` and CHANGELOG references. ClawHub static analyzer was flagging the bare 40-char hex as `suspicious.exposed_secret_literal`.

## [0.1.0] - 2026-04-30

### Added

- Initial release. Port of [`mvanhorn/last30days-skill`](https://github.com/mvanhorn/last30days-skill) (MIT) at SHA [`5b87cca`](https://github.com/mvanhorn/last30days-skill/commit/5b87cca).
- Hybrid source routing: free baseline (Reddit / Hacker News / Polymarket / GitHub) via direct HTTP, all other sources (X / YouTube / Bluesky / TikTok / Instagram / Threads / Pinterest / Web search / LLM judges) via surf v2 HTTP API. Surf is the resilience fallback for the four free-baseline sources when direct HTTP fails (rate-limit, anti-bot, IP block).
- Single auth path: `SURF_API_KEY` (env var or `~/.config/last30days-surf/.env` / `.claude/last30days-surf.env`). Replaces upstream's seven separate keys (xAI, ScrapeCreators, Brave, OpenRouter, Apify, X browser cookies, yt-dlp install).
- LLM planner + relevance judge + fun judge route through surf inference (`/api/v2/inference/v1/chat/completions`, OpenAI-compatible). Defaults: `google/gemini-3.1-flash-lite-preview` (planner + default-depth rerank), `google/gemini-3.1-pro-preview` (deep-depth rerank). Override via `LAST30DAYS_PLANNER_MODEL` / `LAST30DAYS_RERANK_MODEL`.
- New module `lib/surf_client.py` — thin HTTP wrapper with `Authorization: Bearer` auth.
- New module `lib/surf_adapters.py` — per-source helpers that produce upstream's item shape from surf v2 responses.
- All voice contract / 9 LAWs / ELI5 toggle / expert-mode posture / refuse-gate / vs-mode / `--competitors` auto-discovery / planner JSON shape / rerank rubric / cluster algorithm / render envelopes ported verbatim from upstream.

### Changed

- `lib/env.py`: from 650 lines down to ~250 lines. Dropped Codex CLI auth helpers (vestigial in upstream itself per `env.py:180-182` "intentionally skipped" comment), all paid-key env reads (xAI / OpenAI / Google / OpenRouter / Brave / Exa / Serper / Parallel / ScrapeCreators / Apify / Twitter cookies), browser-cookie extraction. Kept `SURF_API_KEY`, model pin overrides, ELI5 toggle, project / global `.env` loaders.
- `lib/providers.py`: dropped `GeminiClient` / `OpenAIClient` / `XAIClient` / `OpenRouterClient` multi-provider dispatch. Single `SurfReasoningClient` routes through `surf_client.post_inference()`. Falls back to local-deterministic mode when `SURF_API_KEY` is unset (upstream-compat behavior).
- `lib/pipeline.py:_retrieve_stream`: rewired all source branches. Free-baseline sources keep their direct-HTTP primary call and add a surf fallback on exception. Surf-only sources skip direct entirely. Out-of-scope sources (Truth Social / Xiaohongshu / Perplexity / xquik) return empty.
- `lib/pipeline.py:available_sources`: rewritten to gate paid sources on `SURF_API_KEY` presence. Free baseline always available.
- `lib/pipeline.py:_surf_search_handles`: replaces upstream's `bird_x.search_handles()` Phase 2 X handle drilldown with `surf twitter/search from:{handle}`.
- `lib/competitors.py`, `lib/resolve.py`: import alias `surf_adapters as grounding` so the upstream `grounding.web_search()` callsites continue to work.
- `lib/ui.py`: replaced upstream's 610-line terminal banner / spinner module with a 50-line stderr-emitting stub. Agent-via-Bash invocation pattern doesn't see live progress; one-line state announcements are sufficient.
- Slug renamed from `last30days` to `last30days-surf` to avoid collision with upstream's existing ClawHub publication.

### Removed

Sources upstream supported that surf cannot reach today (marked out-of-scope, pipeline returns empty):

- Truth Social (Cloudflare-locked, no surf path).
- Xiaohongshu (RED) (self-hosted MCP gateway, no surf path).
- Perplexity Sonar (`surf web/search` is Exa, same backend — duplicate).
- xquik (X-cluster collapsed to single surf twitter primitive).

Features upstream has that v0.1.0 doesn't:

- Watchlist / daily-weekly digest (`briefing.py`, `watchlist.py`, `store.py`). Use `/schedule` from the parent repo for recurring research.
- Codex CLI / Gemini CLI / Claude CLI auth detection. Codex was intentionally skipped in upstream (chatgpt.com backend instability); Gemini CLI and Claude CLI auth never existed in upstream.
- Multi-runtime plugin manifests (`.claude-plugin/`, `.codex-plugin/`, `gemini-extension.json`, `agents/openai.yaml`). This repo's distribution is ClawHub-only via the existing publish flow.

### Verified against

- Upstream [`mvanhorn/last30days-skill@5b87cca`](https://github.com/mvanhorn/last30days-skill/commit/5b87cca) (2026-04-26)
- Surf API v2 (data tools + inference), verified live 2026-04-30. All 17 endpoints on `https://surf.cascade.fyi/api/v2/*` return 200 with valid payloads. End-to-end live run on `--depth quick` for "claude code" returned 124 items across 10 active sources with LLM-judged relevance + fun scoring intact.
- Surf inference models confirmed available: `google/gemini-3.1-flash-lite-preview`, `google/gemini-3.1-pro-preview`
