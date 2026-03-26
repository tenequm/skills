# Writing Effective Skill Descriptions

The `description` field is the most critical component of your skill. It determines when Claude activates your skill from potentially 100+ available skills. Get this right.

## Structure

A strong description has three parts:

1. **Capabilities** - specific things the skill does (action verbs)
2. **Triggers** - when to activate (user phrases, file types, contexts)
3. **Boundaries** - what it does NOT do (optional but useful)

## Rules

- Write in **third person**: "Processes files..." not "I help you..."
- Max **1024 characters**
- No XML angle brackets (`<` or `>`)
- Include **WHAT** + **WHEN**
- Be slightly "pushy" - Claude tends to undertrigger

## Examples: Good Descriptions

### PDF Processing

```yaml
description: Extract text and tables from PDF files, fill forms, merge
  documents. Use when working with PDF files or when the user mentions
  PDFs, forms, or document extraction.
```

Why it works: specific verbs (extract, fill, merge), concrete triggers (PDF files, forms), clear use cases.

### Excel Analysis

```yaml
description: Analyze Excel spreadsheets, create pivot tables, generate
  charts. Use when analyzing Excel files, spreadsheets, tabular data,
  or .xlsx files.
```

Why it works: mentions specific capabilities and file types that trigger naturally.

### Git Commit Helper

```yaml
description: Generate descriptive commit messages by analyzing git diffs.
  Use when the user asks for help writing commit messages or reviewing
  staged changes.
```

Why it works: specific action (generate commit messages) with natural trigger phrases.

### Linear Sprint Planning

```yaml
description: Manages Linear project workflows including sprint planning,
  task creation, and status tracking. Use when user mentions "sprint",
  "Linear tasks", "project planning", or asks to "create tickets".
```

Why it works: names the specific tool, lists capabilities, includes exact phrases.

### Frontend Design

```yaml
description: Create distinctive, production-grade frontend interfaces
  with high design quality. Use this skill when the user asks to build
  web components, pages, or applications. Generates creative, polished
  code that avoids generic AI aesthetics.
```

Why it works: describes both the capability and the quality standard.

### Brand Guidelines

```yaml
description: Applies Anthropic's official brand colors and typography
  to any sort of artifact that may benefit from having Anthropic's
  look-and-feel. Use it when brand colors or style guidelines, visual
  formatting, or company design standards apply.
```

Why it works: specific about what data it provides, clear about activation context.

## Examples: Bad Descriptions

### Too Vague

```yaml
# BAD
description: Helps with documents.
# Why: no specific capabilities, no triggers, matches everything and nothing
```

### Missing Triggers

```yaml
# BAD
description: Creates sophisticated multi-page documentation systems.
# Why: describes capability but not WHEN to use it
```

### Too Technical

```yaml
# BAD
description: Implements the Project entity model with hierarchical
  relationships.
# Why: no user-facing triggers, overly technical
```

### Wrong Point of View

```yaml
# BAD
description: I can help you process Excel files and create reports.
# Why: first person ("I") causes discovery problems in system prompt

# ALSO BAD
description: You can use this to process Excel files.
# Why: second person ("You") also problematic
```

## Adding Negative Triggers

When your skill overtriggers (loads for irrelevant queries), add boundaries:

```yaml
description: Advanced data analysis for CSV files. Use for statistical
  modeling, regression, clustering. Do NOT use for simple data
  exploration (use data-viz skill instead).
```

```yaml
description: PayFlow payment processing for e-commerce. Use specifically
  for online payment workflows, not for general financial queries.
```

## Description for MCP-Enhanced Skills

When your skill works with an MCP server, mention both the tool and the workflow:

```yaml
description: Manages Linear project workflows including sprint planning,
  task creation, and status tracking via MCP. Use when user mentions
  "sprint", "Linear tasks", or asks to "create tickets". Requires
  Linear MCP server to be connected.
```

## Debugging Descriptions

Ask Claude: "When would you use the [skill-name] skill?"

Claude will quote the description back. Check:
- Does it mention the capabilities you expect?
- Does it include the trigger phrases users would actually say?
- Does it mention relevant file types?
- Is it specific enough to distinguish from similar skills?

Adjust based on what's missing. Iterate until Claude correctly identifies when to use your skill.

## Undertriggering vs Overtriggering

| Signal | Problem | Fix |
|--------|---------|-----|
| Skill doesn't load when it should | Undertriggering | Add more use cases, trigger phrases, file types |
| Users manually enabling it | Undertriggering | Broaden description, add synonyms |
| Skill loads for unrelated queries | Overtriggering | Add negative triggers, be more specific |
| Users disabling it | Overtriggering | Narrow scope, clarify boundaries |
