# Skills Repository

Public skills repo. Owner: @opwizardx

## Structure

```
skills/<name>/
├── SKILL.md          # Frontmatter (name, description, metadata.version) + body
└── references/       # On-demand detailed docs
```

Discovery: `.claude-plugin/marketplace.json` and `skills/` directory.

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
3. Add entry to `.claude-plugin/marketplace.json`
4. Commit with conventional commits (`feat`, `fix`, `chore`, etc.)

## Rules

- Use progressive disclosure (SKILL.md + references/)
- All code examples must work - no pseudocode
- Keep SKILL.md under 500 lines, split to references/ when needed
- Bump `metadata.version` in frontmatter when releasing changes
- Update marketplace.json version to match
- No unnecessary files (no README.md, package.json, project.json per skill)
- Use conventional commits

## Quality

- Proper frontmatter with triggers in description
- Quick start with working examples
- Links to official docs
- No deprecated APIs, no filler content
