# pytest Reference

Modern Python testing with pytest and key plugins.

**Docs**: https://docs.pytest.org/en/stable/ | **GitHub**: https://github.com/pytest-dev/pytest

## Installation

```bash
uv add --dev pytest pytest-asyncio pytest-cov pytest-mock
```

## Running Tests

```bash
uv run pytest                          # Run all tests
uv run pytest tests/test_models.py     # Specific file
uv run pytest tests/test_models.py::test_create  # Specific test
uv run pytest -x                       # Stop on first failure
uv run pytest -x --pdb                 # Drop into debugger on failure
uv run pytest -k "test_user"           # Match test names
uv run pytest -m "not slow"            # Skip marked tests
uv run pytest -v                       # Verbose output
uv run pytest --tb=short               # Short tracebacks
uv run pytest -n auto                  # Parallel (needs pytest-xdist)
```

## pyproject.toml Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"                  # pytest-asyncio: auto-detect async tests
addopts = [
    "--strict-markers",                # Error on unknown markers
    "--strict-config",                 # Error on config issues
    "-ra",                             # Show summary for all non-passing tests
]

markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: integration tests",
]

filterwarnings = [
    "error",                           # Treat warnings as errors
    "ignore::DeprecationWarning:some_lib",  # Selectively ignore
]
```

### Coverage Config

```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
fail_under = 80
```

## Key Plugins

### pytest-asyncio (1.0+)

With `asyncio_mode = "auto"` in config, no decorators needed:

```python
# Async tests - just write async def
async def test_fetch_data():
    result = await my_async_function()
    assert result == expected

# Async fixtures
@pytest.fixture
async def async_client():
    async with SomeAsyncClient() as client:
        yield client

# For custom event loop (e.g., uvloop)
# conftest.py
@pytest.fixture(scope="session")
def event_loop_policy():
    import uvloop
    return uvloop.EventLoopPolicy()
```

Breaking changes in 1.0: the `event_loop` fixture was removed. Use `asyncio.get_running_loop()` instead.

### pytest-cov

```bash
uv run pytest --cov=src --cov-report=term-missing
uv run pytest --cov=src --cov-report=html     # HTML report in htmlcov/
```

### pytest-mock

```python
def test_with_mock(mocker):
    mock_api = mocker.patch("myapp.services.external_api")
    mock_api.get_data.return_value = {"status": "ok"}
    result = my_function()
    mock_api.get_data.assert_called_once()
```

### pytest-xdist (Parallel)

```bash
uv add --dev pytest-xdist
uv run pytest -n auto          # Use all CPU cores
uv run pytest -n 4             # Use 4 workers
```

## Fixtures

### Scope Hierarchy

1. **function** (default) - per test
2. **class** - per test class
3. **module** - per .py file
4. **package** - per directory
5. **session** - once for entire run

### Common Patterns

```python
# Yield fixture (setup + teardown)
@pytest.fixture
def db_session(database):
    database.execute("BEGIN")
    yield database
    database.execute("ROLLBACK")

# Factory fixture
@pytest.fixture
def make_user():
    created = []
    def _make(name="test", email="[email protected]"):
        user = User(name=name, email=email)
        created.append(user)
        return user
    yield _make
    for u in created:
        u.delete()

# Parametrized fixture
@pytest.fixture(params=["sqlite", "postgres"])
def database(request):
    if request.param == "sqlite":
        return create_sqlite_db()
    return create_postgres_db()

# Session-scoped resource
@pytest.fixture(scope="session")
def app():
    app = create_app(testing=True)
    yield app
```

### Built-in Fixtures

| Fixture | Purpose |
|---------|---------|
| `tmp_path` | `pathlib.Path` to unique temp directory |
| `monkeypatch` | Modify objects/env vars (auto-reverted) |
| `capsys` | Capture stdout/stderr |
| `request` | Test metadata (params, markers, etc.) |

### monkeypatch Examples

```python
def test_env_var(monkeypatch):
    monkeypatch.setenv("APP_NAME", "test-app")
    result = get_config()
    assert result.app_name == "test-app"

def test_patched_function(monkeypatch):
    monkeypatch.setattr("myapp.services.fetch_data", lambda: {"mock": True})
    result = process()
    assert result["mock"] is True
```

## conftest.py

Fixtures in `conftest.py` are auto-discovered for all tests in the same directory and below. Never import from conftest files.

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="session")
def project_root():
    from pathlib import Path
    return Path(__file__).parent.parent

@pytest.fixture
def mock_api(monkeypatch):
    monkeypatch.setattr("myapp.api.client.fetch", lambda url: {"data": []})

# Custom CLI option
def pytest_addoption(parser):
    parser.addoption("--run-integration", action="store_true", default=False)

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-integration"):
        skip = pytest.mark.skip(reason="need --run-integration")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip)
```

## Parametrize

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", 5),
    ("", 0),
    ("world", 5),
])
def test_length(input, expected):
    assert len(input) == expected

# Multiple parametrize = cartesian product
@pytest.mark.parametrize("x", [1, 2])
@pytest.mark.parametrize("y", [10, 20])
def test_multiply(x, y):
    assert x * y > 0
```

## Project Structure

```
tests/
  conftest.py               # Shared fixtures
  test_models.py            # Unit tests
  test_services.py
  integration/
    conftest.py             # Integration-specific fixtures
    test_api.py
```

## Justfile Recipes

```just
test *ARGS:
    uv run pytest {{ARGS}}

test-cov:
    uv run pytest --cov=src --cov-report=term-missing

test-watch:
    uv run pytest -x --watch   # Needs pytest-watch plugin
```
