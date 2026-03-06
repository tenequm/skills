# Advanced Workflows with UV and Ruff

Comprehensive guide for advanced use cases, monorepos, Docker integration, and production deployments.

## Table of Contents

1. [Monorepo Management](#monorepo-management)
2. [Docker Integration](#docker-integration)
3. [CI/CD Pipelines](#cicd-pipelines)
4. [Development Workflows](#development-workflows)
5. [Production Deployments](#production-deployments)
6. [Team Collaboration](#team-collaboration)

## Monorepo Management

### Workspace Setup

UV supports Cargo-style workspaces for managing multiple packages in one repository.

**Project Structure:**
```
monorepo/
├── pyproject.toml          # Workspace root
├── uv.lock                 # Shared lockfile
├── packages/
│   ├── core/
│   │   ├── pyproject.toml
│   │   └── src/
│   ├── api/
│   │   ├── pyproject.toml
│   │   └── src/
│   └── cli/
│       ├── pyproject.toml
│       └── src/
└── apps/
    └── web/
        ├── pyproject.toml
        └── src/
```

**Root pyproject.toml:**
```toml
[tool.uv.workspace]
members = [
    "packages/*",
    "apps/*"
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "ruff>=0.1.0",
]
```

**Package pyproject.toml (core):**
```toml
[project]
name = "myproject-core"
version = "0.1.0"
dependencies = [
    "pydantic>=2.0.0",
]

[tool.uv.sources]
# No sources needed - uses workspace
```

**Package pyproject.toml (api):**
```toml
[project]
name = "myproject-api"
version = "0.1.0"
dependencies = [
    "fastapi>=0.100.0",
    "myproject-core",  # Workspace dependency
]

[tool.uv.sources]
myproject-core = { workspace = true }
```

### Working with Workspaces

```bash
# Install all workspace packages
uv sync

# Run commands from root
uv run --package myproject-api python -m uvicorn main:app

# Run tests for specific package
uv run --package myproject-core pytest

# Add dependency to specific package
cd packages/api
uv add requests
```

### Shared Ruff Configuration

**Root pyproject.toml:**
```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B"]
```

**Per-package overrides:**
```toml
# packages/cli/pyproject.toml
[tool.ruff.lint.per-file-ignores]
"src/cli/*.py" = ["T201"]  # Allow prints in CLI
```

### Monorepo Scripts

**Makefile:**
```makefile
.PHONY: install lint format test

install:
\tuv sync

lint:
\truff check .

format:
\truff format .

test:
\tuv run pytest

# Per-package commands
test-core:
\tuv run --package myproject-core pytest

test-api:
\tuv run --package myproject-api pytest
```

## Docker Integration

### Multi-Stage Dockerfile

```dockerfile
# syntax=docker/dockerfile:1

# Stage 1: Build stage with UV
FROM python:3.12-slim AS builder

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-cache

# Stage 2: Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Set PATH to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Run application
CMD ["python", "-m", "myapp"]
```

### Development Dockerfile

```dockerfile
FROM python:3.12-slim

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install all dependencies (including dev)
RUN uv sync --frozen --no-cache

# Copy code
COPY . .

# Development server
CMD ["uv", "run", "python", "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
      - uv-cache:/root/.cache/uv
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    command: uv run python -m uvicorn main:app --reload --host 0.0.0.0

  worker:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
      - uv-cache:/root/.cache/uv
    command: uv run python -m celery worker

volumes:
  uv-cache:
```

### Optimized Production Dockerfile

```dockerfile
FROM python:3.12-slim AS builder

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy files
COPY pyproject.toml uv.lock ./
COPY src ./src

# Install dependencies and application
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.12-slim

WORKDIR /app

# Copy only necessary files
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-m", "myapp"]
```

## CI/CD Pipelines

### GitHub Actions

**Complete Workflow:**
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install UV
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync --frozen

      - name: Lint with Ruff
        run: |
          uv run ruff check .
          uv run ruff format --check .

      - name: Type check with mypy
        run: uv run mypy src/

      - name: Security check
        run: uv run ruff check --select S .

  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.11', '3.12']
    steps:
      - uses: actions/checkout@v4

      - name: Install UV
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Set up Python
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --frozen

      - name: Run tests
        run: uv run pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  build:
    needs: [quality, test]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Install UV
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Build package
        run: uv build

      - name: Publish to PyPI
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.PYPI_TOKEN }}
        run: uv publish
```

### GitLab CI

```yaml
stages:
  - lint
  - test
  - build
  - deploy

variables:
  UV_CACHE_DIR: ${CI_PROJECT_DIR}/.cache/uv

cache:
  paths:
    - .cache/uv
    - .venv

before_script:
  - curl -LsSf https://astral.sh/uv/install.sh | sh
  - export PATH="$HOME/.local/bin:$PATH"
  - uv sync --frozen

lint:
  stage: lint
  script:
    - uv run ruff check .
    - uv run ruff format --check .

test:
  stage: test
  parallel:
    matrix:
      - PYTHON_VERSION: ['3.11', '3.12']
  script:
    - uv python install $PYTHON_VERSION
    - uv sync --frozen
    - uv run pytest --cov=src

build:
  stage: build
  only:
    - main
  script:
    - uv build
  artifacts:
    paths:
      - dist/

deploy:
  stage: deploy
  only:
    - main
  script:
    - uv publish --token $PYPI_TOKEN
```

### Circle CI

```yaml
version: 2.1

executors:
  python-executor:
    docker:
      - image: python:3.12-slim

jobs:
  lint:
    executor: python-executor
    steps:
      - checkout
      - run:
          name: Install UV
          command: curl -LsSf https://astral.sh/uv/install.sh | sh
      - run:
          name: Lint
          command: |
            export PATH="$HOME/.local/bin:$PATH"
            uv sync --frozen
            uv run ruff check .
            uv run ruff format --check .

  test:
    executor: python-executor
    steps:
      - checkout
      - run:
          name: Install UV
          command: curl -LsSf https://astral.sh/uv/install.sh | sh
      - run:
          name: Test
          command: |
            export PATH="$HOME/.local/bin:$PATH"
            uv sync --frozen
            uv run pytest

workflows:
  main:
    jobs:
      - lint
      - test
      - deploy:
          requires:
            - lint
            - test
          filters:
            branches:
              only: main
```

## Development Workflows

### Pre-commit Integration

**.pre-commit-config.yaml:**
```yaml
repos:
  # Ruff linting and formatting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.12.8
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  # Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  # Security
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.12.8
    hooks:
      - id: ruff
        name: ruff-security
        args: [--select, S]

  # Standard hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

**Install hooks:**
```bash
uv add --dev pre-commit
uv run pre-commit install
```

### VS Code Integration

**.vscode/settings.json:**
```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    },
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "ruff.lint.args": ["--config=pyproject.toml"],
  "ruff.format.args": ["--config=pyproject.toml"],
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"]
}
```

**.vscode/tasks.json:**
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "UV: Sync",
      "type": "shell",
      "command": "uv sync",
      "group": "build"
    },
    {
      "label": "Ruff: Check",
      "type": "shell",
      "command": "uv run ruff check .",
      "group": "test"
    },
    {
      "label": "Ruff: Format",
      "type": "shell",
      "command": "uv run ruff format .",
      "group": "build"
    },
    {
      "label": "Test",
      "type": "shell",
      "command": "uv run pytest",
      "group": {
        "kind": "test",
        "isDefault": true
      }
    }
  ]
}
```

### Development Scripts

**justfile (like Makefile but better):**
```justfile
# Install dependencies
install:
    uv sync

# Run development server
dev:
    uv run python -m uvicorn main:app --reload

# Lint and format
lint:
    uv run ruff check --fix .
    uv run ruff format .

# Type check
typecheck:
    uv run mypy src/

# Run tests
test:
    uv run pytest -v

# Run tests with coverage
test-cov:
    uv run pytest --cov=src --cov-report=html

# Security check
security:
    uv run ruff check --select S .

# Update dependencies
update:
    uv lock --upgrade
    uv sync

# Clean caches
clean:
    uv cache clean
    ruff clean
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type d -name .pytest_cache -exec rm -rf {} +

# All quality checks
check: lint typecheck security test
```

## Production Deployments

### AWS Lambda

```dockerfile
FROM public.ecr.aws/lambda/python:3.12

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy application
COPY pyproject.toml uv.lock ./
COPY src ${LAMBDA_TASK_ROOT}/src

# Install dependencies
RUN uv sync --frozen --no-dev --no-cache

# Lambda handler
CMD ["src.handler.lambda_handler"]
```

### Google Cloud Run

```dockerfile
FROM python:3.12-slim

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

COPY . .

ENV PORT=8080
CMD exec uv run python -m uvicorn main:app --host 0.0.0.0 --port ${PORT}
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:latest
        ports:
        - containerPort: 8000
        env:
        - name: PYTHONUNBUFFERED
          value: "1"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Helm Chart

**values.yaml:**
```yaml
image:
  repository: myapp
  tag: latest
  pullPolicy: IfNotPresent

replicaCount: 3

service:
  type: ClusterIP
  port: 80
  targetPort: 8000

env:
  - name: PYTHONUNBUFFERED
    value: "1"
  - name: LOG_LEVEL
    value: "info"

resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

## Team Collaboration

### Shared Configuration

**pyproject.toml:**
```toml
[project]
name = "myproject"
version = "0.1.0"
requires-python = ">=3.11"

[tool.uv]
# Shared dev dependencies
dev-dependencies = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]

