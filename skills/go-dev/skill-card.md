# Skill Card

## Description

go-dev provides an opinionated Go development setup - golangci-lint v2, gofumpt, gotestsum, golang-migrate, and just - for developers starting new Go projects or unifying linting, formatting, testing, and CI tooling. It includes ready-to-copy configs (.golangci.yml, Justfile, lefthook.yml, GitHub Actions) and a migration path for existing projects.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Go developers scaffolding a new service or library, replacing Makefile-and-scattered-tools workflows with a unified just-based setup, adding database migration tooling, or standing up a lint/test/security CI pipeline on GitHub Actions.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: No
Credential Type(s): None (DATABASE_URL is needed at runtime for migration recipes, but is project infrastructure, not a skill credential)

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Dependencies:
- Go 1.26+
- golangci-lint v2.11+, gofumpt v0.9+, gotestsum v1.13+, golang-migrate v4.19+
- just (task runner), lefthook (git hooks), govulncheck
- Environment variable (declared in metadata.openclaw envVars, optional): DATABASE_URL - connection string for the Justfile migration recipes

No requires.bins gate is declared: this is a dev-setup skill whose purpose is installing these tools, so it must stay visible to users who have not installed them yet.

## Known Risks and Mitigations

Risk: The skill drives go install commands, git hook installation (lefthook), and auto-fixing lint/format runs that modify source files in place.

Mitigation: Run formatters and --fix lint passes on a clean git worktree so changes are reviewable; hooks are opt-in via lefthook install.

Risk: Database migration recipes (migrate up/down against $DATABASE_URL) can alter or destroy schema state if pointed at the wrong database.

Mitigation: The Justfile reads DATABASE_URL from the environment/.env per project; verify the target database and keep down-migrations tested before running against shared environments.

Risk: Pinned tool versions and config syntax (golangci-lint v2 schema, action versions) drift as upstream releases; stale configs may fail or silently skip linters.

Mitigation: The stack table records minimum verified versions and the skill includes golangci-lint migrate for config upgrades; cross-check golangci-lint.run docs when versions advance.

## References

- golangci-lint: https://golangci-lint.run/
- gofumpt: https://github.com/mvdan/gofumpt
- gotestsum: https://github.com/gotestyourself/gotestsum
- golang-migrate: https://github.com/golang-migrate/migrate
- just: https://github.com/casey/just
- Source: https://github.com/tenequm/skills/tree/main/skills/go-dev

## Skill Output

Output type(s): Code and files - project scaffolding, tool configuration files, CI pipeline definitions, shell commands

Output format: YAML (.golangci.yml, lefthook.yml, GitHub Actions), Justfile syntax, Go project layout, bash commands

Output parameters: Standard layout (cmd/, internal/, migrations/, testdata/); CI gate is just check (fmt-check + lint + test)

Other properties: Commands install Go tools into the local toolchain and may rewrite source files during formatting/lint-fix

## Skill Version

0.2.2

## Ethical Considerations

Generated configurations and CI pipelines should be reviewed by a human before adoption in production repositories, particularly database migration commands and git hooks that act automatically on future commits.
