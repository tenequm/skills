# Skill Card

## Description

lance-format is a deep reference for Lance v9 - the open columnar lakehouse format for multimodal AI - and its Rust crate workspace: file/table formats, structural encodings, vector/scalar/full-text indexes, transactions, MemWAL, namespaces, and object-store configuration.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Engineers building directly on the Lance crates or pylance: creating/reading .lance datasets, choosing file-format versions and encodings, designing indexes, handling optimistic-concurrency commits, schema evolution, time travel, and tuning performance against local or S3-compatible object storage.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: No
Credential Type(s): None. (Workflows targeting cloud object stores use the user's own storage credentials, configured outside this skill.)

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Tools/packages the skill documents: the lance / lance-* Rust crates (Cargo), pylance (Python 3.10+), and integrations with DuckDB, Polars, Ray, Spark, and DataFusion. No CLI binaries or env vars are required to use the reference.

## Known Risks and Mitigations

Risk: The skill documents destructive maintenance operations (cleanup_old_versions, compaction, dataset rewrites) that permanently delete historical versions and data files if applied to production datasets.

Mitigation: Verify retention requirements and tags/branches before cleanup; test maintenance flows on a copy of the dataset first.

Risk: The skill covers unstable format features (file format 2.2/2.3, Data Overlay Files, MemWAL) whose on-disk encodings can change between beta tags; datasets written with them may become unreadable by other Lance versions.

Mitigation: The skill explicitly instructs pinning concrete release tags (v8.0.0 for stable) and using explicit format version numbers rather than the floating next alias.

Risk: Misapplied performance tuning against remote object storage can multiply request costs and latency.

Mitigation: The skill's performance reference mandates leaving store knobs at defaults and minimizing remote calls, based on measured results only.

## References

- Upstream: https://github.com/lance-format/lance (tracked tag: v9.1.0-beta.8)
- Official docs (mirrored verbatim in references/docs/): Lance docs at the tracked tag
- Source: https://github.com/tenequm/skills/tree/main/skills/lance-format

## Skill Output

Output type(s): Rust and Python code using the Lance crates/pylance, format and schema explanations, index and performance recommendations grounded in the mirrored official docs.

Output format: Markdown with Rust/Python/SQL code blocks.

Output parameters: Citations reference path:line in the lance-format/lance repo at the tracked tag; permalinks built as https://github.com/lance-format/lance/blob/v9.1.0-beta.8/<path>.

Other properties: Reference-only skill - it performs no I/O itself; code it produces can create, modify, or delete datasets when executed by the user.

## Skill Version

0.11.1

## Ethical Considerations

The skill is a technical reference with no credential handling; the main duty of care is accuracy - guidance is pinned to a specific upstream tag and performance claims are restricted to benchmark-verified results so users do not make costly storage decisions on speculation.
