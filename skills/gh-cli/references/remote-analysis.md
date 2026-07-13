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
gh repo read-dir PATH --repo OWNER/REPO --json name,size,type --jq '.[] | select(.type=="file") | .name'
```

`read-dir` JSON fields: `gitSHA, gitType, mode, modeOctal, name, nameRaw, path, pathRaw, size, submodule, type`.

### Fallback: the Contents API

```bash
# Raw bytes via Accept header
gh api repos/OWNER/REPO/contents/path/file.ts -H "Accept: application/vnd.github.raw"

# Or decode the base64 JSON response
gh api repos/OWNER/REPO/contents/path/file.ts --jq '.content' | base64 -d
```

There is no `base64decode` template function - `--template '{{.content | base64decode}}'` errors out. See `gh help formatting` for the functions that do exist.

### Cache repeated fetches

When iterating over the same files, cache responses so you do not re-spend the 5000/hr core budget:

```bash
gh api repos/OWNER/REPO/contents/PATH --cache 1h
```

Use `--slurp` with `--paginate` to collect all pages into a single JSON array:

```bash
gh api --paginate --slurp repos/OWNER/REPO/commits
```

### Get entire file tree recursively

```bash
gh api repos/OWNER/REPO/git/trees/main?recursive=1
```

Returns complete tree structure in one request.

## Useful Remote Analysis Patterns

### Check if file exists

```bash
gh api repos/OWNER/REPO/contents/path/file.ts 2>/dev/null && echo "exists" || echo "not found"
```

### Get latest commit for specific file

```bash
gh api repos/OWNER/REPO/commits?path=src/index.ts | jq -r '.[0].sha'
```

### Compare file across branches

```bash
gh api repos/OWNER/REPO/contents/file.ts?ref=main | jq -r '.content' | base64 -d > main.ts
gh api repos/OWNER/REPO/contents/file.ts?ref=dev | jq -r '.content' | base64 -d > dev.ts
diff main.ts dev.ts
```

### Get file from specific commit

```bash
gh api repos/OWNER/REPO/contents/file.ts?ref=abc123 | jq -r '.content' | base64 -d
```

Use any commit SHA, branch name, or tag as the `ref` parameter.

## Working with Large Repositories

For large repos, use the Git Trees API instead of Contents API:

```bash
# Get full tree
gh api repos/OWNER/REPO/git/trees/main?recursive=1 | jq '.tree[] | select(.type == "blob") | .path'
```

This is more efficient for listing many files.

## Common Use Cases

### Inspect configuration files

```bash
gh api repos/vercel/next.js/contents/package.json | jq -r '.content' | base64 -d | jq '.dependencies'
```

### Check documentation

```bash
gh api repos/anthropics/anthropic-sdk-python/contents/README.md | jq -r '.content' | base64 -d
```

### Analyze project structure

```bash
gh api repos/OWNER/REPO/git/trees/main?recursive=1 | jq -r '.tree[] | select(.type == "tree") | .path'
```

Shows all directories in the repository.
