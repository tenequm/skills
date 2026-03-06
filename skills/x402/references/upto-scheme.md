# Upto Scheme Reference

> **Status: Spec finalized, not yet production-ready.** The upto scheme spec was merged in March 2026. The `x402UptoPermit2Proxy` contract is deployed, but SDK client/server/facilitator implementations are still in progress and no facilitators support it yet. Use the `exact` scheme for production workloads. This reference documents the spec for awareness and early adoption preparation.

The `upto` scheme enables usage-based payments where the client authorizes a **maximum amount** and the server settles for the **actual amount consumed**. Ideal for LLM token generation, bandwidth metering, time-based API access, and dynamic compute pricing.

## Key Differences from Exact Scheme

| Property | Exact | Upto |
|----------|-------|------|
| Amount | Fixed, known upfront | Variable, determined at settlement |
| EIP-3009 | Supported (recommended) | NOT supported |
| Permit2 | Fallback | Required (only method) |
| Settlement amount | Must equal authorized amount | Must be <= authorized maximum |
| Zero settlement | Not applicable | Allowed (no charge, no tx needed) |

## Core Properties

1. **Single-Use Authorization** - each authorization settled at most once. After settlement (regardless of amount), the authorization is consumed and cannot be reused. Enforced via Permit2's nonce mechanism.

2. **Time-Bound Authorization** - `validAfter` (not valid before) and `deadline` (expires after). Enforced via Permit2's deadline + witness validAfter.

3. **Recipient Binding** - authorization cryptographically binds recipient address via Permit2 witness pattern (`witness.to`). Prevents facilitator from redirecting funds.

4. **Maximum Amount Enforcement** - settled amount MUST be <= authorized maximum. Settled amount MAY be 0 (no charge if no usage).

5. **Phase-Dependent `amount` Semantics** - at **verification** time, `amount` in PaymentRequirements = maximum the client authorizes. At **settlement** time, `amount` = actual amount to settle (must be <= maximum). This reuses the existing PaymentRequirements type for both phases.

## EVM Implementation

### Why Permit2 Only

EIP-3009 `transferWithAuthorization` requires the exact amount to be known at signature time - the signed `value` is the transfer amount. Upto needs variable settlement, so only Permit2's `permitWitnessTransferFrom` works, where `permitted.amount` is the maximum and `requestedAmount` at settlement can be less.

### One-Time Setup

Clients must approve the Permit2 contract. Three options:
- **Option A**: Direct user approval (`ERC20.approve(Permit2, amount)`)
- **Option B**: Sponsored ERC20 approval (extension) - facilitator pays gas
- **Option C**: EIP-2612 permit (extension) - off-chain signature if token supports it

### PaymentPayload Structure

```json
{
  "x402Version": 2,
  "accepted": {
    "scheme": "upto",
    "network": "eip155:84532",
    "amount": "5000000",
    "asset": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    "payTo": "0x209693Bc6afc0C5328bA36FaF03C514EF312287C",
    "maxTimeoutSeconds": 60
  },
  "payload": {
    "signature": "0x2d6a7588...",
    "permit2Authorization": {
      "permitted": {
        "token": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        "amount": "5000000"
      },
      "from": "0x857b06519E91e3A54538791bDbb0E22373e36b66",
      "spender": "0x402039b3d6E6BEC5A02c2C9fd937ac17A6940002",
      "nonce": "0xf3746613c2d920b5fdabc0856f2aeb2d4f88ee6037b8cc5d04a71a4462f13480",
      "deadline": "1740672154",
      "witness": {
        "to": "0x209693Bc6afc0C5328bA36FaF03C514EF312287C",
        "validAfter": "1740672089"
      }
    }
  }
}
```

The `spender` is the `x402UptoPermit2Proxy` contract at `0x402039b3d6E6BEC5A02c2C9fd937ac17A6940002` (same address across all EVM chains via CREATE2).

### Verification Steps

1. Verify `payload.signature` is valid and recovers to `permit2Authorization.from`
2. Verify client has enabled Permit2 approval (`ERC20.allowance >= amount`)
3. Verify client has sufficient token balance
4. Verify `permit2Authorization.permitted.amount` equals `amount` from requirements
5. Verify `deadline` not expired and `witness.validAfter` is active
6. Verify token and network match requirements
7. Simulate settlement with full amount (worst case)

### Settlement

Settlement amount rules:
- MUST be <= authorized maximum
- MAY be 0 (no charge if no usage)
- Determined by resource server (not client)

Settlement process:
- **Standard**: Call `x402UptoPermit2Proxy.settle(permit, actualAmount, owner, witness, signature)` where `actualAmount <= permit.permitted.amount`
- **With EIP-2612**: Call `x402UptoPermit2Proxy.settleWithPermit(permit2612, permit, actualAmount, owner, witness, signature)`
- **Zero settlement**: No on-chain transaction required. Authorization expires naturally.

### SettlementResponse for Upto

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `success` | boolean | Yes | Whether settlement succeeded |
| `transaction` | string | Yes | Tx hash (empty string if $0 settlement) |
| `network` | string | Yes | CAIP-2 network ID |
| `payer` | string | No | Payer's wallet address |
| `amount` | string | Yes | Actual amount charged (may be "0") |

### x402UptoPermit2Proxy Contract

```solidity
contract x402UptoPermit2Proxy is x402BasePermit2Proxy {
    error AmountExceedsPermitted();

    function settle(
        ISignatureTransfer.PermitTransferFrom calldata permit,
        uint256 amount,
        address owner,
        Witness calldata witness,
        bytes calldata signature
    ) external nonReentrant {
        if (amount > permit.permitted.amount) revert AmountExceedsPermitted();
        _settle(permit, amount, owner, witness, signature);
    }

    function settleWithPermit(
        EIP2612Permit calldata permit2612,
        ISignatureTransfer.PermitTransferFrom calldata permit,
        uint256 amount,
        address owner,
        Witness calldata witness,
        bytes calldata signature
    ) external nonReentrant {
        if (amount > permit.permitted.amount) revert AmountExceedsPermitted();
        _executePermit(permit.permitted.token, owner, permit2612, permit.permitted.amount);
        _settle(permit, amount, owner, witness, signature);
    }
}
```

Witness struct (from base contract):
```solidity
struct Witness {
    address to;           // Destination address (immutable once signed)
    address facilitator;  // Must equal msg.sender at settlement
    uint256 validAfter;   // Earliest valid timestamp
}
```

### EIP-712 Types

```typescript
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
  ],
};
```

### Error Codes

| Code | Description |
|------|-------------|
| `invalid_upto_evm_payload_settlement_exceeds_amount` | Attempted to settle for more than authorized maximum |
| `AmountExceedsPermitted` | Contract-level revert when `amount > permit.permitted.amount` |

## SDK Support

| SDK | Upto Scheme Support |
|-----|:---:|
| TypeScript (`@x402/evm`) | Constants and proxy ABI defined |
| Go | Constants defined (`x402UptoPermit2ProxyAddress`) |
| Python | Not yet implemented |

The upto scheme spec is finalized. SDK client/server/facilitator implementations are in progress. The `x402UptoPermit2Proxy` contract is deployed at `0x402039b3d6E6BEC5A02c2C9fd937ac17A6940002`.
