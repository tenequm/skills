# Skill Card

## Description

python-dev sets up an opinionated Python development stack (uv + ty + ruff + pytest + just) for new projects and for migrating existing projects off pip/poetry/mypy/black/flake8. It provides ready-to-copy pyproject.toml, Justfile, pre-commit, and CI templates.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Python developers starting a new project or modernizing an existing one who want a single, decided toolchain instead of evaluating package managers, linters, and type checkers themselves. The agent uses it to scaffold configuration, wire up linting/formatting/testing, and answer tooling questions from the bundled references.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: No
Credential Type(s): None

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Tools the skill instructs the agent to use: uv, ty, ruff, pytest, pytest-asyncio, pre-commit, just. None are required to read the skill; they are installed as part of following the setup guidance.

## Known Risks and Mitigations

Risk: The skill generates project scaffolding, pyproject.toml, Justfile, and pre-commit configs that can overwrite existing files in a project (especially during migration of an existing codebase).

Mitigation: Review generated files and shell commands before execution; run migrations on a clean git branch so changes are diffable and revertible.

Risk: Pinned tool versions in metadata.upstream and templates (uv, ty, ruff, pytest) go stale; ty in particular is beta (0.0.x) and may produce false positives on heavy-typing libraries.

Mitigation: The skill's CHANGELOG records when guidance was last verified; check current upstream releases before pinning versions in production, and swap ty for pyright where rock-solid type checking is needed (the skill documents this escape hatch).

Risk: The migration workflow removes existing dev dependencies (mypy, black, flake8, isort) via uv commands, which alters the project's lockfile and CI behavior.

Mitigation: Commit the pre-migration state first and run the project's test suite after migration before merging.

## References

- uv: https://docs.astral.sh/uv/
- ty: https://docs.astral.sh/ty/
- ruff: https://docs.astral.sh/ruff/
- pytest: https://docs.pytest.org/
- just: https://just.systems/
- Source: https://github.com/tenequm/skills/tree/main/skills/python-dev

## Skill Output

Output type(s): Project configuration files (pyproject.toml, Justfile, .pre-commit-config.yaml, GitHub Actions workflows), shell commands, and tooling guidance.

Output format: TOML, YAML, Justfile syntax, and shell code blocks in Markdown; files written into the user's project when requested.

Output parameters: Follows src-layout project structure (src/<package>/, tests/) and the templates embedded in SKILL.md.

Other properties: Commands invoke network-installing tools (uv add, pre-commit install); no telemetry or external calls by the skill itself.

## Skill Version

0.2.3

## Ethical Considerations

Generated configuration and migration commands modify real projects; users should review diffs and run tests before adopting them. The skill encodes opinionated tool choices, not neutral comparisons, and says so explicitly.
