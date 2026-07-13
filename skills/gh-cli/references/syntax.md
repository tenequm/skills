# Special Syntax & Command Quirks

GitHub CLI has several syntax inconsistencies and special cases to be aware of.

## Field Name Inconsistencies

**CRITICAL:** Different commands use different field names for the same data.

### Stars field

| Command | Field Name |
|---------|-----------|
| `gh repo view` | `stargazerCount` |
| `gh search repos` | `stargazersCount` |

**Examples:**

```bash
# ✅ Correct for gh repo view
gh repo view anthropics/anthropic-sdk-python --json stargazerCount

# ✅ Correct for gh search repos
gh search repos "anthropics" --json stargazersCount

# ❌ Wrong - will error
gh repo view anthropics/anthropic-sdk-python --json stargazersCount
gh search repos "anthropics" --json stargazerCount
```

### Forks field

| Command | Field Name |
|---------|-----------|
| `gh repo view` | `forkCount` |
| `gh search repos` | `forksCount` |

**Examples:**

```bash
# ✅ Correct
gh repo view owner/repo --json forkCount
gh search repos "query" --json forksCount

# ❌ Wrong
gh repo view owner/repo --json forksCount
gh search repos "query" --json forkCount
```

### Quick reference table

| Data | `gh repo view` | `gh search repos` |
|------|----------------|-------------------|
| Stars | `stargazerCount` | `stargazersCount` |
| Forks | `forkCount` | `forksCount` |
| Topics | `repositoryTopics` | `repositoryTopics` |
| Description | `description` | `description` |
| URL | `url` | `url` |

## Negative Qualifiers

A negative qualifier (prefixed with `-`) inside a quoted query is fine as long as the query does not **begin** with the hyphen:

```bash
# ✅ Works without `--` - query starts with a word
gh search issues "bug report -label:wontfix"

# ❌ Fails - query starts with a hyphen, parsed as a flag
gh search issues "-label:wontfix bug"
# unknown shorthand flag: 'l' in -label:wontfix bug
```

### Use `--`, and put flags before it

`--` marks the end of flags, so a query starting with a hyphen is read as positional. **Everything after `--` is positional** - trailing flags are silently swallowed into the query string:

```bash
# ✅ Correct - flags precede `--`
gh search issues --limit 5 -- "-label:wontfix bug"

# ❌ Wrong - `--limit 5` becomes search text; returns the default 30 results
gh search issues -- "-label:wontfix bug" --limit 5
```

### PowerShell

Use `--%` (stop parsing) operator:

```bash
# ✅ Correct
gh --% search issues -- "bug report -label:wontfix"
gh --% search repos -- "rust -archived:true"

# ❌ Wrong
gh search issues "bug report -label:wontfix"
```

### Common negative qualifiers

```bash
# Exclude labels
gh search issues -- "bug -label:wontfix -label:duplicate"

# Exclude topics
gh search repos -- "web framework -topic:deprecated"

# Exclude archived repos
gh search repos -- "stars:>100 -archived:true"

# Exclude specific languages
gh search code -- "config -language:json"

# Exclude filenames
gh search code -- "authentication -filename:test -filename:spec"
```

## Date Format Quirks

### ISO 8601 format required

```bash
# ✅ Correct
gh search repos "created:>2024-10-01"
gh search repos "pushed:<2024-12-31"

# ❌ Wrong
gh search repos "created:>10/01/2024"  # US format doesn't work
gh search repos "created:>2024/10/01"  # Slashes don't work
```

### Date ranges

```bash
# Between dates
gh search repos "created:2024-01-01..2024-06-30"

# Relative dates work in some contexts
gh search repos "pushed:>2024-10-01"  # After October 1st

# Time is optional (defaults to start of day)
gh search repos "created:>2024-10-01T12:00:00Z"  # With time
gh search repos "created:>2024-10-01"  # Without time (00:00:00)
```

## Search Syntax Gotchas

### Spaces in queries

Wrap multi-word queries in quotes:

```bash
# ✅ Correct
gh search code "error handling" --language=python
gh search repos "machine learning" --sort stars

# ❌ Wrong - treats each word as separate argument
gh search code error handling --language=python
```

