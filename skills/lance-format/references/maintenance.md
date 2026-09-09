# Maintaining this skill

Citations across the reference files are `path:line` relative to the `lance-format/lance` repo;
build a permalink as `https://github.com/lance-format/lance/blob/v12.0.0-beta.15/<path>`. Line
numbers drift between tags - treat them as approximate.

To refresh: `git -C <your lance-format/lance clone> fetch --tags`, then read the newest tag (the
major may have jumped again - the release train re-roots on any `breaking-change` label, and it
has now fired on **three consecutive lines**, so sort tags by date rather than assuming the
current major, and do not assume an intermediate `.1` line ever got a final or even a beta tag).

Three traps worth knowing before you start:

- **The `breaking-change` label is a floor, not a ceiling.** It drives the release bot, so it is
  the right query for "did the major re-root" - but it does **not** enumerate what will break a
  consumer. The `v12.0.0-beta.6 -> beta.15` range is the worked example: exactly two labeled PRs,
  while the two changes most likely to bite (`stable` resolving to 2.2, #8657; the IVF_RQ 5-bit
  default, #8936) carried a conventional-commit `!` and no label. **Always also scan the range for
  `!` commits** (`git log --oneline <a>..<b> | grep '!'`) and diff the defaults you already
  document - version enums, `*_DEFAULT_*` consts, and the sizing formulas in
  `docs/src/guide/performance.md`.
- **A final is not on `main`.** Finals are cut on stabilization branches, so
  `git merge-base --is-ancestor <final> main` returns false for a perfectly official release.
  Check GitHub Releases / crates.io / PyPI to identify the stable pin, not ancestry.
- **You do not need to move `HEAD` to read a tag.** `git show <tag>:<path>`,
  `git grep <pattern> <tag> -- <path>`, `git diff <tagA> <tagB> -- <path>` and
  `git ls-tree -r <tag>` are all read-only, which matters when the clone is shared. Note that a
  `blob:none` partial clone cannot always produce arbitrary historical diffs (`git log -S` may
  fail on absent blobs); tag-to-tag reads of present files still work.

Then:

1. Re-copy the docs mirror: the `.md` files of `docs/src/{guide,quickstart}`,
   `docs/src/format` (plus the `format/index/*.svg` diagrams), and
   `docs/src/integrations/datafusion.md` into `references/docs/`, preserving the tree.
   Update the directory counts in `SKILL.md` if docs were added or removed. **Three** deviations
   from upstream bytes are expected and enforced by this repo's pre-commit hooks, not drift:
   trailing whitespace is stripped from every file; `end-of-file-fixer` removes the trailing
   blank line that `format/table/layout.md` and `format/table/row_id_lineage.md` carry upstream;
   and the same hook *adds* a trailing newline to **all four** `.drawio.svg` diagrams, each of
   which is therefore one byte larger in the mirror than upstream (`indices-compaction`
   51381 -> 51382, `scalar_index` 8210 -> 8211, `starter-example` 14622 -> 14623,
   `indices-fragment handling` 21856 -> 21857).
   Normalize all three before diffing the mirror against a new tag. In practice both
   normalizations reduce to: strip trailing whitespace from every line, then force exactly one
   trailing newline on every file - applying that to a fresh `git archive` of `docs/src`
   reproduces the committed mirror byte-for-byte.
2. Re-check Part A of `references/performance.md` against the new `guide/performance.md` and the
   other perf-bearing sections it routes to. Part A deliberately does **not** copy that text -
   it points at `references/docs/`, so a mirror refresh updates it automatically; what needs
   hand-editing is the provenance note (which tags the guide is byte-unchanged across) and the
   two source-derived "Performance changes not in the guide" subsections. Part B (field-verified
   practices) is experience-derived - only edit it with new *measured* results, never
   speculation.
3. Re-verify the crate workspace and re-read the format spec for the reference files
   (`format-file.md`, `format-table.md`, `indexes.md`, `ops.md`, `changelog-v7-v12.md`), then
   bump `metadata.upstream` plus every current-tag version reference. `lance-reference.md` is
   only the section-number index - update it if the split changes.

## Reference file layout

`references/lance-reference.md` maps the original 16 section numbers onto five files:

| Sections | File |
|----------|------|
| 1-4 (what Lance is, crates, file format, data types) | `format-file.md` |
| 5-10 (table format, schema evolution, versioning, row IDs, transactions, MemWAL) | `format-table.md` |
| 11-12 (indexes, distributed write/indexing) | `indexes.md` |
| 13, 15, 16 (object store, capability matrix, source map) | `ops.md` |
| 14 (v7 -> v12 delta) | `changelog-v7-v12.md` |

Cross-references inside those files are written as "section N" against the original numbering,
so the index file must stay in sync with any re-split.
