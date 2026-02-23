# Ranking Algorithm for Claude Skills

Comprehensive scoring system to rank skills by popularity, freshness, and quality.

## Core Ranking Formula

```
final_score = (base_stars * freshness_multiplier * quality_bonus)
```

## Component 1: Base Stars

Direct indicator of community validation and popularity.

```bash
base_stars = repository.stargazers_count

# Minimum threshold: 10 stars (filter out experiments)
if [ $base_stars -lt 10 ]; then
  skip_result=true
fi
```

## Component 2: Freshness Multiplier

Recent updates indicate active maintenance and modern practices.

### Calculate Days Since Last Update

```bash
# Get pushed_at timestamp from repository
pushed_at="2025-10-28T12:00:00Z"

# Calculate days old (macOS)
days_old=$(( ($(date +%s) - $(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$pushed_at" +%s)) / 86400 ))

# Calculate days old (Linux)
days_old=$(( ($(date +%s) - $(date -d "$pushed_at" +%s)) / 86400 ))
```

### Apply Freshness Multiplier

```bash
if [ $days_old -lt 30 ]; then
  freshness_multiplier=1.5
  freshness_badge="🔥"
  freshness_label="Hot"
elif [ $days_old -lt 90 ]; then
  freshness_multiplier=1.2
  freshness_badge="📅"
  freshness_label="Recent"
elif [ $days_old -lt 180 ]; then
  freshness_multiplier=1.0
  freshness_badge="📆"
  freshness_label="Active"
else
  freshness_multiplier=0.5
  freshness_badge="⏰"
  freshness_label="Older"
fi
```

### Freshness Tiers

| Age Range | Multiplier | Badge | Label | Reasoning |
|-----------|------------|-------|-------|-----------|
| < 30 days | 1.5x | 🔥 | Hot | Very active, likely works with latest Claude |
| 30-90 days | 1.2x | 📅 | Recent | Active maintenance |
| 90-180 days | 1.0x | 📆 | Active | Stable, still maintained |
| > 180 days | 0.5x | ⏰ | Older | May be outdated or abandoned |

## Component 3: Quality Bonus (Optional)

Additional signals of skill quality beyond stars and freshness.

### Quality Signals

```bash
quality_bonus=1.0  # Start at neutral

# Has comprehensive description
if [ ${#description} -gt 100 ]; then
  quality_bonus=$(echo "$quality_bonus + 0.1" | bc)
fi

# Has reference files
reference_count=$(gh api "repos/$repo/contents" | jq '[.[] | select(.name | test("references|docs|examples"))] | length')
if [ $reference_count -gt 0 ]; then
  quality_bonus=$(echo "$quality_bonus + 0.1" | bc)
fi

# Has dependencies documentation
if gh api "repos/$repo/contents" | jq -e '.[] | select(.name == "package.json")' > /dev/null; then
  quality_bonus=$(echo "$quality_bonus + 0.05" | bc)
fi

# Active issues/PRs indicate engagement
open_issues=$(gh api "repos/$repo" | jq '.open_issues_count')
if [ $open_issues -gt 0 ] && [ $open_issues -lt 20 ]; then
  quality_bonus=$(echo "$quality_bonus + 0.05" | bc)
fi

# Has recent commits (beyond just pushed_at)
recent_commits=$(gh api "repos/$repo/commits?per_page=10" | jq 'length')
if [ $recent_commits -ge 5 ]; then
  quality_bonus=$(echo "$quality_bonus + 0.1" | bc)
fi

# Cap quality bonus at 1.5x
if (( $(echo "$quality_bonus > 1.5" | bc -l) )); then
  quality_bonus=1.5
fi
```

### Quality Tier Examples

| Quality Bonus | Characteristics |
|---------------|-----------------|
| 1.0x (baseline) | Basic SKILL.md only |
| 1.1x | + Good description |
| 1.2x | + Reference files |
| 1.3x | + Dependencies documented |
| 1.4x | + Active community (issues/PRs) |
| 1.5x (max) | All of the above |

