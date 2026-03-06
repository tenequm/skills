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

When using negative search qualifiers (prefixed with `-`), you need special syntax to prevent the shell from interpreting the hyphen as a flag.

### Unix/Linux/Mac

Use `--` to mark the end of flags:

```bash
# ✅ Correct
gh search issues -- "bug report -label:wontfix"
gh search repos -- "typescript -topic:deprecated"
gh search code -- "TODO -filename:test"

# ❌ Wrong - shell interprets -label as a flag
gh search issues "bug report -label:wontfix"
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

Limited wildcard support:

```bash
# ✅ Wildcards work in some contexts
gh search code "function*" --language=typescript
gh search repos "react-*" in:name

# ❌ Wildcards don't work everywhere
gh search repos "created:>2024-*"  # Doesn't work with dates
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

File contents from the API are base64-encoded:

```bash
# ✅ Correct - decode with base64 -d
gh api repos/owner/repo/contents/file.ts | jq -r '.content' | base64 -d

# ❌ Wrong - outputs base64 gibberish
gh api repos/owner/repo/contents/file.ts | jq -r '.content'
```

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

```bash
# Check rate limit status
gh api rate_limit

# Authenticated requests have higher limits
# Unauthenticated: 60 requests/hour
# Authenticated: 5000 requests/hour
```

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

Before using in scripts, test the field name:

```bash
# Check available fields
gh repo view owner/repo --json | jq keys

# Check search result fields
gh search repos "query" --json | jq '.[0] | keys'
```

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
