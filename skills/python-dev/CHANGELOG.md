# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-09-09

### Changed

- **Breaking:** git hooks move from **pre-commit to lefthook**, matching `go-dev`. `lefthook`
  installs from PyPI as a platform wheel (`uv add --dev lefthook`), so the hook runs the
  project's own ruff from `uv.lock` instead of a second copy pinned separately by
  `.pre-commit-config.yaml` `rev:`. Existing projects: see the migration steps in SKILL.md.
- **Breaking:** the `[tool.ruff.lint]` template no longer sets `select`. Ruff 0.16 raised the
  default rule set from 59 to 413 rules, so `select = ["E","F","I","UP"]` now produces a
  *weaker* linter than no config at all. Narrow with `ignore`, widen with `extend-select`.
  `E741` left the ignore list with the `E` group it belonged to.
- `[tool.pytest.ini_options]` uses `strict = true` instead of passing `--strict-markers` /
  `--strict-config` through `addopts`. Verified on both 9.0.3 and 9.1.1.
- CI pins `astral-sh/setup-uv@v10.0.1` and `actions/checkout@v7`, and no longer sets
  `enable-cache: true`.
- `uv init` is documented as packaging by default with the `uv_build` backend (uv 0.12);
  the hatchling block is now labelled as a deliberate override.
- ty's beta caveat no longer blames Pydantic, and points at
  `[tool.ty.analysis] replace-imports-with-any` before recommending a wholesale pyright swap.
- Dev-dependency floors raised to the versions the guidance actually requires: `ruff>=0.16.6`,
  `ty>=0.0.79`, `pytest>=9.1.1`, `pytest-asyncio>=1.4.0`.
- `references/pytest-reference.md` replaces the deprecated `event_loop_policy` uvloop recipe
  with the `pytest_asyncio_loop_factories` hook.
- The non-mutating `check` contract is now consistent: three reference recipes still ran
  `ruff check --fix && ruff format`.

### Added

- `lefthook.yml` template with a parallel `guards` group (`private-key`, `merge-conflict`,
  `large-files`),
  ruff check/format with `stage_fixed`, and `ty` on `pre-commit`; `pytest` on `pre-push`.
- `--force-exclude` on both ruff hook jobs, with the reason: ruff ignores `[tool.ruff] exclude`
  for paths passed explicitly, which is exactly what `{staged_files}` does.
- `[tool.ruff.format] exclude = ["*.md"]`, because ruff 0.16 formats Markdown code fences by
  default and would otherwise fail `just check` on READMEs.
- `uv run lefthook validate` in CI; `uv run lefthook install` in the Justfile `install` recipe
  and the setup and migration steps.
- lefthook added to The Stack table; docs linked in Resources.

### Fixed

- The `ty` hook job carried `glob: "*.{py,pyi}"`, and lefthook applies a glob even to a job
  whose `run` never uses `{staged_files}`. A commit touching only `pyproject.toml` - where
  `[tool.ty]` and the dependency pins live - was recorded with **no type checking at all**.
  The glob is gone.
- `references/ruff-reference.md` prescribed the same `select` list SKILL.md now warns against,
  and its "Extended Rule Sets" block used `select` where it must use `extend-select`.
- `references/ty-reference.md` implied `error-on-warning` defaults to `false`; it has defaulted
  to `true` since 0.0.52. It also recommended `uv tool install ty@latest` while telling readers
  to pin.
- `references/uv-reference.md` CI block drifted from SKILL.md (bare `ruff check`, no
  `lefthook validate`, `actions/checkout@v4`).

Verified against: uv@0.12.11, ty@0.0.79, ruff@0.16.6, pytest@9.1.1, pytest-asyncio@1.4.0, lefthook@2.1.12

## [0.2.5] - 2026-08-21

### Changed

- Declared ClawHub browse categories (`development`) and topics in `metadata`, so the release pipeline publishes them instead of leaving the skill in the `other` category.

### Removed

- `skill-card.md`. The ClawHub CLI strips a root `skill-card.md` from every publish and the registry generates its own card, so the authored file never reached ClawHub.

## [0.2.4] - 2026-08-07

### Changed

- Trimmed the frontmatter description to what-plus-when; dropped the trailing 10-item trigger-keyword list.

### Fixed

- The Justfile `check` recipe ran `ruff check --fix && ruff format`, mutating files and duplicating `fix`. It is now non-mutating (`ruff check`, `ruff format --check`) and mirrors the CI block.
- CI example used `actions/checkout@v4`; bumped to `@v6`.

## [0.2.3] - 2026-07-22

### Added

- skill-card.md release record following NVIDIA's skill-card format
- metadata.openclaw block (emoji, homepage) for ClawHub display

## [0.2.2] - 2026-07-10

### Changed
- CHANGELOG preamble pinned to Keep a Changelog 2.0.0 (format unchanged; KaC 2.0.0 keeps existing changelogs valid).

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
