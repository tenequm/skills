# gotestsum Reference

Latest: **v1.13.0** (September 2025). Module: `gotest.tools/gotestsum`. Requires Go 1.24+.

A test runner that wraps `go test -json` with readable output, watch mode, JUnit XML, and rerun capabilities.

## Installation

```bash
go install gotest.tools/gotestsum@latest

# Or run without installing
go run gotest.tools/gotestsum@latest

# Homebrew
brew install gotestsum
```

## Basic Usage

```bash
# Run all tests (equivalent to: go test -json ./...)
gotestsum

# With format and race detection
gotestsum --format testname -- -race ./...

# Everything after -- is passed to go test
gotestsum -- -tags=integration -count=1 ./...

# Single package
gotestsum -- ./internal/user

# Specific test
gotestsum -- -run TestMyFunc ./...

# With coverage
gotestsum -- -race -coverprofile=cover.out -covermode=atomic ./...
```

## Output Formats

Set via `--format` flag or `GOTESTSUM_FORMAT` env var. Default: `pkgname`.

| Format | Description |
|--------|-------------|
| `dots` | Print a character for each test |
| `dots-v2` | One package per line |
| `pkgname` | One line per package (default) |
| `pkgname-and-test-fails` | One line per package + failed test output |
| `testname` | One line per test and package |
| `testdox` | Sentence for each test |
| `github-actions` | testname with GitHub Actions log grouping |
| `standard-quiet` | Standard `go test` format |
| `standard-verbose` | Standard `go test -v` format |

**Format icons** (`--format-icons` or `GOTESTSUM_FORMAT_ICONS`):
- `default` - unicode (check, X)
- `hivis` - high visibility unicode
- `text` - PASS, SKIP, FAIL
- `codicons` / `octicons` / `emoticons` - Nerd Fonts

Additional: `--format-hide-empty-pkg` hides packages with no tests.

## Watch Mode

```bash
# Basic watch
gotestsum --watch --format testname

# With screen clearing (v1.13.0+)
gotestsum --watch --watch-clear --format testname

# Watch with chdir (multi-module repos)
gotestsum --watch --watch-chdir
```

**Interactive keys in watch mode:**
- `r` - rerun tests for previous event
- `u` - rerun with `-update` flag (golden files)
- `d` - debug with delve
- `a` - run all tests (`./...`)
- `l` - rescan directories for new `.go` files

## JUnit XML Output

```bash
# Basic JUnit output
gotestsum --junitfile unit-tests.xml

# With CI-friendly format
gotestsum --format github-actions --junitfile unit-tests.xml -- -race ./...

# Customize naming
gotestsum --junitfile unit-tests.xml \
  --junitfile-testsuite-name relative \
  --junitfile-testcase-classname short

# Project name and clean output
gotestsum --junitfile unit-tests.xml \
  --junitfile-project-name "my-service" \
  --junitfile-hide-empty-pkg \
  --junitfile-hide-skipped-tests
```

Name format options (`--junitfile-testsuite-name`, `--junitfile-testcase-classname`):
- `full` (default) - full package path
- `relative` - relative to repo root
- `short` - base package name

## Rerunning Failed Tests

```bash
# Rerun failed tests up to 2 times
gotestsum --rerun-fails --packages="./..." -- -count=1

# Custom retry count and threshold
gotestsum --rerun-fails=3 \
  --rerun-fails-max-failures=5 \
  --packages="./..." \
  -- -count=1

# Rerun root test when subtests fail
gotestsum --rerun-fails --rerun-fails-run-root-test --packages="./..."

# Abort rerun on data race (v1.12.3+)
gotestsum --rerun-fails --rerun-fails-abort-on-data-race --packages="./..."
```

## Tools

### Find Slowest Tests

```bash
gotestsum --format dots --jsonfile test.json ./...
gotestsum tool slowest --jsonfile test.json --threshold 500ms
```

### Auto-skip Slow Tests

```bash
go test -json -short ./... | gotestsum tool slowest --skip-stmt "testing.Short" --threshold 200ms
```

