---
name: skills-best-practices
description: Build high-quality Agent Skills for Claude following official Anthropic best practices. Covers SKILL.md structure, frontmatter, description writing, progressive disclosure, testing, patterns, troubleshooting, and distribution across all surfaces (Claude.ai, Claude Code, API, Agent SDK). Use when creating new skills, reviewing skill quality, debugging skill triggering, structuring skill directories, writing skill descriptions, or improving existing skills. Triggers on "build a skill", "create a skill", "skill structure", "SKILL.md", "skill best practices", "skill not triggering", "skill quality".
metadata:
  version: "0.3.0"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/skills-best-practices
    emoji: "📐"
---

# Skills Best Practices

Comprehensive reference for building Agent Skills that follow Anthropic's official guidelines. Skills are folders containing instructions, scripts, and resources that teach Claude how to handle specific tasks. They follow the [Agent Skills open standard](https://agentskills.io).

## Quick Start

A minimal skill is a directory with a `SKILL.md` file:

```
my-skill/
├── SKILL.md          # Required - instructions with YAML frontmatter
├── references/       # Optional - detailed docs loaded on demand
├── scripts/          # Optional - executable code
└── assets/           # Optional - templates, fonts, icons
```

Minimal `SKILL.md`:

```yaml
---
name: my-skill-name
description: What it does. Use when [specific triggers].
---

# My Skill Name

[Instructions here]
```

Only `name` and `description` are required in frontmatter.

## Core Design Principles

### Progressive Disclosure (Most Important)

Skills load information in three levels to minimize token usage:

| Level | When Loaded | Token Cost | Content |
|-------|------------|------------|---------|
| **1: Metadata** | Always (startup) | ~100 tokens | `name` + `description` from frontmatter |
| **2: Instructions** | When skill triggers | <5k tokens | SKILL.md body |
| **3: Resources** | As needed | Effectively unlimited | Bundled files, scripts |

Keep SKILL.md under **500 lines**. Move detailed docs to separate files and reference them:

```markdown
## Advanced features
- **Form filling**: See [FORMS.md](FORMS.md)
- **API reference**: See [reference.md](reference.md)
```

Claude reads referenced files only when the task requires them.

### Composability

Skills work alongside other skills. Don't assume yours is the only one loaded.

### Portability

Skills work across Claude.ai, Claude Code, API, and Agent SDK without modification (if dependencies are available).

## Writing the Description (Critical)

The description is the **single most important field** - it determines when your skill activates. Claude uses it to decide relevance from potentially 100+ available skills.

### Rules

- Write in **third person** ("Processes files..." not "I help you process files...")
- Include **WHAT** it does + **WHEN** to use it
- Max 1024 characters, no XML angle brackets
- Be slightly "pushy" - Claude tends to **undertrigger** rather than overtrigger
- Include specific trigger phrases users would naturally say

### Good vs Bad

```yaml
# GOOD - specific, actionable, includes triggers
description: Extract text and tables from PDF files, fill forms, merge
  documents. Use when working with PDF files or when the user mentions
  PDFs, forms, or document extraction.

# BAD - too vague
description: Helps with documents.

# BAD - missing triggers
description: Creates sophisticated multi-page documentation systems.
```

More examples in [references/description-guide.md](references/description-guide.md).

## Frontmatter Reference

### Required Fields

| Field | Rules |
|-------|-------|
| `name` | Kebab-case, max 64 chars, lowercase + numbers + hyphens only. No "claude" or "anthropic" |
| `description` | Non-empty, max 1024 chars, no XML tags. WHAT + WHEN |

### Optional Fields (Claude Code)

| Field | Purpose |
|-------|---------|
| `argument-hint` | Autocomplete hint, e.g. `[issue-number]` |
| `disable-model-invocation` | `true` = only user can invoke (for deploy, commit) |
| `user-invocable` | `false` = hidden from `/` menu (background knowledge) |
| `allowed-tools` | Tools allowed without permission, e.g. `Read, Grep, Glob` |
| `model` | Override model for this skill |
| `effort` | Override effort level: `low`, `medium`, `high`, `max` |
| `context` | `fork` = run in isolated subagent |
| `agent` | Subagent type when `context: fork` (e.g. `Explore`, `Plan`) |
| `paths` | Glob patterns limiting when skill activates |

### Naming Conventions

Prefer **gerund form** for clarity:

- `processing-pdfs`, `analyzing-spreadsheets`, `managing-databases`
- Also acceptable: `pdf-processing`, `process-pdfs`
- Avoid: `helper`, `utils`, `tools`, `documents`

## Structuring Instructions

### Be Concise

Claude is smart. Only add context it doesn't already have:

```markdown
# GOOD (~50 tokens)
## Extract PDF text
Use pdfplumber for text extraction:
```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

# BAD (~150 tokens)
## Extract PDF text
PDF files are a common file format containing text and images.
To extract text, you need a library. There are many available...
```

### Set Degrees of Freedom

- **High freedom** (text guidelines): Multiple approaches valid, context-dependent
- **Medium freedom** (pseudocode/templates): Preferred pattern exists, some variation OK
- **Low freedom** (exact scripts): Operations are fragile, consistency critical

### Recommended SKILL.md Structure

```markdown
# Skill Name

