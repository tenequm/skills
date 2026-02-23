# Search Strategies for Finding Claude Skills

Comprehensive guide to searching GitHub for Claude skills using multiple approaches.

## Overview

Use a **multi-method approach** combining repository search, code search, and pattern matching to find the maximum number of relevant skills.

## Method 1: Repository Search

Find repositories dedicated to Claude skills.

### Basic Repository Search

```bash
gh search repos "claude skills" --sort stars --order desc --limit 20 \
  --json name,stargazersCount,description,url,createdAt,pushedAt,owner
```

### Advanced Repository Queries

```bash
# Skills specifically for Claude Code
gh search repos "claude code skills" --sort stars --limit 20 --json name,stargazersCount,url,pushedAt

# Recent skills (last 30 days)
gh search repos "claude skills" "created:>$(date -v-30d +%Y-%m-%d)" --sort stars --limit 20

# Highly starred skills
gh search repos "claude skills" "stars:>50" --sort stars --limit 20

# Active repositories (recently updated)
gh search repos "claude skills" --sort updated --limit 20

# Repositories with specific topics
gh search repos "topic:claude topic:skills" --sort stars --limit 20
```

### Filter Out Noise

```bash
# Exclude awesome-lists and collections
gh search repos "claude skills" --sort stars --limit 30 | \
  jq '[.[] | select(.name | test("awesome|collection|curated") | not)]'
```

## Method 2: Code Search for SKILL.md

Directly find SKILL.md files across all repositories.

### Basic Code Search

```bash
gh search code "filename:SKILL.md" --limit 30 \
  --json repository,path,url,sha
```

### Path-Specific Searches

```bash
# Skills in .claude/skills directory
gh search code "path:.claude/skills" "filename:SKILL.md" --limit 30

# Skills in skills/ subdirectory (plugin format)
gh search code "path:skills/" "filename:SKILL.md" --limit 30

# Root-level SKILL.md files
gh search code "filename:SKILL.md" "NOT path:/" --limit 30
```

### Content-Based Search

```bash
# Find skills mentioning specific capabilities
gh search code "browser automation" "filename:SKILL.md" --limit 20

# Find MCP-related skills
gh search code "MCP server" "filename:SKILL.md" --limit 20

# Find research/analysis skills
gh search code "web search OR data analysis" "filename:SKILL.md" --limit 20
```

## Method 3: Skill-Specific Pattern Matching

Search for known skill patterns and structures.

### Known Skill Repositories

```bash
# Check popular skill collections
repos=(
  "BehiSecc/awesome-claude-skills"
  "travisvn/awesome-claude-skills"
  "simonw/claude-skills"
  "mrgoonie/claudekit-skills"
)

for repo in "${repos[@]}"; do
  gh api "repos/$repo/git/trees/main?recursive=1" | \
    jq -r '.tree[] | select(.path | contains("SKILL.md")) | .path'
done
```

### Plugin Format Detection

```bash
# Repositories following .claude-plugin structure
gh search code "filename:.claude-plugin" --limit 20 | \
  jq -r '.[] | .repository.full_name' | \
  while read repo; do
    # Check for skills subdirectory
    gh api "repos/$repo/contents/skills" 2>/dev/null | \
      jq -r '.[].name'
  done
```

## Method 4: Organization/User-Based Search

Find skills from known skill creators.

### Popular Skill Authors

```bash
# Search by user
users=(
  "lackeyjb"        # playwright-skill
  "FrancyJGLisboa"  # agent-skill-creator
  "alirezarezvani"  # skill factory
)

for user in "${users[@]}"; do
  gh search repos "user:$user" "SKILL.md" --limit 10
done
```

### Organization Search

```bash
# Search within organizations
gh search repos "org:anthropics" "skills" --limit 20
gh search repos "org:skills-directory" --limit 20
```

## Combining Results

### Deduplication Strategy

```bash
# Collect all results
all_repos=()

# From repository search
repos1=$(gh search repos "claude skills" --json name,owner | jq -r '.[] | "\(.owner.login)/\(.name)"')

# From code search
repos2=$(gh search code "filename:SKILL.md" --json repository | jq -r '.[].repository.full_name' | sort -u)

# Combine and deduplicate
all_repos=($(echo "$repos1 $repos2" | tr ' ' '\n' | sort -u))

# Fetch metadata for unique repos
for repo in "${all_repos[@]}"; do
  gh api "repos/$repo" --jq '{
    name: .name,
    full_name: .full_name,
    stars: .stargazers_count,
    updated: .pushed_at,
    description: .description
  }'
done
```

