# mppx CLI

Verified against mppx 0.8.15 (`mppx --help`).

## Making Requests

```bash
# Paid request (payment handled automatically)
npx mppx https://api.example.com/data

# POST with a JSON body
npx mppx -X POST -J '{"prompt":"hello"}' https://api.example.com/chat

# Show response headers, then full negotiation detail
npx mppx -i https://api.example.com/data
npx mppx -vv https://api.example.com/data
```

Key root flags:

| Flag | Purpose |
|---|---|
| `--account, -a` | Account name (env: `MPPX_ACCOUNT`) |
| `--config, -c` | Path to config file (env: `MPPX_CONFIG`) |
| `--data, -d` / `--json-body, -J` | Request body / JSON body (implies POST) |
| `--header, -H` | Add header (repeatable) |
| `--method, -X` | HTTP method |
| `--method-opt, -M` | Method-specific option, `key=value` (repeatable) |
| `--network` | `mainnet` or `testnet` |
| `--rpc-url, -r` | RPC endpoint (env: `MPPX_RPC_URL`, falls back to `RPC_URL`) |
| `--session` | Session selection: `auto` (default), `new`, or a channel ID |
| `--auto-swap` / `--pay-with` / `--slippage` | Tempo auto-swap controls |
| `--include, -i` | Include response headers in output |
| `--verbose, -v` | Verbosity (`-v` details, `-vv` headers) |
| `--currency` | Payment currency/token address to select |
| `--confirm` | Show confirmation prompts |

Global output flags apply to every command: `--format <toon|json|yaml|md|jsonl>`, `--filter-output`, `--full-output`, `--token-count`, `--token-limit`, `--token-offset`, `--schema`, and `--llms` / `--llms-full` for an LLM-readable manifest. `--mcp` runs the CLI itself as an MCP stdio server.

## Inspecting a Challenge Without Paying

There is no `--inspect` flag. Use `mppx sign --dry-run`, which parses and validates a challenge without signing:

```bash
# Parse a challenge without signing it
npx mppx sign --dry-run --challenge 'Payment id="...", method="tempo", ...'

# Or sign it and emit the Authorization header value
curl -si https://api.example.com/data | grep -i www-authenticate | npx mppx sign
```

`mppx sign` accepts the challenge via `--challenge/-C` or on stdin, and shares the account, network, RPC, and auto-swap flags with the root command.

## Validating a Server

`mppx validate` runs an end-to-end conformance check against an MPP server: discovery, challenge formats, error handling, and the full payment flow.

```bash
npx mppx validate http://localhost:4242

# Skip discovery and test one endpoint directly
npx mppx validate http://localhost:4242 -e POST:/paid --body '{"prompt":"hi"}'
```

| Flag | Purpose |
|---|---|
| `--endpoint, -e` | Endpoint to test as `METHOD:path`; skips discovery |
| `--body` | Request body. In discovery mode, JSON keyed by path is a per-path mapping |
| `--query` | Query parameter `key=value` (repeatable) |
| `--header, -H` | Request header `key:value` (repeatable) |
| `--yes, -y` | Auto-approve mainnet payments |
| `--output-json, -j` | JSON output (auto-enabled in known agent environments) |
| `--verbose, -v` | Verbosity level |

On testnets and Stripe test mode the CLI completes roundtrip test payments automatically. On mainnet it can complete **real** payments from the local wallet, which is why `--yes` exists as an explicit opt-in. Run it against both a sandbox and a production build of your server.

The same checks are available programmatically through the `mppx/validation` export, for wiring conformance into CI.

## Accounts

```bash
npx mppx account create           # create (stored in system keychain)
npx mppx account list             # list all accounts
npx mppx account view             # show account address
npx mppx account default          # set the default account
npx mppx account export           # export a local account's private key
npx mppx account fund --network testnet   # fund with testnet tokens
npx mppx account delete
```

`mppx account fund` is testnet-only; the mainnet option was removed in 0.8.6.

## Sessions

```bash
npx mppx sessions list            # list persistent payment sessions
npx mppx sessions view <id>
npx mppx sessions close <id>      # settle and close a channel
```

The CLI reuses sessions automatically (`--session auto`). Pass `--session new` to force a fresh channel or `--session <channelId>` to target a specific one. Session state lives in the Tempo Wallet channel database, which the `mppx/client/node` SQLite `ChannelStore` also reads.

## Discovery and Services

```bash
npx mppx discover generate        # generate a discovery document
npx mppx discover validate        # validate one
npx mppx services                 # browse the MPP services registry
```

## Integrations

```bash
npx mppx init                     # create an mppx.config.ts in the current directory
npx mppx mcp add                  # register mppx as an MCP server
npx mppx mcp doctor               # diagnose MCP registration
npx mppx skills add               # sync MPP skill files to your agents
npx mppx skills list
npx mppx completions              # shell completion script
```

## Config File

Extend the CLI with custom payment methods via `mppx.config.(js|mjs|ts)`:

```typescript
// mppx.config.ts
import { defineConfig } from 'mppx/cli'
export default defineConfig({ plugins: [myCustomMethod()] })
```

Config resolution has exactly two paths: the `MPPX_CONFIG` env var, or an explicit `--config ./mppx.config.ts`. There is **no** auto-discovery from the current or parent directories (removed in 0.8.1), so a config file sitting in the working directory is ignored unless you point at it.

Plugin authoring helpers live in `mppx/cli/plugins`. Note this is a module export, not a CLI verb - there is no `mppx plugins` command.

## Environment Variables

| Variable | Purpose |
|---|---|
| `MPPX_ACCOUNT` | Default account name |
| `MPPX_CONFIG` | Path to the config file |
| `MPPX_RPC_URL` | RPC endpoint (takes precedence) |
| `RPC_URL` | RPC endpoint fallback |
