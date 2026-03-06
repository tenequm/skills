# Remote Repository Analysis

Fetch files and analyze repositories without cloning them locally.

## Fetch Files Without Cloning

### Get directory listing

```bash
gh api repos/OWNER/REPO/contents/PATH
```

Returns JSON array with file/directory metadata.

### Fetch file content

```bash
gh api repos/OWNER/REPO/contents/path/file.ts | jq -r '.content' | base64 -d
```

The API returns base64-encoded content, so decode it with `base64 -d`.

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