## Search Optimization

### Parallel Execution

```bash
# Run all searches in parallel for speed
{
  gh search repos "claude skills" --limit 20 > repos.json &
  gh search code "filename:SKILL.md" --limit 30 > code.json &
  gh search code "path:.claude/skills" --limit 20 > paths.json &
  wait
}

# Merge results
jq -s 'add | unique_by(.repository.full_name)' repos.json code.json paths.json
```

### Caching Results

```bash
# Cache results to avoid hitting rate limits
cache_file=".skill-finder-cache.json"
cache_ttl=3600  # 1 hour

if [ -f "$cache_file" ] && [ $(($(date +%s) - $(stat -f %m "$cache_file"))) -lt $cache_ttl ]; then
  # Use cached results
  cat "$cache_file"
else
  # Fetch fresh results and cache
  gh search repos "claude skills" --limit 50 > "$cache_file"
  cat "$cache_file"
fi
```

## Category-Specific Searches

### Automation Skills

```bash
gh search code "playwright OR selenium OR puppeteer" "filename:SKILL.md"
gh search code "browser automation OR web automation" "filename:SKILL.md"
```

### Research Skills

```bash
gh search code "web search OR research OR analysis" "filename:SKILL.md"
gh search code "data collection OR scraping" "filename:SKILL.md"
```

### Development Skills

```bash
gh search code "git OR github OR code review" "filename:SKILL.md"
gh search code "testing OR linting OR formatting" "filename:SKILL.md"
```

### Integration Skills

```bash
gh search code "MCP server OR API integration" "filename:SKILL.md"
gh search code "webhook OR external service" "filename:SKILL.md"
```

## Quality Filters

### Star-Based Filtering

```bash
# Only repos with 10+ stars
gh search repos "claude skills" "stars:>=10" --limit 20

# Trending (many stars, recently created)
gh search repos "claude skills" "stars:>50" "created:>2025-01-01" --limit 20
```

### Activity-Based Filtering

```bash
# Updated in last 30 days
gh search repos "claude skills" "pushed:>$(date -v-30d +%Y-%m-%d)" --limit 20

# Active development (multiple commits recently)
gh api graphql -f query='
{
  search(query: "claude skills sort:updated", type: REPOSITORY, first: 20) {
    nodes {
      ... on Repository {
        name
        stargazerCount
        pushedAt
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 10) {
                totalCount
              }
            }
          }
        }
      }
    }
  }
}'
```

## Error Handling

### Rate Limit Checking

```bash
# Check remaining API calls
gh api rate_limit | jq '.rate.remaining'

# If low, wait or authenticate
if [ $(gh api rate_limit | jq '.rate.remaining') -lt 10 ]; then
  echo "⚠️  Low on API calls. Waiting..."
  sleep 60
fi
```

### Fallback Strategies

```bash
# If authenticated search fails, try unauthenticated
gh search repos "claude skills" --limit 10 2>/dev/null || \
  curl -s "https://api.github.com/search/repositories?q=claude+skills&per_page=10"
```

## Performance Benchmarks

| Method | API Calls | Results | Speed | Best For |
|--------|-----------|---------|-------|----------|
| Repository search | 1 | 20-30 | Fast | Popular skills |
| Code search | 1 | 30-50 | Medium | All skills |
| Recursive tree | N repos | 50+ | Slow | Completeness |
| Combined | 3-5 | 100+ | Medium | Best coverage |

## Recommended Workflow

1. **Quick search** (1 API call, <5 sec):
   ```bash
   gh search repos "claude skills" --limit 20
   ```

2. **Comprehensive search** (3 API calls, ~15 sec):
   ```bash
   # Parallel execution
   gh search repos "claude skills" &
   gh search code "filename:SKILL.md" &
   gh search code "path:.claude/skills" &
   wait
   ```

3. **Deep search** (10+ API calls, ~60 sec):
   - All of the above
   - Repository tree traversal
   - Organization searches
   - Known author searches

Choose based on user needs and time constraints.
