# Configuration and Workflows

## Config File Schema

Config files are JSON files used with `--config` or the `unified` command.

### Basic Scraping Config

```json
{
  "name": "react",
  "base_url": "https://react.dev",
  "start_urls": ["https://react.dev/learn", "https://react.dev/reference"],
  "max_pages": 200,
  "rate_limit": 0.5,
  "output_dir": "output/react",
  "selectors": {
    "content": "article, main, .content",
    "title": "h1",
    "code": "pre code"
  },
  "exclude_patterns": ["/blog/*", "/community/*"],
  "enhance_level": 2
}
```

### GitHub Config

```json
{
  "name": "typescript",
  "source": "github",
  "repo": "microsoft/TypeScript",
  "github_token": "${GITHUB_TOKEN}",
  "include_issues": true,
  "max_issues": 50,
  "include_changelog": true,
  "include_releases": true,
  "enhance_level": 2
}
```

### Unified (Multi-Source) Config

Combine multiple sources into one skill:

```json
{
  "name": "django-complete",
  "sources": [
    {
      "type": "docs",
      "base_url": "https://docs.djangoproject.com/en/5.0/",
      "max_pages": 300
    },
    {
      "type": "github",
      "repo": "django/django",
      "max_issues": 50
    },
    {
      "type": "pdf",
      "path": "./django-deployment-guide.pdf"
    }
  ],
  "merge_mode": "rule-based",
  "output_dir": "output/django-complete",
  "enhance_level": 2
}
```

**Merge modes:**
- `rule-based` - Deterministic merging by category
- `claude-enhanced` - AI-assisted merging for better organization

### Config Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Skill name |
| `base_url` | string | Root URL for docs |
| `start_urls` | string[] | Starting pages for crawl |
| `max_pages` | number | Page limit |
| `rate_limit` | number | Seconds between requests |
| `output_dir` | string | Output path |
| `selectors.content` | string | CSS selector for main content |
| `selectors.title` | string | CSS selector for page title |
| `selectors.code` | string | CSS selector for code blocks |
| `exclude_patterns` | string[] | URL patterns to skip |
| `enhance_level` | number | 0-3 enhancement depth |
| `sources` | object[] | Array of sources (unified mode) |
| `merge_mode` | string | How to merge multi-source |

### Syncing Config with Live Site

When docs sites reorganize, use `sync-config` to update start_urls:

```bash
skill-seekers sync-config configs/react.json
```

This diffs your config's `start_urls` against the live site and suggests updates.

---

## Enhancement Workflows

Workflows are YAML files that define multi-stage enhancement pipelines.

### Built-in Presets

| Preset | Focus | Use When |
|--------|-------|----------|
| `default` | Balanced enhancement | General-purpose skills |
| `minimal` | Fast, light touch | Quick iterations |
| `security-focus` | Security vulnerability analysis | Security-sensitive code |
| `architecture-comprehensive` | Deep architectural insights | Complex codebases |
| `api-documentation` | API-focused docs | API reference skills |

### Using Workflows

```bash
# Single workflow
skill-seekers create URL --enhance-workflow default

# Chain workflows (run in order)
skill-seekers create URL --enhance-workflow security-focus --enhance-workflow minimal

# Inline stage (no YAML needed)
skill-seekers create URL --enhance-stage 'perf:Analyze for performance bottlenecks'

# Preview without executing
skill-seekers create URL --enhance-workflow default --workflow-dry-run
```

### Custom Workflow Format

Create custom workflows as YAML files:

```yaml
name: my-custom-workflow
description: Custom enhancement for my use case
variables:
  focus_area: "performance"
  detail_level: "detailed"

stages:
  - name: analyze
    prompt: |
      Analyze the skill content focusing on {{focus_area}}.
      Provide {{detail_level}} analysis of:
      - Key patterns and best practices
      - Common pitfalls
      - Performance considerations

  - name: enhance
    prompt: |
      Based on the analysis, enhance the SKILL.md with:
      - Practical code examples
      - Quick reference tables
      - Clear navigation guidance

  - name: cleanup
    prompt: |
      Review and clean up:
      - Remove redundant sections
      - Fix formatting issues
      - Ensure consistent style
```

### Managing Custom Workflows

```bash
# Copy a built-in preset to customize
skill-seekers workflows copy default
# Edit at ~/.config/skill-seekers/workflows/default.yaml

# Install your own YAML
skill-seekers workflows add ~/my-workflow.yaml

# Override variables at runtime
skill-seekers create URL --enhance-workflow my-workflow --var focus_area=security --var detail_level=basic

# Validate before using
skill-seekers workflows validate my-workflow

# Remove custom workflow
skill-seekers workflows remove my-workflow
```

Custom workflows live in `~/.config/skill-seekers/workflows/`.
