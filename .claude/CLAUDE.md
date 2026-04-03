# Skills Repository

Public skills repo. Owner: @opwizardx

## Structure

```
skills/<name>/
├── SKILL.md          # Frontmatter (name, description, metadata.version) + body
├── references/       # On-demand detailed docs
└── LICENSE.txt       # MIT-0 (auto-added, required by ClawHub)

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

## Rules

- Use progressive disclosure (SKILL.md + references/)
- All code examples must work - no pseudocode
- Keep SKILL.md under 500 lines, split to references/ when needed
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
1. Runs `just check` (lint, typecheck, skill validation, README sync)
2. Diffs changed skills, builds manifest + zip bundles
3. Publishes changed skills to ClawHub via `clawhub` CLI
4. Creates a GitHub Release with bundles and notes

### Manual publishing
```bash
clawhub --no-input publish skills/<folder> \
  --slug <clawhub-slug> --name "Display Name" \
  --version <version> --changelog "..." --tags latest
```

### ClawHub slug overrides
Some folder names collide with existing ClawHub slugs. Overrides live in `CLAWHUB_SLUG_OVERRIDES` in `scripts/generate_readme.py` and are applied automatically by the release pipeline. When publishing manually, use the correct `--slug` value from that dict.

### Key commands
```bash
just check                          # Full validation gate
just readme                         # Regenerate README skills table
just release-prepare <before> <after>  # Build release manifest
just release-publish                # Publish manifest to ClawHub + latest bundles
```

### Rate limit
ClawHub allows max 5 **new** skills per hour. Updates to existing skills are not rate-limited.
