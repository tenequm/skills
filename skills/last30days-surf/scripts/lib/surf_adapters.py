"""Surf-routed adapters for last30days-surf.

One function per source. Each function:
  - Takes the upstream signature (query/topic, from_date, to_date, depth, ...)
  - Calls surf v2 endpoints via surf_client
  - Returns a list of items in the same shape upstream's `parse_X_response()`
    produces, so pipeline.py / normalize.py / signals.py work unchanged.

Used by pipeline.py either as:
  - PRIMARY for sources upstream needed paid keys for: X / YouTube / TikTok /
    Instagram / Threads / Pinterest / Bluesky.
  - FALLBACK for the free-baseline sources when direct HTTP fails: Reddit,
    Hacker News, Polymarket, GitHub.

If surf is unavailable (no SURF_API_KEY), every function returns [] so the
caller can mark the source unavailable cleanly.
"""

from __future__ import annotations

import json
import math
import re
import sys
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus

from . import dates, log, surf_client
from .relevance import token_overlap_relevance


def _log(msg: str) -> None:
    log.debug(f"[surf_adapters] {msg}")


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def _iso_to_date(value: Any) -> str | None:
    """Best-effort ISO datetime / unix timestamp -> YYYY-MM-DD."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc).strftime("%Y-%m-%d")
        except (ValueError, OSError):
            return None
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        # ISO 8601 'YYYY-MM-DDTHH:MM:SS...' or 'YYYY-MM-DD'.
        if len(s) >= 10:
            return s[:10]
    return None


def _in_window(date_str: str | None, from_date: str, to_date: str) -> bool:
    if not date_str:
        return True  # keep undated items by default; date filter is per-source policy
    return from_date <= date_str <= to_date


# ---------------------------------------------------------------------------
# REDDIT
# ---------------------------------------------------------------------------

def reddit_search(
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    subreddits: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Surf fallback for Reddit search. Returns reddit_public-shaped items.

    Calls surf v2 reddit/search; falls back to empty list on error so
    pipeline.py's chain (public direct -> surf -> empty) degrades cleanly.
    """
    if not surf_client.is_available():
        return []
    limit = {"quick": 15, "default": 30, "deep": 60}.get(depth, 30)
    payload: dict[str, Any] = {"query": topic, "sort": "top", "time": "month", "limit": limit}
    if subreddits:
        # Reddit allows space-separated subreddit:foo terms in the query.
        sub_clause = " OR ".join(f"subreddit:{s.lstrip('r/')}" for s in subreddits[:5])
        payload["query"] = f"{topic} ({sub_clause})"
    try:
        data = surf_client.post_v2("reddit/search", payload)
    except surf_client.SurfError as e:
        _log(f"reddit/search HTTP {e.status_code}: {(e.body or '')[:200]}")
        return []
    posts = data.get("posts") or data.get("results") or data.get("items") or []
    items: list[dict[str, Any]] = []
    for post in posts:
        score = _safe_int(post.get("score") or post.get("ups"))
        num_comments = _safe_int(post.get("num_comments") or post.get("comments_count"))
        permalink = post.get("permalink") or post.get("url") or ""
        if "/comments/" not in permalink:
            continue
        if not permalink.startswith("http"):
            permalink = f"https://www.reddit.com{permalink}"
        date_str = _iso_to_date(post.get("created_utc") or post.get("created_at"))
        if not _in_window(date_str, from_date, to_date):
            continue
        author = str(post.get("author") or "[deleted]").strip() or "[deleted]"
        items.append({
            "id": "",
            "title": str(post.get("title") or "").strip(),
            "url": permalink,
            "score": score,
            "num_comments": num_comments,
            "subreddit": str(post.get("subreddit") or "").strip(),
            "created_utc": _safe_float(post.get("created_utc")),
            "author": author if author not in ("[deleted]", "[removed]") else "[deleted]",
            "selftext": str(post.get("selftext") or "")[:500],
            "date": date_str,
            "engagement": {
                "score": score,
                "num_comments": num_comments,
                "upvote_ratio": post.get("upvote_ratio"),
            },
            "relevance": 0.6,
            "why_relevant": "Reddit search via surf",
            "metadata": {},
        })
    items.sort(key=lambda x: x["engagement"]["score"], reverse=True)
    for i, item in enumerate(items):
        item["id"] = f"R{i + 1}"
    return items


