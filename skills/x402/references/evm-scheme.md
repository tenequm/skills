# EVM Scheme Reference

## Schemes Overview

| Scheme | Description |
|--------|-------------|
| **exact** | Transfers a fixed amount; facilitator pays gas, client controls fund flow via signatures |
| **upto** | Usage-based; client authorizes a max, facilitator settles actual amount consumed |

Both schemes use Permit2 as their foundation. The `exact` scheme additionally supports EIP-3009 for compatible tokens.

## Asset Transfer Methods (Exact Scheme)

| Method | Use Case | Recommendation |
|--------|----------|----------------|
| **EIP-3009** | Tokens with native `transferWithAuthorization` (e.g., USDC) | Recommended (simplest, truly gasless) |
| **Permit2** | Any ERC-20 token | Universal fallback |
| **ERC-7710** | Smart accounts with delegation support | Smart account option |

If no `assetTransferMethod` is specified in payload `extra`, implementations prioritize `eip3009` first, then `permit2`.

## Proxy Contracts

Both schemes use deterministic CREATE2-deployed proxy contracts:

| Contract | Address | Purpose |
|----------|---------|---------|
| `x402ExactPermit2Proxy` | `0x402085c248EeA27D92E8b30b2C58ed07f9E20001` | Exact-amount Permit2 settlement |
| `x402UptoPermit2Proxy` | `0x402039b3d6E6BEC5A02c2C9fd937ac17A6940002` | Variable-amount Permit2 settlement |
| Permit2 (canonical) | `0x000000000022D473030F116dDEE9F6B43aC78BA3` | Uniswap Permit2 |
| Multicall3 | `0xcA11bde05977b3631167028862bE2a173976CA11` | Batched reads |

Both proxy contracts inherit `x402BasePermit2Proxy` which provides shared logic: reentrancy guard, `_settle()` internal, `_executePermit()` for EIP-2612, and common error types (`InvalidAmount`, `InvalidDestination`, `InvalidOwner`, `PaymentTooEarly`, `Permit2612AmountMismatch`).

### Exact Proxy Witness

```solidity
struct Witness { address to; uint256 validAfter; }
```

Always transfers the exact `permit.permitted.amount`.

### Upto Proxy Witness

```solidity
struct Witness { address to; address facilitator; uint256 validAfter; }
```

Adds `facilitator` field - only `msg.sender == witness.facilitator` can settle. Settles for any `amount <= permit.permitted.amount`.

## Method 1: EIP-3009 (Exact Only)

Uses `transferWithAuthorization` directly on compatible token contracts (like USDC).

### EIP-712 Authorization Types

```javascript
const authorizationTypes = {
  TransferWithAuthorization: [
    { name: "from", type: "address" },
    { name: "to", type: "address" },
    { name: "value", type: "uint256" },
    { name: "validAfter", type: "uint256" },
    { name: "validBefore", type: "uint256" },
    { name: "nonce", type: "bytes32" },
  ],
};
```

### EIP-3009 Verification

1. Verify EIP-712 signature recovers to `authorization.from` (supports EOA, EIP-1271 smart wallets, ERC-6492 counterfactual)
2. Verify payer has sufficient token balance
3. Verify `authorization.value` exactly matches required amount
4. Verify `validBefore > now + 6s` and `validAfter <= now`
5. Verify recipient and token/network match requirements
6. Simulate `transferWithAuthorization` on-chain

## Method 2: Permit2 (Both Exact and Upto)

Uses `permitWitnessTransferFrom` from the canonical Permit2 contract combined with `x402Permit2Proxy`.

### One-Time Setup (Three Options)

1. **Direct approval** - user submits `approve(Permit2, MaxUint256)` transaction
2. **EIP-2612 permit** (extension `eip2612GasSponsoring`) - gasless off-chain signature; facilitator calls `settleWithPermit()`
3. **ERC-20 approval gas sponsoring** (extension `erc20ApprovalGasSponsoring`) - client signs (not broadcasts) an `approve()` tx; facilitator broadcasts it atomically before settling

### Permit2 EIP-712 Types

```javascript
const permit2WitnessTypes = {
  PermitWitnessTransferFrom: [
    { name: "permitted", type: "TokenPermissions" },
    { name: "spender", type: "address" },
    { name: "nonce", type: "uint256" },
    { name: "deadline", type: "uint256" },
    { name: "witness", type: "Witness" },
  ],
  TokenPermissions: [
    { name: "token", type: "address" },
    { name: "amount", type: "uint256" },
  ],
  Witness: [
    { name: "to", type: "address" },
    { name: "validAfter", type: "uint256" },
  ],  // Exact scheme; Upto adds { name: "facilitator", type: "address" }
};
```

The `spender` is the `x402Permit2Proxy` contract (not the facilitator), which enforces funds go only to `witness.to`.

### Permit2 Verification (All Paths)

