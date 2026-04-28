# uv Reference (0.11.x)

Complete guide to uv - the Python package manager, version manager, and project runner.

> **Heads up (0.10 -> 0.11)**: `uv venv` now requires explicit `--clear` to remove an existing environment (was implicit). `--native-tls` is deprecated in favor of `--system-certs`. `uv python upgrade`, `--upgrade-group`, and workspace commands `uv workspace dir` / `uv workspace list` are now stable. Always run a recent uv (>= 0.11.6) to pick up the wheel-uninstall path-traversal fix (GHSA-pjjw-68hj-v9mw).

**Docs**: https://docs.astral.sh/uv/ | **GitHub**: https://github.com/astral-sh/uv

## Installation

```bash
# macOS/Linux (Homebrew)
brew install uv

# Or via pip
pip install uv

# Verify
uv version
```

## Project Initialization

### `uv init` Templates

```bash
# Application (flat layout, no build system)
uv init my-app

# Packaged application (src layout, build system, entry point) - PREFERRED
uv init --package my-project

# Library (src layout, py.typed marker)
uv init --lib my-lib

# Minimal (only pyproject.toml)
uv init --bare my-project

# With specific build backend
uv init --package --build-backend hatchling my-project

# With author from git config
uv init --package --author-from git my-project
```

### Key `uv init` Flags

| Flag | Effect |
|------|--------|
| `--app` | Application template (default) |
| `--package` | Packaged app with build system and src layout |
| `--lib` | Library (implies --package, adds py.typed) |
| `--bare` | Only pyproject.toml, no other files |
| `--build-backend <name>` | hatchling, flit-core, pdm-backend, setuptools, uv_build, maturin |
| `--python <ver>` | Set requires-python |
| `--author-from git` | Pull author from git config |
| `--vcs git` | Init git repo |
| `--python-pin` | Create .python-version file |

### Generated Structure (--package)

```
my-project/
  .python-version
  README.md
  pyproject.toml
  src/
    my_project/
      __init__.py
```

## Dependency Management

### Adding Dependencies

```bash
# Project dependencies
uv add httpx
uv add "httpx>=0.20"
uv add "httpx==0.27.0"

# Dev dependencies (goes to [dependency-groups] dev)
uv add --dev pytest ruff ty

# Named dependency group
uv add --group lint ruff
uv add --group test coverage

# Optional dependencies (extras)
uv add --optional network httpx

# From requirements file
uv add -r requirements.txt

# From git
uv add git+https://github.com/encode/httpx
uv add git+https://github.com/encode/httpx --tag 0.27.0
uv add git+https://github.com/encode/httpx --branch main

# From local path (editable)
uv add --editable ../packages/foo/

# With platform markers
uv add "jax; sys_platform == 'linux'"

# Control version bound style
uv add httpx --bounds exact     # ==x.y.z
uv add httpx --bounds minor     # >=x.y.z, <x.y+1.0
uv add httpx --bounds major     # >=x.y.z, <x+1.0.0
uv add httpx --bounds lower     # >=x.y.z (default)
```

### Removing Dependencies

```bash
uv remove httpx
uv remove --dev pytest
uv remove --group lint ruff
```

### Lockfile

```bash
uv lock                           # Create/update uv.lock
uv lock --check                   # Check if up-to-date (no changes)
uv lock --upgrade                 # Upgrade all to latest allowed
uv lock --upgrade-package httpx   # Upgrade specific package
uv lock --upgrade-group lint      # Upgrade everything in a dependency-group (uv 0.11.4+)
```

### Syncing Environment

```bash
uv sync                       # Exact sync (default - removes extraneous)
uv sync --inexact             # Don't remove extraneous packages
uv sync --no-dev              # Exclude dev group
uv sync --all-groups          # Include all groups
uv sync --group docs          # Include specific group
uv sync --all-extras          # Include all extras
uv sync --locked              # Error if lockfile outdated
uv sync --frozen              # Don't check lockfile
uv sync --no-install-project  # Skip installing the project itself
```

#### What `uv sync` installs

uv ships with `dev` in `default-groups`, so a bare `uv sync` already pulls dev deps. Other named groups only install when requested.

| Command | Installs |
|---|---|
| `uv sync` | main deps + `dev` |
| `uv sync --no-dev` | main deps only |
| `uv sync --group lint` | main deps + `dev` + `lint` |
| `uv sync --all-groups` | everything in `[dependency-groups]` |

To change the default set, declare it explicitly:

```toml
[tool.uv]
default-groups = ["dev", "test"]   # uv sync now includes both
```

### Exporting

```bash
uv export --format requirements.txt -o requirements.txt
uv export --format pylock.toml                    # PEP 751
uv export --format cyclonedx1.5                   # SBOM
```

## Running Code

### `uv run`

```bash
# Run Python files
uv run main.py
uv run python -c "import example"

# Run entry points
uv run my-cli-command

# Run with extra temporary dependencies
uv run --with httpx python -c "import httpx"

# Run with specific Python version
uv run --python 3.12 main.py

# Run without syncing
uv run --no-sync pytest

# Stdin
echo 'print("hello")' | uv run -
```

### Inline Script Metadata (PEP 723)

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "requests<3",
#   "rich",
# ]
# ///