# ---------------------------------------------------------------------------
# X / TWITTER
# ---------------------------------------------------------------------------

def twitter_search(
    query: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
) -> list[dict[str, Any]]:
    if not surf_client.is_available():
        return []
    limit = {"quick": 12, "default": 30, "deep": 60}.get(depth, 30)
    try:
        data = surf_client.post_v2(
            "twitter/search",
            {"query": f"{query} since:{from_date}", "limit": limit},
        )
    except surf_client.SurfError as e:
        _log(f"twitter/search HTTP {e.status_code}: {(e.body or '')[:200]}")
        return []
    tweets = data.get("tweets") or data.get("results") or []
    items: list[dict[str, Any]] = []
    for i, t in enumerate(tweets):
        author = t.get("author") or {}
        metrics = t.get("public_metrics") or {}
        date_str = _iso_to_date(t.get("created_at"))
        if not _in_window(date_str, from_date, to_date):
            continue
        likes = _safe_int(metrics.get("like_count"))
        retweets = _safe_int(metrics.get("retweet_count"))
        replies = _safe_int(metrics.get("reply_count"))
        quotes = _safe_int(metrics.get("quote_count"))
        items.append({
            "id": str(t.get("id") or f"X{i+1}"),
            "title": str(t.get("text") or "")[:200],
            "url": t.get("url") or f"https://x.com/i/status/{t.get('id', '')}",
            "text": str(t.get("text") or ""),
            "author": author.get("username") or "",
            "author_handle": author.get("username") or "",
            "author_name": author.get("name") or "",
            "date": date_str,
            "engagement": {
                "likes": likes,
                "retweets": retweets,
                "reposts": retweets,
                "replies": replies,
                "quotes": quotes,
                "impressions": _safe_int(metrics.get("impression_count")),
                "bookmarks": _safe_int(metrics.get("bookmark_count")),
            },
            "relevance": 0.7,
            "why_relevant": "X search via surf",
            "metadata": {"lang": t.get("lang"), "source": t.get("source")},
        })
    return items


# ---------------------------------------------------------------------------
# YOUTUBE
# ---------------------------------------------------------------------------

_YT_VIDEO_ID_RE = re.compile(r"(?:v=|/shorts/|/embed/|youtu\.be/)([\w-]{11})")


def _extract_video_id(url: str) -> str | None:
    m = _YT_VIDEO_ID_RE.search(url or "")
    return m.group(1) if m else None


def youtube_search(
    query: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
) -> list[dict[str, Any]]:
    if not surf_client.is_available():
        return []
    n = {"quick": 5, "default": 10, "deep": 20}.get(depth, 10)
    try:
        data = surf_client.web_search(
            query=f"{query} site:youtube.com",
            published_within_days=30,
        )
    except surf_client.SurfError as e:
        _log(f"web/search YT HTTP {e.status_code}: {(e.body or '')[:200]}")
        return []
    results = data.get("results") or []
    items: list[dict[str, Any]] = []
    for r in results[:n]:
        url = r.get("url") or ""
        vid = _extract_video_id(url)
        if not vid:
            continue
        date_str = _iso_to_date(r.get("published_date"))
        if not _in_window(date_str, from_date, to_date):
            continue
        # Best-effort transcript fetch (subtitles).
        transcript_snippet = ""
        try:
            sub = surf_client.youtube_subtitles(video_id=vid, format="inline")
            if isinstance(sub.get("vtt"), str):
                transcript_snippet = sub["vtt"][:5000]
        except surf_client.SurfError:
            pass
        items.append({
            "id": vid,
            "title": r.get("title") or "",
            "url": url,
            "channel": r.get("author") or "",
            "date": date_str,
            "engagement": {"views": 0, "likes": 0, "comments": 0},
            "snippet": (r.get("snippet") or "")[:500],
            "transcript_snippet": transcript_snippet,
            "transcript_highlights": [],
            "relevance": 0.65,
            "why_relevant": "YouTube discovery via surf web search",
            "metadata": {},
        })
    return items


# ---------------------------------------------------------------------------
# BLUESKY
# ---------------------------------------------------------------------------

