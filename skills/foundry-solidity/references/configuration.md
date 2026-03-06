# Foundry Configuration Reference

Complete reference for `foundry.toml` configuration options.

## Basic Structure

```toml
# Default profile
[profile.default]
src = "src"
out = "out"
libs = ["lib"]

# Additional profiles
[profile.ci]
# CI-specific overrides

[profile.production]
# Production build settings
```

## Project Structure

```toml
[profile.default]
# Source directories
src = "src"                    # Contract sources
test = "test"                  # Test files
script = "script"              # Deployment scripts
out = "out"                    # Compiled output
libs = ["lib"]                 # Dependency directories
cache_path = "cache"           # Compilation cache

# Remappings (alternative to remappings.txt)
remappings = [
    "@openzeppelin/=lib/openzeppelin-contracts/",
    "@solmate/=lib/solmate/src/",
    "forge-std/=lib/forge-std/src/"
]
```

## Compiler Settings

```toml
[profile.default]
# Solidity version
solc = "0.8.30"                # Exact version
# solc = "^0.8.0"              # Version range
# auto_detect_solc = true      # Auto-detect from pragmas

# EVM version
evm_version = "prague"         # Target EVM version
# Options: homestead, tangerineWhistle, spuriousDragon, byzantium,
#          constantinople, petersburg, istanbul, berlin, london,
#          paris, shanghai, cancun, prague

# Optimizer
optimizer = true
optimizer_runs = 200           # Optimize for ~200 runs
via_ir = false                 # Use IR-based compilation

# Output
extra_output = ["abi", "evm.bytecode", "storageLayout"]
extra_output_files = ["abi", "storageLayout"]

# Bytecode hash
bytecode_hash = "ipfs"         # ipfs, bzzr1, or none
cbor_metadata = true           # Include CBOR metadata
```

## Testing Configuration

```toml
[profile.default]
# Verbosity (0-5)
verbosity = 2

# Gas settings
gas_limit = 9223372036854775807
gas_price = 0
block_base_fee_per_gas = 0
tx_origin = "0x0000000000000000000000000000000000000001"

# Block settings
block_coinbase = "0x0000000000000000000000000000000000000000"
block_timestamp = 1
block_number = 1
block_difficulty = 0
block_gas_limit = 30000000
chain_id = 31337

# Sender
sender = "0x1804c8AB1F12E6bbf3894d4083f33e07309d1f38"

# Memory limit (bytes)
memory_limit = 33554432        # 32 MB

# Show gas reports
gas_reports = ["*"]            # All contracts
# gas_reports = ["MyContract", "OtherContract"]
gas_reports_ignore = []

# Fail test if gas exceeds this limit
# gas_report_fail_on_increase = true
```

## Fuzz Testing

```toml
[profile.default]
# Number of fuzz runs
fuzz.runs = 256

# Seed for deterministic fuzzing
fuzz.seed = "0x1234"

# Maximum test rejects before failing
fuzz.max_test_rejects = 65536

# Dictionary weight (how much to use discovered values)
fuzz.dictionary_weight = 40

# Include push bytes
fuzz.include_push_bytes = true

# Include storage
fuzz.include_storage = true

# Show logs
fuzz.show_logs = false
```

## Invariant Testing

```toml
[profile.default]
# Number of runs (sequences)
invariant.runs = 256

# Depth (calls per run)
invariant.depth = 15

# Fail on revert
invariant.fail_on_revert = false

# Call override
invariant.call_override = false

# Dictionary weight
invariant.dictionary_weight = 80

# Include storage
invariant.include_storage = true

# Include push bytes
invariant.include_push_bytes = true

# Shrink run limit
invariant.shrink_run_limit = 5000

# Max fuzz dictionary addresses
invariant.max_fuzz_dictionary_addresses = 15

# Max fuzz dictionary values
invariant.max_fuzz_dictionary_values = 10

# Gas limit
invariant.gas_limit = 9223372036854775807
```

## Fork Testing

```toml
[profile.default]
# Default fork URL
# eth_rpc_url = "https://eth-mainnet.alchemyapi.io/v2/..."

# Fork block number
# fork_block_number = 18000000

# Fork retry backoff
fork_retry_backoff = "0"

# RPC storage caching
rpc_storage_caching = {
    chains = "all",
    endpoints = "all"
}

# No storage caching
no_storage_caching = false
```

## RPC Endpoints

```toml
[rpc_endpoints]
mainnet = "https://eth-mainnet.g.alchemy.com/v2/${ALCHEMY_KEY}"
sepolia = "https://eth-sepolia.g.alchemy.com/v2/${ALCHEMY_KEY}"
arbitrum = "https://arb-mainnet.g.alchemy.com/v2/${ALCHEMY_KEY}"
optimism = "https://opt-mainnet.g.alchemy.com/v2/${ALCHEMY_KEY}"
polygon = "https://polygon-mainnet.g.alchemy.com/v2/${ALCHEMY_KEY}"
base = "https://base-mainnet.g.alchemy.com/v2/${ALCHEMY_KEY}"

# Local
localhost = "http://localhost:8545"
anvil = "http://127.0.0.1:8545"

# Environment variable interpolation
custom = "${CUSTOM_RPC_URL}"
```

## Etherscan Configuration

```toml
[etherscan]
mainnet = { key = "${ETHERSCAN_API_KEY}" }
sepolia = { key = "${ETHERSCAN_API_KEY}" }
arbitrum = { key = "${ARBISCAN_API_KEY}" }
optimism = { key = "${OPTIMISTIC_ETHERSCAN_API_KEY}" }
polygon = { key = "${POLYGONSCAN_API_KEY}" }
base = { key = "${BASESCAN_API_KEY}" }

# Custom chain
custom = { key = "${CUSTOM_API_KEY}", url = "https://api.custom-explorer.com/api" }
```

## Formatting

```toml
[fmt]
# Line length
line_length = 120

# Tab width
tab_width = 4

# Bracket spacing
bracket_spacing = false

# Int types (preserve, short, long)
int_types = "long"

# Multiline function header
multiline_func_header = "attributes_first"

# Quote style
quote_style = "double"

# Number underscore (preserve, thousands, none)
number_underscore = "preserve"

# Hex underscore
hex_underscore = "remove"

# Single line statement blocks
single_line_statement_blocks = "preserve"

# Override spacing
override_spacing = false

# Wrap comments
wrap_comments = false

# Ignore files
ignore = ["src/external/**"]

# Contract new lines
contract_new_lines = false

# Sort imports
sort_imports = false
```

## Documentation

```toml
[doc]
# Output directory
out = "docs"

# Repository link
repository = "https://github.com/user/repo"

# Ignore patterns
ignore = ["src/test/**"]
```

## Profiles

### Default Profile

```toml
[profile.default]
src = "src"
out = "out"
libs = ["lib"]
optimizer = true
optimizer_runs = 200
```

### CI Profile

```toml
[profile.ci]
fuzz.runs = 10000
invariant.runs = 1000
invariant.depth = 100
verbosity = 3
```

### Production Profile

```toml
[profile.production]
optimizer = true
optimizer_runs = 1000000
via_ir = true
bytecode_hash = "none"
cbor_metadata = false
```

### Gas Optimization Profile

```toml
[profile.gas]
optimizer = true
optimizer_runs = 1000000
gas_reports = ["*"]
```

### Fast Development Profile

```toml
[profile.fast]
optimizer = false
fuzz.runs = 100
invariant.runs = 50
no_match_test = "testFork_"
```

## Using Profiles

```bash
# Use default profile
forge build
forge test

# Use CI profile
FOUNDRY_PROFILE=ci forge test

# Use production profile
FOUNDRY_PROFILE=production forge build
```

## Environment Variables

```bash
# Override any config option
FOUNDRY_SRC=contracts forge build
FOUNDRY_OPTIMIZER=false forge build
FOUNDRY_OPTIMIZER_RUNS=1000000 forge build
FOUNDRY_EVM_VERSION=shanghai forge build

# Common overrides
FOUNDRY_PROFILE=ci              # Select profile
FOUNDRY_FUZZ_RUNS=10000         # Fuzz runs
FOUNDRY_INVARIANT_RUNS=1000     # Invariant runs
FOUNDRY_VERBOSITY=3             # Test verbosity
```

## Complete Example

```toml
# foundry.toml

[profile.default]
# Project
src = "src"
out = "out"
libs = ["lib"]
test = "test"
script = "script"

# Compiler
solc = "0.8.30"
evm_version = "prague"
optimizer = true
optimizer_runs = 200

# Testing
verbosity = 2
fuzz.runs = 256
fuzz.seed = "0x1234"
invariant.runs = 256
invariant.depth = 50

# Gas
gas_reports = ["*"]

# Output
extra_output = ["storageLayout"]

# Remappings
remappings = [
    "@openzeppelin/=lib/openzeppelin-contracts/contracts/",
    "forge-std/=lib/forge-std/src/"
]

[profile.ci]
fuzz.runs = 10000
fuzz.seed = "0xdeadbeef"
invariant.runs = 1000
invariant.depth = 100
verbosity = 3

[profile.production]
optimizer = true
optimizer_runs = 1000000
via_ir = true

[profile.local]
optimizer = false
fuzz.runs = 100

[rpc_endpoints]
mainnet = "${MAINNET_RPC_URL}"
sepolia = "${SEPOLIA_RPC_URL}"
arbitrum = "${ARBITRUM_RPC_URL}"
optimism = "${OPTIMISM_RPC_URL}"
base = "${BASE_RPC_URL}"
localhost = "http://127.0.0.1:8545"

[etherscan]
mainnet = { key = "${ETHERSCAN_API_KEY}" }
sepolia = { key = "${ETHERSCAN_API_KEY}" }
arbitrum = { key = "${ARBISCAN_API_KEY}" }
optimism = { key = "${OPTIMISTIC_ETHERSCAN_API_KEY}" }
base = { key = "${BASESCAN_API_KEY}" }

[fmt]
line_length = 120
tab_width = 4
bracket_spacing = false
int_types = "long"
multiline_func_header = "attributes_first"
quote_style = "double"
number_underscore = "thousands"
sort_imports = true
```
