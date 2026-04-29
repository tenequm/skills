"""Reasoning provider routing for last30days-surf.

Single provider: surf inference (OpenAI-compatible chat completions endpoint
on the surf API, billed against the embedded balance via SURF_API_KEY).

Replaces upstream's GeminiClient / OpenAIClient / XAIClient / OpenRouterClient
multi-provider dispatch. The vendored planner.py and rerank.py call this
through the same `ReasoningClient` interface, so they work unchanged.

When SURF_API_KEY is unset, resolve_runtime() returns the upstream "local"
fallback (deterministic planner + local-score rerank, no LLM judge calls) so
the skill still produces a brief — just at degraded quality.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

from . import env, schema, surf_client

# Default models. Both pins must include the surf-required `google/` prefix.
GEMINI_FLASH_LITE = "google/gemini-3.1-flash-lite-preview"
GEMINI_PRO = "google/gemini-3.1-pro-preview"

# Legacy upstream constants kept for vendored-test compatibility. None of
# these endpoints are actually called in our port — surf inference replaces
# them all.
GEMINI_URL = ""
OPENAI_RESPONSES_URL = ""
CODEX_RESPONSES_URL = ""
XAI_RESPONSES_URL = ""
OPENROUTER_URL = ""
OPENROUTER_DEFAULT = GEMINI_FLASH_LITE
OPENAI_DEFAULT = GEMINI_FLASH_LITE
XAI_DEFAULT = GEMINI_FLASH_LITE


class ReasoningClient:
    """Shared interface for planner and rerank providers."""

    name: str

    def generate_text(
        self,
        model: str,
        prompt: str,
        *,
        tools: list[dict[str, Any]] | None = None,
        response_mime_type: str | None = None,
    ) -> str:
        raise NotImplementedError

    def generate_json(
        self,
        model: str,
        prompt: str,
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        text = self.generate_text(
            model, prompt, tools=tools, response_mime_type="application/json"
        )
        return extract_json(text)


class SurfReasoningClient(ReasoningClient):
    """Routes planner + rerank LLM calls through surf's OpenAI-compatible
    inference endpoint. Single auth path: SURF_API_KEY."""

    name = "surf"

    def generate_text(
        self,
        model: str,
        prompt: str,
        *,
        tools: list[dict[str, Any]] | None = None,
        response_mime_type: str | None = None,
    ) -> str:
        messages = [{"role": "user", "content": prompt}]
        response_format: dict[str, Any] | None = None
        if response_mime_type == "application/json":
            response_format = {"type": "json_object"}
        try:
            payload = surf_client.post_inference(
                model=model,
                messages=messages,
                temperature=0,
                response_format=response_format,
            )
        except surf_client.SurfUnavailable:
            return ""
        except surf_client.SurfError as e:
            print(
                f"[Providers] surf inference {e.status_code}: "
                f"{(e.body or '')[:300]}",
                file=sys.stderr,
            )
            return ""
        return extract_openai_text(payload)


# Provider -> (planner_default, rerank_default). Only "surf" is meaningful;
# other entries kept so vendored tests that probe the table don't KeyError.
_MODEL_DEFAULTS: dict[str, tuple[str, str]] = {
    "surf": (GEMINI_FLASH_LITE, GEMINI_FLASH_LITE),
    "gemini": (GEMINI_FLASH_LITE, GEMINI_FLASH_LITE),
    "openai": (GEMINI_FLASH_LITE, GEMINI_FLASH_LITE),
    "xai": (GEMINI_FLASH_LITE, GEMINI_FLASH_LITE),
    "openrouter": (GEMINI_FLASH_LITE, GEMINI_FLASH_LITE),
}


def _resolve_model_pins(
    config: dict[str, Any], depth: str, provider_name: str
) -> tuple[str, str]:
    default_planner, default_rerank = _MODEL_DEFAULTS.get(
        provider_name, (GEMINI_FLASH_LITE, GEMINI_FLASH_LITE)
    )
    if depth == "deep":
        default_rerank = GEMINI_PRO

    planner_model = config.get("LAST30DAYS_PLANNER_MODEL") or default_planner
    rerank_model = config.get("LAST30DAYS_RERANK_MODEL") or default_rerank
    return planner_model, rerank_model


def _resolve_x_backend(config: dict[str, Any]) -> str | None:
    """X/Twitter backend selector. Surf is the only path in our port."""
    return env.get_x_source(config)


def mock_runtime(config: dict[str, Any], depth: str) -> schema.ProviderRuntime:
    """Resolve model pins for mock/test mode without requiring live creds."""
    provider_name = (config.get("LAST30DAYS_REASONING_PROVIDER") or "surf").lower()
    if provider_name == "auto":
        provider_name = "surf"
    planner_model, rerank_model = _resolve_model_pins(config, depth, provider_name)
    return schema.ProviderRuntime(
        reasoning_provider=provider_name,
        planner_model=planner_model,
        rerank_model=rerank_model,
        x_search_backend=_resolve_x_backend(config),
    )


def resolve_runtime(
    config: dict[str, Any], depth: str
) -> tuple[schema.ProviderRuntime, ReasoningClient | None]:
    """Resolve the reasoning provider and pinned models for a run.

    If SURF_API_KEY is configured (and provider is "surf"/"auto"), returns a
    SurfReasoningClient that routes LLM calls through surf inference.
    Otherwise falls back to the upstream "local" deterministic mode (no
    client; planner runs the regex cascade, rerank uses local_relevance only).
    """
    provider_name = (
        config.get("LAST30DAYS_REASONING_PROVIDER") or "auto"
    ).lower()
    surf_key = config.get("SURF_API_KEY")

    if provider_name in ("auto", "surf") and surf_key:
        planner_model, rerank_model = _resolve_model_pins(config, depth, "surf")
        runtime = schema.ProviderRuntime(
            reasoning_provider="surf",
            planner_model=planner_model,
            rerank_model=rerank_model,
            x_search_backend=_resolve_x_backend(config),
        )
        return runtime, SurfReasoningClient()

    # Local fallback (no LLM judge). Matches upstream behavior when no
    # provider key is set: deterministic planner + local-score rerank.
    return (
        schema.ProviderRuntime(
            reasoning_provider="local",
            planner_model="deterministic",
            rerank_model="local-score",
            x_search_backend=_resolve_x_backend(config),
        ),
        None,
    )


# ---------------------------------------------------------------------------
# Response parsing helpers (kept verbatim from upstream — vendored callers
# import these directly).
# ---------------------------------------------------------------------------

def extract_json(text: str) -> dict[str, Any]:
    """Extract the first JSON object from a model response."""
    text = text.strip()
    if not text:
        raise ValueError("Expected JSON response, got empty text")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise
        return json.loads(match.group(0))


def extract_openai_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    output = payload.get("output") or payload.get("choices") or []
    for item in output:
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            if isinstance(item.get("text"), str):
                return item["text"]
            content = item.get("content") or []
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and isinstance(part.get("text"), str):
                        return part["text"]
                    if (
                        isinstance(part, dict)
                        and part.get("type") == "output_text"
                        and isinstance(part.get("text"), str)
                    ):
                        return part["text"]
            message = item.get("message") or {}
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"]
    if payload:
        print(
            f"[Providers] extract_openai_text: no text in payload keys: "
            f"{list(payload.keys())}",
            file=sys.stderr,
        )
    return ""


def extract_gemini_text(payload: dict[str, Any]) -> str:
    """Compat shim. Surf does not return Gemini-native shapes; this exists
    only so vendored tests that mock Gemini-style payloads still pass."""
    for candidate in payload.get("candidates", []):
        content = candidate.get("content") or {}
        for part in content.get("parts", []):
            text = part.get("text")
            if text:
                return text
    return ""