### CI Matrix Partitioning

```bash
# Partition tests across CI jobs based on timing data
echo -n "matrix=" >> $GITHUB_OUTPUT
go list ./... | gotestsum tool matrix --timing-files ./*.log --partitions 4 >> $GITHUB_OUTPUT
```

## Post-Run Commands

```bash
# Desktop notifications
go install gotest.tools/gotestsum/contrib/notify@latest
gotestsum --post-run-command notify

# Print slowest tests after run
gotestsum --jsonfile tmp.json \
  --post-run-command "bash -c 'gotestsum tool slowest --num 10 --jsonfile tmp.json'"
```

Post-run environment variables:
- `GOTESTSUM_ELAPSED` - test run time
- `TESTS_TOTAL`, `TESTS_FAILED`, `TESTS_SKIPPED`, `TESTS_ERRORS`

## All CLI Flags

```
--format, -f string          Output format (default "pkgname")
--format-hide-empty-pkg      Hide empty packages
--format-icons string        Icon set
--raw-command                Don't prepend 'go test -json'
--no-color                   Disable color (auto-detected in CI)
--max-fails int              Stop after N failures
--jsonfile string            Write all TestEvents to file
--jsonfile-timing-events     Write only pass/skip/fail events
--junitfile string           Write JUnit XML
--junitfile-testsuite-name   Name format: full|relative|short
--junitfile-testcase-classname  Classname format: full|relative|short
--junitfile-project-name     Project name in XML
--junitfile-hide-empty-pkg   Omit empty packages in XML
--junitfile-hide-skipped-tests  Omit skipped tests in XML
--hide-summary string        Hide: skipped,failed,errors,output,all
--rerun-fails int            Rerun failed tests (default max 2)
--rerun-fails-max-failures   Skip rerun if initial failures > N (default 10)
--rerun-fails-run-root-test  Rerun root test case for subtest failures
--rerun-fails-abort-on-data-race  Stop rerun on data race
--watch                      Watch .go files and rerun
--watch-chdir                cd to modified file's dir
--watch-clear                Clear screen on rerun
--packages list              Space-separated package list
--post-run-command command   Run after tests complete
--debug                      Enable debug logging
--version                    Show version
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `GOTESTSUM_FORMAT` | Default output format |
| `GOTESTSUM_FORMAT_ICONS` | Icon set |
| `GOTESTSUM_JUNITFILE` | JUnit output path |
| `GOTESTSUM_JUNITFILE_PROJECT_NAME` | Project name in JUnit |
| `GOTESTSUM_JSONFILE` | JSON output path |
| `TEST_DIRECTORY` | Default test directory (instead of `./...`) |

## Justfile Recipes

```just
# Run all tests
test:
    gotestsum --format testname -- -race ./...

# Tests with coverage
test-cov:
    gotestsum --format testname -- -race -coverprofile=cover.out -covermode=atomic ./...
    go tool cover -func=cover.out

# CI output with JUnit XML
test-ci:
    gotestsum --format github-actions \
      --junitfile unit-tests.xml \
      --junitfile-hide-empty-pkg \
      -- -race -count=1 ./...

# Watch mode
test-watch:
    gotestsum --watch --watch-clear --format testname

# Rerun flaky tests
test-flaky:
    gotestsum --format testname \
      --rerun-fails=3 \
      --rerun-fails-max-failures=5 \
      --packages="./..." -- -count=1
```

## Recent Changes

| Version | Date | Key Changes |
|---------|------|-------------|
| v1.13.0 | Sep 2025 | `--watch-clear` flag, Go test attributes support (Go 1.24+) |
| v1.12.3 | Jun 2025 | `--rerun-fails-abort-on-data-race` flag |
| v1.12.2 | May 2025 | `--junitfile-hide-skipped-tests` flag |
| v1.12.1 | Mar 2025 | Go 1.24 compatibility, JUnit `skipped` attribute |
| v1.12.0 | May 2024 | `--format-icons` flag with Nerd Fonts |