[tool.ruff]
# Team-wide code style
line-length = 88
target-version = "py311"

[tool.ruff.lint]
# Agreed upon rules
select = ["E", "W", "F", "I", "B", "UP"]
ignore = []

[tool.ruff.lint.per-file-ignores]
# Consistent exceptions
"tests/*" = ["S101"]
"__init__.py" = ["F401"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### Code Review Checklist

**CONTRIBUTING.md:**
```markdown
## Code Review Checklist

Before submitting a PR:

- [ ] Run `uv run ruff check --fix .`
- [ ] Run `uv run ruff format .`
- [ ] Run `uv run mypy src/`
- [ ] Run `uv run pytest`
- [ ] Update `uv.lock` if dependencies changed
- [ ] Add tests for new features
- [ ] Update documentation
- [ ] Ensure CI passes
```

### Onboarding Guide

**README.md:**
```markdown
## Getting Started

### Prerequisites

- Python 3.11+
- UV package manager

### Setup

1. Install UV:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone repository:
   ```bash
   git clone https://github.com/org/repo.git
   cd repo
   ```

3. Install dependencies:
   ```bash
   uv sync
   ```

4. Run tests:
   ```bash
   uv run pytest
   ```

5. Start development server:
   ```bash
   uv run python -m uvicorn main:app --reload
   ```

### Development Commands

- `uv run ruff check --fix .` - Lint code
- `uv run ruff format .` - Format code
- `uv run pytest` - Run tests
- `uv run mypy src/` - Type check

### Adding Dependencies

```bash
uv add package-name
```

### Updating Dependencies

```bash
uv lock --upgrade
uv sync
```
```

## Performance Optimization

### Caching Strategies

```bash
# Pre-warm cache in CI
- name: Cache UV
  uses: actions/cache@v3
  with:
    path: ~/.cache/uv
    key: ${{ runner.os }}-uv-${{ hashFiles('uv.lock') }}

# Use frozen lockfile for reproducibility
uv sync --frozen

# Offline mode for airgapped environments
uv sync --offline
```

### Build Optimization

```bash
# Compile bytecode
export UV_COMPILE_BYTECODE=1

# Use system Python if available
export UV_SYSTEM_PYTHON=1

# Skip cache in CI
export UV_NO_CACHE=1
```

## Troubleshooting

### Common Issues

**Slow dependency resolution:**
```bash
# Use frozen lockfile
uv sync --frozen

# Clear cache
uv cache clean
```

**Out of disk space:**
```bash
# Prune old cache entries
uv cache prune

# Check cache size
du -sh ~/.cache/uv
```

**Permission errors:**
```bash
# Fix ownership
sudo chown -R $USER ~/.cache/uv
sudo chown -R $USER ~/.local/share/uv
```

## Resources

- [UV Documentation](https://docs.astral.sh/uv/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
