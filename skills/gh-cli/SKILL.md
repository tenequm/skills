---
name: gh-cli
description: GitHub CLI for remote repository analysis, file fetching, codebase comparison, and discovering trending code/repos. Use when analyzing repos without cloning, comparing codebases, or searching for popular GitHub projects.
metadata:
  version: "1.3.0"
  upstream: "gh@2.96.0"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/gh-cli
    emoji: "🐙"
    primaryEnv: GH_TOKEN
    requires:
      bins:
        - gh
    envVars:
      - name: GH_TOKEN
        required: false
        description: GitHub auth token used by gh CLI.
      - name: GITHUB_TOKEN
        required: false
        description: Alias for GH_TOKEN.
      - name: GH_HOST
        required: false
        description: GitHub Enterprise host override.
---

# GitHub CLI - Remote Analysis & Discovery

Remote repository operations, codebase comparison, and code discovery without cloning.

## When to Use

- Analyze repositories without cloning
- Compare codebases side-by-side
- Fetch specific files from any repo
- Find trending repositories and code patterns
- Search code across GitHub

## Quick Operations

### Fetch a file remotely

```bash
gh repo read-file path/file.ts --repo OWNER/REPO
```

`gh repo read-file` (preview) is the preferred path: it prints raw content, takes `--ref` for any branch/tag/commit, and handles files above the Contents API's 1MB inline limit. Fall back to `gh api` where the command is unavailable:

```bash
gh api repos/OWNER/REPO/contents/path/file.ts -H "Accept: application/vnd.github.raw"
```

There is **no `base64decode` template function** - `--template '{{.content | base64decode}}'` fails with `function "base64decode" not defined`. To decode the default JSON response, pipe it:

```bash
gh api repos/OWNER/REPO/contents/path/file.ts --jq '.content' | base64 -d
```

### Get directory listing

```bash
gh repo read-dir PATH --repo OWNER/REPO

# Or via the API
gh api repos/OWNER/REPO/contents/PATH
```

### Pin the repo in scripted workflows

`gh` infers the repository from the current working directory. In agent or CI workflows - where a `cd` may persist - always pass `--repo OWNER/REPO` so a stray cwd cannot silently retarget the command.

### Search code

```bash
gh search code "pattern" --language=typescript
```

### Find trending repos

```bash
gh search repos --language=rust --sort stars --order desc
```

## Compare Two Codebases

Systematic workflow for comparing repositories to identify similarities and differences.

**Example use**: "Compare solana-fm/explorer-kit and tenequm/solana-idls"

### Step 1: Fetch directory structures

```bash
gh repo read-dir PATH --repo OWNER-A/REPO-A
gh repo read-dir PATH --repo OWNER-B/REPO-B
```

If comparing a monorepo package, specify the path (e.g., `packages/explorerkit-idls`).

### Step 2: Compare file lists

```bash
gh repo read-dir PATH --repo OWNER-A/REPO-A --json name --jq '.[].name'
gh repo read-dir PATH --repo OWNER-B/REPO-B --json name --jq '.[].name'
```

Compare the output of each command to identify files unique to each repo and common files.

### Step 3: Fetch key files for comparison

Compare package dependencies:

```bash
gh repo read-file package.json --repo OWNER-A/REPO-A
gh repo read-file package.json --repo OWNER-B/REPO-B
```

Compare main entry points:

```bash
gh repo read-file src/index.ts --repo OWNER-A/REPO-A
gh repo read-file src/index.ts --repo OWNER-B/REPO-B
```

Add `--cache 1h` to `gh api` calls when iterating on the same files repeatedly, to avoid re-spending rate limit.

### Step 4: Analyze differences

Compare the fetched files to identify:

**API Surface**
- What functions/classes are exported?
- Are the APIs similar or completely different?

**Dependencies**
- Shared dependencies (same approach)
- Different dependencies (different implementation)

**Unique Features**
- Features only in repo1
- Features only in repo2

For detailed comparison strategies, see [references/comparison.md](references/comparison.md).

## Discover Trending Content

### Find trending repositories

```bash
# Most starred repos
gh search repos --sort stars --order desc --limit 20

# Trending in specific language
gh search repos --language=rust --sort stars --order desc

# Recently popular (created in last month)
gh search repos "created:>2024-10-01" --sort stars --order desc

# Trending in specific topic
gh search repos "topic:machine-learning" --sort stars --order desc
```

