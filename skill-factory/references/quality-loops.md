# Quality Assurance Loops

How skill-factory ensures every skill meets minimum quality standards.

## Quality Scoring (Anthropic Best Practices)

Based on official Anthropic guidelines, total possible: 10.0 points

### Scoring Criteria

| Criterion | Weight | What to Check |
|-----------|--------|---------------|
| Description Quality | 2.0 | Specific, includes when_to_use, third-person |
| Name Convention | 0.5 | Lowercase, hyphens, descriptive |
| Conciseness | 1.5 | <500 lines OR progressive disclosure |
| Progressive Disclosure | 1.0 | Reference files for details |
| Examples & Workflows | 1.0 | Concrete code samples |
| Degree of Freedom | 0.5 | Appropriate for task type |
| Dependencies | 0.5 | Documented and verified |
| Structure | 1.0 | Well-organized sections |
| Error Handling | 0.5 | Scripts handle errors |
| Anti-Patterns | 1.0 | No time-sensitive info, consistent terminology |
| Testing | 0.5 | Evidence of testing |

## Enhancement Loop Algorithm

```python
def quality_assurance_loop(skill_path: str, min_score: float = 8.0) -> Skill:
    """
    Iteratively improve skill until it meets quality threshold.
    Max iterations: 5 (prevents infinite loops)
    """
    max_iterations = 5
    iteration = 0

    while iteration < max_iterations:
        # Score skill
        score, issues = score_skill(skill_path)

        print(f"📊 Quality check: {score}/10")

        if score >= min_score:
            print(f"✅ Quality threshold met ({score} >= {min_score})")
            return load_skill(skill_path)

        # Report issues
        print(f"   ⚠️  Issues found:")
        for issue in issues:
            print(f"       - {issue.description}")

        # Apply fixes
        print(f"🔧 Enhancing skill...")
        skill = apply_fixes(skill_path, issues)

        iteration += 1

    # If we hit max iterations without reaching threshold
    if score < min_score:
        print(f"⚠️  Quality score {score} below threshold after {max_iterations} iterations")
        print(f"   Manual review recommended")
        return load_skill(skill_path)

    return load_skill(skill_path)
```

## Fix Strategies

### Issue: Description Too Generic

**Detection:**
```python
def check_description(skill):
    desc = skill.frontmatter.description
    if len(desc) < 50:
        return Issue("Description too short (< 50 chars)")
    if not contains_specifics(desc):
        return Issue("Description lacks specifics")
    if "help" in desc.lower() or "tool" in desc.lower():
        return Issue("Description too vague")
    return None
```

**Fix:**
```python
def fix_description(skill):
    # Extract key topics from skill content
    topics = extract_topics(skill.content)

    # Generate specific description
    desc = f"Comprehensive guide for {skill.name} covering "
    desc += ", ".join(topics[:3])
    desc += f". Use when working with {topics[0]} "
    desc += f"and need {', '.join(topics[1:3])}"

    skill.frontmatter.description = desc
    return skill
```

### Issue: Missing Examples

**Detection:**
```python
def check_examples(skill):
    code_blocks = count_code_blocks(skill.content)
    if code_blocks < 3:
        return Issue(f"Only {code_blocks} code examples (recommend 5+)")
    return None
```

**Fix:**
```python
def add_examples(skill, source_docs=None):
    if source_docs:
        # Extract from documentation
        examples = extract_code_examples(source_docs)
    else:
        # Generate from skill content
        examples = generate_examples_from_topics(skill)

    # Add examples section
    if "## Examples" not in skill.content:
        skill.content += "\n\n## Examples\n\n"

    for ex in examples[:5]:  # Add top 5 examples
        skill.content += f"### {ex.title}\n\n"
        skill.content += f"```{ex.language}\n{ex.code}\n```\n\n"
        if ex.explanation:
            skill.content += f"{ex.explanation}\n\n"

    return skill
```

### Issue: Too Long (> 500 lines)

**Detection:**
```python
def check_length(skill):
    line_count = count_lines(skill.content)
    if line_count > 500:
        return Issue(f"SKILL.md is {line_count} lines (recommend <500)")
    return None
```

**Fix:**
```python
def apply_progressive_disclosure(skill):
    # Identify sections that can be moved to references
    movable_sections = find_detail_sections(skill.content)

    skill.references = {}

    for section in movable_sections:
        # Create reference file
        ref_name = slugify(section.title)
        ref_path = f"references/{ref_name}.md"

        # Move content
        skill.references[ref_name] = section.content

        # Replace with reference
        skill.content = skill.content.replace(
            section.full_text,
            f"See {ref_path} for detailed {section.title.lower()}."
        )

    return skill
```

### Issue: Poor Structure