### Boolean operators

GitHub search doesn't support traditional AND/OR/NOT:

```bash
# ✅ Use qualifiers instead
gh search repos "topic:react topic:typescript"  # Implicit AND
gh search issues -- "bug -label:wontfix"  # Implicit NOT

# ❌ Wrong - literal text search
gh search repos "react AND typescript"
gh search repos "bug NOT wontfix"
```

### Wildcards

GitHub code search has **no `*` wildcard** - an asterisk is matched as a literal character. `gh search code "function*"` returns files containing the literal token `function*` (e.g. JS generator declarations), not every word starting with "function".

```bash
# ❌ Not a wildcard - matches the literal string "function*"
gh search code "function*" --language=typescript

# ✅ Scope with flags instead
gh search code "function" --language=typescript --filename hooks.ts
```

## JSON Output Quirks

### jq is required for field extraction

```bash
# ✅ Correct - use jq to extract fields
gh api repos/owner/repo/contents/file.ts | jq -r '.content'

# ❌ Wrong - raw output is base64 + JSON
gh api repos/owner/repo/contents/file.ts
```

### Array handling

```bash
# ✅ Correct - iterate array
gh search repos "topic:rust" --json name --jq '.[].name'

# ❌ Wrong - returns raw JSON array
gh search repos "topic:rust" --json name
```

### Null handling

```bash
# ✅ Correct - handle nulls
gh api repos/owner/repo/contents/path | jq -r '.content // empty'

# ❌ Wrong - errors on null
gh api repos/owner/repo/contents/path | jq -r '.content'
```

## API Endpoint Quirks

### Base64 encoding

The Contents API returns file content base64-encoded. There is **no `base64decode` template function** in `gh` - `--template '{{.content | base64decode}}'` fails with `template: :1: function "base64decode" not defined`. The full function list is in `gh help formatting`.

```bash
# ✅ Best - purpose-built command, no decoding needed
gh repo read-file file.ts --repo owner/repo

# ✅ Ask the API for raw bytes
gh api repos/owner/repo/contents/file.ts -H "Accept: application/vnd.github.raw"

# ✅ Or decode the JSON response yourself
gh api repos/owner/repo/contents/file.ts --jq '.content' | base64 -d

# ❌ Wrong - no such template function
gh api repos/owner/repo/contents/file.ts --template '{{.content | base64decode}}'
```

The Contents API only inlines files up to **1MB**; past that, `.content` comes back empty. `gh repo read-file` falls back to raw fetching automatically, which is why it is the safer default.

### Recursive tree flag

For recursive directory listings, use query parameter:

```bash
# ✅ Correct
gh api repos/owner/repo/git/trees/main?recursive=1

# ❌ Wrong - returns only top level
gh api repos/owner/repo/git/trees/main
```

### Ref parameter

Specify branch/tag/commit with `ref`:

```bash
# ✅ Correct
gh api repos/owner/repo/contents/file.ts?ref=dev
gh api repos/owner/repo/contents/file.ts?ref=v1.0.0
gh api repos/owner/repo/contents/file.ts?ref=abc123

# ❌ Wrong - uses default branch
gh api repos/owner/repo/contents/file.ts
```

## Pagination

### Default limits

Different commands have different default limits:

```bash
# gh search commands default to 30 results
gh search repos "topic:rust"  # Returns max 30

# Specify limit explicitly
gh search repos "topic:rust" --limit 100  # Max 100

# API commands may paginate automatically
gh api repos/owner/repo/issues  # May return all or paginate
```

### Manual pagination

```bash
# Use --paginate for API calls
gh api --paginate repos/owner/repo/issues

# Search commands have hard limit of 1000 total results
gh search repos "topic:python" --limit 1000
```

## Permission Errors

### Authentication required

Some operations require authentication:

```bash
# Works without auth
gh search repos "topic:rust"
gh api repos/owner/repo/contents/README.md

# Requires auth
gh repo view owner/private-repo
gh search repos "is:private"

# Set token
export GH_TOKEN="your_token"
# or
gh auth login
```

### Rate limiting

