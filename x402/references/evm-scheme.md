# EVM Exact Scheme Reference

The `exact` scheme on EVM transfers a specific amount where the facilitator pays gas but the client controls fund flow via cryptographic signatures.

## Two Asset Transfer Methods

| Method | Use Case | Recommendation |
|--------|----------|----------------|
| **EIP-3009** | Tokens with native `transferWithAuthorization` (e.g., USDC) | Recommended (simplest, truly gasless) |
| **Permit2** | Tokens without EIP-3009 (any ERC-20) | Universal fallback |

If no `assetTransferMethod` is specified in payload `extra`, implementations prioritize `eip3009` first, then `permit2`.

## Method 1: EIP-3009

Uses `transferWithAuthorization` directly on compatible token contracts (like USDC).

### PaymentPayload Structure

```json
{
  "x402Version": 2,
  "resource": { "url": "...", "description": "...", "mimeType": "..." },
  "accepted": {
    "scheme": "exact",
    "network": "eip155:84532",
    "amount": "10000",
    "asset": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    "payTo": "0x209693Bc6afc0C5328bA36FaF03C514EF312287C",
    "maxTimeoutSeconds": 60,
    "extra": {
      "assetTransferMethod": "eip3009",
      "name": "USDC",
      "version": "2"
    }
  },
  "payload": {
    "signature": "0x2d6a7588d6acca505cbf0d9a4a227e0c52c6c34...",
    "authorization": {
      "from": "0x857b06519E91e3A54538791bDbb0E22373e66b66",
      "to": "0x209693Bc6afc0C5328bA36FaF03C514EF312287C",
      "value": "10000",
      "validAfter": "1740672089",
      "validBefore": "1740672154",
      "nonce": "0xf3746613c2d920b5fdabc0856f2aeb2d4f88ee6037b8cc5d04a71a4462f13480"
    }
  }
}
```

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

### Verification Steps

1. **Signature validation** - verify EIP-712 signature recovers to `authorization.from`
2. **Balance check** - confirm payer has sufficient token balance
3. **Amount validation** - payment amount **exactly matches** required amount (strict equality)
4. **Time window check** - authorization within valid time range
5. **Parameter matching** - authorization params match payment requirements
6. **Transaction simulation** - simulate `transferWithAuthorization` to ensure success

### Settlement

Facilitator calls `transferWithAuthorization` on the EIP-3009 contract with the `payload.signature` and `payload.authorization` parameters.

## Method 2: Permit2

Uses `permitWitnessTransferFrom` from the canonical Permit2 contract combined with `x402Permit2Proxy`.

### One-Time Setup

Clients must approve the Permit2 contract to spend tokens. Three options:

1. **Direct approval** - user submits standard `approve(Permit2)` transaction
2. **Sponsored ERC20 approval** (extension) - facilitator pays gas for approval
3. **EIP-2612 permit** (extension) - if token supports EIP-2612, user signs a permit

### PaymentPayload Structure

```json
{
  "x402Version": 2,
  "accepted": {
    "scheme": "exact",
    "network": "eip155:84532",
    "amount": "10000",
    "payTo": "0x209693Bc6afc0C5328bA36FaF03C514EF312287C",
    "maxTimeoutSeconds": 60,
    "asset": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    "extra": {
      "assetTransferMethod": "permit2",
      "name": "USDC",
      "version": "2"
    }
  },
  "payload": {
    "signature": "0x2d6a7588...",
    "permit2Authorization": {
      "permitted": {
        "token": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        "amount": "10000"
      },
      "from": "0x857b06519E91e3A54538791bDbb0E22373e36b66",
      "spender": "0xx402Permit2ProxyAddress",
      "nonce": "0xf3746613...",
      "deadline": "1740672154",
      "witness": {
        "to": "0x209693Bc6afc0C5328bA36FaF03C514EF312287C",
        "validAfter": "1740672089",
        "extra": {}
      }
    }
  }
}
```

The `spender` is the `x402Permit2Proxy` contract (not the facilitator), which enforces funds go only to `witness.to`.

### Permit2 Verification Steps

1. Verify `payload.signature` is valid and recovers to `permit2Authorization.from`
2. Verify client has enabled Permit2 approval (`ERC20.allowance(from, Permit2_Address) >= amount`)
3. Verify client has sufficient token balance
4. Verify `permit2Authorization.amount` exactly matches the required amount
5. Verify `deadline` not expired and `witness.validAfter` is active
6. Verify token and network match requirements
7. Simulate `x402Permit2Proxy.settle`

