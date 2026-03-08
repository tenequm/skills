# React SDK Reference

Detailed reference for `@privy-io/react-auth` and related packages.

## Table of Contents

- [PrivyProvider Configuration](#privyprovider-configuration)
- [Core Hooks](#core-hooks)
- [Authentication Hooks](#authentication-hooks)
- [Wallet Hooks](#wallet-hooks)
- [Wagmi Integration](#wagmi-integration)
- [Viem Integration](#viem-integration)
- [Appearance & Theming](#appearance--theming)
- [Whitelabel Patterns](#whitelabel-patterns)
- [EVM Network Configuration](#evm-network-configuration)
- [App Clients](#app-clients)

## PrivyProvider Configuration

The `PrivyProvider` must wrap any component using Privy hooks. Render it as close to the root as possible.

### Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `appId` | `string` | Yes | Privy app ID from Dashboard |
| `clientId` | `string` | No | App client ID for multi-environment deployments |
| `config` | `PrivyClientConfig` | No | Configuration object |

### Full Config Shape

```tsx
import {PrivyProvider} from '@privy-io/react-auth';
import {toSolanaWalletConnectors} from '@privy-io/react-auth/solana';

<PrivyProvider
  appId="your-privy-app-id"
  clientId="your-client-id" // optional
  config={{
    // Login methods to enable
    loginMethods: ['email', 'sms', 'wallet', 'google', 'apple', 'twitter',
                   'github', 'discord', 'farcaster', 'telegram', 'passkey',
                   'linkedin', 'tiktok', 'spotify', 'instagram'],

    // Embedded wallet creation behavior
    embeddedWallets: {
      ethereum: {
        createOnLogin: 'users-without-wallets' // 'all-users' | 'off'
      },
      solana: {
        createOnLogin: 'users-without-wallets'
      }
    },

    // UI appearance
    appearance: {
      showWalletLoginFirst: false,
      walletChainType: 'ethereum-and-solana', // 'ethereum-only' | 'solana-only'
      theme: 'light', // 'dark' | custom theme object
      accentColor: '#6A6FF5',
      logo: 'https://your-logo.png',
      landingHeader: 'Welcome',
      loginMessage: 'Sign in to continue'
    },

    // External wallet connectors
    externalWallets: {
      solana: {
        connectors: toSolanaWalletConnectors()
      }
    },

    // Solana RPC config (needed for embedded wallet UIs)
    solana: {
      rpcs: {
        'solana:mainnet': {
          rpc: createSolanaRpc('https://api.mainnet-beta.solana.com'),
          rpcSubscriptions: createSolanaRpcSubscriptions('wss://api.mainnet-beta.solana.com')
        }
      }
    },

    // Supported EVM chains
    supportedChains: [mainnet, base, arbitrum],
    defaultChain: base
  }}
>
  {children}
</PrivyProvider>
```

## Core Hooks

### usePrivy

Primary hook for auth state and user info.

```tsx
import {usePrivy} from '@privy-io/react-auth';

const {
  ready,          // boolean - SDK initialized
  authenticated,  // boolean - user is logged in
  user,           // PrivyUser | null
  login,          // () => void - opens login modal
  logout,         // () => Promise<void>
  linkEmail,      // () => void
  linkWallet,     // () => void
  linkPhone,      // () => void
  unlinkEmail,    // (email: string) => void
  unlinkWallet,   // (address: string) => void
  unlinkPhone,    // (phone: string) => void
  connectWallet,  // () => void - connect external wallet
  getAccessToken, // () => Promise<string | null> - auto-refreshes
} = usePrivy();
```

### useLogin

Login with callbacks for lifecycle events.

```tsx
import {useLogin} from '@privy-io/react-auth';

const {login} = useLogin({
  onComplete: (user) => {
    console.log('Logged in:', user.id);
    router.push('/dashboard');
  },
  onError: (error) => {
    console.error('Login failed:', error);
  }
});
```

### User Object Shape

```tsx
interface PrivyUser {
  id: string;              // Privy DID (did:privy:...)
  createdAt: Date;
  linkedAccounts: LinkedAccount[];
  email?: {address: string};
  phone?: {number: string};
  wallet?: {address: string; chainType: string};
  google?: {email: string; subject: string};
  twitter?: {username: string; subject: string};
  discord?: {username: string; subject: string};
  github?: {username: string; subject: string};
  farcaster?: {fid: number; username: string};
  telegram?: {telegramUserId: string; username: string};
  // ... other linked account types
}
```

## Authentication Hooks

### useLoginWithEmail

```tsx
import {useLoginWithEmail} from '@privy-io/react-auth';

const {sendCode, loginWithCode, state} = useLoginWithEmail({
  onComplete: (user) => console.log('Logged in', user),
  onError: (error) => console.error(error)
});

// Step 1: Send OTP
await sendCode({email: 'user@example.com'});

// Step 2: Verify OTP
await loginWithCode({code: '123456'});

// Track state: 'initial' | 'sending-code' | 'awaiting-code-input' | 'submitting-code' | 'done'
```

### useLoginWithSms

```tsx
import {useLoginWithSms} from '@privy-io/react-auth';

const {sendCode, loginWithCode, state} = useLoginWithSms();
await sendCode({phoneNumber: '+1234567890'});
await loginWithCode({code: '123456'});
```

### useLoginWithOAuth

```tsx
import {useLoginWithOAuth} from '@privy-io/react-auth';

const {initOAuth, state} = useLoginWithOAuth();

// Supported providers: 'google', 'apple', 'twitter', 'discord', 'github',
//   'linkedin', 'tiktok', 'spotify', 'instagram'
await initOAuth({provider: 'google'});
```

### useLoginWithPasskey

```tsx
import {useLoginWithPasskey} from '@privy-io/react-auth';
import {useSignupWithPasskey} from '@privy-io/react-auth';

const {loginWithPasskey} = useLoginWithPasskey();
const {signupWithPasskey} = useSignupWithPasskey();

// Login with existing passkey
await loginWithPasskey();

// Create new account with passkey
await signupWithPasskey();
```

### useLoginWithTelegram

```tsx
import {useLoginWithTelegram} from '@privy-io/react-auth';

const {login, state} = useLoginWithTelegram();
await login();
```

### useLoginWithWallet

```tsx
import {useLoginWithWallet} from '@privy-io/react-auth';

const {login} = useLoginWithWallet();
await login({walletAddress: '0x...'}); // Optional: specify wallet
```

## Wallet Hooks

### useWallets (EVM)

```tsx
import {useWallets} from '@privy-io/react-auth';

const {ready, wallets} = useWallets();
// ready: boolean - wallets finished loading
// wallets: ConnectedWallet[] - all connected wallets (embedded + external)

const embeddedWallet = wallets.find((w) => w.walletClientType === 'privy');
const externalWallet = wallets.find((w) => w.walletClientType !== 'privy');
```

### useSendTransaction (EVM)

```tsx
import {useSendTransaction} from '@privy-io/react-auth';

const {sendTransaction} = useSendTransaction();
const txReceipt = await sendTransaction({
  to: '0xRecipient',
  value: 100000n, // in wei
  data: '0x...',   // optional calldata
  chainId: 8453    // optional chain
});
```

### useCreateWallet

```tsx
import {useCreateWallet} from '@privy-io/react-auth';

const {createWallet} = useCreateWallet();
const wallet = await createWallet(); // Creates embedded Ethereum wallet
```

### Wallet Object Methods

```tsx
const wallet = wallets[0];

// Get EIP-1193 provider (for viem/ethers)
const provider = await wallet.getEthereumProvider();

// Switch chain
await wallet.switchChain(8453); // Base chain ID

// Get address
const address = wallet.address;

// Wallet type
const isEmbedded = wallet.walletClientType === 'privy';
```

## Wagmi Integration

### Critical: Import from @privy-io/wagmi

```tsx
// CORRECT
import {createConfig, WagmiProvider} from '@privy-io/wagmi';

// WRONG - do NOT import these from wagmi directly
// import {createConfig, WagmiProvider} from 'wagmi';
```

### Complete Provider Setup

```tsx
// providers.tsx
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {PrivyProvider} from '@privy-io/react-auth';
import {WagmiProvider, createConfig} from '@privy-io/wagmi';
import {mainnet, base, sepolia} from 'viem/chains';
import {http} from 'wagmi';

const queryClient = new QueryClient();

const wagmiConfig = createConfig({
  chains: [mainnet, base, sepolia],
  transports: {
    [mainnet.id]: http(),
    [base.id]: http(),
    [sepolia.id]: http()
  }
});

export default function Providers({children}: {children: React.ReactNode}) {
  return (
    <PrivyProvider appId="your-app-id" config={{/* ... */}}>
      <QueryClientProvider client={queryClient}>
        <WagmiProvider config={wagmiConfig}>
          {children}
        </WagmiProvider>
      </QueryClientProvider>
    </PrivyProvider>
  );
}
```

### Switching Active Wallet

```tsx
import {useWallets} from '@privy-io/react-auth';
import {useSetActiveWallet} from '@privy-io/wagmi';

const {wallets} = useWallets();
const {setActiveWallet} = useSetActiveWallet();

// Set a different wallet as active for wagmi hooks
const targetWallet = wallets.find((w) => w.address === desiredAddress);
await setActiveWallet(targetWallet);
```

### When to Use Privy vs wagmi

- **wagmi**: Read/write actions from a connected wallet (useAccount, useSendTransaction, useContractWrite, useBalance, etc.)
- **Privy**: Connect external wallets, create embedded wallets, manage auth state

## Viem Integration

```tsx
import {createWalletClient, custom} from 'viem';
import {sepolia} from 'viem/chains';
import {useWallets} from '@privy-io/react-auth';

const {wallets} = useWallets();
const wallet = wallets[0];

// Switch to desired chain
await wallet.switchChain(sepolia.id);

// Get EIP-1193 provider
const provider = await wallet.getEthereumProvider();

// Create viem wallet client
const walletClient = createWalletClient({
  account: wallet.address as `0x${string}`,
  chain: sepolia,
  transport: custom(provider)
});

// Use walletClient for signing/transactions
```

## Appearance & Theming

```tsx
config={{
  appearance: {
    theme: 'dark',                    // 'light' | 'dark' | custom
    accentColor: '#6A6FF5',           // Brand color for buttons/links
    logo: 'https://your-logo.png',    // Logo in login modal
    showWalletLoginFirst: true,       // Show wallet option first
    walletChainType: 'ethereum-only', // Chain type filter
    landingHeader: 'Welcome',         // Modal header text
    loginMessage: 'Log in or sign up' // Modal description
  }
}}
```

## Whitelabel Patterns

All authentication flows can be built with custom UI using dedicated hooks.

### Complete Whitelabel Login

```tsx
'use client';
import {useState} from 'react';
import {useLoginWithEmail, useLoginWithOAuth, useLoginWithPasskey} from '@privy-io/react-auth';

function CustomLogin() {
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');

  const {sendCode, loginWithCode, state: emailState} = useLoginWithEmail();
  const {initOAuth} = useLoginWithOAuth();
  const {loginWithPasskey} = useLoginWithPasskey();

  return (
    <div>
      {/* Email login */}
      <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
      <button onClick={() => sendCode({email})} disabled={emailState === 'sending-code'}>
        Send Code
      </button>

      {emailState === 'awaiting-code-input' && (
        <>
          <input value={code} onChange={(e) => setCode(e.target.value)} placeholder="Code" />
          <button onClick={() => loginWithCode({code})}>Verify</button>
        </>
      )}

      {/* Social logins */}
      <button onClick={() => initOAuth({provider: 'google'})}>Google</button>
      <button onClick={() => initOAuth({provider: 'apple'})}>Apple</button>
      <button onClick={() => initOAuth({provider: 'twitter'})}>Twitter</button>

      {/* Passkey */}
      <button onClick={() => loginWithPasskey()}>Passkey</button>
    </div>
  );
}
```

### Linking Accounts

```tsx
import {useLinkWithPasskey} from '@privy-io/react-auth';

const {linkWithPasskey} = useLinkWithPasskey();
await linkWithPasskey(); // Link passkey to existing user
```

Similarly: `useLinkEmail`, `useLinkPhone`, `useLinkWallet` for linking additional auth methods.

## EVM Network Configuration

```tsx
import {mainnet, base, arbitrum, optimism, polygon} from 'viem/chains';

<PrivyProvider
  appId="your-app-id"
  config={{
    supportedChains: [mainnet, base, arbitrum, optimism, polygon],
    defaultChain: base // Default chain for transactions
  }}
>
```

Custom chains can also be defined using viem's `defineChain`.

## App Clients

For multi-environment deployments (staging, production), use app clients:

```tsx
<PrivyProvider
  appId="your-privy-app-id"
  clientId="client_xxx" // Different per environment
  config={{/* ... */}}
>
```

Configure app clients in the Privy Dashboard to customize auth settings, allowed URLs, and other behavior per environment.

## Additional Hooks

### useLoginWithSiwe / useLoginWithSiws

```tsx
import {useLoginWithSiwe} from '@privy-io/react-auth';

const {generateSiweMessage, loginWithSiwe} = useLoginWithSiwe();
// Sign-In with Ethereum: generate SIWE message, sign with wallet, verify
```

### useImportWallet

```tsx
import {useImportWallet} from '@privy-io/react-auth';

const {importWallet} = useImportWallet();
await importWallet({privateKey: '0x...'});
```

### toViemAccount (utility)

```tsx
import {toViemAccount, useWallets} from '@privy-io/react-auth';

const {wallets} = useWallets();
const account = await toViemAccount({wallet: wallets[0]});
// Use as viem account for signing
```

### Extended Chains

```tsx
import {useCreateWallet} from '@privy-io/react-auth/extended-chains';

const {createWallet} = useCreateWallet();
// Supports: 'cosmos', 'stellar', 'sui', 'tron', 'bitcoin-segwit', 'near', 'ton', 'starknet', 'spark'
await createWallet({chainType: 'sui'});
```

## Cross-App Wallets

`@privy-io/cross-app-connect` enables embedded wallets to be used by other apps (even non-Privy apps).

```tsx
import {toPrivyWallet} from '@privy-io/cross-app-connect/rainbow-kit';

const privyWallet = toPrivyWallet({
  id: '<privy-wallet-app-id>',
  name: 'Provider App',
  iconUrl: 'https://example.com/logo.png'
});
```

Docs: https://docs.privy.io/wallets/global-wallets/overview

## Package Versions (as of March 2026)

| Package | Version |
|---------|---------|
| `@privy-io/react-auth` | 3.16.0 |
| `@privy-io/node` | 0.10.1 |
| `@privy-io/wagmi` | 4.0.2 |
| `@privy-io/expo` | 0.63.8 |
| `@privy-io/cross-app-connect` | 0.5.4 |
| `@privy-io/js-sdk-core` | 0.60.4 |

## Official Links

- React setup: https://docs.privy.io/basics/react/setup
- React quickstart: https://docs.privy.io/basics/react/quickstart
- React features matrix: https://docs.privy.io/basics/react/features
- Wagmi integration: https://docs.privy.io/wallets/connectors/ethereum/integrations/wagmi
- Viem integration: https://docs.privy.io/wallets/connectors/ethereum/integrations/viem
- Whitelabel auth: https://docs.privy.io/authentication/user-authentication/whitelabel
- Appearance config: https://docs.privy.io/basics/react/appearance
- EVM networks: https://docs.privy.io/basics/react/evm-networks
- Solana networks: https://docs.privy.io/basics/react/solana-networks
- Migration to v3: https://docs.privy.io/basics/react/migration-v3
- Cross-app wallets: https://docs.privy.io/wallets/global-wallets/overview
- EIP-7702 integration: https://docs.privy.io/recipes/react/eip-7702
- Expo/React Native: https://docs.privy.io/basics/react-native/setup
- GitHub examples repo: https://github.com/privy-io/examples
