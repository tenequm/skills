# XRPL Exact Scheme Reference

The `exact` scheme on the XRP Ledger uses payer-signed XRPL `Payment` transactions. The payer signs a complete transaction and pays the XRPL network fee themselves; the facilitator only reads ledger state and submits the signed blob.

**TypeScript only** - `@x402/xrpl`. Python and Go not implemented.

> **Not yet on npm.** The package is tagged `npm-@x402/xrpl@v2.20.0` and ships in-repo at 2.20.0, but `npm install @x402/xrpl` currently 404s - build from source until the publish workflow runs. Every other `@x402/*` package is published at 2.20.0.

## Network Identifiers

| Network | CAIP-2 ID | Default WebSocket endpoint |
|---------|-----------|----------------------------|
| XRPL Mainnet | `xrpl:0` | `wss://s1.ripple.com:51233` |
| XRPL Testnet | `xrpl:1` | `wss://s.altnet.rippletest.net:51233` |
| XRPL Devnet | `xrpl:2` | `wss://s.devnet.rippletest.net:51233` |
| Custom | `xrpl:<networkId>` | Supply via `wsUrlByNetwork` |

The default facilitator (`https://x402.org/facilitator`) supports `xrpl:1`.

## No Fee Sponsorship

Unlike every other x402 chain, XRPL cannot sponsor fees. The payer signs a complete transaction with the fee embedded, so:

```
extra.areFeesSponsored  MUST be present and MUST be false
```

The facilitator needs no funded account - it reads ledger state and submits. This inverts the usual x402 gas-abstraction assumption: the payer must hold XRP for fees regardless of which asset they are paying in.

## No Default Asset - Explicit Pricing Required

XRPL has no dollar-string default-asset mapping. A server that writes `price: "$0.001"` for an XRPL route throws:

```
XRPL exact payments require explicit AssetAmount pricing
```

Use an `AssetAmount` instead:

| Asset type | `asset` | `amount` | `extra` |
|------------|---------|----------|---------|
| Native XRP | the literal string `"XRP"` | integer **drops** string (1 XRP = 1,000,000 drops) | - |
| Issued currency (IOU) | currency code (3-char or 40-hex) | XRPL decimal `value` string, e.g. `"10.5"` | `extra.issuer` = issuer classic address |

There is no `extra.decimals` field - issued-currency amounts are ledger decimal values, so `amount` is used verbatim as the signed `value`.

## Asset Transfer Methods (Sequencing)

`extra.assetTransferMethod` selects how the signed transaction is sequenced:

| Method | Behavior | Trade-off |
|--------|----------|-----------|
| `"sequence"` (default) | Consumes the payer account's current `Sequence` | No preflight transaction, no extra reserve, but **one pending payment per account at a time** |
| `"ticketSequence"` | Consumes a pre-created XRPL Ticket (`Sequence = 0` plus `TicketSequence`) | Multiple concurrent pending payments; each outstanding ticket locks owner reserve (0.2 XRP on mainnet), max 250 per account |

The client follows the method pinned in the payment requirements and defaults to `"sequence"`. Servers offer `"ticketSequence"` by advertising it in `extra.assetTransferMethod`, optionally as a second `accepts` entry so clients can choose.

**Sequence-mode footgun:** while a `"sequence"` payment is pending, the payer account must not sign or submit other transactions. Consuming the sequence elsewhere **permanently invalidates** the payment.

For `"ticketSequence"`, the client auto-creates one ticket when none is available. `ticketCreateCount` controls this (default `1`; set `0` to require pre-provisioned tickets).

## Payload

```json
{
  "payload": {
    "signedTxBlob": "1200002280000000240000000161..."
  }
}
```

A single hex-encoded signed XRPL transaction blob.

## TypeScript Usage

### Client

