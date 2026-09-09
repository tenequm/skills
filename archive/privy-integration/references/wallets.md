# Wallets Reference

Comprehensive reference for Privy's wallet infrastructure: embedded wallets, smart wallets, external connectors, gas sponsorship, policies, and funding.

## Table of Contents

- [Embedded Wallets Overview](#embedded-wallets-overview)
- [Creating Wallets](#creating-wallets)
- [Signing and Transactions (EVM)](#signing-and-transactions-evm)
- [Smart Wallets (ERC-4337)](#smart-wallets-erc-4337)
- [External Wallets](#external-wallets)
- [Gas Sponsorship](#gas-sponsorship)
- [Wallet Policies and Controls](#wallet-policies-and-controls)
- [Funding Wallets](#funding-wallets)
- [Wallet Export](#wallet-export)
- [HD Wallets](#hd-wallets)
- [Architecture and Security](#architecture-and-security)

## Embedded Wallets Overview

Privy embedded wallets are self-custodial wallets built into your app. Users get wallets without managing seed phrases. Keys are secured in TEEs (Trusted Execution Environments) - neither Privy nor your app can access private keys.

**Supported chains:**
- All EVM chains (Ethereum, Base, Arbitrum, Optimism, Polygon, BNB, etc.)
- Solana
- Bitcoin via Spark - includes Lightning (create Lightning invoices, claim static deposits). Guide: https://docs.privy.io/recipes/spark-btc-guide
- Tron, Sui, Stellar (Tier 2 support)

**Custody options:**
- **User wallets**: User has full custody via Privy auth
- **Server wallets**: Your app controls wallets via API
- **Shared custody**: Both user and server can sign (quorum-based)

## Creating Wallets

### Auto-create on Login (React)

```tsx
<PrivyProvider
  appId="your-app-id"
  config={{
    embeddedWallets: {
      ethereum: {createOnLogin: 'users-without-wallets'},
      solana: {createOnLogin: 'users-without-wallets'}
    }
  }}
>
```

Options: `'users-without-wallets'` | `'all-users'` | `'off'`

### Manual Creation (React)

```tsx
import {useCreateWallet} from '@privy-io/react-auth';

const {createWallet} = useCreateWallet();
const wallet = await createWallet(); // Ethereum embedded wallet
```

### Solana Wallet Creation (React)

```tsx
import {useCreateWallet} from '@privy-io/react-auth/solana';

const {createWallet} = useCreateWallet();
const wallet = await createWallet({createAdditional: false});
// createAdditional: true creates an additional HD wallet
```

### Server-Side Creation

```ts
// Ethereum
const wallet = await privy.wallets().create({chain_type: 'ethereum'});

// Solana
const wallet = await privy.wallets().create({chain_type: 'solana'});

// User-owned wallet
const wallet = await privy.wallets().create({
  chain_type: 'ethereum',
  owner: {user_id: 'did:privy:xxx'}
});

// Batch creation
const wallets = await privy.wallets().createBatch([
  {chain_type: 'ethereum'},
  {chain_type: 'solana'},
  {chain_type: 'ethereum'}
]);
```

### Pregenerate Wallets

Create wallets for users before they sign in:

```ts
// Server-side: pregenerate for a user by email
const user = await privy.users().create({
  linked_accounts: [{type: 'email', address: 'user@example.com'}],
  create_ethereum_wallet: true,
  create_solana_wallet: true
});
```

## Signing and Transactions (EVM)

### React SDK

```tsx
import {useSendTransaction} from '@privy-io/react-auth';

const {sendTransaction} = useSendTransaction();

// Simple ETH transfer
await sendTransaction({
  to: '0xRecipient',
  value: 100000n
});

// Contract interaction
await sendTransaction({
  to: '0xContractAddress',
  data: encodedFunctionData,
  chainId: 8453
});
```

### Sign a Message (React)

```tsx
import {useSignMessage} from '@privy-io/react-auth';

const {signMessage} = useSignMessage();
const signature = await signMessage({message: 'Hello'});
```

### Sign Typed Data (React)

```tsx
import {useSignTypedData} from '@privy-io/react-auth';

const {signTypedData} = useSignTypedData();
const signature = await signTypedData({
  domain: {name: 'MyApp', version: '1', chainId: 8453, verifyingContract: '0x...'},
  types: {/* EIP-712 types */},
  primaryType: 'Transfer',
  message: {/* data */}
});
```

### Server-Side Transactions

```ts
// Send transaction
const {hash} = await privy.wallets().ethereum().sendTransaction(walletId, {
  caip2: 'eip155:8453',
  params: {
    transaction: {
      to: '0xRecipient',
      value: '0x1',
      chain_id: 8453
    }
  }
});

// Sign without sending
const {signature} = await privy.wallets().ethereum().signTransaction(walletId, {
  caip2: 'eip155:8453',
  params: {
    transaction: {to: '0x...', value: '0x1', chain_id: 8453}
  }
});
```

## Smart Wallets (ERC-4337)

Smart wallets are onchain smart contracts controlled by an embedded signer. They enable gas sponsorship, batched transactions, and programmable permissions.

**EVM only.** Privy smart wallets (account abstraction) exist on EVM chains only. On Solana, Privy provides standard EOA embedded wallets - there is no Privy Solana smart wallet. Don't assume Solana account abstraction.

### Supported Providers

| Provider | Package |
|----------|---------|
| Kernel (ZeroDev) | Built-in |
| Safe | Built-in |
| Alchemy (LightAccount) | Built-in |
| Biconomy | Built-in |
| Thirdweb | Built-in |
| Coinbase Smart Wallet | Built-in |

### Setup

1. Enable smart wallets in Dashboard (Wallets > Smart Wallets)
2. Choose account implementation
3. (Optional) Add paymaster URL for gas sponsorship

```bash
npm i permissionless viem
```

```tsx
import {PrivyProvider} from '@privy-io/react-auth';
import {SmartWalletsProvider} from '@privy-io/react-auth/smart-wallets';

export default function Providers({children}: {children: React.ReactNode}) {
  return (
    <PrivyProvider appId="your-app-id" config={{/* ... */}}>
      <SmartWalletsProvider>{children}</SmartWalletsProvider>
    </PrivyProvider>
  );
}
```

### Using Smart Wallets

```tsx
import {useSmartWallets} from '@privy-io/react-auth/smart-wallets';

const {client: smartWalletClient} = useSmartWallets();

// Send transaction (gas sponsored if paymaster configured)
const txHash = await smartWalletClient.sendTransaction({
  account: smartWalletClient.account,
  to: '0xRecipient',
  value: 100000n
});

// Batch transactions
const txHash = await smartWalletClient.sendTransaction({
  account: smartWalletClient.account,
  calls: [
    {to: '0xAddr1', value: 100n},
    {to: '0xAddr2', data: '0x...'}
  ]
});
```

### Smart Wallet Address

The smart wallet address differs from the embedded signer address. Store smart wallet addresses via the `useSmartWallets` hook or listen for the `user.wallet_created` webhook.

### Server-Side Smart Wallets

For server-created wallets using smart accounts, use Pimlico's `permissionless` package with Privy wallets as signers. See: https://docs.privy.io/wallets/gas-and-asset-management/gas/ethereum

## Wallet Actions

Beyond raw `sendTransaction`/`signMessage`, the Node SDK ships higher-level, policy-gated **actions** on `privy.wallets()`. These orchestrate multi-step on-chain flows (quotes, approvals, routing) server-side, which is ideal for autonomous agents that need to earn, swap, or move funds without hand-rolling each transaction. All actions are async and report progress via webhooks; check status with `privy.wallets().actions...` / the `wallets/actions` status endpoint.

### Earn (DeFi yield)

Deposit into and withdraw from yield vaults, claim incentives, and read positions.

```ts
const earn = privy.wallets().earn();
// earn().deposit(...) / withdraw(...) / claim(...) / getVaultDetails(...) / getVaultPosition(...)
```

Docs: https://docs.privy.io/wallets/actions/earn/overview (setup, policies, and `earn` webhooks under the same path).

### Swap

Quote and execute token swaps, including cross-asset / cross-chain (DADC) routes.

```ts
const swap = privy.wallets().swap;
// swap.getQuote({...}) then swap.execute({...})
```

Docs: https://docs.privy.io/wallets/actions/swap/overview

### Transfer (with bridging)

`transfer()` moves assets and can bridge across chains in one call.

```ts
const result = await privy.wallets().transfer(walletId, {
  // recipient, asset, amount, source/destination chains, optional bridging...
});
```

Docs: https://docs.privy.io/wallets/actions/transfer/overview (and `transfer/bridging`). Actions overview: https://docs.privy.io/wallets/actions/overview

## External Wallets

### Connecting External Wallets

```tsx
import {usePrivy} from '@privy-io/react-auth';

const {connectWallet} = usePrivy();

// Opens wallet connection modal (MetaMask, WalletConnect, etc.)
connectWallet();
```

### Configuring External Connectors

EVM connectors are auto-detected. For Solana, import and pass connectors:

```tsx
import {toSolanaWalletConnectors} from '@privy-io/react-auth/solana';

<PrivyProvider
  config={{
    externalWallets: {
      solana: {connectors: toSolanaWalletConnectors()}
    }
  }}
>
```

### Authenticating with External Wallet

```tsx
import {useLoginWithWallet} from '@privy-io/react-auth';

const {login} = useLoginWithWallet();
await login(); // Prompts wallet signature for SIWE
```

### Accessing Connected Wallets

```tsx
import {useWallets} from '@privy-io/react-auth';

const {wallets} = useWallets();
// Includes both embedded and external wallets
// wallet.walletClientType: 'privy' (embedded), 'metamask', 'phantom', etc.
```

**Footgun - resolving the right address.** A user can have both EVM and Solana embedded wallets. When you need an EVM address from `user.linked_accounts` (especially server-side), filter by `chain_type === 'ethereum'` - grabbing the first wallet may return a Solana base58 address, which a viem/EVM call rejects with `"Address is invalid - must be hex value of 20 bytes"` (often surfacing as a generic 500). Guard with viem's `isAddress()` so a non-EVM address yields a clean error. Note this only fixes new logins; rows already persisted with the wrong address need a re-sync.

## Gas Sponsorship

### Native Gas Sponsorship (Recommended)

Privy's native gas sponsorship uses EIP-7702 + paymasters on EVM and fee payers on Solana. Configure in Dashboard.

**Supported EVM networks:** Ethereum, Base, Arbitrum, Optimism, Polygon, BNB, Unichain, Berachain, Monad, MegaETH, World Chain, and more (plus testnets).

**Supported Solana networks:** Mainnet, Devnet.

### Smart Wallet Gas Sponsorship (EVM)

Register a paymaster URL in the Dashboard. Privy routes transactions to the paymaster which pays gas instead of the user.

### Solana Gas Sponsorship (Fee Payer Pattern)

1. Create a fee payer wallet on your server
2. Client prepares transaction with fee payer as `feePayer`
3. Client signs with user's wallet, sends to server
4. Server signs with fee payer wallet, broadcasts

```ts
// Server: create fee payer
import {Keypair} from '@solana/web3.js';
const feePayerWallet = new Keypair();
// Fund this wallet with SOL for gas

// Client: prepare transaction with custom fee payer
const transaction = new Transaction();
transaction.feePayer = new PublicKey(feePayerAddress);
// ... add instructions, get recent blockhash
// Sign with user wallet, send to server
// Server signs with fee payer, broadcasts
```

### Security Best Practices for Gas Sponsorship

- Implement rate limiting per user/session
- Set spending caps per wallet/time period
- Monitor gas usage with webhooks
- Use custom rate limits: https://docs.privy.io/recipes/gas-sponsorship-rate-limits

## Wallet Policies and Controls

### Policy Types

- **Spending limits**: Max transfer amounts per time window
- **Allowlisted contracts**: Only interact with approved contracts
- **Allowlisted recipients**: Only send to approved addresses
- **Calldata restrictions**: Restrict smart contract function calls
- **Time-based rules**: Actions only during certain time windows

### Quorum Approvals

Require m-of-n approvals from designated signers before executing transactions.

### Authorization Keys

Add cryptographic authorization keys to wallets for additional security. Requests require signatures from both the wallet owner and the authorization key.

### Signers

Add server-side signers to user wallets to enable:
- Server-side transaction execution
- Automated operations (bots, limit orders)
- Shared custody between user and app

Docs: https://docs.privy.io/wallets/using-wallets/signers/overview

**Footgun - signing a user-owned wallet from the server.** Embedded wallets created via the frontend SDK are *user-owned*; the server cannot sign for them out of the box. `signSecp256k1()` (and other signing calls) fail with `"No valid authorization keys or user signing keys available"` until you register an authorization key as a signer: (1) generate a P256 key (`openssl ecparam -name prime256v1 -genkey`); (2) add it as a key quorum (threshold 1) in Dashboard > Authorization Keys; (3) attach the quorum as a signer on each wallet (e.g. via `useSigners().addSigners()` after login); (4) include the key's P256 signature in the `privy-authorization-signature` header on wallet API calls. If you don't need user custody, app-owned **server wallets** (`privy.wallets().create({chain_type})`) sidestep all of this - no authorization context, no quorums.

## Funding Wallets

Privy supports multiple funding methods:

- **Card**: Credit/debit card via onramp providers
- **Apple Pay / Google Pay**: Mobile payment
- **Bank account**: ACH / wire transfer
- **Exchange**: Transfer from crypto exchange
- **Wallet**: Transfer from external wallet
- **Relay deposit addresses**: Generate dedicated deposit addresses

Configure in Dashboard under Wallets > Funding.

### Programmatic fiat on/offramp + KYC

Beyond the dashboard funding UI, Privy exposes programmatic **fiat onramp/offramp** with KYC via an `Onramps` resource and fiat APIs (backed by Bridge, Stripe, and Kraken Embed). Use these to onboard fiat-to-crypto and cash out crypto-to-fiat inside your own flow, including collecting KYC and creating fiat accounts.

Docs: https://docs.privy.io/wallets/funding/fiat-onramp (config: `/wallets/funding/configuration`; recipes: `/recipes/bridge-onramp`, `/recipes/stripe-headless-onramp`).

Funding overview: https://docs.privy.io/wallets/gas-and-asset-management/funding/overview

## Wallet Export

Users can export their embedded wallet private keys as an escape hatch.

```tsx
import {usePrivy} from '@privy-io/react-auth';

const {exportWallet} = usePrivy();
await exportWallet(); // Opens secure export modal
```

Server-side export:
```ts
const {private_key} = await privy.wallets().export(walletId);
```

## HD Wallets

Privy supports hierarchical deterministic (HD) wallets for creating multiple wallets from a single seed.

```tsx
import {useCreateWallet} from '@privy-io/react-auth';

const {createWallet} = useCreateWallet();

// Create additional HD wallet for the same user
const hdWallet = await createWallet({createAdditional: true});
```

Recipe: https://docs.privy.io/wallets/wallets/import-a-wallet/hd-wallets

## Architecture and Security

**Important**: Privy uses **Shamir's Secret Sharing (SSS) + TEEs**, NOT MPC/TSS. This is a deliberate architectural choice - SSS is a mature 1970s algorithm vs TSS (2017). Keys are only ever reconstituted client-side in secure enclaves.

### Key Management (2-of-2 Shamir)

1. Private key generated inside AWS Nitro Enclave (TEE) from 128-bit CSPRNG entropy
2. Key split into 2 Shamir shares:
   - **Auth share** - encrypted, stored by Privy. Released only upon valid authentication
   - **Enclave share** - encrypted with TEE's key. Decryptable only inside the TEE
3. Neither share alone reveals anything about the private key
4. Key reconstructed temporarily in-memory inside TEE for signing, then discarded

### Signing Flow

1. App sends request with API credential + authorization key signature
2. Privy API authenticates the credential
3. Request forwarded to TEE with auth share
4. TEE verifies authorization, decrypts enclave share
5. TEE combines shares, reconstructs key, signs
6. Signature returned, key discarded

### Custody Model

- **User custody**: User authenticates to unlock wallet. Privy holds key shares but cannot use them alone.
- **Server custody**: Your app controls wallets via API secret + optional authorization keys.
- **Flexible custody**: Configure per wallet with quorums and policies.

### HD Wallet Derivation Paths

- Ethereum: `m/44'/60'/0'/0/i`
- Solana: `m/44'/501'/i/0'`

### Security Docs

- Architecture: https://docs.privy.io/security/wallet-infrastructure/architecture
- Secure enclaves: https://docs.privy.io/security/wallet-infrastructure/secure-enclaves
- Security FAQs / threat models: https://docs.privy.io/security/security-faqs
- Security checklist: https://docs.privy.io/security/implementation-guide/security-checklist
- CSP guidance: https://docs.privy.io/security/implementation-guide/content-security-policy
- Open-source SSS library: https://github.com/privy-io/shamir-secret-sharing

## Agentic Wallets

For autonomous agent wallets with policy-based controls, authorization keys, OpenClaw integration, and the Agent Auth Protocol, see **[agent-auth.md](agent-auth.md)**.

For x402 and MPP payment integration with Privy wallets, see **[agent-payments.md](agent-payments.md)**.

## Official Links

- Wallets overview: https://docs.privy.io/wallets/overview
- Create a wallet: https://docs.privy.io/wallets/wallets/create/create-a-wallet
- Wallet actions (earn/swap/transfer): https://docs.privy.io/wallets/actions/overview
- Smart wallets: https://docs.privy.io/wallets/using-wallets/evm-smart-wallets/overview
- Smart wallets SDK: https://docs.privy.io/wallets/using-wallets/evm-smart-wallets/setup/configuring-sdk
- Smart wallets Dashboard: https://docs.privy.io/wallets/using-wallets/evm-smart-wallets/setup/configuring-dashboard
- Gas overview: https://docs.privy.io/wallets/gas-and-asset-management/gas/overview
- Gas Ethereum: https://docs.privy.io/wallets/gas-and-asset-management/gas/ethereum
- Gas Solana: https://docs.privy.io/wallets/gas-and-asset-management/gas/solana
- External connectors: https://docs.privy.io/wallets/connectors/overview
- Policies: https://docs.privy.io/controls/policies/overview
- Signers: https://docs.privy.io/wallets/using-wallets/signers/overview
- Funding: https://docs.privy.io/wallets/gas-and-asset-management/funding/overview
- Transaction management: https://docs.privy.io/transaction-management/overview
