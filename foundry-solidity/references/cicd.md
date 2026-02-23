# CI/CD Integration

GitHub Actions workflows for Foundry projects.

## Basic Workflow

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [main]
  pull_request:

env:
  FOUNDRY_PROFILE: ci

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive

      - name: Install Foundry
        uses: foundry-rs/foundry-toolchain@v1

      - name: Run tests
        run: forge test -vvv
```

## With Caching

```yaml
name: Test

on: [push, pull_request]

env:
  FOUNDRY_PROFILE: ci

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive

      - name: Install Foundry
        uses: foundry-rs/foundry-toolchain@v1
        with:
          cache: true

      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: |
            lib
            cache
            out
          key: ${{ runner.os }}-foundry-${{ hashFiles('**/foundry.toml') }}
          restore-keys: |
            ${{ runner.os }}-foundry-

      - name: Build
        run: forge build

      - name: Run tests
        run: forge test -vvv
```

## Full Pipeline

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

env:
  FOUNDRY_PROFILE: ci

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive

      - name: Install Foundry
        uses: foundry-rs/foundry-toolchain@v1
        with:
          cache: true

      - name: Build
        run: forge build --sizes

  test:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive

      - name: Install Foundry
        uses: foundry-rs/foundry-toolchain@v1
        with:
          cache: true

      - name: Run tests
        run: forge test -vvv

  coverage:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive

      - name: Install Foundry
        uses: foundry-rs/foundry-toolchain@v1
        with:
          cache: true

      - name: Generate coverage
        run: forge coverage --report lcov

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: lcov.info

  gas-report:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive

      - name: Install Foundry
        uses: foundry-rs/foundry-toolchain@v1
        with:
          cache: true

      - name: Gas snapshot
        run: forge snapshot --check --tolerance 5
```

## Fork Testing in CI

```yaml
jobs:
  fork-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive

      - name: Install Foundry
        uses: foundry-rs/foundry-toolchain@v1
        with:
          cache: true

      - name: Run fork tests
        run: forge test --match-test "testFork" -vvv
        env:
          MAINNET_RPC_URL: ${{ secrets.MAINNET_RPC_URL }}
```

## Gas Snapshot Tracking

### Check for regressions

```yaml
- name: Gas snapshot check
  run: |
    forge snapshot
    forge snapshot --diff .gas-snapshot
```

### Comment on PR

```yaml
- name: Compare gas
  run: forge snapshot --diff .gas-snapshot > gas-diff.txt

- name: Post gas diff
  uses: actions/github-script@v7
  with:
    script: |
      const fs = require('fs');
      const diff = fs.readFileSync('gas-diff.txt', 'utf8');
      if (diff.trim()) {
        github.rest.issues.createComment({
          issue_number: context.issue.number,
          owner: context.repo.owner,
          repo: context.repo.repo,
          body: '## Gas Changes\n```\n' + diff + '\n```'
        });
      }
```

## Deployment

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive

      - name: Install Foundry
        uses: foundry-rs/foundry-toolchain@v1

      - name: Deploy
        run: |
          forge script script/Deploy.s.sol \
            --rpc-url ${{ secrets.RPC_URL }} \
            --broadcast \
            --verify
        env:
          PRIVATE_KEY: ${{ secrets.DEPLOYER_PRIVATE_KEY }}
          ETHERSCAN_API_KEY: ${{ secrets.ETHERSCAN_API_KEY }}
```

## CI Profile

Configure higher fuzz runs for CI in `foundry.toml`:

```toml
[profile.default]
fuzz.runs = 256
invariant.runs = 256

[profile.ci]
fuzz.runs = 10000
invariant.runs = 1000
verbosity = 3
```

Use with `FOUNDRY_PROFILE=ci forge test`.

## Secrets Management

Required secrets for CI:
- `MAINNET_RPC_URL`: For fork testing
- `DEPLOYER_PRIVATE_KEY`: For deployment
- `ETHERSCAN_API_KEY`: For verification

**Never commit secrets to the repository.**

## Matrix Testing

Test across Solidity versions:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        solc: ["0.8.20", "0.8.25", "0.8.30"]
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive

      - name: Install Foundry
        uses: foundry-rs/foundry-toolchain@v1

      - name: Test with Solc ${{ matrix.solc }}
        run: forge test
        env:
          FOUNDRY_SOLC_VERSION: ${{ matrix.solc }}
```
