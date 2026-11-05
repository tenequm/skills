---
name: gh-cli
description: GitHub CLI for remote repository analysis, file fetching, codebase comparison, and discovering trending code/repos. Use when analyzing repos without cloning, comparing codebases, or searching for popular GitHub projects.
metadata:
  version: "1.4.0"
  categories: "development, integrations"
  topics: "github, gh-cli, code-search, repo-analysis, pull-requests"
  upstream: "gh@2.101.0"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/gh-cli
    emoji: "🐙"
    primaryEnv: GH_TOKEN
    requires:
      bins:
        - gh
    install:
      - kind: brew
        formula: gh
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

`gh repo read-file` (preview) is the preferred path: it prints raw content, takes `--ref` for any branch/tag/commit, and handles large files. `--output PATH` writes to disk (`--clobber` to overwrite); `--json` returns metadata (`content, downloadUrl, encoding, gitSHA, gitUrl, htmlUrl, name, path, size, type, url`). Fall back to `gh api` where the command is unavailable:

```bash
gh api repos/OWNER/REPO/contents/path/file.ts -H "Accept: application/vnd.github.raw"
```

There is **no `base64decode` template function** - `--template '{{.content | base64decode}}'` fails with `function "base64decode" not defined`. To decode the default JSON response, pipe it:

```bash
gh api repos/OWNER/REPO/contents/path/file.ts --jq '.content' | base64 -d
```

The Contents API inlines only files up to **1MB**. Past that, `.content` is an empty string (`encoding: "none"`) and the pipe above silently prints nothing - use `read-file` or the raw `Accept` header instead.

### Terminal escape sequences (gh 2.97.0+)

`gh` refuses to print remote content containing terminal escape sequences (ANSI art, some test fixtures) instead of passing it to your terminal:

- `gh repo read-file`: `file contains terminal escape sequences; use --allow-escape-sequences to read anyway`
- `gh api` raw bodies: `the response contains terminal escape sequences; pass --allow-escape-sequences to output it anyway`
- `gh pr diff` when piped: `the diff contains terminal escape sequences; pass --allow-escape-sequences to output it anyway`

Pass `--allow-escape-sequences` (also on `gh release download --output -` and `gh gist view`) when you need the bytes verbatim, or write to disk with `gh repo read-file --output`, which always keeps the raw bytes. The check came with the GHSA-3m3g-3wcr-px46 fix; run gh 2.98.0 or later to get it and the other 2.97/2.98 security fixes.

### Get directory listing

```bash
gh repo read-dir PATH --repo OWNER/REPO    # omit PATH to list the repo root

# Or via the API
gh api repos/OWNER/REPO/contents/PATH
```

`gh repo read-dir --json` returns an object, not an array - `{"entries":[...]}` - so filter with `.entries[]`:

```bash
gh repo read-dir src --repo OWNER/REPO --json name,type --jq '.entries[] | select(.type=="file") | .name'
```

### Pin the repo in scripted workflows

`gh` infers the repository from the current working directory. In agent or CI workflows - where a `cd` may persist - always pass `--repo OWNER/REPO` so a stray cwd cannot silently retarget the command. Signatures of a missing `--repo`:

- Outside a git repo: `failed to run git: fatal: not a git repository`
- In a repo with no remote: `no git remotes found`
- Inside a *different* repo: no error - the command targets that repo, and IDs from elsewhere 404

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
diff <(gh repo read-dir PATH --repo OWNER-A/REPO-A --json name --jq '.entries[].name') \
     <(gh repo read-dir PATH --repo OWNER-B/REPO-B --json name --jq '.entries[].name')
```

Lines prefixed `<` exist only in repo A, `>` only in repo B.

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

Comparing two refs of the **same** repo (or a fork of it) is one call to the compare API, capped at 250 commits and 300 files:

```bash
gh api repos/OWNER/REPO/compare/v1.0.0...v2.0.0 --jq '{ahead_by, files: [.files[].filename]}'
```

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
# Most starred repos - a bare `--sort` with no query or filter flag fails: Invalid search query ""
gh search repos "stars:>10000" --sort stars --order desc --limit 20

# Trending in specific language
gh search repos --language=rust --sort stars --order desc

# Recently popular (created in the last 30 days; works with BSD and GNU date)
SINCE=$(date -v-30d +%F 2>/dev/null || date -d '30 days ago' +%F)
gh search repos "created:>$SINCE" --sort stars --order desc

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
# Find open bugs (--state takes only open|closed here; omit it for both)
gh search issues --label=bug --state=open

# Search assigned issues
gh search issues --assignee=@me --state=open

# Meaning-based issue search (gh 2.98.0+): relevance-ranked, issues only, one page, no --sort/--order
gh search issues worktree checkout --repo cli/cli --search-type hybrid
```

Separate words are ANDed. A single quoted multi-word argument is sent as an **exact phrase**, so `gh search issues "worktree checkout"` can return nothing with exit 0.

### Search rate limits

Search runs on a much tighter budget than the 5000/hr core API - check with `gh api rate_limit`:

| Resource | Limit (authenticated) |
|----------|----------------------|
| `core` (incl. `gh api`, `gh repo read-file`) | 5000/hr |
| `search` (repos, issues, prs, commits) | 30/min |
| `code_search` | 10/min |
| `semantic_search` (`--search-type semantic\|hybrid`) | 10/min - not listed by `gh api rate_limit` |

For advanced search syntax, see [references/search.md](references/search.md).

## Special Syntax