## Complete Scoring Implementation

### Bash Implementation

```bash
#!/bin/bash

calculate_score() {
  local repo=$1
  local stars=$2
  local pushed_at=$3

  # Calculate days since last update
  days_old=$(( ($(date +%s) - $(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$pushed_at" +%s)) / 86400 ))

  # Freshness multiplier
  if [ $days_old -lt 30 ]; then
    freshness=1.5
    badge="🔥"
  elif [ $days_old -lt 90 ]; then
    freshness=1.2
    badge="📅"
  elif [ $days_old -lt 180 ]; then
    freshness=1.0
    badge="📆"
  else
    freshness=0.5
    badge="⏰"
  fi

  # Calculate final score
  score=$(echo "$stars * $freshness" | bc)

  echo "$score|$badge|$days_old"
}

# Example usage
result=$(calculate_score "lackeyjb/playwright-skill" 612 "2025-10-28T12:00:00Z")
score=$(echo "$result" | cut -d'|' -f1)
badge=$(echo "$result" | cut -d'|' -f2)
days=$(echo "$result" | cut -d'|' -f3)

echo "Score: $score, Badge: $badge, Days: $days"
# Output: Score: 918.0, Badge: 🔥, Days: 2
```

### JQ Implementation (More Portable)

```bash
gh search repos "claude skills" --json name,stargazersCount,pushedAt --limit 20 | \
  jq -r --arg now "$(date -u +%s)" '.[] |
    . as $repo |
    ($repo.pushedAt | fromdateiso8601) as $pushed |
    (($now | tonumber) - $pushed) / 86400 | floor as $days |
    (if $days < 30 then 1.5 elif $days < 90 then 1.2 elif $days < 180 then 1.0 else 0.5 end) as $multiplier |
    (if $days < 30 then "🔥" elif $days < 90 then "📅" elif $days < 180 then "📆" else "⏰" end) as $badge |
    ($repo.stargazersCount * $multiplier) as $score |
    "\($score)|\($repo.name)|\($repo.stargazersCount)|\($badge)|\($days)"
  ' | sort -t'|' -k1 -nr | head -10
```

## Ranking Examples

### Real-World Scores

| Skill | Stars | Days Old | Freshness | Multiplier | Final Score | Rank |
|-------|-------|----------|-----------|------------|-------------|------|
| playwright-skill | 612 | 2 | 🔥 | 1.5x | **918** | #1 |
| agent-skill-creator | 96 | 5 | 🔥 | 1.5x | **144** | #2 |
| skill-codex | 153 | 9 | 🔥 | 1.5x | **229.5** | Would be #2, but bumped by age |
| ios-simulator-skill | 77 | 2 | 🔥 | 1.5x | **115.5** | #3 |
| claude-skills-mcp | 85 | 2 | 🔥 | 1.5x | **127.5** | #4 |

*With hot multiplier, even 77 stars beats 96 stars from 30+ days ago*

### Score Comparison Scenarios

**Scenario 1: Fresh skill vs. Popular old skill**
- Skill A: 50 stars, 10 days old → 50 × 1.5 = **75 points** 🔥
- Skill B: 100 stars, 200 days old → 100 × 0.5 = **50 points** ⏰
- **Winner: Skill A** (freshness wins)

**Scenario 2: Very popular but older skill**
- Skill A: 1000 stars, 365 days old → 1000 × 0.5 = **500 points** ⏰
- Skill B: 200 stars, 15 days old → 200 × 1.5 = **300 points** 🔥
- **Winner: Skill A** (massive popularity overcomes age)

**Scenario 3: Moderate skill, regularly updated**
- Skill A: 50 stars, 85 days old → 50 × 1.2 = **60 points** 📅
- Skill B: 60 stars, 95 days old → 60 × 1.0 = **60 points** 📆
- **Tie** (freshness threshold matters)

## Handling Edge Cases

### Newly Created Skills (< 7 days old)

