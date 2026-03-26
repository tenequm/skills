# Skill Patterns and Workflows

Advanced patterns for structuring skills, drawn from Anthropic's official examples and early adopter experience.

## Contents

- Choosing your approach (problem-first vs tool-first)
- Pattern 1: Sequential workflow orchestration
- Pattern 2: Multi-MCP coordination
- Pattern 3: Iterative refinement with feedback loops
- Pattern 4: Context-aware tool selection
- Pattern 5: Domain-specific intelligence
- Pattern 6: Plan-validate-execute
- Pattern 7: Template pattern
- Pattern 8: Examples pattern (input/output pairs)
- Progressive disclosure patterns
- Skills + MCP integration
- Skills + Subagents integration

## Choosing Your Approach

### Problem-First

User describes an outcome; the skill orchestrates the right tools:

```
"I need to set up a project workspace"
-> Skill calls create_project, add_members, configure_settings
```

### Tool-First

User has a tool connected; the skill teaches best practices:

```
"I have Notion MCP connected"
-> Skill provides optimal workflows and conventions
```

Most skills lean one direction. Know which framing fits your use case.

## Pattern 1: Sequential Workflow Orchestration

Use when: multi-step processes must follow a specific order.

```markdown
## Workflow: Onboard New Customer

### Step 1: Create Account
Call MCP tool: `create_customer`
Parameters: name, email, company

### Step 2: Setup Payment
Call MCP tool: `setup_payment_method`
Wait for: payment method verification

### Step 3: Create Subscription
Call MCP tool: `create_subscription`
Parameters: plan_id, customer_id (from Step 1)

### Step 4: Send Welcome Email
Call MCP tool: `send_email`
Template: welcome_email_template
```

Key techniques:
- Explicit step ordering
- Dependencies between steps clearly stated
- Validation at each stage
- Rollback instructions for failures

## Pattern 2: Multi-MCP Coordination

Use when: workflows span multiple services.

```markdown
## Phase 1: Design Export (Figma MCP)
1. Export design assets from Figma
2. Generate design specifications
3. Create asset manifest

## Phase 2: Asset Storage (Drive MCP)
1. Create project folder in Drive
2. Upload all assets
3. Generate shareable links

## Phase 3: Task Creation (Linear MCP)
1. Create development tasks
2. Attach asset links to tasks
3. Assign to engineering team

## Phase 4: Notification (Slack MCP)
1. Post handoff summary to #engineering
2. Include asset links and task references
```

Key techniques:
- Clear phase separation
- Data passing between MCPs explicitly described
- Validation before moving to next phase
- MCP tool names use `ServerName:tool_name` format

## Pattern 3: Iterative Refinement

Use when: output quality improves with iteration.

```markdown
## Iterative Report Creation

### Initial Draft
1. Fetch data via MCP
2. Generate first draft
3. Save to temporary file

### Quality Check
Run: `python scripts/check_report.py`
Identify issues:
- Missing sections
- Inconsistent formatting
- Data validation errors

### Refinement Loop
1. Address each identified issue
2. Regenerate affected sections
3. Re-validate
4. Repeat until quality threshold met

### Finalization
1. Apply final formatting
2. Generate summary
3. Save final version
```

The feedback loop (`validate -> fix -> re-validate`) greatly improves output quality.

## Pattern 4: Context-Aware Tool Selection

Use when: same outcome, different tools depending on context.

```markdown
## Smart File Storage

### Decision Tree
1. Check file type and size
2. Determine best storage:
   - Large files (>10MB): cloud storage MCP
   - Collaborative docs: Notion/Docs MCP
   - Code files: GitHub MCP
   - Temporary files: local storage

### Execute Storage
Based on decision, call appropriate MCP tool.

### Provide Context
Explain to user why that storage was chosen.
```

## Pattern 5: Domain-Specific Intelligence

Use when: your skill adds specialized knowledge beyond tool access.

