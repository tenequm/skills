# Client-Side Development

Guide for building Solana dApp frontends: wallet connections, balance queries, token transfers, and transaction management.

## Which Library?

| Building | Use | Install |
|----------|-----|---------|
| React/Next.js dApp | framework-kit (`@solana/client` + `@solana/react-hooks`) | `npm i @solana/client @solana/react-hooks` |
| Non-React frontend (Svelte, Vue) | `@solana/client` standalone | `npm i @solana/client` |
| Server-side scripts, bots, CLIs | `@solana/kit` 6.x | `npm i @solana/kit` |
| Anchor program TS client | `@coral-xyz/anchor` (requires `@solana/web3.js` v1) | `npm i @coral-xyz/anchor @solana/web3.js` |
| Migrating from web3.js v1 | `@solana/web3-compat` | `npm i @solana/web3-compat` |

> **Default recommendation:** Use framework-kit for any frontend. It handles wallet discovery, state management, and caching out of the box. Use `@solana/kit` 6.x only when you need raw RPC control without framework-kit's abstractions (server-side scripts, bots, CLIs).

## Framework-Kit

Solana Foundation's official dApp framework. Built on `@solana/kit` 5.x + Zustand (state) + SWR (React caching).

- [Documentation](https://www.framework-kit.com/) | [GitHub](https://github.com/solana-foundation/framework-kit)

### Setup (React)

```tsx
import { autoDiscover, createClient } from "@solana/client";
import { SolanaProvider, useWalletConnection, useBalance } from "@solana/react-hooks";

const client = createClient({
  cluster: "devnet", // or "mainnet" | "testnet" | "localnet"
  walletConnectors: autoDiscover(),
});

export function App() {
  return (
    <SolanaProvider client={client}>
      <WalletPanel />
    </SolanaProvider>
  );
}
```

Cluster monikers auto-resolve RPC + WebSocket URLs. Use `endpoint` for custom RPC:

```ts
const client = createClient({
  endpoint: "https://your-rpc.example.com",
  walletConnectors: autoDiscover(),
});
```

Filter which wallets appear:

```ts
import { autoDiscover, filterByNames } from "@solana/client";

const client = createClient({
  cluster: "devnet",
  walletConnectors: autoDiscover({ filter: filterByNames("phantom", "solflare") }),
});
```

> **Next.js / RSC:** Components using these hooks must be marked with `'use client'`.

### Wallet Connection

```tsx
function WalletPanel() {
  const { connectors, connect, disconnect, wallet, status, currentConnector } =
    useWalletConnection();
  const address = wallet?.account.address;
  const balance = useBalance(address);

  if (status === "connected") {
    return (
      <div>
        <p>Connected via {currentConnector?.name}</p>
        <p>{address?.toString()}</p>
        <p>Lamports: {balance.lamports?.toString() ?? "loading..."}</p>
        <button onClick={disconnect}>Disconnect</button>
      </div>
    );
  }

  return connectors.map((c) => (
    <button key={c.id} onClick={() => connect(c.id)}>
      Connect {c.name}
    </button>
  ));
}
```

### Send SOL

```tsx
import { useSolTransfer } from "@solana/react-hooks";

function SendSol({ destination }: { destination: string }) {
  const { send, isSending, status, signature, error } = useSolTransfer();
  return (
    <div>
      <button
        disabled={isSending}
        onClick={() => send({ destination, amount: 100_000_000n /* 0.1 SOL */ })}
      >
        {isSending ? "Sending..." : "Send 0.1 SOL"}
      </button>
      {signature ? <p>Signature: {signature}</p> : null}
      {error ? <p>Error: {String(error)}</p> : null}
    </div>
  );
}
```

### SPL Token Balance + Transfer

```tsx
import { useSplToken } from "@solana/react-hooks";

function TokenPanel({ mint, destinationOwner }: { mint: string; destinationOwner: string }) {
  const { balance, send, isSending, status, error, sendSignature } = useSplToken(mint);

  if (status === "disconnected") return <p>Connect wallet to view balance</p>;
  if (status === "loading") return <p>Loading balance...</p>;

  return (
    <div>
      <p>Balance: {balance?.uiAmount ?? "0"}</p>
      <button
        disabled={isSending}
        onClick={() => send({ amount: 1n, destinationOwner, amountInBaseUnits: true })}
      >
        {isSending ? "Sending..." : "Send 1 token"}
      </button>
      {sendSignature ? <p>Signature: {sendSignature}</p> : null}
    </div>
  );
}
```

Token 2022 mints: pass `config: { tokenProgram: "auto" }` as second argument to `useSplToken`.

### Arbitrary Transactions

```tsx
import type { TransactionInstructionInput } from "@solana/client";
import { useTransactionPool, useWalletSession } from "@solana/react-hooks";

function TransactionFlow({ ix }: { ix: TransactionInstructionInput }) {
  const session = useWalletSession();
  const { addInstruction, prepareAndSend, isSending, sendSignature, sendError } =
    useTransactionPool();

  return (
    <div>
      <button onClick={() => addInstruction(ix)}>Add instruction</button>
      <button
        disabled={isSending || !session}
        onClick={() => prepareAndSend({ authority: session })}
      >
        {isSending ? "Sending..." : "Prepare & Send"}
      </button>
      {sendSignature ? <p>Signature: {sendSignature}</p> : null}
      {sendError ? <p>{String(sendError)}</p> : null}
    </div>
  );
}
```

For simpler cases where you already have instructions:

```tsx
import { useSendTransaction } from "@solana/react-hooks";

const { send, isSending, signature, error } = useSendTransaction();
await send({ instructions });
```

### Non-React Usage (`@solana/client` standalone)

`@solana/client` works without React in any JS runtime:

```ts
import { autoDiscover, createClient } from "@solana/client";

const client = createClient({
  cluster: "devnet",
  walletConnectors: autoDiscover(),
});

// Connect wallet
await client.actions.connectWallet("wallet-standard:phantom");

// Read balance
const wallet = client.store.getState().wallet;
if (wallet.status === "connected") {
  const lamports = await client.actions.fetchBalance(wallet.session.account.address);
  console.log(`Lamports: ${lamports.toString()}`);
}

// Send SOL
const signature = await client.solTransfer.sendTransfer({
  amount: 100_000_000n,
  authority: wallet.session,
  destination: "Ff34MXWdgNsEJ1kJFj9cXmrEe7y2P93b95mGu5CJjBQJ",
});

// SPL token
const usdc = client.splToken({ mint: "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" });
const balance = await usdc.fetchBalance(wallet.session.account.address);

// Arbitrary transaction
import { getTransferSolInstruction } from "@solana-program/system";

const prepared = await client.transaction.prepare({
  authority: wallet.session,
  instructions: [
    getTransferSolInstruction({
      destination: "Ff34MXWdgNsEJ1kJFj9cXmrEe7y2P93b95mGu5CJjBQJ",
      lamports: 10_000n,
      source: wallet.session.account.address,
    }),
  ],
});
const sig = await client.transaction.send(prepared);
```

### Additional Hooks

| Hook | Purpose |
|------|---------|
| `useAccount(address)` | Fetch + watch account data (lamports, owner, slot) |
| `useWaitForSignature(sig, opts)` | Track confirmation status |
| `useProgramAccounts(program)` | Query all accounts owned by a program (wrap in `SolanaQueryProvider`) |
| `useSimulateTransaction(wire)` | Simulate transaction before sending |
| `useLookupTable(address)` | Fetch address lookup table |
| `useNonceAccount(address)` | Fetch durable nonce account |
| `useClientStore(selector)` | Direct access to Zustand store |

## @solana/kit 6.x (Server-Side / Direct Control)

For server-side scripts, bots, and CLIs where you don't need wallet connection UI or React state management. Kit 6.x provides functional, tree-shakeable primitives for RPC, transaction building, and signing.

- [Documentation](https://solanakit.org) | [npm](https://www.npmjs.com/package/@solana/kit)

This is a lower-level SDK. If you're building a frontend dApp, use framework-kit instead.

## Version Compatibility

- **Framework-kit** uses `@solana/kit ^5.0.0` internally. You don't manage this - it's a framework-kit dependency.
- **`@solana/kit` 6.x** exists as a standalone SDK for direct use (server-side, scripts).
- These don't conflict: framework-kit handles its own Kit 5.x; if you also need Kit 6.x for server-side code, they're separate packages.
- **`@solana/web3-compat`** bridges legacy `@solana/web3.js` v1 code to Kit primitives for incremental migration.

## Resources

- [Framework-kit docs](https://www.framework-kit.com/)
- [Framework-kit GitHub](https://github.com/solana-foundation/framework-kit)
- [Vite + React example](https://github.com/solana-foundation/framework-kit/tree/main/examples/vite-react)
- [Next.js example](https://github.com/solana-foundation/framework-kit/tree/main/examples/nextjs)
- [@solana/kit docs](https://solanakit.org)
