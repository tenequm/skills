# Sample Output Examples

Expected output format for skill-finder searches with fitness-based evaluation.

## Example 1: Specific Use Case Query

**User Query:** "Find me a skill for creating pitch decks"

**Output:**

```
🔍 Searching for skills matching: "pitch deck creation"
   Semantic terms: pitch deck, presentation, slides, powerpoint, keynote

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Skills for: "creating pitch decks"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 #1 presentation-builder ⭐ 245 🔥 | FITNESS: 9.2/10

   Quality Assessment:
   ✅ Description: Excellent (2.0/2.0)
      "Create presentations and pitch decks with templates, charts, and data visualization"
   ✅ Structure: Well organized (0.9/1.0)
   ✅ Examples: Comprehensive workflows (1.0/1.0)
   ⚠️  Length: 520 lines (slightly over 500 recommended)
   ✅ Progressive disclosure: Excellent use of reference files

   Overall Quality: 8.7/10 (Excellent)

   Why it fits your request:
   • Specifically designed for pitch deck creation
   • Mentions "pitch deck" 8 times in SKILL.md
   • Has pitch deck templates and examples
   • Includes business presentation workflows
   • Supports PowerPoint and Google Slides
   • Has data visualization helpers

   Why it's high quality:
   • Follows all Anthropic best practices
   • Clear, concise instructions
   • Comprehensive examples with workflows
   • Well-tested and actively maintained
   • Good error handling and validation

   📎 https://github.com/user/presentation-builder/blob/main/SKILL.md

   [Preview Full Analysis] [Install]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 #2 office-automation ⭐ 450 📅 | FITNESS: 6.5/10

   Quality Assessment:
   ✅ Well-documented with examples
   ✅ Good structure and organization
   ⚠️  Description too broad ("office automation")
   ⚠️  Not focused on presentations specifically
   ❌ Missing pitch deck specific features

   Overall Quality: 7.2/10 (Good)

   Why it partially fits:
   • Includes PowerPoint/Slides capabilities
   • Has slide creation examples
   • Can handle basic presentations

   Why it's not ideal:
   • Generic "office automation" scope
   • No pitch deck templates
   • Lacks business presentation focus
   • No data visualization specific to decks
   • Lower semantic match (only 2 relevant mentions)

   📎 https://github.com/user/office-automation/blob/main/SKILL.md

   [Preview] [Install]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 #3 document-creator ⭐ 180 🔥 | FITNESS: 4.8/10

   Quality Assessment:
   ✅ Clear description and examples
   ⚠️  Mixed focus (documents + presentations)
   ❌ No progressive disclosure
   ❌ Very long SKILL.md (850 lines)

   Overall Quality: 5.5/10 (Fair)

   Why it's a weak match:
   • Primarily focused on documents, not presentations
   • Mentions "presentation" only once
   • No pitch deck specific content
   • Would need significant adaptation

   📎 https://github.com/user/document-creator/blob/main/SKILL.md

   [Review] [Skip]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 From Awesome Lists:

Found in awesome-claude-skills (BehiSecc):
  • pptx-generator (FITNESS: 7.2/10) - Good for basic slides
  • slide-master (FITNESS: 8.1/10) - Strong presentation focus

Found in awesome-claude-skills (travisvn):
  • deck-builder (FITNESS: 7.8/10) - Pitch deck oriented

[Evaluate These] [Show All]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Recommendation: presentation-builder (FITNESS: 9.2/10) ⭐⭐⭐⭐⭐

   Best match for your needs. Specifically designed for pitch decks,
   high quality, follows best practices, and actively maintained.

   Alternative: slide-master from awesome-list (FITNESS: 8.1/10)
   if you need different templates or workflow.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Example 2: Data Analysis Query

**User Query:** "What's the best skill for automated data analysis?"

**Output:**

```
🔍 Searching for skills matching: "automated data analysis"
   Semantic terms: data analysis, automation, analytics, statistics, visualization

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Skills for: "automated data analysis"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 #1 data-analyzer ⭐ 312 🔥 | FITNESS: 9.5/10

   Quality Assessment:
   ✅ Description: Perfect specificity (2.0/2.0)
   ✅ Concise: 380 lines with excellent references
   ✅ Examples: Multiple workflows with validation
   ✅ Progressive disclosure: Exemplary
   ✅ Error handling: Comprehensive

   Overall Quality: 9.3/10 (Excellent)

   Why it's perfect for your need:
   • Explicitly designed for automated data analysis
   • Mentions "automation" and "analysis" throughout
   • Has complete analysis workflows
   • Includes validation and feedback loops
   • Supports multiple data formats
   • Has statistical analysis helpers

   Key Features:
   • CSV, Excel, JSON analysis
   • Automated statistical tests
   • Visualization generation
   • Report automation
   • Quality checks and validation

   📎 https://github.com/user/data-analyzer/blob/main/SKILL.md

   [Preview Full Analysis] [Install]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 #2 excel-master ⭐ 456 📅 | FITNESS: 7.8/10

   Quality Assessment:
   ✅ Good quality, well-maintained
   ⚠️  Excel-specific (limited to one format)
   ⚠️  Less automation focus

   Overall Quality: 7.5/10 (Good)

   Why it's good but not perfect:
   • Strong Excel analysis capabilities
   • Has some automation features
   • But limited to Excel format only
   • Less comprehensive than data-analyzer

   📎 https://github.com/user/excel-master/blob/main/SKILL.md

   [Preview] [Install]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Recommendation: data-analyzer (FITNESS: 9.5/10) ⭐⭐⭐⭐⭐

   Exactly what you need. Purpose-built for automated data analysis,
   excellent quality, comprehensive features.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Example 3: No Strong Match Found