## Quick start
[Minimal working example]

## Workflow Decision Tree
[Route to the right approach based on task type]

## Detailed Instructions
[Step-by-step for each workflow]

## Examples
[Concrete input/output pairs]

## Troubleshooting
[Common errors and fixes]
```

### Reference Files

Keep references **one level deep** from SKILL.md. Avoid nested chains:

```markdown
# BAD: Too deep
SKILL.md -> advanced.md -> details.md -> actual info

# GOOD: One level
SKILL.md -> advanced.md (contains the info directly)
SKILL.md -> reference.md (contains the info directly)
```

For reference files >100 lines, include a **table of contents** at the top.

## Patterns

### Sequential Workflow

```markdown
## Step 1: Analyze input
Run: `python scripts/analyze.py input.pdf`

## Step 2: Validate
Run: `python scripts/validate.py fields.json`
Fix any errors before continuing.

## Step 3: Execute
Run: `python scripts/process.py input.pdf fields.json output.pdf`
```

### Conditional Workflow (Decision Tree)

```markdown
## Workflow Decision Tree
**Creating new content?** -> Follow "Creation workflow"
**Editing existing content?** -> Follow "Editing workflow"
**Reviewing content?** -> Follow "Review workflow"
```

### Feedback Loop

```markdown
1. Make edits
2. Validate: `python scripts/validate.py`
3. If validation fails -> fix issues -> go to step 2
4. Only proceed when validation passes
```

### Checklist Pattern (for complex tasks)

```markdown
Copy this checklist and track progress:
- [ ] Step 1: Analyze input
- [ ] Step 2: Create plan
- [ ] Step 3: Validate plan
- [ ] Step 4: Execute
- [ ] Step 5: Verify output
```

More patterns in [references/patterns.md](references/patterns.md).

## Scripts

When your skill includes executable code:

- **Solve, don't punt**: Handle errors explicitly instead of letting them fail
- **Justify constants**: No magic numbers - document why each value was chosen
- **Prefer execution over loading**: Scripts run without entering context; only output consumes tokens
- **Clarify intent**: "Run `analyze.py`" (execute) vs "See `analyze.py`" (read as reference)
- **List dependencies** in SKILL.md and verify availability

## Testing

### Triggering Tests

```
Should trigger:
- "Help me set up a new project in [Service]"
- "I need to create a project" (paraphrased)

Should NOT trigger:
- "What's the weather?" (unrelated)
- "Write Python code" (too generic)
```

### Functional Tests

Test normal operations, edge cases, and out-of-scope requests. Run the same request 3-5 times to check consistency.

### Debug Triggering

Ask Claude: "When would you use the [skill-name] skill?" - it quotes the description back. Adjust based on what's missing.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Skill never loads | Description too vague | Add specific triggers and key terms |
| Skill loads for wrong tasks | Description too broad | Add negative triggers, be more specific |
| Instructions not followed | Too verbose or buried | Put critical instructions at top, use headers |
| Slow/degraded responses | SKILL.md too large | Move content to references/, keep under 500 lines |
| "Could not find SKILL.md" | Wrong filename | Must be exactly `SKILL.md` (case-sensitive) |
| "Invalid skill name" | Spaces or capitals | Use kebab-case: `my-skill-name` |

## Distribution

| Surface | How to Deploy |
|---------|--------------|
| Claude.ai | Settings > Features > Upload zip |
| Claude Code (personal) | `~/.claude/skills/<name>/SKILL.md` |
| Claude Code (project) | `.claude/skills/<name>/SKILL.md` |
| Claude Code (plugin) | `<plugin>/skills/<name>/SKILL.md` |
| API | POST `/v1/skills` with beta headers |
| Enterprise | Managed settings (org-wide) |

Skills don't sync across surfaces - deploy separately to each.

## Security

- Only use skills from **trusted sources**
- No XML angle brackets in frontmatter (injection risk)
- Audit all bundled scripts and resources before using third-party skills
- Be cautious of skills that fetch from external URLs

## Additional References

- [Description writing guide](references/description-guide.md) - detailed examples and anti-patterns
- [Patterns and workflows](references/patterns.md) - advanced patterns with MCP, subagents, iterative refinement
- [Claude Code features](references/claude-code-features.md) - context:fork, dynamic injection, argument substitution
- [Quality checklist](references/checklist.md) - pre-upload validation checklist
- [ClawHub publishing](references/clawhub-publishing.md) - `metadata.openclaw` schema, moderation pipeline, reason codes catalog, pre-publish checklist

## Official Resources

- [Agent Skills Spec](https://agentskills.io/specification)
- [Claude Code Skills Docs](https://code.claude.com/docs/en/skills)
- [API Skills Guide](https://platform.claude.com/docs/en/build-with-claude/skills-guide)
- [Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Anthropic Skills Repo](https://github.com/anthropics/skills)
- [Engineering Blog: Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills)
- [Complete Guide PDF](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf)
