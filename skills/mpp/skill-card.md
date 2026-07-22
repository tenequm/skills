# Skill Card

## Description

mpp teaches building with MPP (Machine Payments Protocol) - the open HTTP 402 protocol for machine-to-machine payments - covering the mppx TypeScript SDK, pympp, the mpp Rust SDK, Tempo stablecoin/Stripe/Lightning payment methods, and charge/session/subscription intents.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Developers building paid APIs, payment-gated content, AI agent payment flows, MCP tool payments, or pay-per-token streaming over HTTP 402 - on the server (charging) or the client (paying), in TypeScript, Python, or Rust.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: Optional
Credential Type(s): Server-side MPP signing secret (MPP_SECRET_KEY), client wallet credentials (BIP-39 MNEMONIC or an EVM private key / Privy server wallet via PRIVY_APP_ID + PRIVY_APP_SECRET), Stripe API keys (STRIPE_SECRET_KEY and related) for the Stripe method, and upstream API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY) only when gating those APIs behind the payments proxy.

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Packages/CLIs the skill instructs the agent to use: mppx (npm) and the npx mppx CLI, viem, pympp (pip), mpp (cargo), @buildonspark/lightning-mpp-sdk, the tempo wallet CLI, and framework middleware (Hono, Express, Next.js, Elysia, FastAPI).

## Known Risks and Mitigations

Risk: The skill documents flows that sign and settle real stablecoin, card, and Bitcoin payments; a leaked wallet mnemonic, private key, or Stripe secret grants direct control of funds, and misconfigured pricing can overcharge or undercharge real customers.

Mitigation: Use testnet accounts and throwaway keys during development (the skill's testing flow auto-funds testnet accounts), bound agent spend with Tempo access keys (per-token limits, scopes, expiry), and human-review pricing and recipient addresses before production.

Risk: Session payment channels lock client deposits in escrow; documented failure modes (Store.memory() state loss on redeploy, unfunded recipient fee-token wallets, stalled upstreams) can leave client funds locked.

Mitigation: The skill mandates persistent stores in production, funding the recipient wallet with the stablecoin fee token, upstream AbortSignal timeouts, and channel recovery via channelId - follow its Production Gotchas section.

Risk: Rotating MPP_SECRET_KEY carelessly invalidates all in-flight payment challenges, breaking active paid sessions.

Mitigation: Rotate with an overlap window (issue with the new key while verifying the old until outstanding challenge TTLs expire), as the skill specifies.

## References

- MPP protocol and docs: https://mpp.dev (spec: https://paymentauth.org; IETF draft-ryan-httpauth-payment)
- mppx TypeScript SDK: https://github.com/wevm/mppx (tracked: mppx 0.8.1)
- pympp: https://github.com/tempoxyz/pympp (0.9.0); mpp Rust SDK: https://github.com/tempoxyz/mpp-rs (0.10.4)
- Tempo docs: https://docs.tempo.xyz; Stripe MPP docs: https://docs.stripe.com/payments/machine/mpp
- Source: https://github.com/tenequm/skills/tree/main/skills/mpp

## Skill Output

Output type(s): Server and client integration code (paid endpoints, middleware, payment proxies, MCP payment wrappers), CLI test commands, and configuration for stores/sessions/spend controls.

Output format: Code in TypeScript, Python, and Rust; shell commands; Markdown explanations.

Output parameters: Follows MPP protocol primitives (Challenge / Credential / Receipt headers) and mppx subpath-import conventions documented in the skill.

Other properties: Executing the produced code moves real funds on mainnet rails (Tempo, Stripe, Lightning); testnet paths are documented and should be used first.

## Skill Version

0.8.3

## Ethical Considerations

This skill handles financial infrastructure: code it produces charges real parties and spends from real wallets, so humans should review pricing, recipients, and spend limits before deployment, and agent wallets should run under scoped access keys with hard budgets. Payment gating must not be used to deceptively charge users or obscure costs.
