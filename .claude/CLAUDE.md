# Skills Repository Instructions

Public repository of production-ready Claude Code skills. Owner: @opwizardx

## Repository Structure

```
├── nx.json                      # Nx config (releases, caching)
├── .claude/
│   ├── CLAUDE.md               # This file
│   ├── commands/release.md     # /release command
│   ├── docs/                   # Detailed guides
│   └── skills/skill-creator/   # Skill creation tools
├── .claude-plugin/marketplace.json  # Plugin registry (auto-synced)
├── scripts/sync-marketplace.sh      # Version sync script
└── [plugin-name]/              # Each plugin at root level
    ├── package.json            # Version, name ending in -skill
    ├── project.json            # Nx project config
    ├── CHANGELOG.md            # Auto-generated
    ├── SKILL.md                # Main skill (200-500 lines)
    └── references/             # Detailed docs (on-demand)
```

## Current Plugins

| Plugin | Version | Description |
|--------|---------|-------------|
| chrome-extension-wxt | 1.1.0 | Chrome extensions with WXT |
| cloudflare-workers | 3.0.0 | Cloudflare Workers development |
| erc-8004 | 0.1.0 | ERC-8004 Trustless Agents |
| founder-playbook | 0.1.1 | Decision frameworks for founders |
| foundry-solidity | 0.1.0 | Solidity with Foundry toolkit |
| frontend-dev | 0.0.0 | React/TS, Tailwind/shadcn, TanStack, Vite, Biome |
| gh-cli | 1.1.0 | GitHub CLI for remote repos |
| impactful-writing | 0.1.0 | High-impact writing across platforms |
| python-dev | 0.1.0 | Python with uv, ty, ruff, pytest |
| skill-factory | 0.2.0 | Autonomous skill creation |
| skill-finder | 1.1.0 | Find and evaluate skills |
| solana | 0.6.0 | Solana dev, security auditing, ZK compression |
| uv-ruff-python-tools | 0.1.0 | Python with uv and ruff |
| web3-protocol-gtm | 0.2.0 | Web3 GTM strategy |
| x402 | 0.1.0 | x402 payment protocol |

## Quick Reference

### Create New Plugin

```bash
python3 .claude/skills/skill-creator/scripts/init_skill.py [name] --path .

# package.json: version "0.0.0", name "[name]-skill"
# Add to pnpm-workspace.yaml and marketplace.json
```

### Validate

```bash
pnpm validate                    # All plugins
cd [plugin] && pnpm validate     # Single plugin
```

### Release

```bash
/release                         # Interactive release (human)
pnpm nx release --dry-run        # Preview changes
```

**Non-interactive (for Claude Code / CI):**
```bash
# MUST use version specifier AND pipe 'N' to skip publish prompt
echo "N" | pnpm nx release patch --projects=name
echo "N" | pnpm nx release minor --projects=name

# After release, sync marketplace manually (hook may not run):
bash scripts/sync-marketplace.sh
git add .claude-plugin/marketplace.json
git commit -m "chore: sync marketplace after name@version release"
git push
```

## Critical Rules

### DO
- Validate before committing (must be 10/10)
- Use progressive disclosure (SKILL.md + references/)
- Include working code examples
- Link to official documentation
- Use conventional commits for changelogs
- Start new plugins at version 0.0.0

### DON'T
- Create unnecessary files or documentation
- Include deprecated APIs or patterns
- Use pseudocode (all examples must work)
- Manually edit versions in package.json
- Commit CHANGELOG.md with new plugins
- Add fluff or filler content

### Plugin Requirements

1. **Structure**: `[name]/package.json` + `[name]/SKILL.md`
2. **Workspace**: Listed in `pnpm-workspace.yaml`
3. **Marketplace**: Entry in `.claude-plugin/marketplace.json`
4. **Nx Project**: `project.json` with validate target

### Version Management

- All versions via `pnpm nx release`
- Conventional commits generate changelogs
- marketplace.json auto-synced during release
- Tags: `plugin-name@version`

## Quality Standards

### SKILL.md Requirements
- Proper frontmatter (name, description with triggers)
- "When to Use" section
- Quick start workflow
- Code examples that work
- Links to official docs

### Validation Score
- **10/10**: Required for commit
- **<10**: Fix issues before proceeding

## Detailed Documentation

For comprehensive workflows, see `.claude/docs/skill-creation-guide.md`:
- Full skill creation workflow
- Script documentation
- Research approach
- Git commit standards
- Communication templates
