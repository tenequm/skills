# Solana Integration Reference

Complete reference for integrating Privy with Solana - embedded wallets, external connectors, transaction signing, and gas sponsorship.

## Table of Contents

- [Setup](#setup)
- [Solana Wallet Hooks](#solana-wallet-hooks)
- [External Solana Connectors](#external-solana-connectors)
- [Creating Wallets](#creating-wallets)
- [Signing Messages](#signing-messages)
- [Signing Transactions](#signing-transactions)
- [Sending Transactions](#sending-transactions)
- [Preparing Transactions with @solana/kit](#preparing-transactions-with-solanakit)
- [Using @solana/web3.js](#using-solanaweb3js)
- [Gas Sponsorship (Fee Payer)](#gas-sponsorship-fee-payer)
- [Server-Side Solana Operations](#server-side-solana-operations)
- [Next.js Webpack Config](#nextjs-webpack-config)

## Setup

### PrivyProvider with Solana

```tsx
'use client';
import {PrivyProvider} from '@privy-io/react-auth';
import {toSolanaWalletConnectors} from '@privy-io/react-auth/solana';
import {createSolanaRpc, createSolanaRpcSubscriptions} from '@solana/kit';

export function Providers({children}: {children: React.ReactNode}) {
  return (
    <PrivyProvider
      appId={process.env.NEXT_PUBLIC_PRIVY_APP_ID!}
      config={{
        // Solana RPC config (required for embedded wallet UIs)
        solana: {
          rpcs: {
            'solana:mainnet': {
              rpc: createSolanaRpc('https://api.mainnet-beta.solana.com'),
              rpcSubscriptions: createSolanaRpcSubscriptions('wss://api.mainnet-beta.solana.com')
            }
          }
        },
        appearance: {
          showWalletLoginFirst: true,
          walletChainType: 'solana-only' // or 'ethereum-and-solana'
        },
        loginMethods: ['wallet', 'email'],
        externalWallets: {
          solana: {
            connectors: toSolanaWalletConnectors() // Detect Phantom, Solflare, etc.
          }
        },
        embeddedWallets: {
          solana: {createOnLogin: 'all-users'}
        }
      }}
    >
      {children}
    </PrivyProvider>
  );
}
```

`config.solana.rpcs` is only required when using Privy's embedded wallet UIs (`signTransaction`, `signAndSendTransaction`). If your app only uses external Solana wallets, you can omit it and prepare/send transactions via your own RPC client.

### Dependencies

```bash
npm i @privy-io/react-auth @solana/kit @solana-program/system
# or for @solana/web3.js:
npm i @privy-io/react-auth @solana/web3.js
```

## Solana Wallet Hooks

All Solana-specific hooks are imported from `@privy-io/react-auth/solana`:

```tsx
import {
  useWallets,
  useCreateWallet,
  useSignMessage,
  useSignTransaction,
  useSignAndSendTransaction,
  useSendTransaction
} from '@privy-io/react-auth/solana';
```

### useWallets (Solana)

```tsx
import {useWallets} from '@privy-io/react-auth/solana';

const {ready, wallets} = useWallets();

// Find embedded wallet
const embeddedWallet = wallets.find((w) => w.standardWallet.name === 'Privy');

// Find external wallet (Phantom, etc.)
const externalWallet = wallets.find((w) => w.standardWallet.name === 'Phantom');
```

## External Solana Connectors

```tsx
import {toSolanaWalletConnectors} from '@privy-io/react-auth/solana';

// In PrivyProvider config
config={{
  externalWallets: {
    solana: {
      connectors: toSolanaWalletConnectors()
    }
  }
}}
```

This enables detection of all Solana standard wallets: Phantom, Solflare, Backpack, etc.

## Creating Wallets

### Auto-create on Login

```tsx
config={{
  embeddedWallets: {
    solana: {createOnLogin: 'all-users'} // or 'users-without-wallets' | 'off'
  }
}}
```

### Manual Creation

```tsx
import {useCreateWallet} from '@privy-io/react-auth/solana';

const {createWallet} = useCreateWallet();

const wallet = await createWallet({createAdditional: false});
// createAdditional: true for HD wallets (multiple wallets per user)
console.log('Address:', wallet.address);
```

## Signing Messages

```tsx
import {useSignMessage, useWallets} from '@privy-io/react-auth/solana';

const {signMessage} = useSignMessage();
const {wallets} = useWallets();

const wallet = wallets.find((w) => w.standardWallet.name === 'Privy');

const handleSign = async () => {
  if (!wallet) throw new Error('No wallet found');
  const signature = await signMessage({
    message: new TextEncoder().encode('Hello from Privy!'),
    wallet
  });
  console.log('Signature:', signature);
};
```

## Signing Transactions

```tsx
import {useSignTransaction, useWallets} from '@privy-io/react-auth/solana';

const {signTransaction} = useSignTransaction();
const {wallets} = useWallets();

const handleSign = async () => {
  const wallet = wallets.find((w) => w.standardWallet.name === 'Privy');
  if (!wallet) throw new Error('No wallet');

  const transaction = await buildTransaction(wallet); // Your transaction builder
  const signed = await signTransaction({transaction, wallet});
  console.log('Signed:', signed);
};
```

## Sending Transactions

```tsx
import {useSignAndSendTransaction, useWallets} from '@privy-io/react-auth/solana';

const {signAndSendTransaction} = useSignAndSendTransaction();
const {wallets} = useWallets();

const handleSend = async () => {
  const wallet = wallets.find((w) => w.standardWallet.name === 'Privy');
  if (!wallet) throw new Error('No wallet');

  const transaction = await buildTransaction(wallet);
  const txSignature = await signAndSendTransaction({transaction, wallet});
  console.log('TX:', txSignature);
};
```

### useSendTransaction (simplified)

```tsx
import {useSendTransaction} from '@privy-io/react-auth/solana';
import {Connection, Transaction, SystemProgram, LAMPORTS_PER_SOL} from '@solana/web3.js';

const {sendTransaction} = useSendTransaction();
const connection = new Connection('https://api.mainnet-beta.solana.com');

const transaction = new Transaction().add(
  SystemProgram.transfer({
    fromPubkey: wallet.publicKey,
    toPubkey: new PublicKey('RECIPIENT'),
    lamports: 0.1 * LAMPORTS_PER_SOL
  })
);

await sendTransaction({transaction, connection});
```

## Preparing Transactions with @solana/kit

The modern `@solana/kit` (formerly `@solana/web3.js` v2) uses a pipe-based API:

```tsx
import type {ConnectedStandardSolanaWallet} from '@privy-io/react-auth/solana';
import {
  pipe,
  createSolanaRpc,
  getTransactionEncoder,
  createTransactionMessage,
  setTransactionMessageFeePayer,
  setTransactionMessageLifetimeUsingBlockhash,
  appendTransactionMessageInstructions,
  compileTransaction,
  address,
  createNoopSigner
} from '@solana/kit';
import {getTransferSolInstruction} from '@solana-program/system';

async function buildTransaction(wallet: ConnectedStandardSolanaWallet) {
  const transferInstruction = getTransferSolInstruction({
    amount: BigInt(0.1 * 1_000_000_000), // lamports
    destination: address('RECIPIENT_ADDRESS'),
    source: createNoopSigner(address(wallet.address))
  });

  const rpc = createSolanaRpc('https://api.mainnet-beta.solana.com');
  const {value: latestBlockhash} = await rpc.getLatestBlockhash().send();

  const transaction = pipe(
    createTransactionMessage({version: 0}),
    (tx) => setTransactionMessageFeePayer(address(wallet.address), tx),
    (tx) => setTransactionMessageLifetimeUsingBlockhash(latestBlockhash, tx),
    (tx) => appendTransactionMessageInstructions([transferInstruction], tx),
    (tx) => compileTransaction(tx),
    (tx) => new Uint8Array(getTransactionEncoder().encode(tx))
  );

  return transaction;
}
```

## Using @solana/web3.js

The classic `@solana/web3.js` v1 API:

```tsx
import {
  Connection,
  Transaction,
  SystemProgram,
  PublicKey,
  LAMPORTS_PER_SOL
} from '@solana/web3.js';

async function buildTransaction(fromAddress: string) {
  const connection = new Connection('https://api.mainnet-beta.solana.com');

  const transaction = new Transaction().add(
    SystemProgram.transfer({
      fromPubkey: new PublicKey(fromAddress),
      toPubkey: new PublicKey('RECIPIENT'),
      lamports: 0.1 * LAMPORTS_PER_SOL
    })
  );

  const {blockhash} = await connection.getLatestBlockhash();
  transaction.recentBlockhash = blockhash;
  transaction.feePayer = new PublicKey(fromAddress);

  return transaction;
}
```

## Gas Sponsorship (Fee Payer)

Solana gas sponsorship uses a fee payer pattern (no paymasters like EVM).

### Architecture

1. Server creates and funds a fee payer wallet
2. Client builds transaction with `feePayer` set to fee payer address
3. Client signs with user wallet, sends partially-signed TX to server
4. Server signs with fee payer wallet, broadcasts to network

### Server-Side Fee Payer Setup

```ts
import {Keypair} from '@solana/web3.js';
import bs58 from 'bs58';

// Generate or load fee payer
const feePayerWallet = new Keypair();
const feePayerAddress = feePayerWallet.publicKey.toBase58();
const feePayerPrivateKey = bs58.encode(feePayerWallet.secretKey);

// Or use a Privy server wallet as fee payer
const feePayerWallet = await privy.wallets().create({chain_type: 'solana'});
```

### Client-Side: Build with Fee Payer

```tsx
const transaction = new Transaction().add(/* instructions */);
transaction.feePayer = new PublicKey(feePayerAddress); // Server's fee payer
const {blockhash} = await connection.getLatestBlockhash();
transaction.recentBlockhash = blockhash;

// Sign with user's wallet
const signed = await signTransaction({transaction, wallet: userWallet});

// Send to server for fee payer signature
const response = await fetch('/api/sponsor', {
  method: 'POST',
  body: JSON.stringify({transaction: signed.serialize().toString('base64')})
});
```

### Server-Side: Sign and Broadcast

```ts
// API route: /api/sponsor
const {transaction: serialized} = req.body;
const transaction = Transaction.from(Buffer.from(serialized, 'base64'));

// Sign with fee payer
transaction.partialSign(feePayerKeypair);

// Broadcast
const connection = new Connection('https://api.mainnet-beta.solana.com');
const signature = await connection.sendRawTransaction(transaction.serialize());
```

Docs: https://docs.privy.io/wallets/gas-and-asset-management/gas/solana

## Server-Side Solana Operations

### Create Wallet

```ts
const wallet = await privy.wallets().create({chain_type: 'solana'});
```

### Sign Message

```ts
const {signature} = await privy.wallets().solana().signMessage(walletId, {
  message: 'Hello'
});
```

### Sign and Send Transaction

```ts
const {signature} = await privy.wallets().solana().signAndSendTransaction(walletId, {
  caip2: 'solana:mainnet',
  params: {
    transaction: base64EncodedTransaction
  }
});
```

### Sign Transaction (without sending)

```ts
const {signed_transaction} = await privy.wallets().solana().signTransaction(walletId, {
  caip2: 'solana:mainnet',
  params: {
    transaction: base64EncodedTransaction
  }
});
```

## Next.js Webpack Config

When using Privy with Solana on Next.js with Yarn, add this webpack config:

```ts
// next.config.ts
import type {NextConfig} from 'next';

const nextConfig: NextConfig = {
  webpack: (config) => {
    config.externals['@solana/kit'] = 'commonjs @solana/kit';
    config.externals['@solana-program/memo'] = 'commonjs @solana-program/memo';
    config.externals['@solana-program/system'] = 'commonjs @solana-program/system';
    config.externals['@solana-program/token'] = 'commonjs @solana-program/token';
    return config;
  }
};

export default nextConfig;
```

This is only needed when using Yarn as package manager with Next.js and webpack.

## Official Links

- Solana getting started recipe: https://docs.privy.io/recipes/solana/getting-started-with-privy-and-solana
- Solana SPL tokens: https://docs.privy.io/recipes/solana/sending-spl-tokens
- Solana sending SOL: https://docs.privy.io/recipes/solana/sending-sol
- Solana standard wallets: https://docs.privy.io/recipes/solana/solana-standard-wallets
- Solana mobile wallet adapter: https://docs.privy.io/recipes/solana/solana-mobile-wallet-adapter
- @solana/kit integration: https://docs.privy.io/wallets/connectors/solana/solana-kit
- @solana/web3.js integration: https://docs.privy.io/wallets/connectors/solana/solana-web3js
- Solana networks config: https://docs.privy.io/basics/react/solana-networks
- Gas sponsorship Solana: https://docs.privy.io/wallets/gas-and-asset-management/gas/solana
- React Native Solana deeplinking: https://docs.privy.io/recipes/react-native/deeplinking-solana-wallets
