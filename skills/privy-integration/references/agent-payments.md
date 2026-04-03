# Agent Payments Reference

Privy integration with machine-to-machine payment protocols: x402, MPP (Machine Payments Protocol), and the Tempo blockchain.

## Table of Contents

- [x402 Protocol](#x402-protocol)
- [MPP (Machine Payments Protocol)](#mpp-machine-payments-protocol)
- [Tempo Chain](#tempo-chain)
- [x402 vs MPP Comparison](#x402-vs-mpp-comparison)

## x402 Protocol

x402 is an open payment protocol for instant, automatic payments over HTTP. When a resource requires payment, the server responds with `402 Payment Required`. The client constructs an `X-PAYMENT` header with a signed payment authorization and retries. A facilitator handles on-chain settlement so users only need USDC (not ETH/SOL for gas).

Protocol site: https://x402.org

### React Integration (useX402Fetch)

Built into `@privy-io/react-auth` since v3.7.0. No extra packages needed.

```tsx
import {useX402Fetch, useWallets} from '@privy-io/react-auth';

function PremiumContent() {
  const {wallets} = useWallets();
  const {wrapFetchWithPayment} = useX402Fetch();

  async function fetchContent() {
    const fetchWithPayment = wrapFetchWithPayment({
      walletAddress: wallets[0]?.address,
      fetch
    });
    const response = await fetchWithPayment('https://api.example.com/premium');
    return response.json();
  }

  return <button onClick={fetchContent}>Fetch Premium Content</button>;
}
```

### Max Payment Protection (React)

Cap the maximum payment per request to prevent overspending:

```tsx
const fetchWithPayment = wrapFetchWithPayment({
  walletAddress: wallets[0].address,
  fetch,
  maxValue: BigInt(1000000) // Max 1 USDC (6 decimals)
});
```

### Node.js Integration (Server-Side)

```bash
npm i @privy-io/node @x402/fetch
```

```ts
import {PrivyClient} from '@privy-io/node';
import {createX402Client} from '@privy-io/node/x402';
import {wrapFetchWithPayment} from '@x402/fetch';

const privy = new PrivyClient({
  appId: process.env.PRIVY_APP_ID!,
  appSecret: process.env.PRIVY_APP_SECRET!
});

// Get or create agent wallet
const wallet = await privy.wallets().get({walletId: 'your-wallet-id'});

// Create x402 client from Privy wallet
const x402client = createX402Client(privy, {
  walletId: wallet.id,
  address: wallet.address
});

// Wrap fetch for automatic 402 handling
const fetchWithPayment = wrapFetchWithPayment(fetch, x402client);

// Use like normal fetch - 402 responses are handled transparently
const response = await fetchWithPayment('https://api.example.com/premium');
const data = await response.json();
```

### Requirements

- Users/agents need **USDC** in their Privy wallet on the correct network (Base, Base Sepolia, or Solana)
- The **facilitator** pays gas fees - users only need USDC, not ETH or SOL
- Testnet USDC: https://faucet.circle.com/

### x402 Facilitators

| Name | URL | Docs |
|------|-----|------|
| Pay AI | `https://facilitator.payai.network/` | https://docs.payai.network/x402/reference |
| Corbits | `https://facilitator.corbits.dev/` | https://docs.corbits.dev/ |
| Coinbase | `https://api.cdp.coinbase.com/platform/v2/x402` | https://docs.cdp.coinbase.com/api-reference/v2/rest-api/x402-facilitator/x402-facilitator |

### x402 Payment Flow

```
1. Client requests resource via fetchWithPayment()
2. Server responds 402 with payment requirements (amount, currency, recipient)
3. Client wallet signs X-PAYMENT header (payment authorization)
4. Request retries with X-PAYMENT header attached
5. Facilitator verifies signature and settles on-chain (USDC transfer)
6. Server delivers content with 200 OK
```

## MPP (Machine Payments Protocol)

MPP is an open protocol for machine-to-machine payments over HTTP. Like x402, it uses HTTP 402 to signal payment required. Unlike x402, MPP settles on the **Tempo** blockchain using **PathUSD**, supports **sessions** for high-frequency payments, and is payment-method agnostic (stablecoins, cards, Lightning, custom rails).

Protocol site: https://mpp.dev

### Installation

```bash
npm i @privy-io/node mppx viem
```

### Creating a Privy-Backed Signer

MPP's `tempo()` payment method expects a viem Account. Since Privy wallets are server-managed, create a custom viem account that delegates signing to Privy's API:

```ts
import {PrivyClient} from '@privy-io/node';
import {toAccount} from 'viem/accounts';
import {keccak256} from 'viem';

const privy = new PrivyClient({
  appId: process.env.PRIVY_APP_ID!,
  appSecret: process.env.PRIVY_APP_SECRET!
});

function createPrivyAccount(walletId: string, address: `0x${string}`) {
  async function signHash(hash: `0x${string}`): Promise<`0x${string}`> {
    const result = await privy.wallets().ethereum().signSecp256k1(walletId, {
      params: {hash}
    });
    return result.signature as `0x${string}`;
  }

  return toAccount({
    address,
    async signMessage({message}) {
      const result = await privy.wallets().ethereum().signMessage(walletId, {
        message: typeof message === 'string' ? message : message.raw
      });
      return result.signature as `0x${string}`;
    },
    async signTransaction(transaction, options) {
      const serializer = options?.serializer;
      if (!serializer) throw new Error('Tempo serializer required');
      const unsignedSerialized = await serializer(transaction);
      const hash = keccak256(unsignedSerialized);
      const signature = await signHash(hash as `0x${string}`);
      const {SignatureEnvelope} = await import('ox/tempo');
      const envelope = SignatureEnvelope.from(signature);
      return (await serializer(transaction, envelope as any)) as `0x${string}`;
    },
    async signTypedData(typedData) {
      const result = await privy.wallets().ethereum().signTypedData(walletId, {
        params: typedData as any
      });
      return result.signature as `0x${string}`;
    }
  });
}
```

**Important**: Tempo transactions use a custom serialization format. `signTransaction` uses the Tempo-provided serializer and Privy's raw `signSecp256k1` endpoint rather than the higher-level `signTransaction` API.

### MPP Client - Making Paid Requests

```ts
import {Mppx, tempo} from 'mppx/client';

async function makePayment(walletId: string, address: `0x${string}`, url: string) {
  const account = createPrivyAccount(walletId, address);
  const mppx = Mppx.create({
    polyfill: false,
    methods: [tempo({account})]
  });
  const response = await mppx.fetch(url);
  return response.json();
}
```

### MPP Client - Polyfill Mode

Transparently handles 402 responses on all `fetch` calls:

```ts
import {Mppx, tempo} from 'mppx/client';

const account = createPrivyAccount(walletId, address);
Mppx.create({
  polyfill: true,
  methods: [tempo({account})]
});

// All fetch calls now handle 402 responses automatically
const response = await fetch('https://api.example.com/weather');
```

### MPP Server - Creating a Paywall (Next.js)

```ts
// app/api/weather/route.ts
import {Mppx, tempo} from 'mppx/nextjs';

const mppx = Mppx.create({
  methods: [
    tempo.charge({
      testnet: true,
      currency: '0x20c0000000000000000000000000000000000000', // PathUSD
      recipient: process.env.MPP_RECIPIENT as `0x${string}`
    })
  ]
});

export const GET = mppx.charge({amount: '0.1'})(() =>
  Response.json({
    temperature: 72,
    condition: 'Sunny',
    location: 'San Francisco, CA'
  })
);
```

### Full End-to-End Example

```ts
import {PrivyClient} from '@privy-io/node';
import {Mppx, tempo} from 'mppx/client';

const privy = new PrivyClient({
  appId: process.env.PRIVY_APP_ID!,
  appSecret: process.env.PRIVY_APP_SECRET!
});

// 1. Create agent wallet
const wallet = await privy.wallets().create({chain_type: 'ethereum'});

// 2. Build viem account backed by Privy
const account = createPrivyAccount(wallet.id, wallet.address as `0x${string}`);

// 3. Create MPP client
const mppx = Mppx.create({
  polyfill: false,
  methods: [tempo({account})]
});

// 4. Make a paid request
const response = await mppx.fetch('https://api.example.com/weather');
const weather = await response.json();
```

### MPP Sessions

Sessions enable high-frequency, low-value payments without per-request on-chain transactions:

1. Client **locks funds** upfront on Tempo
2. As services are consumed, client issues **signed vouchers** off-chain
3. Vouchers are **settled periodically** on-chain (batch)
4. Sub-100ms latency, near-zero per-request fees

This makes pay-as-you-go viable at internet scale for agents and real-time services (streaming inference, continuous data feeds, etc.).

### MPP Payment Flow

```
1. Client requests resource via mppx.fetch(url)
2. Server responds 402 with payment requirements (amount, currency, recipient)
3. MPP client signs payment credential using the Privy-backed account
4. Request retries with payment credential attached
5. Server verifies credential and settles on Tempo
6. Server delivers content with 200 OK
```

## Tempo Chain

Tempo is a low-cost, high-throughput EVM-compatible blockchain optimized for payments. Gas is paid in stablecoins (not ETH).

### Chain Details

| Property | Mainnet | Testnet (Moderato) |
|----------|---------|-------------------|
| CAIP-2 | `eip155:4217` | `eip155:42431` |
| RPC | `https://rpc.tempo.xyz` | `https://rpc.moderato.tempo.xyz` |
| Explorer | `https://explore.tempo.xyz` | `https://explore.tempo.xyz` |
| chain_type | `ethereum` | `ethereum` |

### Tokens

| Token | Address | Decimals | Standard |
|-------|---------|----------|----------|
| PathUSD | `0x20c0000000000000000000000000000000000000` | 6 | TIP-20 |
| alphaUSD | `0x20c0000000000000000000000000000000000001` | 6 | TIP-20 |

TIP-20 is Tempo's equivalent of ERC-20. Access via `Abis.tip20` from `tempo.ts/viem`.

### Tempo with Privy (Client-Side)

Using `tempo.ts` SDK with viem extensions:

```tsx
import {toViemAccount, useWallets} from '@privy-io/react-auth';
import {tempo} from 'tempo.ts/chains';
import {tempoActions} from 'tempo.ts/viem';
import {createWalletClient, custom, parseUnits, stringToHex} from 'viem';

const {wallets} = useWallets();
const wallet = wallets[0];
const provider = await wallet.getEthereumProvider();

const tempoChain = tempo({
  feeToken: '0x20c0000000000000000000000000000000000001' // alphaUSD
});

const client = createWalletClient({
  account: wallet.address as `0x${string}`,
  chain: tempoChain,
  transport: custom(provider)
}).extend(tempoActions());

// Transfer with memo
const metadata = await client.token.getMetadata({token: alphaUsd});
const {receipt} = await client.token.transferSync({
  to: recipientAddress,
  amount: parseUnits('1.00', metadata.decimals),
  memo: stringToHex('Payment for services'),
  token: alphaUsd
});
```

### Tempo with Privy (Three Transaction Approaches)

**1. Native Tempo tx type (0x76)** - uses custom viem account delegating to Privy's `signSecp256k1`:
- Enables per-transaction fee token specification
- Requires the `createPrivyAccount` pattern (see MPP section above)

**2. EVM tx type via tempoActions** - uses Privy's `createViemAccount` helper:
- Standard EIP-1559 transactions
- No Tempo-specific features like custom `feeToken` per tx

**3. Direct via Privy sendTransaction API** - manual ABI encoding:
- Supports Privy's native gas sponsorship via `sponsor` parameter
- Uses `caip2: 'eip155:4217'` (mainnet) or `'eip155:42431'` (testnet)

### Reading Balances (Tempo)

```ts
import {Abis} from 'tempo.ts/viem';
import {createPublicClient, webSocket} from 'viem';

const publicClient = createPublicClient({
  chain: tempoChain,
  transport: webSocket('wss://rpc.testnet.tempo.xyz')
});

const balance = await publicClient.readContract({
  address: '0x20c0000000000000000000000000000000000001', // alphaUSD
  abi: Abis.tip20,
  functionName: 'balanceOf',
  args: [walletAddress]
});
```

### Treasury Funding Pattern (Server-Side)

Fund agent wallets from a treasury wallet using Privy's Node SDK:

```ts
import {encodeFunctionData} from 'viem';
import {erc20Abi} from 'viem';

const result = await privy.wallets().ethereum().sendTransaction(treasuryWalletId, {
  caip2: 'eip155:42431', // Tempo testnet
  params: {
    transaction: {
      to: pathUsdAddress,
      data: encodeFunctionData({
        abi: erc20Abi,
        functionName: 'transfer',
        args: [agentAddress, amount]
      }),
      value: '0x0'
    }
  }
});
```

### User Lookup for Payments (Server-Side)

Resolve email/phone to wallet address for payment routing:

```ts
import {PrivyClient} from '@privy-io/node';

const privy = new PrivyClient({
  appId: process.env.PRIVY_APP_ID!,
  appSecret: process.env.PRIVY_APP_SECRET!
});

async function resolveRecipient(identifier: string) {
  const isEmail = identifier.includes('@');
  const user = isEmail
    ? await privy.users().getByEmailAddress({address: identifier}).catch(() => null)
    : await privy.users().getByPhoneNumber({number: identifier}).catch(() => null);

  if (!user) {
    // Create user with wallet if not found
    const newUser = await privy.users().create({
      linked_accounts: [isEmail
        ? {type: 'email', address: identifier}
        : {type: 'phone', number: identifier}
      ],
      wallets: [{chain_type: 'ethereum'}]
    });
    return newUser;
  }
  return user;
}

// Extract wallet address
const wallet = user.linked_accounts?.find(
  (a) => a.type === 'wallet' && a.chain_type === 'ethereum'
);
const recipientAddress = wallet?.address;
```

## x402 vs MPP Comparison

| Dimension | x402 | MPP |
|-----------|------|-----|
| Settlement chain | Base, Solana (via facilitators) | Tempo blockchain |
| Currency | USDC | PathUSD (+ other rails) |
| Execution model | One transaction per request | Sessions (off-chain vouchers + periodic settlement) |
| Performance | Per-request on-chain tx | Sub-100ms via sessions |
| Payment methods | Blockchain only (USDC) | Multi-rail: stablecoins, cards, Lightning, custom |
| Gas handling | Facilitator pays | Tempo handles (gas in stablecoins) |
| Client SDK | `@x402/fetch` + `@privy-io/react-auth` (useX402Fetch) | `mppx` |
| Server SDK | `@x402/server` | `mppx/nextjs` |
| Client pattern | `wrapFetchWithPayment(fetch, x402client)` | `mppx.fetch(url)` or polyfill mode |
| Privy React support | Built-in (`useX402Fetch` since v3.7.0) | Not built-in (server-side via Node SDK) |
| Privy Node support | `createX402Client` from `@privy-io/node/x402` | Custom viem account via `signSecp256k1` |
| Compatibility | - | MPP is compatible with x402-style flows |

**When to use x402**: Simpler integration, USDC-based payments, client-side React apps, existing Base/Solana infrastructure.

**When to use MPP**: High-frequency payments (sessions), multi-rail support needed, Tempo ecosystem, server-side autonomous agents.

## Official Links

| Topic | URL |
|-------|-----|
| x402 protocol | https://x402.org |
| x402 Privy docs | https://docs.privy.io/recipes/agent-integrations/x402 |
| MPP protocol | https://mpp.dev |
| MPP Privy docs | https://docs.privy.io/recipes/agent-integrations/mpp |
| mppx npm | https://www.npmjs.com/package/mppx |
| MPP demo repo | https://github.com/privy-io/examples/tree/main/examples/privy-next-mpp-agent-demo |
| Tempo Privy docs | https://docs.privy.io/recipes/evm/tempo |
| Tempo demo repo | https://github.com/privy-io/examples/tree/main/examples/privy-next-tempo |
| Tempo blog post | https://privy.io/blog/building-on-privy-with-tempo-machine-payments-protocol |
| Smart wallets demo | https://github.com/privy-io/examples/tree/main/examples/privy-next-smart-wallets |
