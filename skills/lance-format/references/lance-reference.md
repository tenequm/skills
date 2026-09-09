# Lance v12 reference - section index

The reference is split across five files. Cross-references written as "section N" (in these
files, in `performance.md`, and in `SKILL.md`) use the original 16-section numbering:

| Sections | File |
|----------|------|
| 1 What Lance is, 2 Crate workspace, 3 File format, 4 Data types | `format-file.md` |
| 5 Table format, 6 Schema evolution, 7 Versioning/tags/branches, 8 Row IDs, 9 Transactions, 10 MemWAL | `format-table.md` |
| 11 Indexes, 12 Distributed write and indexing | `indexes.md` |
| 13 Object store, 15 Capability matrix, 16 Source map | `ops.md` |
| 14 What changed (v7 -> v12) | `changelog-v7-v12.md` |

Each file keeps the original section headings and its own table of contents.

Citations are `path:line` relative to the repo root. Build a permalink as
`https://github.com/lance-format/lance/blob/v12.0.0-beta.15/<path>`. Line numbers drift
between tags; treat them as approximate. The authoritative in-repo sources are the format
spec under `docs/src/format/`, the user guide under `docs/src/guide/`, the protobuf schemas
under `protos/`, and the Rust workspace under `rust/`.
