# Server SDK Reference

Reference for `@privy-io/node` and server-side Privy integration.

## Table of Contents

- [Setup](#setup)
- [Wallet Operations](#wallet-operations)
- [User Management](#user-management)
- [Token Verification](#token-verification)
- [Token Types](#token-types)
- [Webhooks](#webhooks)
- [REST API](#rest-api)
- [Error Handling](#error-handling)
- [Custom Auth Provider](#custom-auth-provider)

## Setup

```bash
npm i @privy-io/node
```

```ts
import {PrivyClient} from '@privy-io/node';

const privy = new PrivyClient({
  appId: process.env.PRIVY_APP_ID!,
  appSecret: process.env.PRIVY_APP_SECRET!
});
```

This replaces the deprecated `@privy-io/server-auth` package. Migration guide: https://docs.privy.io/basics/nodeJS/migration

## Wallet Operations

### Create a Wallet

```ts
// Server-managed wallet (no user owner)
const wallet = await privy.wallets().create({chain_type: 'ethereum'});
console.log(wallet.id, wallet.address);

// Solana wallet
const solWallet = await privy.wallets().create({chain_type: 'solana'});

// User-owned wallet
const userWallet = await privy.wallets().create({
  chain_type: 'ethereum',
  owner: {user_id: 'did:privy:xxx'}
});
```

### Sign a Message

```ts
// Ethereum
const {signature} = await privy.wallets().ethereum().signMessage(walletId, {
  message: 'Hello, Privy!'
});

// Solana
const {signature} = await privy.wallets().solana().signMessage(walletId, {
  message: 'Hello, Privy!'
});
```

### Send a Transaction (Ethereum)

```ts
const response = await privy.wallets().ethereum().sendTransaction(walletId, {
  caip2: 'eip155:8453', // Base mainnet
  params: {
    transaction: {
      to: '0xRecipientAddress',
      value: '0x1', // hex-encoded wei
      chain_id: 8453
    }
  }
});
console.log(response.hash);
```

### Send a Transaction (Solana)

```ts
const response = await privy.wallets().solana().signAndSendTransaction(walletId, {
  caip2: 'solana:mainnet',
  params: {
    transaction: serializedTransaction // base64-encoded
  }
});
```

### Sign Typed Data (EIP-712)

```ts
const {signature} = await privy.wallets().ethereum().signTypedData(walletId, {
  domain: {name: 'MyApp', version: '1', chainId: 8453},
  types: {/* EIP-712 types */},
  primaryType: 'Transfer',
  message: {/* typed data */}
});
```

### Get Wallet Info

```ts
const wallet = await privy.wallets().get(walletId);
// wallet.id, wallet.address, wallet.chain_type

const allWallets = await privy.wallets().list();
```

### Export Wallet

```ts
const {private_key} = await privy.wallets().export(walletId);
```

## User Management

### Create a User

```ts
const user = await privy.users().create({
  linked_accounts: [
    {type: 'email', address: 'user@example.com'},
    {type: 'custom_auth', custom_user_id: 'ext-user-123'}
  ]
});
```

### Create User with Pre-generated Wallet

```ts
const user = await privy.users().create({
  linked_accounts: [{type: 'email', address: 'user@example.com'}],
  create_ethereum_wallet: true,
  create_solana_wallet: true
});
```

### Get User

```ts
// By Privy user ID
const user = await privy.users().get('did:privy:xxx');

// By email
const user = await privy.users().getByEmail('user@example.com');

// By wallet address
const user = await privy.users().getByWalletAddress('0x...');

// By phone
const user = await privy.users().getByPhone('+1234567890');

// By Twitter username
const user = await privy.users().getByTwitterUsername('username');
```

### Search Users

```ts
const results = await privy.users().search({
  query: 'search term',
  // or filter by:
  emails: ['user@example.com'],
  phones: ['+1234567890'],
  walletAddresses: ['0x...']
});
```

### Delete a User

```ts
await privy.users().delete('did:privy:xxx');
```

### Add Custom Metadata

```ts
await privy.users().setCustomMetadata('did:privy:xxx', {
  role: 'admin',
  tier: 'premium'
});
```

## Token Verification

### Access Token Verification

```ts
// In an API route or middleware
const authHeader = req.headers.authorization; // "Bearer <access-token>"
const accessToken = authHeader?.replace('Bearer ', '');

try {
  const {userId, sessionId, appId} = await privy.verifyAuthToken(accessToken);
  // userId: 'did:privy:xxx'
  // Proceed with authenticated request
} catch (error) {
  // Token invalid or expired
  return res.status(401).json({error: 'Unauthorized'});
}
```

### Identity Token Verification

Identity tokens contain user data (linked accounts, metadata). Must be enabled in Dashboard.

```ts
const {userId, linkedAccounts, customMetadata} = await privy.verifyIdentityToken(identityToken);
```

### Getting Access Token on the Client

```tsx
import {usePrivy} from '@privy-io/react-auth';

const {getAccessToken} = usePrivy();

// Auto-refreshes if expired
const accessToken = await getAccessToken();

// Send to backend
const response = await fetch('/api/protected', {
  headers: {Authorization: `Bearer ${accessToken}`}
});
```

## Token Types

### Access Tokens
- **Lifetime**: 1 hour (configurable in Dashboard)
- **Format**: ES256-signed JWT
- **Claims**: `sid` (session ID), `sub` (user DID), `aud` (app ID), `iss` (privy.io), `iat`, `exp`
- **Use**: Backend API authentication

### Refresh Tokens
- **Lifetime**: 30 days (configurable)
- **Format**: Opaque string (not a JWT)
- **Management**: Handled entirely by Privy SDK, never expose to app code
- **Use**: Auto-refresh access tokens

### Identity Tokens
- **Lifetime**: 10 hours (configurable)
- **Format**: ES256-signed JWT
- **Claims**: User DID, linked accounts, custom metadata, app ID, timestamps
- **Use**: Access user data without extra API calls
- **Setup**: Must be enabled in Dashboard under User management > Authentication > Advanced

## Webhooks

Privy fires webhooks for various events. Configure in the Dashboard.

### Event Types

**User events:**
- `user.authenticated` - User logs in
- `user.created` - New user created
- `user.linked_account` - Account linked
- `user.unlinked_account` - Account unlinked
- `user.transferred_account` - Account transferred
- `user.updated_account` - Account updated

**Wallet events:**
- `user.wallet_created` - Embedded wallet created
- `wallet.funds_deposited` - Funds deposited
- `wallet.funds_withdrawn` - Funds withdrawn
- `wallet.private_key_export` - Key exported
- `wallet.recovered` - Wallet recovered

**Transaction events:**
- `transaction.broadcasted` - TX broadcast to network
- `transaction.confirmed` - TX confirmed on-chain
- `transaction.execution_reverted` - TX reverted
- `transaction.failed` - TX failed
- `transaction.replaced` - TX replaced (speed-up/cancel)
- `transaction.still_pending` - TX pending for extended time

**MFA events:**
- `mfa.enabled` - User enabled MFA
- `mfa.disabled` - User disabled MFA

**Intent events:**
- `intent.created` - New intent created
- `intent.authorized` - Intent authorized

### Webhook Verification (Recommended)

Privy uses Svix for webhook delivery. Verify signatures using `@privy-io/node`:

```ts
const privy = new PrivyClient({
  appId: process.env.PRIVY_APP_ID!,
  appSecret: process.env.PRIVY_APP_SECRET!,
  webhookSigningSecret: process.env.PRIVY_WEBHOOK_SIGNING_SECRET!
});

// POST /api/webhooks/privy
export async function POST(req: Request) {
  const body = await req.json();

  const payload = await privy.webhooks().verify({
    payload: body,
    svix: {
      id: req.headers.get('svix-id')!,
      timestamp: req.headers.get('svix-timestamp')!,
      signature: req.headers.get('svix-signature')!
    }
  });

  switch (payload.type) {
    case 'user.created':
      // Handle new user
      break;
    case 'transaction.confirmed':
      // Handle confirmed tx
      break;
  }

  return new Response('OK', {status: 200});
}
```

Delivery: at-least-once with retries (immediately, 5s, 5min, 30min, 2h, 5h, 10h, 10h). Endpoint auto-disabled after 5 days of consecutive failure.

Static IPs for allowlisting: `44.228.126.217`, `50.112.21.217`, `52.24.126.164`, `54.148.139.208`

## REST API

The REST API can be used directly for server-to-server operations. Base URL: `https://auth.privy.io/api/v1`

### Authentication

```
Authorization: Basic base64(appId:appSecret)
```

### Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/users` | Create a user |
| GET | `/users/{userId}` | Get user by ID |
| GET | `/users` | List all users |
| DELETE | `/users/{userId}` | Delete a user |
| POST | `/wallets` | Create a wallet |
| GET | `/wallets/{walletId}` | Get wallet |
| POST | `/wallets/{walletId}/rpc` | Execute wallet RPC |

Full OpenAPI spec: https://docs.privy.io/api-reference

## Error Handling

```ts
import {APIError, PrivyAPIError} from '@privy-io/node';

try {
  const wallet = await privy.wallets().create({chain_type: 'ethereum'});
} catch (error) {
  if (error instanceof APIError) {
    // HTTP error from Privy API (4xx, 5xx)
    console.log(error.status); // e.g. 400
    console.log(error.name);   // e.g. 'BadRequestError'
  } else if (error instanceof PrivyAPIError) {
    // SDK-level error
    console.log(error.message);
  } else {
    throw error; // Unrelated error
  }
}
```

## Custom Auth Provider

Integrate Privy with your existing auth (Auth0, Firebase, Cognito, etc.).

```tsx
// Client-side: pass your JWT to Privy
import {useLoginWithCustomAuth} from '@privy-io/react-auth';

const {loginWithCustomAuth} = useLoginWithCustomAuth();
await loginWithCustomAuth({customAccessToken: yourJWT});
```

Configure in Dashboard: set your JWKS endpoint or public key, issuer, and audience.

Docs: https://docs.privy.io/authentication/user-authentication/custom-auth

## Official Links

- Node.js setup: https://docs.privy.io/basics/nodeJS/setup
- Node.js quickstart: https://docs.privy.io/basics/nodeJS/quickstart
- Migration from server-auth: https://docs.privy.io/basics/nodeJS/migration
- Key concepts: https://docs.privy.io/basics/nodeJS/key-concepts
- Python SDK: https://docs.privy.io/basics/python/quickstart
- Go SDK: https://docs.privy.io/basics/go/quickstart
- Rust SDK: https://docs.privy.io/basics/rust/quickstart
- Java SDK: https://docs.privy.io/basics/java/quickstart
- REST API quickstart: https://docs.privy.io/basics/rest-api/quickstart
- Access tokens: https://docs.privy.io/authentication/user-authentication/access-tokens
- Identity tokens: https://docs.privy.io/authentication/user-authentication/identity-tokens
- Webhooks overview: https://docs.privy.io/wallets/webhooks/overview