```typescript
import { Wallet } from "xrpl";
import { x402Client } from "@x402/core/client";
import { createXrplWalletSigner } from "@x402/xrpl";
import { ExactXrplScheme } from "@x402/xrpl/exact/client";

const wallet = Wallet.fromSeed(process.env.XRPL_SEED);
const signer = createXrplWalletSigner(wallet);

const client = new x402Client().register("xrpl:*", new ExactXrplScheme(signer));
```

The client uses `xrpl.Client` to autofill `Sequence` (or `Sequence = 0` plus `TicketSequence`), `Fee`, `LastLedgerSequence`, and `NetworkID` for custom networks before signing. Override the connection with `wsUrlByNetwork` or `clientFactory`; set `feeDrops` only to bypass network fee autofill. Applications that prepare transactions externally pass `preparePaymentTransaction`.

### Server

```typescript
import { x402ResourceServer } from "@x402/core/server";
import { ExactXrplScheme } from "@x402/xrpl/exact/server";

const server = new x402ResourceServer(facilitator)
  .register("xrpl:1", new ExactXrplScheme());
```

### Facilitator

```typescript
import { ExactXrplScheme } from "@x402/xrpl/exact/facilitator";

facilitator.register("xrpl:1", new ExactXrplScheme());
```

## Ticket Provisioning

```typescript
import { Wallet } from "xrpl";
import { createTickets, createXrplWalletSigner, getXrplTicketSequences } from "@x402/xrpl";

const signer = createXrplWalletSigner(Wallet.fromSeed(process.env.XRPL_SEED));
const ticketSequences = await createTickets(signer, "xrpl:1", 5);
const available = await getXrplTicketSequences(account, "xrpl:1");
```

## Duplicate Settlement Mitigation

`@x402/xrpl` ships a `SettlementCache` keyed on the signed transaction blob. TTL is sized from the payment's `maxTimeoutSeconds` (which bounds `LastLedgerSequence` expiry) with a **120 second floor** and margin, mirroring the SVM cache. Repeat submissions of the same blob return `duplicate_settlement`.

The reasoning: while the transaction can still land, re-submission would pass re-verification (its sequence or ticket is not yet consumed) and resolve to the same validated `tesSUCCESS`.

## Verification Notes

- Signing public keys must be canonical: 33-byte compressed secp256k1 (`02`/`03` prefix) or ed25519 (`ED` prefix), 64 hex chars. `rippled` rejects non-canonical keys at preflight, so verification rejects them too rather than accepting an unsettleable payload.
- Default facilitator max fee: `10000` drops.
- Expiration converts `maxTimeoutSeconds` to ledgers at ~5 seconds per ledger, plus a 2-ledger tolerance.
- The `tfPartialPayment` flag (`0x00020000`) is checked - partial payments would deliver less than the signed amount.

## Testnet Setup

1. Fund a payer account with the [XRPL Testnet faucet](https://xrpl.org/resources/dev-tools/xrp-faucets) (`wss://s.altnet.rippletest.net:51233`, network `xrpl:1`).
2. Keep [reserves](https://xrpl.org/docs/concepts/accounts/reserves) funded: base reserve (1 XRP) plus 0.2 XRP owner reserve per outstanding ticket.
3. For IOU payments, the receiving account needs a [trust line](https://xrpl.org/docs/concepts/tokens/fungible-tokens) to the issuer and the payer needs sufficient balance.
4. The facilitator needs no funded account.

## Key Exports

| Purpose | Export |
|---------|--------|
| Client signer from an `xrpl` Wallet | `createXrplWalletSigner(wallet)` |
| Create tickets | `createTickets(signer, network, ticketCount)` |
| List available tickets | `getXrplTicketSequences(account, network)` |
| Invoice id to XRPL `InvoiceID` | `invoiceIdToInvoiceIdField(invoiceId)` |
| Network constants | `XRPL_MAINNET`, `XRPL_TESTNET`, `XRPL_DEVNET` |
| Scheme (all roles) | `ExactXrplScheme` from `@x402/xrpl/exact/{client,server,facilitator}` |
