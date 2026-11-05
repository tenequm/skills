# Compare Two Codebases

Systematic workflow for comparing repositories to identify similarities, differences, and unique features.

## When to Use

- "Are repo-a and repo-b providing the same functionality?"
- "What's different between these two implementations?"
- "Which repo has more features?"
- "Can I replace library X with library Y?"

## 4-Step Comparison Workflow

### Step 1: Fetch directory structures

```bash
gh repo read-dir PATH --repo OWNER-A/REPO-A --json name,type > repo1.json
gh repo read-dir PATH --repo OWNER-B/REPO-B --json name,type > repo2.json
```

If comparing a monorepo package, specify the path (e.g., `packages/explorerkit-idls`). Omit `PATH` to list the repo root.

### Step 2: Compare file lists

`read-dir --json` wraps the listing in `{"entries":[...]}`:

```bash
jq -r '.entries[].name' repo1.json | sort > repo1-files.txt
jq -r '.entries[].name' repo2.json | sort > repo2-files.txt
diff repo1-files.txt repo2-files.txt
```

This shows:
- Files unique to repo1 (prefixed with `<`)
- Files unique to repo2 (prefixed with `>`)

For whole-repo comparisons, list every file in one request per repo:

```bash
gh api 'repos/OWNER-A/REPO-A/git/trees/HEAD?recursive=1' --jq '.tree[] | select(.type == "blob") | .path' | sort > repo1-files.txt
gh api 'repos/OWNER-B/REPO-B/git/trees/HEAD?recursive=1' --jq '.tree[] | select(.type == "blob") | .path' | sort > repo2-files.txt
comm -3 repo1-files.txt repo2-files.txt
```

Use `HEAD`, not a hardcoded `main` - repos with another default branch return 404.

### Step 3: Fetch key files for comparison

Compare the most important files:

#### Package dependencies

```bash
gh repo read-file package.json --repo OWNER-A/REPO-A > repo1-pkg.json
gh repo read-file package.json --repo OWNER-B/REPO-B > repo2-pkg.json
```

Then compare dependencies:

```bash
diff <(jq -S '{dependencies, peerDependencies}' repo1-pkg.json) <(jq -S '{dependencies, peerDependencies}' repo2-pkg.json)
```

#### Main entry points

```bash
gh repo read-file src/index.ts --repo OWNER-A/REPO-A > repo1-index.ts
gh repo read-file src/index.ts --repo OWNER-B/REPO-B > repo2-index.ts
```

`gh repo read-file` handles files past the Contents API's 1MB inline limit; the older `gh api .../contents/FILE --jq '.content' | base64 -d` pattern silently prints nothing for them.

### Step 4: Analyze differences

Compare the fetched files to identify:

**API Surface**
- What functions/classes are exported?
- Are the APIs similar or completely different?
- Which repo has more comprehensive exports?

**Dependencies**
- Shared dependencies (same approach)
- Different dependencies (different implementation)
- Dependency versions (maintenance status)

**Unique Features**
- Features only in repo1
- Features only in repo2
- Similar features with different implementations

## Comparing Versions of the Same Repo

When both sides live in one repository network (tags, branches, or a fork), the compare API does the diff server-side:

```bash
# Commit and file summary between two tags
gh api repos/OWNER/REPO/compare/v1.0.0...v2.0.0 --jq '{ahead_by, behind_by, total_commits, files: (.files | length)}'

# Changed file names
gh api repos/OWNER/REPO/compare/v1.0.0...v2.0.0 --jq '.files[].filename'

# Fork branch vs upstream branch
gh api repos/OWNER/REPO/compare/main...FORK-OWNER:feature --jq '.files[].filename'
```

Limits: at most 250 commits and 300 files in the response. It returns 404 for unrelated repositories - use the 4-step workflow above for those.

## Example: Compare Solana IDL Libraries

```bash
# Repo 1: solana-fm/explorer-kit (monorepo package)
gh repo read-dir packages/explorerkit-idls --repo solana-fm/explorer-kit --json name > repo1.json

# Repo 2: tenequm/solana-idls (standalone)
gh repo read-dir --repo tenequm/solana-idls --json name > repo2.json

# Compare file structures
diff <(jq -r '.entries[].name' repo1.json | sort) <(jq -r '.entries[].name' repo2.json | sort)

# Compare dependencies
echo "=== Repo 1 Dependencies ==="
gh repo read-file packages/explorerkit-idls/package.json --repo solana-fm/explorer-kit | jq '{dependencies, peerDependencies}'
echo "=== Repo 2 Dependencies ==="
gh repo read-file package.json --repo tenequm/solana-idls | jq '{dependencies, peerDependencies}'

# Compare exports
echo "=== Repo 1 Exports ==="
gh repo read-file packages/explorerkit-idls/src/index.ts --repo solana-fm/explorer-kit | grep -E "^export"
echo "=== Repo 2 Exports ==="
gh repo read-file src/index.ts --repo tenequm/solana-idls | grep -E "^export"
```

## Analysis Framework

After fetching files, analyze systematically:

### 1. Purpose & Scope
- What problem does each repo solve?
- Same problem or different use cases?

### 2. API Design
- Are the APIs compatible?
- Which is more user-friendly?
- Breaking changes if switching?

### 3. Dependencies
- Shared ecosystem (similar approach)
- Different dependencies (different implementation)
- Heavy vs lightweight

### 4. Maintenance
- Last commit dates
- Release frequency
- Issue/PR activity

```bash
gh repo view OWNER/REPO --json pushedAt,latestRelease,stargazerCount,isArchived
```

### 5. Features
- Core features both have
- Unique to repo1
- Unique to repo2

## Tips

**Compare READMEs first**

```bash
gh repo read-file README.md --repo OWNER-A/REPO-A > repo1-readme.md
gh repo read-file README.md --repo OWNER-B/REPO-B > repo2-readme.md
```

This gives you a high-level understanding before diving into code.

**Check for common file patterns**

- `package.json` - Dependencies and metadata
- `tsconfig.json` - TypeScript configuration
- `src/index.ts` - Main entry point
- `README.md` - Documentation and examples
- `CHANGELOG.md` - Version history

**Use git tree for overview**

```bash
gh api 'repos/OWNER/REPO/git/trees/HEAD?recursive=1' --jq '.tree[] | select(.type == "blob") | .path' | grep -E "\.(ts|js|json)$"
```

Gets all TypeScript/JavaScript/JSON files quickly.
