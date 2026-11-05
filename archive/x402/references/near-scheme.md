# NEAR Exact Scheme Reference

The `exact` scheme on NEAR uses a NEP-366 `SignedDelegate` authorizing exactly one NEP-141 `ft_transfer`. A facilitator-selected **relayer** sponsors the on-chain transaction, so the payer needs no NEAR for gas.

**TypeScript only** - `@x402/near` (published on npm at 2.20.0). Python and Go not implemented.

NEAR previously appeared in the spec with no SDK; it graduated to a shipped TypeScript implementation in this release line.

## Network Identifiers

| Network | CAIP-2 ID | Default RPC |
|---------|-----------|-------------|
| NEAR Mainnet | `near:mainnet` | `https://rpc.mainnet.fastnear.com` |
| NEAR Testnet | `near:testnet` | `https://rpc.testnet.fastnear.com` |

Defaults point at FastNEAR's keyless public endpoints - the legacy `*.near.org` public RPC is deprecated. Override per network through the signer configuration when a private or archival node is required.

The default `x402.org` facilitator does **not** support NEAR. A [community NEAR facilitator](https://docs.x402.org/dev-tools/facilitators) is listed in the docs facilitator directory.

## Default Assets

Circle USDC NEP-141 contract accounts, 6 decimals, used as the fallback for simple money inputs:

| Network | Contract account |
|---------|------------------|
| `near:mainnet` | `17208628f84f5d6ad33f0da3bbbeb27ffcb398eac501a31bd6ad2011e36133a1` |
| `near:testnet` | `3e2210e1184b45b64c8a434c0a7e7b23cc04ea7eb7a6c3c32520d03d4afcb8af` |

## Payload

```json
{
  "payload": {
    "signedDelegateAction": "<base64-encoded Borsh SignedDelegate>"
  }
}
```

A base64-encoded Borsh NEP-366 `SignedDelegate` whose delegate action represents exactly one NEP-141 `ft_transfer`.

## Protocol Flow

1. Server returns `402` with NEAR payment requirements
2. Client builds a NEP-366 delegate action wrapping one `ft_transfer` to `payTo` for the exact amount, with `1` yoctoNEAR attached (NEP-141 requires this)
3. Client signs the delegate action with a **full-access key** (ed25519 or secp256k1)
4. Facilitator verifies the signed delegate against the payment requirements
5. Facilitator submits it through a relayer account, sponsoring gas
6. Settlement reports `success: true` only once the inner `ft_transfer` receipt has succeeded on-chain

## Verification Rules

- Version, scheme, network, and requirement consistency (asset, recipient, amount, timeout)
- NEP-366 `SignedDelegate` signature (ed25519 or secp256k1)
- Exactly one `ft_transfer` to `payTo` for the exact `amount`, with `1` yoctoNEAR attached
- Deterministic `maxTimeoutSeconds` to `max_block_height` window
- Replay protection via the on-chain access-key nonce (`view_access_key`)
- **Full-access key required** - standard function-call keys are rejected
- Chain-state preflight: account existence, deployed token code, `ft_balance_of`, and `storage_balance_of` (NEP-145), **failing closed on any RPC error**

Settlement re-verifies, deduplicates concurrent submissions via an in-memory `SettlementCache`, then submits through the relayer.

## Footgun: Full-Access Key Required

The payer must sign with a full-access key. Function-call access keys - the standard, safer NEAR pattern for dApp interaction - are rejected. Wallets that only expose function-call keys cannot pay via this scheme.

## Footgun: Storage Registration (NEP-145)

Verification checks `storage_balance_of` on the token contract. On NEAR, a recipient that has never been registered with a NEP-141 token has no storage deposit, and the transfer will fail. Register the `payTo` account with the token contract before going live - this is NEAR's analogue of the Solana "destination ATA must exist" footgun.

## TypeScript Usage

### Client

```typescript
import { x402Client } from "@x402/core/client";
import { createClientNearSigner } from "@x402/near";
import { ExactNearScheme } from "@x402/near/exact/client";

const signer = createClientNearSigner({
  accountId: "alice.testnet",
  secretKey: process.env.NEAR_SECRET_KEY, // ed25519:... full-access key
});

const client = new x402Client();
client.register("near:*", new ExactNearScheme(signer));
```

### Resource Server

```typescript
import { x402ResourceServer } from "@x402/core/server";
import { ExactNearScheme } from "@x402/near/exact/server";

const server = new x402ResourceServer();
server.register("near:*", new ExactNearScheme());
```

### Facilitator

```typescript
import { x402Facilitator } from "@x402/core/facilitator";
import { createFacilitatorNearSigner } from "@x402/near";
import { ExactNearScheme } from "@x402/near/exact/facilitator";

const signer = createFacilitatorNearSigner({
  relayers: [{ accountId: "relayer.testnet", secretKey: process.env.NEAR_RELAYER_KEY }],
});

const facilitator = new x402Facilitator();
facilitator.register("near:testnet", new ExactNearScheme(signer));
```

`ExactNearFacilitatorOptions` has a single field, `maxSponsoredGas?: bigint`, bounding what the relayer will sponsor.

`createClientNearSigner` and `createFacilitatorNearSigner` are JSON-RPC-backed reference implementations accepting an optional `rpcUrls` map. Substitute any implementation of the `ClientNearSigner` / `FacilitatorNearSigner` interfaces (for example KMS-backed, or a custom relayer).

## Key Exports

| Purpose | Export |
|---------|--------|
| Client signer | `createClientNearSigner({ accountId, secretKey, rpcUrls? })` |
| Facilitator signer | `createFacilitatorNearSigner({ relayers, rpcUrls? })` |
| RPC provider factory | `createProviderFactory` |
| Duplicate settlement cache | `SettlementCache` |
| Network constants | `NEAR_MAINNET_CAIP2`, `NEAR_TESTNET_CAIP2` |
| Scheme (all roles) | `ExactNearScheme` from `@x402/near/exact/{client,server,facilitator}` |
