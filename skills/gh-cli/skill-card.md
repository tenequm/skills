# Skill Card

## Description

gh-cli teaches use of the GitHub CLI (gh) for remote repository analysis, file fetching, codebase comparison, and code/repo discovery without cloning - plus PR, issue, Actions, and release workflows.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Developers and agents analyzing GitHub repositories remotely: fetching files, comparing codebases, searching code, finding trending projects, and managing issues/PRs/releases from the terminal without cloning.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: Yes
Credential Type(s): GitHub CLI auth (gh auth login) or a GH_TOKEN/GITHUB_TOKEN personal access token; GH_HOST for GitHub Enterprise.

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Tools/CLIs the skill instructs the agent to use: gh (GitHub CLI, installable via the Homebrew gh formula), plus standard shell utilities (base64, jq-style --jq filters built into gh).

## Known Risks and Mitigations

Risk: The skill may run gh commands that create, edit, close, or revert issues/PRs/releases on real repositories; mutating commands executed against the wrong repo cause visible damage.

Mitigation: Review mutating commands before execution and pin the target with --repo OWNER/REPO (the skill explicitly instructs this so a stray cwd cannot retarget commands).

Risk: The authenticated token grants whatever scopes it carries; an over-scoped GH_TOKEN lets the agent push, delete, or administer repositories beyond the analysis tasks this skill covers.

Mitigation: Use least-privilege (read-mostly, fine-grained) tokens for analysis workflows and separate tokens for write operations.

Risk: Search and API commands consume tight rate limits (30/min search, 10/min code search); loops can exhaust them and block other tooling.

Mitigation: Follow the skill's rate-limit table, check gh api rate_limit, and use --cache for repeated fetches.

## References

- GitHub CLI: https://github.com/cli/cli (tracked upstream: gh 2.96.0)
- Official manual: https://cli.github.com/manual/
- Search syntax: https://docs.github.com/en/search-github
- Source: https://github.com/tenequm/skills/tree/main/skills/gh-cli

## Skill Output

Output type(s): Executed gh command output - fetched file contents, directory listings, search results, comparison analyses, and issue/PR/release operation results.

Output format: Terminal text, JSON (via --json/--jq), and Markdown summaries.

Output parameters: Field names differ between commands (e.g. stargazerCount vs stargazersCount) as documented in the skill; otherwise not applicable.

Other properties: Read operations are side-effect free; PR/issue/release commands mutate remote state; API calls consume GitHub rate limits.

## Skill Version

1.3.1

## Ethical Considerations

The skill operates on real repositories with a user's GitHub identity; mutating actions (comments, PRs, releases) are attributed to that user and should be human-reviewed. Code discovery should respect upstream licenses when reusing fetched code.