def bluesky_search(
    query: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
) -> list[dict[str, Any]]:
    if not surf_client.is_available():
        return []
    limit = {"quick": 10, "default": 25, "deep": 50}.get(depth, 25)
    url = (
        "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
        f"?q={quote_plus(query)}&sort=top&limit={limit}"
    )
    try:
        data = surf_client.crawl(url, format="json")
    except surf_client.SurfError as e:
        _log(f"bluesky search HTTP {e.status_code}: {(e.body or '')[:200]}")
        return []
    body = (data.get("content") or [None])[0]
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            return []
    if not isinstance(body, dict):
        return []
    posts = body.get("posts") or []
    items: list[dict[str, Any]] = []
    for p in posts:
        record = p.get("record") or {}
        author = p.get("author") or {}
        date_str = _iso_to_date(p.get("indexedAt") or record.get("createdAt"))
        if not _in_window(date_str, from_date, to_date):
            continue
        items.append({
            "id": p.get("uri") or "",
            "title": (record.get("text") or "")[:200],
            "url": (
                f"https://bsky.app/profile/{author.get('handle','')}/post/"
                f"{(p.get('uri') or '').rsplit('/', 1)[-1]}"
            ),
            "text": record.get("text") or "",
            "author": author.get("handle") or "",
            "author_name": author.get("displayName") or "",
            "date": date_str,
            "engagement": {
                "likes": _safe_int(p.get("likeCount")),
                "reposts": _safe_int(p.get("repostCount")),
                "replies": _safe_int(p.get("replyCount")),
                "quotes": _safe_int(p.get("quoteCount")),
            },
            "relevance": 0.6,
            "why_relevant": "Bluesky search via surf",
            "metadata": {},
        })
    return items


# ---------------------------------------------------------------------------
# TIKTOK / INSTAGRAM / THREADS / PINTEREST (web/crawl-based)
# ---------------------------------------------------------------------------

def _crawl_or_empty(url: str) -> dict[str, Any] | None:
    if not surf_client.is_available():
        return None
    try:
        data = surf_client.crawl(url)
    except surf_client.SurfError as e:
        _log(f"crawl {url} HTTP {e.status_code}: {(e.body or '')[:200]}")
        return None
    if data.get("outcome") and data["outcome"] != "success":
        _log(f"crawl {url} outcome={data['outcome']}; marking unavailable")
        return None
    return data


