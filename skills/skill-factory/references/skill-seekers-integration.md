# Skill_Seekers Integration Guide

How skill-factory integrates with Skill_Seekers for automated skill creation.

## What is Skill_Seekers?

[Skill_Seekers](https://github.com/yusufkaraaslan/Skill_Seekers) is a Python tool (3,562★) that automatically converts:
- Documentation websites → Claude skills
- GitHub repositories → Claude skills
- PDF files → Claude skills

**Key features:**
- AST parsing for code analysis
- OCR for scanned PDFs
- Conflict detection (docs vs actual code)
- MCP integration
- 299 passing tests

## Installation

### One-Command Install

```bash
~/Projects/claude-skills/skill-factory/scripts/install-skill-seekers.sh
```

### Manual Install

```bash
# Clone
git clone https://github.com/yusufkaraaslan/Skill_Seekers ~/Skill_Seekers

# Install dependencies
cd ~/Skill_Seekers
pip install -r requirements.txt

# Optional: MCP integration
./setup_mcp.sh
```

### Verify Installation

```bash
cd ~/Skill_Seekers
python3 -c "import cli.doc_scraper" && echo "✅ Installed correctly"
```

## Usage from skill-factory

skill-factory automatically uses Skill_Seekers when appropriate.

**Automatic detection:**
```
User: "Create React skill from react.dev"
      ↓
skill-factory detects documentation source
      ↓
Automatically runs Skill_Seekers
      ↓
Post-processes output
      ↓
Quality checks
      ↓
Delivers result
```

## Integration Points

### 1. Automatic Installation Check

Before using Skill_Seekers:
```python
def check_skill_seekers():
    seekers_path = os.environ.get('SKILL_SEEKERS_PATH', f'{HOME}/Skill_Seekers')

    if not os.path.exists(seekers_path):
        print("Skill_Seekers not found. Install? (y/n)")
        if input().lower() == 'y':
            install_skill_seekers()
        else:
            return False

    # Verify dependencies
    try:
        subprocess.run(
            ['python3', '-c', 'import cli.doc_scraper'],
            cwd=seekers_path,
            check=True,
            capture_output=True
        )
        return True
    except:
        print("Dependencies missing. Installing...")
        install_dependencies(seekers_path)
        return True
```

### 2. Scraping with Optimal Settings

```python
def scrape_documentation(url: str, skill_name: str):
    seekers_path = get_seekers_path()

    # Optimal settings for Claude skills
    cmd = [
        'python3', 'cli/doc_scraper.py',
        '--url', url,
        '--name', skill_name,
        '--async',  # 2-3x faster
        '--output', f'{seekers_path}/output/{skill_name}'
    ]

    # Run with progress monitoring
    process = subprocess.Popen(
        cmd,
        cwd=seekers_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    for line in process.stdout:
        # Show progress to user
        print(f"   {line.decode().strip()}")

    return f'{seekers_path}/output/{skill_name}'
```

### 3. Post-Processing Output

Skill_Seekers output needs enhancement for Claude compatibility:

```python
def post_process_skill_seekers_output(output_dir):
    skill_path = f'{output_dir}/SKILL.md'

    # Load skill
    skill = load_skill(skill_path)

    # Enhancements
    enhancements = []

    # 1. Check frontmatter
    if not has_proper_frontmatter(skill):
        skill = add_frontmatter(skill)
        enhancements.append("Added proper YAML frontmatter")

    # 2. Check description specificity
    if is_description_generic(skill):
        skill = improve_description(skill)
        enhancements.append("Improved description specificity")

    # 3. Check examples
    example_count = count_code_blocks(skill)
    if example_count < 5:
        # Extract more from scraped data
        skill = extract_more_examples(skill, output_dir)
        enhancements.append(f"Added {count_code_blocks(skill) - example_count} more examples")

    # 4. Apply progressive disclosure if needed
    if count_lines(skill) > 500:
        skill = apply_progressive_disclosure(skill)
        enhancements.append("Applied progressive disclosure")

    # Save enhanced skill
    save_skill(skill_path, skill)

    return skill_path, enhancements
```

### 4. Quality Scoring

```python
def quality_check_seekers_output(skill_path):
    # Score against Anthropic best practices
    score, issues = score_skill(skill_path)

    print(f"📊 Initial quality: {score}/10")

    if score < 8.0:
        print(f"   ⚠️  Issues: {len(issues)}")
        for issue in issues:
            print(f"       - {issue}")

    return score, issues
```

## Supported Documentation Sources

### Documentation Websites

**Common frameworks:**
- React: https://react.dev
- Vue: https://vuejs.org
- Django: https://docs.djangoproject.com
- FastAPI: https://fastapi.tiangolo.com
- Rust docs: https://docs.rs/[crate]

**Usage:**
```python
scrape_documentation('https://react.dev', 'react-development')
```

### GitHub Repositories

**Example:**
```python
scrape_github_repo('facebook/react', 'react-internals')
```

Features:
- AST parsing for actual API
- Conflict detection vs docs
- README extraction
- Issues/PR analysis
- CHANGELOG parsing

### PDF Files

**Example:**
```python
scrape_pdf('/path/to/manual.pdf', 'api-manual')
```

Features:
- Text extraction
- OCR for scanned pages
- Table extraction
- Code block detection
- Image extraction

## Configuration

### Environment Variables

```bash
# Skill_Seekers location
export SKILL_SEEKERS_PATH="$HOME/Skill_Seekers"

# Cache behavior
export SKILL_SEEKERS_NO_CACHE="true"  # For "latest" requests

# Output location
export SKILL_SEEKERS_OUTPUT="$HOME/.claude/skills"
```

### Custom Presets

Skill_Seekers has presets for common frameworks:
```python
presets = {
    'react': {
        'url': 'https://react.dev',
        'selectors': {'main_content': 'article'},
        'categories': ['components', 'hooks', 'api']
    },
    'rust': {
        'url_pattern': 'https://docs.rs/{crate}',
        'type': 'rust_docs'
    }
    # ... more presets
}
```

## Performance

Typical scraping times:

| Documentation Size | Sync Mode | Async Mode |
|-------------------|-----------|------------|
| Small (100-500 pages) | 15-30 min | 5-10 min |
| Medium (500-2K pages) | 30-60 min | 10-20 min |
| Large (10K+ pages) | 60-120 min | 20-40 min |

**Always use `--async` flag** (2-3x faster)

## Troubleshooting

### Skill_Seekers Not Found

```bash
# Check installation
ls ~/Skill_Seekers

# If missing, install
scripts/install-skill-seekers.sh
```

### Dependencies Missing

```bash
cd ~/Skill_Seekers
pip install -r requirements.txt
```

### Python Version Error

Skill_Seekers requires Python 3.10+:
```bash
python3 --version  # Should be 3.10 or higher
```

### Scraping Fails

Check selectors in configuration:
```python
# If default selectors don't work
python3 cli/doc_scraper.py \
    --url https://example.com \
    --name example \
    --selector "main" \  # Custom selector
    --async
```

## Advanced Features

### Conflict Detection

When combining docs + GitHub:
```python
scrape_multi_source({
    'docs': 'https://react.dev',
    'github': 'facebook/react'
}, 'react-complete')

# Outputs:
# - Documented APIs
# - Actual code APIs
# - ⚠️  Conflicts highlighted
# - Side-by-side comparison
```

### MCP Integration

If Skill_Seekers MCP is installed:
```
User (in Claude Code): "Generate React skill from react.dev"

Claude automatically uses Skill_Seekers MCP server
```

## Quality Enhancement Loop

After Skill_Seekers scraping:

```python
1. Scrape with Skill_Seekers → Initial skill
2. Quality check → Score: 7.4/10
3. Apply enhancements → Fix issues
4. Re-check → Score: 8.2/10 ✅
5. Test with scenarios
6. Deliver
```

## When NOT to Use Skill_Seekers

Don't use for:
- Custom workflows (no docs to scrape)
- Company-specific processes
- Novel methodologies
- Skills requiring original thinking

Use manual TDD approach instead (Path B).

## Source

Integration built on [Skill_Seekers v2.0.0](https://github.com/yusufkaraaslan/Skill_Seekers)
- MIT License
- 3,562 stars
- Active maintenance
- 299 passing tests

## Quick Reference

```bash
# Check installation
scripts/check-skill-seekers.sh

# Install
scripts/install-skill-seekers.sh

# Scrape documentation
scripts/run-automated.sh <url> <skill-name>

# Scrape GitHub
scripts/run-github-scrape.sh <org/repo> <skill-name>

# Scrape PDF
scripts/run-pdf-scrape.sh <pdf-path> <skill-name>
```