1. Verify `spender` is the correct `x402Permit2Proxy` address
2. Verify `witness.to` matches `requirements.payTo`
3. Verify `deadline > now + 6s` and `witness.validAfter <= now`
4. Verify `permitted.amount` matches (exact) or covers (upto) required amount
5. Verify `permitted.token` matches requirements
6. Verify EIP-712 signature (EOA, EIP-1271, or deployed smart contract fallthrough to simulation)
7. Simulation branch:
   - **Standard**: simulate `x402Permit2Proxy.settle()`
   - **EIP-2612 extension**: validate permit fields, simulate `settleWithPermit()`
   - **ERC-20 approval extension**: validate signed tx, simulate bundle

### Permit2 Settlement (Three Paths)

1. **EIP-2612 path** - calls `settleWithPermit(permit2612, permit, owner, witness, signature)` atomically
2. **ERC-20 approval path** - delegates to `extensionSigner.sendTransactions([signedApproveTx, { to: proxy, data: settleCalldata }])`
3. **Standard path** - calls `settle(permit, owner, witness, signature)` directly

## Multicall3 Batched Reads

All SDKs use Multicall3 (`tryAggregate`) to batch diagnostic reads in a single RPC round-trip. Used for: checking proxy deployment, token balance, Permit2 allowance, ETH balance for gas.

```typescript
import { multicall, MULTICALL3_ADDRESS } from "@x402/evm";
const results = await multicall(signer.readContract.bind(signer), calls);
```

**Go**: `evm.Multicall(ctx, signer, calls)` - same semantics.

## Universal Signature Verification (Go)

`VerifyUniversalSignature()` handles:
1. Parse ERC-6492 wrapper if present
2. If 65-byte signature + no factory: try EOA ECDSA recovery (optimization)
3. Otherwise: `GetCode` to check deployment
4. Undeployed + has ERC-6492 factory + `allowUndeployed`: return false but preserve deployment info
5. Deployed: EIP-1271 verification

## Extensions

### EIP-2612 Gas Sponsoring

Extension key: `eip2612GasSponsoring`. Client signs an EIP-2612 `permit(owner, Permit2, amount, deadline, v, r, s)` off-chain. Facilitator atomically executes it via `settleWithPermit()`.

### ERC-20 Approval Gas Sponsoring

Extension key: `erc20ApprovalGasSponsoring`. Fallback for tokens without EIP-2612. Client signs (not broadcasts) a raw `approve(Permit2, MaxUint256)` transaction. Facilitator broadcasts it before settling.

## Default Asset Resolution

When a server uses price string syntax (`"$0.001"`), the SDK resolves to the chain's default stablecoin:

| Network | Token | Address | Decimals | Transfer Method | EIP-2612 |
|---------|-------|---------|----------|-----------------|----------|
| Base Sepolia (`eip155:84532`) | USDC | `0x036CbD53842c5426634e7929541eC2318f3dCF7e` | 6 | EIP-3009 | - |
| Base Mainnet (`eip155:8453`) | USD Coin | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` | 6 | EIP-3009 | - |
| MegaETH (`eip155:4326`) | MegaUSD | `0xFAfDdbb3FC7688494971a79cc65DCa3EF82079E7` | 18 | Permit2 | Yes |
| Monad (`eip155:143`) | USD Coin | `0x754704Bc059F8C67012fEd69BC8A327a5aafb603` | 6 | EIP-3009 | - |

### Custom Tokens with registerMoneyParser

**TypeScript (Server):**
```typescript
import { ExactEvmScheme } from "@x402/evm/exact/server";
const server = new ExactEvmScheme();
server.registerMoneyParser(async (amount, network) => {
  if (network === "eip155:8453") {
    return {
      amount: (amount * 1e18).toString(),
      asset: "0xYourTokenAddress",
      extra: { assetTransferMethod: "permit2" },
    };
  }
  return null;
});
```

**Go:**
```go
evmScheme := evm.NewExactEvmScheme().RegisterMoneyParser(
    func(amount float64, network x402.Network) (*x402.AssetAmount, error) {
        return &x402.AssetAmount{
            Amount: fmt.Sprintf("%.0f", amount*1e18),
            Asset:  "0xYourTokenAddress",
            Extra:  map[string]interface{}{"assetTransferMethod": "permit2"},
        }, nil
    },
)
```

## Client RPC Configuration

```typescript
// Single RPC config
new ExactEvmScheme(signer, { rpcUrl: "https://..." });
// Per-chain config
new ExactEvmScheme(signer, { 8453: { rpcUrl: "..." }, 137: { rpcUrl: "..." } });
```

## Signer Types

### ClientEvmSigner

Required: `address`, `signTypedData()`
Optional (for extensions): `readContract()`, `signTransaction()`, `getTransactionCount()`, `estimateFeesPerGas()`

### FacilitatorEvmSigner

Required: `getAddresses()`, `readContract()`, `verifyTypedData()`, `writeContract()`, `sendTransaction()`, `waitForTransactionReceipt()`, `getCode()`

Supports multiple addresses for load balancing and key rotation.

## SDK Support

| SDK | Exact EIP-3009 | Exact Permit2 | Upto |
|-----|---------------|---------------|------|
| TypeScript (`@x402/evm`) | Full | Full (+ EIP-2612, ERC-20 approval extensions) | Full |
| Go | Full | Full (+ ERC-20 approval) | - |
| Python | Full | Full | - |
