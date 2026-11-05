# Dependency Management

Managing dependencies in Foundry using git submodules and Soldeer.

## Git Submodules (Default)

### Installing Dependencies

```bash
# Install latest master
forge install vectorized/solady

# Install specific tag
forge install vectorized/solady@v0.0.265

# Install specific commit
forge install vectorized/solady@a5bb996e91aae5b0c068087af7594d92068b12f1

# No automatic commit (for CI)
forge install OpenZeppelin/openzeppelin-contracts --no-commit
```

Dependencies are cloned to `lib/[name]`.

### Remappings

Forge auto-generates remappings:

```bash
$ forge remappings
forge-std/=lib/forge-std/src/
solady/=lib/solady/src/
```

Use in imports:

```solidity
import {Test} from "forge-std/Test.sol";
import {ERC20} from "solady/tokens/ERC20.sol";
```

### Custom Remappings

Create `remappings.txt`:

```
@openzeppelin/=lib/openzeppelin-contracts/contracts/
@solmate/=lib/solmate/src/
forge-std/=lib/forge-std/src/
```

Or in `foundry.toml`:

```toml
[profile.default]
remappings = [
    "@openzeppelin/=lib/openzeppelin-contracts/contracts/",
    "@solmate/=lib/solmate/src/"
]
```

### Updating Dependencies

```bash
# Update specific dependency
forge update lib/solady

# Update all
forge update
```

### Removing Dependencies

```bash
forge remove solady
# or
forge remove lib/solady
```

## Soldeer (Modern Package Manager)

Soldeer provides npm-style dependency management with a central registry.

### Initialize

```bash
forge soldeer init
```

Creates `dependencies/` folder and configures `foundry.toml`.

### Installing Packages

```bash
# From registry (soldeer.xyz)
forge soldeer install @openzeppelin-contracts~5.0.2
forge soldeer install forge-std~1.8.1

# From URL
forge soldeer install @custom~1.0.0 --url https://example.com/lib.zip

# From git
forge soldeer install lib~1.0 --git https://github.com/org/lib.git --tag v1.0
```

Configuration in `foundry.toml`:

```toml
[profile.default]
libs = ["dependencies"]

[dependencies]
"@openzeppelin-contracts" = { version = "5.0.2" }
forge-std = { version = "1.8.1" }
```

### Updating

```bash
forge soldeer update
forge soldeer update --regenerate-remappings
```

### Removing

```bash
forge soldeer uninstall @openzeppelin-contracts
```

### Soldeer Config

```toml
[soldeer]
remappings_generate = true
remappings_version = true      # @lib-5.0.2 suffix
remappings_prefix = "@"        # @lib instead of lib
remappings_location = "txt"    # or "config"
recursive_deps = true          # Install sub-dependencies
```

## Comparison

| Feature | Git Submodules | Soldeer |
|---------|----------------|---------|
| Setup | Simple | Requires config |
| Version pinning | Commit hash | Semantic version |
| Central registry | No | Yes (soldeer.xyz) |
| Team sharing | .gitmodules | foundry.toml |
| Private repos | Full support | URL only |

## Best Practices

### Version Pinning

```bash
# Production: Use specific tag
forge install openzeppelin/openzeppelin-contracts@v5.0.0

# Development: Can use master
forge install vectorized/solady
```

### Handling Conflicts

When dependencies have conflicting versions, use remapping contexts:

```
# remappings.txt
lib/lib_1/:@openzeppelin/=lib/lib_1/node_modules/@openzeppelin/
lib/lib_2/:@openzeppelin/=lib/lib_2/node_modules/@openzeppelin/
```

### CI Configuration

```bash
# After clone, init submodules
git submodule update --init --recursive

# Or use --no-commit during install
forge install OpenZeppelin/openzeppelin-contracts --no-commit
```

### Hardhat Compatibility

```bash
# Enable node_modules support
forge install --hh
```

## Troubleshooting

**Submodule not found after clone:**
```bash
git submodule update --init --recursive
```

**Remapping not working:**
```bash
forge remappings > remappings.txt
```

**Soldeer package missing:**
Check [soldeer.xyz](https://soldeer.xyz) or publish your own.