### Field name inconsistencies

**IMPORTANT:** GitHub CLI uses inconsistent field names across commands:

| Field | `gh repo view` | `gh search repos` |
|-------|----------------|-------------------|
| Stars | `stargazerCount` | `stargazersCount` |
| Forks | `forkCount` | `forksCount` |
| Topics | `repositoryTopics` | not available |
| Watchers | `watchers` (`{totalCount}`) | `watchersCount` - actually the star count |

**Examples:**

```bash
# ✅ Correct for gh repo view
gh repo view owner/repo --json stargazerCount,forkCount

# ✅ Correct for gh search repos
gh search repos "query" --json stargazersCount,forksCount
```

Other fields that do not exist where you expect them: `gh pr view` has no `merged` (use `mergedAt` or `state`), `gh search prs` has no `mergedAt` (use `closedAt`), and `gh run list` has no `jobs` (use `gh run view <id> --json jobs`). A wrong field fails with `Unknown JSON field: "X"` followed by the valid list.

### One qualifier per argument

`gh search` (gh 2.97.0+) splits each argument at its **first** `:` and wraps the rest in quotes if it contains a space. Packing several qualifiers into one quoted string silently breaks the filter:

```bash
# ❌ Sent as language:"go stars:>500" - the language filter is lost
gh search repos "rate limiting middleware language:go stars:>500"

# ✅ Keywords and qualifiers as separate arguments; quote only those containing > or <
gh search repos rate limiting middleware language:go "stars:>500"
```

`gh pr list --search` and `gh issue list --search` pass their string through untouched, so one quoted string is fine there.

### Excluding search results

A negative qualifier works as its own argument or at the end of a quoted string (`"bug report -label:wontfix"`). `--` is only required when the query *starts* with a hyphen, which the shell would otherwise read as a flag.

**Put every flag before `--`.** Everything after `--` is positional, so trailing flags get swallowed into the query string:

```bash
# ✅ Correct - flags first
gh search issues --limit 5 -- -label:wontfix bug

# ❌ Wrong - --limit 5 becomes part of the search query, silently returning 30 results
gh search issues -- -label:wontfix bug --limit 5
```

For more syntax gotchas, see [references/syntax.md](references/syntax.md).

## Scripting Gotchas

- **Every command needs auth** - without a token `gh` prints `please run:  gh auth login` and exits 4. The exception is `gh release download` on public repos.
- **`gh api` writes its error body to stdout.** On failure it exits 1, prints `gh: Not Found (HTTP 404)` to stderr, and prints the error JSON to stdout without applying `--jq`. `$(gh api ...)` then captures the error as if it were data, so check the exit status:

  ```bash
  if sha=$(gh api repos/OWNER/REPO/contents/README.md --jq .sha); then echo "$sha"; else echo "fetch failed" >&2; fi
  ```

- **`-f`/`-F` switch `gh api` to POST**, so GET-only endpoints answer 404. Add `-X GET` to send the fields as a query string:

  ```bash
  gh api -X GET search/issues -f q='repo:cli/cli is:open worktree' --jq '.total_count'
  ```

- **`--jq` takes one expression and no jq flags** (a trailing `-r` fails with `unknown shorthand flag: 'r'`); string results already print raw.
- **`--paginate --slurp` cannot combine with `--jq`/`--template`.** Pipe to `jq` instead, or use `--paginate --jq`, which filters each page.
- **Quote endpoints containing `?`** - zsh treats an unquoted `?` as a glob and fails with `no matches found`.
- **Exit codes** (`gh help exit-codes`): 0 success, 1 failure, 2 cancelled, 4 authentication required. Some commands add their own: `gh pr checks` exits 8 while checks are pending.

## Preview Commands

Recent `gh` releases added preview commands relevant to remote analysis and discovery. They are subject to change without notice.

```bash
# Read a repo without cloning (see Quick Operations above)
gh repo read-file PATH --repo OWNER/REPO
gh repo read-dir PATH --repo OWNER/REPO

# GitHub Discussions - often where design rationale lives
gh discussion list --repo OWNER/REPO --search "keyword" --answered
gh discussion view <number> --repo OWNER/REPO --comments

# Agent skills on GitHub
gh skill search <query>
gh skill preview OWNER/REPO <skill>    # print SKILL.md without installing
gh skill install OWNER/REPO <skill>
```

`gh discussion list --json` returns `{"discussions":[...],"next":...,"totalCount":...}`, so filter with `--jq '.discussions[].title'`. `gh discussion view` also accepts a comment URL (`.../discussions/123#discussioncomment-456`) to show one full reply thread, and `--comments` cannot be combined with `--json`.

`gh pr revert <number>` (opens a PR reverting a merged PR) is a regular command, not a preview - see [pull_requests.md](references/pull_requests.md).

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
- [pull_requests.md](references/pull_requests.md) - PR workflows, CI checks, review threads
- [issues.md](references/issues.md) - Issue management
- [actions.md](references/actions.md) - GitHub Actions, run attempts, reruns
- [releases.md](references/releases.md) - Release management

**Setup & Configuration:**
- [getting_started.md](references/getting_started.md) - `gh auth setup-git` credential helper
- [other.md](references/other.md) - Environment variables, auth traps, aliases, config
- [extensions.md](references/extensions.md) - CLI extensions

## Resources

- Official docs: https://cli.github.com/manual/
- GitHub CLI: https://github.com/cli/cli
- Search syntax: https://docs.github.com/en/search-github
