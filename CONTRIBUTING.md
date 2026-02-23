# Contributing to Claude Plugins

Thank you for your interest in contributing! This guide will help you get started.

## Requirements

- Node.js 24+ LTS
- pnpm 10+
- Python 3.12+ (for validation scripts)
- [uv](https://docs.astral.sh/uv/) (for pre-commit hooks)

## Setup

```bash
# Clone the repository
git clone https://github.com/tenequm/claude-plugins.git
cd claude-plugins

# Install dependencies
pnpm install

# Install pre-commit hooks
uvx pre-commit install
```

## Making Changes to Skills

When you modify a skill, simply commit your changes - Nx Release will handle versioning:

```bash
# 1. Make your changes to a skill
vim gh-cli/SKILL.md

# 2. Validate your changes
cd gh-cli
pnpm validate

# 3. Commit with conventional commits format
cd ..
git add .
git commit -m "feat(gh-cli): add trending repos section"
# or
git commit -m "fix(gh-cli): correct API endpoint URL"

# 4. Push
git push
```

**Conventional Commit Format:**
```
type(scope): description

Examples:
- feat(solana): add production deployment guide
- fix(gh-cli): correct repo search syntax
- docs(cloudflare-workers): update Workers AI examples
```

**Common Types:**
- `feat`: New features (minor version bump)
- `fix`: Bug fixes (patch version bump)
- `docs`: Documentation only changes (patch version bump)
- `refactor`: Code refactoring (patch version bump)
- `BREAKING CHANGE`: Breaking changes (major version bump)

## Releasing

Releases are done manually using Nx Release:

```bash
# Release all changed plugins (interactive)
pnpm nx release

# Release specific plugins
pnpm nx release --projects=solana,gh-cli

# Release with automatic version bump
pnpm nx release minor  # or patch, major

# Preview release without making changes
pnpm nx release --dry-run
```

**What happens during release:**
1. Nx validates all plugins (cached, fast)
2. Prompts for version bump per plugin
3. Updates package.json files
4. Generates CHANGELOG.md from conventional commits
5. Syncs marketplace.json automatically
6. Creates commit and git tags
7. Pushes to GitHub
8. Creates GitHub releases with changelogs

## Versioning Guidelines

Nx Release determines version bumps from conventional commits:

- **Patch** (0.1.x): `fix:`, `docs:`, `refactor:`, `chore:`
- **Minor** (0.x.0): `feat:`
- **Major** (x.0.0): `BREAKING CHANGE:` in commit body or footer

## Validation

```bash
# Validate specific skill
cd gh-cli
pnpm validate

# Validate all skills in workspace
cd ..
pnpm validate

# Nx caches validation - second run is instant!
```

## Creating New Skills

Each skill should follow Anthropic's best practices:

1. Main file: `SKILL.md` (frontmatter + concise overview)
2. References: `references/*.md` (detailed documentation)
3. Optional: `scripts/`, `assets/` directories

See the [official skill-creator](https://github.com/anthropics/skills) for guidelines.

## Development

### Pre-commit Hooks

This repository uses pre-commit to validate skills before committing.

**Setup:**

```bash
# Install pre-commit hooks
uvx pre-commit install

# Run manually on all files
uvx pre-commit run --all-files
```

**What gets validated:**
- Skill structure (SKILL.md format, frontmatter)
- No secrets or API keys
- YAML syntax
- No trailing whitespace

**Note:** Nx caching speeds up pre-commit validation significantly!

### Continuous Integration

GitHub Actions automatically runs these checks on every push and pull request:

- Skill validation (with Nx caching)
- Pre-commit checks
- Automated releases (manual trigger)

### Repository Structure

```
claude-plugins/
├── .nx/                     # Nx cache (gitignored)
├── nx.json                  # Nx configuration for caching and releases
├── .claude-plugin/          # Plugin marketplace configuration
│   └── marketplace.json     # Plugin registry (auto-synced)
├── .github/workflows/       # CI/CD workflows
├── chrome-extension-wxt/    # Chrome extension plugin
│   ├── package.json        # Plugin metadata with version
│   ├── project.json        # Nx project configuration
│   ├── CHANGELOG.md        # Auto-generated changelog
│   ├── SKILL.md            # Main skill file
│   └── references/         # Detailed reference docs
├── gh-cli/                  # GitHub CLI plugin
│   ├── package.json
│   ├── project.json
│   ├── CHANGELOG.md
│   ├── SKILL.md
│   └── references/
└── scripts/                 # Build and release scripts
    └── sync-marketplace.sh  # Syncs versions to marketplace.json
```

## Technology Stack

- **Nx**: Monorepo tooling with caching and release management
- **pnpm**: Fast, disk-efficient package manager
- **Conventional Commits**: Semantic versioning from commit messages
- **pre-commit**: Git hook framework for validation

## Code of Conduct

Please be respectful and constructive in all interactions. We're here to build useful tools together!

## Questions?

Feel free to open an issue or discussion on GitHub.