Rate limits are **per-resource**, and search is far tighter than the core budget most people quote:

| Resource | Unauthenticated | Authenticated |
|----------|-----------------|---------------|
| `core` (`gh api`, `gh repo view`, `gh repo read-file`) | 60/hr | 5000/hr |
| `search` (repos, issues, prs, commits) | 10/min | 30/min |
| `code_search` | n/a | 10/min |
| `graphql` | n/a | 5000/hr |

```bash
# Check every resource's live limit and remaining budget
gh api rate_limit --jq '.resources | map_values({limit, remaining})'
```

A search-heavy loop exhausts the 30/min search budget long before it dents the 5000/hr core budget. Search also caps at **1000 total results** per query regardless of `--limit`.

## Quoting Rules

### Shell quoting

```bash
# ✅ Double quotes for variables
gh api repos/$OWNER/$REPO/contents/file.ts

# ✅ Single quotes for literal strings
gh search code 'function*'

# ✅ Escape special chars in double quotes
gh search repos "name with \"quotes\""
```

### JSON quoting in --json

```bash
# ✅ Comma-separated field list
gh repo view owner/repo --json name,description,stargazerCount

# ❌ Wrong - no quotes around field names
gh repo view owner/repo --json "name","description"

# ❌ Wrong - spaces
gh repo view owner/repo --json name, description
```

## Command-Specific Quirks

### gh search code has no sorting

`gh search code` is powered by GitHub's legacy code-search engine and supports **no** `--sort`/`--order` flags - passing them fails with `unknown flag: --sort`. A `stars:>N` (or similar repo-popularity) qualifier inside the query is matched as literal file text, not a filter. Scope results with the available flags instead:

```bash
# ✅ Available scoping flags
gh search code "useWallet" --language=typescript --owner=vercel
gh search code --filename Dockerfile --extension dockerfile
gh search code react --match path   # match file path vs file contents {file|path}

# ❌ Wrong - no such flag on code search
gh search code "useWallet" --sort indexed
gh search code "useWallet" --sort stars
```

`--sort`/`--order` *do* work on `gh search repos` ({forks|help-wanted-issues|stars|updated}) and `gh search issues`/`gh search prs` - it is only code search that dropped them.

### gh search vs gh api

Different approaches for different use cases:

```bash
# Use gh search for discovery
gh search repos "topic:rust" --sort stars

# Use gh api for precise data
gh api repos/owner/repo --jq '.stargazers_count'
```

### gh repo view vs gh api

Field names differ:

```bash
# gh repo view uses camelCase
gh repo view owner/repo --json stargazerCount

# gh api uses snake_case
gh api repos/owner/repo --jq '.stargazers_count'
```

## Common Errors

### "No field named X"

You used the wrong field name for the command:

```bash
# Error: "No field named stargazersCount"
gh repo view owner/repo --json stargazersCount

# Fix: use stargazerCount for gh repo view
gh repo view owner/repo --json stargazerCount
```

### "Not Found (404)"

File doesn't exist or wrong ref:

```bash
# Check file exists in branch
gh api repos/owner/repo/contents/path/file.ts?ref=main

# Try different ref
gh api repos/owner/repo/contents/path/file.ts?ref=dev
```

### "Bad credentials"

Authentication issue:

```bash
# Check auth status
gh auth status

# Re-authenticate
gh auth login
```

## Tips

### Always test field names

Run the command with a bare `--json` to list the valid fields. Note it writes the list to **stderr** and exits non-zero, so piping it to `jq` yields nothing:

```bash
# ✅ Correct - prints the available field list
gh repo view owner/repo --json
gh search repos "query" --json

# ❌ Wrong - stdout is empty, jq prints nothing
gh repo view owner/repo --json | jq keys
```

An empty JSON result from `--json` usually means the command errored on an unknown field rather than matching nothing. Re-run it bare to see the error.

### Use --help

Every command has detailed help:

```bash
gh search repos --help
gh api --help
gh repo view --help
```

### Check the manual

For edge cases, check official docs:

- CLI manual: https://cli.github.com/manual/
- Search syntax: https://docs.github.com/en/search-github
- API reference: https://docs.github.com/en/rest
