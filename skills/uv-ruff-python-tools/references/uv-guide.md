# UV: Complete Guide

UV is an extremely fast Python package and project manager, written in Rust. It's 10-100x faster than pip and replaces multiple tools in the Python ecosystem.

## Table of Contents

1. [Installation](#installation)
2. [Project Management](#project-management)
3. [Dependency Management](#dependency-management)
4. [Python Version Management](#python-version-management)
5. [Tool Management](#tool-management)
6. [The pip Interface](#the-pip-interface)
7. [Scripts](#scripts)
8. [Building and Publishing](#building-and-publishing)
9. [Configuration](#configuration)
10. [Caching](#caching)

## Installation

### Standalone Installer (Recommended)

**macOS and Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Alternative Methods

**With Homebrew:**
```bash
brew install uv
```

**With pip:**
```bash
pip install uv
```

**With pipx:**
```bash
pipx install uv
```

**With conda:**
```bash
conda install -c conda-forge uv
```

### Upgrading UV

**If installed with standalone installer:**
```bash
uv self update
```

**If installed with pipx:**
```bash
pipx upgrade uv
```

### Shell Autocompletion

**Bash:**
```bash
echo 'eval "$(uv generate-shell-completion bash)"' >> ~/.bashrc
```

**Zsh:**
```bash
echo 'eval "$(uv generate-shell-completion zsh)"' >> ~/.zshrc
```

**Fish:**
```bash
echo 'uv generate-shell-completion fish | source' > ~/.config/fish/completions/uv.fish
```

**PowerShell:**
```powershell
Add-Content -Path $PROFILE -Value '(& uv generate-shell-completion powershell) | Out-String | Invoke-Expression'
```

## Project Management

### Creating a New Project

```bash
# Initialize a new project
uv init my-project
cd my-project

# Project structure created:
# my-project/
# ├── .gitignore
# ├── .python-version
# ├── README.md
# ├── hello.py
# └── pyproject.toml
```

### Project Structure

UV creates a standardized project structure:

**pyproject.toml:**
```toml
[project]
name = "my-project"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.11"
dependencies = []
```

### Running Project Code

```bash
# Run a Python file in the project environment
uv run python hello.py

# Run a specific command
uv run pytest

# Run with specific Python version
uv run --python 3.12 python hello.py
```

### Project Commands

```bash
# Initialize existing directory as project
uv init .

# Sync environment with dependencies
uv sync

# Lock dependencies
uv lock

# Clean up project
uv cache clean
```

## Dependency Management

### Adding Dependencies

```bash
# Add a production dependency
uv add requests

# Add multiple dependencies
uv add requests pandas numpy

# Add with version constraint
uv add "requests>=2.31.0"
uv add "pandas<3.0.0"

# Add from git repository
uv add git+https://github.com/user/repo.git

# Add from local path
uv add ../path/to/package
```

### Development Dependencies

```bash
# Add development dependencies
uv add --dev pytest black ruff

# Add to specific dependency group
uv add --group docs sphinx sphinx-rtd-theme
```

### Optional Dependencies

```bash
# Add pandas with optional dependencies
uv add pandas --optional plot

# Install with optional dependencies
uv sync --extra plot
```

### Removing Dependencies

```bash
# Remove a dependency
uv remove requests

# Remove development dependency
uv remove --dev pytest
```

### Upgrading Dependencies

```bash
# Upgrade all dependencies
uv lock --upgrade

# Upgrade specific package
uv lock --upgrade-package requests

# Sync after upgrade
uv sync
```

### Dependency Groups

```toml
# In pyproject.toml
[project.optional-dependencies]
dev = ["pytest>=7.0.0", "ruff>=0.1.0"]
docs = ["sphinx>=5.0.0", "sphinx-rtd-theme"]
test = ["pytest", "pytest-cov", "pytest-mock"]

[tool.uv]
dev-dependencies = [
    "black>=23.0.0",
]
```

```bash
# Install with specific groups
uv sync --group docs
uv sync --group test

# Install only specific group
uv sync --only-group dev

# Exclude a group
uv sync --no-group docs
```

### Lockfile Management

UV creates a `uv.lock` file that ensures reproducible environments:

```bash
# Create/update lockfile
uv lock

# Sync environment to match lockfile
uv sync

# Upgrade dependencies and update lockfile
uv lock --upgrade

# Export to requirements.txt
uv export -o requirements.txt

# Export for specific groups
uv export --group docs -o requirements-docs.txt
```

## Python Version Management

### Installing Python

```bash
# Install specific Python version
uv python install 3.12

# Install multiple versions
uv python install 3.11 3.12 3.13

# Install latest patch version
uv python install 3.12
```

### Listing Python Versions

```bash
# List installed Python versions
uv python list

# List only installed versions
uv python list --only-installed

# List all available versions
uv python list --all-versions
```

### Pinning Python Version

```bash
# Pin Python version for project
uv python pin 3.12

# This creates/updates .python-version file
# Pin to specific patch version
uv python pin 3.12.4

# Pin to latest compatible version
uv python pin 3.12
```

### Using Specific Python Version

```bash
# Run with specific Python
uv run --python 3.11 python script.py

# Create venv with specific Python
uv venv --python 3.12

# Use PyPy
uv run --python [email protected] python script.py
```

### Python Discovery

UV automatically discovers Python installations from:
- System Python
- Homebrew Python
- pyenv Python
- conda Python
- Downloaded UV-managed Python

## Tool Management

UV can run and install command-line tools like `pytest`, `black`, `ruff`, etc.

### Running Tools (uvx)

```bash
# Run tool in ephemeral environment
uvx ruff check .
uvx black .
uvx pytest

# Equivalent to:
uv tool run ruff check .
```

### Installing Tools

```bash
# Install tool globally
uv tool install ruff

# Install specific version
uv tool install "ruff==0.1.0"

# Upgrade installed tool
uv tool upgrade ruff

# List installed tools
uv tool list

# Uninstall tool
uv tool uninstall ruff
```

### Tool Directory

Tools are installed in:
- **macOS/Linux**: `~/.local/share/uv/tools`
- **Windows**: `%APPDATA%\uv\tools`

## The pip Interface

UV provides a drop-in replacement for pip commands:

### Installation Commands

```bash
# Install packages
uv pip install requests

# Install from requirements.txt
uv pip install -r requirements.txt

# Install in editable mode
uv pip install -e .

# Uninstall package
uv pip uninstall requests
```

### Environment Management

```bash
# Create virtual environment
uv venv

# Create with specific Python
uv venv --python 3.12

# Create with specific name
uv venv .venv-custom

# Activate (same as standard venv)
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

### Dependency Resolution

```bash
# Compile requirements
uv pip compile requirements.in -o requirements.txt

# With upgrades
uv pip compile requirements.in --upgrade

# Platform-independent (universal)
uv pip compile requirements.in --universal

# Sync environment
uv pip sync requirements.txt
```

### Listing and Freezing

```bash
# List installed packages
uv pip list

# Freeze dependencies
uv pip freeze

# Freeze to file
uv pip freeze > requirements.txt
```

## Scripts

UV can manage dependencies for single-file scripts:

### Inline Script Dependencies

```python
# script.py
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
#     "pandas",
# ]
# ///

import requests
import pandas as pd

response = requests.get("https://api.example.com/data")
df = pd.DataFrame(response.json())
print(df)
```

```bash
# Add dependencies to script
uv add --script script.py requests pandas

# Run script (UV auto-installs dependencies)
uv run script.py
```

### Script Management

```bash
# Run script with inline dependencies
uv run script.py

# Run with specific Python version
uv run --python 3.12 script.py
```

## Building and Publishing

### Building Packages

```bash
# Build wheel and sdist
uv build

# Build only wheel
uv build --wheel

# Build only sdist
uv build --sdist

# Build to specific directory
uv build --out-dir dist/
```

### Publishing Packages

```bash
# Publish to PyPI
uv publish

# Publish to TestPyPI
uv publish --publish-url https://test.pypi.org/legacy/

# Publish with token
uv publish --token <token>

# Publish with username/password
uv publish --username <user> --password <pass>
```

### Package Configuration

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-package"
version = "0.1.0"
description = "My awesome package"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "[email protected]"}
]
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
]
dependencies = [
    "requests>=2.31.0",
]

[project.urls]
Homepage = "https://github.com/user/repo"
Documentation = "https://docs.example.com"
Repository = "https://github.com/user/repo.git"
```

## Configuration

### pyproject.toml Configuration

```toml
[tool.uv]
# Python version constraints
python = ">=3.11"

# Package indexes
index-url = "https://pypi.org/simple"
extra-index-url = ["https://example.com/simple"]

# Dependency resolution
resolution = "highest"  # or "lowest", "lowest-direct"

# Package sources
[tool.uv.sources]
my-package = { git = "https://github.com/user/repo.git" }
local-package = { path = "../local-package" }

# Dependency groups
dev-dependencies = [
    "pytest>=7.0.0",
    "ruff>=0.1.0",
]
```

### Environment Variables

```bash
# Custom Python installation directory
export UV_PYTHON_INSTALL_DIR="$HOME/.python"

# Custom cache directory
export UV_CACHE_DIR="$HOME/.cache/uv"

# Disable cache
export UV_NO_CACHE=1

# Custom index URL
export UV_INDEX_URL="https://pypi.org/simple"

# Offline mode
export UV_OFFLINE=1
```

### UV Settings File

Create `~/.config/uv/uv.toml` (or `%APPDATA%\uv\uv.toml` on Windows):

```toml
# Global UV configuration
native-tls = true
no-cache = false
cache-dir = "~/.cache/uv"

[pip]
index-url = "https://pypi.org/simple"
```

## Caching

UV uses aggressive caching for speed:

### Cache Location

- **macOS/Linux**: `~/.cache/uv`
- **Windows**: `%LOCALAPPDATA%\uv\cache`

### Cache Commands

```bash
# View cache directory
uv cache dir

# Clean cache
uv cache clean

# Clean specific package
uv cache clean requests

# Prune old cache entries
uv cache prune
```

### Cache Behavior

UV caches:
- Downloaded packages and wheels
- Built wheels from source distributions
- Package metadata
- Git repositories
- Python installations

## Performance Tips

**Parallel Downloads:**
- UV downloads packages in parallel by default
- Uses global cache to avoid re-downloads

**Universal Resolution:**
- Create platform-independent lockfiles
- Faster CI/CD across different platforms

```bash
uv lock --universal
```

**Offline Mode:**
```bash
# Use only cached packages
uv sync --offline
```

**Pre-warming Cache:**
```bash
# Download all dependencies without installing
uv sync --no-install
```

## Common Issues and Solutions

### Permission Denied

```bash
# Change ownership of UV directory
sudo chown -R $USER ~/.local/share/uv  # macOS/Linux
```

### Python Version Not Found

```bash
# Install the required Python version
uv python install 3.12

# Or point to existing Python
uv venv --python /usr/bin/python3.12
```

### Dependency Conflicts

```bash
# Try different resolution strategy
uv lock --resolution lowest

# Override specific package version
uv add "package==1.0.0"

# Check for conflicts
uv pip tree
```

### Cache Issues

```bash
# Clear cache and reinstall
uv cache clean
uv sync --reinstall
```

## Best Practices

1. **Always use lockfiles** for reproducible environments
2. **Pin Python versions** in projects with `.python-version`
3. **Use dependency groups** to organize dependencies
4. **Leverage the cache** - don't disable it unless necessary
5. **Use `uv run`** instead of activating virtualenvs
6. **Export requirements.txt** for compatibility with other tools
7. **Use `uvx`** for one-off tool executions
8. **Configure in pyproject.toml** for project-specific settings

## Comparison with Other Tools

| Feature | uv | pip | poetry | conda |
|---------|-----|-----|--------|-------|
| Speed | 10-100x | 1x | 2-5x | 0.5x |
| Lockfiles | ✅ | ❌ | ✅ | ✅ |
| Python Management | ✅ | ❌ | ❌ | ✅ |
| Project Init | ✅ | ❌ | ✅ | ❌ |
| Tool Running | ✅ | ❌ | ❌ | ❌ |
| Universal Locks | ✅ | ❌ | ❌ | ✅ |
| Written in | Rust | Python | Python | Python |
| Memory Usage | Low | Medium | Medium | High |

## Resources

- [UV Documentation](https://docs.astral.sh/uv/)
- [UV GitHub](https://github.com/astral-sh/uv)
- [UV Benchmarks](https://github.com/astral-sh/uv/blob/main/BENCHMARKS.md)
- [PEP 751 - Lockfile Standard](https://peps.python.org/pep-0751/)
