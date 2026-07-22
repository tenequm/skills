# Skill Card

## Description

foundry-solidity guides development and testing of Solidity smart contracts with the Foundry toolkit (forge, cast, anvil, chisel) - covering unit/fuzz/invariant/fork testing, deployment scripts, verification, and modern Solidity 0.8.30 patterns.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Smart contract developers building, testing, deploying, or debugging Ethereum/EVM contracts with Foundry. Use it for writing Forge tests, deploy scripts, foundry.toml configuration, cast interactions, and local anvil forks.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: Optional
Credential Type(s): EVM private key (PRIVATE_KEY / DEPLOYER_PRIVATE_KEY env vars, for deployment and cast send), RPC endpoints (MAINNET_RPC_URL, SEPOLIA_RPC_URL, etc.), block-explorer verification API keys (ETHERSCAN_API_KEY and per-chain variants). Local build/test workflows need no credentials.

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Tools/CLIs the skill instructs the agent to use: forge, cast, anvil, chisel (the Foundry toolkit; installable via the Homebrew foundry formula or the upstream foundryup installer), forge-std library.

## Known Risks and Mitigations

Risk: The skill documents commands that broadcast real transactions (forge script --broadcast, forge create, cast send) signed with a private key from an environment variable; a leaked key or a broadcast to the wrong chain can lose funds or deploy unintended contracts.

Mitigation: Use throwaway/testnet keys as the skill instructs, run scripts as dry-runs (without --broadcast) first, and have a human confirm the target chain and signer before any mainnet broadcast.

Risk: Deployed contract code is immutable and holds value; bugs shipped via the deployment flows in this skill cannot be patched in place.

Mitigation: The skill's testing guidance (fuzz, invariant, fork tests) and security reference should be applied before deployment; audit high-value contracts independently.

Risk: cast and fork tests send RPC URLs (and any embedded API keys) to third-party providers; verification uploads source code to block explorers.

Mitigation: Keep RPC URLs and explorer keys in env vars, not committed files; treat verification as publishing the source.

## References

- Foundry: https://github.com/foundry-rs/foundry and https://getfoundry.sh
- forge-std: https://github.com/foundry-rs/forge-std
- Solidity docs: https://docs.soliditylang.org
- Source: https://github.com/tenequm/skills/tree/main/skills/foundry-solidity

## Skill Output

Output type(s): Solidity contracts, Forge test files (*.t.sol), deploy scripts (*.s.sol), foundry.toml configuration, and executed forge/cast/anvil command output.

Output format: Code in Solidity and TOML; shell commands; Markdown explanations.

Output parameters: Follows Foundry project conventions (src/, test/, script/, lib/); tests named test_*/testFuzz_*.

Other properties: Commands with --broadcast or cast send have on-chain side effects and cost gas; everything else is local and side-effect free.

## Skill Version

0.2.3

## Ethical Considerations

Deployment and transaction flows can move real funds irreversibly; a human should review broadcast commands, target chains, and signers before execution. The security patterns documented here are for defending contracts, not for exploiting deployed ones.
