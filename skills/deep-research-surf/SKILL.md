---
name: deep-research-surf
description: Conducts deep, multi-angle research using Surf MCP tools and parallel subagents. Use for deep research, competitive landscape analysis, strategic intelligence, or /deep-research-surf [topic]. Triggers - deep research, deep dive on, competitive landscape, strategic intelligence, multi-source synthesis.
metadata:
  version: "0.2.1"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/deep-research-surf
    emoji: "🔭"
---

# Deep Research (Surf)

You are conducting deep, multi-angle research using the Surf MCP suite and parallel subagents. The goal is strategic intelligence with cross-source validation, evidence-rich findings, and orthogonal insights that single-pass searches miss.

Invocation pattern: `/deep-research-surf [topic]` or any of the trigger phrases in the description. The user may also pass an explicit `[topic]` argument; if absent, ask once before fanning out.

## Tool policy

Always prefer Surf MCP tools (`mcp__surf__*`) over `WebSearch` or `WebFetch`, both for yourself and for every subagent you spawn. Surf primitives cover web search, web crawl, GitHub, Reddit, Twitter / X, Amazon, and YouTube subtitles. Read each tool's schema at invocation time for current parameters and capabilities.

## Core Principles

- **Context engineering**: smaller context budgets for broad scanning, larger budgets for critical deep dives.
- **Search depth control**: match search depth to the task - quick scan for landscape mapping, comprehensive search for authoritative sources.
- **Progressive disclosure**: start broad and light, identify key sources, then deep-dive only where it pays off.
- **Synthesis over summarization**: extract cross-source patterns and actionable insights, not sequential source descriptions.
- **Explicit novelty seeking**: actively search for contrarian views, unique angles, and lesser-known insights that complement mainstream findings.
- **Plain hyphens only**: no emdashes, en-dashes, em-dashes, or `--`. Use `-` everywhere in output.

## Execution

### Stage 0: Topic Assessment & Source Planning

Before spawning anything, internally commit to a one-paragraph plan covering:

1. **What is the actual question?** Restate the topic in your own words. If ambiguous, identify 2-3 interpretations and pick the most useful, or ask the user once.
2. **Where should we look?** Available Surf primitives: web (search + crawl), GitHub, Reddit, Twitter / X, Amazon, YouTube subtitles. Pick whichever fit the topic.
3. **What is already known?** If the user provided context (a doc, prior conversation, design file), read it first. Subagents must know what NOT to repeat.

### Stage 1: Multi-Angle Discovery (always 3 parallel subagents)

Spawn three subagents in parallel via the Task tool (`subagent_type=general-purpose`, `run_in_background=true`). Each gets a distinct angle.

#### Subagent 1A: Broad Overview

Mission: establish baseline; identify themes, key players, dominant narrative.

Searches: 2-3 broad queries via Surf web search.

Sample queries:
- `"[topic] overview 2025-2026"`
- `"[topic] comprehensive guide"`
- `"what is [topic] how it works"`

Returns: themes, key players, 2-3 areas requiring deep dives, source URLs.

#### Subagent 1B: Diversified Perspectives

Mission: cover technical, user, comparative, leadership, and critical angles with balanced context.

Searches: 6-8 queries across categories via Surf web search. Reach for Surf GitHub, Reddit, or Twitter primitives where the topic warrants.

Query categories (one or two queries each):
- Technical / implementation: `"[topic] architecture design patterns"`, `"[topic] technical deep dive engineering"`
- User / community: `"[topic] developer experience feedback"`, `"[topic] user testimonials reviews"`
- Comparative: `"[topic] vs [alternatives] comparison benchmarks"`, `"[topic] alternatives competitors"`
- Case studies: `"[topic] case studies customer success stories"`, `"[topic] real-world use cases"`
- Leadership / strategy: `"[topic] founder interview CEO strategy"`, `"[topic] company blog announcements"`
- Critical: `"[topic] limitations problems challenges"`, `"[topic] criticism drawbacks cons"`

Returns: per-category findings with URLs, quotes, data points.

#### Subagent 1C: Novelty & Trend Search

Mission: contrarian views, lesser-known strategies, emerging signals.

Searches: 2-3 queries via Surf web search. Reddit and X are often where contrarian opinions live.

Sample queries:
- `"[topic] contrarian opinions different perspective"`
- `"[topic] lesser-known strategies hidden tactics"`
- `"[topic] emerging trends future directions 2026"`

Returns: orthogonal insights, contrarian views, emerging signals.

#### Stage 1 contract

Each subagent returns structured findings under 1500 words containing: themes, evidence (quotes, data, dates), source URLs as clickable markdown links, unique angles. Wait for all three before Stage 2.

### Stage 2: Critical Deep Dives (dynamic N parallel subagents)

