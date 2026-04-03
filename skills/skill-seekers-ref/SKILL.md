---
name: skill-seekers-ref
description: Convert documentation, GitHub repos, PDFs, codebases, videos, and more into structured AI skills using the skill-seekers CLI. Use this skill whenever the user wants to create an AI skill from any knowledge source, scrape docs into a skill, analyze a codebase for patterns, enhance skill quality with AI, package skills for Claude/Gemini/OpenAI/Cursor/RAG platforms, or work with the skill-seekers tool in any capacity. Triggers on "skill-seekers", "create a skill from docs", "scrape documentation", "convert repo to skill", "extract knowledge from PDF", "codebase analysis", "enhance SKILL.md", "package skill for Claude", "AI skill creation", "skill from YouTube video", "RAG skill pipeline".
metadata:
  version: "0.1.0"
---

# Skill Seekers

Skill Seekers converts documentation, GitHub repos, PDFs, codebases, videos, and 10+ other source types into structured AI skills. One command takes a source and produces a platform-ready skill package.

Install: `pip install skill-seekers`

## Core Concept

The pipeline is: **Source -> Extract -> Analyze -> Organize -> (Enhance) -> Package**

The `create` command handles the full pipeline automatically by detecting source type from the input:

```bash
# URL -> docs scraping
skill-seekers create https://react.dev --target claude

# owner/repo -> GitHub scraping
skill-seekers create facebook/react --target claude

# ./path -> local codebase analysis
skill-seekers create ./my-project --target claude

# file.pdf -> PDF extraction
skill-seekers create ./manual.pdf --target claude
```

## Quick Start

```bash
# Create a skill from docs (simplest case)
skill-seekers create https://tailwindcss.com/docs --target claude --max-pages 50

# With AI enhancement (much higher quality)
skill-seekers create https://tailwindcss.com/docs --target claude --max-pages 50 --enhance-workflow default

# Upload to Claude
skill-seekers upload output/tailwindcss-claude.zip --target claude

# Or install directly to an agent's directory
skill-seekers install-agent output/tailwindcss/ --agent claude
```

## Presets for Speed Control

The `-p` flag controls analysis depth:

| Preset | Time | When to Use |
|--------|------|-------------|
| `-p quick` | 1-2 min | Prototyping, testing the pipeline |
| `-p standard` | 5-10 min | Default, good balance |
| `-p comprehensive` | 20-60 min | Production skills, deep analysis |

```bash
skill-seekers create https://docs.astral.sh/ruff --target claude -p quick
```

## Source Types

### Documentation Websites

```bash
skill-seekers create https://react.dev --target claude --max-pages 100

# With parallel workers for speed
skill-seekers scrape --url https://react.dev --workers 5 --async

# Resume interrupted scrape
skill-seekers resume --list
skill-seekers resume <job-id>
```

The scraper checks for `llms.txt` first (10x faster when available), then falls back to BFS page crawling.

### GitHub Repositories

```bash
skill-seekers create microsoft/TypeScript --target claude

# With local clone for unlimited analysis (bypasses API limits)
skill-seekers github --repo django/django --local-repo-path ./django-clone

# Skip issues/changelog to speed up
skill-seekers github --repo owner/repo --no-issues --no-changelog
```

Set a GitHub token for private repos and higher rate limits:
```bash
skill-seekers config --github
```

### Local Codebases (C3.x Analysis)

Analyzes code patterns, architecture, tests, and config across 27+ languages:

```bash
skill-seekers analyze --directory ./my-project --preset standard

# Skip specific analysis phases
skill-seekers analyze --directory ./src --skip-patterns --skip-test-examples
```

C3.x detects: design patterns (Singleton, Factory, Observer...), test examples, config patterns (9 formats), architecture (MVC, MVVM...), and generates how-to guides.

### PDFs

```bash
skill-seekers create ./handbook.pdf --target claude
skill-seekers pdf --pdf ./manual.pdf --name "product-manual"
```

Supports OCR for scanned documents.

### Other Sources

Each has a dedicated subcommand with specific options:

| Source | Command | Key Flags |
|--------|---------|-----------|
| Word docs | `skill-seekers word --docx file.docx` | |
| EPUB books | `skill-seekers epub --epub file.epub` | |
| Videos/YouTube | `skill-seekers video --url URL` | `--visual`, `--whisper-model` |
| Jupyter notebooks | `skill-seekers jupyter --notebook file.ipynb` | |
| OpenAPI specs | `skill-seekers openapi --spec spec.yaml` | `--spec-url URL` |
| PowerPoint | `skill-seekers pptx` | |
| HTML files | `skill-seekers html` | |
| RSS feeds | `skill-seekers rss` | |
| Man pages | `skill-seekers manpage` | |
| Confluence | `skill-seekers confluence` | |
| Notion | `skill-seekers notion` | |
| Slack/Discord | `skill-seekers chat --platform slack` | `--channel`, `--max-messages` |
| AsciiDoc | `skill-seekers asciidoc` | |

### Multi-Source (Unified)

Combine docs + GitHub + PDF into one skill using a config file:

```bash
skill-seekers unified --config configs/my-project.json
```

Config file format - see `references/config-and-workflows.md`.

