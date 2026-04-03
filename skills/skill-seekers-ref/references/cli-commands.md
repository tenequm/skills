# CLI Commands Reference

Full reference for all skill-seekers commands. Run `skill-seekers <command> --help` for the most up-to-date flags.

## Table of Contents

- [create](#create) - Universal entry point (auto-detects source)
- [scrape](#scrape) - Scrape documentation websites
- [github](#github) - Scrape GitHub repositories
- [analyze](#analyze) - Analyze local codebases
- [pdf](#pdf) - Extract from PDFs
- [video](#video) - Extract from videos/YouTube
- [word / epub / jupyter / html / openapi / asciidoc / pptx / rss / manpage / confluence / notion / chat](#other-extractors) - Specialized extractors
- [unified](#unified) - Multi-source scraping
- [enhance](#enhance) - AI-powered skill enhancement
- [enhance-status](#enhance-status) - Monitor enhancement progress
- [package](#package) - Package for target platform
- [upload](#upload) - Upload to platform
- [install](#install) - Full pipeline (fetch -> enhance -> package -> upload)
- [install-agent](#install-agent) - Copy skill to agent directories
- [quality](#quality) - Score skill documentation quality
- [workflows](#workflows) - Manage enhancement workflow presets
- [config](#config) - Configure tokens and API keys
- [estimate](#estimate) - Estimate page count before scraping
- [resume](#resume) - Resume interrupted scraping
- [stream](#stream) - Stream large files chunk by chunk
- [update](#update) - Incremental doc updates

---

## create

Universal command that auto-detects source type from input.

```bash
skill-seekers create <source> [options]
```

**Source detection:**
- `https://...` -> web docs scraping
- `owner/repo` -> GitHub scraping
- `./path` or `/path` -> local codebase analysis
- `file.pdf` -> PDF extraction
- `file.json` -> config file (multi-source)

**Common flags:**

| Flag | Description |
|------|-------------|
| `--name NAME` | Skill name (default: auto-detected) |
| `-d TEXT` | Skill description |
| `-o DIR` | Output directory |
| `-p PRESET` | `quick` (1-2 min), `standard` (5-10 min), `comprehensive` (20-60 min) |
| `--target PLATFORM` | Target platform for packaging |
| `--enhance-level LEVEL` | 0=disabled, 1=SKILL.md only, 2=+arch/config (default), 3=full |
| `--enhance-workflow NAME` | Apply workflow preset (can use multiple times) |
| `--enhance-stage 'name:prompt'` | Inline custom enhancement stage |
| `--var 'key=value'` | Override workflow variable |
| `--dry-run` | Preview without executing |
| `-v` | Verbose output |
| `-q` | Quiet mode |
| `-c FILE` | Load settings from JSON config |
| `--chunk-for-rag` | Enable semantic chunking for RAG |
| `--chunk-tokens N` | Chunk size (default: 512) |
| `--chunk-overlap-tokens N` | Overlap (default: 50) |

**Progressive help** (shows source-specific flags):
- `--help-web` - Web scraping options
- `--help-github` - GitHub options
- `--help-local` - Local codebase options
- `--help-pdf` - PDF options
- `--help-config` - Multi-source config options
- `--help-advanced` - Rare/advanced options
- `--help-all` - All 120+ flags

---

## scrape

Scrape documentation websites.

```bash
skill-seekers scrape <url> [options]
skill-seekers scrape --config configs/react.json
```

**Key flags:**

| Flag | Description |
|------|-------------|
| `--url URL` | Base documentation URL |
| `--config FILE` | Load from JSON config |
| `-i` | Interactive configuration mode |
| `--max-pages N` | Max pages to scrape |
| `--workers N` | Parallel workers (1-10, default: 1) |
| `--async` | Async mode (2-3x faster than threads) |
| `-r SECONDS` | Rate limit between requests (default: 0.5) |
| `--no-rate-limit` | Disable rate limiting |
| `--resume` | Resume from last checkpoint |
| `--fresh` | Clear checkpoint and start fresh |
| `--skip-scrape` | Skip scraping, use existing data |

---

## github

Scrape GitHub repositories.

```bash
skill-seekers github --repo facebook/react [options]
```

**Key flags:**

| Flag | Description |
|------|-------------|
| `--repo OWNER/REPO` | GitHub repository |
| `--token TOKEN` | GitHub personal access token |
| `--local-repo-path PATH` | Local clone for unlimited C3.x analysis |
| `--no-issues` | Skip GitHub issues |
| `--no-changelog` | Skip CHANGELOG |
| `--no-releases` | Skip releases |
| `--max-issues N` | Max issues to fetch (default: 100) |
| `--scrape-only` | Only scrape, don't build skill |
| `--non-interactive` | Non-interactive for CI/CD |
| `--profile NAME` | GitHub profile from config |

---

## analyze

Analyze local codebases with C3.x engine.

```bash
skill-seekers analyze --directory ./my-project [options]
```

**Key flags:**

| Flag | Description |
|------|-------------|
| `--directory DIR` | Directory to analyze (required) |
| `--preset PRESET` | `quick`, `standard` (default), `comprehensive` |
| `--languages LANGS` | Comma-separated (e.g., `Python,JavaScript`) |
| `--file-patterns PATTERNS` | Comma-separated file patterns |
| `--skip-api-reference` | Skip API docs generation |
| `--skip-dependency-graph` | Skip dependency graph |
| `--skip-patterns` | Skip pattern detection |
| `--skip-test-examples` | Skip test example extraction |
| `--skip-how-to-guides` | Skip how-to guides |
| `--skip-config-patterns` | Skip config pattern extraction |
| `--skip-docs` | Skip README/docs |
| `--no-comments` | Skip comment extraction |

---

## pdf

Extract from PDF files.

```bash
skill-seekers pdf --pdf ./manual.pdf [options]
```

| Flag | Description |
|------|-------------|
| `--pdf PATH` | PDF file path |
| `--config FILE` | PDF config JSON |
| `--from-json FILE` | Build from extracted JSON |

OCR is supported for scanned documents.

---

## video

Extract from videos and YouTube.

```bash
skill-seekers video --url https://youtube.com/watch?v=... [options]
```

| Flag | Description |
|------|-------------|
| `--url URL` | Video URL (YouTube, Vimeo) |
| `--video-file PATH` | Local video file |
| `--playlist URL` | Playlist URL |
| `--languages LANGS` | Transcript languages (default: en) |
| `--visual` | Enable visual/frame extraction |
| `--whisper-model MODEL` | Whisper model size (default: base) |
| `--visual-interval SECS` | Frame scan interval (default: 0.7) |
| `--visual-similarity THRESH` | Duplicate frame threshold (default: 3.0) |
| `--vision-ocr` | Use Claude Vision for low-confidence frames |
| `--start-time TIME` | Start time (seconds, MM:SS, HH:MM:SS) |
| `--end-time TIME` | End time |
| `--setup` | Auto-detect GPU and install visual deps |

---

## Other Extractors

All share common flags (`--name`, `-d`, `-o`, `--enhance-level`, `--enhance-workflow`, etc.).

| Command | Source | Key Flag |
|---------|--------|----------|
| `word` | Word .docx | `--docx PATH` |
| `epub` | EPUB e-books | `--epub PATH` |
| `jupyter` | Jupyter notebooks | `--notebook PATH` |
| `html` | Local HTML files | (positional path) |
| `openapi` | OpenAPI/Swagger | `--spec PATH` or `--spec-url URL` |
| `asciidoc` | AsciiDoc .adoc | (positional path) |
| `pptx` | PowerPoint | (positional path) |
| `rss` | RSS/Atom feeds | (feed URL) |
| `manpage` | Man pages | (page name) |
| `confluence` | Confluence wiki | (space/page config) |
| `notion` | Notion pages | (page ID/URL) |
| `chat` | Slack/Discord exports | `--export-path`, `--platform`, `--channel`, `--max-messages` |

---

## unified

Combine multiple sources into one skill via config file.

```bash
skill-seekers unified --config configs/my-project.json [options]
```

| Flag | Description |
|------|-------------|
| `--config FILE` | Unified config JSON (required) |
| `--merge-mode MODE` | `rule-based` or `claude-enhanced` |
| `--fresh` | Clear existing data |

---

## enhance

AI-powered skill quality improvement.

```bash
skill-seekers enhance <skill_directory> [options]
```

| Flag | Description |
|------|-------------|
| `--target PLATFORM` | `claude`, `gemini`, `openai` (auto-detected from env) |
| `--api-key KEY` | API key (or use env vars) |
| `--background` | Run in background (non-blocking) |
| `--daemon` | Detached process (survives terminal close) |
| `--interactive-enhancement` | Opens terminal window |
| `--no-force` | Enable confirmations (force is ON by default) |
| `--timeout SECONDS` | Timeout (default: 600) |
| `--agent AGENT` | Local agent to use (default: claude) |
| `--agent-cmd CMD` | Override agent command template |

**Enhancement modes:**

| Mode | Blocks? | Survives Exit? | Best For |
|------|---------|----------------|----------|
| Headless (default) | Yes | No | CI/CD |
| `--background` | No | No | Scripts |
| `--daemon` | No | Yes | Long tasks |
| `--interactive-enhancement` | No | Yes | Manual |

---

## enhance-status

Monitor background/daemon enhancement.

```bash
skill-seekers enhance-status <skill_directory>
skill-seekers enhance-status <skill_directory> --watch
skill-seekers enhance-status <skill_directory> --watch --interval 5
skill-seekers enhance-status <skill_directory> --json
```

---

## package

Package skill for a target platform.

```bash
skill-seekers package <skill_directory> [options]
```

| Flag | Description |
|------|-------------|
| `--target PLATFORM` | Target platform (default: claude) |
| `--no-open` | Don't open output folder |
| `--skip-quality-check` | Skip quality checks |
| `--upload` | Auto-upload after packaging |
| `--streaming` | Memory-efficient mode for large docs |
| `--chunk-for-rag` | Enable RAG chunking |
| `--chunk-tokens N` | Chunk size (default: 512) |
| `--chunk-overlap-tokens N` | Overlap (default: 50) |

---

## upload

Upload packaged skill to a platform.

```bash
skill-seekers upload <package_file> [options]
```

| Flag | Description |
|------|-------------|
| `--target PLATFORM` | Target: claude, gemini, openai, chroma, weaviate |
| `--api-key KEY` | Platform API key |
| `--chroma-url URL` | ChromaDB URL |
| `--persist-directory DIR` | Local ChromaDB storage dir |
| `--weaviate-url URL` | Weaviate URL |
| `--use-cloud` | Use Weaviate Cloud |
| `--cluster-url URL` | Weaviate cluster URL |

---

## install

Full pipeline: fetch -> scrape -> enhance -> package -> upload.

```bash
skill-seekers install --config <name-or-path> [options]
```

| Flag | Description |
|------|-------------|
| `--config CONFIG` | Config name (e.g., `react`) or path |
| `--destination DIR` | Output dir (default: output/) |
| `--no-upload` | Skip upload |
| `--unlimited` | Remove page limits |
| `--dry-run` | Preview |

---

## install-agent

Copy skill to agent-specific directories.

```bash
skill-seekers install-agent <skill_directory> --agent <agent>
```

| Flag | Description |
|------|-------------|
| `--agent AGENT` | `claude`, `cursor`, `vscode`, `amp`, `goose`, `opencode`, `all` |
| `--force` | Overwrite without asking |
| `--dry-run` | Preview |

---

## quality

Score skill documentation quality (0-10 scale).

```bash
skill-seekers quality <skill_directory> [--report] [--threshold N]
```

---

## workflows

Manage enhancement workflow presets.

```bash
skill-seekers workflows list                    # List all workflows
skill-seekers workflows show <name>             # Print YAML content
skill-seekers workflows copy <name>             # Copy to user dir for editing
skill-seekers workflows add <file.yaml>         # Install custom workflow
skill-seekers workflows remove <name>           # Delete from user dir
skill-seekers workflows validate <name-or-file> # Validate workflow
```

User workflows live in `~/.config/skill-seekers/workflows/`.

---

## config

Configure tokens and API keys interactively.

```bash
skill-seekers config --show      # Show current config
skill-seekers config --github    # Set up GitHub token
skill-seekers config --api-keys  # Set up API keys
skill-seekers config --test      # Test connections
```

---

## estimate

Estimate page count before committing to a full scrape.

```bash
skill-seekers estimate configs/react.json
skill-seekers estimate --all                    # List all available configs
skill-seekers estimate --max-discovery 200
```

---

## resume

Resume interrupted scraping jobs.

```bash
skill-seekers resume --list    # List resumable jobs
skill-seekers resume <job-id>  # Resume specific job
skill-seekers resume --clean   # Clean up old progress files
```

---

## stream

Stream large files chunk by chunk for memory-efficient processing.

```bash
skill-seekers stream <input_file> --output <dir> --streaming-chunk-chars 4000
```

---

## update

Incrementally update skills without full rescrape.

```bash
skill-seekers update <skill_directory> --check-changes  # Check only
skill-seekers update <skill_directory> --force           # Force update all
```

---

## Global Flags

These flags work on most commands:

| Flag | Description |
|------|-------------|
| `--name NAME` | Skill name |
| `-d TEXT` | Description |
| `-o DIR` | Output directory |
| `--enhance-level 0-3` | Enhancement depth |
| `--api-key KEY` | API key |
| `--doc-version VERSION` | Version tag for metadata |
| `--dry-run` | Preview mode |
| `-v` | Verbose (DEBUG logging) |
| `-q` | Quiet (WARNING only) |
| `--enhance-workflow NAME` | Workflow preset (repeatable) |
| `--enhance-stage 'name:prompt'` | Inline stage (repeatable) |
| `--var 'key=value'` | Workflow variable override (repeatable) |
| `--workflow-dry-run` | Preview workflow stages |
| `--workflow-history FILE` | Save workflow execution log |
