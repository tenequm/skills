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
gh api repos/OWNER-A/REPO-A/contents/PATH > repo1.json
gh api repos/OWNER-B/REPO-B/contents/PATH > repo2.json
```

If comparing a monorepo package, specify the path (e.g., `packages/explorerkit-idls`).

### Step 2: Compare file lists

```bash
jq -r '.[].name' repo1.json > repo1-files.txt
jq -r '.[].name' repo2.json > repo2-files.txt
diff repo1-files.txt repo2-files.txt
```

This shows:
- Files unique to repo1 (prefixed with `<`)
- Files unique to repo2 (prefixed with `>`)
- Common files (no prefix)

### Step 3: Fetch key files for comparison

Compare the most important files:

#### Package dependencies

```bash
gh api repos/OWNER-A/REPO-A/contents/package.json | jq -r '.content' | base64 -d > repo1-pkg.json
gh api repos/OWNER-B/REPO-B/contents/package.json | jq -r '.content' | base64 -d > repo2-pkg.json
```

Then compare dependencies:

```bash
jq '.dependencies' repo1-pkg.json
jq '.dependencies' repo2-pkg.json
```

#### Main entry points

```bash
gh api repos/OWNER-A/REPO-A/contents/src/index.ts | jq -r '.content' | base64 -d > repo1-index.ts
gh api repos/OWNER-B/REPO-B/contents/src/index.ts | jq -r '.content' | base64 -d > repo2-index.ts
```

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

## Example: Compare Solana IDL Libraries

```bash
# Repo 1: solana-fm/explorer-kit (monorepo package)
gh api repos/solana-fm/explorer-kit/contents/packages/explorerkit-idls > repo1.json

# Repo 2: tenequm/solana-idls (standalone)
gh api repos/tenequm/solana-idls/contents/ > repo2.json

# Compare file structures
jq -r '.[].name' repo1.json > repo1-files.txt
jq -r '.[].name' repo2.json > repo2-files.txt
diff repo1-files.txt repo2-files.txt

# Fetch package.json from both
gh api repos/solana-fm/explorer-kit/contents/packages/explorerkit-idls/package.json | jq -r '.content' | base64 -d > repo1-pkg.json
gh api repos/tenequm/solana-idls/contents/package.json | jq -r '.content' | base64 -d > repo2-pkg.json

# Compare dependencies
echo "=== Repo 1 Dependencies ==="
jq '.dependencies' repo1-pkg.json
echo "=== Repo 2 Dependencies ==="
jq '.dependencies' repo2-pkg.json

# Fetch main entry points
gh api repos/solana-fm/explorer-kit/contents/packages/explorerkit-idls/src/index.ts | jq -r '.content' | base64 -d > repo1-index.ts
gh api repos/tenequm/solana-idls/contents/src/index.ts | jq -r '.content' | base64 -d > repo2-index.ts

# Compare exports
echo "=== Repo 1 Exports ==="
grep -E "^export" repo1-index.ts
echo "=== Repo 2 Exports ==="
grep -E "^export" repo2-index.ts
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

### 5. Features
- Core features both have
- Unique to repo1
- Unique to repo2

## Tips

**Compare READMEs first**

```bash
gh api repos/OWNER-A/REPO-A/contents/README.md | jq -r '.content' | base64 -d > repo1-readme.md
gh api repos/OWNER-B/REPO-B/contents/README.md | jq -r '.content' | base64 -d > repo2-readme.md
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
gh api repos/OWNER/REPO/git/trees/main?recursive=1 | jq '.tree[] | select(.type == "blob") | .path' | grep -E "\.(ts|js|json)$"
```

Gets all TypeScript/JavaScript/JSON files quickly.
