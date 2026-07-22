# Skill Card

## Description

x402 teaches an agent to build internet-native payment flows with the x402 open protocol (HTTP 402 Payment Required) - paid APIs, paywalled content, and AI-agent micropayments settled on-chain - using the TypeScript, Python, and Go SDKs across EVM, Solana, Stellar, and Aptos networks.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Developers building paid APIs, paywalls, MCP tools that charge per call, or agent-to-agent payment flows with the x402 protocol. Covers seller (resource server), buyer (client), and facilitator roles, scheme selection (exact, upto, batch-settlement, auth-capture), and mainnet deployment.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: Optional
Credential Type(s): Blockchain signing keys supplied via environment variables (EVM_PRIVATE_KEY, SVM_PRIVATE_KEY, APTOS_PRIVATE_KEY, FACILITATOR_KEY) - only needed when running client or facilitator code, not for server-side integration or reading the reference

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

- x402 SDKs: @x402/* npm packages (TypeScript), x402 on PyPI (Python), github.com/x402-foundation/x402/go/v2 (Go)
- Signing libraries used in examples: viem (EVM), @solana/kit (Solana)
- Package managers npm / pip / go for installing the SDKs

## Known Risks and Mitigations

Risk: The skill documents payment flows that sign real on-chain stablecoin transfers (USDC and others) with a private key read from an environment variable; a misconfigured flow, wrong network ID, or wrong payTo address can spend real funds irreversibly.

Mitigation: Quick starts and the default facilitator (https://x402.org/facilitator) target testnets (Base Sepolia, Solana Devnet, Stellar Testnet, Aptos Testnet); mainnet deployment is a deliberate, documented switch. Use dedicated low-value hot wallets for agent payments and human-review transaction parameters before going to mainnet.

Risk: Private keys held in environment variables can leak into logs, shell history, or model context.

Mitigation: All keys are declared as optional envVars in the skill metadata, examples read them via process.env / os.environ rather than embedding literals, and users should scope keys to minimal balances and rotate them.

Risk: Buyer-side wrappers pay automatically on any 402 response, so a malicious or mispriced endpoint could drain an agent's wallet through repeated charges.

Mitigation: The SDKs support payment selectors, price limits, and lifecycle hooks for approval logic; fund buyer wallets with only the amount an agent is allowed to spend.

## References

- x402 protocol repo and spec (tracked upstream: @x402/core@2.17.0, @x402/evm@2.17.0, x402@2.14.0 on PyPI, go/v2@v2.17.0): https://github.com/x402-foundation/x402
- x402 documentation: https://docs.x402.org
- Source: https://github.com/tenequm/skills/tree/main/skills/x402

## Skill Output

Output type(s): Payment-enabled application code - resource server middleware, buyer clients, facilitator setups, MCP payment integrations - plus protocol explanations.

Output format: TypeScript, Python, and Go code with install commands, in Markdown.

Output parameters: Follows x402 v2 protocol types (PaymentRequired, PaymentPayload, SettlementResponse) and CAIP-2 network identifiers.

Other properties: Generated code, when run by the user with funded keys, initiates real on-chain transactions; testnet defaults limit blast radius during development.

## Skill Version

0.10.2

## Ethical Considerations

This skill enables software that moves real money on-chain; transactions are irreversible and autonomous agent spending should be capped, monitored, and human-reviewed before mainnet use. Keys must be least-privilege, low-balance, and never exposed in prompts or logs.
