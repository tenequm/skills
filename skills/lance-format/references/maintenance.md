# Maintaining this skill

Citations across the reference files are `path:line` relative to the `lance-format/lance` repo;
build a permalink as `https://github.com/lance-format/lance/blob/v14.0.0-beta.14/<path>`. Line
numbers drift between tags - treat them as approximate.

To refresh: `git -C <your lance-format/lance clone> fetch --tags`, then read the newest tag (the
major may have jumped again - the release train re-roots on any `breaking-change` label, and it
has now fired on **five consecutive lines**, so sort tags by date rather than assuming the
current major, and do not assume an intermediate `.1` line got a final; 12.1 never got a tag,
13.1 got two betas and was still abandoned). Check for a **final** too: `v13.0.0` shipped five
days before `v14.0.0-beta.14`, so the stable pin and the tracked frontier can both move in one
refresh. A final can also be the next line's release root plus a couple of release commits
(`v13.0.0` is `release-root/14.0.0-beta.N` + 2), so its delta and the next line's overlap
completely - do not double-count.

Traps worth knowing before you start:

- **The `breaking-change` label is a floor, not a ceiling.** It drives the release bot, so it is
  the right query for "did the major re-root" - but it does **not** enumerate what will break a
  consumer. Worked examples: in `v12.0.0-beta.6 -> beta.15` the two changes most likely to bite
  (`stable` resolving to 2.2, #8657; the IVF_RQ 5-bit default, #8936) carried a `!` and no label;
  in the v14 line the manifest-field move #9482 carried only `format-change`. **Always also scan
  the range for `!` commits** (`git log --oneline <a>..<b> | grep '!:'`), query the
  `format-change` label, and diff the defaults you already document - version enums,
  `*_DEFAULT_*` consts, and the sizing formulas in `docs/src/guide/performance.md`. The defaults
  diff is what caught `inline_optimization_enabled` flipping `true -> false` (#9180), which
  carried neither marker.
- **The spec pages can run ahead of the code.** At `v14.0.0-beta.14`, `format/table/versioning.md`
  lists bit 9 (FRI with stable row IDs) as reader/writer `Yes` and bit 13 (independent covering
  fields) as normative, and `guide/blob.md` says any Blob v2 write activates managed blobs (bit
  14) - while `rust/lance-table/src/feature_flags.rs` supports bit 9 only in debug builds, masks
  bit 13 out of `supported_flags_when`, and has required an explicit `lance.blob.managed` opt-in
  since #9891. When a doc table and a `const` disagree, **verify which one the build enforces**
  and record the split rather than copying the table. The previous example (bit 10, documented
  long before `v13.0.0` supported it) resolved in the code's favour once the code caught up.
- **A final is not on `main`.** Finals are cut on stabilization branches, so
  `git merge-base --is-ancestor <final> main` returns false for a perfectly official release.
  Check GitHub Releases / crates.io / PyPI to identify the stable pin, not ancestry.
- **You do not need to move `HEAD` to read a tag.** `git show <tag>:<path>`,
  `git grep <pattern> <tag> -- <path>`, `git diff <tagA> <tagB> -- <path>` and
  `git ls-tree -r <tag>` are all read-only, which matters when the clone is shared. In zsh, quote
  `"$T:path"` - an unquoted `$T:r...` is parsed as a history modifier. A `blob:none` partial
  clone cannot always produce arbitrary historical diffs (`git log -S` may fail on absent blobs);
  tag-to-tag reads of present files still work.

Then:

1. Re-copy the docs mirror: the `.md` files of `docs/src/{guide,quickstart}`, all of
   `docs/src/format` except `format/AGENTS.md` and the `*.png` assets (so every `.md` and every
   `.svg` under it, at any depth), and `docs/src/integrations/datafusion.md` into
   `references/docs/`, preserving the tree. Update the directory counts in `SKILL.md` if docs
   were added or removed. Two deviations from upstream bytes are expected and enforced by this
   repo's pre-commit hooks, not drift: trailing whitespace is stripped from every line, and
   every file ends in exactly one newline - which adds a byte to the four `.drawio.svg` diagrams
   (`indices-compaction` 51381 -> 51382, `scalar_index` 8210 -> 8211, `starter-example`
   14622 -> 14623, `indices-fragment handling` 21856 -> 21857). Applying both normalizations to
   a fresh `git archive` of `docs/src` reproduces the committed mirror byte-for-byte.
2. Re-check Part A of `references/performance.md` against the new `guide/performance.md` and the
   other perf-bearing sections it routes to. Part A deliberately does **not** copy that text -
   it points at `references/docs/`, so a mirror refresh updates it automatically; what needs
   hand-editing is the provenance note (which tags the guide changed at) and the two
   source-derived "Performance changes not in the guide" subsections. Part B (field-verified
   practices) is experience-derived - only edit it with new *measured* results, never
   speculation.
3. Re-verify the crate workspace and re-read the format spec for the reference files
   (`format-file.md`, `format-table.md`, `indexes.md`, `ops.md`, `changelog-v7-v14.md`), then
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
| 14 (v7 -> v14 delta) | `changelog-v7-v14.md` |

Cross-references inside those files are written as "section N" against the original numbering,
so the index file must stay in sync with any re-split.
