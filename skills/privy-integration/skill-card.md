# Skill Card

## Description

privy-integration guides integrating Privy authentication, embedded wallets, and agent payment protocols (x402, MPP) into web and agentic apps - covering the React SDK, Node.js SDK, wagmi, smart wallets (ERC-4337), Solana, Tempo, and policy-constrained agentic wallets.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Web and agent developers adding Privy auth and embedded/self-custodial wallets to React or Node.js apps, wiring wagmi/viem, enabling x402 or MPP machine payments, or provisioning policy-governed agentic wallets for autonomous agents.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: Yes
Credential Type(s): Privy App ID and App Secret (PRIVY_APP_ID / PRIVY_APP_SECRET server-side, NEXT_PUBLIC_PRIVY_APP_ID client-side), Privy webhook signing secret (PRIVY_WEBHOOK_SIGNING_SECRET), and an MPP recipient address (MPP_RECIPIENT) for payment flows.

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Packages the skill instructs the agent to use: @privy-io/react-auth (plus /solana and /smart-wallets subpaths), @privy-io/wagmi, @privy-io/node, wagmi, viem, @tanstack/react-query, mppx, @x402/fetch.

## Known Risks and Mitigations

Risk: The skill documents server-side wallet control - PRIVY_APP_SECRET plus the Node SDK can create wallets and sign real transactions for users and agents; a leaked secret grants transaction authority over every app wallet.

Mitigation: Keep the app secret server-side only, scope agentic wallets with Privy policies (spend limits, allowed contracts/recipients), and prefer the user-owned-with-agent-signers model so users retain revocation authority.

Risk: x402 and MPP payment flows spend real USDC/stablecoins automatically when an endpoint returns 402; an unbounded wrapper can drain a wallet on a malicious or misbehaving API.

Mitigation: Set maxValue / maxDeposit bounds as shown in the skill, fund payment wallets with small dedicated balances, and human-review recipient endpoints before enabling autonomous payment.

Risk: Misconfigured auth (missing Allowed Origins, mishandled token verification) can silently break or weaken login security.

Mitigation: Follow the skill's verification pattern (utils().auth().verifyAccessToken) and its documented footguns, including registering every app domain and dev port in the Privy Dashboard.

## References

- Privy docs: https://docs.privy.io (tracked: @privy-io/react-auth 3.29.1, @privy-io/node 0.20.0, @privy-io/wagmi 4.0.11)
- x402 protocol: https://x402.org; MPP protocol: https://mpp.dev (mppx 0.6.30, @x402/fetch 2.14.0)
- Agent Auth Protocol: https://agentauthprotocol.com
- Source: https://github.com/tenequm/skills/tree/main/skills/privy-integration

## Skill Output

Output type(s): React and Node.js integration code (providers, hooks, token verification, wallet creation, payment-wrapped fetch), configuration snippets, and architecture guidance.

Output format: Code in TypeScript/TSX; shell install commands; Markdown explanations.

Output parameters: Follows Privy SDK conventions (PrivyProvider config shape, hook APIs, CAIP-2 chain IDs); otherwise not applicable.

Other properties: Produced code performs authentication and can sign on-chain transactions when executed; wallet-mutating and payment code should be tested on testnets first.

## Skill Version

0.4.2

## Ethical Considerations

The skill touches both user identity and user funds: auth flows must protect user credentials and sessions, and payment/agentic-wallet flows can move real money, so humans should review policies, spend limits, and transaction code before production use. Agent-controlled wallets should always run under explicit, revocable constraints.
