# Skill Card

## Description

command-skill-creator creates automation command skills (slash commands) for Claude Code projects - imperative, phased-execution prompts that automate workflows like deploys, commits, releases, and migrations. It walks through intent capture, frontmatter design, phase structuring, safety gates, and a final audit checklist.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Claude Code users who want to turn a repeatable multi-step workflow into an explicit /slash-command with approval gates - e.g. "turn this deploy process into a command" - rather than a passive knowledge skill.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: No
Credential Type(s): None

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Dependencies:
- Claude Code (skills are written to the target project's .claude/skills/ directory)

## Known Risks and Mitigations

Risk: The command skills this skill produces automate side-effectful actions (deploys, commits, file mutations); a poorly designed command could let the model trigger them autonomously.

Mitigation: The skill mandates disable-model-invocation: true for all command skills, approval gates before irreversible phases, and explicit error-handling instructions; its audit checklist must pass before finalizing.

Risk: Generated commands may embed hardcoded absolute paths or environment assumptions that break or misfire on other machines.

Mitigation: The audit checklist forbids hardcoded paths and requires ${CLAUDE_PROJECT_DIR}/${CLAUDE_SKILL_DIR} variables and adaptive discovery; review the generated SKILL.md before first use.

Risk: Writing into a target project's .claude/skills/ modifies that repository.

Mitigation: The creation workflow presents the skill content and audit results to the user before placement; users review before committing.

## References

- Claude Code skills documentation (frontmatter fields, $ARGUMENTS, path variables)
- Source: https://github.com/tenequm/skills/tree/main/skills/command-skill-creator

## Skill Output

Output type(s): Files - a complete SKILL.md (plus optional supporting files) for a new command skill, and an audit report

Output format: Markdown with YAML frontmatter, placed at <project>/.claude/skills/<command-name>/SKILL.md

Output parameters: Frontmatter fields per the skill's reference table (name, description, disable-model-invocation, argument-hint, allowed-tools, model, context, agent); SKILL.md kept under 200 lines

Other properties: The 12-item audit checklist must pass before a generated command is finalized

## Skill Version

0.1.2

## Ethical Considerations

Command skills automate actions with real side effects; humans should review every generated command and keep approval gates in place before running it against production systems.
