# Discovering Trending Content

Complete guide to finding popular repositories, code patterns, and active projects on GitHub.

## Find Trending Repositories

### By popularity

```bash
# Most starred repositories (all time)
gh search repos --sort stars --order desc --limit 20

# Most forked repos
gh search repos --sort forks --order desc

# Most help-wanted issues (NOT a watchers sort - there is none)
gh search repos --sort help-wanted-issues --order desc
```

`gh search repos --sort` accepts only `{forks|help-wanted-issues|stars|updated}`. Watcher counts are available per-repo via `gh repo view OWNER/REPO --json watchers`, but you cannot sort search results by them.

### By language

```bash
# Trending repos in specific language
gh search repos --language=rust --sort stars --order desc
gh search repos --language=typescript --sort stars --order desc
gh search repos --language=python --sort stars --order desc
```

### By recency

```bash
# Recently popular (created in last month, sorted by stars)
gh search repos "created:>2024-10-01" --sort stars --order desc

# Created this year
gh search repos "created:>2024-01-01" --sort stars --order desc

# Recently updated popular repos
gh search repos "stars:>100 pushed:>2024-10-01" --sort updated --order desc
```

### By topic

```bash
# Trending in specific topic
gh search repos "topic:machine-learning" --sort stars --order desc
gh search repos "topic:blockchain" --sort stars --order desc
gh search repos "topic:react" --sort stars --order desc

# Multiple topics (AND)
gh search repos "topic:blockchain topic:typescript" --sort stars --order desc
```

### By activity

```bash
# Most active repos (by recent updates)
gh search repos --sort updated --order desc

# Active repos (many recent commits)
gh search repos "pushed:>2024-10-01" --sort stars

# Repos with many open issues (active community)
gh search repos "good-first-issues:>5" --sort stars --order desc
```

## Advanced Discovery Queries

### Unique projects

```bash
# Repos with many stars but few forks (unique ideas)
gh search repos "stars:>1000 forks:<100"

# High star-to-fork ratio (original content)
gh search repos "stars:>500 forks:<50"
```

### By file presence

Use `--filename`, `--extension`, and `--match` to scope. Code search has no sorting flags. (The `--filename` flag and an in-query `filename:` qualifier are equivalent - `gh` translates the flag into the qualifier - so either form works.)

```bash
# Find repos by file presence (e.g., has Dockerfile)
gh search code --filename Dockerfile

# Has specific config files
gh search code --filename vite.config.ts
gh search code --filename wxt.config.ts

# Restrict matching to the file path vs file contents
gh search code react --match path --extension tsx
```

### By description keywords

```bash
# Combined filters: Popular Solana repos updated recently
gh search repos "solana in:name,description stars:>100" --sort updated --order desc

# Specific keywords in description
gh search repos "machine learning in:description stars:>1000"
```

### By size and license

```bash
# Small but popular repos (easy to learn from)
gh search repos "stars:>1000 size:<1000" --language=typescript

# Specific license
gh search repos "license:mit stars:>500" --language=rust
```

### By organization

```bash
# Popular repos from specific org
gh search repos "org:vercel stars:>100"
gh search repos "org:anthropics"
```

## Discover Popular Code Patterns

### Find implementations

```bash
# Find implementations (code search has no sorting - scope with --language/--owner/--repo)
gh search code "function useWallet" --language=typescript
gh search code "async fn main" --language=rust

# Specific patterns
gh search code "createContext" --language=typescript
gh search code "impl Display for" --language=rust
```

### By repository

Code search cannot sort by stars, and a `stars:>N` qualifier in the query is matched as literal file text, not a popularity filter. To find code in known-popular repos, first discover the repos with `gh search repos`, then scope code search to them with `--owner`/`--repo`.

```bash
# Scope code search to a specific owner or repo
gh search code "authentication" --language=typescript --owner=vercel
gh search code "middleware" --repo=honojs/hono

# Two-step: find popular repos, then search their code
gh search repos "topic:web-framework stars:>1000" --json fullName --jq '.[].fullName'
gh search code "middleware" --repo=<one-of-the-above>
```

### By organization

```bash
# Search specific organization's popular code
gh search code "authentication" --owner=anthropics
gh search code "config" --owner=vercel
```

### By recency

