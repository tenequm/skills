---
name: python-dev
description: Opinionated Python development setup with uv, ty, ruff, pytest, lefthook, and just. Use when creating a new Python project, writing or fixing pyproject.toml, or configuring linting, formatting, type checking, testing, git hooks, or CI.
metadata:
  version: "0.3.0"
  categories: "development"
  topics: "python, uv, ruff, pytest, lefthook"
  upstream: "uv@0.12.11, ty@0.0.79, ruff@0.16.6, pytest@9.1.1, pytest-asyncio@1.4.0, lefthook@2.1.12"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/python-dev
    emoji: "🐍"
---

# Python Development Setup

Opinionated, production-ready Python development stack. No choices to make - just use this.

## When to Use

- Starting a new Python project
- Modernizing an existing project (migrating from pip/poetry/mypy/black/flake8)
- Setting up linting, formatting, type checking, or testing
- Creating a Justfile for project commands
- Configuring pyproject.toml as the single source of truth

## The Stack

| Tool | Role | Replaces |
|------|------|----------|
| [uv](https://docs.astral.sh/uv/) 0.12+ | Package manager, Python versions, runner | pip, poetry, pyenv, virtualenv |
| [ty](https://docs.astral.sh/ty/) (beta) | Type checker (Astral, Rust) | mypy, pyright |
| [ruff](https://docs.astral.sh/ruff/) | Linter + formatter | flake8, black, isort, pyupgrade |
| [pytest](https://docs.pytest.org/) | Testing | unittest |
| [just](https://just.systems/) | Command runner | make |
| [lefthook](https://lefthook.dev/) 2.1+ | Git hooks (single binary, parallel) | pre-commit |

> **Note on ty**: ty is in beta (0.0.x) - no stable API, and inference can change between any
> two versions, so pin it. Pydantic is no longer a fair complaint: ty has shipped a dedicated
> library-support track for it since 0.0.57 (constructors, `model_config`, `BaseSettings`,
> `RootModel`, strict vs lax). Django and SQLAlchemy still have no such support and remain the
> likely source of false positives. Before swapping the whole checker, reach for
> `[tool.ty.analysis] replace-imports-with-any = ["sqlalchemy.**"]`, which silences one bad
> dependency instead of all of them. If you do need rock-solid checking today, swap `ty` for
> `pyright` and keep the rest of the stack unchanged.

## Quick Start: New Project

```bash
# 1. Create project with src layout (uv 0.12+ packages by default; --package is redundant)
uv init my-project
cd my-project

# 2. Pin Python version
uv python pin 3.13

# 3. Add dev dependencies
uv add --dev ruff ty pytest pytest-asyncio lefthook

# 4. Create Justfile and lefthook.yml (see templates below)
# 5. Configure pyproject.toml (see template below)
# 6. Install git hooks
uv run lefthook install

# 7. Run checks
just check
```

## pyproject.toml Template

This is the single config file. Copy this and adjust `[project]` fields.

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "Project description"
readme = "README.md"
requires-python = ">=3.13"
license = {text = "MIT"}
dependencies = []

[project.scripts]
my-project = "my_project:main"   # CLI: `uv run my-project` -> main() in src/my_project/__init__.py

[dependency-groups]
dev = [
    "ruff>=0.16.6",          # 0.16 changed the default rule set - see the lint note below
    "ty>=0.0.79",            # beta: pin tight, inference changes between minors
    "pytest>=9.1.1",         # 9.1 fixed addopts strictness being ignored
    "pytest-asyncio>=1.4.0", # 1.4 added the loop-factories hook
    "lefthook>=2.1.12",
]

# uv 0.12+ generates `uv_build` here instead. Keep that unless you need a hatchling
# plugin - this block is a deliberate override, not what `uv init` gives you.
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/my_project"]

# =============================================================================
# RUFF - Loose, helpful rules only
# =============================================================================
[tool.ruff]
target-version = "py313"
line-length = 100

[tool.ruff.lint]
# Ruff 0.16 enables 413 rules by default (up from 59). Do NOT write a `select`
# list here unless you mean to shrink that - `select = ["E","F","I","UP"]` now
# makes ruff weaker than no config at all. Narrow with `extend-select`/`ignore`.
ignore = [
    "E501",   # line too long - formatter handles it
    "UP007",  # X | Y unions - Optional[X] is more readable
]
exclude = [".git", ".venv", "__pycache__", "build", "dist"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "lf"
# Ruff 0.16 formats Python blocks inside Markdown by default. Drop this line
# only if you want README code fences reformatted too.
exclude = ["*.md"]

# =============================================================================
# TY - Type Checker
# =============================================================================
[tool.ty.environment]
python-version = "3.13"

[tool.ty.src]
include = ["src"]

# =============================================================================
# PYTEST
# =============================================================================
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
# pytest 9.0 silently ignored --strict-markers/--strict-config passed via
# addopts. Use the ini keys, which work on 9.0 and 9.1 alike. `strict = true`
# is the shorthand and also covers strict_xfail + strict_parametrization_ids.
strict = true
addopts = ["-ra"]
```

`asyncio_default_fixture_loop_scope` is intentionally unset above; pytest-asyncio warns about
that on every run. Set it to `"function"` to silence the warning and lock the behavior in.

## Justfile Template

```just
# Check types, lint, and formatting (non-mutating; mirrors CI)
check:
    uv run ty check
    uv run ruff check
    uv run ruff format --check

# Run tests
test *ARGS:
    uv run pytest {{ARGS}}

# Run tests with coverage
test-cov:
    uv run pytest --cov=src --cov-report=term-missing

# Auto-fix and format
fix:
    uv run ruff check --fix
    uv run ruff format

# Install/sync all dependencies
install:
    uv sync --all-groups
    uv run lefthook install

# Update all dependencies
update:
    uv lock --upgrade
    uv sync --all-groups

# Clean build artifacts
clean:
    rm -rf dist/ build/ .pytest_cache/ .ruff_cache/ htmlcov/
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
```

## Lefthook Config

Lefthook replaces pre-commit here for the same reason go-dev uses it: one binary, hooks in
parallel, and - the reason that matters most in Python - the hook runs **your** ruff from
`uv.lock` instead of a second copy pinned separately in a hook config. It installs from PyPI as
a platform wheel, so `uv add --dev lefthook` is the whole install; no Go toolchain.

```bash
uv run lefthook install     # writes .git/hooks/pre-commit and pre-push
```

```yaml
# lefthook.yml
assert_lefthook_installed: true

pre-commit:
  piped: true   # a failed job stops the rest; lint must fix before format runs
  jobs:
    - name: guards
      group:
        parallel: true
        jobs:
          - name: private-key
            run: "! grep -lE 'BEGIN [A-Z ]*PRIVATE KEY' {staged_files}"
          - name: merge-conflict
            run: "! grep -lE '^(<<<<<<<|>>>>>>>) ' {staged_files}"
          - name: large-files
            exclude: ["uv.lock"]
            run: "! find {staged_files} -type f -size +1000k | grep ."
    - name: ruff-check
      glob: "*.{py,pyi,ipynb}"
      run: uv run ruff check --force-exclude --fix {staged_files}
      stage_fixed: true
    - name: ruff-format
      glob: "*.{py,pyi,ipynb}"
      run: uv run ruff format --force-exclude {staged_files}
      stage_fixed: true
    - name: ty
      run: uv run ty check   # no glob - see the glob trap below

pre-push:
  jobs:
    - name: test
      run: uv run pytest
```

**`--force-exclude` is mandatory, not decoration.** Ruff ignores its own `exclude` config for
paths passed explicitly on the command line, and `{staged_files}` passes paths explicitly.
Without the flag a staged file under `[tool.ruff] exclude` gets linted anyway - verified: with
the flag `ruff check --force-exclude src/generated/gen.py` reports `All checks passed`, without
it the same call finds errors. pre-commit users never met this because `ruff-pre-commit` bakes
the flag into its hook entry; on lefthook it is yours to remember.

**`stage_fixed: true` is the ergonomic win over pre-commit.** pre-commit fails the commit when
a hook rewrites a file and makes you re-stage and re-run. lefthook re-runs `git add` on the
fixed files and the commit proceeds. Since 2.1.12 a failing `git add` fails the hook, so a fix
can never slip through unstaged.

**Ordering is why `piped: true` is set.** Ruff's own guidance is lint-with-fix before format,
because `--fix` emits code that then needs reformatting. Piped also means the guards run first
and a leaked key stops the commit before any tool burns time.

Notes worth knowing before editing this config:

- **A `glob` silently skips the whole job when nothing matches** - and that is a gate hole, not
  a convenience. A job with a `glob` but no `{staged_files}` in its `run` is still filtered by
  that glob, so `ty` with `glob: "*.{py,pyi}"` is skipped on a commit that changes only
  `pyproject.toml` - exactly where `[tool.ty]` and your dependency pins live. Verified: such a
  commit prints `ty (skip) no matching staged files` and records with no type check at all.
  Any job that checks the *project* rather than the staged files must carry no glob. The ruff
  jobs above keep theirs because they act on `{staged_files}` and nothing else.
- **`**` matches one or more directories, not zero or more.** `glob: "src/**/*.py"` does *not*
  match `src/main.py`. Use `glob_matcher: doublestar` for the behavior every other tool has.
- **Config location is load-bearing.** lefthook auto-discovers only the repo root or `.config/`
  (the latter since v1.11.12). Anywhere else and commits silently stop running hooks, because
  git invokes the hook directly and no task-runner recipe can intercept that.
- **Never put a mutating job in `pre-push`.** A job that rewrites files there fails the push and
  leaves you with uncommitted edits. `--fix` belongs in `pre-commit`, where `stage_fixed`
  handles it; `pre-push` stays read-only, like the `pytest` job above.
- **`file_types` is available** when a glob is too blunt - `text`, `binary`, `executable`,
  `symlink`, and MIME types including `text/x-python`.
- **Deleted files drop out of `{staged_files}`** and the job is skipped with
  `no files for inspection`, so a deletion-only commit does not error.
- **Unstaged changes are hidden for the hook's duration and restored after**, so the gate judges
  what you are actually committing, not your dirty worktree. Verified on 2.1.12: staging a clean
  file while leaving a broken copy unstaged passes, commits the clean version, and gives the
  unstaged edit back.
- **lefthook is dormant until installed.** `assert_lefthook_installed: true` turns a missing
  binary into a failure instead of hooks silently not firing. Make `lefthook install` part of
  onboarding.
- `lefthook validate` catches a malformed config in CI; `lefthook dump` prints the merged
  effective config. A gitignored `lefthook-local.yml` lets one developer add or skip jobs
  without imposing it on teammates.

**What you give up by leaving pre-commit.** The `pre-commit-hooks` library has no lefthook
equivalent. Three of its hooks were worth keeping and are hand-rolled in the `guards` group
above: `detect-private-key`, `check-merge-conflict` and `check-added-large-files`. Four are
**not** replicated - `check-yaml`, `check-toml`, `end-of-file-fixer`, `trailing-whitespace` and
`mixed-line-ending`: ruff's formatter already handles whitespace and final newlines for Python
files, and the rest only ever covered non-Python files. Add them back as shell jobs if your repo
carries a lot of hand-edited YAML. You also lose `pre-commit autoupdate` and hosted
`pre-commit.ci` - in exchange, `uv lock --upgrade` is now the one place tool versions move.

## Project Structure

Always use src layout:

```
my-project/
  src/
    my_project/
      __init__.py
      cli.py
      models.py
  tests/
    conftest.py
    test_models.py
  pyproject.toml
  Justfile
  uv.lock
  .python-version
  lefthook.yml
  .gitignore
```

## Daily Workflow

```bash
just check          # Type check + lint + format
just test           # Run tests
just test -x        # Stop on first failure
just fix            # Auto-fix lint issues
uv add httpx        # Add a dependency
uv add --dev hypothesis  # Add dev dependency
uv sync             # main deps + dev (dev is in default-groups)
uv sync --all-groups  # everything in [dependency-groups]
uv run python -m my_project  # Run the project
```

## CI (GitHub Actions)

Mirror `just check` + `just test` in CI. Drop this in `.github/workflows/ci.yml`:

```yaml
name: CI
on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: astral-sh/setup-uv@v10.0.1   # pin the full version - see below
      - run: uv sync --all-groups
      - run: uv run ty check
      - run: uv run ruff check --output-format github
      - run: uv run ruff format --check
      - run: uv run pytest
      - run: uv run lefthook validate
```

`astral-sh/setup-uv` installs uv, manages the Python install requested by `.python-version`, and caches the resolver. No separate `setup-python` step needed.

Two things about that pin:

- **Pin the full version, not `@v10`.** From v8 setup-uv stopped publishing floating tags of
  both kinds - *"To increase security even more we will stop publishing minor tags. You won't be
  able to use `@v8` or `@v8.0` any longer."* Confirmed: the `v6` and `v7` refs resolve,
  `v8`/`v9`/`v10` 404. Only exact patch versions exist, so pin one or a commit SHA.
- **Do not set `enable-cache: true`.** The default is `auto`, which since v10 deliberately
  *disables* the cache on `pull_request_target`, `workflow_run` and `release` to block cache
  poisoning. Forcing it on turns that protection off.

## Existing Project Migration

```bash
# 1. Install uv if not present
brew install uv

# 2. Convert requirements.txt to pyproject.toml deps
uv add -r requirements.txt

# 3. Replace mypy with ty
uv remove --dev mypy
uv add --dev ty

# 4. Replace black/flake8/isort with ruff
uv remove --dev black flake8 isort
uv add --dev ruff

# 5. Replace pre-commit with lefthook
uv run pre-commit uninstall      # while it can still read its own config
uv remove --dev pre-commit
rm .pre-commit-config.yaml
uv add --dev lefthook
uv run lefthook install

# 6. Apply pyproject.toml config sections from template above
# 7. Create Justfile and lefthook.yml from templates above
# 8. Run: just check
```

`lefthook install` does not clobber an existing hook - it renames it to
`.git/hooks/pre-commit.old` and tells you so. Running `pre-commit uninstall` first just saves
you deleting that leftover.

## Reference Docs

Detailed guides for each tool in `references/`:
- **uv-reference.md** - Project init, dependencies, lock/sync, Python versions, build/publish
- **ty-reference.md** - Configuration, rules, CLI flags, known limitations
- **ruff-reference.md** - Rule sets, formatter options, per-file ignores, CI integration
- **pytest-reference.md** - Plugins, fixtures, async testing, conftest patterns
- **justfile-reference.md** - Syntax, variables, parameters, shebang recipes, settings

## Resources

- [uv docs](https://docs.astral.sh/uv/) | [uv GitHub](https://github.com/astral-sh/uv)
- [ty docs](https://docs.astral.sh/ty/) | [ty GitHub](https://github.com/astral-sh/ty)
- [ruff docs](https://docs.astral.sh/ruff/) | [ruff GitHub](https://github.com/astral-sh/ruff)
- [pytest docs](https://docs.pytest.org/en/stable/)
- [just manual](https://just.systems/man/en/)
- [lefthook docs](https://lefthook.dev/) | [lefthook GitHub](https://github.com/evilmartians/lefthook)
