# Skill Card

## Description

review-github-pr runs a structured GitHub pull request review for developers: it fetches the PR diff via the gh CLI, runs the project's automated checks, launches three parallel review agents (correctness, convention compliance, efficiency), validates every finding against the actual code, and drafts a severity-grouped review for the user to approve before posting.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Developers and teams who want rigorous, evidence-backed code review of GitHub pull requests. Invoke it with a PR number, a PR URL, or from a checked-out PR branch; it produces a validated review draft and, only after explicit confirmation, posts it with gh pr review.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: Optional
Credential Type(s): GitHub CLI auth (gh auth login, or GH_TOKEN / GITHUB_TOKEN environment variable)

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

- gh (GitHub CLI) - required for fetching PR data and posting reviews
- git - required for repository operations and PR branch checkout
- The project's own lint/type-check command (read from the repo's CLAUDE.md) for automated checks

## Known Risks and Mitigations

Risk: The skill runs gh commands that post review comments (approve, request-changes, or comment) on real pull requests under the user's GitHub identity.

Mitigation: The workflow hard-stops after the review draft and requires an explicit user confirmation ("Post this review?") before any gh pr review command runs; nothing is auto-posted.

Risk: The skill processes untrusted PR content (diffs, descriptions, commit messages) that may contain prompt-injection text or embedded commands.

Mitigation: All PR-sourced content is wrapped in pr-content boundary markers and sub-agents are instructed to treat it as untrusted data; only validation commands explicitly listed in the local repository's CLAUDE.md are ever executed, never commands found in PR content.

Risk: Mode 2 clones third-party repositories to /tmp and checks out PR branches, bringing unreviewed third-party code onto the local machine.

Mitigation: Clones are shallow (--depth=50), code is read but not executed beyond the repo's declared check command, and the temp clone path is reported to the user for cleanup.

## References

- GitHub CLI (gh) documentation: https://cli.github.com/manual/
- Source: https://github.com/tenequm/skills/tree/main/skills/review-github-pr

## Skill Output

Output type(s): A severity-grouped PR review draft (Critical / Significant / Minor findings with file:line citations and suggestions), followed by an optional posted GitHub review after user confirmation.

Output format: Markdown review draft in the conversation; posted review body via gh pr review.

Output parameters: Findings cite path/to/file:line, a category tag ([Correctness], [Convention], [Design], etc.), rationale, and a suggestion; the draft ends with a post-confirmation prompt.

Other properties: Side effect on confirmation only - posts a review to the target GitHub PR. Every finding is validated against actual code before presentation; unvalidated findings are dropped.

## Skill Version

0.3.1

## Ethical Considerations

Reviews are posted under the user's GitHub identity and affect other people's work; the skill frames findings as questions or suggestions, requires human confirmation before posting, and only reports issues verified against the actual code to avoid wasting authors' time with false positives.