**User Query:** "Find me a skill for quantum computing simulations"

**Output:**

```
🔍 Searching for skills matching: "quantum computing simulations"
   Semantic terms: quantum, computing, simulation, qubit, circuit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  No Strong Matches Found
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Searched 47 skills, but none strongly match your query.

Best partial matches:

🏆 #1 scientific-computing ⭐ 123 📅 | FITNESS: 4.2/10

   Quality: 7.0/10 (Good)

   Partial match because:
   • General scientific computing
   • Mentions "simulation" a few times
   • No quantum-specific content
   • Would need significant adaptation

   📎 https://github.com/user/scientific-computing/blob/main/SKILL.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 #2 python-automation ⭐ 89 🔥 | FITNESS: 3.1/10

   Quality: 6.5/10 (Good)

   Weak match:
   • Python scripting focus
   • Could theoretically run quantum libraries
   • But no quantum-specific guidance

   📎 https://github.com/user/python-automation/blob/main/SKILL.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Recommendations:

   None of these skills are strong matches for quantum computing.

   Consider:
   • Searching awesome-lists directly for quantum skills
   • Requesting a quantum skill from curators
   • Creating a custom skill for your specific need
   • Broaden search: "scientific computing" or "physics simulations"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Example 4: Full Analysis Details

**User Action:** Clicks [Preview Full Analysis] on presentation-builder

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Full Analysis: presentation-builder
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏢 Repository Info:
   Owner: presentation-tools
   Stars: ⭐ 245
   Updated: 🔥 2 days ago (very active)
   URL: https://github.com/presentation-tools/presentation-builder

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Quality Breakdown (Anthropic Best Practices)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Description Quality:      2.0/2.0 ✅
  ✅ Highly specific: "Create presentations and pitch decks"
  ✅ Includes what: presentation/pitch deck creation
  ✅ Includes when: "Use when creating business presentations"
  ✅ Written in third person
  ✅ Contains key trigger terms
  ✅ Under 1024 characters

Name Convention:          0.5/0.5 ✅
  ✅ Follows naming rules (lowercase, hyphens)
  ✅ Descriptive gerund form
  ✅ Clear and specific
  ✅ No reserved words

Conciseness:              1.3/1.5 ⚠️
  ⚠️  520 lines (slightly over 500 recommended)
  ✅ No unnecessary fluff
  ✅ Gets to the point quickly
  ✅ Additional details in separate files

Progressive Disclosure:   1.0/1.0 ✅
  ✅ SKILL.md serves as excellent overview
  ✅ References 4 additional files appropriately:
     • templates.md (pitch deck templates)
     • charts.md (data visualization guide)
     • workflows.md (presentation creation flows)
     • examples.md (real-world examples)
  ✅ All references are 1 level deep
  ✅ Well-organized by feature

Examples & Workflows:     1.0/1.0 ✅
  ✅ Concrete pitch deck example
  ✅ Step-by-step workflow
  ✅ Input/output pairs shown
  ✅ Code snippets included
  ✅ Real patterns, not placeholders

Degree of Freedom:        0.5/0.5 ✅
  ✅ Appropriate for task type
  ✅ Flexible for creative tasks
  ✅ Structured for technical steps
  ✅ Good balance

Dependencies:             0.5/0.5 ✅
  ✅ All dependencies listed (python-pptx, matplotlib)
  ✅ Installation instructions clear
  ✅ Verified available in environment

Structure:                0.9/1.0 ✅
  ✅ Excellent organization
  ✅ Clear section headings
  ✅ Logical flow
  ⚠️  Minor: One inconsistent heading style

Error Handling:           0.5/0.5 ✅
  ✅ Scripts handle errors explicitly
  ✅ Validation loops for quality
  ✅ Clear error messages
  ✅ Feedback loops implemented

Anti-Patterns:            0.9/1.0 ✅
  ✅ No time-sensitive information
  ✅ Consistent terminology
  ✅ Unix-style paths throughout
  ⚠️  One instance: offers 2 template choices (minor)

Testing:                  0.5/0.5 ✅
  ✅ Clear testing approach documented
  ✅ Example evaluations included
  ✅ Success criteria defined

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Quality Score: 8.7/10 (Excellent Tier)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Semantic Match Analysis

User Query: "creating pitch decks"

Extracted terms: pitch deck, presentation, slides, powerpoint, keynote

Skill Content Analysis:
  ✅ "pitch deck" - 8 occurrences
  ✅ "presentation" - 15 occurrences
  ✅ "slides" - 12 occurrences
  ✅ "powerpoint" - 4 occurrences
  ✅ "business" - 6 occurrences (contextually relevant)
  ✅ Has "templates" section with pitch deck examples
  ✅ Has "data visualization" section for charts
  ✅ Has complete workflow for deck creation

Key Features Found:
  • Pitch deck template library
  • Business presentation workflows
  • Data chart integration
  • Multi-format export (PPTX, Google Slides)
  • Automated layout suggestions

Semantic Match Score: 9.5/10

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fitness Score Calculation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

semantic_match * 0.4  = 9.5 * 0.4  = 3.8
quality_score * 0.3   = 8.7 * 0.3  = 2.61
(stars/100) * 0.2     = 2.45 * 0.2 = 0.49
freshness * 0.1       = 10 * 0.1   = 1.0
                                    ------
Final FITNESS Score:                  8.9/10

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Recommendation: Highly Recommended ⭐⭐⭐⭐⭐

This skill is an excellent match for your needs:

Strengths:
  • Purpose-built for pitch deck creation
  • Follows Anthropic best practices closely
  • Well-maintained and actively developed
  • Comprehensive features and workflows
  • High semantic alignment with your query

Minor considerations:
  • Slightly over 500 lines (520) - still very good
  • One minor heading inconsistency

Overall: This is the best available skill for creating pitch decks.
Install with confidence.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Install Now] [View SKILL.md] [Back to Results]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Example 5: Multiple Good Matches

**User Query:** "Find skills for git commit messages"

**Output:**

```
🔍 Searching for skills matching: "git commit messages"
   Semantic terms: git, commit, message, changelog, version control

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Skills for: "git commit messages"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Found 3 excellent matches!

