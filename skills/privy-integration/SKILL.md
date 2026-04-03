---
name: privy-integration
description: Integrates Privy authentication, embedded wallets, and agent payment protocols into web and agentic apps. Covers React SDK (PrivyProvider, hooks, wagmi), Node.js SDK, smart wallets (ERC-4337), x402 and MPP machine payments, Tempo chain, and agentic wallets with policies. Use when setting up Privy auth, creating embedded or agentic wallets, adding x402 or MPP payments, integrating with Tempo, configuring wallet policies, or connecting Privy to MCP/Agent Auth flows.
metadata:
  version: "0.2.0"
---

# Privy Integration

Privy provides authentication and wallet infrastructure for apps built on crypto rails. Embed self-custodial wallets, authenticate users via email/SMS/socials/passkeys/wallets, and transact on EVM and Solana chains. Also supports agent payment protocols (x402, MPP) and autonomous agentic wallets.

Key packages:
- `@privy-io/react-auth` - React SDK (auth + wallets + x402)
- `@privy-io/react-auth/solana` - Solana wallet hooks
- `@privy-io/react-auth/smart-wallets` - Smart wallets (ERC-4337)
- `@privy-io/wagmi` - wagmi v2 connector
- `@privy-io/node` - Server-side SDK (replaces deprecated `@privy-io/server-auth`)
- `mppx` - MPP client/server SDK (settles on Tempo)

Docs index: `https://docs.privy.io/llms.txt`

## Workflow Decision Tree

**Setting up Privy auth in a React app?** -> Quick Start below, then [references/react-sdk.md](references/react-sdk.md)
**Adding wagmi/viem to a Privy app?** -> Wagmi Integration below, then [references/react-sdk.md](references/react-sdk.md)
**Working server-side (Node.js)?** -> Server-Side section below, then [references/server-sdk.md](references/server-sdk.md)
**Adding x402 or MPP payments?** -> x402/MPP sections below, then [references/agent-payments.md](references/agent-payments.md)
**Building agentic wallets or agent auth?** -> Agentic Wallets below, then [references/agent-auth.md](references/agent-auth.md)
**Solana-specific integration?** -> [references/solana.md](references/solana.md)
**Wallet management (smart wallets, policies, funding)?** -> [references/wallets.md](references/wallets.md)

## Quick Start (React + Next.js)

### 1. Install

```bash
npm i @privy-io/react-auth
```

### 2. Wrap app with PrivyProvider

```tsx
'use client';
import {PrivyProvider} from '@privy-io/react-auth';

export default function Providers({children}: {children: React.ReactNode}) {
  return (
    <PrivyProvider
      appId={process.env.NEXT_PUBLIC_PRIVY_APP_ID!}
      config={{
        embeddedWallets: {
          ethereum: {createOnLogin: 'users-without-wallets'}
        }
      }}
    >
      {children}
    </PrivyProvider>
  );
}
```

### 3. Check readiness before using hooks

```tsx
import {usePrivy} from '@privy-io/react-auth';

function App() {
  const {ready, authenticated, user} = usePrivy();
  if (!ready) return <div>Loading...</div>;
  // Safe to use Privy hooks now
}
```

### 4. Login (email OTP example)

```tsx
import {useLoginWithEmail} from '@privy-io/react-auth';

function LoginForm() {
  const {sendCode, loginWithCode} = useLoginWithEmail();
  // sendCode({email}) then loginWithCode({code})
}
```

### 5. Send a transaction (EVM)

```tsx
import {useSendTransaction} from '@privy-io/react-auth';

function SendButton() {
  const {sendTransaction} = useSendTransaction();
  return (
    <button onClick={() => sendTransaction({to: '0x...', value: 100000})}>
      Send
    </button>
  );
}
```

## PrivyProvider Config

```tsx
config={{
  // Auth methods enabled for login
  loginMethods: ['email', 'sms', 'wallet', 'google', 'apple', 'twitter',
                 'github', 'discord', 'farcaster', 'telegram', 'passkey'],

  // Embedded wallet creation
  embeddedWallets: {
    ethereum: {createOnLogin: 'users-without-wallets'}, // or 'all-users' | 'off'
    solana: {createOnLogin: 'users-without-wallets'}
  },

  // UI appearance
  appearance: {
    showWalletLoginFirst: false,
    walletChainType: 'ethereum-and-solana', // or 'ethereum-only' | 'solana-only'
    theme: 'light', // or 'dark'
    accentColor: '#6A6FF5',
    logo: 'https://your-logo.png'
  },

  // External wallet connectors (Solana)
  externalWallets: {
    solana: {connectors: toSolanaWalletConnectors()}
  },

  // Solana RPC config (required for embedded wallet UIs)
  solana: {
    rpcs: {
      'solana:mainnet': {
        rpc: createSolanaRpc('https://api.mainnet-beta.solana.com'),
        rpcSubscriptions: createSolanaRpcSubscriptions('wss://api.mainnet-beta.solana.com')
      }
    }
  }
}}
```