import requests
from rich.pretty import pprint
resp = requests.get("https://peps.python.org/api/peps.json")
pprint(resp.json())
```

Run with: `uv run script.py` - dependencies install automatically.

### `uvx` (Tool Runner)

```bash
uvx ruff check .              # Run tool without installing
uvx ruff@0.6.0 --version      # Specific version
uvx --with mkdocs-material mkdocs build

# Install persistently
uv tool install ruff
uv tool upgrade ruff
uv tool list
uv tool uninstall ruff
```

## Python Version Management

```bash
# Install
uv python install 3.13
uv python install 3.12 3.13    # Multiple
uv python install pypy          # Alternative implementation

# Pin (creates .python-version)
uv python pin 3.13
uv python pin --global 3.13     # Global default

# List
uv python list
uv python list --only-installed

# Upgrade patch versions
uv python upgrade 3.13          # 3.13.x -> latest 3.13.y
uv python upgrade               # All installed

# Find
uv python find '>=3.12'

# Remove
uv python uninstall 3.12
```

## pyproject.toml Configuration

### `[tool.uv]` Settings

```toml
[tool.uv]
managed = true                    # uv manages this project
required-version = ">=0.10.0"     # Enforce minimum uv version
default-groups = ["dev"]          # Groups to sync by default

# Resolution
resolution = "highest"            # highest, lowest, lowest-direct
prerelease = "if-necessary-or-explicit"

# Performance
compile-bytecode = false
link-mode = "clone"               # clone (macOS), hardlink (Linux)
```

### `[tool.uv.sources]` - Custom Dependency Sources

```toml
[tool.uv.sources]
# From specific index
torch = { index = "pytorch" }

# From git
httpx = { git = "https://github.com/encode/httpx", tag = "0.27.0" }

# Local editable
my-lib = { path = "../my-lib", editable = true }

# Workspace member
my-pkg = { workspace = true }
```

### `[[tool.uv.index]]` - Package Indexes

```toml
[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cpu"
explicit = true    # Only used when referenced in sources

[[tool.uv.index]]
name = "private"
url = "https://private.example.com/simple/"
default = true     # Replaces PyPI
```

### `[dependency-groups]` (PEP 735)

```toml
[dependency-groups]
dev = [
    "ruff>=0.15.0",
    "ty>=0.0.30",
    "pytest>=9.0.0",
    {include-group = "lint"},
]
lint = ["ruff"]
test = ["pytest", "coverage"]
docs = ["sphinx", "furo"]
```

`[dependency-groups]` is PEP 735 and supported by uv (and modern pip 25+). For libraries published to PyPI that need broader tooling support, `[project.optional-dependencies]` (extras) remains the portable choice.

## CLI Entry Points (`[project.scripts]`)

Declare console scripts in `pyproject.toml`:

```toml
[project.scripts]
my-project = "my_project:main"
my-project-admin = "my_project.cli:admin"
```

Format is `<script-name> = "<module>:<callable>"`. Two requirements:

1. **A build system.** Editable installs (which `uv sync` performs for the current project) need `[build-system]`. Without it, `uv sync` errors with "project requires a build system to install".

   ```toml
   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"

   [tool.hatch.build.targets.wheel]
   packages = ["src/my_project"]
   ```

2. **A matching callable.** `my_project:main` resolves to the `main` attribute of `src/my_project/__init__.py`. `my_project.cli:admin` resolves to `admin` in `src/my_project/cli.py`.

   ```python
   # src/my_project/__init__.py
   def main() -> None:
       print("hello from my-project")
   ```

After `uv sync`, run with `uv run my-project`. uv installs the project editable, so edits under `src/` take effect on the next invocation - no reinstall.

## Workspaces (Monorepos)

Root `pyproject.toml`:

```toml
[tool.uv.workspace]
members = ["packages/*"]
exclude = ["packages/experimental"]
```

```bash
uv workspace list       # List all members
uv workspace dir        # Show workspace root
uv run --package foo    # Run in specific member's context
```

Key: single `uv.lock` for entire workspace, single `requires-python` intersection.

## Build and Publish

```bash
# Build
uv build                     # sdist + wheel into dist/
uv build --wheel             # Wheel only
uv build --no-sources        # Ignore tool.uv.sources (before publishing)

# Version management
uv version                   # Read current
uv version 1.0.0             # Set exact
uv version --bump patch      # 1.2.3 -> 1.2.4
uv version --bump minor      # 1.2.3 -> 1.3.0
uv version --bump major      # 1.2.3 -> 2.0.0

# Publish
uv publish                   # To PyPI
uv publish --token <TOKEN>
uv publish --index testpypi

# Prevent accidental PyPI publish
# Add to classifiers: "Private :: Do Not Upload"
```

## CI/CD (GitHub Actions)

```yaml
name: CI
on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true
      - run: uv sync --all-groups
      - run: uv run ty check
      - run: uv run ruff check
      - run: uv run ruff format --check
      - run: uv run pytest
```

## Troubleshooting

```bash
uv cache clean               # Clear package cache
uv lock --upgrade             # Regenerate lockfile
rm -rf .venv && uv sync      # Reset environment
uv python list --only-installed  # Check Python installations
```
