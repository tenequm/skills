# Maintaining this skill

Citations across the reference files are `path:line` relative to the `lance-format/lance` repo;
build a permalink as `https://github.com/lance-format/lance/blob/v15.0.0-beta.10/<path>`. Line
numbers drift between tags - treat them as approximate.

To refresh: `git -C <your lance-format/lance clone> fetch --tags`, then read the newest tag (the
major may have jumped again - the release train re-roots on any `breaking-change` label, and it
has now fired on **eight consecutive minor lines**, 7.2 through 14.1: every `X.1`/`X.2` line was
abandoned for the next major, so sort tags by date rather than assuming the current major, and do
not assume an intermediate line got a final. Abandoned lines come in two shapes: tagged (7.2 five
betas, 9.1 eight, 10.1 two, 13.1 two) and untagged (8.1, 11.1, 12.1, 14.1 never got a `v*` tag,
only a `release-root/X.Y.0-beta.N` tag), so `git tag -l 'release-root/*' --sort=creatordate` is
the line history and `git tag -l 'v*'` alone undercounts it.

Check the **stable pin** separately from the frontier. Since the v14 line finals follow a
release-branch patch model:

- Finals and patches are cut on `release/vX.Y` branches (`origin/release/v14.0`), never on `main`.
  Each version goes through an `-rc.N` chain first (`v14.0.0-rc.1`, `rc.2`, then `v14.0.0`;
  `v14.0.1-rc.1` -> `v14.0.1`; `v14.0.2-rc.1` -> `v14.0.2`). An `rc` tag alone is not a release:
  at this refresh `v14.0.3` exists only as `v14.0.3-rc.1`.
- After each release the branch is bumped to the next patch's `-beta.0`
  (`chore: bump to 14.0.3-beta.0 for next patch development`). A `x.y.z-beta.0` version on a
  release branch means "unreleased", not a published beta.
- Backports land as **new PRs with new numbers** (#10363 on `main` is #10364 on
  `release/v14.0`), so match fixes between `main` and a release branch by commit title, not by
  PR number.
- **Check each registry on its own.** `v14.0.0` was tagged and released on GitHub but never
  reached crates.io (`lance-io` used an unmerged `object_store` commit through
  `[patch.crates-io]`, which `cargo publish` cannot carry; #10364 removed it in `v14.0.1`), so the Rust floor of the v14 line is `14.0.1` while PyPI and GitHub start at
  `14.0.0`. Query `https://crates.io/api/v1/crates/lance/versions` directly. Maven Central's
  `maven-metadata.xml` `<release>` for `org.lance:lance-core` includes betas (it read
  `15.0.0-beta.8` at this refresh), so it does not identify the stable pin either.

A final can also be the next line's release root plus a couple of release commits
(`v13.0.0` is `release-root/14.0.0-beta.N` + 2), so its delta and the next line's overlap
completely - do not double-count. The v14 final is the opposite case: `v14.0.0` is
`v14.0.0-beta.14` + 145 commits on the stabilization branch and is not an ancestor of `main`.

Traps worth knowing before you start:

- **The `breaking-change` label is a floor, not a ceiling.** It drives the release bot, so it is
  the right query for "did the major re-root" - but it does **not** enumerate what will break a
  consumer. Worked examples: in `v12.0.0-beta.6 -> beta.15` the two changes most likely to bite
  (`stable` resolving to 2.2, #8657; the IVF_RQ 5-bit default, #8936) carried a `!` and no label;
  in the v14 line the manifest-field move #9482 carried only `format-change`; in the v15 line the
  row-address writer fence #10352 carried only `bug`/`critical-fix`. **Always also scan the range
  for `!` commits** (`git log --oneline <a>..<b> | grep '!:'`), query the `format-change` and
  `critical-fix` labels, and diff the defaults you already document - version enums,
  `*_DEFAULT_*` consts, and the sizing formulas in `docs/src/guide/performance.md`. The defaults
  diff is what caught `inline_optimization_enabled` flipping `true -> false` (#9180), which
  carried neither marker.
- **The spec pages can run ahead of the code.** `format/table/versioning.md` lists bit 9 (FRI
  with stable row IDs), bit 12 (fragment tree) and bit 13 (independent covering fields) as
  reader/writer `Yes`, while `rust/lance-table/src/feature_flags.rs` supports bit 9 only in debug
  builds and masks bits 12 and 13 out of `supported_flags_when` - unchanged through
  `v15.0.0-beta.10`. #10299 (`v15.0.0-beta.6`) is a docs-only PR ("**No implementation changes are
  included**") that specifies row-address index versions for FTS (v4), NGram, RTree, MinHash LSH
  (v1) and vector (v3) while the code constants stay at the old versions. When a doc table and a
  `const` disagree, **verify which one the build enforces** and record the split rather than
  copying the table.
- **The docs can also lag the code, and lag a whole release line.** The managed-blob activation
  text ("Publishing a new data file containing a Blob v2 field activates the Managed Blob
  capability") stayed in `versioning.md` and `guide/blob.md` at every v14 tag through
  `v14.0.3-rc.1`, although the code has required the `lance.blob.managed` opt-in since #9891
  (`v14.0.0-beta.14`); the v15 docs fixed it at `v15.0.0-beta.2` (#9193). In the other direction,
  the code supports bit 16 (zone write seeds) since `v15.0.0-beta.1` (#10102) and bit 17 (object
  metadata) since `v15.0.0-beta.6` (#10383), while `v15.0.0-beta.10`'s `versioning.md` still says
  "Bits 16 and 17 are reserved but remain unsupported." A doc page that was right at the last
  refresh is not evidence it is right now.
- **A final is not on `main`.** Finals are cut on stabilization branches, so
  `git merge-base --is-ancestor <final> main` returns false for a perfectly official release.
  Check GitHub Releases / crates.io / PyPI to identify the stable pin, not ancestry.
- **You do not need to move `HEAD` to read a tag.** `git show <tag>:<path>`,
  `git grep <pattern> <tag> -- <path>`, `git diff <tagA> <tagB> -- <path>` and
  `git ls-tree -r <tag>` are all read-only, which matters when the clone is shared. In zsh, quote
  `"${T}:path"` - an unquoted `$T:r...` is parsed as a history modifier. A `blob:none` partial
  clone cannot always produce arbitrary historical diffs (`git log -S` may fail on absent blobs);
  tag-to-tag reads of present files still work, but `git grep` across several tags at once can
  stall fetching blobs - read one tag at a time.

Then:

1. Re-copy the docs mirror: the `.md` files of `docs/src/guide` and `docs/src/quickstart`
   **except `quickstart/index.md`** (since `v15.0.0-beta.10` it is "Getting Started with
   LanceDB", product content this skill does not cover; `quickstart/spark.md` stays), all of
   `docs/src/format` except `format/AGENTS.md` and the `*.png` assets (so every `.md` and every
   `.svg` under it, at any depth), and `docs/src/integrations/datafusion.md` into
   `references/docs/`, preserving the tree. At `v15.0.0-beta.10` that is **61 markdown files plus
   5 diagrams**; update the directory counts in `SKILL.md` if docs were added or removed (the
   `v15` refresh removed `format/table/jsonb.md`, reverted by #9889). Two deviations from upstream
   bytes are expected, not drift - apply both when mirroring (this repo's `just check` fails on
   trailing whitespace): trailing whitespace is stripped from every line, and every file ends in
   exactly one newline - which adds a byte to the four `.drawio.svg` diagrams
   (`indices-compaction` 51381 -> 51382, `scalar_index` 8210 -> 8211, `starter-example`
   14622 -> 14623, `indices-fragment handling` 21856 -> 21857; unchanged at `v15.0.0-beta.10`)
   and to upstream pages that lack a final newline (`format/index.md`, `format/file/index.md`).
   Applying both normalizations to a fresh `git archive` of `docs/src` reproduces the committed
   mirror byte-for-byte. Also re-check `docs/make-full-website.sh` for the sibling repos the
   built site assembles (nine at `v15.0.0-beta.10`, `lance-flink` new), since those sections
   cannot be mirrored.
2. Re-check Part A of `references/performance.md` against the new `guide/performance.md` and the
   other perf-bearing sections it routes to. Part A deliberately does **not** copy that text -
   it points at `references/docs/`, so a mirror refresh updates it automatically; what needs
   hand-editing is the provenance note (which tags the guide changed at - find them with
   `git log <a>..<b> -- docs/src/guide/performance.md` and `git tag --contains <sha>`) and the
   source-derived "Performance changes not in the guide" subsections. Part B (field-verified
   practices) is experience-derived - only edit it with new *measured* results, never
   speculation.
3. Re-verify the crate workspace (`git ls-tree -d --name-only <tag> rust/`; 28 crates at
   `v15.0.0-beta.10`) and re-read the format spec for the reference files (`format-file.md`,
   `format-table.md`, `indexes.md`, `ops.md`, `changelog-v7-v15.md`), then bump
   `metadata.upstream` plus every current-tag version reference. `lance-reference.md` is only the
   section-number index - update it if the split changes.

## Reference file layout

`references/lance-reference.md` maps the original 16 section numbers onto five files:

| Sections | File |
|----------|------|
| 1-4 (what Lance is, crates, file format, data types) | `format-file.md` |
| 5-10 (table format, schema evolution, versioning, row IDs, transactions, MemWAL) | `format-table.md` |
| 11-12 (indexes, distributed write/indexing) | `indexes.md` |
| 13, 15, 16 (object store, capability matrix, source map) | `ops.md` |
| 14 (v7 -> v15 delta) | `changelog-v7-v15.md` |

Cross-references inside those files are written as "section N" against the original numbering,
so the index file must stay in sync with any re-split.