## Wagmi Integration

Import `createConfig` and `WagmiProvider` from `@privy-io/wagmi` (NOT from `wagmi`).

```bash
npm i @privy-io/react-auth @privy-io/wagmi wagmi @tanstack/react-query
```

```tsx
import {PrivyProvider} from '@privy-io/react-auth';
import {WagmiProvider, createConfig} from '@privy-io/wagmi';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {mainnet, base} from 'viem/chains';
import {http} from 'wagmi';

const queryClient = new QueryClient();
const wagmiConfig = createConfig({
  chains: [mainnet, base],
  transports: {[mainnet.id]: http(), [base.id]: http()}
});

// Nesting order: PrivyProvider > QueryClientProvider > WagmiProvider
export default function Providers({children}: {children: React.ReactNode}) {
  return (
    <PrivyProvider appId="your-app-id" config={privyConfig}>
      <QueryClientProvider client={queryClient}>
        <WagmiProvider config={wagmiConfig}>{children}</WagmiProvider>
      </QueryClientProvider>
    </PrivyProvider>
  );
}
```

Use wagmi hooks (useAccount, useSendTransaction, etc.) for read/write actions. Use Privy hooks for wallet connection/creation.

## Server-Side Token Verification

```bash
npm i @privy-io/node
```

```ts
import {PrivyClient} from '@privy-io/node';

const privy = new PrivyClient({
  appId: process.env.PRIVY_APP_ID!,
  appSecret: process.env.PRIVY_APP_SECRET!
});

// Verify access token from Authorization header
const {userId} = await privy.verifyAuthToken(accessToken);
```

## Whitelabel Authentication

All auth flows can be fully whitelabeled with custom UI. Key hooks:

| Hook | Auth method |
|------|------------|
| `useLoginWithEmail` | Email OTP (`sendCode`, `loginWithCode`) |
| `useLoginWithSms` | SMS OTP |
| `useLoginWithOAuth` | Social logins (`initOAuth({provider: 'google'})`) |
| `useLoginWithPasskey` | Passkeys |
| `useSignupWithPasskey` | Passkey signup |
| `useLoginWithTelegram` | Telegram |
| `useLogin` | General login with callbacks |

## x402 Payments (Quick Start)

Built into `@privy-io/react-auth` since v3.7.0. Handles HTTP 402 payment flows automatically using USDC.

```tsx
import {useX402Fetch, useWallets} from '@privy-io/react-auth';

function PaidContent() {
  const {wallets} = useWallets();
  const {wrapFetchWithPayment} = useX402Fetch();

  const fetchContent = async () => {
    const fetchWithPayment = wrapFetchWithPayment({
      walletAddress: wallets[0]?.address,
      fetch,
      maxValue: BigInt(1000000) // Max 1 USDC
    });
    const res = await fetchWithPayment('https://api.example.com/premium');
    return res.json();
  };
}
```

Server-side (Node.js):
```ts
import {createX402Client} from '@privy-io/node/x402';
import {wrapFetchWithPayment} from '@x402/fetch';

const x402client = createX402Client(privy, {walletId: wallet.id, address: wallet.address});
const fetchWithPayment = wrapFetchWithPayment(fetch, x402client);
const response = await fetchWithPayment('https://api.example.com/premium');
```

## MPP Payments (Quick Start)

MPP (Machine Payments Protocol) settles on Tempo using PathUSD. Supports sessions for high-frequency payments.

```ts
import {Mppx, tempo} from 'mppx/client';

// Create Privy-backed viem account (see references/agent-payments.md for full pattern)
const account = createPrivyAccount(wallet.id, wallet.address);

const mppx = Mppx.create({polyfill: false, methods: [tempo({account})]});
const response = await mppx.fetch('https://api.example.com/weather');
```

## Agentic Wallets (Quick Start)

Server-controlled wallets with policy-based constraints for autonomous agents.