### x402Permit2Proxy Contract

```solidity
contract x402Permit2Proxy {
    ISignatureTransfer public immutable PERMIT2;

    string public constant WITNESS_TYPE_STRING =
        "Witness witness)Witness(bytes extra,address to,uint256 validAfter)TokenPermissions(address token,uint256 amount)";

    bytes32 public constant WITNESS_TYPEHASH =
        keccak256("Witness(bytes extra,address to,uint256 validAfter)");

    struct Witness {
        address to;
        uint256 validAfter;
        bytes extra;
    }

    function settle(
        ISignatureTransfer.PermitTransferFrom calldata permit,
        uint256 amount,
        address owner,
        Witness calldata witness,
        bytes calldata signature
    ) external {
        require(block.timestamp >= witness.validAfter, "Too early");
        require(amount <= permit.permitted.amount, "Amount higher than permitted");

        ISignatureTransfer.SignatureTransferDetails memory transferDetails =
            ISignatureTransfer.SignatureTransferDetails({
                to: witness.to,
                requestedAmount: amount
            });

        bytes32 witnessHash = keccak256(abi.encode(
            WITNESS_TYPEHASH,
            keccak256(witness.extra),
            witness.to,
            witness.validAfter
        ));

        PERMIT2.permitWitnessTransferFrom(
            permit, transferDetails, owner, witnessHash, WITNESS_TYPE_STRING, signature
        );
    }

    // Extension: EIP-2612 permit + settle
    function settleWith2612(
        EIP2612Permit calldata permit2612,
        uint256 amount,
        ISignatureTransfer.PermitTransferFrom calldata permit,
        address owner,
        Witness calldata witness,
        bytes calldata signature
    ) external {
        IERC20Permit(permit.permitted.token).permit(
            owner, address(PERMIT2), permit2612.value, permit2612.deadline,
            permit2612.v, permit2612.r, permit2612.s
        );
        _settleInternal(permit, amount, owner, witness, signature);
    }
}
```

The `x402Permit2Proxy` is deployed to the same address across all EVM chains using `CREATE2`.

## Default Asset Resolution

When a server uses price string syntax (`"$0.001"`), x402 needs to know which stablecoin to use. Each supported chain has a default asset (USDC) configured internally. If `assetTransferMethod` is not specified, the system defaults to EIP-3009.

### Using Custom Tokens with registerMoneyParser

For tokens other than the default USDC, use `registerMoneyParser` on the server scheme:

**TypeScript:**
```typescript
import { ExactEvmScheme } from "@x402/evm/exact/server";

const server = new ExactEvmScheme();

server.registerMoneyParser(async (amount, network) => {
  if (network === "eip155:8453") {
    return {
      amount: (amount * 1e18).toString(),  // Adjust decimals for your token
      asset: "0xYourTokenAddress",
      extra: {
        assetTransferMethod: "permit2",  // Required for non-EIP-3009 tokens
      },
    };
  }
  return null;  // Fall through to default
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

### Using Pre-Parsed AssetAmount

Alternatively, specify token details directly in route config:

```typescript
{
  "GET /api/resource": {
    accepts: [{
      payTo: "0x...",
      scheme: "exact",
      network: "eip155:8453",
      price: {
        amount: "1000000",
        asset: "0xYourTokenAddress",
        extra: { assetTransferMethod: "permit2" },
      },
    }],
  },
}
```

### Client Permit2 Requirements

When the server specifies `assetTransferMethod: "permit2"`, clients need a one-time Permit2 approval:

```typescript
import { createPermit2ApprovalTx, PERMIT2_ADDRESS } from "@x402/evm";

const tx = createPermit2ApprovalTx(tokenAddress);
await walletClient.sendTransaction(tx);
```

If the client hasn't approved, they receive a `412 Precondition Failed` with error code `PERMIT2_ALLOWANCE_REQUIRED`.

## Supported EVM Assets

- ERC-20 tokens implementing EIP-3009 (e.g., USDC) - default, recommended
- Any ERC-20 via Permit2 fallback - requires `assetTransferMethod: "permit2"`

## Common USDC Addresses

| Network | USDC Address |
|---------|-------------|
| Base Sepolia | `0x036CbD53842c5426634e7929541eC2318f3dCF7e` |
| Base Mainnet | `0x833589fCD6eDb6E08f4c7C32D4f71b54bda02913` |
