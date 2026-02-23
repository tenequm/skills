# Request Analysis Logic

How skill-factory automatically determines the best creation method.

## Detection Patterns

### Pattern 1: Documentation-Based (Path A)

**Triggers:**
- URL mentioned (https://..., http://...)
- "from [site] docs" ("from react.dev", "from docs.rs")
- "latest documentation", "current docs"
- "based on [framework] documentation"
- Documentation site names (MDN, docs.rs, react.dev, etc.)
- Version keywords ("latest", "current", "v2", "newest")

**Examples:**
```
"Create a React skill from react.dev" → Path A
"Create Anchor skill with latest docs" → Path A
"Skill for FastAPI based on current documentation" → Path A
```

### Pattern 2: GitHub Repository (Path A)

**Triggers:**
- GitHub URL (github.com/...)
- "from [org]/[repo]" format
- "based on [repo] repository"
- "analyze [repo] and create skill"

**Examples:**
```
"Create skill from facebook/react repository" → Path A
"Skill based on coral-xyz/anchor repo" → Path A
```

### Pattern 3: PDF/Manual (Path A)

**Triggers:**
- .pdf extension mentioned
- "PDF", "manual", "handbook"
- File path with .pdf

**Examples:**
```
"Create skill from API-manual.pdf" → Path A
"Extract skill from technical handbook PDF" → Path A
```

### Pattern 4: Custom Workflow (Path B)

**Triggers:**
- No documentation source mentioned
- Workflow/process descriptions
- "for [doing X]" without source reference
- Best practices/methodology descriptions
- Company-specific processes

**Examples:**
```
"Create skill for debugging Solana transactions" → Path B
"Skill for code review workflows" → Path B
"Create skill for technical writing standards" → Path B
```

### Pattern 5: Hybrid (Path C)

**Triggers:**
- Documentation source + custom requirements
- "docs" AND "plus custom workflows"
- "based on docs but add [X]"
- Multiple sources mentioned

**Examples:**
```
"Anchor skill from docs plus debugging workflows" → Path C
"React docs with company coding standards" → Path C
```

## Requirement Extraction

### Quality Keywords

**"Best practices":**
- Enable strict quality checking
- Minimum score: 8.5 (higher than default 8.0)
- Include anti-patterns section

**"Latest", "Current", "Newest":**
- Scrape fresh documentation (no cache)
- Check for version mentions
- Prefer official sources

**"Comprehensive", "Complete", "Detailed":**
- Extended coverage requirement
- More test scenarios
- Reference files for progressive disclosure

**"Examples", "Code samples", "Patterns":**
- Ensure code examples included
- Extract from documentation
- Generate if needed

## Decision Algorithm

```python
def analyze_request(request: str) -> Path:
    # Normalize
    request_lower = request.lower()

    # Check for documentation sources
    has_url = contains_url(request)
    has_docs_keyword = any(kw in request_lower
                          for kw in ["docs", "documentation", "manual"])
    has_version_keyword = any(kw in request_lower
                             for kw in ["latest", "current", "newest"])

    # Check for custom workflow indicators
    has_workflow_keyword = any(kw in request_lower
                              for kw in ["workflow", "process", "debugging",
                                        "methodology", "standards"])
    no_source = not (has_url or has_docs_keyword)

    # Decision logic
    if (has_url or has_docs_keyword or has_version_keyword) and has_workflow_keyword:
        return Path.HYBRID
    elif has_url or has_docs_keyword or has_version_keyword:
        return Path.AUTOMATED
    elif no_source and has_workflow_keyword:
        return Path.MANUAL_TDD
    else:
        # Default: ask for clarification
        return Path.CLARIFY

def extract_requirements(request: str) -> Requirements:
    requirements = Requirements()
    request_lower = request.lower()

    # Quality level
    if "best practices" in request_lower:
        requirements.min_quality_score = 8.5
        requirements.include_antipatterns = True
    else:
        requirements.min_quality_score = 8.0

    # Coverage
    if any(kw in request_lower for kw in ["comprehensive", "complete", "detailed"]):
        requirements.coverage_level = "extensive"
        requirements.use_progressive_disclosure = True
    else:
        requirements.coverage_level = "standard"

    # Examples
    if any(kw in request_lower for kw in ["examples", "code samples", "patterns"]):
        requirements.examples_required = True
        requirements.min_examples = 10

    # Version freshness
    if any(kw in request_lower for kw in ["latest", "current", "newest"]):
        requirements.use_cache = False
        requirements.check_version = True

    return requirements
```

## Confidence Scoring

Each path gets a confidence score:

```python
def score_path_confidence(request: str) -> Dict[Path, float]:
    scores = {
        Path.AUTOMATED: 0.0,
        Path.MANUAL_TDD: 0.0,
        Path.HYBRID: 0.0
    }

    # Automated indicators
    if contains_url(request):
        scores[Path.AUTOMATED] += 0.8
    if "docs" in request.lower() or "documentation" in request.lower():
        scores[Path.AUTOMATED] += 0.6
    if "github.com" in request:
        scores[Path.AUTOMATED] += 0.7
    if ".pdf" in request:
        scores[Path.AUTOMATED] += 0.7

    # Manual TDD indicators
    if "workflow" in request.lower():
        scores[Path.MANUAL_TDD] += 0.5
    if "process" in request.lower():
        scores[Path.MANUAL_TDD] += 0.5
    if "custom" in request.lower():
        scores[Path.MANUAL_TDD] += 0.4
    if not (contains_url(request) or "docs" in request.lower()):
        scores[Path.MANUAL_TDD] += 0.6

    # Hybrid indicators
    if scores[Path.AUTOMATED] > 0.5 and scores[Path.MANUAL_TDD] > 0.4:
        scores[Path.HYBRID] = (scores[Path.AUTOMATED] + scores[Path.MANUAL_TDD]) / 1.5

    return scores

def select_path(scores: Dict[Path, float]) -> Path:
    # Select highest confidence
    max_score = max(scores.values())

    # Require minimum confidence
    if max_score < 0.5:
        return Path.CLARIFY  # Ask user for more info

    # Return highest scoring path
    return max(scores, key=scores.get)
```

## Clarification Questions

If confidence < 0.5, ask for clarification:

```
Low confidence - need clarification:

Do you have a documentation source?
  □ Yes, documentation website: ____________
  □ Yes, GitHub repository: ____________
  □ Yes, PDF file at: ____________
  □ No, this is a custom workflow/process

If custom workflow, briefly describe:
____________________________________________
```

## Source Extraction

```python
def extract_source(request: str) -> Optional[str]:
    # URL pattern
    url_match = re.search(r'https?://[^\s]+', request)
    if url_match:
        return url_match.group(0)

    # GitHub repo pattern (org/repo)
    github_match = re.search(r'github\.com/([^/\s]+/[^/\s]+)', request)
    if github_match:
        return f"https://github.com/{github_match.group(1)}"

    # Documentation site mentions
    doc_sites = {
        "react.dev": "https://react.dev",
        "docs.rs": "https://docs.rs",
        "python.org": "https://docs.python.org",
        # ... more mappings
    }

    for site, url in doc_sites.items():
        if site in request.lower():
            # Try to extract specific package/framework
            return resolve_doc_url(site, request)

    # PDF path
    pdf_match = re.search(r'[\w/.-]+\.pdf', request)
    if pdf_match:
        return pdf_match.group(0)

    return None
```

## Examples with Analysis

### Example 1
```
Request: "Create a skill for Anchor development with latest docs and best practices"

Analysis:
- Source: "Anchor" + "latest docs" → docs.rs/anchor-lang
- Requirements:
  - latest → use_cache=False
  - best practices → min_quality=8.5, include_antipatterns=True
- Path: AUTOMATED
- Confidence: 0.85

Execution: Path A (automated scraping)
```

### Example 2
```
Request: "Create a skill for debugging Solana transaction failures"

Analysis:
- Source: None detected
- Requirements:
  - debugging workflow (custom)
- Path: MANUAL_TDD
- Confidence: 0.75

Execution: Path B (manual TDD)
```

### Example 3
```
Request: "React skill from react.dev plus our company's JSX patterns"

Analysis:
- Source: "react.dev" → https://react.dev
- Requirements:
  - documentation source present
  - custom patterns ("our company's")
- Path: HYBRID
- Confidence: 0.80

Execution: Path C (scrape react.dev, then add custom patterns)
```

### Example 4
```
Request: "Create a skill"

Analysis:
- Source: None
- Requirements: None specific
- Path: CLARIFY
- Confidence: 0.1

Action: Ask clarification questions
```
