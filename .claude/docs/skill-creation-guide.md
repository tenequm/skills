# Skill Creation Guide

Detailed workflows for creating and maintaining skills in this repository.

## Creating a New Skill

### 1. Research Phase

Before creating any skill:
- Search for latest best practices and current trends
- Review official documentation
- Verify information is current (check dates, versions)
- Note framework/tool versions

### 2. Initialize Plugin

```bash
# Initialize skill structure (creates [plugin-name]/ with SKILL.md, references/, etc.)
python3 .claude/skills/skill-creator/scripts/init_skill.py [plugin-name] --path .

# Create package.json (start at 0.0.0)
cat > [plugin-name]/package.json <<EOF
{
  "name": "[plugin-name]-skill",
  "version": "0.0.0",
  "private": true,
  "description": "Your description",
  "scripts": {
    "validate": "python3 ../.claude/skills/skill-creator/scripts/quick_validate.py ."
  }
}
EOF

# Create project.json for Nx
cat > [plugin-name]/project.json <<EOF
{
  "name": "[plugin-name]",
  "\$schema": "../node_modules/nx/schemas/project-schema.json",
  "sourceRoot": "[plugin-name]",
  "projectType": "library",
  "targets": {
    "validate": {
      "executor": "nx:run-commands",
      "options": {
        "command": "pnpm validate",
        "cwd": "[plugin-name]"
      },
      "cache": true,
      "inputs": [
        "{projectRoot}/SKILL.md",
        "{projectRoot}/references/**/*.md",
        "{projectRoot}/package.json"
      ]
    }
  },
  "release": {
    "version": {
      "generator": "@nx/js:release-version"
    }
  }
}
EOF

# Add to pnpm workspace
echo "  - '[plugin-name]'" >> pnpm-workspace.yaml

# Add to marketplace.json
# Edit .claude-plugin/marketplace.json
```

### 3. Create Content

**SKILL.md structure:**
```markdown
---
name: skill-name
description: Clear description with trigger keywords. Use when [scenarios].
---

# Skill Title

Brief overview.

## When to Use This Skill
- Scenario 1
- Scenario 2

## Quick Start Workflow
1. Step 1
2. Step 2

## Core Concepts
### Concept 1
Brief explanation with code example.

## Advanced Topics
For details, see `references/topic.md`

## Resources
- Official Docs: [link]
```

**Progressive disclosure:**
- `[plugin]/SKILL.md`: 200-500 lines (overview, quick start)
- `[plugin]/references/*.md`: Detailed guides loaded on-demand

### 4. Validate

```bash
cd [plugin-name]
pnpm validate
# Must score 10.0/10
```

### 5. Commit

Use conventional commits for changelog generation:
```bash
git add [plugin-name]/ pnpm-workspace.yaml README.md .claude-plugin/marketplace.json
git commit -m "feat([plugin-name]): add [plugin-name] plugin"
```

### 6. Release

```bash
/release
# Or: pnpm nx release --projects=[plugin-name]
# Select "minor" for first release → 0.1.0
```

## skill-creator Scripts

### init_skill.py
Creates initial skill structure with proper directories.

```bash
python3 .claude/skills/skill-creator/scripts/init_skill.py \
  skill-name \
  --path ./path \
  --description "Brief description"
```

Creates: `[name]/SKILL.md`, `[name]/references/`, `[name]/scripts/`, `[name]/assets/`

### quick_validate.py
Validates skill against Anthropic best practices.

**Checks:**
- SKILL.md has proper frontmatter
- Description includes trigger keywords
- SKILL.md is concise (<500 lines)
- Uses progressive disclosure
- Contains concrete examples
- No anti-patterns

**Scoring:**
- 10.0/10: Perfect
- 8.0-9.9: Good, minor improvements needed
- <8.0: Does not meet standards

### package_skill.py
Creates .zip package for distribution.

## Version Guidelines

### Semantic Versioning
- **Patch (0.1.x)**: Bug fixes, typos, small improvements
- **Minor (0.x.0)**: New features, sections, significant additions
- **Major (x.0.0)**: Breaking changes, structure changes

### Version Progression
```
0.0.0 (initial)
  ↓ minor
0.1.0 (first release)
  ↓ patch
0.1.1, 0.1.2...
  ↓ minor
0.2.0, 0.3.0...
  ↓ major (when stable)
1.0.0 (production-ready)
```

## Research Approach

### Sources (in order of priority)
1. **Official documentation** - Primary source of truth
2. **Official examples** - Real-world patterns
3. **Community resources** - Current best practices

### Quality Checklist
- [ ] Verified against official docs
- [ ] Confirmed version numbers
- [ ] Tested code examples
- [ ] Checked for deprecated APIs
- [ ] Reviewed recent release notes

## Git Commit Standards

### Format
```
type(scope): brief description

- Detail 1
- Detail 2
```

### Types
- **feat**: New skill
- **fix**: Corrections
- **docs**: Documentation only
- **refactor**: Restructure without content changes
- **chore**: Maintenance

### Examples
```bash
git commit -m "feat(solana): add security audit guide"
git commit -m "fix(gh-cli): correct API endpoint examples"
git commit -m "docs: update README with new plugin"
```

## Communicating with User

### Starting a New Skill
1. Clarify requirements and use cases
2. Explain research plan
3. Show progress during creation
4. Present results with validation score

### Updating Existing Skill
1. Explain what will change
2. Show validation still passes
3. Summarize changes made

## Potential Skills to Create

### Web Development
- react-modern, nextjs-app-router, astro-sites, vite-projects

### Backend
- hono-api, trpc-backend, drizzle-orm, prisma-database

### DevOps
- docker-compose, github-actions, vercel-deploy

### Testing
- vitest-testing, playwright-e2e, msw-mocking

### AI/ML
- openai-integration, langchain-apps, huggingface-models