```bash
# New skills may have inflated scores, add small penalty
if [ $days_old -lt 7 ]; then
  new_skill_penalty=0.9
  score=$(echo "$score * $new_skill_penalty" | bc)
  note="⚠️ Very new skill - limited validation"
fi
```

### Archived or Deprecated Skills

```bash
# Check if repository is archived
is_archived=$(gh api "repos/$repo" | jq -r '.archived')

if [ "$is_archived" = "true" ]; then
  score=0  # Exclude from results
  note="🔒 Archived - no longer maintained"
fi
```

### Fork vs. Original

```bash
# Check if repository is a fork
is_fork=$(gh api "repos/$repo" | jq -r '.fork')

if [ "$is_fork" = "true" ]; then
  # Check if fork has more stars than parent
  parent_stars=$(gh api "repos/$repo" | jq -r '.parent.stargazers_count')
  if [ $stars -gt $parent_stars ]; then
    # Fork is more popular, keep it
    note="🍴 Popular fork"
  else
    # Prefer original
    score=$(echo "$score * 0.8" | bc)
    note="🍴 Fork - see original"
  fi
fi
```

## Sorting and Display

### Final Sort Order

```bash
# Sort by score (descending), then by stars (descending)
results | sort -t'|' -k1,1nr -k3,3nr | head -10
```

### Ties

When scores are identical:
1. Sort by stars (higher first)
2. If still tied, sort by freshness (newer first)
3. If still tied, sort alphabetically

```bash
# Multi-level sort
jq -r '.[] | "\(.score)|\(.stars)|\(.days_old)|\(.name)"' | \
  sort -t'|' -k1,1nr -k2,2nr -k3,3n -k4,4
```

## Performance Optimization

### Bulk Scoring

```bash
# Score all repos in one pass
gh search repos "claude skills" --json name,stargazersCount,pushedAt,fullName --limit 50 | \
  jq -r --arg now "$(date -u +%s)" '
    .[] |
    . as $repo |
    ($repo.pushedAt | fromdateiso8601) as $pushed |
    (($now | tonumber) - $pushed) / 86400 | floor as $days |
    (if $days < 30 then 1.5 elif $days < 90 then 1.2 elif $days < 180 then 1.0 else 0.5 end) as $mult |
    ($repo.stargazersCount * $mult) as $score |
    {
      name: $repo.name,
      full_name: $repo.fullName,
      stars: $repo.stargazersCount,
      days_old: $days,
      score: $score
    }
  ' | jq -s 'sort_by(-.score) | .[0:10]'
```

### Caching Scores

```bash
# Cache scores to avoid recalculation
score_cache=".skill-scores.json"

# Generate or load cache
if [ ! -f "$score_cache" ] || [ $(($(date +%s) - $(stat -f %m "$score_cache"))) -gt 3600 ]; then
  # Regenerate cache (older than 1 hour)
  calculate_all_scores > "$score_cache"
fi

# Use cached scores
cat "$score_cache" | jq '.[] | select(.score > 50)'
```

## Customization

### User-Defined Weights

Allow users to adjust ranking preferences:

```bash
# Default weights
STAR_WEIGHT=1.0
FRESHNESS_WEIGHT=1.0
QUALITY_WEIGHT=0.5

# Calculate weighted score
weighted_score=$(echo "$stars * $STAR_WEIGHT + $freshness_score * $FRESHNESS_WEIGHT + $quality_score * $QUALITY_WEIGHT" | bc)
```

### Category-Specific Ranking

Different categories may value different factors:

```bash
# For automation skills: prioritize quality (working code)
if [ "$category" = "automation" ]; then
  QUALITY_WEIGHT=1.5
fi

# For research skills: prioritize freshness (up-to-date sources)
if [ "$category" = "research" ]; then
  FRESHNESS_WEIGHT=1.5
fi
```

---

**Summary:** The ranking algorithm balances popularity (stars) with recency (freshness), ensuring users see both well-established skills and cutting-edge new capabilities. Quality signals provide additional nuance for edge cases.
