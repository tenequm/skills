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

# `readme` runs first so the pre-commit hooks in `lint-repo` verify a synced
# README instead of failing on drift this recipe is about to fix.
#
# `lint-repo` IS pre-commit, and .pre-commit-config.yaml mirrors every other check
# (lint-skills, lint-python, format-python, typecheck-python, readme-sync). Listing
# those recipes here too just ran them twice - check_skills.py alone costs ~49s a
# pass. The private recipes stay for targeted loops (`just check-skills`); only the
# duplicate dependencies are gone. The three steps below are strictly ordered, so
# there is nothing for just's `[parallel]` attribute to overlap.
check: sync readme lint-repo

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

release-latest-bundles:
    uv run python scripts/publish_release.py latest-bundles
