# Skills Repository

Public skills repo. Owner: @opwizardx

## Structure

```
skills/<name>/
├── SKILL.md          # Frontmatter (name, description, metadata.version) + body
├── references/       # On-demand detailed docs
└── LICENSE.txt       # Apache-2.0 (required by ClawHub; copy from any existing skill)

scripts/
├── generate_readme.py         # README table + ClawHub slug overrides
├── prepare_skill_release.py   # Build release manifest from git diff
├── publish_release.py         # Publish to ClawHub + GitHub Releases
└── check_skills.py            # Repo policy linter

Justfile                       # Task runner (just check, just readme, etc.)
.github/workflows/release.yml  # CI: auto-publish on push to main
```

## Adding a Skill

1. Create `skills/<name>/SKILL.md` with frontmatter:
   ```yaml
   ---
   name: skill-name
   description: What it does and when to use it. Include trigger phrases.
   metadata:
     version: "0.1.0"
   ---
   ```
2. Add optional `references/` for detailed docs
3. Commit with conventional commits (`feat`, `fix`, `chore`, etc.)

## ClawHub catalog metadata (required)

`metadata.categories` and `metadata.topics` are flat comma-separated strings. They are
repo-local fields: ClawHub never reads frontmatter for them, so the release pipeline
translates them into `clawhub skill publish --categories/--topics`.

```yaml
metadata:
  version: "0.1.3"
  categories: "agents, productivity"
  topics: "context, handoff, compaction"
```

- `categories` is required. A skill first published without it is stored as `other`
  permanently until someone re-publishes or edits it on ClawHub.
- Max 3 categories from: `integrations, automation, research, development, productivity,
  communication, creative, knowledge, agents, operations, security, finance, lifestyle, other`.
  `other` cannot be combined with a specific category.
- Max 5 topics, each <= 48 chars, lowercase and hyphen-separated. ClawHub rejects 16
  reserved names (`official`, `verified`, `featured`, `trusted`, ...); `check_skills.py`
  rejects them first.
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

- Optional. Skills with no upstream tool (e.g., `polish`, `impactful-writing`) omit it.
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

Use `/update-skill <skill-name>` (at `.claude/skills/update-skill/`) to maintain both fields. It runs research, gates approvals, applies edits, bumps version, updates CHANGELOG, runs `just check`, and commits + pushes on confirmation.

## Rules

- Single-file SKILL.md by default; split to references/ only when content is conditionally loaded (big chunks needed by only some invocations). Skills that must travel as one file stay single-file - condense, don't split
- All code examples must work - no pseudocode
- Size: 25k chars recommended, 50k chars hard ceiling (`wc -c`; CI-enforced via check_skills.py; line counts are not a metric). Condense carefully - never drop load-bearing content to hit a number
- **ALWAYS** bump `metadata.version` in frontmatter when any file in a skill is modified (SKILL.md or references/). Use semver: patch for fixes, minor for new content, major for breaking changes
- No unnecessary files (no README.md, package.json, project.json per skill)
- Use conventional commits

## Quality

- Proper frontmatter with triggers in description
- Quick start with working examples
- Links to official docs
- No deprecated APIs, no filler content

## Release Process

### Automated (CI)
On push to `main`, `.github/workflows/release.yml`:
1. Runs `just check` (lint, typecheck, skill validation, ClawHub publish preflight, README sync)
2. Diffs changed skills, builds manifest + zip bundles
3. Publishes changed skills to ClawHub via `clawhub` CLI
4. Creates a GitHub Release tagged `skills-<short-sha>` (first 7 chars; verify with `gh release view skills-$(git rev-parse --short HEAD)`) with bundles and notes

### Manual publishing
```bash
clawhub --no-input skill publish skills/<folder> \
  --slug <clawhub-slug> --name "Display Name" \
  --version <version> --changelog "..." --tags latest \
  --categories "<slugs>" --topics "<topics>" \
  --source-repo tenequm/skills --source-commit <sha> --source-path skills/<folder>
```

### Slugs, URLs, licensing
- Slugs are scoped per publisher, not globally unique: two owners can hold the same slug,
  and the bare form then resolves ambiguously (`AMBIGUOUS_SKILL_SLUG`). Always link and
  install owner-scoped: page `https://clawhub.ai/tenequm/skills/<slug>`, install
  `@tenequm/<slug>`. There is no unscoped skill URL - `/skills/<slug>` is parsed as
  owner `skills` and renders not-found.
- ClawHub licenses every published skill `MIT-0` registry-wide; no per-skill override.
  The Apache-2.0 `LICENSE.txt` still ships in the bundle for the source repo.
- `clawhub skill rename <slug> <new-slug>` keeps the old slug as a redirect.

### ClawHub slug overrides
Some folder names collide with existing ClawHub slugs. Overrides live in `CLAWHUB_SLUG_OVERRIDES` in `scripts/generate_readme.py` and are applied automatically by the release pipeline. When publishing manually, use the correct `--slug` value from that dict.

### Key commands
```bash
just check                          # Full validation gate (lint + agentskills validate + ClawHub dry-run preflight)
just readme                         # Regenerate README skills table
just release-prepare <before> <after>  # Build release manifest
just release-publish                # Publish manifest to ClawHub + latest bundles
```

### Rate limit
ClawHub allows max 200 **new** skills per 24 hours. Updates to existing skills are not rate-limited.
