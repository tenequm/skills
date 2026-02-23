# Anthropic Best Practices for Claude Skills

Extracted from official Anthropic documentation with attribution.

## Core Principles

1. **Conciseness** - Keep SKILL.md under 500 lines
2. **Progressive Disclosure** - Use reference files for details
3. **Specific Descriptions** - Clear when_to_use in frontmatter
4. **Concrete Examples** - Real code, not placeholders
5. **Assume Intelligence** - Trust Claude to understand

## SKILL.md Structure

```markdown
---
name: skill-name
description: Specific description of what this does and when to use it
---

# Skill Name

## Overview
Brief explanation of core purpose

## When to Use
Clear triggers and use cases

## Quick Reference
Table or bullets for common operations

## Examples
Concrete, runnable code

## Common Mistakes
What goes wrong + fixes
```

## Quality Scoring (10 points total)

### 1. Description Quality (2.0 points)
- ✅ Specific, not vague
- ✅ Includes what the skill does
- ✅ Includes when to use it
- ✅ Written in third person
- ✅ Under 1024 characters
- ❌ No "helps with", "tool for" vagueness

### 2. Name Convention (0.5 points)
- ✅ lowercase-with-hyphens
- ✅ Descriptive (not "helper", "utils")
- ✅ Gerund form preferred (-ing)
- ✅ Under 64 characters

### 3. Conciseness (1.5 points)
- ✅ <300 lines = 1.5 points
- ✅ <500 lines = 1.0 points
- ⚠️  500-800 lines = 0.5 points
- ❌ >800 lines = 0.0 points

### 4. Progressive Disclosure (1.0 points)
- ✅ Main SKILL.md is overview/TOC
- ✅ Details in reference files
- ✅ No deeply nested references (max 1 level)

### 5. Examples & Workflows (1.0 points)
- ✅ Concrete code examples
- ✅ Input/output pairs
- ✅ Real patterns, not placeholders
- ❌ No "template" or "fill-in-blank"

### 6. Degree of Freedom (0.5 points)
- ✅ High freedom for flexible tasks (text instructions)
- ✅ Low freedom for fragile tasks (exact scripts)

### 7. Dependencies (0.5 points)
- ✅ All dependencies listed
- ✅ Installation instructions
- ✅ Verified available

### 8. Structure (1.0 points)
- ✅ Clear section headings
- ✅ Logical flow
- ✅ Consistent formatting
- ✅ Unix paths (forward slashes)

### 9. Error Handling (0.5 points)
For skills with scripts:
- ✅ Scripts handle errors
- ✅ Clear error messages
- ✅ Validation loops

### 10. Anti-Patterns to Avoid (1.0 points)
- ❌ Time-sensitive information
- ❌ Inconsistent terminology
- ❌ Windows-style paths (\)
- ❌ Too many options without guidance
- ❌ Deeply nested references

### 11. Testing (0.5 points)
- ✅ Evidence of testing
- ✅ Evaluation examples
- ✅ Success criteria

## Common Issues & Fixes

### Issue: Description Too Vague
❌ Bad: "Helps with documents"
✅ Good: "Analyze Excel spreadsheets, create pivot tables, generate charts. Use when working with .xlsx files or tabular data."

### Issue: Too Long
❌ Bad: 800-line SKILL.md with everything inline
✅ Good: 300-line overview + 3 reference files

### Issue: Abstract Examples
❌ Bad: `function doSomething() { /* your code here */ }`
✅ Good: Complete, runnable examples from real use cases

### Issue: No When-to-Use
❌ Bad: description: "React development tool"
✅ Good: description: "Build React applications with hooks, routing, and state management. Use when creating React projects, need component patterns, or debugging React-specific issues."

## File Organization

```
skill-name/
├── SKILL.md                 # <500 lines overview
├── references/              # Detailed docs
│   ├── api-reference.md
│   ├── advanced-usage.md
│   └── troubleshooting.md
├── scripts/                 # Executable tools
│   └── helper-script.sh
└── examples/               # Complete examples
    └── example-project.md
```

## Frontmatter Best Practices

```yaml
---
name: processing-documents
description: Extract text from PDFs, analyze Word docs, convert formats. Use when working with PDF, DOCX, or document conversion tasks.
dependencies:
  - pypdf2
  - python-docx
---
```

## Progressive Disclosure Pattern

**Main SKILL.md (200 lines):**
- Overview
- Quick reference table
- Common workflows
- Links to references

**References (unlimited):**
- Detailed API docs
- Advanced patterns
- Troubleshooting
- Extended examples

## Quality Tiers

- **Excellent (8.0-10.0):** Production-ready, follows all best practices
- **Good (6.0-7.9):** Usable, minor improvements needed
- **Fair (4.0-5.9):** Needs review, several issues
- **Poor (0.0-3.9):** Significant problems, not recommended

## Source

Based on [Anthropic Skills Documentation](https://github.com/anthropics/skills)
- skill-creator/SKILL.md
- Official best practices guide

## Quick Validation Checklist

Before deploying any skill:
- [ ] Description specific and under 1024 chars?
- [ ] Name follows lowercase-hyphen convention?
- [ ] SKILL.md under 500 lines (or uses progressive disclosure)?
- [ ] Has 3+ concrete code examples?
- [ ] No time-sensitive information?
- [ ] Dependencies documented?
- [ ] Unix-style paths?
- [ ] Tested with real queries?
