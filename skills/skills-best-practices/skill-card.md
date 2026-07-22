# Skill Card

## Description

skills-best-practices is a reference guide for building high-quality Agent Skills following Anthropic's official guidelines, covering SKILL.md structure, frontmatter, description writing, progressive disclosure, testing, distribution, and ClawHub publishing.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Skill authors creating a new Agent Skill, reviewing an existing skill's quality, debugging why a skill won't trigger, or preparing a skill for publishing to a registry such as ClawHub. Pure knowledge reference - it changes how the agent writes and structures skill files, nothing else.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: No
Credential Type(s): None

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

- No required tools or credentials. Optionally suggests running the spec validator via `uvx --from skills-ref agentskills validate` when the user wants pre-publish validation.

## Known Risks and Mitigations

Risk: Guidance could become stale as the Agent Skills spec, Claude Code frontmatter fields, or ClawHub moderation rules evolve, leading authors to publish skills that fail validation.

Mitigation: The skill tracks upstream docs via a per-skill CHANGELOG and recommends running the official agentskills validator locally before publishing, so stale advice is caught by the validation gate.

Risk: The skill documents the Claude Code dynamic-injection syntax (a `!` prefix on backticked commands), which the loader executes even inside code fences; a careless copy of such an example into a new skill could run shell commands on load.

Mitigation: The skill explicitly warns about this hazard in its Security section and instructs authors to keep such examples in references/ files or break the `!`-backtick adjacency.

## References

- Agent Skills Spec: https://agentskills.io/specification
- Claude Code Skills Docs: https://code.claude.com/docs/en/skills
- Anthropic Skills Repo: https://github.com/anthropics/skills
- ClawHub docs (skill-format, security-audits, moderation): https://github.com/openclaw/clawhub/tree/main/docs
- Source: https://github.com/tenequm/skills/tree/main/skills/skills-best-practices

## Skill Output

Output type(s): Advice, reviews, and concrete edits to skill files (SKILL.md frontmatter and body, references/ layout, descriptions) produced while the agent creates or improves a skill.

Output format: Markdown guidance and YAML/Markdown skill file content.

Output parameters: Not applicable

Other properties: No side effects; the skill itself executes nothing and requires no network access.

## Skill Version

0.6.3

## Ethical Considerations

The skill teaches authors to write accurate skill metadata and descriptions rather than misleading ones, and highlights security-relevant practices (no injection-prone frontmatter, auditing bundled scripts, declaring credentials honestly) that protect downstream users who install published skills.
