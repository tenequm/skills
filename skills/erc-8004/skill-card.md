# Skill Card

## Description

erc-8004 provides a reference for the ERC-8004 Trustless Agents standard - on-chain agent identity, reputation, validation, and discovery on EVM chains - including the Agent0 TypeScript SDK, registry contract addresses, and the registration file format.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Developers registering AI agents on-chain, building agent reputation or validation systems, or discovering agents by capability across EVM chains. Use it when working with the agent0-sdk npm package, the ERC-8004 registry contracts, or agent registration files.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: Optional
Credential Type(s): EVM private key (PRIVATE_KEY env var, for on-chain registration and feedback), EVM RPC endpoint (RPC_URL), Pinata JWT (PINATA_JWT, for IPFS pinning). Read-only discovery and search need only an RPC endpoint.

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Tools/packages the skill instructs the agent to use: agent0-sdk (npm), Node.js/TypeScript runtime. No CLI binaries are required.

## Known Risks and Mitigations

Risk: The skill documents flows that sign and broadcast real on-chain transactions (agent registration, feedback submission) with a private key from an environment variable; a leaked or over-funded key grants full control of the associated account.

Mitigation: Use throwaway or testnet keys for development, confirm chainId, signer, and balance before broadcasting, and reserve hardware wallets or scoped signers for mainnet activity, as the skill itself instructs.

Risk: Registering an agent publishes its registration file (name, endpoints, wallet address) permanently to IPFS and an on-chain registry; mistakes or sensitive data cannot be fully retracted.

Mitigation: Review the registration file contents before calling registerIPFS(); test the full flow on a testnet registry (Base Sepolia) first.

Risk: Reputation data read from the registry is only as trustworthy as the supplied clientAddresses reviewer list; naive aggregation is vulnerable to Sybil feedback.

Mitigation: Follow the skill's guidance to pass a curated trusted-reviewer list to getSummary() and treat unfiltered feedback as untrusted input.

## References

- ERC-8004 contracts: https://github.com/erc-8004/erc-8004-contracts
- Agent0 TypeScript SDK: https://github.com/agent0lab/agent0-ts
- SDK docs: https://sdk.ag0.xyz
- EIP discussion: https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098
- Source: https://github.com/tenequm/skills/tree/main/skills/erc-8004

## Skill Output

Output type(s): TypeScript integration code using agent0-sdk, agent registration JSON files, on-chain transactions (registration, feedback) when the user requests them, and explanations of the ERC-8004 standard.

Output format: Markdown with TypeScript and JSON code blocks; project files when scaffolding an integration.

Output parameters: Registration files follow the ERC-8004 registration-v1 JSON schema; agent identifiers use the "chainId:tokenId" format.

Other properties: On-chain writes cost gas and are irreversible; the skill instructs confirming chainId, signer, and balance before broadcasting.

## Skill Version

0.2.2

## Ethical Considerations

Flows in this skill can move funds and create permanent public records on blockchains; a human should review every transaction before it is signed, and only least-privilege keys should be exposed to the agent. Reputation tooling should not be used to fabricate or manipulate agent feedback.