**Code search has no date filter.** `created:` is not a code-search qualifier - it is matched as literal file text, so `gh search code "React hooks" "created:>2024-01-01"` returns files that literally contain that string (this very page has been a top hit for it). To find recent code, discover recently-pushed repos first, then scope code search to them:

```bash
# 1. Find recently active repos
gh search repos "topic:react pushed:>2026-06-01" --json fullName --jq '.[].fullName'

# 2. Search code within one
gh search code "useEffect" --repo=<one-of-the-above>
```

## Combining Filters

### Examples of powerful combinations

```bash
# Popular TypeScript repos updated this month
gh search repos "language:typescript stars:>500 pushed:>2024-10-01" --sort updated

# New promising projects (recent, growing fast)
gh search repos "created:>2024-06-01 stars:>100" --sort stars --order desc

# Active open-source with good first issues
gh search repos "good-first-issues:>3 stars:>100 pushed:>2024-10-01"

# Well-maintained projects (recent activity + documentation)
gh search repos "stars:>1000 pushed:>2024-10-01" --language=typescript | grep -i "readme"
```

## Qualifiers Reference

### Date qualifiers

- `created:>YYYY-MM-DD` - Created after date
- `created:<YYYY-MM-DD` - Created before date
- `pushed:>YYYY-MM-DD` - Updated after date
- `pushed:<YYYY-MM-DD` - Updated before date

### Numeric qualifiers

- `stars:>N` - More than N stars
- `stars:N..M` - Between N and M stars
- `forks:>N` - More than N forks
- `size:<N` - Smaller than N KB

### Boolean qualifiers

- `is:public` - Public repos
- `is:private` - Private repos (requires auth)
- `archived:false` - Not archived
- `archived:true` - Archived repos

### Location qualifiers

- `in:name` - Search in repo name
- `in:description` - Search in description
- `in:readme` - Search in README
- `in:name,description` - Search in both

## Tips for Discovery

### Start broad, then filter

```bash
# 1. Find all Solana repos
gh search repos "solana"

# 2. Filter by popularity
gh search repos "solana stars:>100"

# 3. Filter by recency
gh search repos "solana stars:>100 pushed:>2024-10-01"

# 4. Add language
gh search repos "solana stars:>100 pushed:>2024-10-01" --language=rust
```

### Use topics for precision

Topics are more precise than text search:

```bash
# Better: Use topic
gh search repos "topic:web3" --sort stars

# Less precise: Text search
gh search repos "web3" --sort stars
```

### Check activity indicators

High stars but old updates = abandoned:

```bash
# Good: Popular AND recently updated
gh search repos "stars:>1000 pushed:>2024-10-01"

# Risk: Popular but potentially stale
gh search repos "stars:>1000"
```

### Look for hidden gems

Sometimes the best code isn't the most popular:

```bash
# Well-maintained but not famous
gh search repos "stars:10..100 pushed:>2024-10-01" --language=rust

# Recent projects gaining traction
gh search repos "created:>2024-09-01 stars:>10" --sort stars
```

## Output formatting

### Get specific fields

```bash
# Just repo names
gh search repos "topic:react" --json name --jq '.[].name'

# Name and star count
gh search repos "topic:react" --limit 5 --json name,stargazersCount --jq '.[] | "\(.name): \(.stargazersCount) stars"'

# Full URLs
gh search repos "topic:rust" --json url --jq '.[].url'
```

### Limit results

```bash
# Top 10 only
gh search repos "language:typescript" --sort stars --limit 10

# Top 50
gh search repos "topic:machine-learning" --limit 50
```

## Common Discovery Workflows

### "Find similar repos to X"

```bash
# 1. Check topics of repo X
gh repo view OWNER/REPO --json repositoryTopics

# 2. Search by those topics
gh search repos "topic:web3 topic:solana" --sort stars --order desc
```

### "What's trending in [language] this month?"

```bash
gh search repos "language:rust created:>2024-10-01" --sort stars --order desc --limit 20
```

### "Find actively maintained [topic] projects"

```bash
gh search repos "topic:blockchain pushed:>2024-10-01 stars:>50" --sort updated --order desc
```

### "Discover new tools for [task]"

```bash
# Example: PDF processing tools
gh search repos "pdf in:name,description language:python stars:>50" --sort stars
```
