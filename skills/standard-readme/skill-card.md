# Skill Card

## Description

standard-readme writes or audits README.md files against the Standard Readme specification for any software repository. It enforces the spec's exact section order, required sections, and formatting rules in both a write mode and an audit mode.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Maintainers and contributors who want a spec-compliant README: generating one for a new repo, rewriting an existing one, or getting a severity-grouped audit of an existing README without a rewrite. The agent derives project facts (name, install command, license) from the repo's own files rather than asking the user.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: No
Credential Type(s): None

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

No external tools, CLIs, or packages; the skill only reads project files and writes Markdown.

## Known Risks and Mitigations

Risk: Write mode replaces an existing README.md, which can drop project-specific content that does not map onto the spec's sections.

Mitigation: The spec's Extra Sections slot preserves custom content, and the audit mode offers a report-only path; users should diff the rewrite against the original before committing.

Risk: Generated install/usage examples or license statements may not match the project's real CLI, API, or LICENSE file if the repository context is incomplete or misread.

Mitigation: The workflow requires deriving all facts from actual project files (package manifests, LICENSE, source) and self-checking before presenting; users should still verify code examples run and the stated license matches.

## References

- Standard Readme specification: https://github.com/RichardLitt/standard-readme
- Source: https://github.com/tenequm/skills/tree/main/skills/standard-readme

## Skill Output

Output type(s): A complete README.md (write mode) or a severity-grouped compliance report (audit mode).

Output format: Markdown; audit findings as a numbered list grouped into Must fix / Should fix / Suggestions.

Output parameters: README sections follow the Standard Readme fixed order (Title through License), with required-section and formatting rules as defined in SKILL.md.

Other properties: Write mode overwrites README.md only when the user asks for the file to be written; no network access needed.

## Skill Version

0.1.2

## Ethical Considerations

A rewritten README speaks for the project, so maintainers should review it for accuracy (claims, examples, license) before publishing. The skill avoids inventing package names or commands, but final responsibility for published documentation stays with the human.
