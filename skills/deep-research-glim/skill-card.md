# Skill Card

## Description

deep-research-glim conducts deep, multi-angle research through the glim MCP tool suite and parallel subagents: staged discovery, targeted deep dives, coverage validation, cross-source analysis, and a synthesized report with cited sources.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Anyone needing strategic intelligence on a topic - competitive landscape analysis, technology deep dives, market or community sentiment - with cross-source validation rather than a single-pass search. Invoked as /deep-research-glim [topic] or via deep-research trigger phrases.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: Yes
Credential Type(s): A configured glim MCP server (https://glim.sh). glim is a paid service billed per tool call via x402 USDC (Solana/Base) or MPP (Tempo); the payment credential lives in the MCP server configuration, not in this skill.

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

The skill drives glim MCP tools exclusively (mcp__glim__* - web search, web fetch/crawl, GitHub, Reddit, Twitter/X, Amazon, YouTube transcripts) plus the agent's own Task tool for parallel subagents. It uses no CLI binaries; there is deliberately no requires block in the openclaw metadata.

## Known Risks and Mitigations

Risk: The skill sends search queries and fetched page content through the paid glim MCP service; confidential material included in a research topic or seed context leaves the local environment.

Mitigation: Do not include confidential or personal material in research queries; scope topics to publicly researchable questions.

Risk: Each run fans out to 3+ subagents issuing many glim calls (Stage 1 alone runs 10+ searches), and glim bills per call, so a broad topic can accumulate real cost.

Mitigation: The skill's context-engineering and progressive-disclosure principles cap search depth to task needs, and Stage 2 dive count (N) is a deliberate judgment call; users can narrow the topic before fan-out.

Risk: Synthesized findings can overweight low-quality web sources or smooth over disagreements.

Mitigation: The workflow mandates cross-validation (each key finding cited from 2+ sources), an explicit contradictions section, speculation flagged separately from evidence, and a red-team checkpoint before delivery.

## References

- glim MCP suite (https://glim.sh) - the tool layer the skill drives; the skill tracks no versioned upstream package
- Source: https://github.com/tenequm/skills/tree/main/skills/deep-research-glim

## Skill Output

Output type(s): A structured research report synthesizing multi-source findings.

Output format: Markdown with a fixed section structure (Executive Summary, Key Findings, Unique Insights, Contradictions and Nuances, Strategic Insights, Key Metrics to Track, Sources) and clickable source links.

Output parameters: Report headings are fixed by the Stage 5 template; findings are organized thematically with per-theme citations.

Other properties: Spawns parallel background subagents; incurs per-call glim service costs; plain hyphens only in output by design.

## Skill Version

0.2.6

## Ethical Considerations

Research output aggregates public web, social, and code sources; users should respect the terms of the underlying platforms and verify claims before acting on them. Queries transit a paid third-party service, so sensitive topics should not be researched through it.
