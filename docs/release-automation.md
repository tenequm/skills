# Release Automation

This repo publishes skill releases from pushes to `main` using [.github/workflows/release.yml](../.github/workflows/release.yml).

## What happens on each push

1. `pre-commit` runs across the repo.
2. `scripts/prepare_skill_release.py` diffs `github.event.before` against `github.sha`.
3. Changed `skills/<slug>/` folders are detected.
4. Each changed skill must have a new version in `SKILL.md`.
5. A zip bundle is produced for every changed skill.
6. `scripts/publish_release.py clawhub ...` publishes those changed skills to ClawHub.
7. GitHub Release notes are generated from the per-skill diff and attached with the bundles.

## Versioning rule

If a file inside `skills/<slug>/` changes, bump that skill's version before merging to `main`.

The repository policy requires `metadata.version`.

## Required secret

Add this GitHub Actions secret in the repository settings:

- `CLAWHUB_TOKEN`: API token for `clawhub login --token ...`

The workflow uses the documented non-interactive ClawHub CLI flow:

```bash
clawhub login --token "$CLAWHUB_TOKEN" --no-browser
clawhub --no-input publish ./my-skill --slug my-skill --name "My Skill" --version 1.0.0 --changelog "..." --tags latest
```

## Generated assets

Each release includes:

- `dist/releases/release-notes.md`
- `dist/releases/manifest.json`
- `dist/releases/bundles/<skill>-<version>.zip`

The zip bundles are portable skill folders for manual installation or external installers.

## Stable latest bundle links

`README.md` links to a separate rolling GitHub release tag: `skills-latest`.

That release is rebuilt from the current repository state on every push that changes at least one skill. It contains:

- one stable asset per skill: `<slug>.zip`
- `catalog.json`
- `notes.md`

This is separate from the per-push immutable release because immutable releases only include changed skills, which is not enough for a README table of "latest bundle" links across the whole repository.

Regenerate the README table locally with:

```bash
just readme
```

CI verifies that the generated section is in sync.

## Main Commands

The intended human-facing interface is:

```bash
just check
just readme
just release-prepare <before> <after>
just release-publish
```

## Claude Desktop note

Do not treat these zip bundles as native Claude Desktop extensions.

Claude Desktop installs `.mcpb` desktop extensions for MCP servers, not raw skill directories. If you want one-click Claude Desktop installs, that is a separate product surface: build an MCP server, add `manifest.json`, then package it with `mcpb pack`.