```markdown
## Payment Processing with Compliance

### Before Processing (Compliance Check)
1. Fetch transaction details via MCP
2. Apply compliance rules:
   - Check sanctions lists
   - Verify jurisdiction allowances
   - Assess risk level
3. Document compliance decision

### Processing
IF compliance passed:
  - Process transaction
ELSE:
  - Flag for review
  - Create compliance case

### Audit Trail
- Log all compliance checks
- Record processing decisions
```

## Pattern 6: Plan-Validate-Execute

Use when: complex operations where mistakes are costly.

```markdown
## Batch Update Workflow

### Step 1: Analyze
Run: `python scripts/analyze.py input.pdf`
Output: fields.json

### Step 2: Create Plan
Edit fields.json with intended changes

### Step 3: Validate Plan
Run: `python scripts/validate.py fields.json`
Fix any errors before proceeding.
Verbose error messages help: "Field 'signature_date' not found.
Available fields: customer_name, order_total, signature_date_signed"

### Step 4: Execute
Run: `python scripts/apply.py input.pdf fields.json output.pdf`

### Step 5: Verify
Run: `python scripts/verify.py output.pdf`
If verification fails, return to Step 2.
```

Why this works:
- Catches errors before changes are applied
- Machine-verifiable with scripts
- Reversible planning phase
- Clear debugging with specific error messages

## Pattern 7: Template Pattern

Provide templates for output format. Match strictness to needs:

### Strict (API responses, data formats)

```markdown
ALWAYS use this exact structure:

# [Analysis Title]

## Executive summary
[One-paragraph overview]

## Key findings
- Finding 1 with data
- Finding 2 with data

## Recommendations
1. Specific action
2. Specific action
```

### Flexible (when adaptation is useful)

```markdown
Sensible default format - adjust as needed:

# [Title]
## Summary
## Findings
## Recommendations
```

## Pattern 8: Examples Pattern

For output-quality-dependent skills, provide input/output pairs:

```markdown
## Commit message format

**Example 1:**
Input: Added user authentication with JWT tokens
Output:
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware

**Example 2:**
Input: Fixed bug where dates displayed incorrectly
Output:
fix(reports): correct date formatting in timezone conversion

Use UTC timestamps consistently across report generation
```

Examples communicate desired style better than descriptions alone.

## Progressive Disclosure Patterns

### High-Level Guide with References

```
SKILL.md:
  Quick start + overview
  Links to: FORMS.md, REFERENCE.md, EXAMPLES.md
```

Claude loads each file only when needed.

### Domain-Specific Organization

```
bigquery-skill/
├── SKILL.md (overview and navigation)
└── reference/
    ├── finance.md (revenue, billing)
    ├── sales.md (pipeline, accounts)
    └── product.md (API usage, features)
```

When user asks about revenue, Claude reads only finance.md.

### Conditional Details

```markdown
## Creating documents
Use docx-js. See [DOCX-JS.md](DOCX-JS.md).

## Editing documents
For simple edits, modify XML directly.
**For tracked changes**: See [REDLINING.md](REDLINING.md)
```

## Skills + MCP Integration

MCP provides **tool access** (what Claude can do). Skills provide **workflow knowledge** (how Claude should do it).

Without skills: users connect MCP but don't know optimal workflows, each conversation starts from scratch, inconsistent results.

With skills: pre-built workflows activate automatically, consistent tool usage, best practices embedded.

When referencing MCP tools in skills, use fully qualified names:

```markdown
Use the BigQuery:bigquery_schema tool to retrieve schemas.
Use the GitHub:create_issue tool to create issues.
```

## Skills + Subagents Integration

Skills and subagents complement each other:

- **Skills**: portable expertise any agent can load
- **Subagents**: independent task execution with own context

Use together: a code-review subagent loads language-specific best practice skills.

In Claude Code, use `context: fork` in frontmatter to run a skill in an isolated subagent:

```yaml
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
---

Research $ARGUMENTS thoroughly:
1. Find relevant files using Glob and Grep
2. Read and analyze the code
3. Summarize findings with file references
```
