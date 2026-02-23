# Migration Guide: Moving to UV and Ruff

Complete guide for migrating from pip, conda, poetry, or pipx to UV, and from Flake8, Black, isort to Ruff.

## Table of Contents

1. [Why Migrate?](#why-migrate)
2. [From pip + virtualenv](#from-pip--virtualenv)
3. [From conda](#from-conda)
4. [From poetry](#from-poetry)
5. [From pipx](#from-pipx)
6. [From Flake8/Black/isort to Ruff](#from-flake8blackisort-to-ruff)
7. [Complete Workflow Migration](#complete-workflow-migration)

## Why Migrate?

### UV Benefits

- **10-100x faster** than pip for package installation
- **Single tool** replacing pip, pip-tools, pipx, poetry, pyenv, virtualenv
- **Automatic environment management** - no manual activation needed
- **Universal lockfiles** for cross-platform reproducibility
- **Python version management** built-in
- **Zero dependencies** - standalone binary

### Ruff Benefits

- **10-100x faster** than existing linters
- **Single tool** replacing Flake8, Black, isort, pyupgrade, autoflake
- **800+ lint rules** with auto-fix capabilities
- **Formatting** compatible with Black
- **Editor integration** with first-class support
- **Zero configuration** needed to get started

## From pip + virtualenv

### Current Workflow

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt

# Run application
python main.py
```

### New Workflow with UV

```bash
# Initialize project (one-time)
uv init my-project
cd my-project

# Add dependencies
uv add requests pandas numpy

# Add dev dependencies
uv add --dev pytest black ruff

# Run application (no activation needed!)
uv run python main.py

# Run tests
uv run pytest
```

### Migration Steps

**Step 1: Install UV**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Step 2: Convert requirements.txt to pyproject.toml**

If you have `requirements.txt`:
```bash
# Create new project
uv init .

# Install from requirements.txt
uv pip install -r requirements.txt

# Generate pyproject.toml dependencies
uv add $(cat requirements.txt | grep -v '^#' | grep -v '^$')
```

Or manually create `pyproject.toml`:
```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31.0",
    "pandas>=2.0.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "ruff>=0.1.0",
]
```

**Step 3: Create lockfile**
```bash
uv lock
```

**Step 4: Update CI/CD**

Before:
```yaml
- name: Setup Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.11'

- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
```

After:
```yaml
- name: Install uv
  run: curl -LsSf https://astral.sh/uv/install.sh | sh

- name: Install dependencies
  run: uv sync
```

**Step 5: Update Development Scripts**

Before:
```bash
#!/bin/bash
source .venv/bin/activate
python manage.py runserver
```

After:
```bash
#!/bin/bash
uv run python manage.py runserver
```

### Maintaining requirements.txt (Optional)

If you need to maintain `requirements.txt` for compatibility:
```bash
# Generate requirements.txt from lockfile
uv export -o requirements.txt

# Generate dev requirements
uv export --group dev -o requirements-dev.txt
```

## From conda

### Current Workflow

```bash
# Create environment
conda create -n myenv python=3.11
conda activate myenv

# Install dependencies
conda install numpy pandas scipy
pip install requests  # Some packages not in conda

# Export environment
conda env export > environment.yml
```

### New Workflow with UV

```bash
# Initialize project
uv init my-project
cd my-project

# Pin Python version
uv python pin 3.11

# Add dependencies (all from PyPI)
uv add numpy pandas scipy requests

# All dependencies in one place
uv lock
```

### Migration Steps

**Step 1: Export conda dependencies**
```bash
# Get list of installed packages
conda list --export > conda-packages.txt

# Or just the package names
conda env export --from-history > environment.yml
```

**Step 2: Convert to pyproject.toml**

From `environment.yml`:
```yaml
name: myenv
dependencies:
  - python=3.11
  - numpy=1.24.0
  - pandas=2.0.0
  - pip:
    - requests==2.31.0
```

To `pyproject.toml`:
```toml
[project]
name = "myproject"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "numpy>=1.24.0",
    "pandas>=2.0.0",
    "requests>=2.31.0",
]
```

**Step 3: Handle Conda-Only Packages**

Some packages are only available through conda. Options:
1. **Use PyPI alternatives**: Many packages are now on PyPI
2. **Keep conda for specific packages**: Use conda + uv hybrid
3. **Build from source**: UV can build packages if needed

**Step 4: Remove Conda Environment**
```bash
# Deactivate conda environment
conda deactivate

# Remove environment
conda env remove -n myenv
```

### Conda vs UV Comparison

| Feature | conda | UV |
|---------|-------|-----|
| Speed | Slow (10-30min) | Fast (10-30sec) |
| Python Versions | ✅ | ✅ |
| Non-Python Packages | ✅ | ❌ |
| PyPI Packages | Limited | Full |
| Lockfiles | ✅ | ✅ |
| Cross-platform | ✅ | ✅ |
| Memory Usage | High (1-2GB) | Low (<100MB) |

### When to Keep Conda

Keep conda if you need:
- Non-Python packages (R, Julia, C libraries)
- Specific binary distributions
- Legacy scientific computing workflows

You can use both:
```bash
# Use conda for system-level dependencies
conda install gcc openblas

# Use uv for Python packages
uv sync
```

## From poetry

### Current Workflow

```bash
# Create project
poetry new my-project
cd my-project

# Add dependencies
poetry add requests

# Install dependencies
poetry install

# Run scripts
poetry run python main.py
```

### New Workflow with UV

```bash
# Create project
uv init my-project
cd my-project

# Add dependencies
uv add requests

# Install dependencies (automatic with add)
# No separate install step needed!

# Run scripts
uv run python main.py
```

### Migration Steps

**Step 1: Convert pyproject.toml**

Poetry `pyproject.toml`:
```toml
[tool.poetry]
name = "my-project"
version = "0.1.0"
description = ""
authors = ["Your Name <[email protected]>"]

[tool.poetry.dependencies]
python = "^3.11"
requests = "^2.31.0"

[tool.poetry.dev-dependencies]
pytest = "^7.0.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

UV `pyproject.toml`:
```toml
[project]
name = "my-project"
version = "0.1.0"
description = ""
authors = [{name = "Your Name", email = "[email protected]"}]
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Step 2: Convert Version Constraints**

Poetry uses caret (`^`) for version constraints:
- `^2.31.0` means `>=2.31.0, <3.0.0`

UV uses standard pip syntax:
- `>=2.31.0,<3.0.0` or `>=2.31.0`

**Step 3: Remove Poetry Files**
```bash
rm poetry.lock
rm -rf .venv
poetry env remove --all
```

**Step 4: Initialize UV**
```bash
uv lock
uv sync
```

**Step 5: Update Scripts**

Before:
```toml
[tool.poetry.scripts]
start = "my_project.main:main"
```

After:
```toml
[project.scripts]
start = "my_project.main:main"
```

Or just use `uv run`:
```bash
uv run python -m my_project.main
```

### Poetry vs UV Comparison

| Feature | Poetry | UV |
|---------|--------|-----|
| Speed | Medium | Very Fast |
| Lockfiles | ✅ | ✅ |
| Python Management | ❌ | ✅ |
| Tool Running | ❌ | ✅ (uvx) |
| Build Backend | poetry-core | Any (hatchling, setuptools) |
| Configuration | Opinionated | Flexible |

## From pipx

### Current Workflow

```bash
# Install tools globally
pipx install black
pipx install ruff
pipx install pytest

# Run tools
black .
ruff check .
```

### New Workflow with UV

```bash
# Install tools globally
uv tool install black
uv tool install ruff
uv tool install pytest

# Or run tools ephemerally
uvx black .
uvx ruff check .
uvx pytest
```

### Migration Steps

**Step 1: List pipx installations**
```bash
pipx list
```

**Step 2: Install with UV**
```bash
# For each tool in pipx list
uv tool install tool-name
```

**Step 3: Remove pipx tools**
```bash
pipx uninstall-all
```

**Step 4: Update PATH (if needed)**

Tools are installed in:
- **pipx**: `~/.local/bin/`
- **uv**: `~/.local/bin/` (same location!)

No PATH changes needed!

### pipx vs UV Tool Comparison

| Feature | pipx | UV Tool |
|---------|------|---------|
| Speed | Medium | Fast |
| Ephemeral runs | ❌ | ✅ (uvx) |
| Python Management | ❌ | ✅ |
| Isolated Environments | ✅ | ✅ |
| Upgrade Command | ✅ | ✅ |

## From Flake8/Black/isort to Ruff

### Current Workflow

```bash
# Multiple tools
isort .
black .
flake8 .

# With configuration in multiple files
# .flake8
# pyproject.toml [tool.black]
# pyproject.toml [tool.isort]
```

### New Workflow with Ruff

```bash
# Single command
ruff check --fix . && ruff format .

# All configuration in pyproject.toml
# [tool.ruff]
```

### Migration Steps

**Step 1: Install Ruff**
```bash
uv add --dev ruff
```

**Step 2: Convert Configuration**

From `.flake8`:
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build
per-file-ignores =
    __init__.py:F401
```

From `pyproject.toml`:
```toml
[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
known_first_party = ["myproject"]
```

To unified Ruff config:
```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
ignore = ["E203", "W503"]
exclude = [".git", "__pycache__", "build"]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]

[tool.ruff.lint.isort]
known-first-party = ["myproject"]

[tool.ruff.format]
quote-style = "double"
```

**Step 3: Test Ruff**
```bash
# Check for issues
ruff check .

# Auto-fix
ruff check --fix .

# Format
ruff format .
```

**Step 4: Remove Old Tools**
```bash
uv remove --dev black isort flake8
```

**Step 5: Update Pre-commit**

Before:
```yaml
repos:
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

After:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.12.8
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

**Step 6: Update CI/CD**

Before:
```yaml
- name: Lint
  run: |
    pip install black isort flake8
    isort --check .
    black --check .
    flake8 .
```

After:
```yaml
- name: Lint
  run: |
    uv tool install ruff
    ruff check .
    ruff format --check .
```

## Complete Workflow Migration

### Before: Traditional Setup

**Project Structure:**
```
my-project/
├── .flake8
├── requirements.txt
├── requirements-dev.txt
├── setup.py
└── src/
```

**Development Workflow:**
```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Development
isort .
black .
flake8 .
pytest

# Every day
source .venv/bin/activate  # Easy to forget!
```

### After: Modern Setup with UV + Ruff

**Project Structure:**
```
my-project/
├── pyproject.toml  # All configuration
├── uv.lock         # Reproducible dependencies
└── src/
```

**Development Workflow:**
```bash
# Setup (one-time)
uv sync

# Development (no activation needed!)
uv run ruff check --fix .
uv run ruff format .
uv run pytest

# That's it!
```

### Migration Checklist

- [ ] Install UV
- [ ] Convert requirements to pyproject.toml
- [ ] Generate lockfile (`uv lock`)
- [ ] Install dependencies (`uv sync`)
- [ ] Install Ruff (`uv add --dev ruff`)
- [ ] Convert linter/formatter config
- [ ] Test Ruff (`ruff check . && ruff format .`)
- [ ] Update CI/CD pipelines
- [ ] Update pre-commit hooks
- [ ] Update documentation
- [ ] Remove old tools
- [ ] Update team workflows
- [ ] Celebrate faster builds! 🎉

## Rollback Plan

If you need to rollback:

**Save Old Configuration:**
```bash
# Before migration
cp requirements.txt requirements.txt.backup
cp .flake8 .flake8.backup
# etc.
```

**Keep Old Files:**
Don't delete old files until you're confident in the migration.

**Gradual Migration:**
You can run UV and pip side-by-side:
```bash
# Use both during transition
uv sync              # For new workflow
pip install -r requirements.txt  # For old workflow
```

## Common Issues

### UV Can't Find Python

```bash
# Install Python with UV
uv python install 3.12

# Or point to existing Python
uv python pin $(which python3.12)
```

### Ruff Too Strict

```bash
# Start with minimal rules
ruff check --select F .  # Only Pyflakes

# Gradually add more
ruff check --select E,F .  # Add pycodestyle
```

### Performance Issues

```bash
# Clear caches
uv cache clean
ruff clean

# Exclude large directories
# In pyproject.toml
[tool.ruff]
exclude = ["node_modules", "vendor"]
```

## Success Stories

**Typical Results After Migration:**

- **Installation time**: 5 minutes → 30 seconds (10x faster)
- **Linting time**: 15 seconds → 0.5 seconds (30x faster)
- **CI/CD time**: 10 minutes → 2 minutes (5x faster)
- **Tools to manage**: 7 → 2 (3.5x fewer)
- **Config files**: 4 → 1 (4x simpler)
- **Memory usage**: 2GB → 200MB (10x less)

## Next Steps

After migration:
1. Configure Ruff rules to your needs
2. Set up pre-commit hooks
3. Update team documentation
4. Train team on new workflow
5. Monitor CI/CD improvements
6. Consider adopting more modern Python features

## Resources

- [UV Documentation](https://docs.astral.sh/uv/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [UV Migration FAQ](https://docs.astral.sh/uv/guides/projects/)
- [Ruff Migration Guide](https://docs.astral.sh/ruff/formatter/)
