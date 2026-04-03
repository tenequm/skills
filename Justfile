set shell := ["bash", "-euo", "pipefail", "-c"]
export UV_CACHE_DIR := env_var_or_default("UV_CACHE_DIR", "/tmp/uv-cache")
export UV_TOOL_DIR := env_var_or_default("UV_TOOL_DIR", "/tmp/uv-tools")

[private]
sync:
    uv sync --all-extras

[private]
lint-repo:
    uvx pre-commit run --all-files

[private]
lint-python:
    uv run ruff check scripts
    uv run ruff format --check scripts

[private]
typecheck-python:
    uv run ty check scripts

[private]
check-skills:
    uv run python scripts/check_skills.py

readme:
    uv run python scripts/generate_readme.py

[private]
readme-check:
    uv run python scripts/generate_readme.py --check

check: sync lint-repo lint-python typecheck-python check-skills readme

release-prepare before after github_output='':
    if [[ -n "{{github_output}}" ]]; then extra_args=(--github-output "{{github_output}}"); else extra_args=(); fi; \
    if [[ "{{before}}" == "ALL" || "{{before}}" == "all" ]]; then \
      uv run python scripts/prepare_skill_release.py \
        --all \
        --after "{{after}}" \
        --dist-dir dist/releases \
        --manifest-path dist/releases/manifest.json \
        --notes-path dist/releases/release-notes.md \
        "${extra_args[@]}"; \
    else \
      uv run python scripts/prepare_skill_release.py \
        --before "{{before}}" \
        --after "{{after}}" \
        --dist-dir dist/releases \
        --manifest-path dist/releases/manifest.json \
        --notes-path dist/releases/release-notes.md \
        "${extra_args[@]}"; \
    fi

release-publish manifest='dist/releases/manifest.json':
    uv run python scripts/publish_release.py clawhub --manifest "{{manifest}}"
    uv run python scripts/publish_release.py latest-bundles
