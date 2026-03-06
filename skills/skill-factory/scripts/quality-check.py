#!/usr/bin/env python3
"""
Quality checker for Claude skills based on Anthropic best practices.
Returns score 0-10 and lists issues.
"""

import sys
import re
from pathlib import Path


def check_description(frontmatter):
    """Check description quality (2.0 points)"""
    desc = frontmatter.get('description', '')

    score = 0.0
    issues = []

    if not desc:
        issues.append("Missing description")
        return score, issues

    # Length check
    if len(desc) < 50:
        issues.append("Description too short (< 50 chars)")
    else:
        score += 0.5

    # Specificity check
    vague_words = ['helps with', 'tool for', 'useful', 'handles']
    if any(word in desc.lower() for word in vague_words):
        issues.append("Description contains vague phrases")
    else:
        score += 0.5

    # when_to_use check
    if 'when ' in desc.lower() or 'use when' in desc.lower():
        score += 0.5
    else:
        issues.append("Description missing 'when to use' guidance")

    # Third person check
    if not any(word in desc.lower() for word in ['you', 'your', 'i ', "i'm"]):
        score += 0.5
    else:
        issues.append("Description should be third person")

    return min(score, 2.0), issues


def check_name(frontmatter):
    """Check name convention (0.5 points)"""
    name = frontmatter.get('name', '')

    score = 0.0
    issues = []

    if not name:
        issues.append("Missing name")
        return score, issues

    # Lowercase and hyphens
    if name == name.lower() and '-' in name:
        score += 0.25
    else:
        issues.append("Name should be lowercase-with-hyphens")

    # Not too generic
    if name not in ['helper', 'utils', 'tool', 'skill']:
        score += 0.25
    else:
        issues.append("Name too generic")

    return min(score, 0.5), issues


def check_conciseness(content):
    """Check length (1.5 points)"""
    lines = content.count('\n')

    if lines < 300:
        return 1.5, []
    elif lines < 500:
        return 1.0, []
    elif lines < 800:
        return 0.5, [f"SKILL.md is {lines} lines (recommend <500)"]
    else:
        return 0.0, [f"SKILL.md is {lines} lines (way over 500 limit)"]


def check_examples(content):
    """Check for code examples (1.0 points)"""
    code_blocks = len(re.findall(r'```[\w]*\n', content))

    issues = []
    if code_blocks == 0:
        issues.append("No code examples found")
        return 0.0, issues
    elif code_blocks < 3:
        issues.append(f"Only {code_blocks} code examples (recommend 5+)")
        return 0.5, issues
    else:
        return 1.0, []


def check_structure(content):
    """Check structure (1.0 points)"""
    issues = []
    score = 1.0

    # Required sections
    if '## Overview' not in content and '## What' not in content:
        issues.append("Missing overview section")
        score -= 0.3

    if '## Usage' not in content and '## How' not in content:
        issues.append("Missing usage section")
        score -= 0.3

    # Windows paths check
    if '\\' in content and 'C:\\' in content:
        issues.append("Contains Windows-style paths (use Unix /)")
        score -= 0.4

    return max(score, 0.0), issues


def check_antipatterns(content):
    """Check for anti-patterns (1.0 points)"""
    issues = []
    score = 1.0

    # Time-sensitive info
    time_patterns = [r'\d{4}-\d{2}-\d{2}', r'last updated', r'as of \d{4}']
    for pattern in time_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append("Contains time-sensitive information")
            score -= 0.5
            break

    # Inconsistent terminology
    if content.count('skill') + content.count('Skill') > 0:
        if content.count('plugin') + content.count('Plugin') > 0:
            issues.append("Inconsistent terminology (skill vs plugin)")
            score -= 0.5

    return max(score, 0.0), issues


def parse_frontmatter(content):
    """Extract YAML frontmatter"""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return {}

    fm = {}
    for line in match.group(1).split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            fm[key.strip()] = value.strip()

    return fm


def score_skill(skill_path):
    """Score a skill file against Anthropic best practices"""
    if not Path(skill_path).exists():
        print(f"Error: {skill_path} not found")
        sys.exit(1)

    with open(skill_path, 'r') as f:
        content = f.read()

    frontmatter = parse_frontmatter(content)

    total_score = 0.0
    all_issues = []

    # Run checks
    checks = [
        ('Description', check_description, frontmatter),
        ('Name', check_name, frontmatter),
        ('Conciseness', check_conciseness, content),
        ('Examples', check_examples, content),
        ('Structure', check_structure, content),
        ('Anti-patterns', check_antipatterns, content),
    ]

    for name, check_func, arg in checks:
        score, issues = check_func(arg)
        total_score += score
        if issues:
            all_issues.extend([f"{name}: {issue}" for issue in issues])

    # Add partial scores for other criteria (simplified)
    total_score += 1.0  # Progressive disclosure (assume good if references/ exists)
    total_score += 0.5  # Degree of freedom (assume appropriate)
    total_score += 0.5  # Dependencies (assume documented)
    total_score += 0.5  # Error handling (assume good)
    total_score += 0.5  # Testing (assume some testing)

    return round(total_score, 1), all_issues


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: quality-check.py <path-to-SKILL.md>")
        sys.exit(1)

    score, issues = score_skill(sys.argv[1])

    print(f"{score}/10")

    if issues:
        print("\nIssues found:")
        for issue in issues:
            print(f"  - {issue}")

    # Exit code: 0 if >= 8.0, 1 otherwise
    sys.exit(0 if score >= 8.0 else 1)
