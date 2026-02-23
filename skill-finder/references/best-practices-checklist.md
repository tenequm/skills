# Anthropic Best Practices Checklist

Evaluation criteria for assessing Claude Skill quality based on official Anthropic guidelines.

## Purpose

Use this checklist to evaluate skills found on GitHub. Each criterion contributes to the overall quality score (0-10).

## Evaluation Criteria

### 1. Description Quality (Weight: 2.0)

**What to check:**
- [ ] Description is specific, not vague
- [ ] Includes what the skill does
- [ ] Includes when to use it (trigger conditions)
- [ ] Contains key terms users would mention
- [ ] Written in third person
- [ ] Under 1024 characters
- [ ] No XML tags

**Scoring:**
- 2.0: All criteria met, very clear and specific
- 1.5: Most criteria met, good clarity
- 1.0: Basic description, somewhat vague
- 0.5: Very vague or generic
- 0.0: Missing or completely unclear

**Examples:**

**Good (2.0):**
```yaml
description: Analyze Excel spreadsheets, create pivot tables, generate charts. Use when working with Excel files, spreadsheets, tabular data, or .xlsx files.
```

**Bad (0.5):**
```yaml
description: Helps with documents
```

### 2. Name Convention (Weight: 0.5)

**What to check:**
- [ ] Uses lowercase letters, numbers, hyphens only
- [ ] Under 64 characters
- [ ] Follows naming pattern (gerund form preferred)
- [ ] Descriptive, not vague
- [ ] No reserved words ("anthropic", "claude")

**Scoring:**
- 0.5: Follows all conventions
- 0.25: Minor issues (e.g., not gerund but still clear)
- 0.0: Violates conventions or very vague

**Good:** `processing-pdfs`, `analyzing-spreadsheets`
**Bad:** `helper`, `utils`, `claude-tool`

### 3. Conciseness (Weight: 1.5)

**What to check:**
- [ ] SKILL.md body under 500 lines
- [ ] No unnecessary explanations
- [ ] Assumes Claude's intelligence
- [ ] Gets to the point quickly
- [ ] Additional content in separate files if needed

**Scoring:**
- 1.5: Very concise, well-edited, <300 lines
- 1.0: Reasonable length, <500 lines
- 0.5: Long but not excessive, 500-800 lines
- 0.0: Very verbose, >800 lines

### 4. Progressive Disclosure (Weight: 1.0)

**What to check:**
- [ ] SKILL.md serves as overview/table of contents
- [ ] Additional details in separate files
- [ ] Clear references to other files
- [ ] Files organized by domain/feature
- [ ] No deeply nested references (max 1 level deep)

**Scoring:**
- 1.0: Excellent use of progressive disclosure
- 0.75: Good organization with some references
- 0.5: Some separation, could be better
- 0.25: All content in SKILL.md, no references
- 0.0: Poorly organized or deeply nested

### 5. Examples and Workflows (Weight: 1.0)

**What to check:**
- [ ] Has concrete examples (not abstract)
- [ ] Includes code snippets
- [ ] Shows input/output pairs
- [ ] Has clear workflows for complex tasks
- [ ] Examples use real patterns, not placeholders

**Scoring:**
- 1.0: Excellent examples and clear workflows
- 0.75: Good examples, some workflows
- 0.5: Basic examples, no workflows
- 0.25: Few or abstract examples
- 0.0: No examples

### 6. Appropriate Degree of Freedom (Weight: 0.5)

**What to check:**
- [ ] Instructions match task fragility
- [ ] High freedom for flexible tasks (text instructions)
- [ ] Low freedom for fragile tasks (specific scripts)
- [ ] Clear when to use exact commands vs adapt

**Scoring:**
- 0.5: Perfect match of freedom to task type
- 0.25: Reasonable but could be better
- 0.0: Inappropriate level (too rigid or too loose)

### 7. Dependencies Documentation (Weight: 0.5)

**What to check:**
- [ ] Required packages listed
- [ ] Installation instructions provided
- [ ] Dependencies verified as available
- [ ] No assumption of pre-installed packages

**Scoring:**
- 0.5: All dependencies documented and verified
- 0.25: Dependencies mentioned but not fully documented
- 0.0: Dependencies assumed or not mentioned