```ts
// Create agent wallet
const wallet = await privy.wallets().create({chain_type: 'ethereum'});

// Execute transactions - validated against attached policies
const {hash} = await privy.wallets().ethereum().sendTransaction(wallet.id, {
  caip2: 'eip155:8453',
  params: {transaction: {to: '0x...', value: '0x1', chain_id: 8453}}
});
```

Two control models: **agent-controlled** (fully autonomous, developer-owned) and **user-owned with agent signers** (user retains revocation authority). See [references/agent-auth.md](references/agent-auth.md) for policy examples and setup.

## Reference Docs

Read the appropriate reference file for detailed integration guides:

- **[references/react-sdk.md](references/react-sdk.md)** - All React hooks, PrivyProvider config, wagmi/viem setup, appearance config, whitelabel patterns, wallet UI components
- **[references/server-sdk.md](references/server-sdk.md)** - Node.js SDK (`@privy-io/node`), token types and verification, user management API, REST API, webhooks
- **[references/wallets.md](references/wallets.md)** - Embedded wallets (EVM + Solana), smart wallets (ERC-4337), gas sponsorship, external connectors, policies and controls, funding, wallet export
- **[references/solana.md](references/solana.md)** - Solana-specific setup, connectors, @solana/kit and @solana/web3.js integration, transaction signing, gas sponsorship via fee payer
- **[references/agent-payments.md](references/agent-payments.md)** - x402 protocol (React + Node.js), MPP with mppx SDK (client + server), Tempo blockchain (PathUSD, TIP-20), sessions, facilitators, x402 vs MPP comparison
- **[references/agent-auth.md](references/agent-auth.md)** - Agentic wallets (policies, authorization keys, OpenClaw), Agent Auth Protocol (per-agent identity, capabilities), MCP authorization, Better Auth bridge

## Key Documentation URLs

| Topic | URL |
|-------|-----|
| Full docs index (LLM-friendly) | https://docs.privy.io/llms.txt |
| React setup | https://docs.privy.io/basics/react/setup |
| React quickstart | https://docs.privy.io/basics/react/quickstart |
| Auth overview | https://docs.privy.io/authentication/overview |
| Whitelabel auth | https://docs.privy.io/authentication/user-authentication/whitelabel |
| Tokens (access/refresh/identity) | https://docs.privy.io/authentication/user-authentication/tokens |
| Wallets overview | https://docs.privy.io/wallets/overview |
| Wagmi integration | https://docs.privy.io/wallets/connectors/ethereum/integrations/wagmi |
| Viem integration | https://docs.privy.io/wallets/connectors/ethereum/integrations/viem |
| Smart wallets | https://docs.privy.io/wallets/using-wallets/evm-smart-wallets/overview |
| Smart wallets SDK config | https://docs.privy.io/wallets/using-wallets/evm-smart-wallets/setup/configuring-sdk |
| Gas sponsorship | https://docs.privy.io/wallets/gas-and-asset-management/gas/overview |
| Gas on Ethereum | https://docs.privy.io/wallets/gas-and-asset-management/gas/ethereum |
| Gas on Solana | https://docs.privy.io/wallets/gas-and-asset-management/gas/solana |
| Node.js SDK quickstart | https://docs.privy.io/basics/nodeJS/quickstart |
| Solana recipe | https://docs.privy.io/recipes/solana/getting-started-with-privy-and-solana |
| Connectors overview | https://docs.privy.io/wallets/connectors/overview |
| Custom auth provider | https://docs.privy.io/authentication/user-authentication/custom-auth |
| Webhooks | https://docs.privy.io/wallets/webhooks/overview |
| x402 integration | https://docs.privy.io/recipes/agent-integrations/x402 |
| MPP integration | https://docs.privy.io/recipes/agent-integrations/mpp |
| Agentic wallets | https://docs.privy.io/recipes/agent-integrations/agentic-wallets |
| OpenClaw integration | https://docs.privy.io/recipes/agent-integrations/openclaw-agentic-wallets |
| Tempo chain | https://docs.privy.io/recipes/evm/tempo |
| Wallet policies | https://docs.privy.io/wallets/policies/overview |
| Wallet signers | https://docs.privy.io/wallets/using-wallets/signers/overview |
| x402 protocol | https://x402.org |
| MPP protocol | https://mpp.dev |
| Agent Auth Protocol | https://agentauthprotocol.com |
| MCP auth spec | https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization |
