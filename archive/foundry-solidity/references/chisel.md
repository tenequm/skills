# Chisel REPL

Interactive Solidity REPL for quick experimentation.

## Starting Chisel

```bash
# Basic REPL
chisel

# With fork
chisel --fork-url https://eth-mainnet.g.alchemy.com/v2/KEY

# Specific block
chisel --fork-url $RPC_URL --fork-block-number 18000000
```

## Basic Usage

```
➜ uint256 x = 42
➜ x * 2
Type: uint256
├ Hex: 0x54
├ Hex (full word): 0x0000000000000000000000000000000000000000000000000000000000000054
└ Decimal: 84

➜ address alice = address(0x1234)
➜ alice.balance
Type: uint256
└ Decimal: 0
```

## Commands

| Command | Description |
|---------|-------------|
| `!help` | Show all commands |
| `!clear` | Clear session state |
| `!source` | Show generated source |
| `!rawstack` | Show raw stack output |
| `!edit` | Open in editor |
| `!export` | Export session to script |

## Session Management

```bash
# List saved sessions
chisel list

# Load session
chisel load my-session

# Save current session (in REPL)
!save my-session

# Clear cache
chisel clear-cache
```

## Working with Contracts

```
➜ interface IERC20 {
    function balanceOf(address) external view returns (uint256);
}

➜ IERC20 usdc = IERC20(0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48)

➜ usdc.balanceOf(0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503)
Type: uint256
└ Decimal: 1234567890
```

## Math Testing

Quick calculations without deploying:

```
➜ uint256 a = 1000000
➜ uint256 b = 3
➜ a / b
Type: uint256
└ Decimal: 333333

➜ (a * 1e18) / b
Type: uint256
└ Decimal: 333333333333333333333333
```

## Hash Functions

```
➜ keccak256("hello")
Type: bytes32
└ 0x1c8aff950685c2ed4bc3174f3472287b56d9517b9c948127319a09a7a36deac8

➜ keccak256(abi.encode(uint256(1), address(0x1234)))
```

## ABI Encoding

```
➜ abi.encode(uint256(42), address(0x1234))
➜ abi.encodePacked("hello", "world")
➜ abi.encodeWithSelector(bytes4(0x12345678), 100)
```

## Use Cases

1. **Quick math**: Test calculations before implementing
2. **ABI encoding**: Debug encoding issues
3. **Hash verification**: Check keccak256 outputs
4. **Contract interaction**: Test calls on fork
5. **Solidity syntax**: Experiment with new features

## Configuration

Chisel inherits project settings from `foundry.toml`:

```toml
[profile.default]
solc = "0.8.30"
evm_version = "prague"
```

Run chisel from project root to use these settings.