### Discover popular code patterns

```bash
# Find popular implementations (code search has no sorting - scope with filters)
gh search code "function useWallet" --language=typescript

# Scope to a known repo (code search can't filter by stars - stars:>N is literal text)
gh search code "implementation" --repo=honojs/hono

# Search specific organization
gh search code "authentication" --owner=anthropics
```

For complete discovery queries and patterns, see [references/discovery.md](references/discovery.md).

## Search Basics

### Code search

```bash
# Search across all repositories
gh search code "API endpoint" --language=python

# Search in specific organization
gh search code "auth" --owner=anthropics

# Exclude results with negative qualifiers
gh search issues -- "bug report -label:wontfix"
```

### Issue & PR search

```bash
# Find open bugs
gh search issues --label=bug --state=open

# Search assigned issues
gh search issues --assignee=@me --state=open
```

### Search rate limits

Search runs on a much tighter budget than the 5000/hr core API - check with `gh api rate_limit`:

| Resource | Limit (authenticated) |
|----------|----------------------|
| `core` (incl. `gh api`, `gh repo read-file`) | 5000/hr |
| `search` (repos, issues, prs, commits) | 30/min |
| `code_search` | 10/min |

For advanced search syntax, see [references/search.md](references/search.md).

## Special Syntax

### Field name inconsistencies

**IMPORTANT:** GitHub CLI uses inconsistent field names across commands:

| Field | `gh repo view` | `gh search repos` |
|-------|----------------|-------------------|
| Stars | `stargazerCount` | `stargazersCount` |
| Forks | `forkCount` | `forksCount` |

**Examples:**

```bash
# ✅ Correct for gh repo view
gh repo view owner/repo --json stargazerCount,forkCount

# ✅ Correct for gh search repos
gh search repos "query" --json stargazersCount,forksCount
```

### Excluding search results

A negative qualifier inside a quoted query (`"bug -label:wontfix"`) works as-is. `--` is only required when the query *starts* with a hyphen, which the shell would otherwise read as a flag.

**Put every flag before `--`.** Everything after `--` is positional, so trailing flags get swallowed into the query string:

```bash
# ✅ Correct - flags first
gh search issues --limit 5 -- "-label:wontfix bug"

# ❌ Wrong - --limit 5 becomes part of the search query, silently returning 30 results
gh search issues -- "-label:wontfix bug" --limit 5
```

For more syntax gotchas, see [references/syntax.md](references/syntax.md).

## Preview Commands

Recent `gh` releases added preview commands relevant to remote analysis and discovery. They are subject to change without notice.

```bash
# Read a repo without cloning (see Quick Operations above)
gh repo read-file PATH --repo OWNER/REPO
gh repo read-dir PATH --repo OWNER/REPO

# GitHub Discussions - often where design rationale lives
gh discussion list --repo OWNER/REPO
gh discussion view <number> --repo OWNER/REPO

# Agent skills on GitHub
gh skill search <query>
gh skill install <skill>

# Revert a merged PR
gh pr revert <number> --repo OWNER/REPO
```

## Advanced Workflows

For detailed documentation on specific workflows:

**Core Workflows:**
- [remote-analysis.md](references/remote-analysis.md) - Advanced file fetching patterns
- [comparison.md](references/comparison.md) - Complete codebase comparison guide
- [discovery.md](references/discovery.md) - All trending and discovery queries
- [search.md](references/search.md) - Advanced search syntax
- [syntax.md](references/syntax.md) - Special syntax and command quirks

**GitHub Operations:**
- [repositories.md](references/repositories.md) - Repository operations
- [pull_requests.md](references/pull_requests.md) - PR workflows
- [issues.md](references/issues.md) - Issue management
- [actions.md](references/actions.md) - GitHub Actions
- [releases.md](references/releases.md) - Release management

**Setup & Configuration:**
- [getting_started.md](references/getting_started.md) - `gh auth setup-git` credential helper
- [other.md](references/other.md) - Environment variables, aliases, config
- [extensions.md](references/extensions.md) - CLI extensions

## Resources

- Official docs: https://cli.github.com/manual/
- GitHub CLI: https://github.com/cli/cli
- Search syntax: https://docs.github.com/en/search-github
