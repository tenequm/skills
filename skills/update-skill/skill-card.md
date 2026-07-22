# Skill Card

## Description

update-skill runs a thorough on-demand refresh of one skill in a skills repository: parallel research across usage history, upstream releases, and canonical docs, followed by two human-approval gates, a version bump, CHANGELOG update, repo validation, and a gated commit/push with CI watch.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Maintainers of a skills repository who want a single skill refreshed against its upstream packages and docs without unreviewed edits or commits. Invoked explicitly as /update-skill [skill-name]; model auto-invocation is disabled.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: Optional
Credential Type(s): GitHub credentials for git push and the gh CLI (only at the final, human-approved commit/push phase). The pond MCP server (https://pond.cascade.fyi/) is optional; without it the prior-session usage research angle is skipped.

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Tools the skill instructs the agent to use: git (worktrees, commit, push), gh (PRs, CI watch), the repo's validation command (e.g. just check), and optionally the pond MCP server for prior-session mining.

## Known Risks and Mitigations

Risk: The workflow ends in a git commit and push that, in auto-publishing repos, ships the updated skill straight to a public registry.

Mitigation: Two hard approval gates - GATE 1 before any file edit and GATE 2 before any commit/push - require explicit affirmative replies; a branch guard asks before pushing to the default branch.

Risk: Research drawn from pond (private cross-project session history) could leak private hostnames, project names, or personal data into a public repository.

Mitigation: A dedicated privacy/leak scan runs on every diff and all new files before GATE 2; any [LEAK] finding is a hard blocker until redacted, and scope-checking in the verification phase routes private-infrastructure learnings away from public skill content.

Risk: Unverified research findings (stale docs, hallucinated release notes) could be written into a skill as fact.

Mitigation: Ground-truth verification requires every proposed edit row to cite a primary source read the same day; pond findings are advisory-only until re-grounded.

## References

- Keep a Changelog 2.0.0 (https://keepachangelog.com/en/2.0.0/), tracked in metadata.upstream as keep-a-changelog@2.0.0
- pond MCP (https://pond.cascade.fyi/), optional research source
- Source: https://github.com/tenequm/skills/tree/main/skills/update-skill

## Skill Output

Output type(s): A structured research report (packages diff, proposed edits, coverage sweep), edits to the target skill's SKILL.md / references / CHANGELOG.md, a conventional-commit git commit, and optionally a pushed branch with a PR.

Output format: Markdown report in-conversation; file edits in Markdown/YAML; git commits.

Output parameters: Report sections are fixed (tracked packages diff, proposed upstream string, CHANGELOG entry, edit rows with stable IDs, coverage attestation); CHANGELOG entries follow Keep a Changelog 2.0.0.

Other properties: No edits before GATE 1 approval, no commits before GATE 2 approval; no-op runs exit with a verbatim "all current" statement and zero file changes.

## Skill Version

0.8.1

## Ethical Considerations

The skill is designed around explicit human consent for every mutation and includes a mandatory privacy scan to keep personal or private-infrastructure data out of public repositories. Users remain accountable for the content they approve at each gate.
