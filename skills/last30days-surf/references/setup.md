# Setup + troubleshooting

How to install, fund, configure, and recover surf for `last30days-surf`.

## Install

This skill is a Python pipeline (Python 3.12+). The Python script is invoked via the agent's Bash tool. No npm install, no skill compilation step.

Per-skill dependencies: just stdlib + `requests` (installed via your system package manager or `pip install requests`).

## Get a surf API key

1. Go to <https://surf.cascade.fyi/app>.
2. Sign in (OAuth via Tempo / Google / GitHub).
3. Generate an API key in the dashboard. Copy it.

## Fund the embedded balance

Surf bills the embedded balance per call. Calls are pay-per-use; nothing recurring.

The surf dashboard does NOT embed an on-ramp directly, so funding is a two-step:

1. Load USDC into a Tempo wallet at <https://wallet.tempo.xyz>.
2. Transfer that USDC into your surf wallet (address visible in the surf dashboard at <https://surf.cascade.fyi/app>).

A typical research run hits ~10-30 surf calls. Pricing (per surf docs at the time of writing): web/crawl ~$0.002, web/search ~$0.01, youtube/subtitles ~$0.01, twitter primitives ~$0.005, github primitives ~$0.005. **Run cost will be measured in actual tests during validation; the skill emits a per-source call count in the engine footer so users can see what they paid for.**

## Configure

Three places the skill looks for `SURF_API_KEY`, in priority order (highest wins):

1. **Process env**: `export SURF_API_KEY="..."` before invoking.
2. **Project config**: `.claude/last30days-surf.env` in the current directory or any parent (walk-up).
3. **Global config**: `~/.config/last30days-surf/.env`.

Use 600/400 file permissions on either config file (the skill warns at startup if it's group/world-readable).

Optional env vars:

| Var | Default | Purpose |
|---|---|---|
| `LAST30DAYS_PLANNER_MODEL` | `google/gemini-3.1-flash-lite-preview` | Override planner model. Any model in surf's inference router enum works. |
| `LAST30DAYS_RERANK_MODEL` | `google/gemini-3.1-flash-lite-preview` (default depth) / `google/gemini-3.1-pro-preview` (deep) | Override rerank/fun judge model. |
| `LAST30DAYS_REASONING_PROVIDER` | `surf` | Provider name. Hard-pinned to surf in this port. |
| `ELI5_MODE` | `false` | Persists ELI5 toggle across runs. |
| `LAST30DAYS_CONFIG_DIR` | `~/.config/last30days-surf` | Override global config dir. Set to `""` to skip global config. |

## Verify

```bash
python3 <skill-path>/scripts/last30days.py --diagnose
```

Expected output (with key set):

```json
{
  "providers": {"surf": true},
  "local_mode": false,
  "reasoning_provider": "surf",
  "x_backend": "surf",
  "available_sources": ["reddit", "hackernews", "polymarket", "github", "x", "youtube", "bluesky", "grounding", "tiktok", "instagram", "threads"],
  "has_surf": true,
  "has_github": true
}
```

Without the key:

```json
{
  "providers": {"surf": false},
  "local_mode": true,
  "available_sources": ["reddit", "hackernews", "polymarket", "github"],
  "has_surf": false
}
```

## Mock mode (no network)

To verify the pipeline orchestration without burning surf credits:

```bash
python3 <skill-path>/scripts/last30days.py --mock --quick "claude code"
```

Mock mode exercises planner + render + envelope contract end-to-end against fixtures. Useful when developing or debugging the skill itself.

## Troubleshooting

### HTTP 401 from surf

`SURF_API_KEY` is invalid or revoked. Verify at <https://surf.cascade.fyi/app>.

### HTTP 402 (Payment Required)

Embedded balance is empty. Top up via the wallet.tempo.xyz → surf wallet flow.

### HTTP 429 from direct sources

Reddit / GitHub / Algolia have rate-limited the egress IP. The skill auto-falls back to surf for resilience. If surf is also configured, brief should still render. If not, the source is marked unavailable in the footer.

### `outcome: bot_challenge` / `outcome: login_wall` from web/crawl (TikTok / Instagram / Threads)

Surf's mobile-proxy / decodo escalation didn't get past the platform's anti-bot. The skill marks the source unavailable cleanly. Brief renders without that source. This is a platform-side issue; not a config error.

### "Could not find SKILL.md" / wrong path

This skill ships at `skills/last30days-surf/SKILL.md` in the repo. Your skill loader's path-glob may be picking up an older snapshot if you've installed multiple last30days variants. List installed skills and remove duplicates.

### Brief is thin / "Evidence is thin for this topic"

Either the topic is too niche (low coverage everywhere) or the time window is empty (nothing significant happened in 30 days). Two recovery paths: ask the user to refine the topic, or pass `--days 90` / `--days 365` to widen the lookback window.

### Synthesis emits a trailing `Sources:` block (LAW 1 violation)

This is a documented model failure. The Pre-Present Self-Check in SKILL.md scans the last 15 lines and deletes Sources/References patterns. If it leaks past, file as a regression with the topic + run output.

### How do I run the pure-function tests?

```bash
cd <skill-path>
python3 -m pytest tests/ -q
```

Note: `just check` in the parent repo runs the policy linter only; the test suite runs separately.

### Watchlist / digest features

Out of scope for v0.1.0. Upstream's `briefing.py` / `watchlist.py` / `store.py` are not ported. If you need recurring research, schedule the agent invocation externally (cron, or this repo's `/schedule` command).
