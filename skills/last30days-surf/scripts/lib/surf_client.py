"""Surf API client for last30days-surf.

Thin HTTP wrapper around surf v2 endpoints (data tools) and surf inference
(LLM judge calls). Single auth scheme: `Authorization: Bearer $SURF_API_KEY`.

Endpoints (verified 2026-04-29):
- Data tools: https://surf.cascade.fyi/api/v2/{tool}
- Inference:  https://surf.cascade.fyi/api/v2/inference/v1/chat/completions
              (assumed; v1 inference exists but is x402-per-call only and
               does not honor the API-key embedded balance)

If `SURF_API_KEY` is unset, every surf call returns a sentinel `unavailable`
result so callers can mark the source unavailable cleanly without crashing.
This preserves the upstream "free baseline" UX (Reddit / HN / Polymarket /
GitHub still work direct-HTTP without a key).
"""

from __future__ import annotations

import os
from typing import Any, Optional

from . import http, log

SURF_BASE = "https://surf.cascade.fyi"
SURF_DATA_PREFIX = "/api/v2"
SURF_INFERENCE_PATH = "/api/v2/inference/v1/chat/completions"

DEFAULT_TIMEOUT = 60
INFERENCE_TIMEOUT = 120


def _api_key() -> Optional[str]:
    """Return the surf API key from env, or None if unset."""
    key = os.environ.get("SURF_API_KEY") or ""
    return key.strip() or None


def is_available() -> bool:
    return _api_key() is not None


def _auth_headers() -> dict[str, str]:
    key = _api_key()
    if not key:
        return {}
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


class SurfUnavailable(Exception):
    """Raised when SURF_API_KEY is not set and the caller invoked a surf-routed primitive."""


class SurfError(Exception):
    """Wraps non-2xx responses from surf with body for diagnosis."""
    def __init__(self, message: str, status_code: Optional[int] = None, body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


def post_v2(
    path: str,
    payload: dict[str, Any],
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """POST to a surf v2 data endpoint, returning parsed JSON.

    Args:
        path: trailing path under /api/v2/, e.g. "web/crawl", "twitter/search".
        payload: JSON body.
        timeout: request timeout seconds.

    Raises:
        SurfUnavailable: if SURF_API_KEY is unset.
        SurfError: on non-2xx response (wraps status + body).
        http.HTTPError: on transport-level failures after retries.
    """
    if not is_available():
        raise SurfUnavailable(f"surf path /api/v2/{path} called but SURF_API_KEY is not set")
    url = f"{SURF_BASE}{SURF_DATA_PREFIX}/{path.lstrip('/')}"
    try:
        return http.post(url, payload, headers=_auth_headers(), timeout=timeout)
    except http.HTTPError as e:
        raise SurfError(
            f"surf {path} returned HTTP {e.status_code}",
            status_code=e.status_code,
            body=e.body,
        ) from e


def post_inference(
    model: str,
    messages: list[dict[str, Any]],
    max_tokens: Optional[int] = None,
    temperature: float = 0.0,
    response_format: Optional[dict[str, Any]] = None,
    timeout: int = INFERENCE_TIMEOUT,
) -> dict[str, Any]:
    """POST to surf inference (OpenAI-compatible chat completion).

    Returns the raw OpenAI-style response dict; callers parse via
    `providers.extract_openai_text()` or equivalent.

    Raises:
        SurfUnavailable: if SURF_API_KEY is unset.
        SurfError: on non-2xx response.
    """
    if not is_available():
        raise SurfUnavailable("surf inference called but SURF_API_KEY is not set")
    url = f"{SURF_BASE}{SURF_INFERENCE_PATH}"
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if response_format is not None:
        payload["response_format"] = response_format
    try:
        return http.post(url, payload, headers=_auth_headers(), timeout=timeout)
    except http.HTTPError as e:
        # Surface 402 / 401 distinctly so callers can hint at funding state.
        if e.status_code == 402:
            log.debug(f"[surf_client] inference returned 402 (payment-required); embedded balance may need top-up")
        raise SurfError(
            f"surf inference returned HTTP {e.status_code}",
            status_code=e.status_code,
            body=e.body,
        ) from e


def crawl(
    url: str,
    format: str = "markdown",
    selector: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """surf web/crawl shorthand. Returns CrawlOutcome envelope per surf v2."""
    payload: dict[str, Any] = {"url": url, "format": format}
    if selector:
        payload["selector"] = selector
    return post_v2("web/crawl", payload, timeout=timeout)


def web_search(
    query: str,
    published_within_days: Optional[int] = None,
    include_domains: Optional[list[str]] = None,
    exclude_domains: Optional[list[str]] = None,
    response_format: str = "concise",
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """surf web/search shorthand."""
    payload: dict[str, Any] = {"query": query, "response_format": response_format}
    if published_within_days is not None:
        payload["published_within_days"] = published_within_days
    if include_domains:
        payload["include_domains"] = include_domains
    if exclude_domains:
        payload["exclude_domains"] = exclude_domains
    return post_v2("web/search", payload, timeout=timeout)


def youtube_subtitles(
    video_id: str,
    language_code: str = "en",
    origin: str = "uploader_provided",
    format: str = "inline",
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """surf youtube/subtitles shorthand."""
    return post_v2(
        "youtube/subtitles",
        {
            "video_id": video_id,
            "language_code": language_code,
            "origin": origin,
            "format": format,
        },
        timeout=timeout,
    )