## AI Enhancement

Enhancement transforms raw extraction (quality ~3/10) into polished skills (~9/10). It uses AI to extract best practices, create quick references, and improve organization.

### Local Enhancement (Free with Claude Code)

```bash
skill-seekers enhance output/my-skill/
skill-seekers enhance output/my-skill/ --background   # non-blocking
skill-seekers enhance output/my-skill/ --daemon        # survives terminal close
skill-seekers enhance-status output/my-skill/          # check progress
```

### API Enhancement

```bash
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers enhance output/my-skill/ --target claude

# Or Gemini / OpenAI
export GOOGLE_API_KEY=AIzaSy...
skill-seekers enhance output/my-skill/ --target gemini
```

### Enhancement Workflows (v3.1.0+)

Workflow presets apply specific enhancement strategies:

```bash
# Built-in presets
skill-seekers enhance output/my-skill/ --enhance-workflow default
skill-seekers enhance output/my-skill/ --enhance-workflow security-focus
skill-seekers enhance output/my-skill/ --enhance-workflow api-documentation
skill-seekers enhance output/my-skill/ --enhance-workflow architecture-comprehensive
skill-seekers enhance output/my-skill/ --enhance-workflow minimal

# Chain multiple workflows
skill-seekers create URL --enhance-workflow security-focus --enhance-workflow minimal

# Inline custom stage
skill-seekers create URL --enhance-stage 'perf:Analyze for performance bottlenecks'

# List / manage workflows
skill-seekers workflows list
skill-seekers workflows show security-focus
skill-seekers workflows copy default    # copy to ~/.config/skill-seekers/workflows/ for editing
skill-seekers workflows add ./my-workflow.yaml
skill-seekers workflows validate my-workflow
```

See `references/config-and-workflows.md` for custom workflow YAML format.

## Output Formats and Packaging

Package skills for 16+ platforms:

```bash
# Package for a specific platform
skill-seekers package output/my-skill/ --target claude
skill-seekers package output/my-skill/ --target gemini
skill-seekers package output/my-skill/ --target cursor
skill-seekers package output/my-skill/ --target openai

# Upload directly
skill-seekers upload output/my-skill.zip --target claude

# Install to agent directory
skill-seekers install-agent output/my-skill/ --agent claude
skill-seekers install-agent output/my-skill/ --agent cursor
skill-seekers install-agent output/my-skill/ --agent all
```

**Supported targets:**
- AI platforms: `claude`, `gemini`, `openai`
- Coding assistants: `cursor`, `windsurf`, `cline`, `continue`
- RAG/vector: `langchain`, `llamaindex`, `chroma`, `faiss`, `haystack`, `qdrant`, `weaviate`, `pinecone`
- Generic: `markdown`, `json`, `yaml`

### RAG Chunking

For vector database targets, enable semantic chunking:

```bash
skill-seekers package output/my-skill/ --target chroma --chunk-for-rag --chunk-tokens 512 --chunk-overlap-tokens 50
```

## Complete Workflow (install command)

The `install` command runs the full pipeline: fetch -> scrape -> enhance -> package -> upload:

```bash
skill-seekers install --config configs/react.json
skill-seekers install --config react --no-upload    # skip upload step
skill-seekers install --config react --dry-run      # preview only
```

## Quality Scoring

Check skill quality before shipping:

```bash
skill-seekers quality output/my-skill/
skill-seekers quality output/my-skill/ --report --threshold 7
```

## Utility Commands

```bash
# Estimate page count before scraping
skill-seekers estimate configs/react.json

# Incremental update (no full rescrape)
skill-seekers update output/my-skill/ --check-changes
skill-seekers update output/my-skill/ --force

# Stream large files chunk by chunk
skill-seekers stream large-doc.md --output output/

# Configure tokens and API keys
skill-seekers config --show
skill-seekers config --github
skill-seekers config --api-keys
skill-seekers config --test
```

## Common Patterns

### "I want to create a skill from X docs quickly"

```bash
skill-seekers create https://docs.example.com --target claude -p quick --max-pages 30
```

### "I want a production-quality skill"

```bash
skill-seekers create https://docs.example.com --target claude -p comprehensive --enhance-workflow default
```

### "I want to analyze my local codebase"

```bash
skill-seekers analyze --directory ./my-project --preset comprehensive
skill-seekers enhance output/my-project/
skill-seekers install-agent output/my-project/ --agent claude
```

### "I want skills for multiple platforms"

```bash
skill-seekers create https://docs.example.com -o output/my-skill
skill-seekers package output/my-skill/ --target claude
skill-seekers package output/my-skill/ --target cursor
skill-seekers package output/my-skill/ --target chroma --chunk-for-rag
```

### "I want to keep skills up to date automatically"

Use CI/CD with the `install` command - see `references/automation.md`.

## Reference Files

For detailed information on specific topics:
- `references/cli-commands.md` - Full CLI reference with all flags for every command
- `references/config-and-workflows.md` - Config file schema, unified configs, custom workflow YAML format
- `references/config-examples.md` - Ready-to-use config examples for common frameworks
- `references/automation.md` - CI/CD integration, Docker, batch processing