### 8. Structure and Organization (Weight: 1.0)

**What to check:**
- [ ] Clear section headings
- [ ] Logical flow of information
- [ ] Table of contents for long files
- [ ] Consistent formatting
- [ ] Unix-style paths (forward slashes)

**Scoring:**
- 1.0: Excellently organized
- 0.75: Well organized with minor issues
- 0.5: Basic organization
- 0.25: Poor organization
- 0.0: No clear structure

### 9. Error Handling (Weight: 0.5)

**What to check (for skills with scripts):**
- [ ] Scripts handle errors explicitly
- [ ] Clear error messages
- [ ] Fallback strategies provided
- [ ] Validation loops for critical operations
- [ ] No "voodoo constants"

**Scoring:**
- 0.5: Excellent error handling
- 0.25: Basic error handling
- 0.0: No error handling or punts to Claude

### 10. Avoids Anti-Patterns (Weight: 1.0)

**What to avoid:**
- [ ] Time-sensitive information
- [ ] Inconsistent terminology
- [ ] Windows-style paths
- [ ] Offering too many options without guidance
- [ ] Deeply nested references
- [ ] Vague or generic content

**Scoring:**
- 1.0: No anti-patterns
- 0.75: 1-2 minor anti-patterns
- 0.5: Multiple anti-patterns
- 0.0: Severe anti-patterns

### 11. Testing and Validation (Weight: 0.5)

**What to check:**
- [ ] Evidence of testing mentioned
- [ ] Evaluation examples provided
- [ ] Clear success criteria
- [ ] Feedback loops for quality

**Scoring:**
- 0.5: Clear testing approach
- 0.25: Some testing mentioned
- 0.0: No testing mentioned

## Scoring System

**Total possible: 10.0 points**

Calculate weighted score:
```
quality_score = (
  description_score * 2.0 +
  name_score * 0.5 +
  conciseness_score * 1.5 +
  progressive_disclosure_score * 1.0 +
  examples_score * 1.0 +
  freedom_score * 0.5 +
  dependencies_score * 0.5 +
  structure_score * 1.0 +
  error_handling_score * 0.5 +
  anti_patterns_score * 1.0 +
  testing_score * 0.5
)
```

## Quality Tiers

**Excellent (8.0-10.0):**
- Follows all best practices
- Clearly professional
- Ready for production use
- **Recommendation:** Strongly recommended

**Good (6.0-7.9):**
- Follows most best practices
- Minor improvements needed
- Usable but not perfect
- **Recommendation:** Recommended with minor notes

**Fair (4.0-5.9):**
- Follows some best practices
- Several improvements needed
- May work but needs review
- **Recommendation:** Consider with caution

**Poor (0.0-3.9):**
- Violates many best practices
- Significant issues
- High risk of problems
- **Recommendation:** Not recommended

## Quick Evaluation Process

For rapid assessment during search:

1. **Read SKILL.md frontmatter** (30 sec)
   - Check description quality (most important)
   - Check name convention

2. **Scan SKILL.md body** (1-2 min)
   - Check length (<500 lines?)
   - Look for examples
   - Check for references to other files
   - Note any obvious anti-patterns

3. **Check file structure** (30 sec)
   - Look for reference files
   - Check for scripts/utilities
   - Verify organization

4. **Calculate quick score** (30 sec)
   - Focus on weighted criteria
   - Estimate tier (Excellent/Good/Fair/Poor)

**Total time per skill: ~3-4 minutes**

## Automation Tips

When evaluating multiple skills:

```bash
# Check SKILL.md length
wc -l SKILL.md

# Count reference files
find . -name "*.md" -not -name "SKILL.md" | wc -l

# Check for common anti-patterns
grep -i "claude can help\|I can help\|you can use" SKILL.md

# Verify Unix paths
grep -E '\\\|\\\\' SKILL.md

# Check description length
head -10 SKILL.md | grep "description:" | wc -c
```

## Reference

Based on official Anthropic documentation:
- [Agent Skills Overview](https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills/overview)
- [Best Practices Guide](https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills/best-practices)
- [Claude Code Skills](https://docs.anthropic.com/en/docs/claude-code/skills)

---

**Usage:** Use this checklist when evaluating skills found through skill-finder to provide quality scores and recommendations to users.
