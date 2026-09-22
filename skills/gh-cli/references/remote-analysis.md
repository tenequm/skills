# Remote Repository Analysis

Fetch files and analyze repositories without cloning them locally.

## Fetch Files Without Cloning

### Preferred: `gh repo read-file` / `gh repo read-dir`

These preview commands are purpose-built for reading a repo without cloning. They print raw content (no base64 step), accept `--ref` for any branch/tag/commit, and transparently handle files past the Contents API's 1MB inline limit.

```bash
# Read a file from the default branch
gh repo read-file path/file.ts --repo OWNER/REPO

# From a specific branch, tag, or commit
gh repo read-file path/file.ts --repo OWNER/REPO --ref v1.2.0

# Save straight to disk
gh repo read-file path/file.ts --repo OWNER/REPO --output ./file.ts

# List a directory
gh repo read-dir PATH --repo OWNER/REPO
gh repo read-dir PATH --repo OWNER/REPO --json name,size,type --jq '.entries[] | select(.type=="file") | .name'
```

`read-dir --json` returns an object, `{"entries":[...]}`, so jq filters start with `.entries[]`. Fields: `gitSHA, gitType, mode, modeOctal, name, nameRaw, path, pathRaw, size, submodule, type`. Omit `PATH` to list the repo root.

Both commands refuse to print content containing terminal escape sequences unless you pass `--allow-escape-sequences`; `read-file --output` always writes the raw bytes.

### Fallback: the Contents API

```bash
# Raw bytes via Accept header
gh api repos/OWNER/REPO/contents/path/file.ts -H "Accept: application/vnd.github.raw"

# Or decode the base64 JSON response (files up to 1MB only)
gh api repos/OWNER/REPO/contents/path/file.ts --jq '.content' | base64 -d
```

For files between 1MB and 100MB the Contents API returns `"content": ""` and `"encoding": "none"`, so the base64 pipe silently prints nothing. Use `gh repo read-file` or the raw `Accept` header; past 100MB the endpoint is unsupported.

There is no `base64decode` template function - `--template '{{.content | base64decode}}'` errors out. See `gh help formatting` for the functions that do exist.

### Cache repeated fetches

When iterating over the same files, cache responses so you do not re-spend the 5000/hr core budget:

```bash
gh api repos/OWNER/REPO/contents/PATH --cache 1h
```

Use `--slurp` with `--paginate` to collect all pages into a single JSON array. `--slurp` cannot be combined with `--jq` or `--template`, so pipe to `jq`, or use `--paginate --jq` to filter each page:

```bash
gh api --paginate --slurp 'repos/OWNER/REPO/tags?per_page=100' | jq 'map(length) | add'
gh api --paginate 'repos/OWNER/REPO/tags?per_page=100' --jq '.[].name'
```

### Get entire file tree recursively

```bash
gh api 'repos/OWNER/REPO/git/trees/HEAD?recursive=1'
```

Returns complete tree structure in one request. Use `HEAD` (or the real default branch) rather than hardcoding `main` - repos whose default branch is `trunk` or `master` return 404. Quote the endpoint: zsh reads the unquoted `?` as a glob and fails with `no matches found`.

## Useful Remote Analysis Patterns

### Check if file exists

```bash
gh api repos/OWNER/REPO/contents/path/file.ts --silent 2>/dev/null && echo "exists" || echo "not found"
```

`--silent` matters: on a 404, `gh api` still prints the error JSON to stdout.

### Get latest commit for specific file

```bash
gh api 'repos/OWNER/REPO/commits?path=src/index.ts' --jq '.[0].sha'
```

### Compare file across branches

```bash
diff <(gh repo read-file file.ts --repo OWNER/REPO --ref main) \
     <(gh repo read-file file.ts --repo OWNER/REPO --ref dev)
```

### Get file from specific commit

```bash
gh repo read-file file.ts --repo OWNER/REPO --ref abc123
```

Use any commit SHA, branch name, or tag as the `--ref` value.

### Compare two refs

```bash
gh api repos/OWNER/REPO/compare/v1.0.0...v2.0.0 --jq '{ahead_by, behind_by, files: [.files[].filename]}'
```

The compare API returns at most 250 commits and 300 files. It works across forks in the same repository network with `OWNER:BRANCH` on either side, never between unrelated repos.

## Working with Large Repositories

For large repos, use the Git Trees API instead of Contents API:

```bash
# Get full tree
gh api 'repos/OWNER/REPO/git/trees/HEAD?recursive=1' --jq '.tree[] | select(.type == "blob") | .path'
```

This is more efficient for listing many files. Very large trees come back with `"truncated": true`; list subtrees separately in that case.

## Common Use Cases

### Inspect configuration files

```bash
gh repo read-file package.json --repo vercel/next.js | jq '{dependencies, devDependencies, peerDependencies}'
```

### Check documentation

```bash
gh repo read-file README.md --repo anthropics/anthropic-sdk-python
```

### Analyze project structure

```bash
gh api 'repos/OWNER/REPO/git/trees/HEAD?recursive=1' --jq '.tree[] | select(.type == "tree") | .path'
```

Shows all directories in the repository.
