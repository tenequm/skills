# Skill Linting

This repository validates skills in two layers:

1. Official Agent Skills validation via the reference library
2. Repository policy validation inside `scripts/check_skills.py`

## Official validation

CI runs the official validator from the Agent Skills reference library:

```bash
uvx --from skills-ref agentskills validate skills/<slug>
```

This checks `SKILL.md` format against the open Agent Skills spec.

## Repository policy validation

The local linter enforces repository-specific rules that are not part of the base spec:

- `metadata.version` must exist and be a non-empty string
- `name` must match the parent directory
- `SKILL.md` must have a non-empty body
- `SKILL.md` should stay under 500 lines
- `metadata` values must be strings

Run the full local gate with:

```bash
just check
```

## Why both exist

The official validator gives you spec compliance.

The local linter gives you release and repository hygiene. In this repo, release automation depends on explicit skill versioning, so `metadata.version` is mandatory even though `metadata` itself is optional in the base spec.