After Stage 1 returns, evaluate the aggregated findings. Identify the critical sources or angles that warrant full content extraction:

- Founder / CEO interviews with strategic insight
- Comprehensive case studies with metrics
- Technical deep-dives requiring full context
- Primary sources with unique data
- Specific GitHub repos worth deep audit (README + commits + issues)
- Reddit threads with high-signal discussion
- YouTube videos whose transcripts hold unique content

Decide N based on what Stage 1 surfaced. N is your judgment - could be 2, could be 6. Spawn N subagents in parallel via the Task tool, one per critical source or angle. Each uses the appropriate Surf detail primitive (web crawl, GitHub get, Reddit post, Twitter tweet, YouTube subtitles) for full-content extraction.

Each Stage 2 subagent returns: full extracted content, key quotes, data points, why this source matters.

### Stage 3: Coverage Validation

Run the gap-detection checklist on the aggregated Stage 1 + Stage 2 corpus:

- [ ] Growth metrics / trajectory data
- [ ] Founder / leadership perspectives
- [ ] User testimonials / community feedback
- [ ] Critical / contrarian views
- [ ] Technical implementation details (not just strategy)
- [ ] Specific examples with numbers, dates, quotes
- [ ] Historical context (how did this evolve)
- [ ] Competitive landscape understood

If a critical gap exists:
- Small / fillable solo: run 1-2 targeted Surf searches yourself
- Large / requires distinct angle: spawn an additional subagent

If no critical gap, proceed to Stage 4.

### Stage 4: Cross-Source Analysis (solo)

Analyze the full corpus:

1. **Pattern identification**: themes that repeat across multiple sources
2. **Evidence quality**: claims backed by concrete data versus speculation
3. **Contradiction detection**: where sources disagree, why
4. **Unique insight extraction**: what only ONE source mentioned that is valuable
5. **Triangulation**: which key claims validate across 2+ independent sources

Extract:
- Specific quotes that capture key insights
- Data points, metrics, timelines, growth numbers
- Causal relationships (X led to Y because Z)
- Unsupported speculation flagged separately from evidence-backed claims
- Orthogonal insights highlighted

### Stage 5: Synthesis & Report (solo)

Output the synthesis using exactly this structure:

```markdown
# [Research Topic Title]

## Executive Summary

2-3 paragraphs directly answering the core research question:
- What is the definitive answer?
- What are the 3-5 most important takeaways?
- What makes this topic significant or unique?

## Key Findings

Organize thematically (NOT source-by-source) with cross-source validation.

### 1. [Theme Name] - [One-line insight]

Evidence:
- [Specific finding from Source A with quote/data]
- [Corroborating evidence from Source B]
- [Unique angle from Source C]

Source citations: [Source A](url), [Source B](url)

### 2. [Theme Name] - [One-line insight]
[Repeat pattern]

### 3-6. [Additional themes...]

## Unique Insights (Orthogonal Findings)

Findings that appeared in only 1-2 sources but provide valuable perspective:
- **[Insight 1]**: [Description with citation]
- **[Insight 2]**: [Description with citation]

## Contradictions & Nuances

Where sources disagree or context matters:
- **[Topic]**: Source A claims X, but Source B argues Y because Z
- **[Topic]**: Common misconception is X, but evidence suggests Y

## Strategic Insights

Actionable recommendations based on synthesis.

### What to Replicate
- [Pattern with reasoning]

### What to Adapt (Not Copy Blindly)
- [Approach with context-specific considerations]

### Differentiation Opportunities
- [Angle: how to do this differently or better]
- [White space not addressed by existing solutions]

## Key Metrics to Track

Based on research, what should be measured:
1. [Metric - why it matters]
2. [Metric - why it matters]

## Sources

Organized by type with one-line annotation.

**Primary Sources:**
- [Source 1](url) - Why valuable: [one-line]

**Analytical Sources:**
- [Source 2](url) - Why valuable: [one-line]

**User / Community Sources:**
- [Source 3](url) - Why valuable: [one-line]
```

Quality checklist before delivering:
- Each key finding cites 2+ sources (cross-validation)
- Contradictions explicitly noted, not smoothed over
- Unique insights called out separately
- Specific examples include numbers, dates, quotes, names
- Patterns extracted ACROSS sources, not sequential summaries
- Sources annotated with why each was valuable
- Recommendations are specific, not generic

## Meta-cognition checkpoints

Throughout the run, ask yourself:
- Have I explored diverse source types? (Primary, user, analytical, critical)
- Did I find contrarian views? (Novelty Stage 1C should have surfaced these)
- Can I validate major claims across 2+ sources?
- Have I identified the critical sources worth deep crawls in Stage 2?
- What would someone who disagrees with my synthesis argue? Red-team the conclusion before delivering.