def tiktok_search(
    query: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    hashtags: list[str] | None = None,
    creators: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Surf-only TikTok adapter. Tries search URL; tags/creators if provided.

    Returns thin items (TikTok SSR doesn't always expose engagement to
    anonymous fetches). Pipeline marks the source unavailable cleanly when
    the crawl hits a bot challenge or login wall.
    """
    if not surf_client.is_available():
        return []
    items: list[dict[str, Any]] = []
    targets = [f"https://www.tiktok.com/search/video?q={quote_plus(query)}"]
    for h in (hashtags or [])[:2]:
        targets.append(f"https://www.tiktok.com/tag/{quote_plus(h.lstrip('#'))}")
    for c in (creators or [])[:2]:
        targets.append(f"https://www.tiktok.com/@{c.lstrip('@')}")
    for url in targets[:3]:
        data = _crawl_or_empty(url)
        if not data:
            continue
        # Best-effort: surf returns an SSR JSON blob; pipeline does not depend
        # on per-item parsing here for v0.1.0 — just mark presence.
        items.append({
            "id": url,
            "title": f"TikTok search: {query}" if "/search/" in url else url,
            "url": url,
            "author": "",
            "date": None,
            "engagement": {"views": 0, "likes": 0, "comments": 0, "shares": 0},
            "snippet": "",
            "relevance": 0.4,
            "why_relevant": "TikTok crawl via surf",
            "metadata": {"raw_outcome": data.get("outcome")},
        })
    return items


def instagram_search(
    query: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    ig_creators: list[str] | None = None,
) -> list[dict[str, Any]]:
    if not surf_client.is_available():
        return []
    items: list[dict[str, Any]] = []
    targets = [f"https://www.instagram.com/explore/tags/{quote_plus(query.replace(' ', ''))}/"]
    for c in (ig_creators or [])[:2]:
        targets.append(f"https://www.instagram.com/{c.lstrip('@')}/")
    for url in targets[:3]:
        data = _crawl_or_empty(url)
        if not data:
            continue
        items.append({
            "id": url,
            "title": f"Instagram tag: {query}" if "/tags/" in url else url,
            "url": url,
            "author": "",
            "date": None,
            "engagement": {"views": 0, "likes": 0, "comments": 0},
            "snippet": "",
            "relevance": 0.4,
            "why_relevant": "Instagram crawl via surf",
            "metadata": {"raw_outcome": data.get("outcome")},
        })
    return items


def threads_search(
    query: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
) -> list[dict[str, Any]]:
    if not surf_client.is_available():
        return []
    url = f"https://www.threads.com/search?q={quote_plus(query)}&serp_type=default"
    data = _crawl_or_empty(url)
    if not data:
        return []
    return [{
        "id": url,
        "title": f"Threads search: {query}",
        "url": url,
        "author": "",
        "date": None,
        "engagement": {"likes": 0, "replies": 0, "reposts": 0, "quotes": 0},
        "snippet": "",
        "relevance": 0.4,
        "why_relevant": "Threads crawl via surf",
        "metadata": {"raw_outcome": data.get("outcome")},
    }]


def pinterest_search(
    query: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
) -> list[dict[str, Any]]:
    if not surf_client.is_available():
        return []
    url = f"https://www.pinterest.com/search/pins/?q={quote_plus(query)}"
    data = _crawl_or_empty(url)
    if not data:
        return []
    return [{
        "id": url,
        "title": f"Pinterest search: {query}",
        "url": url,
        "author": "",
        "date": None,
        "engagement": {"saves": 0, "comments": 0},
        "snippet": "",
        "relevance": 0.4,
        "why_relevant": "Pinterest crawl via surf",
        "metadata": {"raw_outcome": data.get("outcome")},
    }]


# ---------------------------------------------------------------------------
# HACKER NEWS / POLYMARKET — surf fallback when direct fails
# ---------------------------------------------------------------------------

def _crawl_json(target_url: str) -> Any:
    if not surf_client.is_available():
        return None
    try:
        data = surf_client.crawl(target_url, format="json")
    except surf_client.SurfError as e:
        _log(f"crawl {target_url} HTTP {e.status_code}: {(e.body or '')[:200]}")
        return None
    body = (data.get("content") or [None])[0]
    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return None
    return body


def hackernews_search(
    query: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
) -> list[dict[str, Any]]:
    """Surf fallback when direct Algolia fails."""
    epoch_from = int(datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc).timestamp())
    hits_per_page = {"quick": 15, "default": 30, "deep": 60}.get(depth, 30)
    target = (
        "https://hn.algolia.com/api/v1/search?"
        f"query={quote_plus(query)}&tags=story&"
        f"numericFilters=created_at_i>{epoch_from},points>2&"
        f"hitsPerPage={hits_per_page}"
    )
    body = _crawl_json(target)
    if not isinstance(body, dict):
        return []
    hits = body.get("hits") or []
    items: list[dict[str, Any]] = []
    for i, hit in enumerate(hits):
        object_id = str(hit.get("objectID") or "")
        points = _safe_int(hit.get("points"))
        num_comments = _safe_int(hit.get("num_comments"))
        date_str = _iso_to_date(hit.get("created_at"))
        article_url = hit.get("url") or ""
        hn_url = f"https://news.ycombinator.com/item?id={object_id}"
        rank_score = max(0.3, 1.0 - (i * 0.02))
        engagement_boost = min(0.2, math.log1p(points) / 40)
        if query:
            content_score = token_overlap_relevance(query, hit.get("title", ""))
            relevance = min(1.0, 0.6 * rank_score + 0.4 * content_score + engagement_boost)
        else:
            relevance = min(1.0, rank_score * 0.7 + engagement_boost + 0.1)
        items.append({
            "id": object_id,
            "title": hit.get("title", ""),
            "url": article_url,
            "hn_url": hn_url,
            "author": hit.get("author", ""),
            "date": date_str,
            "engagement": {"points": points, "comments": num_comments},
            "relevance": round(relevance, 2),
            "why_relevant": f"HN story (surf fallback): {hit.get('title', '')[:60]}",
        })
    return items


def polymarket_search(
    query: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
) -> list[dict[str, Any]]:
    """Surf fallback for Polymarket when direct Gamma fails. Returns raw
    market dicts; pipeline.py applies upstream's polymarket.parse_polymarket_response
    afterwards (the upstream parser handles filtering/relevance/movement)."""
    target = (
        "https://gamma-api.polymarket.com/markets?"
        "active=true&closed=false&order=volume24hr&ascending=false&limit=20"
    )
    body = _crawl_json(target)
    if not isinstance(body, list):
        return []
    # Return upstream-shaped wrapper so polymarket.parse_polymarket_response()
    # can normalize it. Upstream expects dict with "items"; markets are passed
    # through the same path.
    return body


# ---------------------------------------------------------------------------
# GITHUB — surf fallback for anonymous-rate-limited cases
# ---------------------------------------------------------------------------

def github_search(
    query: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    kind: str = "conversations",
) -> list[dict[str, Any]]:
    if not surf_client.is_available():
        return []
    per_page = {"quick": 15, "default": 30, "deep": 60}.get(depth, 30)
    try:
        data = surf_client.post_v2(
            "github/search",
            {
                "query": f"{query} created:>{from_date}",
                "kind": kind,
                "per_page": per_page,
                "sort": "reactions",
                "order": "desc",
            },
        )
    except surf_client.SurfError as e:
        _log(f"github/search HTTP {e.status_code}: {(e.body or '')[:200]}")
        return []
    results = data.get("results") or data.get("items") or []
    items: list[dict[str, Any]] = []
    for r in results:
        date_str = _iso_to_date(r.get("created_at") or r.get("updated_at"))
        items.append({
            "id": str(r.get("id") or r.get("number") or ""),
            "title": r.get("title") or r.get("full_name") or "",
            "url": r.get("html_url") or r.get("url") or "",
            "repo": r.get("repository_full_name") or r.get("full_name") or "",
            "state": r.get("state") or "",
            "date": date_str,
            "engagement": {
                "reactions": _safe_int((r.get("reactions") or {}).get("total_count")),
                "comments": _safe_int(r.get("comments")),
                "stars": _safe_int(r.get("stargazers_count")),
                "forks": _safe_int(r.get("forks_count")),
            },
            "is_pr": bool(r.get("pull_request")),
            "snippet": (r.get("body") or r.get("description") or "")[:300],
            "relevance": 0.65,
            "why_relevant": "GitHub search via surf",
        })
    return items


# ---------------------------------------------------------------------------
# WEB SEARCH (replaces grounding.py multi-backend)
# ---------------------------------------------------------------------------

def web_search(
    query: str,
    date_range: tuple[str, str],
    config: dict[str, Any],
    backend: str = "auto",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Surf web/search + selective crawl. Returns (items, meta) matching
    upstream grounding.web_search() signature so pipeline.py is unchanged."""
    if not surf_client.is_available():
        return [], {"backend": "unavailable", "error": "SURF_API_KEY not set"}
    from_date, to_date = date_range
    days = max(1, (datetime.fromisoformat(to_date) - datetime.fromisoformat(from_date)).days)
    try:
        data = surf_client.web_search(
            query=query, published_within_days=days, response_format="concise"
        )
    except surf_client.SurfError as e:
        return [], {"backend": "surf", "error": f"HTTP {e.status_code}", "body": (e.body or "")[:200]}
    results = data.get("results") or []
    items: list[dict[str, Any]] = []
    for r in results:
        date_str = _iso_to_date(r.get("published_date"))
        if not _in_window(date_str, from_date, to_date):
            continue
        items.append({
            "id": r.get("url") or "",
            "title": r.get("title") or "",
            "url": r.get("url") or "",
            "author": r.get("author") or "",
            "date": date_str,
            "snippet": (r.get("snippet") or "")[:1000],
            "highlights": r.get("highlights") or [],
            "engagement": {},
            "relevance": _safe_float(r.get("score"), 0.6),
            "why_relevant": "web search via surf",
        })
    return items, {"backend": "surf", "count": len(items)}
