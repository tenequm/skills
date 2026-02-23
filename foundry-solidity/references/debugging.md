# Debugging Workflows

Foundry debugging tools for finding and fixing smart contract issues.

## Verbosity Levels

```bash
forge test                 # Summary only
forge test -v              # Show passing test names
forge test -vv             # Print logs for all tests
forge test -vvv            # Traces for failing tests
forge test -vvvv           # Traces for all tests + setup
forge test -vvvvv          # All traces + storage changes
```

**Use:**
- `-vv`: Quick check of console.log output
- `-vvv`: First step when test fails
- `-vvvv`: Full debugging with all traces

## Understanding Traces

### Trace Format

```
[24661] TestContract::testFunction()
├─ [2262] Target::read()
│   └─ ← 0
├─ [20398] Target::write(42)
│   └─ ← ()
└─ ← ()
```

- `[gas]`: Gas consumed by call and nested calls
- **Green**: Successful calls
- **Red**: Reverting calls
- **Blue**: Cheatcode calls
- **Cyan**: Emitted logs
- **Yellow**: Contract deployments

### Common Trace Errors

| Error | Meaning |
|-------|---------|
| `OOG` | Out of gas |
| `Revert` | Transaction reverted |
| `InvalidFEOpcode` | Unknown opcode (0xFE) |
| `NotActivated` | EVM feature not available |

## Console Logging

### Basic Usage

```solidity
import {console} from "forge-std/console.sol";

function test_Debug() public {
    console.log("Value:", value);
    console.log("Address:", msg.sender);
    console.log("Balance:", address(this).balance);
}
```

### Format Specifiers

```solidity
console.log("String: %s", "hello");
console.log("Decimal: %d", 123);
console.log("Hex: %x", 255);

// Multiple arguments (up to 4)
console.log("From %s to %s: %d", from, to, amount);

// Type-specific
console.logBytes32(hash);
console.logAddress(token);
console.logBool(success);
```

### Debugging Pattern

```solidity
function test_Transfer() public {
    console.log("=== Transfer ===");
    console.log("From:", from);
    console.log("To:", to);
    console.log("Amount:", amount);

    token.transfer(to, amount);

    console.log("Balance after:", token.balanceOf(to));
}
```

## Breakpoints

Set breakpoints in code, jump to them in debugger:

```solidity
function test_Complex() public {
    vm.breakpoint("start");
    uint256 x = calculate();

    vm.breakpoint("middle");
    process(x);

    vm.breakpoint("end");
}
```

In debugger, press `'` + letter to jump (e.g., `'a` for first breakpoint).

## Interactive Debugger

### Starting

```bash
# Debug specific test
forge test --debug --match-test "test_Function"

# Debug script
forge script script/Deploy.s.sol --debug

# Debug transaction from chain
cast run --debug 0x123...
```

### Debugger Layout

Four quadrants:
1. **Top-left**: EVM opcodes (current instruction highlighted)
2. **Top-right**: Stack state
3. **Bottom-left**: Solidity source code
4. **Bottom-right**: Memory contents

### Navigation Keys

**Movement:**
- `j/k`: Step forward/backward
- `g/G`: Go to beginning/end
- `c/C`: Next/previous CALL instruction
- `'a-z`: Jump to breakpoint

**Display:**
- `t`: Toggle stack labels
- `m`: Toggle memory as UTF8
- `h`: Help
- `q`: Quit

### Debugging Workflow

```bash
# 1. Test fails
forge test --match-test "test_Deposit"

# 2. See what failed
forge test -vvv --match-test "test_Deposit"

# 3. Add console.log for quick debugging
# OR use interactive debugger
forge test --debug --match-test "test_Deposit"

# 4. Step through with j/k, watch stack with t
```

## Gas Profiling

### Gas Reports

```bash
forge test --gas-report
```

Output:
```
│ Function    │ min   │ avg   │ median │ max   │ calls │
├─────────────┼───────┼───────┼────────┼───────┼───────┤
│ transfer    │ 2900  │ 5234  │ 5200   │ 8901  │ 145   │
│ balanceOf   │ 596   │ 596   │ 596    │ 596   │ 234   │
```

### Gas Snapshots

```bash
forge snapshot              # Create snapshot
forge snapshot --diff       # Compare to previous
forge snapshot --check      # Fail if changed
```

### Inline Measurement

```solidity
function test_GasUsage() public {
    uint256 gasBefore = gasleft();

    contract.operation();

    uint256 gasUsed = gasBefore - gasleft();
    console.log("Gas used:", gasUsed);
}
```

## Common Error Patterns

### Assertion Failure

```
AssertionError: a == b
  Expected: 1000000
  Actual: 500000
```

**Debug:** Run with `-vvv` to trace calculation.

### Revert Without Message

```
Error: reverted
```

**Debug:**
1. Run with `-vvvv` for full trace
2. Find red (reverting) call in trace
3. Add console.log before suspect operations

### Out of Gas

```
Error: OutOfGas
```

**Fix:** Reduce loop iterations or split into batches.

### Custom Error

```solidity
vm.expectRevert(abi.encodeWithSelector(
    InsufficientBalance.selector,
    1000,  // have
    2000   // need
));
token.transfer(recipient, 2000);
```

## Best Practices

1. **Start simple**: Use console.log before --debug
2. **Isolate tests**: Test one thing per test function
3. **Use descriptive logs**: Log state at each step
4. **Check assumptions**: Verify preconditions
5. **Save traces**: `forge test -vvvv > trace.txt`