**Detection:**
```python
def check_structure(skill):
    issues = []

    # Check for required sections
    required = ["## Overview", "## Usage", "## Examples"]
    for section in required:
        if section not in skill.content:
            issues.append(f"Missing {section}")

    # Check heading hierarchy
    if has_heading_skips(skill.content):
        issues.append("Heading hierarchy skips levels")

    # Check for TOC if long
    if count_lines(skill.content) > 200 and "## Table of Contents" not in skill.content:
        issues.append("Long skill missing table of contents")

    return issues if issues else None
```

**Fix:**
```python
def fix_structure(skill, issues):
    # Add missing sections
    if "Missing ## Overview" in issues:
        overview = generate_overview(skill)
        skill.content = insert_after_frontmatter(skill.content, overview)

    if "Missing ## Usage" in issues:
        usage = generate_usage_section(skill)
        skill.content = insert_before_examples(skill.content, usage)

    # Fix heading hierarchy
    if "Heading hierarchy" in str(issues):
        skill.content = normalize_headings(skill.content)

    # Add TOC if needed
    if "missing table of contents" in str(issues):
        toc = generate_toc(skill.content)
        skill.content = insert_toc(skill.content, toc)

    return skill
```

### Issue: Vague/Generic Content

**Detection:**
```python
def check_specificity(skill):
    vague_phrases = [
        "you can", "might want to", "it's possible",
        "there are various", "several options",
        "many ways to", "different approaches"
    ]

    content_lower = skill.content.lower()
    vague_count = sum(1 for phrase in vague_phrases if phrase in content_lower)

    if vague_count > 10:
        return Issue(f"Too many vague phrases ({vague_count})")

    return None
```

**Fix:**
```python
def improve_specificity(skill):
    # Replace vague with specific
    replacements = {
        "you can": "Use",
        "might want to": "Should",
        "there are various": "Three main approaches:",
        "several options": "Options:",
        "many ways to": "Primary methods:",
    }

    for vague, specific in replacements.items():
        skill.content = skill.content.replace(vague, specific)

    return skill
```

## Testing Integration

After each enhancement, run tests:

```python
def enhance_and_test(skill):
    while score < min_score:
        # Enhance
        skill = apply_enhancements(skill)

        # Score
        score = calculate_score(skill)

        # Test
        test_results = run_tests(skill)

        if not test_results.all_passed():
            # Tests revealed new issues
            issues = test_results.get_failures()
            skill = fix_test_failures(skill, issues)

    return skill
```

## Progress Reporting

User sees:

```
📊 Quality check: 7.4/10
   ⚠️  Issues found:
       - Description too generic
       - Missing examples in 4 sections
       - Some outdated patterns detected

🔧 Enhancing skill...
   ✏️  Improving description... ✅
   📝 Adding code examples... ✅
   🔄 Updating patterns... ✅

📊 Quality check: 8.9/10 ✅
```

Internal execution:

```python
issues = [
    Issue("description_generic", fix=fix_description),
    Issue("missing_examples", fix=add_examples, count=4),
    Issue("outdated_patterns", fix=update_patterns)
]

for issue in issues:
    print(f"   {issue.icon}  {issue.action}... ", end="")
    skill = issue.fix(skill)
    print("✅")
```

## Quality Metrics Dashboard

After completion:

```
📊 Final Quality Report

Anthropic Best Practices Score: 8.9/10

Breakdown:
✅ Description Quality:      2.0/2.0  (Excellent)
✅ Name Convention:          0.5/0.5  (Correct)
✅ Conciseness:              1.4/1.5  (Good - 420 lines)
✅ Progressive Disclosure:   1.0/1.0  (Excellent - 3 reference files)
✅ Examples & Workflows:     1.0/1.0  (12 code examples)
✅ Degree of Freedom:        0.5/0.5  (Appropriate)
✅ Dependencies:             0.5/0.5  (Documented)
✅ Structure:                1.0/1.0  (Well-organized)
✅ Error Handling:           0.5/0.5  (N/A for doc skill)
✅ Anti-Patterns:            0.5/1.0  (Minor: 2 time refs)
✅ Testing:                  0.5/0.5  (15/15 tests passing)

Recommendations:
⚠️  Remove 2 time-sensitive references for 1.0/1.0 on anti-patterns
```

## Failure Modes

### Can't Reach Threshold

If after 5 iterations score is still < 8.0:

```
⚠️  Quality score 7.8 after 5 iterations

Blocking issues:
- Source documentation lacks code examples
- Framework has limited reference material

Recommendations:
1. Manual examples needed (auto-generation limited)
2. Consider hybrid approach with custom content
3. Lower quality threshold to 7.5 for this specific case

Continue with current skill? (y/n)
```

### Conflicting Requirements

```
⚠️  Conflicting requirements detected

Issue: Comprehensive coverage (800 lines) vs Conciseness (<500 lines)

Resolution: Applying progressive disclosure
- Main SKILL.md: 380 lines (overview + quick ref)
- Reference files: 5 files with detailed content
```

## Summary

Quality loops ensure:
1. Every skill scores >= threshold (default 8.0)
2. Anthropic best practices followed
3. Automatic fixes applied
4. Tests pass
5. User sees progress, not complexity
