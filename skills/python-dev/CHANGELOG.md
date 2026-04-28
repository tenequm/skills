# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-04-28

### Added
- `metadata.upstream` field tracking uv, ty, ruff, ruff-pre-commit, pytest, pytest-asyncio, pre-commit, pre-commit-hooks at concrete pinned versions.
- CHANGELOG.md (this file) seeded as the canonical "last verified" signal.
- "Note on ty" beta caveat in SKILL.md so users know to swap in pyright for type-heavy stacks.
- "CI (GitHub Actions)" section in SKILL.md mirroring `just check` + `just test`, using `astral-sh/setup-uv@v6` with caching.
- SKILL.md `[project.scripts]` template now annotated with the call path; Daily Workflow gains two `uv sync` lines clarifying default vs `--all-groups`.
- references/uv-reference.md: new "CLI Entry Points (`[project.scripts]`)" section covering build-system requirement, `module:callable` semantics, and editable-install behavior.
- references/uv-reference.md: "What `uv sync` installs" sub-table under Syncing Environment with a `default-groups` example.
- references/uv-reference.md: PEP 735 / extras trade-off note.
- references/ty-reference.md: `--fix` CLI flag (ty 0.0.31+).
- references/uv-reference.md: `uv lock --upgrade-group <name>` (uv 0.11.4+).

### Changed
- Pinned dev-group versions in SKILL.md template: ruff `>=0.15.0`, ty `>=0.0.30`, pytest `>=9.0.0`, pytest-asyncio `>=1.3.0`, pre-commit `>=4.0.0`.
- Pre-commit hooks: `pre-commit-hooks` rev v5.0.0 -> v6.0.0; `ruff-pre-commit` rev v0.8.4 -> v0.15.12.
- Stack table now lists "uv 0.11+" and labels ty as "(beta)".
- references/uv-reference.md: header bumped to 0.11.x with migration heads-up (`uv venv --clear` requirement, `--native-tls` deprecation, GHSA-pjjw-68hj-v9mw fix).
- references/pytest-reference.md: heads-up summarising 8 -> 9 changes (native `[tool.pytest]` TOML, dropped 3.9, stricter mode, CVE-2025-71176 fix).
- references/ruff-reference.md: heads-up summarising 0.14 (default target py3.14) and 0.15 (2026 style guide, block suppression comments).
- references/pytest-reference.md: pytest-asyncio note expanded to call out 1.3 dropping Python 3.9 and adding pytest 9 compatibility.

Verified against: uv@0.11.8, ty@0.0.33, ruff@0.15.12, ruff-pre-commit@0.15.12, pytest@9.0.3, pytest-asyncio@1.3.0, pre-commit@4.6.0, pre-commit-hooks@6.0.0

## [0.1.2] - 2026-04-09
- Initial CHANGELOG; tracking established.
