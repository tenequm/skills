"""Environment + config loading for last30days-surf.

Single auth source: SURF_API_KEY. All upstream multi-provider / cookie /
Codex-CLI machinery is removed because surf replaces it.

Public surface preserved (so vendored callers in pipeline.py /
planner.py / providers.py / etc. work unchanged):
  - get_config() -> dict
  - load_env_file(Path) -> dict
  - config_exists() -> bool
  - get_reddit_source(config) -> str | None
  - get_x_source(config) -> str | None
  - get_x_source_with_method(config) -> (str | None, str)
  - is_reddit_available(config) -> bool
  - AUTH_STATUS_OK / AUTH_STATUS_MISSING / AUTH_SOURCE_API_KEY / AUTH_SOURCE_NONE

The skill's adapters check `surf_client.is_available()` at call time;
provider routing is hard-pinned to "surf" via LAST30DAYS_REASONING_PROVIDER
default. Sources upstream couldn't reach without keys (Truth Social,
Xiaohongshu, Perplexity Sonar) are always reported unavailable.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Literal

_config_override = os.environ.get('LAST30DAYS_CONFIG_DIR')
if _config_override == "":
    CONFIG_DIR: Path | None = None
    CONFIG_FILE: Path | None = None
elif _config_override:
    CONFIG_DIR = Path(_config_override)
    CONFIG_FILE = CONFIG_DIR / ".env"
else:
    CONFIG_DIR = Path.home() / ".config" / "last30days-surf"
    CONFIG_FILE = CONFIG_DIR / ".env"

PROJECT_ENV_FILENAME = "last30days-surf.env"

AuthSource = Literal["api_key", "none"]
AuthStatus = Literal["ok", "missing"]
AUTH_SOURCE_API_KEY: AuthSource = "api_key"
AUTH_SOURCE_NONE: AuthSource = "none"
AUTH_STATUS_OK: AuthStatus = "ok"
AUTH_STATUS_MISSING: AuthStatus = "missing"


def _check_file_permissions(path: Path) -> None:
    try:
        mode = path.stat().st_mode
        if mode & 0o044:
            sys.stderr.write(
                f"[last30days-surf] WARNING: {path} is readable by other users. "
                f"Run: chmod 600 {path}\n"
            )
            sys.stderr.flush()
    except OSError as exc:
        sys.stderr.write(f"[last30days-surf] WARNING: could not stat {path}: {exc}\n")
        sys.stderr.flush()


def load_env_file(path: Path | None) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path or not path.exists():
        return env
    _check_file_permissions(path)
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if value and value[0] in ('"', "'") and value[-1] == value[0]:
                value = value[1:-1]
            if key and value:
                env[key] = value
    return env


def _find_project_env() -> Path | None:
    """Walk up from cwd looking for .claude/last30days-surf.env."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / ".claude" / PROJECT_ENV_FILENAME
        if candidate.exists():
            return candidate
        if parent == Path.home() or parent == parent.parent:
            break
    return None


def get_config() -> dict[str, Any]:
    """Load configuration. Priority: env vars > project .env > global .env.

    Always returns the same key set so vendored callers work unchanged.
    """
    file_env = load_env_file(CONFIG_FILE) if CONFIG_FILE else {}
    project_env_path = _find_project_env()
    project_env = load_env_file(project_env_path) if project_env_path else {}
    merged_env = {**file_env, **project_env}

    surf_api_key = os.environ.get("SURF_API_KEY") or merged_env.get("SURF_API_KEY")

    config: dict[str, Any] = {
        # Surf is the canonical (and only) auth path.
        "SURF_API_KEY": surf_api_key,
        # Provider hard-pinned to surf so upstream's auto-resolution doesn't
        # try Gemini/OpenAI/xAI/OpenRouter chains. The vendored providers.py
        # exposes a single SurfRouter that handles this.
        "LAST30DAYS_REASONING_PROVIDER": (
            os.environ.get("LAST30DAYS_REASONING_PROVIDER")
            or merged_env.get("LAST30DAYS_REASONING_PROVIDER")
            or "surf"
        ),
        # Model pin overrides — default to upstream's defaults with the
        # surf-required `google/` prefix.
        "LAST30DAYS_PLANNER_MODEL": (
            os.environ.get("LAST30DAYS_PLANNER_MODEL")
            or merged_env.get("LAST30DAYS_PLANNER_MODEL")
        ),
        "LAST30DAYS_RERANK_MODEL": (
            os.environ.get("LAST30DAYS_RERANK_MODEL")
            or merged_env.get("LAST30DAYS_RERANK_MODEL")
        ),
        # Upstream-compat shims; always None in our port. Kept so vendored
        # callers that read these keys don't KeyError.
        "OPENAI_API_KEY": None,
        "OPENAI_AUTH_SOURCE": AUTH_SOURCE_NONE,
        "OPENAI_AUTH_STATUS": AUTH_STATUS_MISSING,
        "OPENAI_CHATGPT_ACCOUNT_ID": None,
        "CODEX_AUTH_FILE": None,
        "GOOGLE_API_KEY": None,
        "GEMINI_API_KEY": None,
        "GOOGLE_GENAI_API_KEY": None,
        "XAI_API_KEY": None,
        "OPENROUTER_API_KEY": None,
        "BRAVE_API_KEY": None,
        "EXA_API_KEY": None,
        "SERPER_API_KEY": None,
        "PARALLEL_API_KEY": None,
        "SCRAPECREATORS_API_KEY": None,
        "APIFY_API_TOKEN": None,
        "AUTH_TOKEN": None,
        "CT0": None,
        "BSKY_HANDLE": None,
        "BSKY_APP_PASSWORD": None,
        "TRUTHSOCIAL_TOKEN": None,
        "XIAOHONGSHU_API_BASE": None,
        "XQUIK_API_KEY": None,
        "FROM_BROWSER": "off",
        "INCLUDE_SOURCES": "",
        # ELI5 toggle persistence, kept verbatim.
        "ELI5_MODE": (
            os.environ.get("ELI5_MODE")
            or merged_env.get("ELI5_MODE")
            or "false"
        ),
    }

    if project_env_path:
        config["_CONFIG_SOURCE"] = f"project:{project_env_path}"
    elif CONFIG_FILE and CONFIG_FILE.exists():
        config["_CONFIG_SOURCE"] = f"global:{CONFIG_FILE}"
    else:
        config["_CONFIG_SOURCE"] = "env_only"

    return config


