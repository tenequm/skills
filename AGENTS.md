# Skills Repository

Public skills repo. Owner: @tenequm

## Structure

```
skills/<name>/
├── SKILL.md          # Frontmatter + body
├── references/       # On-demand detailed docs (optional)
└── CHANGELOG.md      # Optional, see below

archive/<name>/       # Retired skills: not published, marked `metadata.internal: true`
Justfile              # All tooling: check, preflight, readme, release
lefthook.yml          # Git hooks: `just check` on commit, `just preflight` on push
.github/workflows/ci.yml       # check + preflight on every PR/push, release on main
.github/betterleaks.toml       # Secret-scan allowlist (placeholder creds in references/)
```

Tools: `just`, `yq` (mikefarah v4), `jq`, `betterleaks`, `lefthook`, `clawhub` (npm), `gh`.
Run `just setup` once per clone: installs the lefthook hooks and links `skills/update-skill` into the gitignored `.claude/skills/` and `.agents/skills/`.

## Adding a Skill

1. Create `skills/<name>/SKILL.md`:
   ```yaml
   ---
   name: skill-name
   description: What it does and when to use it. Include trigger phrases.
   metadata:
     version: "0.1.0"
     categories: "development"
     topics: "example-topic"
     openclaw:
       homepage: https://github.com/tenequm/skills/tree/main/skills/skill-name
       emoji: "🧰"
   ---
   ```
2. Add optional `references/` for detailed docs
3. `just readme`, then `just check` and `just preflight`
4. Commit with conventional commits (`feat`, `fix`, `chore`, etc.)

No per-skill `LICENSE.txt`: ClawHub licenses every published skill MIT-0 and rejects
conflicting terms; the repo itself is MIT (`LICENSE`).

## ClawHub catalog metadata (required)

`metadata.categories` and `metadata.topics` are flat comma-separated strings. They are
repo-local fields: ClawHub never reads frontmatter for them, so `just release` translates
them into `clawhub skill publish --categories/--topics`.

- `categories` is required. A skill first published without it is stored as `other`
  permanently until someone re-publishes or edits it on ClawHub.
- Max 3 categories from: `integrations, automation, research, development, productivity,
  communication, creative, knowledge, agents, operations, security, finance, lifestyle, other`.
  `other` cannot be combined with a specific category.
- Max 5 topics, each <= 48 chars, lowercase and hyphen-separated. ClawHub rejects 16
  reserved names (`official`, `verified`, `featured`, `trusted`, ...); `just check`
  rejects them first.
- `metadata.openclaw` is required with `homepage` (the skill's tree URL) and `emoji`.
- Do not add a `skill-card.md`. The ClawHub CLI strips any root `skill-card.md` before
  upload and the registry generates its own card after the security scan.

## Per-skill upstream tracking (optional)

For skills that wrap a specific tool, package, or library, two conventions track freshness:

### `metadata.upstream` flat string

```yaml
metadata:
  version: "0.3.0"
  upstream: "effect@4.0.0-beta.58, @effect/platform@0.70.0"
```

- Optional. Skills with no upstream tool (e.g., `polish`, `grill-me`) omit it.
- Comma-separated `<name>@<version>` entries. npm scopes (`@scope/pkg`) work because the leading `@` is part of the name.
- Concrete release tags or commit SHAs only. Floating tags (`@latest`, `@next`, `@beta`, `@canary`) are rejected.
- Anthropic's `metadata: dict[str, str]` contract is respected (flat string, not nested object).

### Per-skill `CHANGELOG.md`

Path: `skills/<name>/CHANGELOG.md`. Format: [Keep a Changelog v2.0.0](https://keepachangelog.com/en/2.0.0/).

- Standard sections only (Added / Changed / Deprecated / Removed / Fixed / Security); omit empty ones.
- Version heading: `## [x.y.z] - YYYY-MM-DD`.
- `[Unreleased]` header kept between releases.
- `Verified against:` trailer added only when at least one tracked package version changed in that release.
- The topmost CHANGELOG entry date is the canonical "last verified" signal - no separate frontmatter date field.

### `/update-skill` command

Use `/update-skill <skill-name>` (linked by `just setup`) to maintain both fields. It runs research, gates approvals, applies edits, bumps version, updates CHANGELOG, runs `just check`, and commits + pushes on confirmation.

## Rules

- Single-file SKILL.md by default; split to references/ only when content is conditionally loaded (big chunks needed by only some invocations). Skills that must travel as one file stay single-file - condense, don't split
- All code examples must work - no pseudocode
- Size: 25k recommended, 50k hard ceiling (`wc -c` bytes; enforced by `just check`; line counts are not a metric). Condense carefully - never drop load-bearing content to hit a number
- Descriptions: 250 chars max (enforced)
- **ALWAYS** bump `metadata.version` in frontmatter when any file in a skill is modified (SKILL.md or references/). Use semver: patch for fixes, minor for new content, major for breaking changes. `just release` fails on a changed skill without a bump
- No unnecessary files (no README.md, package.json, project.json per skill)
- Use conventional commits

## Quality

- Proper frontmatter with triggers in description
- Quick start with working examples
- Links to official docs
- No deprecated APIs, no filler content

## Commands

```bash
just check          # Offline: skill policy lint, README drift, whitespace, secrets (~1s)
just preflight      # ClawHub publish dry-run for every skill (network + clawhub login)
just readme         # Regenerate the README skills table
just release-plan   # What would publish since the last skills-* tag
just release        # Publish + GitHub release (CI runs this on main)
```

## Release Process

On push to `main`, `ci.yml` runs `check` and `preflight`, then the `release` job runs
`just release`:
1. Diffs `skills/` against the last `skills-*` tag; every changed skill must have a new `metadata.version`
2. Publishes each changed skill to ClawHub with categories, topics and source provenance
3. Creates GitHub release `skills-<short-sha>` (notes only, no assets), which also creates the tag

A failed publish creates no tag, so the next run retries the same range; versions already
on ClawHub are skipped.

### Slugs, URLs, licensing
- ClawHub slug = folder name. Slugs are scoped per publisher: two owners can hold the same
  slug, and the bare form then resolves ambiguously (`AMBIGUOUS_SKILL_SLUG`). Always link and
  install owner-scoped: page `https://clawhub.ai/tenequm/skills/<slug>`, install
  `@tenequm/<slug>`. There is no unscoped skill URL - `/skills/<slug>` is parsed as
  owner `skills` and renders not-found.
- `clawhub skill rename <slug> <new-slug>` and `clawhub skill merge <src> <dst>` keep the old slug as a redirect.
- Retiring a skill: `git mv skills/<name> archive/`, add `metadata.internal: true`, then
  `clawhub delete @tenequm/<slug> --reason "..."` (soft delete; `undelete` works while the
  slug is reserved, 30 days) or `clawhub skill merge` into its successor.

### Rate limit
ClawHub allows max 200 **new** skills per 24 hours. Updates to existing skills are not rate-limited.
