# Skill Quality Checklist

Validate your skill before upload or sharing. Based on Anthropic's official checklist from "The Complete Guide to Building Skills for Claude."

## Before You Start

- [ ] Identified 2-3 concrete use cases the skill enables
- [ ] Tools identified (built-in, MCP, or scripts)
- [ ] Planned folder structure (SKILL.md + what else is needed)

## Frontmatter

- [ ] Folder named in **kebab-case** (no spaces, no capitals)
- [ ] `SKILL.md` file exists (exact spelling, case-sensitive)
- [ ] YAML frontmatter has `---` delimiters
- [ ] `name`: kebab-case, max 64 chars, no "claude"/"anthropic"
- [ ] `description`: includes WHAT and WHEN, max 1024 chars
- [ ] No XML angle brackets (`<` `>`) anywhere in frontmatter
- [ ] No `README.md` inside the skill folder

## Description Quality

- [ ] Written in **third person** ("Processes..." not "I help...")
- [ ] Includes specific **capabilities** (action verbs)
- [ ] Includes specific **trigger phrases** users would say
- [ ] Mentions relevant **file types** if applicable
- [ ] Specific enough to distinguish from similar skills
- [ ] Slightly "pushy" - Claude tends to undertrigger

## Instructions Quality

- [ ] Concise - only adds context Claude doesn't already have
- [ ] Clear and actionable (not vague or ambiguous)
- [ ] Uses markdown headers for structure
- [ ] Critical instructions at the **top**, not buried
- [ ] Working examples provided (not pseudocode)
- [ ] Error handling included for common failures
- [ ] Consistent terminology throughout (pick one term, stick with it)

## Progressive Disclosure

- [ ] SKILL.md body under **500 lines**
- [ ] Detailed docs in separate files (references/, scripts/)
- [ ] References clearly linked from SKILL.md
- [ ] References are **one level deep** (no nested chains)
- [ ] Long reference files (>100 lines) have a table of contents

## Scripts (if applicable)

- [ ] Scripts handle errors explicitly (don't punt to Claude)
- [ ] No "voodoo constants" (all values justified with comments)
- [ ] Required packages listed in instructions
- [ ] Package availability verified in target environment
- [ ] Clear whether Claude should execute or read each script
- [ ] Scripts use forward slashes in paths (not backslashes)

## Testing

### Triggering Tests

- [ ] Triggers on obvious, direct requests
- [ ] Triggers on paraphrased/natural requests
- [ ] Does NOT trigger on unrelated topics
- [ ] Does NOT trigger on similar-but-distinct requests

### Functional Tests

- [ ] Valid outputs generated for normal inputs
- [ ] Edge cases handled (missing data, unusual formats)
- [ ] API/MCP calls succeed (if applicable)
- [ ] Output consistency across 3-5 runs
- [ ] Tested with at least Haiku and Sonnet (ideally Opus too)

### Real-World Validation

- [ ] Tested in real conversations (not just test scenarios)
- [ ] A new user can accomplish the task on first try
- [ ] Users don't need to prompt Claude about next steps
- [ ] Workflows complete without user correction

## Before Upload

- [ ] All tests pass
- [ ] Tool integration works (if applicable)
- [ ] No time-sensitive information (or in "old patterns" section)
- [ ] No Windows-style paths (all forward slashes)
- [ ] No deprecated APIs referenced

## After Upload

- [ ] Test in real conversations on target surface
- [ ] Monitor for under/over-triggering
- [ ] Collect user feedback
- [ ] Iterate on description and instructions based on usage
- [ ] Update version in metadata

## Performance Comparison (Optional)

Compare with and without skill:

| Metric | Without Skill | With Skill |
|--------|--------------|------------|
| Messages to complete | ? | ? |
| Failed API calls | ? | ? |
| Tokens consumed | ? | ? |
| User corrections needed | ? | ? |

Aim for: 90%+ triggering accuracy, 0 failed API calls, fewer user corrections.