def config_exists() -> bool:
    if _find_project_env():
        return True
    if CONFIG_FILE:
        return CONFIG_FILE.exists()
    return False


# ---------------------------------------------------------------------------
# Source-availability shims (upstream contract preserved)
# ---------------------------------------------------------------------------

def get_reddit_source(config: dict[str, Any]) -> str | None:
    """Return Reddit backend identifier.

    For our port, Reddit is always served via direct public JSON
    (free baseline, zero config). Returns "public" so callers know it's wired.
    """
    return "public"


def is_reddit_available(config: dict[str, Any]) -> bool:
    return get_reddit_source(config) is not None


def get_x_source(config: dict[str, Any]) -> str | None:
    """Return X/Twitter backend identifier.

    For our port, X is served via surf when SURF_API_KEY is set.
    Returns "surf" or None.
    """
    return "surf" if config.get("SURF_API_KEY") else None


def get_x_source_with_method(config: dict[str, Any]) -> tuple[str | None, str]:
    return (get_x_source(config), "surf")


def get_youtube_source(config: dict[str, Any]) -> str | None:
    return "surf" if config.get("SURF_API_KEY") else None


def get_github_source(config: dict[str, Any]) -> str | None:
    """GitHub via direct anonymous REST. Always available."""
    return "public"


# ---------------------------------------------------------------------------
# Removed in our port (kept as no-ops if any vendored module still calls them)
# ---------------------------------------------------------------------------

def extract_browser_credentials(config: dict[str, Any]) -> dict[str, str]:
    return {}


# ---------------------------------------------------------------------------
# Source-availability shims — every paid/cookie-based source upstream had is
# now either surf-routed or out-of-scope. These return surf-availability so
# pipeline.py's availability checks light up the right sources.
# ---------------------------------------------------------------------------

def _surf_available(config: dict[str, Any]) -> bool:
    return bool(config.get("SURF_API_KEY"))


def is_youtube_sc_available(config: dict[str, Any]) -> bool:
    return _surf_available(config)


def is_bluesky_available(config: dict[str, Any]) -> bool:
    return _surf_available(config)


def is_threads_available(config: dict[str, Any]) -> bool:
    return _surf_available(config)


def is_pinterest_available(config: dict[str, Any]) -> bool:
    return _surf_available(config)


def is_truthsocial_available(config: dict[str, Any]) -> bool:
    return False  # out of scope: surf has no Truth Social path


def is_xiaohongshu_available(config: dict[str, Any]) -> bool:
    return False  # out of scope: surf has no Xiaohongshu path


def is_xquik_available(config: dict[str, Any]) -> bool:
    return False  # x-cluster collapsed to single surf twitter primitive


def is_tiktok_comments_available(config: dict[str, Any]) -> bool:
    # We don't enrich TikTok comments in v0.1.0 (would require additional
    # web/crawl calls per video). Surface false for now.
    return False


def is_youtube_comments_available(config: dict[str, Any]) -> bool:
    return False  # see is_tiktok_comments_available


def get_tiktok_token(config: dict[str, Any]) -> str | None:
    return None


def get_instagram_token(config: dict[str, Any]) -> str | None:
    return None


def get_pinterest_token(config: dict[str, Any]) -> str | None:
    return None


def get_xquik_token(config: dict[str, Any]) -> str | None:
    return None


def get_x_source_status(config: dict[str, Any]) -> dict[str, Any]:
    """Compat shim — diagnose() reads this. We collapse to a single surf-based
    status because the four upstream X backends are gone."""
    return {
        "source": "surf" if _surf_available(config) else None,
        "bird_installed": False,
        "bird_authenticated": False,
        "bird_username": None,
    }


def load_codex_auth(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return {}


def get_codex_access_token() -> tuple[str | None, str]:
    return None, AUTH_STATUS_MISSING


def get_openai_auth(file_env: dict[str, str]):
    """Compat shim. Upstream returned an OpenAIAuth dataclass; we return a
    minimal duck-typed namespace because surf replaces OpenAI entirely."""
    class _Auth:
        token: str | None = None
        source: AuthSource = AUTH_SOURCE_NONE
        status: AuthStatus = AUTH_STATUS_MISSING
        account_id: str | None = None
        codex_auth_file: str = ""
    return _Auth()