🏆 #1 commit-helper ⭐ 89 🔥 | FITNESS: 9.1/10

   Quality: 8.9/10 (Excellent)

   Perfect for:
   • Generating commit messages from diffs
   • Following conventional commit format
   • Analyzing changes semantically

   📎 https://github.com/user/commit-helper/blob/main/SKILL.md
   [Preview] [Install]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 #2 git-automation ⭐ 156 🔥 | FITNESS: 8.7/10

   Quality: 8.2/10 (Excellent)

   Good for:
   • Broader git workflows
   • Includes commit message generation
   • Plus branching and PR helpers

   📎 https://github.com/user/git-automation/blob/main/SKILL.md
   [Preview] [Install]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 #3 changelog-generator ⭐ 67 📅 | FITNESS: 7.4/10

   Quality: 7.8/10 (Good)

   Alternative approach:
   • Focused on changelog generation
   • Can help with commit message consistency
   • Different workflow than #1 and #2

   📎 https://github.com/user/changelog-generator/blob/main/SKILL.md
   [Preview] [Install]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Recommendation:

   All three are high quality! Choose based on your workflow:

   • commit-helper (FITNESS: 9.1/10) - Best if you ONLY need commit messages
   • git-automation (FITNESS: 8.7/10) - Best if you want broader git help
   • changelog-generator (FITNESS: 7.4/10) - Best if you maintain changelogs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Key Differences from Old Output

### Old Approach (Popularity-Based):
```
🏆 #1 awesome-claude-skills ⭐ 1703 🔥
   BehiSecc/awesome-claude-skills • Updated 6 days ago
   A curated list of Claude Skills.
   📎 https://github.com/BehiSecc/awesome-claude-skills
```

Problems:
- Just shows star count
- No quality assessment
- No fitness to user query
- Awesome-lists mixed with actual skills
- No explanation of WHY it's ranked #1

### New Approach (Fitness-Based):
```
🏆 #1 presentation-builder ⭐ 245 🔥 | FITNESS: 9.2/10

   Quality Assessment: 8.7/10 (Excellent)

   Why it fits your request:
   • Specifically designed for pitch decks
   • Mentions your key terms 8 times
   • Has templates and workflows

   Why it's high quality:
   • Follows Anthropic best practices
   • Well-tested and maintained
```

Benefits:
- Shows FITNESS to specific query
- Explains WHY it's a good match
- Evaluates against best practices
- Separates awesome-lists
- Actionable quality assessment

---

**Remember:** The goal is finding the RIGHT skill for the SPECIFIC need, not just what's popular.
